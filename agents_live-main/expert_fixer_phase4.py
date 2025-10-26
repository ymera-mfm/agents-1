#!/usr/bin/env python3
"""
Expert Systematic Fixer - Phase 4: Final Issues
Completes remaining code quality improvements
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional

class Phase4Fixer:
    def __init__(self):
        self.root = Path(".")
        self.fixes = []
    
    def find_files_with_print(self) -> List[Path]:
        """Find files that still have print statements"""
        files_with_print = []
        
        # Already processed files
        processed = [
            'config_compat.py', 'learning_agent_main.py',
            'analyze_agent_dependencies.py', 'generate_agent_testing_report.py',
            'agent_classifier.py', '02_remove_duplicates.py', 'generator_engine_prod.py',
            'expert_fixer_phase1.py', 'expert_fixer_phase2.py', 'expert_fixer_phase3.py',
            'setup.py', 'conftest.py'
        ]
        
        py_files = [f for f in self.root.glob("*.py") 
                    if not f.name.startswith('test_') 
                    and f.name not in processed]
        
        for file_path in py_files[:30]:  # Check next 30 files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'print(' in content:
                        # Count print statements
                        count = content.count('print(')
                        files_with_print.append((file_path, count))
            except:
                pass
        
        # Sort by count
        files_with_print.sort(key=lambda x: x[1], reverse=True)
        return files_with_print
    
    def fix_print_in_file(self, file_path: Path) -> Optional[Dict]:
        """Fix print statements in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                original = content
            
            if 'print(' not in content:
                return None
            
            lines = content.split('\n')
            
            # Add logging if needed
            has_logging = 'import logging' in content
            has_logger = 'logger = ' in content or 'self.logger' in content
            
            if not has_logging:
                # Find insertion point
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""') and not line.strip().startswith("'''"):
                        if line.startswith('import ') or line.startswith('from '):
                            insert_idx = i
                            break
                        else:
                            insert_idx = i
                            break
                
                lines.insert(insert_idx, 'import logging')
                lines.insert(insert_idx + 1, '')
                content = '\n'.join(lines)
                lines = content.split('\n')
                has_logging = True
            
            if not has_logger and has_logging:
                # Add logger
                import_end = 0
                for i, line in enumerate(lines):
                    if line.strip() and not (line.startswith('import ') or line.startswith('from ') or line.startswith('#')):
                        import_end = i
                        break
                
                lines.insert(import_end, 'logger = logging.getLogger(__name__)')
                lines.insert(import_end + 1, '')
                content = '\n'.join(lines)
                lines = content.split('\n')
            
            # Replace print statements
            modifications = 0
            new_lines = []
            
            for line in lines:
                if 'print(' in line and not line.strip().startswith('#'):
                    indent = len(line) - len(line.lstrip())
                    indent_str = line[:indent]
                    
                    match = re.search(r'print\((.*)\)', line)
                    if match:
                        content_str = match.group(1)
                        lower = content_str.lower()
                        
                        if 'error' in lower or 'fail' in lower:
                            level = 'error'
                        elif 'warning' in lower or 'warn' in lower:
                            level = 'warning'
                        elif 'debug' in lower:
                            level = 'debug'
                        else:
                            level = 'info'
                        
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
    
    def run_print_fixes(self, limit=10):
        """Fix print statements in remaining files"""
        print("🔧 Phase 4: Completing Print → Logging Conversions")
        print("=" * 70)
        
        files = self.find_files_with_print()
        
        if not files:
            print("   ✅ No more print statements to fix!")
            return []
        
        print(f"Found {len(files)} files with print statements")
        print(f"Processing top {min(limit, len(files))} files...\n")
        
        fixed_count = 0
        for file_path, count in files[:limit]:
            result = self.fix_print_in_file(file_path)
            if result and result.get("status") == "fixed":
                print(f"   ✅ {file_path.name}: {result['modifications']} print → logging")
                self.fixes.append(result)
                fixed_count += 1
            elif result and result.get("status") == "error":
                print(f"   ❌ {file_path.name}: {result.get('error', '')[:50]}")
        
        print(f"\n📊 Summary: Fixed {fixed_count} files")
        return self.fixes
    
    def clean_unused_imports(self, file_path: Path) -> Optional[Dict]:
        """Remove obviously unused imports"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                original = content
            
            lines = content.split('\n')
            new_lines = []
            removed = []
            
            for line in lines:
                # Check for obviously unused imports
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    # Simple check - if module appears only once (in the import), might be unused
                    # This is a basic heuristic
                    if 'import json' in line and content.count('json.') == 0 and content.count('json(') == 0:
                        removed.append(line.strip())
                        continue
                    elif 'import sys' in line and content.count('sys.') == 0:
                        removed.append(line.strip())
                        continue
                
                new_lines.append(line)
            
            if removed:
                content = '\n'.join(new_lines)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return {
                    "file": str(file_path),
                    "removed": len(removed),
                    "status": "fixed"
                }
            
            return None
            
        except Exception as e:
            return None
    
    def run(self):
        """Run Phase 4 fixes"""
        print("🚀 Starting Phase 4: Final Code Quality Improvements\n")
        
        # Fix remaining print statements
        print_fixes = self.run_print_fixes(limit=10)
        
        print(f"\n✅ Phase 4 Complete: {len(print_fixes)} files improved")
        
        return self.fixes

def main():
    fixer = Phase4Fixer()
    fixes = fixer.run()
    
    if fixes:
        print(f"\n✅ Applied {len(fixes)} fixes")
        return 0
    else:
        print("\n⚠️  No additional fixes applied")
        return 0

if __name__ == "__main__":
    sys.exit(main())
