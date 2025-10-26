"""
Test suite for Phase 1: Core Integration
Tests agent management, task management, chat, and file upload features
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
    print("✓ Health check passed")

async def test_root_endpoint():
    """Test root endpoint"""
    print("\n=== Testing Root Endpoint ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
    print("✓ Root endpoint passed")

async def test_agent_lifecycle():
    """Test complete agent lifecycle"""
    print("\n=== Testing Agent Lifecycle ===")
    async with httpx.AsyncClient() as client:
        
        # Create agent
        print("\n1. Creating agent...")
        agent_data = {
            "name": "Test Developer Agent",
            "agent_type": "developer",
            "capabilities": [
                {
                    "name": "python",
                    "level": 8,
                    "description": "Python development"
                },
                {
                    "name": "testing",
                    "level": 7,
                    "description": "Test automation"
                }
            ],
            "metadata": {
                "department": "engineering",
                "location": "cloud"
            }
        }
        
        response = await client.post(f"{BASE_URL}/api/v1/agents", json=agent_data)
        print(f"Status: {response.status_code}")
        assert response.status_code == 201
        
        agent = response.json()
        agent_id = agent['id']
        print(f"Created agent ID: {agent_id}")
        print(f"Agent details: {json.dumps(agent, indent=2, default=str)}")
        
        # Get agent
        print(f"\n2. Retrieving agent {agent_id}...")
        response = await client.get(f"{BASE_URL}/api/v1/agents/{agent_id}")
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        print(f"Agent: {json.dumps(response.json(), indent=2, default=str)}")
        
        # List agents
        print("\n3. Listing all agents...")
        response = await client.get(f"{BASE_URL}/api/v1/agents")
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        agents = response.json()
        print(f"Total agents: {len(agents)}")
        
        # Update agent
        print(f"\n4. Updating agent {agent_id}...")
        update_data = {
            "status": "active",
            "metadata": {
                "department": "engineering",
                "location": "cloud",
                "updated": True
            }
        }
        response = await client.put(f"{BASE_URL}/api/v1/agents/{agent_id}", json=update_data)
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        updated_agent = response.json()
        print(f"Updated status: {updated_agent['status']}")
        
        # Delete agent
        print(f"\n5. Deleting agent {agent_id}...")
        response = await client.delete(f"{BASE_URL}/api/v1/agents/{agent_id}")
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        print(f"Response: {response.json()}")
        
    print("✓ Agent lifecycle test passed")

async def test_task_management():
    """Test task management"""
    print("\n=== Testing Task Management ===")
    async with httpx.AsyncClient() as client:
        
        # Create agent first
        print("\n1. Creating agent for task assignment...")
        agent_data = {
            "name": "Task Executor Agent",
            "agent_type": "analyst",
            "capabilities": [
                {"name": "data_analysis", "level": 9}
            ],
            "metadata": {}
        }
        response = await client.post(f"{BASE_URL}/api/v1/agents", json=agent_data)
        agent_id = response.json()['id']
        print(f"Created agent ID: {agent_id}")
        
        # Create task
        print("\n2. Creating task...")
        task_data = {
            "name": "Analyze Dataset",
            "description": "Analyze user behavior dataset",
            "task_type": "data_analysis",
            "parameters": {
                "dataset": "users_2024.csv",
                "metrics": ["engagement", "retention"]
            },
            "priority": "high",
            "agent_id": agent_id,
            "required_capabilities": ["data_analysis"]
        }
        
        response = await client.post(f"{BASE_URL}/api/v1/tasks", json=task_data)
        print(f"Status: {response.status_code}")
        assert response.status_code == 201
        
        task = response.json()
        task_id = task['id']
        print(f"Created task ID: {task_id}")
        print(f"Task details: {json.dumps(task, indent=2, default=str)}")
        
        # Get task
        print(f"\n3. Retrieving task {task_id}...")
        response = await client.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        
        # Update task status
        print(f"\n4. Updating task status...")
        update_data = {
            "status": "in_progress"
        }
        response = await client.put(
            f"{BASE_URL}/api/v1/tasks/{task_id}/status?status=in_progress"
        )
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        
        # Complete task
        print(f"\n5. Completing task...")
        response = await client.put(
            f"{BASE_URL}/api/v1/tasks/{task_id}/status?status=completed",
            json={
                "result": {
                    "engagement_rate": 0.78,
                    "retention_rate": 0.65
                }
            }
        )
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        completed_task = response.json()
        print(f"Task result: {completed_task.get('result')}")
        
        # List tasks for agent
        print(f"\n6. Listing tasks for agent {agent_id}...")
        response = await client.get(f"{BASE_URL}/api/v1/tasks?agent_id={agent_id}")
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        tasks = response.json()
        print(f"Total tasks for agent: {len(tasks)}")
        
    print("✓ Task management test passed")

async def test_chat_system():
    """Test chat system"""
    print("\n=== Testing Chat System ===")
    async with httpx.AsyncClient() as client:
        
        session_id = "test-session-123"
        
        # Send chat message
        print(f"\n1. Sending chat message to session {session_id}...")
        message_data = {
            "session_id": session_id,
            "content": "Hello! This is a test message.",
            "message_type": "user"
        }
        
        response = await client.post(f"{BASE_URL}/api/v1/chat/message", json=message_data)
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        print(f"Response: {response.json()}")
        
        # Send another message
        print(f"\n2. Sending agent response...")
        agent_message = {
            "session_id": session_id,
            "content": "Hello! I received your message.",
            "message_type": "agent"
        }
        
        response = await client.post(f"{BASE_URL}/api/v1/chat/message", json=agent_message)
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        
        # Get chat history
        print(f"\n3. Retrieving chat history for session {session_id}...")
        response = await client.get(f"{BASE_URL}/api/v1/chat/{session_id}/history")
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        
        history = response.json()
        print(f"Total messages: {history['count']}")
        print(f"Messages: {json.dumps(history['messages'], indent=2, default=str)}")
        
    print("✓ Chat system test passed")

async def test_file_management():
    """Test file upload and download"""
    print("\n=== Testing File Management ===")
    async with httpx.AsyncClient() as client:
        
        session_id = "file-test-session"
        
        # Create a test file
        print("\n1. Creating test file...")
        test_content = b"This is a test file content for Phase 1 integration testing."
        
        # Upload file
        print(f"\n2. Uploading file to session {session_id}...")
        files = {"file": ("test_file.txt", test_content, "text/plain")}
        
        response = await client.post(
            f"{BASE_URL}/api/v1/files/upload?session_id={session_id}&temporary=false",
            files=files
        )
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        
        file_info = response.json()
        file_id = file_info['file_id']
        print(f"Uploaded file ID: {file_id}")
        print(f"File info: {json.dumps(file_info, indent=2, default=str)}")
        
        # Get file metadata
        print(f"\n3. Retrieving file metadata for {file_id}...")
        response = await client.get(f"{BASE_URL}/api/v1/files/{file_id}/metadata")
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        metadata = response.json()
        print(f"Metadata: {json.dumps(metadata, indent=2, default=str)}")
        
        # Download file
        print(f"\n4. Downloading file {file_id}...")
        response = await client.get(f"{BASE_URL}/api/v1/files/{file_id}")
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        print(f"Downloaded {len(response.content)} bytes")
        
        # Delete file
        print(f"\n5. Deleting file {file_id}...")
        response = await client.delete(f"{BASE_URL}/api/v1/files/{file_id}")
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        print(f"Response: {response.json()}")
        
    print("✓ File management test passed")

async def test_statistics():
    """Test statistics endpoint"""
    print("\n=== Testing Statistics ===")
    async with httpx.AsyncClient() as client:
        
        response = await client.get(f"{BASE_URL}/api/v1/stats")
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        
        stats = response.json()
        print(f"Platform statistics:")
        print(json.dumps(stats, indent=2, default=str))
        
    print("✓ Statistics test passed")

async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("YMERA Platform - Phase 1 Integration Tests")
    print("="*80)
    
    try:
        await test_health_check()
        await test_root_endpoint()
        await test_agent_lifecycle()
        await test_task_management()
        await test_chat_system()
        await test_file_management()
        await test_statistics()
        
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
