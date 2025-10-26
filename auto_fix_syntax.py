#!/usr/bin/env python3
"""
Automated Syntax Error Fixer
Fixes common syntax errors in the codebase
"""

import re
from pathlib import Path

def fix_curly_quotes(filepath):
    """Fix curly quotes in file"""
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        fixed = content.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
        if fixed != content:
            filepath.write_text(fixed, encoding='utf-8')
            return True, "Fixed curly quotes"
        return False, "No curly quotes found"
    except Exception as e:
        return False, f"Error: {str(e)}"

def fix_pytest_ini_py(filepath):
    """Rename pytest.ini.py to pytest.ini.backup"""
    try:
        backup_path = filepath.parent / "pytest.ini.backup_py"
        filepath.rename(backup_path)
        return True, f"Renamed to {backup_path.name}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def add_missing_except_block(filepath, line_num):
    """Add missing except block at specified line"""
    try:
        lines = filepath.read_text(encoding='utf-8', errors='ignore').split('\n')
        if line_num <= len(lines):
            # Find indentation of try block
            indent = ""
            for i in range(line_num - 1, max(0, line_num - 20), -1):
                if 'try:' in lines[i]:
                    indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
                    break
            
            # Insert except block
            except_block = [
                f"{indent}except Exception as e:",
                f"{indent}    logger.error(f'Error: {{e}}')",
                f"{indent}    raise"
            ]
            lines.insert(line_num, '\n'.join(except_block))
            filepath.write_text('\n'.join(lines), encoding='utf-8')
            return True, "Added except block"
        return False, "Line number out of range"
    except Exception as e:
        return False, f"Error: {str(e)}"

def fix_file_fragments(filepath):
    """Check if file is a fragment and mark it"""
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        first_line = content.split('\n')[0].strip()
        
        # Check if file starts with non-declaration code
        if first_line and not any(first_line.startswith(x) for x in [
            '#', '"""', "'''", 'import', 'from', 'class', 'def', 'async', '@'
        ]):
            # This is likely a fragment
            new_name = filepath.parent / f"_FRAGMENT_{filepath.name}"
            filepath.rename(new_name)
            return True, f"Renamed to {new_name.name} (file fragment)"
        return False, "File appears valid"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main fix function"""
    repo_path = Path(__file__).parent
    
    fixes = {
        'code_editor_agent_api.py': fix_curly_quotes,
        'pytest.ini.py': fix_pytest_ini_py,
        'prod_drafting_agent.py': fix_file_fragments,
        'production_custom_engines_full.py': fix_file_fragments,
        'chat_service.py': fix_file_fragments,
    }
    
    print("="*80)
    print("AUTOMATED SYNTAX ERROR FIXES")
    print("="*80)
    print()
    
    results = []
    
    for filename, fix_func in fixes.items():
        filepath = repo_path / filename
        if not filepath.exists():
            results.append((filename, False, "File not found"))
            continue
        
        print(f"Fixing {filename}...", end=' ')
        success, message = fix_func(filepath)
        results.append((filename, success, message))
        
        if success:
            print(f"✅ {message}")
        else:
            print(f"⚠️ {message}")
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    fixed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"Fixed: {fixed}/{total}")
    print()
    
    for filename, success, message in results:
        status = "✅" if success else "⚠️"
        print(f"{status} {filename}: {message}")
    
    return 0 if fixed > 0 else 1

if __name__ == "__main__":
    exit(main())
