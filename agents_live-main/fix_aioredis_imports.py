"""Script to fix deprecated aioredis imports to redis.asyncio"""

import re
import sys
from pathlib import Path

def fix_aioredis_imports(file_path: Path) -> bool:
    """
    Fix aioredis imports in a file by replacing with redis.asyncio
    Returns True if changes were made
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace import statements
        content = re.sub(
            r'import aioredis\b',
            'from redis import asyncio as aioredis',
            content
        )
        
        # Replace from imports
        content = re.sub(
            r'from aioredis import',
            'from redis.asyncio import',
            content
        )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


if __name__ == "__main__":
    files_to_fix = [
        "audit_manager.py",
        "base_agent.py",
        "configuration_manager.py",
        "core_engine_complete.py",
        "core_engine_init.py",
        "intelligence_engine.py",
        "learning_engine_fixed.py",
        "notification_manager.py",
        "response_aggregator_fixed.py",
        "security_agent.py",
        "ymera_api_system.py"
    ]
    
    fixed_count = 0
    for file_name in files_to_fix:
        file_path = Path(file_name)
        if file_path.exists():
            if fix_aioredis_imports(file_path):
                print(f"✓ Fixed: {file_name}")
                fixed_count += 1
            else:
                print(f"○ No changes needed: {file_name}")
        else:
            print(f"✗ Not found: {file_name}")
    
    print(f"\nTotal files fixed: {fixed_count}")
