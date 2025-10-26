# tests/security/test_security.py
import pytest
from fastapi import status
from security_headers import secure_headers
import json

class TestSecurityHeaders:
    """Test security headers are properly set"""
    
    @pytest.mark.asyncio
    async def test_security_headers_present(self, test_client):
        """Test that security headers are present in responses"""
        response = test_client.get("/health")
        
        # Check essential security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        
        assert "Strict-Transport-Security" in response.headers
        assert "Referrer-Policy" in response.headers

class TestAPISecurity:
    """Test API security features"""
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_client, test_user):
        """Test rate limiting functionality"""
        user = await test_user()
        
        # Make rapid requests to trigger rate limiting
        for i in range(15):  # Should trigger rate limit
            response = test_client.post("/auth/login", json={
                "username": "testuser",
                "password": "wrongpassword"  # Use wrong password to avoid success
            })
            
            if response.status_code == 429:  # Rate limited
                assert "Retry-After" in response.headers
                break
        else:
            pytest.fail("Rate limiting was not triggered")
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, test_client, test_user, auth_headers):
        """Test SQL injection prevention"""
        user = await test_user()
        headers = await auth_headers(user)
        
        # Attempt SQL injection in project name
        malicious_name = "Test'; DROP TABLE users; --"
        response = test_client.post("/projects", json={
            "name": malicious_name,
            "status": "active"
        }, headers=headers)
        
        # Should either succeed (with sanitized input) or fail gracefully
        assert response.status_code in [201, 400, 422]
        
        # Verify users table still exists by querying it
        users_response = test_client.get("/users", headers=headers)
        assert users_response.status_code != 500  # Should not cause server error
    
    @pytest.mark.asyncio
    async def test_xss_prevention(self, test_client, test_user, auth_headers):
        """Test XSS prevention"""
        user = await test_user()
        headers = await auth_headers(user)
        
        # Attempt XSS in project description
        xss_payload = "<script>alert('XSS')</script>"
        response = test_client.post("/projects", json={
            "name": "XSS Test Project",
            "description": xss_payload,
            "status": "active"
        }, headers=headers)
        
        # Should succeed but sanitize the input
        assert response.status_code == 201
        
        # Check that the response doesn't contain the script tags
        project_response = test_client.get(
            f"/projects/{response.json()['id']}", 
            headers=headers
        )
        
        assert "<script>" not in project_response.json()["description"]
        assert "&lt;script&gt;" in project_response.json()["description"]  # Should be HTML encoded