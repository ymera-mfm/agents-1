"""Tests for resilience utilities (circuit breaker, retry logic, graceful degradation)"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from core.resilience import (
    CircuitBreaker,
    CircuitState,
    retry_with_exponential_backoff,
    with_retry,
    GracefulDegradation
)


class TestCircuitBreaker:
    """Test circuit breaker pattern"""
    
    def test_circuit_starts_closed(self):
        """Circuit breaker should start in CLOSED state"""
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    def test_circuit_opens_after_threshold(self):
        """Circuit should open after reaching failure threshold"""
        cb = CircuitBreaker(failure_threshold=3)
        
        # Simulate 3 failures
        for i in range(3):
            try:
                cb.call(lambda: exec('raise Exception("test")'))
            except:
                pass
        
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count >= 3
    
    def test_circuit_rejects_calls_when_open(self):
        """Circuit should reject calls when OPEN"""
        cb = CircuitBreaker(failure_threshold=2)
        
        # Force circuit to OPEN
        cb.state = CircuitState.OPEN
        
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            cb.call(lambda: "should not execute")
    
    def test_successful_call_resets_failure_count(self):
        """Successful call should reset failure count"""
        cb = CircuitBreaker(failure_threshold=5)
        
        # One failure
        try:
            cb.call(lambda: exec('raise Exception("test")'))
        except:
            pass
        
        assert cb.failure_count == 1
        
        # Successful call
        result = cb.call(lambda: "success")
        assert result == "success"
        assert cb.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_async_circuit_breaker(self):
        """Circuit breaker should work with async functions"""
        cb = CircuitBreaker(failure_threshold=3)
        
        async def async_success():
            return "async_success"
        
        result = await cb.call_async(async_success)
        assert result == "async_success"
        assert cb.state == CircuitState.CLOSED


class TestRetryWithExponentialBackoff:
    """Test retry logic with exponential backoff"""
    
    @pytest.mark.asyncio
    async def test_successful_call_no_retry(self):
        """Successful call should not retry"""
        call_count = 0
        
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await retry_with_exponential_backoff(
            success_func,
            max_retries=3
        )
        
        assert result == "success"
        assert call_count == 1  # Called only once
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Should retry on failure"""
        call_count = 0
        
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("temporary failure")
            return "success after retries"
        
        result = await retry_with_exponential_backoff(
            failing_then_success,
            max_retries=5,
            base_delay=0.01  # Small delay for tests
        )
        
        assert result == "success after retries"
        assert call_count == 3  # Failed twice, succeeded on third
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Should raise exception after max retries"""
        call_count = 0
        
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("always fails")
        
        with pytest.raises(ValueError, match="always fails"):
            await retry_with_exponential_backoff(
                always_fails,
                max_retries=2,
                base_delay=0.01
            )
        
        assert call_count == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_with_retry_decorator(self):
        """Test retry decorator"""
        call_count = 0
        
        @with_retry(max_retries=2, base_delay=0.01)
        async def decorated_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("retry me")
            return "decorated success"
        
        result = await decorated_func()
        assert result == "decorated success"
        assert call_count == 2


class TestGracefulDegradation:
    """Test graceful degradation patterns"""
    
    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self):
        """Should use fallback when primary fails"""
        
        async def primary():
            raise Exception("primary failed")
        
        async def fallback():
            return "fallback result"
        
        result = await GracefulDegradation.with_fallback(primary, fallback)
        assert result == "fallback result"
    
    @pytest.mark.asyncio
    async def test_primary_success_no_fallback(self):
        """Should use primary result when it succeeds"""
        
        async def primary():
            return "primary result"
        
        async def fallback():
            return "fallback result"
        
        result = await GracefulDegradation.with_fallback(primary, fallback)
        assert result == "primary result"
    
    @pytest.mark.asyncio
    async def test_optional_cache_with_cache_hit(self):
        """Should return cached value when available"""
        
        async def cache_get(key):
            return "cached_value"
        
        async def cache_set(key, value):
            pass
        
        async def compute():
            return "computed_value"
        
        result = await GracefulDegradation.optional_cache(
            cache_get, cache_set, compute, "test_key"
        )
        
        assert result == "cached_value"
    
    @pytest.mark.asyncio
    async def test_optional_cache_with_cache_miss(self):
        """Should compute value when cache misses"""
        
        async def cache_get(key):
            return None
        
        async def cache_set(key, value):
            pass
        
        async def compute():
            return "computed_value"
        
        result = await GracefulDegradation.optional_cache(
            cache_get, cache_set, compute, "test_key"
        )
        
        assert result == "computed_value"
    
    @pytest.mark.asyncio
    async def test_optional_cache_continues_on_cache_failure(self):
        """Should continue without cache if cache operations fail"""
        
        async def cache_get(key):
            raise Exception("cache unavailable")
        
        async def cache_set(key, value):
            raise Exception("cache unavailable")
        
        async def compute():
            return "computed_value"
        
        # Should not raise exception, just compute
        result = await GracefulDegradation.optional_cache(
            cache_get, cache_set, compute, "test_key"
        )
        
        assert result == "computed_value"
