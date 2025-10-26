#!/usr/bin/env python3
"""
Automated Cleanup Script
Removes duplicates and old versions automatically
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class AutomatedCleaner:
    def __init__(self, analysis_file: Path):
        with open(analysis_file) as f:
            self.analysis = json.load(f)
        
        self.root = Path.cwd()
        self.backup_dir = self.root / 'cleanup' / 'backup'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.actions = []
        self.removed_files = []
    
    def clean(self):
        """Run automated cleanup."""
        print("=" * 80)
        print("AUTOMATED CLEANUP")
        print("=" * 80)
        
        print("\n⚠️  This will:")
        print("   - Remove duplicate files")
        print("   - Remove old versions")
        print("   - Backup all removed files")
        
        response = input("\nProceed? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted")
            return
        
        # Step 1: Remove duplicates
        print("\n1. Removing duplicates...")
        self._remove_duplicates()
        
        # Step 2: Remove old versions
        print("\n2. Removing old versions...")
        self._remove_old_versions()
        
        # Step 3: Save cleanup log
        print("\n3. Saving cleanup log...")
        self._save_log()
        
        print("\n" + "=" * 80)
        print(f"✅ Cleanup Complete!")
        print(f"   Removed: {len(self.removed_files)} files")
        print(f"   Backup: {self.backup_dir}")
        print("=" * 80)
    
    def _remove_duplicates(self):
        """Remove duplicate files, keeping the best version."""
        duplicates = self.analysis.get('duplicates', {})
        
        for hash_val, files in duplicates.items():
            if len(files) <= 1:
                continue
            
            # Sort by: 1) in core/agents/engines, 2) shortest path, 3) alphabetical
            sorted_files = sorted(files, key=lambda f: (
                0 if any(x in f['path'] for x in ['core/', 'agents/', 'engines/']) else 1,
                len(f['path']),
                f['path']
            ))
            
            # Keep first (best) file, remove others
            keep = sorted_files[0]
            remove = sorted_files[1:]
            
            print(f"\n   Keeping: {keep['path']}")
            for file_info in remove:
                self._remove_file(file_info['path'], f"Duplicate of {keep['path']}")
    
    def _remove_old_versions(self):
        """Remove old versions, keeping the newest/best."""
        versions = self.analysis.get('versions', {})
        
        for base_name, file_versions in versions.items():
            if len(file_versions) <= 1:
                continue
            
            # Find the main/production version (no suffix or _production)
            main_files = [f for f in file_versions if f.get('version') == 'main' or '_prod' in f.get('version', '')]
            
            if main_files:
                # Sort by size (larger is usually more complete)
                sorted_main = sorted(main_files, key=lambda f: f.get('lines', 0), reverse=True)
                keep = sorted_main[0]
            else:
                # No clear main version, keep the largest
                sorted_by_size = sorted(file_versions, key=lambda f: f.get('lines', 0), reverse=True)
                keep = sorted_by_size[0]
            
            print(f"\n   Base: {base_name}")
            print(f"   Keeping: {keep['name']} ({keep.get('lines', 0)} lines)")
            
            for file_info in file_versions:
                if file_info['path'] != keep['path']:
                    self._remove_file(file_info['path'], f"Old version of {keep['name']}")
    
    def _remove_file(self, file_path: str, reason: str):
        """Remove a file with backup."""
        full_path = self.root / file_path
        
        if not full_path.exists():
            print(f"   ⚠️  Skip (not found): {file_path}")
            return
        
        # Create backup
        backup_path = self.backup_dir / file_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(full_path, backup_path)
            full_path.unlink()
            
            self.removed_files.append(file_path)
            self.actions.append({
                'action': 'remove',
                'file': file_path,
                'reason': reason,
                'backup': str(backup_path),
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"   ✅ Removed: {file_path}")
            print(f"      Reason: {reason}")
        except Exception as e:
            print(f"   ❌ Error removing {file_path}: {e}")
    
    def _save_log(self):
        """Save cleanup log."""
        log_file = self.backup_dir / 'cleanup_log.json'
        
        log = {
            'timestamp': datetime.now().isoformat(),
            'removed_files': len(self.removed_files),
            'actions': self.actions,
            'files': self.removed_files
        }
        
        with open(log_file, 'w') as f:
            json.dump(log, f, indent=2)
        
        print(f"\n   Log saved: {log_file}")


def main():
    """Main entry point."""
    analysis_file = Path('cleanup/01_analysis_report.json')
    
    if not analysis_file.exists():
        print("❌ Analysis file not found!")
        print("   Run: python3 cleanup/01_analyze_repository.py")
        return
    
    cleaner = AutomatedCleaner(analysis_file)
    cleaner.clean()


if __name__ == "__main__":
    main()
