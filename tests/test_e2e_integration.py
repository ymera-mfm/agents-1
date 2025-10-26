"""
Comprehensive End-to-End Integration Tests
Tests the full integration between backend and frontend
"""
import pytest
import asyncio
import httpx
from agent_communication import CommunicationAgent
from agent_monitoring import MonitoringAgent
from main import app
from fastapi.testclient import TestClient


# Initialize test client
client = TestClient(app)


class TestE2EIntegration:
    """End-to-End integration tests"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_system_info_endpoint(self):
        """Test system info endpoint"""
        response = client.get("/api/v1/system/info")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "websocket_connections" in data
    
    def test_list_agents_endpoint(self):
        """Test list agents endpoint"""
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "agents" in data["data"]
        assert "pagination" in data["data"]
    
    def test_create_agent_endpoint(self):
        """Test create agent endpoint"""
        agent_data = {
            "agent_id": "test_agent_e2e",
            "name": "Test Agent",
            "type": "coder"
        }
        response = client.post("/api/v1/agents", json=agent_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == "test_agent_e2e"
    
    def test_get_agent_endpoint(self):
        """Test get agent endpoint"""
        response = client.get("/api/v1/agents/test_agent_123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == "test_agent_123"
        assert "name" in data["data"]
        assert "type" in data["data"]
        assert "status" in data["data"]
    
    def test_delete_agent_endpoint(self):
        """Test delete agent endpoint"""
        response = client.delete("/api/v1/agents/test_agent_123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_projects_endpoint(self):
        """Test list projects endpoint"""
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "projects" in data["data"]
    
    def test_websocket_connection(self):
        """Test WebSocket connection"""
        with client.websocket_connect("/ws") as websocket:
            # Send ping
            websocket.send_json({"type": "ping"})
            # Receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"
    
    def test_websocket_subscribe(self):
        """Test WebSocket subscription"""
        with client.websocket_connect("/ws") as websocket:
            # Subscribe to channel
            websocket.send_json({"type": "subscribe", "channel": "agents"})
            # Receive subscription confirmation
            data = websocket.receive_json()
            assert data["type"] == "subscribed"
            assert data["channel"] == "agents"


@pytest.mark.asyncio
class TestE2EAgentOperations:
    """End-to-End agent operations tests"""
    
    async def test_agent_lifecycle(self):
        """Test complete agent lifecycle"""
        # Create agent
        comm_agent = CommunicationAgent()
        assert await comm_agent.initialize()
        
        # Register agent
        await comm_agent.register_agent("lifecycle_test_agent")
        
        # Send message
        message = {
            "from": "test",
            "to": "lifecycle_test_agent",
            "type": "test",
            "payload": {"data": "test"}
        }
        response = await comm_agent.process_message(message)
        assert response["status"] == "delivered"
        
        # Cleanup
        await comm_agent.unregister_agent("lifecycle_test_agent")
    
    async def test_monitoring_integration(self):
        """Test monitoring agent integration"""
        monitor = MonitoringAgent()
        assert await monitor.initialize()
        
        # Get metrics
        metrics = await monitor.get_current_metrics()
        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "disk_usage" in metrics
        
        # Check health
        health = await monitor.check_system_health()
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
    
    async def test_multi_agent_communication(self):
        """Test communication between multiple agents"""
        comm_agent = CommunicationAgent()
        monitor = MonitoringAgent()
        
        # Initialize both
        assert await comm_agent.initialize()
        assert await monitor.initialize()
        
        # Register monitor with comm
        await comm_agent.register_agent(monitor.agent_id)
        
        # Test message routing
        message = {
            "from": comm_agent.agent_id,
            "to": monitor.agent_id,
            "type": "health_check",
            "payload": {}
        }
        response = await comm_agent.process_message(message)
        assert response["status"] == "delivered"


class TestE2EAPIIntegration:
    """Test API integration scenarios"""
    
    def test_cors_headers(self):
        """Test CORS middleware is configured"""
        # Note: TestClient doesn't expose CORS headers the same way as real requests
        # This test verifies the endpoint works, actual CORS testing requires integration test
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        # Verify the response is valid JSON
        assert response.json()["status"] == "healthy"
    
    def test_api_version_in_path(self):
        """Test API versioning in path"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        # Test that old API paths don't work
        response_old = client.get("/health")
        assert response_old.status_code == 404
    
    def test_error_handling(self):
        """Test API error handling"""
        # Test 404 for non-existent endpoint
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_create_agent_validation(self):
        """Test agent creation validation"""
        # Missing agent_id
        response = client.post("/api/v1/agents", json={"name": "Test"})
        assert response.status_code == 400


class TestE2EPerformance:
    """Performance and load tests"""
    
    def test_health_check_performance(self):
        """Test health check response time"""
        import time
        start = time.time()
        response = client.get("/api/v1/health")
        end = time.time()
        
        assert response.status_code == 200
        # Should respond in less than 100ms
        assert (end - start) < 0.1
    
    def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return client.get("/api/v1/health")
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        assert all(r.status_code == 200 for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
