"""
Tests for specialized agents (Code Generation and DevOps)
"""
import pytest
import asyncio
from agent_code_generation import CodeGenerationAgent
from agent_devops import DevOpsAgent


@pytest.mark.asyncio
async def test_code_generation_agent_initialization():
    """Test code generation agent initialization"""
    agent = CodeGenerationAgent("test_code_gen")
    result = await agent.initialize()
    assert result is True
    assert agent.agent_id == "test_code_gen"
    assert "python" in agent.supported_languages


@pytest.mark.asyncio
async def test_code_generation_generate_code():
    """Test code generation functionality"""
    agent = CodeGenerationAgent("test_code_gen")
    await agent.initialize()
    
    message = {
        "type": "generate_code",
        "language": "python",
        "specification": "Create a function to calculate fibonacci numbers",
        "options": {}
    }
    
    response = await agent.process_message(message)
    
    assert response["status"] == "success"
    assert response["language"] == "python"
    assert "code" in response
    assert len(response["code"]) > 0
    assert agent.generation_stats["total_requests"] == 1
    assert agent.generation_stats["successful_generations"] == 1


@pytest.mark.asyncio
async def test_code_generation_unsupported_language():
    """Test handling of unsupported language"""
    agent = CodeGenerationAgent("test_code_gen")
    await agent.initialize()
    
    message = {
        "type": "generate_code",
        "language": "cobol",
        "specification": "Test",
        "options": {}
    }
    
    response = await agent.process_message(message)
    
    assert response["status"] == "error"
    assert "Unsupported language" in response["error"]


@pytest.mark.asyncio
async def test_code_analysis():
    """Test code analysis functionality"""
    agent = CodeGenerationAgent("test_code_gen")
    await agent.initialize()
    
    test_code = """
def hello_world():
    print("This is a very long line that exceeds the recommended 120 characters limit for code readability and maintainability")
    return True
"""
    
    message = {
        "type": "analyze_code",
        "language": "python",
        "code": test_code,
        "options": {}
    }
    
    response = await agent.process_message(message)
    
    assert response["status"] == "success"
    assert "analysis" in response
    assert "metrics" in response["analysis"]
    assert "quality_score" in response["analysis"]
    assert response["analysis"]["metrics"]["lines_of_code"] > 0


@pytest.mark.asyncio
async def test_code_refactoring():
    """Test code refactoring functionality"""
    agent = CodeGenerationAgent("test_code_gen")
    await agent.initialize()
    
    test_code = """
def test():


    print("test")


    return True
"""
    
    message = {
        "type": "refactor_code",
        "language": "python",
        "code": test_code,
        "options": {}
    }
    
    response = await agent.process_message(message)
    
    assert response["status"] == "success"
    assert "refactored_code" in response
    assert "changes" in response
    # Refactored code should have fewer lines due to blank line removal
    assert len(response["refactored_code"].split('\n')) < len(test_code.split('\n'))


@pytest.mark.asyncio
async def test_test_generation():
    """Test test case generation functionality"""
    agent = CodeGenerationAgent("test_code_gen")
    await agent.initialize()
    
    test_code = """
def add(a, b):
    return a + b
"""
    
    message = {
        "type": "generate_tests",
        "language": "python",
        "code": test_code,
        "options": {"framework": "pytest"}
    }
    
    response = await agent.process_message(message)
    
    assert response["status"] == "success"
    assert "test_code" in response
    assert "pytest" in response["test_framework"]
    assert "def test_" in response["test_code"]


@pytest.mark.asyncio
async def test_code_generation_statistics():
    """Test statistics tracking"""
    agent = CodeGenerationAgent("test_code_gen")
    await agent.initialize()
    
    # Generate some activity
    await agent.process_message({
        "type": "generate_code",
        "language": "python",
        "specification": "Test",
        "options": {}
    })
    
    await agent.process_message({
        "type": "generate_code",
        "language": "javascript",
        "specification": "Test",
        "options": {}
    })
    
    stats = agent.get_statistics()
    
    assert stats["stats"]["total_requests"] == 2
    assert stats["stats"]["successful_generations"] == 2
    assert "python" in stats["stats"]["languages_used"]
    assert "javascript" in stats["stats"]["languages_used"]


@pytest.mark.asyncio
async def test_devops_agent_initialization():
    """Test DevOps agent initialization"""
    agent = DevOpsAgent("test_devops")
    result = await agent.initialize()
    assert result is True
    assert agent.agent_id == "test_devops"
    assert "development" in agent.infrastructure_state["environments"]


@pytest.mark.asyncio
async def test_devops_deploy_service():
    """Test service deployment"""
    agent = DevOpsAgent("test_devops")
    await agent.initialize()
    
    message = {
        "type": "deploy",
        "environment": "development",
        "service": "api-service",
        "options": {"version": "1.0.0"}
    }
    
    response = await agent.process_message(message)
    
    assert response["status"] == "success"
    assert "deployment_id" in response
    assert len(agent.deployment_history) == 1
    assert agent.automation_stats["total_deployments"] == 1


@pytest.mark.asyncio
async def test_devops_invalid_environment():
    """Test deployment to invalid environment"""
    agent = DevOpsAgent("test_devops")
    await agent.initialize()
    
    message = {
        "type": "deploy",
        "environment": "invalid_env",
        "service": "api-service",
        "options": {}
    }
    
    response = await agent.process_message(message)
    
    assert response["status"] == "error"
    assert "Invalid environment" in response["error"]


@pytest.mark.asyncio
async def test_devops_provision_infrastructure():
    """Test infrastructure provisioning"""
    agent = DevOpsAgent("test_devops")
    await agent.initialize()
    
    message = {
        "type": "provision",
        "environment": "staging",
        "options": {
            "resources": [
                {"type": "compute", "name": "web-server"},
                {"type": "database", "name": "postgres"}
            ]
        }
    }
    
    response = await agent.process_message(message)
    
    assert response["status"] == "success"
    assert len(response["provisioned_resources"]) == 2
    assert agent.automation_stats["infrastructure_changes"] == 2


@pytest.mark.asyncio
async def test_devops_monitor_health():
    """Test health monitoring"""
    agent = DevOpsAgent("test_devops")
    await agent.initialize()
    
    # First deploy a service
    await agent.process_message({
        "type": "deploy",
        "environment": "production",
        "service": "web-app",
        "options": {"version": "2.0.0"}
    })
    
    # Then monitor it
    message = {
        "type": "monitor",
        "environment": "production",
        "service": "web-app"
    }
    
    response = await agent.process_message(message)
    
    assert response["status"] == "success"
    assert "health" in response
    assert "services" in response["health"]


@pytest.mark.asyncio
async def test_devops_analyze_logs():
    """Test log analysis"""
    agent = DevOpsAgent("test_devops")
    await agent.initialize()
    
    message = {
        "type": "analyze_logs",
        "environment": "production",
        "service": "api-service",
        "options": {}
    }
    
    response = await agent.process_message(message)
    
    assert response["status"] == "success"
    assert "analysis" in response
    assert "patterns" in response["analysis"]
    assert "recommendations" in response["analysis"]


@pytest.mark.asyncio
async def test_devops_rollback():
    """Test deployment rollback"""
    agent = DevOpsAgent("test_devops")
    await agent.initialize()
    
    # Deploy version 1.0
    await agent.process_message({
        "type": "deploy",
        "environment": "production",
        "service": "api",
        "options": {"version": "1.0.0"}
    })
    
    # Deploy version 2.0
    await agent.process_message({
        "type": "deploy",
        "environment": "production",
        "service": "api",
        "options": {"version": "2.0.0"}
    })
    
    # Rollback to 1.0
    message = {
        "type": "rollback",
        "environment": "production",
        "service": "api",
        "options": {}
    }
    
    response = await agent.process_message(message)
    
    assert response["status"] == "success"
    assert "1.0.0" in response["message"]


@pytest.mark.asyncio
async def test_devops_statistics():
    """Test DevOps statistics tracking"""
    agent = DevOpsAgent("test_devops")
    await agent.initialize()
    
    # Perform some operations
    await agent.process_message({
        "type": "deploy",
        "environment": "development",
        "service": "test-service",
        "options": {}
    })
    
    stats = agent.get_statistics()
    
    assert stats["stats"]["total_deployments"] > 0
    assert stats["deployment_count"] > 0


@pytest.mark.asyncio
async def test_agent_checkpointing():
    """Test specialized agent checkpointing"""
    # Test Code Generation Agent checkpointing
    code_agent = CodeGenerationAgent("checkpoint_test")
    await code_agent.initialize()
    
    await code_agent.process_message({
        "type": "generate_code",
        "language": "python",
        "specification": "Test",
        "options": {}
    })
    
    checkpoint = await code_agent.get_checkpoint_state()
    assert "generation_stats" in checkpoint
    assert checkpoint["generation_stats"]["total_requests"] == 1
    
    # Test DevOps Agent checkpointing
    devops_agent = DevOpsAgent("checkpoint_test")
    await devops_agent.initialize()
    
    await devops_agent.process_message({
        "type": "deploy",
        "environment": "development",
        "service": "test",
        "options": {}
    })
    
    checkpoint = await devops_agent.get_checkpoint_state()
    assert "automation_stats" in checkpoint
    assert checkpoint["automation_stats"]["total_deployments"] == 1
