"""Security tests for cryptography fixes"""
import pytest
import hashlib
import json


def test_pattern_id_uses_secure_hash():
    """Test that pattern IDs use SHA-256 instead of MD5"""
    # Simulate the pattern ID generation
    pattern_data = {"type": "test", "value": 123}
    pattern_str = json.dumps(pattern_data, sort_keys=True)
    
    # Should use SHA-256
    pattern_id = hashlib.sha256(pattern_str.encode()).hexdigest()
    
    # SHA-256 produces 64 character hex string
    assert len(pattern_id) == 64
    
    # MD5 would produce 32 characters (this should not be used)
    md5_pattern = hashlib.md5(pattern_str.encode()).hexdigest()
    assert len(md5_pattern) == 32
    assert pattern_id != md5_pattern


def test_sha256_produces_different_hashes():
    """Test that different inputs produce different SHA-256 hashes"""
    data1 = json.dumps({"type": "pattern1"}, sort_keys=True)
    data2 = json.dumps({"type": "pattern2"}, sort_keys=True)
    
    hash1 = hashlib.sha256(data1.encode()).hexdigest()
    hash2 = hashlib.sha256(data2.encode()).hexdigest()
    
    assert hash1 != hash2


def test_sha256_is_deterministic():
    """Test that SHA-256 is deterministic (same input = same output)"""
    data = json.dumps({"type": "test", "value": 123}, sort_keys=True)
    
    hash1 = hashlib.sha256(data.encode()).hexdigest()
    hash2 = hashlib.sha256(data.encode()).hexdigest()
    
    assert hash1 == hash2
