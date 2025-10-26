"""Simple test agent for benchmarking"""
import time


class SimpleTestAgent:
    """A simple agent for testing benchmarking functionality"""
    
    def __init__(self):
        self.name = "SimpleTestAgent"
        self.data = []
        # Simulate some initialization work
        time.sleep(0.001)
    
    def simple_method(self):
        """A simple method that does basic work"""
        result = sum(range(100))
        return result
    
    def compute_heavy(self):
        """A method that does more computation"""
        result = sum(range(1000))
        return result
    
    def memory_operation(self):
        """A method that uses some memory"""
        temp_data = list(range(1000))
        return len(temp_data)


class FastTestAgent:
    """A very fast agent for testing excellent performance"""
    
    def __init__(self):
        self.name = "FastTestAgent"
        self.counter = 0
    
    def quick_increment(self):
        """Very fast operation"""
        self.counter += 1
        return self.counter
    
    def quick_check(self):
        """Another fast operation"""
        return self.counter > 0


class SlowTestAgent:
    """A slower agent for testing acceptable performance"""
    
    def __init__(self):
        self.name = "SlowTestAgent"
        self.data = {}
        # Simulate slower initialization
        time.sleep(0.08)
    
    def slow_operation(self):
        """A slower operation"""
        time.sleep(0.01)
        return len(self.data)
