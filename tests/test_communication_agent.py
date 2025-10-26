"""Tests for communication_agent module"""

import pytest
from unittest.mock import AsyncMock, Mock, patch


class TestCommunicationAgent:
    """Test CommunicationAgent class"""
    
    def test_communication_agent_import(self):
        """Test that CommunicationAgent can be imported"""
        from communication_agent import CommunicationAgent
        assert CommunicationAgent is not None
        assert hasattr(CommunicationAgent, '__init__')
    
    @pytest.mark.asyncio
    async def test_communication_agent_initialization_mocked(self):
        """Test agent initialization with mocked dependencies"""
        with patch('base_agent.NATS'), \
             patch('base_agent.asyncpg.create_pool'), \
             patch('base_agent.consul.Consul'), \
             patch('redis.asyncio.from_url'):
            
            from communication_agent import CommunicationAgent
            from base_agent import AgentConfig
            config = AgentConfig(name="test_comm_agent", enable_metrics_server=False)
            
            agent = CommunicationAgent(config)
            assert agent.config.name == "test_comm_agent"


class TestCommunicationAgentMethods:
    """Test CommunicationAgent methods"""
    
    @pytest.mark.asyncio
    async def test_agent_has_required_methods(self):
        """Test that agent has required methods"""
        with patch('base_agent.NATS'), \
             patch('base_agent.asyncpg.create_pool'), \
             patch('base_agent.consul.Consul'), \
             patch('redis.asyncio.from_url'):
            
            from communication_agent import CommunicationAgent
            from base_agent import AgentConfig
            config = AgentConfig(name="test_comm", enable_metrics_server=False)
            agent = CommunicationAgent(config)
            
            # Check for required methods from BaseAgent
            assert hasattr(agent, '_execute_task_impl')
            assert hasattr(agent, 'start')
            assert hasattr(agent, 'config')
