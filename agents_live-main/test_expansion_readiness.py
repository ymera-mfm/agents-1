"""
Unit tests for expansion_readiness module
"""

import pytest
import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from expansion_readiness import ExpansionManager


class TestExpansionManager:
    """Test cases for ExpansionManager class"""
    
    def test_expansion_manager_initialization(self):
        """Test that ExpansionManager initializes correctly"""
        manager = ExpansionManager()
        assert hasattr(manager, 'expansion_framework')
        assert isinstance(manager.expansion_framework, dict)
    
    def test_setup_expansion_framework_creates_files(self):
        """Test that setup_expansion_framework creates all required files"""
        manager = ExpansionManager()
        
        # Run the setup
        manager.setup_expansion_framework()
        
        # Verify all files were created
        base_path = Path('enhanced_workspace/integration')
        assert (base_path / 'plugin_architecture.py').exists()
        assert (base_path / 'api_versioning.py').exists()
        assert (base_path / 'config_template.py').exists()
        assert (base_path / 'EXPANSION_GUIDE.md').exists()
    
    def test_plugin_architecture_file_content(self):
        """Test that plugin_architecture.py has required classes"""
        manager = ExpansionManager()
        manager.create_plugin_architecture()
        
        plugin_file = Path('enhanced_workspace/integration/plugin_architecture.py')
        content = plugin_file.read_text()
        
        assert 'class PluginManager:' in content
        assert 'class BasePlugin:' in content
        assert 'register_plugin' in content
        assert 'add_hook' in content
        assert 'execute_hook' in content
        assert 'from collections import defaultdict' in content


class TestPluginArchitecture:
    """Test cases for plugin architecture components"""
    
    def test_plugin_manager_initialization(self):
        """Test PluginManager initialization"""
        from enhanced_workspace.integration.plugin_architecture import PluginManager
        
        pm = PluginManager()
        assert hasattr(pm, 'plugins')
        assert hasattr(pm, 'hooks')
        assert isinstance(pm.plugins, dict)
    
    def test_plugin_registration(self):
        """Test plugin registration"""
        from enhanced_workspace.integration.plugin_architecture import PluginManager, BasePlugin
        
        class TestPlugin(BasePlugin):
            def __init__(self):
                super().__init__('test_plugin', '1.0.0')
        
        pm = PluginManager()
        pm.register_plugin('test', TestPlugin)
        
        assert 'test' in pm.plugins
        assert pm.plugins['test'] == TestPlugin
    
    def test_hook_system(self):
        """Test hook registration and execution"""
        from enhanced_workspace.integration.plugin_architecture import PluginManager
        
        pm = PluginManager()
        
        # Test data
        callback_executed = []
        
        def test_callback(*args, **kwargs):
            callback_executed.append(True)
        
        # Add hook and execute
        pm.add_hook('test_hook', test_callback)
        pm.execute_hook('test_hook')
        
        assert len(callback_executed) == 1
        assert callback_executed[0] is True
    
    def test_base_plugin_structure(self):
        """Test BasePlugin class structure"""
        from enhanced_workspace.integration.plugin_architecture import BasePlugin
        
        plugin = BasePlugin('test', '1.0.0')
        
        assert plugin.name == 'test'
        assert plugin.version == '1.0.0'
        assert hasattr(plugin, 'initialize')
        assert hasattr(plugin, 'execute')


class TestAPIVersioning:
    """Test cases for API versioning system"""
    
    def test_api_version_manager_initialization(self):
        """Test APIVersionManager initialization"""
        from enhanced_workspace.integration.api_versioning import APIVersionManager
        
        manager = APIVersionManager()
        assert hasattr(manager, 'versions')
        assert hasattr(manager, 'current_version')
        assert manager.current_version == 'v1'
    
    def test_version_registration(self):
        """Test version registration"""
        from enhanced_workspace.integration.api_versioning import APIVersionManager
        
        manager = APIVersionManager()
        test_routes = {'/test': 'handler'}
        
        manager.register_version('v2', test_routes)
        
        assert 'v2' in manager.versions
        assert manager.versions['v2'] == test_routes
    
    def test_get_version(self):
        """Test getting version routes"""
        from enhanced_workspace.integration.api_versioning import APIVersionManager
        
        manager = APIVersionManager()
        v1_routes = {'/v1/test': 'handler_v1'}
        v2_routes = {'/v2/test': 'handler_v2'}
        
        manager.register_version('v1', v1_routes)
        manager.register_version('v2', v2_routes)
        
        assert manager.get_version('v1') == v1_routes
        assert manager.get_version('v2') == v2_routes
    
    def test_version_fallback(self):
        """Test fallback to current version"""
        from enhanced_workspace.integration.api_versioning import APIVersionManager
        
        manager = APIVersionManager()
        v1_routes = {'/v1/test': 'handler_v1'}
        
        manager.register_version('v1', v1_routes)
        
        # Non-existent version should fall back to current version (v1)
        assert manager.get_version('v999') == v1_routes


class TestConfigTemplate:
    """Test cases for configuration template"""
    
    def test_config_structure(self):
        """Test configuration template structure"""
        from enhanced_workspace.integration.config_template import expansion_config
        
        assert 'plugin_settings' in expansion_config
        assert 'api_settings' in expansion_config
        assert 'feature_flags' in expansion_config
        assert 'expansion_modules' in expansion_config
    
    def test_plugin_settings(self):
        """Test plugin settings structure"""
        from enhanced_workspace.integration.config_template import expansion_config
        
        plugin_settings = expansion_config['plugin_settings']
        assert 'enabled' in plugin_settings
        assert 'auto_load' in plugin_settings
        assert 'plugin_directory' in plugin_settings
    
    def test_api_settings(self):
        """Test API settings structure"""
        from enhanced_workspace.integration.config_template import expansion_config
        
        api_settings = expansion_config['api_settings']
        assert 'current_version' in api_settings
        assert 'supported_versions' in api_settings
        assert 'deprecation_warnings' in api_settings
        assert api_settings['current_version'] == 'v1'
    
    def test_feature_flags(self):
        """Test feature flags structure"""
        from enhanced_workspace.integration.config_template import expansion_config
        
        feature_flags = expansion_config['feature_flags']
        assert 'experimental_features' in feature_flags
        assert 'beta_features' in feature_flags
    
    def test_expansion_modules(self):
        """Test expansion modules structure"""
        from enhanced_workspace.integration.config_template import expansion_config
        
        modules = expansion_config['expansion_modules']
        assert 'analytics' in modules
        assert 'reporting' in modules
        assert 'integrations' in modules
        
        # Each module should have enabled flag and config
        for module_name, module_config in modules.items():
            assert 'enabled' in module_config
            assert 'config' in module_config


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
