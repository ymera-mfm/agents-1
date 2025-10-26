"""
OpenTelemetry Prometheus Exporter Stub

This is a stub module that provides compatibility when opentelemetry-exporter-prometheus
is not installed. It provides minimal functionality to allow imports to succeed.

To use the real implementation:
    pip install opentelemetry-exporter-prometheus
"""

__version__ = "0.0.0-stub"


class PrometheusMetricReader:
    """Stub PrometheusMetricReader for compatibility"""
    
    def __init__(self, *args, **kwargs):
        """Initialize stub reader"""
        self.port = kwargs.get('port', 9464)
        self.endpoint = kwargs.get('endpoint', '/metrics')
    
    def collect(self):
        """Stub collect method"""
        return []
    
    def shutdown(self):
        """Stub shutdown method"""
        pass


def start_http_server(port=9464, addr='0.0.0.0', registry=None):
    """Stub function to start HTTP server for Prometheus metrics"""
    pass


__all__ = [
    'PrometheusMetricReader',
    'start_http_server',
]
