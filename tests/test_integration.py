"""
Integration tests for the YMERA system
"""
import pytest
import asyncio
from agent_communication import CommunicationAgent
from agent_monitoring import MonitoringAgent


@pytest.mark.asyncio
async def test_agent_communication():
    """Test communication between agents"""
    comm_agent = CommunicationAgent()
    
    # Initialize
    assert await comm_agent.initialize()
    
    # Register a test agent
    await comm_agent.register_agent("test_agent_1")
    
    # Process a message
    message = {
        "from": "sender",
        "to": "test_agent_1",
        "type": "request",
        "payload": {"action": "test"}
    }
    
    response = await comm_agent.process_message(message)
    assert response["status"] == "delivered"
    
    # Check message count
    assert comm_agent.get_message_count() == 1


@pytest.mark.asyncio
async def test_monitoring_agent():
    """Test monitoring agent"""
    monitor = MonitoringAgent()
    
    # Initialize
    assert await monitor.initialize()
    
    # Execute monitoring cycle
    task = asyncio.create_task(monitor.execute())
    await asyncio.sleep(1)
    task.cancel()
    
    # Get metrics
    metrics = await monitor.get_current_metrics()
    assert "cpu_percent" in metrics
    assert "memory_percent" in metrics
    
    # Check health
    health = await monitor.check_system_health()
    assert health["status"] in ["healthy", "degraded"]


@pytest.mark.asyncio
async def test_multi_agent_system():
    """Test multiple agents working together"""
    comm_agent = CommunicationAgent()
    monitor = MonitoringAgent()
    
    # Initialize both agents
    assert await comm_agent.initialize()
    assert await monitor.initialize()
    
    # Register monitoring agent with communication agent
    await comm_agent.register_agent(monitor.agent_id)
    
    # Send health check request
    health_request = {
        "from": comm_agent.agent_id,
        "to": monitor.agent_id,
        "type": "get_health",
        "payload": {}
    }
    
    response = await comm_agent.process_message(health_request)
    assert response["status"] == "delivered"
