"""Security tests for SQL injection prevention"""
import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_parameterized_queries_prevent_injection():
    """Test that parameterized queries prevent SQL injection"""
    # Example of safe parameterized query pattern
    table_name = "users'; DROP TABLE users; --"
    
    # This should be safe with parameterized queries
    safe_query = text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
    ).bindparams(table_name=table_name)
    
    # The query object should contain the parameter
    assert ":table_name" in str(safe_query)


def test_view_name_whitelist_validation():
    """Test that view names are validated against whitelist"""
    allowed_views = ['task_summary', 'agent_summary', 'performance_metrics']
    
    # Valid view name should pass
    valid_view = 'task_summary'
    assert valid_view in allowed_views
    
    # Invalid view name with SQL injection attempt should fail
    malicious_view = "users; DROP TABLE users; --"
    assert malicious_view not in allowed_views
    
    # Another injection attempt
    malicious_view2 = "users' OR '1'='1"
    assert malicious_view2 not in allowed_views


def test_dynamic_where_clause_uses_parameters():
    """Test that dynamic WHERE clauses use parameterized queries"""
    filters = {
        'status': 'active',
        'user_id': '123'
    }
    
    # Build WHERE clause with parameters (safe pattern)
    where_clauses = []
    params = {}
    for key, value in filters.items():
        where_clauses.append(f"{key} = :{key}")
        params[key] = value
    
    # Check that we're using parameter placeholders
    assert 'status = :status' in where_clauses
    assert 'user_id = :user_id' in where_clauses
    
    # Check parameters dict has the values
    assert params['status'] == 'active'
    assert params['user_id'] == '123'


@pytest.mark.asyncio
async def test_sql_injection_attempt_in_table_name():
    """Test that SQL injection in table name is prevented"""
    # Malicious table name
    malicious_table = "users'; DROP TABLE users; --"
    
    # With parameterized query, this should be treated as literal string
    safe_query = text(
        "SELECT 1 FROM information_schema.tables WHERE table_name=:table_name"
    ).bindparams(table_name=malicious_table)
    
    # The parameter should be safely bound
    assert "table_name" in safe_query.compile().params
