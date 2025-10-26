"""
Tests for agent checkpointing and recovery functionality
"""
import pytest
import asyncio
import json
import os
from datetime import datetime, timezone
from base_agent import BaseAgent, AgentState, MessageType


class MockStorageBackend:
    """Mock storage backend for testing"""
    def __init__(self):
        self.storage = {}
    
    async def set(self, key: str, value: str):
        self.storage[key] = value
    
    async def get(self, key: str):
        return self.storage.get(key)
    
    def clear(self):
        self.storage.clear()


class CheckpointTestAgent(BaseAgent):
    """Test agent for checkpoint testing"""
    def __init__(self, agent_id: str, config=None):
        super().__init__(agent_id, config)
        self.execution_count = 0
        self.custom_data = {"test": "data"}
    
    async def initialize(self) -> bool:
        return True
    
    async def process_message(self, message):
        return {"status": "processed"}
    
    async def execute(self):
        self.execution_count += 1
        await asyncio.sleep(0.01)
    
    async def get_checkpoint_state(self):
        """Save custom state"""
        return {
            "execution_count": self.execution_count,
            "custom_data": self.custom_data
        }
    
    async def restore_checkpoint_state(self, state):
        """Restore custom state"""
        self.execution_count = state.get("execution_count", 0)
        self.custom_data = state.get("custom_data", {})


@pytest.mark.asyncio
async def test_checkpoint_save_to_storage():
    """Test saving checkpoint to storage backend"""
    storage = MockStorageBackend()
    agent = CheckpointTestAgent("test_agent_1", {"checkpoint_interval": 1})
    agent.set_storage_backend(storage)
    
    await agent.initialize()
    agent.execution_count = 42
    agent.custom_data = {"important": "state"}
    
    # Save checkpoint
    result = await agent.save_checkpoint()
    assert result is True
    
    # Verify checkpoint was saved
    checkpoint_key = f"agent:checkpoint:{agent.agent_id}"
    checkpoint_data = await storage.get(checkpoint_key)
    assert checkpoint_data is not None
    
    data = json.loads(checkpoint_data)
    assert data["agent_id"] == "test_agent_1"
    assert data["state"] == AgentState.INITIALIZED.value
    assert data["custom_state"]["execution_count"] == 42
    assert data["custom_state"]["custom_data"]["important"] == "state"


@pytest.mark.asyncio
async def test_checkpoint_load_from_storage():
    """Test loading checkpoint from storage backend"""
    storage = MockStorageBackend()
    
    # Create and save checkpoint
    agent1 = CheckpointTestAgent("test_agent_2", {"checkpoint_interval": 1})
    agent1.set_storage_backend(storage)
    await agent1.initialize()
    agent1.execution_count = 100
    agent1.custom_data = {"test": "value"}
    await agent1.save_checkpoint()
    
    # Create new agent and load checkpoint
    agent2 = CheckpointTestAgent("test_agent_2", {"checkpoint_interval": 1})
    agent2.set_storage_backend(storage)
    result = await agent2.load_checkpoint()
    
    assert result is True
    assert agent2.execution_count == 100
    assert agent2.custom_data["test"] == "value"


@pytest.mark.asyncio
async def test_checkpoint_save_to_file():
    """Test saving checkpoint to file when no storage backend"""
    agent = CheckpointTestAgent("test_agent_file", {"checkpoint_interval": 1})
    agent.execution_count = 50
    
    # Save checkpoint (should use file fallback)
    result = await agent.save_checkpoint()
    assert result is True
    
    # Verify file was created
    checkpoint_file = f"/tmp/agent_checkpoint_{agent.agent_id}.json"
    assert os.path.exists(checkpoint_file)
    
    # Load and verify contents
    with open(checkpoint_file, 'r') as f:
        data = json.load(f)
    
    assert data["agent_id"] == "test_agent_file"
    assert data["custom_state"]["execution_count"] == 50
    
    # Cleanup
    os.remove(checkpoint_file)


@pytest.mark.asyncio
async def test_checkpoint_load_from_file():
    """Test loading checkpoint from file"""
    agent_id = "test_agent_file_load"
    
    # Create and save checkpoint
    agent1 = CheckpointTestAgent(agent_id, {"checkpoint_interval": 1})
    agent1.execution_count = 75
    await agent1.save_checkpoint()
    
    # Create new agent and load checkpoint
    agent2 = CheckpointTestAgent(agent_id, {"checkpoint_interval": 1})
    result = await agent2.load_checkpoint()
    
    assert result is True
    assert agent2.execution_count == 75
    
    # Cleanup
    checkpoint_file = f"/tmp/agent_checkpoint_{agent_id}.json"
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)


@pytest.mark.asyncio
async def test_checkpoint_load_nonexistent():
    """Test loading checkpoint when none exists"""
    agent = CheckpointTestAgent("nonexistent_agent")
    result = await agent.load_checkpoint()
    assert result is False


@pytest.mark.asyncio
async def test_should_checkpoint():
    """Test checkpoint interval logic"""
    agent = CheckpointTestAgent("test_agent_interval", {"checkpoint_interval": 0.1})
    
    # Should not checkpoint immediately
    assert await agent.should_checkpoint() is False
    
    # Wait for interval to pass
    await asyncio.sleep(0.15)
    
    # Should checkpoint now
    assert await agent.should_checkpoint() is True
    
    # Save checkpoint
    await agent.save_checkpoint()
    
    # Should not checkpoint immediately after save
    assert await agent.should_checkpoint() is False


@pytest.mark.asyncio
async def test_checkpoint_on_error():
    """Test that checkpoint is saved when agent encounters error"""
    storage = MockStorageBackend()
    
    class ErrorAgent(CheckpointTestAgent):
        async def execute(self):
            self.execution_count += 1
            if self.execution_count == 3:
                raise ValueError("Test error")
            await asyncio.sleep(0.01)
    
    agent = ErrorAgent("error_agent", {"checkpoint_interval": 1})
    agent.set_storage_backend(storage)
    
    # Start agent and let it fail
    try:
        await asyncio.wait_for(agent.start(), timeout=1.0)
    except (ValueError, RuntimeError, asyncio.TimeoutError):
        pass
    
    # Verify checkpoint was saved before error
    checkpoint_key = f"agent:checkpoint:{agent.agent_id}"
    checkpoint_data = await storage.get(checkpoint_key)
    assert checkpoint_data is not None


@pytest.mark.asyncio
async def test_checkpoint_on_stop():
    """Test that checkpoint is saved when agent stops gracefully"""
    storage = MockStorageBackend()
    agent = CheckpointTestAgent("stop_agent", {"checkpoint_interval": 10})
    agent.set_storage_backend(storage)
    
    await agent.initialize()
    agent.execution_count = 25
    agent.state = AgentState.RUNNING
    
    # Stop agent
    await agent.stop()
    
    # Verify checkpoint was saved
    checkpoint_key = f"agent:checkpoint:{agent.agent_id}"
    checkpoint_data = await storage.get(checkpoint_key)
    assert checkpoint_data is not None
    
    data = json.loads(checkpoint_data)
    assert data["custom_state"]["execution_count"] == 25


@pytest.mark.asyncio
async def test_agent_status_includes_checkpoint():
    """Test that agent status includes checkpoint information"""
    agent = CheckpointTestAgent("status_agent", {"checkpoint_interval": 1})
    await agent.initialize()
    await agent.save_checkpoint()
    
    status = agent.get_status()
    assert "last_checkpoint" in status
    assert status["last_checkpoint"] is not None
    
    # Verify it's a valid ISO timestamp
    checkpoint_time = datetime.fromisoformat(status["last_checkpoint"])
    assert checkpoint_time.tzinfo is not None
