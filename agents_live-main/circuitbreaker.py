"""
Circuit Breaker Stub

This is a stub module that provides compatibility when circuitbreaker is not installed.

To use the real implementation:
    pip install circuitbreaker
"""

__version__ = "0.0.0-stub"


def circuit(failure_threshold=5, recovery_timeout=30, expected_exception=Exception):
    """Stub circuit breaker decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


class CircuitBreaker:
    """Stub CircuitBreaker class"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=30, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.state = 'closed'
    
    def call(self, func, *args, **kwargs):
        """Stub call method"""
        return func(*args, **kwargs)


__all__ = [
    'circuit',
    'CircuitBreaker',
]
