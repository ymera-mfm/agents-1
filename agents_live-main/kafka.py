"""
Kafka Python Stub

This is a stub module that provides compatibility when kafka-python is not installed.

To use the real implementation:
    pip install kafka-python
"""

__version__ = "0.0.0-stub"


class KafkaProducer:
    """Stub KafkaProducer"""
    
    def __init__(self, **configs):
        self.bootstrap_servers = configs.get('bootstrap_servers', [])
    
    def send(self, topic, value=None, key=None, partition=None, timestamp=None):
        """Stub send method"""
        class StubFuture:
            def get(self, timeout=None):
                return None
        return StubFuture()
    
    def flush(self):
        """Stub flush method"""
        pass
    
    def close(self):
        """Stub close method"""
        pass


class KafkaConsumer:
    """Stub KafkaConsumer"""
    
    def __init__(self, *topics, **configs):
        self.topics = topics
        self.bootstrap_servers = configs.get('bootstrap_servers', [])
    
    def __iter__(self):
        """Stub iterator"""
        return iter([])
    
    def commit(self):
        """Stub commit method"""
        pass
    
    def close(self):
        """Stub close method"""
        pass


__all__ = [
    'KafkaProducer',
    'KafkaConsumer',
]
