"""
Tests for Base Agent functionality
"""
import pytest
import asyncio
from typing import Any, Dict, Optional

from base_agent import BaseAgent, AgentState, MessageType


class TestAgent(BaseAgent):
    """Test implementation of BaseAgent"""
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.initialized = False
        self.execution_count = 0
        
    async def initialize(self) -> bool:
        self.initialized = True
        return True
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return {"status": "processed", "message_id": message.get("id")}
    
    async def execute(self) -> Any:
        self.execution_count += 1
        if self.execution_count >= 3:
            await self.stop()
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initialization"""
    agent = TestAgent("test_agent_1")
    assert agent.agent_id == "test_agent_1"
    assert agent.state == AgentState.INITIALIZED
    assert not agent.initialized


@pytest.mark.asyncio
async def test_agent_start_stop():
    """Test agent start and stop"""
    agent = TestAgent("test_agent_2")
    
    # Start agent in background
    task = asyncio.create_task(agent.start())
    
    # Wait a bit
    await asyncio.sleep(0.5)
    
    # Stop agent
    await agent.stop()
    
    # Wait for task to complete
    try:
        await asyncio.wait_for(task, timeout=2.0)
    except asyncio.TimeoutError:
        pass
    
    assert agent.initialized
    assert agent.state == AgentState.STOPPED


@pytest.mark.asyncio
async def test_agent_message_processing():
    """Test agent message processing"""
    agent = TestAgent("test_agent_3")
    await agent.initialize()
    
    message = {
        "id": "msg_1",
        "type": "test",
        "payload": {"data": "test"}
    }
    
    response = await agent.process_message(message)
    assert response["status"] == "processed"
    assert response["message_id"] == "msg_1"


@pytest.mark.asyncio
async def test_agent_status():
    """Test agent status reporting"""
    agent = TestAgent("test_agent_4", config={"key": "value"})
    status = agent.get_status()
    
    assert status["agent_id"] == "test_agent_4"
    assert status["state"] == AgentState.INITIALIZED.value
    assert status["config"]["key"] == "value"


@pytest.mark.asyncio
async def test_agent_message_queue():
    """Test agent message queuing"""
    agent = TestAgent("test_agent_5")
    
    message = {"id": "msg_1", "data": "test"}
    await agent.receive_message(message)
    
    assert not agent.message_queue.empty()
    queued_msg = await agent.message_queue.get()
    assert queued_msg["id"] == "msg_1"
