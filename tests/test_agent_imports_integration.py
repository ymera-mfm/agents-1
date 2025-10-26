"""
Integration Tests for Agent Import Validation
Tests that all agents can be imported successfully with optional dependencies.
"""

import unittest
import sys
import os
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAgentImportsIntegration(unittest.TestCase):
    """Integration tests for agent imports"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.level_0_agents = [
            'base_agent',
            'enhanced_base_agent',
            'production_base_agent'
        ]
        
        cls.level_1_agents = [
            'coding_agent',
            'communication_agent',
            'drafting_agent',
            'editing_agent',
            'enhanced_learning_agent',
            'enhanced_llm_agent',
            'enhancement_agent',
            'examination_agent',
            'example_agent',
            'llm_agent',
            'metrics_agent',
            'orchestrator_agent',
            'performance_engine_agent',
            'prod_communication_agent',
            'prod_monitoring_agent',
            'production_monitoring_agent',
            'real_time_monitoring_agent',
            'security_agent',
            'static_analysis_agent',
            'validation_agent'
        ]
        
        cls.level_2_agents = [
            'learning_agent'
        ]
    
    def test_level_0_agents_import_successfully(self):
        """Test that all Level 0 (foundation) agents import successfully"""
        failed_agents = []
        
        for agent in self.level_0_agents:
            try:
                __import__(agent)
            except Exception as e:
                failed_agents.append((agent, type(e).__name__, str(e)[:50]))
        
        if failed_agents:
            error_msg = "\n".join([
                f"  - {agent}: {error} ({msg})"
                for agent, error, msg in failed_agents
            ])
            self.fail(f"Level 0 agents failed to import:\n{error_msg}")
    
    def test_level_1_agents_import_successfully(self):
        """Test that all Level 1 (core) agents import successfully"""
        failed_agents = []
        
        for agent in self.level_1_agents:
            try:
                __import__(agent)
            except Exception as e:
                failed_agents.append((agent, type(e).__name__, str(e)[:50]))
        
        if failed_agents:
            error_msg = "\n".join([
                f"  - {agent}: {error} ({msg})"
                for agent, error, msg in failed_agents
            ])
            self.fail(f"Level 1 agents failed to import:\n{error_msg}")
    
    def test_level_2_agents_import_or_config_validation(self):
        """Test Level 2 agents - allow config validation errors"""
        for agent in self.level_2_agents:
            try:
                __import__(agent)
                # If import succeeds, agent is good
            except Exception as e:
                error_type = type(e).__name__
                # ValidationError from Pydantic is expected for learning_agent
                # when env vars are not configured
                if 'ValidationError' in error_type:
                    # This is acceptable - agent imports but needs config
                    pass
                else:
                    # Other errors are real failures
                    self.fail(
                        f"{agent} failed with unexpected error: "
                        f"{error_type}: {str(e)[:100]}"
                    )
    
    def test_all_agents_have_graceful_dependency_handling(self):
        """Test that agents handle missing dependencies gracefully"""
        # This test verifies the pattern is present in agent files
        agent_files = [
            'base_agent.py',
            'production_base_agent.py',
            'llm_agent.py',
            'validation_agent.py'
        ]
        
        for agent_file in agent_files:
            file_path = Path(__file__).parent.parent / agent_file
            if not file_path.exists():
                continue
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for optional dependency pattern
            self.assertIn(
                'try:',
                content,
                f"{agent_file} should have try-except blocks for dependencies"
            )
            self.assertIn(
                'except ImportError:',
                content,
                f"{agent_file} should catch ImportError for optional dependencies"
            )
            self.assertIn(
                'HAS_',
                content,
                f"{agent_file} should have HAS_* feature flags"
            )
    
    def test_import_success_rate_meets_target(self):
        """Test that overall import success rate meets 95% target"""
        total_agents = len(self.level_0_agents) + len(self.level_1_agents)
        failed_count = 0
        
        for agent in self.level_0_agents + self.level_1_agents:
            try:
                __import__(agent)
            except Exception:
                failed_count += 1
        
        success_rate = 100 * (total_agents - failed_count) / total_agents
        
        self.assertGreaterEqual(
            success_rate,
            95.0,
            f"Import success rate ({success_rate:.1f}%) below target (95%)"
        )
    
    def test_agents_with_optional_deps_have_fallbacks(self):
        """Test that agents with optional dependencies have proper fallbacks"""
        # Test a few key agents to ensure they have fallback mechanisms
        test_cases = [
            ('base_agent', ['HAS_NATS', 'HAS_REDIS', 'HAS_OPENTELEMETRY']),
            ('llm_agent', ['HAS_TIKTOKEN', 'HAS_OPENAI', 'HAS_ANTHROPIC']),
            ('validation_agent', ['HAS_SQLALCHEMY', 'HAS_PYDANTIC']),
        ]
        
        for agent_file, expected_flags in test_cases:
            file_path = Path(__file__).parent.parent / f"{agent_file}.py"
            if not file_path.exists():
                continue
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            for flag in expected_flags:
                self.assertIn(
                    flag,
                    content,
                    f"{agent_file} should define {flag} feature flag"
                )


class TestAgentDependencyPatterns(unittest.TestCase):
    """Test that agents follow proper dependency patterns"""
    
    def test_no_agent_has_hard_dependency_on_optional_package(self):
        """Ensure no agent has direct imports that will fail"""
        # List of packages that should be wrapped in try-except
        optional_packages = [
            'nats', 'redis', 'asyncpg', 'consul',
            'psutil', 'numpy', 'nltk', 'spacy',
            'tiktoken', 'openai', 'anthropic',
            'structlog', 'sqlalchemy'
        ]
        
        # Sample check on a few key files
        agent_files = [
            'base_agent.py',
            'llm_agent.py',
            'drafting_agent.py'
        ]
        
        for agent_file in agent_files:
            file_path = Path(__file__).parent.parent / agent_file
            if not file_path.exists():
                continue
            
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Check that optional imports are within try blocks
            in_try_block = False
            try_indent = None
            for line in lines:
                stripped = line.lstrip()
                # Detect start of try block
                if stripped.startswith('try:'):
                    in_try_block = True
                    try_indent = len(line) - len(stripped)
                # Detect end of try block (except/finally at same or lower indent)
                elif (stripped.startswith('except') or stripped.startswith('finally:')) and in_try_block:
                    block_indent = len(line) - len(stripped)
                    if try_indent is not None and block_indent <= try_indent:
                        in_try_block = False
                        try_indent = None
                # Check if optional package is imported outside try block
                if not in_try_block:
                    for package in optional_packages:
                        if f'import {package}' in stripped and not stripped.startswith('#'):
                            self.fail(
                                f"{agent_file} has unprotected import of {package} "
                                f"on line: {line.strip()}"
                            )


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
