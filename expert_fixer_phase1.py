#!/usr/bin/env python3
"""
Expert Systematic Fixer - Phase 1: Critical Fixes
Converts print statements to proper logging
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict

class PrintToLoggingFixer:
    def __init__(self):
        self.root = Path(".")
        self.fixes = []
        
    def fix_print_statements(self, file_path: Path) -> Dict:
        """Convert print statements to logging calls"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                original_content = content
            
            # Check if file already uses logging
            has_logging = 'import logging' in content
            has_logger = 'logger = ' in content or 'self.logger' in content
            
            if not has_logging:
                # Add logging import at top
                lines = content.split('\n')
                # Find first import
                import_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        import_idx = i
                        break
                
                # Add after docstring if exists
                if lines[0].startswith('"""') or lines[0].startswith("'''"):
                    # Find end of docstring
                    quote = '"""' if lines[0].startswith('"""') else "'''"
                    for i in range(1, len(lines)):
                        if quote in lines[i]:
                            import_idx = i + 1
                            break
                
                lines.insert(import_idx, 'import logging')
                lines.insert(import_idx + 1, '')
                content = '\n'.join(lines)
                has_logging = True
            
            if not has_logger and has_logging:
                # Add logger setup after imports
                lines = content.split('\n')
                import_end = 0
                for i, line in enumerate(lines):
                    if line.strip() and not (line.startswith('import ') or line.startswith('from ') or line.startswith('#')):
                        import_end = i
                        break
                
                logger_name = file_path.stem
                lines.insert(import_end, f'logger = logging.getLogger(__name__)')
                lines.insert(import_end + 1, '')
                content = '\n'.join(lines)
            
            # Replace print statements
            modifications = 0
            
            # Pattern: print("string")
            def replace_print(match):
                nonlocal modifications
                modifications += 1
                indent = match.group(1)
                message = match.group(2)
                
                # Determine log level from content
                message_lower = message.lower()
                if 'error' in message_lower or 'fail' in message_lower:
                    return f'{indent}logger.error({message})'
                elif 'warning' in message_lower or 'warn' in message_lower:
                    return f'{indent}logger.warning({message})'
                elif 'debug' in message_lower:
                    return f'{indent}logger.debug({message})'
                else:
                    return f'{indent}logger.info({message})'
            
            # Match print statements
            content = re.sub(
                r'^(\s*)print\((.*?)\)$',
                replace_print,
                content,
                flags=re.MULTILINE
            )
            
            if modifications > 0 and content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return {
                    "file": str(file_path),
                    "modifications": modifications,
                    "status": "fixed"
                }
            
            return None
            
        except Exception as e:
            return {
                "file": str(file_path),
                "status": "error",
                "error": str(e)
            }
    
    def run(self, limit=10):
        """Fix print statements in files"""
        print("🔧 Phase 1: Converting Print Statements to Logging")
        print("=" * 70)
        
        # Get Python files (non-test)
        py_files = [f for f in self.root.glob("*.py") 
                    if not f.name.startswith('test_') and f.name not in [
                        'setup.py', 'conftest.py'
                    ]][:limit]
        
        print(f"Processing {len(py_files)} files...\n")
        
        fixed_count = 0
        for file_path in py_files:
            result = self.fix_print_statements(file_path)
            if result and result.get("status") == "fixed":
                print(f"✅ {file_path.name}: {result['modifications']} print → logging")
                self.fixes.append(result)
                fixed_count += 1
            elif result and result.get("status") == "error":
                print(f"❌ {file_path.name}: {result.get('error', 'Unknown error')[:50]}")
        
        print(f"\n📊 Summary: Fixed {fixed_count} files")
        return self.fixes

def main():
    fixer = PrintToLoggingFixer()
    fixes = fixer.run(limit=15)  # Fix first 15 files
    
    if fixes:
        print(f"\n✅ Applied {len(fixes)} fixes")
        return 0
    else:
        print("\n⚠️  No fixes applied")
        return 1

if __name__ == "__main__":
    sys.exit(main())
