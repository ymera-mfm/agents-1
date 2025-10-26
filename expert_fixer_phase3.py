#!/usr/bin/env python3
"""
Expert Systematic Fixer - Phase 3: Continue Logging Migration
Process more files converting print to logging
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict

class Phase3LoggingFixer:
    def __init__(self):
        self.root = Path(".")
        self.fixes = []
        
    def fix_print_statements(self, file_path: Path) -> Dict:
        """Convert print statements to logging calls"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                original_content = content
            
            # Skip if no print statements
            if 'print(' not in content:
                return None
            
            # Check if file already uses logging
            has_logging = 'import logging' in content
            has_logger = 'logger = ' in content or 'self.logger' in content
            
            lines = content.split('\n')
            
            if not has_logging:
                # Find where to add import
                insert_idx = 0
                in_docstring = False
                
                for i, line in enumerate(lines):
                    # Skip module docstring
                    if i == 0 and (line.startswith('"""') or line.startswith("'''")):
                        in_docstring = True
                        continue
                    
                    if in_docstring:
                        if '"""' in line or "'''" in line:
                            in_docstring = False
                            insert_idx = i + 1
                        continue
                    
                    # Find first import or first non-empty line
                    if line.strip() and not line.startswith('#'):
                        if line.startswith('import ') or line.startswith('from '):
                            insert_idx = i
                            break
                        else:
                            insert_idx = i
                            break
                
                # Insert logging import
                lines.insert(insert_idx, 'import logging')
                lines.insert(insert_idx + 1, '')
                content = '\n'.join(lines)
                lines = content.split('\n')
                has_logging = True
            
            if not has_logger and has_logging:
                # Add logger after imports
                import_end = 0
                for i, line in enumerate(lines):
                    if line.strip() and not (line.startswith('import ') or line.startswith('from ') or line.startswith('#') or line.startswith('"""') or line.startswith("'''")):
                        import_end = i
                        break
                
                lines.insert(import_end, f'logger = logging.getLogger(__name__)')
                lines.insert(import_end + 1, '')
                content = '\n'.join(lines)
                lines = content.split('\n')
            
            # Replace print statements
            modifications = 0
            new_lines = []
            
            for line in lines:
                original_line = line
                
                # Match print( with proper indentation
                if 'print(' in line and not line.strip().startswith('#'):
                    # Extract indentation
                    indent = len(line) - len(line.lstrip())
                    indent_str = line[:indent]
                    
                    # Try to parse the print statement
                    # Simple case: print("message") or print('message')
                    match = re.search(r'print\((.*)\)', line)
                    if match:
                        content_str = match.group(1)
                        
                        # Determine log level
                        lower_content = content_str.lower()
                        if 'error' in lower_content or 'fail' in lower_content:
                            level = 'error'
                        elif 'warning' in lower_content or 'warn' in lower_content:
                            level = 'warning'
                        elif 'debug' in lower_content:
                            level = 'debug'
                        else:
                            level = 'info'
                        
                        # Replace with logger call
                        line = f'{indent_str}logger.{level}({content_str})'
                        modifications += 1
                
                new_lines.append(line)
            
            if modifications > 0:
                content = '\n'.join(new_lines)
                
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
    
    def run(self, limit=20):
        """Fix print statements in more files"""
        print("🔧 Phase 3: Additional Print → Logging Conversions")
        print("=" * 70)
        
        # Get Python files that weren't processed yet
        already_processed = [
            'config_compat.py', 'learning_agent_main.py',
            'analyze_agent_dependencies.py', 'generate_agent_testing_report.py'
        ]
        
        py_files = [f for f in self.root.glob("*.py") 
                    if not f.name.startswith('test_') 
                    and f.name not in already_processed
                    and f.name not in ['setup.py', 'conftest.py', 'expert_fixer_phase1.py', 'expert_fixer_phase2.py']][:limit]
        
        print(f"Processing {len(py_files)} files...\n")
        
        fixed_count = 0
        for file_path in py_files:
            result = self.fix_print_statements(file_path)
            if result and result.get("status") == "fixed":
                print(f"✅ {file_path.name}: {result['modifications']} print → logging")
                self.fixes.append(result)
                fixed_count += 1
            elif result and result.get("status") == "error":
                print(f"❌ {file_path.name}: {result.get('error', 'Unknown')[:50]}")
        
        print(f"\n📊 Summary: Fixed {fixed_count} files")
        return self.fixes

def main():
    fixer = Phase3LoggingFixer()
    fixes = fixer.run(limit=20)
    
    if fixes:
        print(f"\n✅ Applied {len(fixes)} fixes")
        return 0
    else:
        print("\n⚠️  No additional fixes needed")
        return 0

if __name__ == "__main__":
    sys.exit(main())
