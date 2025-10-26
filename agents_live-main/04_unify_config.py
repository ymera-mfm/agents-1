#!/usr/bin/env python3
"""
Configuration Unification
Consolidates all config files into single source of truth
"""

from pathlib import Path
from typing import Dict, Any, List, Set
import json
import os
import ast
import re
from datetime import datetime


class ConfigUnifier:
    def __init__(self, root_path: Path):
        self.root = root_path
        self.configs = []
        self.unified_settings = {}
        self.env_vars = set()
        
    def unify(self):
        """Unify all configuration files."""
        print("=" * 80)
        print("CONFIGURATION UNIFICATION")
        print("=" * 80)
        
        # Step 1: Find all config files
        print("\n1. Finding configuration files...")
        self._find_configs()
        
        # Step 2: Parse and merge
        print("\n2. Merging configurations...")
        unified = self._merge_configs()
        
        # Step 3: Create unified config
        print("\n3. Creating unified configuration...")
        self._create_unified_config(unified)
        
        # Step 4: Create .env template
        print("\n4. Creating .env template...")
        self._create_env_template(unified)
        
        # Step 5: Generate migration guide
        print("\n5. Creating migration guide...")
        self._create_migration_guide()
        
        print("\n" + "=" * 80)
        print("✅ Configuration Unified!")
        print("=" * 80)
    
    def _find_configs(self):
        """Find all configuration files."""
        config_patterns = ['config', 'setting', '.env']
        
        for py_file in self.root.rglob("*.py"):
            if any(part.startswith('.') or part == 'venv' for part in py_file.parts):
                continue
            
            if any(pattern in py_file.name.lower() for pattern in config_patterns):
                self.configs.append(py_file)
                print(f"   Found: {py_file.relative_to(self.root)}")
        
        print(f"\n   Total: {len(self.configs)} config files")
    
    def _merge_configs(self) -> Dict[str, Any]:
        """Merge all configurations into unified structure."""
        unified = {
            'database': {},
            'api': {},
            'security': {},
            'services': {},
            'features': {},
            'general': {}
        }
        
        for config_file in self.configs:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract variable assignments
                settings = self._extract_settings(content, config_file)
                
                # Categorize settings
                for key, value in settings.items():
                    category = self._categorize_setting(key)
                    unified[category][key] = value
                    
            except Exception as e:
                print(f"   ⚠️  Error parsing {config_file.name}: {e}")
        
        return unified
    
    def _extract_settings(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Extract settings from file content."""
        settings = {}
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Look for assignments at module level
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            # Skip private variables
                            if not var_name.startswith('_'):
                                try:
                                    value = ast.literal_eval(node.value)
                                    settings[var_name] = value
                                except:
                                    # Can't evaluate, store as string representation
                                    settings[var_name] = ast.unparse(node.value) if hasattr(ast, 'unparse') else '<complex>'
                
                # Look for class attributes in config classes
                elif isinstance(node, ast.ClassDef):
                    if any(keyword in node.name.lower() for keyword in ['config', 'setting']):
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        var_name = target.id
                                        if not var_name.startswith('_'):
                                            try:
                                                value = ast.literal_eval(item.value)
                                                settings[var_name] = value
                                            except:
                                                settings[var_name] = '<complex>'
        except:
            # If AST parsing fails, use regex fallback
            pattern = r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.+)$'
            for line in content.split('\n'):
                match = re.match(pattern, line.strip())
                if match:
                    var_name = match.group(1)
                    settings[var_name] = match.group(2).strip()
        
        return settings
    
    def _categorize_setting(self, key: str) -> str:
        """Categorize a setting based on its name."""
        key_lower = key.lower()
        
        if any(db_term in key_lower for db_term in ['db', 'database', 'postgres', 'sql', 'redis']):
            return 'database'
        elif any(api_term in key_lower for api_term in ['api', 'host', 'port', 'url', 'endpoint']):
            return 'api'
        elif any(sec_term in key_lower for sec_term in ['secret', 'key', 'token', 'password', 'auth', 'jwt', 'crypto']):
            return 'security'
        elif any(svc_term in key_lower for svc_term in ['service', 'external', 'integration', 'webhook']):
            return 'services'
        elif any(feat_term in key_lower for feat_term in ['feature', 'flag', 'enable', 'disable']):
            return 'features'
        else:
            return 'general'
    
    def _create_unified_config(self, unified: Dict[str, Any]):
        """Create unified configuration file."""
        output_file = self.root / 'core' / 'unified_config.py'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('#!/usr/bin/env python3\n')
            f.write('"""\n')
            f.write('Unified Configuration for YMERA Backend\n')
            f.write('Generated by configuration unification process\n')
            f.write(f'Created: {datetime.now().isoformat()}\n')
            f.write('"""\n\n')
            f.write('import os\n')
            f.write('from typing import Optional\n')
            f.write('from pydantic import BaseSettings, Field\n\n\n')
            
            # Create settings classes for each category
            for category, settings in unified.items():
                if not settings:
                    continue
                    
                class_name = f"{category.capitalize()}Settings"
                f.write(f'class {class_name}(BaseSettings):\n')
                f.write(f'    """{category.capitalize()} configuration settings."""\n\n')
                
                for key, value in settings.items():
                    # Determine type
                    if isinstance(value, bool):
                        type_hint = 'bool'
                        default = str(value)
                    elif isinstance(value, int):
                        type_hint = 'int'
                        default = str(value)
                    elif isinstance(value, str):
                        type_hint = 'str'
                        # Check if it's an env var reference
                        if value.startswith('os.getenv') or value.startswith('os.environ'):
                            default = f'Field(default_factory=lambda: {value})'
                            self.env_vars.add(key)
                        else:
                            default = f'"{value}"'
                    else:
                        type_hint = 'str'
                        default = f'"{value}"'
                    
                    f.write(f'    {key}: {type_hint} = {default}\n')
                
                f.write('\n\n')
            
            # Create main unified config class
            f.write('class UnifiedConfig(BaseSettings):\n')
            f.write('    """Main unified configuration."""\n\n')
            
            for category in unified.keys():
                if unified[category]:
                    class_name = f"{category.capitalize()}Settings"
                    f.write(f'    {category}: {class_name} = {class_name}()\n')
            
            f.write('\n    class Config:\n')
            f.write('        env_file = ".env"\n')
            f.write('        env_file_encoding = "utf-8"\n')
            f.write('        case_sensitive = False\n\n\n')
            
            # Create singleton instance
            f.write('# Singleton instance\n')
            f.write('_config: Optional[UnifiedConfig] = None\n\n\n')
            f.write('def get_config() -> UnifiedConfig:\n')
            f.write('    """Get unified configuration instance."""\n')
            f.write('    global _config\n')
            f.write('    if _config is None:\n')
            f.write('        _config = UnifiedConfig()\n')
            f.write('    return _config\n')
        
        print(f"   Created: {output_file.relative_to(self.root)}")
    
    def _create_env_template(self, unified: Dict[str, Any]):
        """Create .env template file."""
        output_file = self.root / '.env.template'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('# YMERA Backend Configuration Template\n')
            f.write(f'# Generated: {datetime.now().isoformat()}\n')
            f.write('# Copy this to .env and fill in your values\n\n')
            
            for category, settings in unified.items():
                if not settings:
                    continue
                
                f.write(f'\n# {category.upper()} SETTINGS\n')
                f.write(f'# {"-" * 50}\n')
                
                for key, value in settings.items():
                    # Only include settings that need environment variables
                    if key in self.env_vars or any(term in key.upper() for term in ['SECRET', 'KEY', 'PASSWORD', 'TOKEN']):
                        f.write(f'{key}=\n')
        
        print(f"   Created: {output_file.relative_to(self.root)}")
    
    def _create_migration_guide(self):
        """Create migration guide for moving to unified config."""
        output_file = self.root / 'cleanup' / 'CONFIG_MIGRATION_GUIDE.md'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('# Configuration Migration Guide\n\n')
            f.write('## Overview\n\n')
            f.write('This guide helps migrate from multiple config files to the unified configuration system.\n\n')
            
            f.write('## Old Configuration Files\n\n')
            f.write('The following config files were found:\n\n')
            for config_file in sorted(self.configs):
                f.write(f'- `{config_file.relative_to(self.root)}`\n')
            
            f.write('\n## New Unified Configuration\n\n')
            f.write('All settings have been consolidated into:\n')
            f.write('- `core/unified_config.py` - Main configuration file\n')
            f.write('- `.env.template` - Environment variable template\n\n')
            
            f.write('## Migration Steps\n\n')
            f.write('1. **Review unified configuration**:\n')
            f.write('   ```bash\n')
            f.write('   cat core/unified_config.py\n')
            f.write('   ```\n\n')
            
            f.write('2. **Create .env file**:\n')
            f.write('   ```bash\n')
            f.write('   cp .env.template .env\n')
            f.write('   # Edit .env with your actual values\n')
            f.write('   ```\n\n')
            
            f.write('3. **Update imports**:\n')
            f.write('   ```python\n')
            f.write('   # Old:\n')
            f.write('   from config import some_setting\n')
            f.write('   from production_config import another_setting\n\n')
            f.write('   # New:\n')
            f.write('   from core.unified_config import get_config\n')
            f.write('   config = get_config()\n')
            f.write('   value = config.general.some_setting\n')
            f.write('   ```\n\n')
            
            f.write('4. **Test thoroughly**:\n')
            f.write('   - Verify all imports work\n')
            f.write('   - Check environment variables are loaded\n')
            f.write('   - Run test suite\n\n')
            
            f.write('5. **Remove old config files**:\n')
            f.write('   ```bash\n')
            f.write('   # After verifying everything works\n')
            f.write('   git rm config.py production_config.py config_manager.py\n')
            f.write('   # etc...\n')
            f.write('   ```\n\n')
            
            f.write('## Configuration Categories\n\n')
            f.write('Settings are organized into:\n')
            f.write('- `database` - Database connections (PostgreSQL, Redis, etc.)\n')
            f.write('- `api` - API settings (host, port, URLs)\n')
            f.write('- `security` - Security settings (secrets, keys, auth)\n')
            f.write('- `services` - External services and integrations\n')
            f.write('- `features` - Feature flags\n')
            f.write('- `general` - General application settings\n\n')
            
            f.write('## Example Usage\n\n')
            f.write('```python\n')
            f.write('from core.unified_config import get_config\n\n')
            f.write('config = get_config()\n\n')
            f.write('# Access settings by category\n')
            f.write('db_url = config.database.DATABASE_URL\n')
            f.write('api_host = config.api.API_HOST\n')
            f.write('secret_key = config.security.SECRET_KEY\n')
            f.write('```\n\n')
            
            f.write('## Rollback\n\n')
            f.write('If needed, you can rollback:\n')
            f.write('```bash\n')
            f.write('git checkout HEAD~1 -- core/unified_config.py\n')
            f.write('# Restore old config files from git history\n')
            f.write('```\n')
        
        print(f"   Created: {output_file.relative_to(self.root)}")


def main():
    """Main entry point."""
    print("\n⚠️  WARNING: This will analyze all configuration files.")
    print("   A new unified configuration will be created.")
    print("   Old config files will NOT be deleted (manual cleanup required).\n")
    
    response = input("Proceed with configuration unification? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return
    
    unifier = ConfigUnifier(Path.cwd())
    unifier.unify()
    
    print("\n📝 Next steps:")
    print("1. Review: core/unified_config.py")
    print("2. Create: .env from .env.template")
    print("3. Read: cleanup/CONFIG_MIGRATION_GUIDE.md")
    print("4. Test: Update imports and verify")
    print("5. Cleanup: Remove old config files after verification")


if __name__ == "__main__":
    main()
