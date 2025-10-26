"""Tests for metrics_agent module"""

import pytest
from unittest.mock import AsyncMock, Mock, patch


class TestMetricsAgent:
    """Test MetricsAgent class"""
    
    def test_metrics_agent_import(self):
        """Test that MetricsAgent can be imported"""
        from metrics_agent import MetricsAgent
        assert MetricsAgent is not None
        assert hasattr(MetricsAgent, '__init__')
    
    @pytest.mark.asyncio
    async def test_metrics_agent_initialization_mocked(self):
        """Test agent initialization with mocked dependencies"""
        with patch('base_agent.NATS'), \
             patch('base_agent.asyncpg.create_pool'), \
             patch('base_agent.consul.Consul'), \
             patch('redis.asyncio.from_url'):
            
            from metrics_agent import MetricsAgent
            from base_agent import AgentConfig
            config = AgentConfig(name="test_metrics_agent", enable_metrics_server=False)
            
            agent = MetricsAgent(config)
            assert agent.config.name == "test_metrics_agent"


class TestMetricsAgentMethods:
    """Test MetricsAgent methods"""
    
    @pytest.mark.asyncio
    async def test_agent_has_required_methods(self):
        """Test that agent has required methods"""
        with patch('base_agent.NATS'), \
             patch('base_agent.asyncpg.create_pool'), \
             patch('base_agent.consul.Consul'), \
             patch('redis.asyncio.from_url'):
            
            from metrics_agent import MetricsAgent
            from base_agent import AgentConfig
            config = AgentConfig(name="test_metrics", enable_metrics_server=False)
            agent = MetricsAgent(config)
            
            # Check for required methods from BaseAgent
            assert hasattr(agent, '_execute_task_impl')
            assert hasattr(agent, 'start')
            assert hasattr(agent, 'config')
