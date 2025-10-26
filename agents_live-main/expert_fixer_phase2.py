#!/usr/bin/env python3
"""
Expert Systematic Fixer - Phase 2: Add Type Hints
Adds type hints to public functions
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional

class TypeHintAdder:
    def __init__(self):
        self.root = Path(".")
        self.fixes = []
    
    def add_type_hints(self, file_path: Path) -> Optional[Dict]:
        """Add type hints to functions missing them"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                original_content = content
                lines = content.split('\n')
            
            # Check if typing is imported
            has_typing_import = 'from typing import' in content or 'import typing' in content
            
            modifications = 0
            new_lines = []
            i = 0
            
            while i < len(lines):
                line = lines[i]
                
                # Check if this is a function definition without return type
                if (line.strip().startswith('def ') or line.strip().startswith('async def ')) and '->' not in line:
                    # Skip test functions, private functions, __init__, __str__, etc
                    func_match = re.search(r'def\s+(\w+)\s*\(', line)
                    if func_match:
                        func_name = func_match.group(1)
                        if (not func_name.startswith('_') or func_name == '__init__') and not func_name.startswith('test_'):
                            # Check if it has a return statement to determine type
                            # Look ahead a few lines
                            has_return = False
                            return_value = None
                            for j in range(i+1, min(i+20, len(lines))):
                                if 'return ' in lines[j]:
                                    has_return = True
                                    return_match = re.search(r'return\s+(.+)', lines[j])
                                    if return_match:
                                        return_value = return_match.group(1).strip()
                                    break
                            
                            # Add type hint - remove existing colon first
                            line = line.rstrip()
                            if line.endswith(':'):
                                line = line[:-1]
                            
                            if func_name == '__init__':
                                # __init__ always returns None
                                line = line + ' -> None:'
                                modifications += 1
                            elif has_return and return_value:
                                if return_value in ['True', 'False']:
                                    line = line + ' -> bool:'
                                    modifications += 1
                                elif return_value.startswith('{') or return_value == 'dict()':
                                    line = line + ' -> Dict[str, Any]:'
                                    modifications += 1
                                elif return_value.startswith('[') or return_value == 'list()':
                                    line = line + ' -> List[Any]:'
                                    modifications += 1
                                elif return_value.startswith('"') or return_value.startswith("'"):
                                    line = line + ' -> str:'
                                    modifications += 1
                                elif return_value.isdigit():
                                    line = line + ' -> int:'
                                    modifications += 1
                                elif 'None' in return_value:
                                    line = line + ' -> Optional[Any]:'
                                    modifications += 1
                            elif not has_return or (return_value and 'None' in return_value):
                                line = line + ' -> None:'
                                modifications += 1
                
                new_lines.append(line)
                i += 1
            
            if modifications > 0:
                # Ensure typing imports are present
                if not has_typing_import:
                    # Add typing import
                    for idx, line in enumerate(new_lines):
                        if line.startswith('import ') or line.startswith('from '):
                            new_lines.insert(idx, 'from typing import Dict, List, Optional, Any')
                            new_lines.insert(idx + 1, '')
                            break
                
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
    
    def run(self, limit=10):
        """Add type hints to files"""
        print("🔧 Phase 2: Adding Type Hints to Functions")
        print("=" * 70)
        
        # Get Python files
        py_files = [f for f in self.root.glob("*.py") 
                    if not f.name.startswith('test_') and f.name not in [
                        'setup.py', 'conftest.py'
                    ]][:limit]
        
        print(f"Processing {len(py_files)} files...\n")
        
        fixed_count = 0
        for file_path in py_files:
            result = self.add_type_hints(file_path)
            if result and result.get("status") == "fixed":
                print(f"✅ {file_path.name}: Added {result['modifications']} type hints")
                self.fixes.append(result)
                fixed_count += 1
            elif result and result.get("status") == "error":
                print(f"❌ {file_path.name}: {result.get('error', 'Unknown')[:50]}")
        
        print(f"\n📊 Summary: Fixed {fixed_count} files")
        return self.fixes

def main():
    fixer = TypeHintAdder()
    fixes = fixer.run(limit=10)  # Fix first 10 files
    
    if fixes:
        print(f"\n✅ Applied {len(fixes)} fixes")
        return 0
    else:
        print("\n⚠️  No fixes applied")
        return 1

if __name__ == "__main__":
    sys.exit(main())
