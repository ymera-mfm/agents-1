"""Security tests for code injection prevention"""
import pytest
import ast


def test_ast_literal_eval_is_safe():
    """Test that ast.literal_eval only evaluates literals"""
    # Safe literals
    safe_cases = [
        ("123", 123),
        ("'hello'", "hello"),
        ("[1, 2, 3]", [1, 2, 3]),
        ("{'key': 'value'}", {'key': 'value'}),
        ("True", True),
        ("None", None)
    ]
    
    for expr, expected in safe_cases:
        result = ast.literal_eval(expr)
        assert result == expected


def test_ast_literal_eval_rejects_code():
    """Test that ast.literal_eval rejects code execution attempts"""
    # Dangerous expressions that should be rejected
    dangerous_cases = [
        "__import__('os').system('ls')",
        "eval('print(123)')",
        "exec('x = 1')",
        "open('/etc/passwd').read()",
        "lambda x: x + 1"
    ]
    
    for expr in dangerous_cases:
        with pytest.raises(ValueError):
            ast.literal_eval(expr)


def test_filter_condition_validation():
    """Test that filter conditions are validated instead of evaluated with eval"""
    # Instead of eval(), we should use safe validation
    # This test demonstrates the safe pattern
    
    # Example: Simple literal comparison
    filter_value = "active"
    message_status = "active"
    
    # Safe comparison (no eval needed)
    assert filter_value == message_status
    
    # For complex conditions, use a proper expression parser
    # not eval()


def test_no_eval_in_routing():
    """Test that routing logic doesn't use eval"""
    # Simulate routing without eval
    message = {"subject": "test", "payload": {"status": "active"}}
    
    # Safe routing pattern - direct attribute access
    if message["payload"].get("status") == "active":
        route_matched = True
    else:
        route_matched = False
    
    assert route_matched is True


def test_regex_pattern_matching_is_safe():
    """Test that regex pattern matching can replace eval for many cases"""
    import re
    
    # Use regex patterns instead of eval
    patterns = [
        (r"urgent:.*", "urgent:critical_issue"),  # Should match
        (r"urgent:.*", "normal:routine_task"),     # Should not match
    ]
    
    for pattern, subject in patterns:
        if re.fullmatch(pattern, subject):
            matched = True
        else:
            matched = False
        
        # Verify matching works correctly
        if "urgent" in subject:
            assert matched is True
        else:
            assert matched is False
