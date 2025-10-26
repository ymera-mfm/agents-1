"""Tests for security_agent module"""

import pytest
from unittest.mock import AsyncMock, Mock, patch


class TestSecurityAgent:
    """Test SecurityAgent class"""
    
    def test_security_agent_import(self):
        """Test that SecurityAgent can be imported"""
        from security_agent import SecurityAgent
        assert SecurityAgent is not None
        assert hasattr(SecurityAgent, '__init__')
    
    @pytest.mark.asyncio
    async def test_security_agent_initialization_mocked(self):
        """Test agent initialization with mocked dependencies"""
        from cryptography.fernet import Fernet
        mock_key = Fernet.generate_key()
        
        with patch('base_agent.NATS'), \
             patch('base_agent.asyncpg.create_pool'), \
             patch('base_agent.consul.Consul'), \
             patch('redis.asyncio.from_url'), \
             patch('builtins.open', create=True) as mock_open:
            
            # Mock file read to return a valid Fernet key
            mock_open.return_value.__enter__.return_value.read.return_value = mock_key
            
            from security_agent import SecurityAgent
            from base_agent import AgentConfig
            config = AgentConfig(name="test_security_agent", enable_metrics_server=False)
            
            agent = SecurityAgent(config)
            assert agent.config.name == "test_security_agent"


class TestSecurityAgentMethods:
    """Test SecurityAgent methods"""
    
    @pytest.mark.asyncio
    async def test_agent_has_required_methods(self):
        """Test that agent has required methods"""
        from cryptography.fernet import Fernet
        mock_key = Fernet.generate_key()
        
        with patch('base_agent.NATS'), \
             patch('base_agent.asyncpg.create_pool'), \
             patch('base_agent.consul.Consul'), \
             patch('redis.asyncio.from_url'), \
             patch('builtins.open', create=True) as mock_open:
            
            # Mock file read to return a valid Fernet key
            mock_open.return_value.__enter__.return_value.read.return_value = mock_key
            
            from security_agent import SecurityAgent
            from base_agent import AgentConfig
            config = AgentConfig(name="test_security", enable_metrics_server=False)
            agent = SecurityAgent(config)
            
            # Check for required methods from BaseAgent
            assert hasattr(agent, '_execute_task_impl')
            assert hasattr(agent, 'start')
            assert hasattr(agent, 'config')
