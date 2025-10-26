"""
Test suite for the Agent Dependency Analysis Tool

Tests the functionality of analyze_agent_dependencies.py to ensure
accurate dependency extraction and categorization.
"""

import json
import tempfile
import unittest
from pathlib import Path
from analyze_agent_dependencies import AgentDependencyAnalyzer


class TestAgentDependencyAnalyzer(unittest.TestCase):
    """Test cases for the AgentDependencyAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.analyzer = AgentDependencyAnalyzer(repo_root=self.temp_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_agent(self, filename: str, content: str):
        """Helper to create a test agent file."""
        file_path = self.temp_path / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_analyze_imports_no_dependencies(self):
        """Test analyzing an agent with no internal dependencies."""
        content = """
import asyncio
import logging
from typing import Dict, List

class SimpleAgent:
    pass
"""
        file_path = self.create_test_agent('simple_agent.py', content)
        internal, external = self.analyzer.analyze_imports(file_path)
        
        self.assertEqual(len(internal), 0)
        self.assertEqual(len(external), 3)
        self.assertIn('asyncio', external)
        self.assertIn('logging', external)
        self.assertIn('typing', external)
    
    def test_analyze_imports_with_internal_dependencies(self):
        """Test analyzing an agent with internal dependencies."""
        content = """
import asyncio
from base_agent import BaseAgent
from shared.config.settings import Settings
from agent_communicator import AgentCommunicator

class MyAgent(BaseAgent):
    pass
"""
        file_path = self.create_test_agent('my_agent.py', content)
        internal, external = self.analyzer.analyze_imports(file_path)
        
        self.assertEqual(len(internal), 3)
        self.assertIn('base_agent', internal)
        self.assertIn('shared.config.settings', internal)
        self.assertIn('agent_communicator', internal)
        self.assertEqual(len(external), 1)
        self.assertIn('asyncio', external)
    
    def test_analyze_imports_with_relative_imports(self):
        """Test analyzing an agent with relative imports."""
        content = """
from . import base
from ..shared import config
import logging
"""
        file_path = self.create_test_agent('relative_agent.py', content)
        internal, external = self.analyzer.analyze_imports(file_path)
        
        # Relative imports should be counted as internal
        self.assertTrue(any('.' in imp for imp in internal))
        self.assertIn('logging', external)
    
    def test_find_agent_files(self):
        """Test finding agent files in repository."""
        # Create several test agent files
        self.create_test_agent('base_agent.py', '# Base agent')
        self.create_test_agent('test_agent.py', '# Test agent')
        self.create_test_agent('helper_agent.py', '# Helper agent')
        # Create a file that doesn't match *_agent.py pattern
        (self.temp_path / 'utils.py').write_text('# Not an agent')
        
        agent_files = self.analyzer.find_agent_files()
        
        # Should find all files ending in _agent.py
        self.assertEqual(len(agent_files), 3)
        names = [f.name for f in agent_files]
        self.assertIn('base_agent.py', names)
        self.assertIn('test_agent.py', names)
        self.assertIn('helper_agent.py', names)
        self.assertNotIn('utils.py', names)
    
    def test_categorize_by_dependency_level(self):
        """Test dependency level categorization."""
        dependency_map = {
            'level0_agent.py': {'internal_count': 0},
            'level1_agent.py': {'internal_count': 1},
            'level2_agent.py': {'internal_count': 3},
            'level3_agent.py': {'internal_count': 6},
        }
        
        levels = self.analyzer.categorize_by_dependency_level(dependency_map)
        
        self.assertEqual(len(levels['level_0']), 1)
        self.assertEqual(len(levels['level_1']), 1)
        self.assertEqual(len(levels['level_2']), 1)
        self.assertEqual(len(levels['level_3']), 1)
        
        self.assertIn('level0_agent.py', levels['level_0'])
        self.assertIn('level1_agent.py', levels['level_1'])
        self.assertIn('level2_agent.py', levels['level_2'])
        self.assertIn('level3_agent.py', levels['level_3'])
    
    def test_analyze_generates_valid_report(self):
        """Test that analyze() generates a valid report structure."""
        # Create some test agents
        self.create_test_agent('base_agent.py', 'import asyncio')
        self.create_test_agent('test_agent.py', 'from base_agent import BaseAgent')
        
        report = self.analyzer.analyze()
        
        # Check report structure
        self.assertIn('summary', report)
        self.assertIn('level_0_agents', report)
        self.assertIn('level_1_agents', report)
        self.assertIn('level_2_agents', report)
        self.assertIn('level_3_agents', report)
        self.assertIn('detailed_dependencies', report)
        
        # Check summary fields
        summary = report['summary']
        self.assertIn('total_agents', summary)
        self.assertIn('level_0_independent', summary)
        self.assertIn('level_1_minimal', summary)
        self.assertIn('level_2_moderate', summary)
        self.assertIn('level_3_complex', summary)
        
        # Check that totals match
        total = (
            summary['level_0_independent'] +
            summary['level_1_minimal'] +
            summary['level_2_moderate'] +
            summary['level_3_complex']
        )
        self.assertEqual(total, summary['total_agents'])
    
    def test_save_report_creates_json_file(self):
        """Test that save_report creates a valid JSON file."""
        report = {
            'summary': {'total_agents': 1},
            'level_0_agents': [],
            'level_1_agents': [],
            'level_2_agents': [],
            'level_3_agents': [],
            'detailed_dependencies': {}
        }
        
        output_path = self.temp_path / 'test_report.json'
        self.analyzer.save_report(report, output_path)
        
        # Verify file exists
        self.assertTrue(output_path.exists())
        
        # Verify it's valid JSON
        with open(output_path, 'r') as f:
            loaded_report = json.load(f)
        
        self.assertEqual(loaded_report['summary']['total_agents'], 1)
    
    def test_empty_repository(self):
        """Test analyzer behavior with no agent files."""
        report = self.analyzer.analyze()
        
        self.assertEqual(report['summary']['total_agents'], 0)
        self.assertEqual(len(report['level_0_agents']), 0)
        self.assertEqual(len(report['level_1_agents']), 0)
    
    def test_malformed_python_file(self):
        """Test analyzer handles malformed Python files gracefully."""
        # Create a file with syntax errors
        content = """
import asyncio
from base_agent import BaseAgent

class MalformedAgent(BaseAgent):
    def __init__(self
        # Missing closing parenthesis
"""
        file_path = self.create_test_agent('malformed_agent.py', content)
        
        # Should not raise an exception
        internal, external = self.analyzer.analyze_imports(file_path)
        
        # Should return empty lists for malformed files
        self.assertEqual(len(internal), 0)
        self.assertEqual(len(external), 0)


class TestAgentDependencyAnalysisIntegration(unittest.TestCase):
    """Integration tests using the actual repository."""
    
    def test_actual_repository_analysis(self):
        """Test analysis on the actual repository."""
        analyzer = AgentDependencyAnalyzer()
        report = analyzer.analyze()
        
        # Basic sanity checks
        self.assertGreater(report['summary']['total_agents'], 0)
        
        # Verify structure
        self.assertIn('summary', report)
        self.assertIn('detailed_dependencies', report)
        
        # Verify all agents are categorized
        total_categorized = (
            len(report['level_0_agents']) +
            len(report['level_1_agents']) +
            len(report['level_2_agents']) +
            len(report['level_3_agents'])
        )
        self.assertEqual(total_categorized, report['summary']['total_agents'])


if __name__ == '__main__':
    unittest.main()
