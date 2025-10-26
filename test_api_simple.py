"""
Simple API Test Script
Tests API endpoints without full database setup
"""
import httpx
import asyncio
import sys

async def test_endpoints():
    """Test all API endpoints"""
    base_url = "http://127.0.0.1:8000"
    api_prefix = "/api/v1"
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("Testing /health...")
        response = await client.get(f"{base_url}{api_prefix}/health")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test system info
        print("\nTesting /system/info...")
        response = await client.get(f"{base_url}{api_prefix}/system/info")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test auth login
        print("\nTesting /auth/login...")
        response = await client.post(
            f"{base_url}{api_prefix}/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test list agents
        print("\nTesting /agents...")
        response = await client.get(f"{base_url}{api_prefix}/agents")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test create agent
        print("\nTesting POST /agents...")
        response = await client.post(
            f"{base_url}{api_prefix}/agents",
            json={
                "agent_id": "test_agent_123",
                "name": "Test Agent",
                "type": "coder"
            }
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test get agent
        print("\nTesting GET /agents/test_agent_123...")
        response = await client.get(f"{base_url}{api_prefix}/agents/test_agent_123")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test update agent
        print("\nTesting PUT /agents/test_agent_123...")
        response = await client.put(
            f"{base_url}{api_prefix}/agents/test_agent_123",
            json={"name": "Updated Agent", "config": {"max_tasks": 10}}
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test search agents
        print("\nTesting /agents/search...")
        response = await client.get(f"{base_url}{api_prefix}/agents/search?q=coder")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test bulk create
        print("\nTesting POST /agents/bulk...")
        response = await client.post(
            f"{base_url}{api_prefix}/agents/bulk",
            json={
                "agents": [
                    {"agent_id": "bulk_1", "name": "Bulk Agent 1", "type": "coder"},
                    {"agent_id": "bulk_2", "name": "Bulk Agent 2", "type": "analyst"}
                ]
            }
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test export
        print("\nTesting /agents/export...")
        response = await client.get(f"{base_url}{api_prefix}/agents/export?format=json")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test metrics
        print("\nTesting /metrics...")
        response = await client.get(f"{base_url}{api_prefix}/metrics")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test analytics
        print("\nTesting /analytics...")
        response = await client.get(
            f"{base_url}{api_prefix}/analytics",
            params={
                "start_date": "2025-10-01",
                "end_date": "2025-10-26",
                "group_by": "type",
                "metrics": "count,avg_execution_time"
            }
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test projects
        print("\nTesting /projects...")
        response = await client.get(f"{base_url}{api_prefix}/projects")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test delete agent
        print("\nTesting DELETE /agents/test_agent_123...")
        response = await client.delete(f"{base_url}{api_prefix}/agents/test_agent_123")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        print("\n✓ All endpoint tests completed successfully!")

if __name__ == "__main__":
    try:
        asyncio.run(test_endpoints())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
