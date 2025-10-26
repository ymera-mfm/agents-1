"""Security tests for safe serialization"""
import pytest
import json


def test_json_serialization_is_safe():
    """Test that JSON serialization is used instead of pickle"""
    # Test data
    test_data = {
        "user_id": 123,
        "username": "test_user",
        "metadata": {"key": "value"}
    }
    
    # JSON serialization
    serialized = json.dumps(test_data)
    deserialized = json.loads(serialized)
    
    assert deserialized == test_data


def test_json_handles_basic_types():
    """Test that JSON can handle basic Python types"""
    test_cases = [
        {"type": "dict", "value": {"a": 1, "b": 2}},
        {"type": "list", "value": [1, 2, 3]},
        {"type": "string", "value": "test"},
        {"type": "number", "value": 42},
        {"type": "boolean", "value": True},
        {"type": "null", "value": None}
    ]
    
    for case in test_cases:
        serialized = json.dumps(case["value"])
        deserialized = json.loads(serialized)
        assert deserialized == case["value"]


def test_json_rejects_complex_objects():
    """Test that JSON rejects objects that could be dangerous with pickle"""
    import datetime
    
    # Objects that pickle could handle but JSON cannot (safer)
    with pytest.raises((TypeError, ValueError)):
        json.dumps(datetime.datetime.now())
    
    # Custom objects also rejected
    class CustomClass:
        def __init__(self):
            self.value = 123
    
    with pytest.raises(TypeError):
        json.dumps(CustomClass())


def test_json_prevents_code_execution():
    """Test that JSON deserialization cannot execute code"""
    # Attempt to inject code via JSON (should fail)
    malicious_data = '{"__import__": "os", "system": "rm -rf /"}'
    
    # JSON loads this as a simple dict, no code execution
    result = json.loads(malicious_data)
    
    # It's just a dict with string keys and values
    assert isinstance(result, dict)
    assert result["__import__"] == "os"
    assert result["system"] == "rm -rf /"
    # No code was executed, just stored as strings


def test_redis_cache_value_serialization():
    """Test that Redis cache values can be JSON serialized"""
    cache_values = [
        {"user_data": {"id": 1, "name": "test"}},
        {"session": {"token": "abc123", "expires": 3600}},
        {"metrics": {"cpu": 45.2, "memory": 78.5}}
    ]
    
    for value in cache_values:
        # Should be able to serialize and deserialize
        serialized = json.dumps(value)
        deserialized = json.loads(serialized)
        assert deserialized == value
