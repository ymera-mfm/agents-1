"""
Unit tests for the Enhanced Component Testing Framework
Tests the testing framework functionality
"""

import pytest
import asyncio
from pathlib import Path
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from testing_framework import EnhancedComponentTester


class TestEnhancedComponentTester:
    """Test suite for EnhancedComponentTester class"""
    
    @pytest.fixture
    def tester(self):
        """Create a tester instance"""
        return EnhancedComponentTester()
    
    def test_initialization(self, tester):
        """Test tester initialization"""
        assert tester is not None
        assert tester.test_results == {}
        assert tester.base_path is not None
        assert tester.enhanced_workspace is not None
    
    @pytest.mark.asyncio
    async def test_test_all_enhanced_components(self, tester):
        """Test running all component tests"""
        results = await tester.test_all_enhanced_components()
        
        assert results is not None
        assert isinstance(results, dict)
        
        # Check that all categories are present
        expected_categories = ["agents", "modules", "engines", "systems", "database", "api"]
        for category in expected_categories:
            assert category in results
    
    @pytest.mark.asyncio
    async def test_import_component_valid(self, tester):
        """Test importing a valid component"""
        # Create a temporary test component
        test_component_path = tester.base_path / "enhanced_workspace" / "agents" / "integrated" / "agents_enhanced.py"
        
        if test_component_path.exists():
            module = tester.import_component(str(test_component_path))
            assert module is not None
            assert hasattr(module, '__name__')
    
    @pytest.mark.asyncio
    async def test_import_component_invalid(self, tester):
        """Test importing an invalid component"""
        module = tester.import_component("/nonexistent/path/module.py")
        assert module is None
    
    @pytest.mark.asyncio
    async def test_run_unit_tests(self, tester):
        """Test running unit tests on a component"""
        test_component_path = tester.base_path / "enhanced_workspace" / "agents" / "integrated" / "agents_enhanced.py"
        
        if test_component_path.exists():
            result = await tester.run_unit_tests(str(test_component_path))
            
            assert result is not None
            assert 'status' in result
            assert result['status'] in ['passed', 'failed', 'error']
            
            if 'details' in result:
                assert 'all_passed' in result['details']
    
    @pytest.mark.asyncio
    async def test_run_integration_tests(self, tester):
        """Test running integration tests on a component"""
        test_component_path = tester.base_path / "enhanced_workspace" / "agents" / "integrated" / "agents_enhanced.py"
        
        if test_component_path.exists():
            result = await tester.run_integration_tests(str(test_component_path))
            
            assert result is not None
            assert 'status' in result
    
    @pytest.mark.asyncio
    async def test_run_performance_tests(self, tester):
        """Test running performance tests on a component"""
        test_component_path = tester.base_path / "enhanced_workspace" / "agents" / "integrated" / "agents_enhanced.py"
        
        if test_component_path.exists():
            result = await tester.run_performance_tests(str(test_component_path))
            
            assert result is not None
            assert 'status' in result
            
            if 'details' in result:
                assert 'within_thresholds' in result['details']
                assert 'metrics' in result['details']
    
    @pytest.mark.asyncio
    async def test_run_compatibility_tests(self, tester):
        """Test running compatibility tests on a component"""
        test_component_path = tester.base_path / "enhanced_workspace" / "agents" / "integrated" / "agents_enhanced.py"
        
        if test_component_path.exists():
            result = await tester.run_compatibility_tests(str(test_component_path))
            
            assert result is not None
            assert 'status' in result
    
    @pytest.mark.asyncio
    async def test_run_security_tests(self, tester):
        """Test running security tests on a component"""
        test_component_path = tester.base_path / "enhanced_workspace" / "agents" / "integrated" / "agents_enhanced.py"
        
        if test_component_path.exists():
            result = await tester.run_security_tests(str(test_component_path))
            
            assert result is not None
            assert 'status' in result
    
    @pytest.mark.asyncio
    async def test_execute_component_unit_tests(self, tester):
        """Test executing component unit tests"""
        test_component_path = tester.base_path / "enhanced_workspace" / "agents" / "integrated" / "agents_enhanced.py"
        
        if test_component_path.exists():
            module = tester.import_component(str(test_component_path))
            
            if module:
                result = await tester.execute_component_unit_tests(module)
                
                assert result is not None
                assert 'all_passed' in result
                assert 'passed' in result
                assert 'failed' in result
                assert isinstance(result['passed_tests'], list)
                assert isinstance(result['failed_tests'], list)
    
    def test_generate_test_report(self, tester):
        """Test test report generation"""
        # Add some dummy results
        tester.test_results = {
            'agents': {'status': 'passed'},
            'modules': {'status': 'skipped'}
        }
        
        # This should not raise an exception
        tester.generate_test_report()
        
        # Check if report file was created
        report_path = tester.base_path / "test_report_enhanced.json"
        assert report_path.exists()
        
        # Verify report content
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        assert 'agents' in report_data
        assert 'modules' in report_data


class TestEnhancedComponents:
    """Test the enhanced components themselves"""
    
    @pytest.mark.asyncio
    async def test_enhanced_agent_initialization(self):
        """Test EnhancedAgent initialization"""
        from enhanced_workspace.agents.integrated.agents_enhanced import EnhancedAgent
        
        agent = EnhancedAgent(agent_id="test_001", name="Test Agent")
        assert agent.agent_id == "test_001"
        assert agent.name == "Test Agent"
        assert agent.status == "initialized"
        
        await agent.initialize()
        assert agent.status == "ready"
    
    @pytest.mark.asyncio
    async def test_enhanced_agent_execute_task(self):
        """Test EnhancedAgent task execution"""
        from enhanced_workspace.agents.integrated.agents_enhanced import EnhancedAgent
        
        agent = EnhancedAgent()
        await agent.initialize()
        
        task = {'id': 'task_001', 'description': 'Test task'}
        result = await agent.execute_task(task)
        
        assert result is not None
        assert result['status'] == 'completed'
        assert result['task_id'] == 'task_001'
        assert agent.tasks_completed == 1
    
    @pytest.mark.asyncio
    async def test_enhanced_processing_engine(self):
        """Test EnhancedProcessingEngine"""
        from enhanced_workspace.engines.integrated.engines_enhanced import EnhancedProcessingEngine
        
        engine = EnhancedProcessingEngine(engine_id="engine_001")
        assert engine.engine_id == "engine_001"
        
        result = await engine.process({'data': 'test'})
        assert result is not None
        assert result['status'] == 'processed'
        assert engine.processed_items == 1
    
    @pytest.mark.asyncio
    async def test_enhanced_api_gateway(self):
        """Test EnhancedAPIGateway"""
        from enhanced_workspace.api.integrated.api_enhanced import EnhancedAPIGateway
        
        gateway = EnhancedAPIGateway()
        
        # Register a test route
        async def test_handler(data):
            return {'result': 'success'}
        
        gateway.register_route('/test', test_handler)
        
        # Handle a request
        result = await gateway.handle_request('/test', {'data': 'test'})
        assert result is not None
        assert result['status'] == 'success'
        assert gateway.request_count == 1


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
