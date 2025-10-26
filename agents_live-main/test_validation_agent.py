"""Tests for validation_agent module"""

import pytest
from unittest.mock import AsyncMock, Mock, patch


class TestValidationAgent:
    """Test ValidationAgent class"""
    
    def test_validation_agent_import(self):
        """Test that ValidationAgent can be imported"""
        from validation_agent import ValidationAgent
        assert ValidationAgent is not None
        assert hasattr(ValidationAgent, '__init__')
    
    @pytest.mark.asyncio
    async def test_validation_agent_initialization_mocked(self):
        """Test agent initialization with mocked dependencies"""
        with patch('base_agent.NATS') as mock_nats, \
             patch('base_agent.asyncpg.create_pool') as mock_pg, \
             patch('base_agent.consul.Consul') as mock_consul, \
             patch('redis.asyncio.from_url') as mock_redis:
            
            # Setup mocks
            mock_nats.return_value = AsyncMock()
            mock_pg.return_value = AsyncMock()
            mock_consul.return_value = Mock()
            mock_redis.return_value = AsyncMock()
            
            from validation_agent import ValidationAgent
            from base_agent import AgentConfig
            config = AgentConfig(name="test_validation_agent", enable_metrics_server=False)
            
            agent = ValidationAgent(config)
            assert agent.config.name == "test_validation_agent"


class TestValidationAgentMethods:
    """Test ValidationAgent methods"""
    
    @pytest.mark.asyncio
    async def test_agent_has_required_methods(self):
        """Test that agent has required methods"""
        with patch('base_agent.NATS'), \
             patch('base_agent.asyncpg.create_pool'), \
             patch('base_agent.consul.Consul'), \
             patch('redis.asyncio.from_url'):
            
            from validation_agent import ValidationAgent
            from base_agent import AgentConfig
            config = AgentConfig(name="test_validation", enable_metrics_server=False)
            agent = ValidationAgent(config)
            
            # Check for required methods from BaseAgent
            assert hasattr(agent, '_execute_task_impl')
            assert hasattr(agent, 'start')
            assert hasattr(agent, 'config')
