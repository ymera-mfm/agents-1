"""
Circuit Breaker Pattern
Production-grade circuit breaker for preventing cascade failures
"""

import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass
from collections import deque
import structlog

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Blocking requests
    HALF_OPEN = "half_open"    # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5        # Failures before opening
    success_threshold: int = 2        # Successes to close from half-open
    timeout_seconds: int = 60         # Time before trying half-open
    window_size: int = 100            # Rolling window size
    min_throughput: int = 10          # Minimum requests to calculate
    excluded_exceptions: tuple = ()   # Exceptions that don't count as failures


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Production-grade circuit breaker implementation
    
    Prevents cascade failures by stopping requests to failing services
    and allowing them time to recover.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failures detected, requests blocked
    - HALF_OPEN: Testing if service recovered
    
    Usage:
        breaker = CircuitBreaker("external_api", CircuitBreakerConfig())
        result = await breaker.call(some_async_function, arg1, arg2)
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_success_time = 0
        self.last_state_change = time.time()
        
        # Rolling window for failure rate calculation
        self.call_history = deque(maxlen=config.window_size)
        
        # Metrics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.state_changes = 0
        self.times_opened = 0
        
        logger.info(
            "Circuit breaker initialized",
            name=self.name,
            state=self.state.value,
            config=config
        )
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker
        
        Args:
            func: Async function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Original exception: If function fails
        """
        self.total_calls += 1
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN - service unavailable"
                )
        
        # Execute function
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            await self._on_success(execution_time)
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Check if this exception should be excluded
            if isinstance(e, self.config.excluded_exceptions):
                logger.debug(
                    "Exception excluded from circuit breaker",
                    name=self.name,
                    exception=type(e).__name__
                )
                raise
            
            await self._on_failure(e, execution_time)
            raise
    
    async def call_with_fallback(
        self,
        func: Callable,
        fallback: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with fallback if circuit is open
        
        Args:
            func: Primary async function
            fallback: Fallback async function
            *args, **kwargs: Arguments for primary function
            
        Returns:
            Result from primary or fallback
        """
        try:
            return await self.call(func, *args, **kwargs)
        except CircuitBreakerOpenError:
            logger.info(
                "Circuit open, using fallback",
                name=self.name
            )
            return await fallback(*args, **kwargs)
    
    async def _on_success(self, execution_time: float):
        """Handle successful call"""
        self.total_successes += 1
        self.success_count += 1
        self.last_success_time = time.time()
        self.call_history.append((True, execution_time))
        
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        
        # Reset failure count on success in closed state
        if self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    async def _on_failure(self, error: Exception, execution_time: float):
        """Handle failed call"""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.call_history.append((False, execution_time))
        
        logger.warning(
            "Circuit breaker recorded failure",
            name=self.name,
            error=str(error)[:200],
            error_type=type(error).__name__,
            failure_count=self.failure_count,
            state=self.state.value
        )
        
        if self.state == CircuitState.HALF_OPEN:
            # Immediately open on failure in half-open state
            self._transition_to_open()
        elif self.state == CircuitState.CLOSED:
            # Check if we should open
            if self._should_open():
                self._transition_to_open()
    
    def _should_open(self) -> bool:
        """Check if circuit should open"""
        # Need minimum throughput to make decision
        if len(self.call_history) < self.config.min_throughput:
            return False
        
        # Check failure count threshold
        if self.failure_count >= self.config.failure_threshold:
            return True
        
        # Check failure rate in rolling window
        failures_in_window = sum(1 for success, _ in self.call_history if not success)
        failure_rate = failures_in_window / len(self.call_history)
        
        # Open if failure rate > 50% and we have minimum throughput
        return (
            failure_rate > 0.5 and
            len(self.call_history) >= self.config.min_throughput
        )
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to close circuit"""
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.timeout_seconds
    
    def _transition_to_open(self):
        """Transition to open state"""
        if self.state != CircuitState.OPEN:
            previous_state = self.state
            self.state = CircuitState.OPEN
            self.state_changes += 1
            self.times_opened += 1
            self.last_state_change = time.time()
            
            logger.error(
                "Circuit breaker opening",
                name=self.name,
                previous_state=previous_state.value,
                failure_count=self.failure_count,
                total_failures=self.total_failures,
                total_calls=self.total_calls
            )
            
            # Here you could trigger alerts, metrics, etc.
    
    def _transition_to_half_open(self):
        """Transition to half-open state"""
        previous_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.failure_count = 0
        self.state_changes += 1
        self.last_state_change = time.time()
        
        logger.info(
            "Circuit breaker entering half-open state",
            name=self.name,
            previous_state=previous_state.value
        )
    
    def _transition_to_closed(self):
        """Transition to closed state"""
        previous_state = self.state
        self.state = CircuitState.CLOSED
        self.success_count = 0
        self.failure_count = 0
        self.state_changes += 1
        self.last_state_change = time.time()
        
        logger.info(
            "Circuit breaker closing (recovered)",
            name=self.name,
            previous_state=previous_state.value
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        failure_rate = (
            self.total_failures / self.total_calls
            if self.total_calls > 0 else 0
        )
        
        # Calculate average execution times
        recent_successes = [t for success, t in self.call_history if success]
        recent_failures = [t for success, t in self.call_history if not success]
        
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self.total_calls,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "failure_rate": failure_rate,
            "current_failure_count": self.failure_count,
            "current_success_count": self.success_count,
            "state_changes": self.state_changes,
            "times_opened": self.times_opened,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "last_state_change": self.last_state_change,
            "avg_success_time": sum(recent_successes) / len(recent_successes) if recent_successes else 0,
            "avg_failure_time": sum(recent_failures) / len(recent_failures) if recent_failures else 0,
            "window_size": len(self.call_history)
        }
    
    def reset(self):
        """Manually reset circuit breaker (admin function)"""
        logger.info("Circuit breaker manually reset", name=self.name)
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.call_history.clear()


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers
    
    Usage:
        from shared.patterns import circuit_breaker_registry
        
        breaker = circuit_breaker_registry.get_or_create("external_api")
        result = await breaker.call(api_function, args)
    """
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker"""
        if name not in self.breakers:
            config = config or CircuitBreakerConfig()
            self.breakers[name] = CircuitBreaker(name, config)
        return self.breakers[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.breakers.get(name)
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers"""
        return {
            name: breaker.get_metrics()
            for name, breaker in self.breakers.items()
        }
    
    def reset_all(self):
        """Reset all circuit breakers (admin function)"""
        for breaker in self.breakers.values():
            breaker.reset()
    
    def list_open_breakers(self) -> list[str]:
        """Get list of open circuit breakers"""
        return [
            name for name, breaker in self.breakers.items()
            if breaker.state == CircuitState.OPEN
        ]


# Global registry instance
circuit_breaker_registry = CircuitBreakerRegistry()
