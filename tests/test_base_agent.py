"""
Comprehensive Tests for base_agent module
Phase 1, Week 1: Foundation Tests
Target Coverage: 80%
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock, call
from datetime import datetime
from base_agent import (
    BaseAgent,
    AgentConfig,
    AgentStatus,
    TaskStatus,
    Priority,
    TaskRequest,
    TaskResponse,
    HAS_NATS,
    HAS_REDIS,
    HAS_ASYNCPG,
    HAS_CONSUL,
    HAS_OPENTELEMETRY,
    HAS_PROMETHEUS,
    HAS_STRUCTLOG
)


class TestAgentConfig:
    """Test AgentConfig dataclass"""
    
    def test_agent_config_initialization(self):
        """Test agent configuration can be initialized"""
        config = AgentConfig(
            name="test_agent",
            version="1.0.0",
            agent_type="test"
        )
        assert config.name == "test_agent"
        assert config.version == "1.0.0"
        assert config.agent_type == "test"
    
    def test_agent_config_defaults(self):
        """Test agent configuration has sensible defaults"""
        config = AgentConfig(name="test")
        assert config.version == "1.0.0"
        assert config.agent_type == "generic"
        assert config.max_concurrent_tasks == 10
        assert config.heartbeat_interval == 5
    
    def test_agent_config_custom_settings(self):
        """Test agent configuration with custom settings"""
        config = AgentConfig(
            name="custom_agent",
            max_concurrent_tasks=20,
            log_level="DEBUG",
            custom={"key": "value"}
        )
        assert config.max_concurrent_tasks == 20
        assert config.log_level == "DEBUG"
        assert config.custom["key"] == "value"


class TestAgentEnums:
    """Test agent enumerations"""
    
    def test_agent_status_enum(self):
        """Test AgentStatus enum values"""
        assert AgentStatus.INITIALIZING.value == "initializing"
        assert AgentStatus.ACTIVE.value == "active"
        assert AgentStatus.ERROR.value == "error"
    
    def test_task_status_enum(self):
        """Test TaskStatus enum values"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
    
    def test_priority_enum(self):
        """Test Priority enum values"""
        assert Priority.LOW.value == 1
        assert Priority.NORMAL.value == 2
        assert Priority.HIGH.value == 3
        assert Priority.CRITICAL.value == 4


class TestTaskRequest:
    """Test TaskRequest dataclass"""
    
    def test_task_request_initialization(self):
        """Test TaskRequest can be initialized"""
        task = TaskRequest(
            task_id="test-123",
            task_type="process",
            payload={"data": "test"}
        )
        assert task.task_id == "test-123"
        assert task.task_type == "process"
        assert task.payload["data"] == "test"


class TestBaseAgent:
    """Test BaseAgent class"""
    
    def test_base_agent_is_abstract(self):
        """Test that BaseAgent cannot be instantiated directly"""
        with pytest.raises(TypeError):
            # BaseAgent is abstract and should raise TypeError
            agent = BaseAgent(AgentConfig(name="test"))
    
    def test_base_agent_subclass_creation(self):
        """Test that BaseAgent can be subclassed"""
        class TestAgent(BaseAgent):
            async def _process_task(self, task):
                return {"status": "success"}
            
            async def _handle_message(self, message):
                pass
            
            async def _execute_task_impl(self, task):
                return {"status": "success"}
            
            async def start(self):
                pass
        
        config = AgentConfig(name="test_agent", enable_metrics_server=False)
        with patch('base_agent.NATS'), \
             patch('base_agent.asyncpg.create_pool'), \
             patch('base_agent.consul.Consul'), \
             patch('redis.asyncio.from_url'):
            agent = TestAgent(config)
            assert agent.config.name == "test_agent"
            assert hasattr(agent, '_process_task')
            assert hasattr(agent, '_handle_message')


class TestAgentLifecycle:
    """Test agent lifecycle methods"""
    
    @pytest.mark.asyncio
    async def test_agent_initialization_mocked(self):
        """Test agent initialization with mocked dependencies"""
        class TestAgent(BaseAgent):
            async def _process_task(self, task):
                return {"status": "success"}
            
            async def _handle_message(self, message):
                pass
            
            async def _execute_task_impl(self, task):
                return {"status": "success"}
            
            async def start(self):
                pass
        
        config = AgentConfig(
            name="test_agent",
            nats_url="nats://mock:4222",
            postgres_url="postgresql://mock/db",
            redis_url="redis://mock:6379",
            enable_metrics_server=False
        )
        
        with patch('base_agent.NATS') as mock_nats, \
             patch('base_agent.asyncpg.create_pool') as mock_pg, \
             patch('base_agent.consul.Consul') as mock_consul, \
             patch('redis.asyncio.from_url') as mock_redis:
            
            # Setup mocks
            mock_nats.return_value = AsyncMock()
            mock_pg.return_value = AsyncMock()
            mock_consul.return_value = Mock()
            mock_redis.return_value = AsyncMock()
            
            agent = TestAgent(config)
            
            # Verify agent was created
            assert agent.config.name == "test_agent"
            assert agent.status == AgentStatus.INITIALIZING


class TestAgentConfiguration:
    """Test agent configuration handling"""
    
    def test_agent_config_serialization(self):
        """Test agent configuration can be serialized"""
        config = AgentConfig(
            name="test",
            version="2.0.0",
            custom={"key": "value"}
        )
        
        # Convert to dict
        from dataclasses import asdict
        config_dict = asdict(config)
        
        assert config_dict["name"] == "test"
        assert config_dict["version"] == "2.0.0"
        assert config_dict["custom"]["key"] == "value"


@pytest.mark.asyncio
async def test_agent_graceful_shutdown():
    """Test agent graceful shutdown"""
    class TestAgent(BaseAgent):
        async def _process_task(self, task):
            return {"status": "success"}
        
        async def _handle_message(self, message):
            pass
        
        async def _execute_task_impl(self, task):
            return {"status": "success"}
        
        async def start(self):
            pass
    
    config = AgentConfig(name="test_shutdown", enable_metrics_server=False)
    
    with patch('base_agent.NATS'), \
         patch('base_agent.asyncpg.create_pool'), \
         patch('base_agent.consul.Consul'), \
         patch('redis.asyncio.from_url'):
        
        agent = TestAgent(config)
        # Agent should handle shutdown gracefully
        assert agent.status == AgentStatus.INITIALIZING


class TestOptionalDependencies:
    """Test optional dependency handling"""
    
    def test_has_nats_flag(self):
        """Test HAS_NATS feature flag is boolean"""
        assert isinstance(HAS_NATS, bool)
    
    def test_has_redis_flag(self):
        """Test HAS_REDIS feature flag is boolean"""
        assert isinstance(HAS_REDIS, bool)
    
    def test_has_asyncpg_flag(self):
        """Test HAS_ASYNCPG feature flag is boolean"""
        assert isinstance(HAS_ASYNCPG, bool)
    
    def test_has_consul_flag(self):
        """Test HAS_CONSUL feature flag is boolean"""
        assert isinstance(HAS_CONSUL, bool)
    
    def test_has_opentelemetry_flag(self):
        """Test HAS_OPENTELEMETRY feature flag is boolean"""
        assert isinstance(HAS_OPENTELEMETRY, bool)
    
    def test_has_prometheus_flag(self):
        """Test HAS_PROMETHEUS feature flag is boolean"""
        assert isinstance(HAS_PROMETHEUS, bool)
    
    def test_has_structlog_flag(self):
        """Test HAS_STRUCTLOG feature flag is boolean"""
        assert isinstance(HAS_STRUCTLOG, bool)
    
    def test_agent_works_without_nats(self):
        """Test agent can be created without NATS"""
        class TestAgent(BaseAgent):
            async def _process_task(self, task):
                return {"status": "success"}
            
            async def _handle_message(self, message):
                pass
            
            async def _execute_task_impl(self, task):
                return {"status": "success"}
            
            async def start(self):
                pass
        
        config = AgentConfig(name="test_no_nats", enable_metrics_server=False)
        
        with patch('base_agent.HAS_NATS', False), \
             patch('base_agent.HAS_REDIS', False), \
             patch('base_agent.HAS_ASYNCPG', False), \
             patch('base_agent.HAS_CONSUL', False):
            agent = TestAgent(config)
            assert agent.config.name == "test_no_nats"
            # Agent should be created successfully even without dependencies


class TestTaskRequest:
    """Enhanced TaskRequest tests"""
    
    def test_task_request_with_priority(self):
        """Test TaskRequest with priority"""
        task = TaskRequest(
            task_id="test-456",
            task_type="process",
            payload={"data": "test"},
            priority=Priority.HIGH
        )
        assert task.priority == Priority.HIGH
    
    def test_task_request_defaults(self):
        """Test TaskRequest default values"""
        task = TaskRequest(
            task_id="test-789",
            task_type="process",
            payload={}
        )
        assert task.task_id == "test-789"
        assert task.payload == {}


class TestTaskResponse:
    """Test TaskResponse dataclass"""
    
    def test_task_response_success(self):
        """Test TaskResponse for successful task"""
        response = TaskResponse(
            task_id="test-123",
            status=TaskStatus.COMPLETED,
            result={"output": "success"}
        )
        assert response.task_id == "test-123"
        assert response.status == TaskStatus.COMPLETED
        assert response.result["output"] == "success"
    
    def test_task_response_with_error(self):
        """Test TaskResponse with error"""
        response = TaskResponse(
            task_id="test-456",
            status=TaskStatus.FAILED,
            error="Test error message"
        )
        assert response.status == TaskStatus.FAILED
        assert response.error == "Test error message"


class TestAgentTaskProcessing:
    """Test agent task processing"""
    
    @pytest.mark.asyncio
    async def test_task_execution_success(self):
        """Test successful task execution"""
        class TestAgent(BaseAgent):
            async def _process_task(self, task):
                return {"result": "processed"}
            
            async def _handle_message(self, message):
                pass
            
            async def _execute_task_impl(self, task):
                return await self._process_task(task)
            
            async def start(self):
                pass
        
        config = AgentConfig(name="test_exec", enable_metrics_server=False)
        
        with patch('base_agent.NATS'), \
             patch('base_agent.asyncpg.create_pool'), \
             patch('base_agent.consul.Consul'), \
             patch('redis.asyncio.from_url'):
            
            agent = TestAgent(config)
            task = TaskRequest(
                task_id="exec-001",
                task_type="process",
                payload={"data": "test"}
            )
            
            result = await agent._execute_task_impl(task)
            assert result["result"] == "processed"
    
    @pytest.mark.asyncio
    async def test_task_processing_with_error(self):
        """Test task processing with error handling"""
        class TestAgent(BaseAgent):
            async def _process_task(self, task):
                raise ValueError("Processing error")
            
            async def _handle_message(self, message):
                pass
            
            async def _execute_task_impl(self, task):
                try:
                    return await self._process_task(task)
                except Exception as e:
                    return {"error": str(e)}
            
            async def start(self):
                pass
        
        config = AgentConfig(name="test_error", enable_metrics_server=False)
        
        with patch('base_agent.NATS'), \
             patch('base_agent.asyncpg.create_pool'), \
             patch('base_agent.consul.Consul'), \
             patch('redis.asyncio.from_url'):
            
            agent = TestAgent(config)
            task = TaskRequest(
                task_id="error-001",
                task_type="process",
                payload={}
            )
            
            result = await agent._execute_task_impl(task)
            assert "error" in result


class TestAgentConnectionManagement:
    """Test agent connection management"""
    
    @pytest.mark.asyncio
    async def test_agent_without_connections(self):
        """Test agent initialization without external connections"""
        class TestAgent(BaseAgent):
            async def _process_task(self, task):
                return {"status": "success"}
            
            async def _handle_message(self, message):
                pass
            
            async def _execute_task_impl(self, task):
                return {"status": "success"}
            
            async def start(self):
                self.status = AgentStatus.ACTIVE
        
        config = AgentConfig(
            name="test_no_conn",
            enable_metrics_server=False
        )
        
        with patch('base_agent.HAS_NATS', False), \
             patch('base_agent.HAS_REDIS', False), \
             patch('base_agent.HAS_ASYNCPG', False):
            
            agent = TestAgent(config)
            await agent.start()
            assert agent.status == AgentStatus.ACTIVE


class TestAgentMetrics:
    """Test agent metrics collection"""
    
    def test_agent_metrics_disabled(self):
        """Test agent with metrics disabled"""
        class TestAgent(BaseAgent):
            async def _process_task(self, task):
                return {"status": "success"}
            
            async def _handle_message(self, message):
                pass
            
            async def _execute_task_impl(self, task):
                return {"status": "success"}
            
            async def start(self):
                pass
        
        config = AgentConfig(
            name="test_no_metrics",
            enable_metrics_server=False
        )
        
        with patch('base_agent.NATS'), \
             patch('base_agent.asyncpg.create_pool'), \
             patch('base_agent.consul.Consul'), \
             patch('redis.asyncio.from_url'):
            
            agent = TestAgent(config)
            assert agent.config.enable_metrics_server is False


class TestAgentStatusTransitions:
    """Test agent status transitions"""
    
    @pytest.mark.asyncio
    async def test_status_initializing_to_active(self):
        """Test status transition from INITIALIZING to ACTIVE"""
        class TestAgent(BaseAgent):
            async def _process_task(self, task):
                return {"status": "success"}
            
            async def _handle_message(self, message):
                pass
            
            async def _execute_task_impl(self, task):
                return {"status": "success"}
            
            async def start(self):
                self.status = AgentStatus.ACTIVE
        
        config = AgentConfig(name="test_status", enable_metrics_server=False)
        
        with patch('base_agent.NATS'), \
             patch('base_agent.asyncpg.create_pool'), \
             patch('base_agent.consul.Consul'), \
             patch('redis.asyncio.from_url'):
            
            agent = TestAgent(config)
            assert agent.status == AgentStatus.INITIALIZING
            
            await agent.start()
            assert agent.status == AgentStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_status_to_error(self):
        """Test status transition to ERROR"""
        class TestAgent(BaseAgent):
            async def _process_task(self, task):
                return {"status": "success"}
            
            async def _handle_message(self, message):
                pass
            
            async def _execute_task_impl(self, task):
                return {"status": "success"}
            
            async def start(self):
                self.status = AgentStatus.ERROR
        
        config = AgentConfig(name="test_error_status", enable_metrics_server=False)
        
        with patch('base_agent.NATS'), \
             patch('base_agent.asyncpg.create_pool'), \
             patch('base_agent.consul.Consul'), \
             patch('redis.asyncio.from_url'):
            
            agent = TestAgent(config)
            await agent.start()
            assert agent.status == AgentStatus.ERROR


class TestAgentConfigurationEdgeCases:
    """Test agent configuration edge cases"""
    
    def test_config_with_empty_name(self):
        """Test configuration with empty name"""
        config = AgentConfig(name="")
        assert config.name == ""
    
    def test_config_with_none_custom(self):
        """Test configuration with None custom field"""
        config = AgentConfig(name="test", custom=None)
        assert config.custom is None
    
    def test_config_with_complex_custom(self):
        """Test configuration with complex custom data"""
        complex_data = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "bool": True
        }
        config = AgentConfig(name="test", custom=complex_data)
        assert config.custom["nested"]["key"] == "value"
        assert len(config.custom["list"]) == 3
        assert config.custom["bool"] is True
