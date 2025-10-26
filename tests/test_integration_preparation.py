"""
Unit tests for integration_preparation module
"""
import pytest
import os
from pathlib import Path
import tempfile
import shutil
from integration_preparation import IntegrationPreparer


class TestIntegrationPreparer:
    """Unit tests for IntegrationPreparer class"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_enhancement_progress(self):
        """Sample enhancement progress data"""
        return {
            "analytics": {"status": "enhanced", "version": "2.0"},
            "monitoring": {"status": "enhanced", "version": "2.0"},
            "optimization": {"status": "enhanced", "version": "2.0"}
        }
    
    @pytest.fixture
    def sample_test_results(self):
        """Sample test results data"""
        return {
            "analytics": {"overall_status": "passed", "tests_run": 10, "tests_passed": 10},
            "monitoring": {"overall_status": "passed", "tests_run": 8, "tests_passed": 8},
            "optimization": {"overall_status": "failed", "tests_run": 12, "tests_passed": 10}
        }
    
    @pytest.fixture
    def preparer(self, sample_enhancement_progress, sample_test_results):
        """Create an IntegrationPreparer instance"""
        return IntegrationPreparer(sample_enhancement_progress, sample_test_results)
    
    def test_initialization(self, preparer, sample_enhancement_progress, sample_test_results):
        """Test IntegrationPreparer initialization"""
        assert preparer.enhancement_progress == sample_enhancement_progress
        assert preparer.test_results == sample_test_results
        assert preparer.integration_readiness == {}
        assert isinstance(preparer.workspace_path, Path)
    
    def test_ensure_workspace(self, preparer):
        """Test workspace directory creation"""
        preparer._ensure_workspace()
        integration_path = preparer.workspace_path / "integration"
        assert integration_path.exists()
        assert integration_path.is_dir()
    
    def test_create_api_gateway(self, preparer):
        """Test API gateway creation"""
        preparer._ensure_workspace()
        preparer.create_api_gateway()
        
        gateway_path = preparer.workspace_path / "integration" / "api_gateway.py"
        assert gateway_path.exists()
        
        # Read and verify content
        with open(gateway_path, 'r') as f:
            content = f.read()
        
        assert "UNIFIED API GATEWAY" in content
        assert "FastAPI" in content
        assert "/api/v1/analytics/health" in content
        assert "/api/v1/monitoring/health" in content
        # optimization should not be included (failed tests)
        assert "/api/v1/optimization/health" not in content
    
    def test_setup_communication_layer(self, preparer):
        """Test communication layer setup"""
        preparer._ensure_workspace()
        preparer.setup_communication_layer()
        
        comm_path = preparer.workspace_path / "integration" / "communication_layer.py"
        assert comm_path.exists()
        
        # Read and verify content
        with open(comm_path, 'r') as f:
            content = f.read()
        
        assert "UNIFIED COMMUNICATION LAYER" in content
        assert "class UnifiedCommunication" in content
        assert "route_message" in content
        assert "broadcast_message" in content
    
    def test_create_unified_config(self, preparer):
        """Test unified configuration creation"""
        preparer._ensure_workspace()
        preparer.create_unified_config()
        
        config_path = preparer.workspace_path / "integration" / "unified_config.py"
        assert config_path.exists()
        
        # Read and verify content
        with open(config_path, 'r') as f:
            content = f.read()
        
        assert "UNIFIED CONFIGURATION MANAGEMENT" in content
        assert "class UnifiedConfig" in content
        assert "get_component_config" in content
    
    def test_generate_deployment_packages(self, preparer):
        """Test deployment package generation"""
        preparer._ensure_workspace()
        preparer.generate_deployment_packages()
        
        # Check deploy script
        deploy_path = preparer.workspace_path / "integration" / "deploy.sh"
        assert deploy_path.exists()
        assert os.access(deploy_path, os.X_OK)  # Check if executable
        
        with open(deploy_path, 'r') as f:
            content = f.read()
        assert "DEPLOYMENT SCRIPT" in content
        assert "docker-compose" in content
        
        # Check docker-compose file
        compose_path = preparer.workspace_path / "integration" / "docker-compose.yml"
        assert compose_path.exists()
        
        with open(compose_path, 'r') as f:
            content = f.read()
        assert "version:" in content
        assert "services:" in content
        assert "postgres:" in content
    
    def test_create_integration_docs(self, preparer):
        """Test integration documentation creation"""
        preparer._ensure_workspace()
        preparer.create_integration_docs()
        
        docs_path = preparer.workspace_path / "integration" / "INTEGRATION_README.md"
        assert docs_path.exists()
        
        # Read and verify content
        with open(docs_path, 'r') as f:
            content = f.read()
        
        assert "Integration Documentation" in content
        assert "Analytics" in content
        assert "Monitoring" in content
        assert "Quick Start" in content
        
        # Check integration readiness is updated
        assert preparer.integration_readiness["documentation"] is True
    
    def test_prepare_for_integration(self, preparer):
        """Test full integration preparation process"""
        preparer.prepare_for_integration()
        
        # Verify all files were created
        integration_path = preparer.workspace_path / "integration"
        assert (integration_path / "api_gateway.py").exists()
        assert (integration_path / "communication_layer.py").exists()
        assert (integration_path / "unified_config.py").exists()
        assert (integration_path / "deploy.sh").exists()
        assert (integration_path / "docker-compose.yml").exists()
        assert (integration_path / "INTEGRATION_README.md").exists()
        
        # Verify integration readiness
        assert preparer.integration_readiness["api_gateway"] is True
        assert preparer.integration_readiness["communication_layer"] is True
        assert preparer.integration_readiness["unified_config"] is True
        assert preparer.integration_readiness["deployment_packages"] is True
        assert preparer.integration_readiness["documentation"] is True
    
    def test_only_passed_components_in_gateway(self, preparer):
        """Test that only components with passed tests are included in API gateway"""
        preparer._ensure_workspace()
        preparer.create_api_gateway()
        
        gateway_path = preparer.workspace_path / "integration" / "api_gateway.py"
        with open(gateway_path, 'r') as f:
            content = f.read()
        
        # Analytics and monitoring should be present (passed)
        assert "analytics" in content.lower()
        assert "monitoring" in content.lower()
        
        # Optimization should not be present (failed)
        assert "optimization" not in content.lower()
    
    def test_empty_enhancement_progress(self):
        """Test with empty enhancement progress"""
        preparer = IntegrationPreparer({}, {})
        preparer.prepare_for_integration()
        
        # Should still create all files, just with no component-specific content
        integration_path = preparer.workspace_path / "integration"
        assert (integration_path / "api_gateway.py").exists()
        assert preparer.integration_readiness["api_gateway"] is True


class TestGeneratedFiles:
    """Test the generated files can be imported/parsed"""
    
    @pytest.fixture
    def preparer_with_files(self):
        """Create preparer and generate all files"""
        sample_enhancement_progress = {
            "analytics": {"status": "enhanced", "version": "2.0"}
        }
        sample_test_results = {
            "analytics": {"overall_status": "passed", "tests_run": 10, "tests_passed": 10}
        }
        preparer = IntegrationPreparer(sample_enhancement_progress, sample_test_results)
        preparer.prepare_for_integration()
        return preparer
    
    def test_api_gateway_syntax(self, preparer_with_files):
        """Test that generated API gateway has valid Python syntax"""
        gateway_path = preparer_with_files.workspace_path / "integration" / "api_gateway.py"
        
        # Try to compile the file
        with open(gateway_path, 'r') as f:
            code = f.read()
        
        compile(code, str(gateway_path), 'exec')  # Will raise if invalid syntax
    
    def test_communication_layer_syntax(self, preparer_with_files):
        """Test that generated communication layer has valid Python syntax"""
        comm_path = preparer_with_files.workspace_path / "integration" / "communication_layer.py"
        
        # Try to compile the file
        with open(comm_path, 'r') as f:
            code = f.read()
        
        compile(code, str(comm_path), 'exec')  # Will raise if invalid syntax
    
    def test_unified_config_syntax(self, preparer_with_files):
        """Test that generated unified config has valid Python syntax"""
        config_path = preparer_with_files.workspace_path / "integration" / "unified_config.py"
        
        # Try to compile the file
        with open(config_path, 'r') as f:
            code = f.read()
        
        compile(code, str(config_path), 'exec')  # Will raise if invalid syntax


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
