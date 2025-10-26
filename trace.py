"""
OpenTelemetry trace stub module
"""

class Tracer:
    """Stub Tracer"""
    def start_as_current_span(self, name):
        """Stub span context manager"""
        class StubSpan:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def set_attribute(self, key, value):
                pass
            def add_event(self, name, attributes=None):
                pass
            def set_status(self, status):
                pass
        return StubSpan()

class TracerProvider:
    """Stub TracerProvider"""
    def get_tracer(self, name, version=None):
        return Tracer()

def get_tracer_provider():
    """Get the global tracer provider"""
    return TracerProvider()

def get_tracer(name, version=None):
    """Get a tracer"""
    return Tracer()

def set_tracer_provider(provider):
    """Set the global tracer provider"""
    pass

__all__ = ['Tracer', 'TracerProvider', 'get_tracer', 'get_tracer_provider', 'set_tracer_provider']
