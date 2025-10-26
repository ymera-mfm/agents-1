#!/usr/bin/env python3
import logging

"""
logger = logging.getLogger(__name__)

Phase 2: Remove Duplicate Files
Safely removes identified duplicate files after verification
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json

class DuplicateRemover:
    def __init__(
        self,
        root_path: Path,
        dry_run: bool = True,
        backup_dir: Path = None
    ):
        """
        Args:
            root_path (Path): The root directory to operate on.
            dry_run (bool): If True, no files will be deleted.
            backup_dir (Path, optional): Directory to store backups. Defaults to 'cleanup/backups/<timestamp>' under root_path.
        """
        self.root = root_path
        self.dry_run = dry_run
        if backup_dir is None:
            backup_dir = root_path / 'cleanup' / 'backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = backup_dir
        self.removed_files = []
        
    def remove_duplicates(self):
        """Remove all identified duplicate files."""
        logger.info("=" * 80)
        logger.info("YMERA PHASE 2: REMOVE DUPLICATES")
        logger.info("=" * 80)
        logger.info(f"\nMode: {'DRY RUN (no files will be deleted)' if self.dry_run else 'LIVE (files will be deleted)'}")
        logger.info()
        
        # Define duplicates to remove (keep the first one in each pair)
        duplicates_to_remove = [
            {
                'file': 'api_extensions.py',
                'reason': 'Exact duplicate of extensions.py',
                'keep': 'extensions.py'
            },
            {
                'file': 'api.gateway.py',
                'reason': 'Exact duplicate of gateway.py',
                'keep': 'gateway.py'
            },
            {
                'file': 'deployment_package/migrations/versions/001_add_indexes.py',
                'reason': 'Exact duplicate of migrations/versions/001_add_indexes.py',
                'keep': 'migrations/versions/001_add_indexes.py'
            },
            {
                'file': 'shared/utils/helpers.py',
                'reason': 'Empty file, no functionality',
                'keep': None
            },
        ]
        
        # Process each duplicate
        for dup in duplicates_to_remove:
            self._remove_file(dup)
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info(f"✅ Phase 2 {'Simulation' if self.dry_run else 'Execution'} Complete!")
        logger.info("=" * 80)
        logger.info(f"\nFiles {'would be' if self.dry_run else ''} removed: {len(self.removed_files)}")
        
        if self.removed_files:
            logger.info("\nRemoved files:")
            for f in self.removed_files:
                logger.info(f"  - {f}")
        
        if not self.dry_run and self.removed_files:
            logger.info(f"\nBackups saved to: {self.backup_dir}")
            self._save_manifest()
        
        if self.dry_run:
            logger.info("\n⚠️  This was a DRY RUN. No files were actually deleted.")
            logger.info("To execute for real, run: python3 cleanup/02_remove_duplicates.py --execute")
    
    def _remove_file(self, duplicate_info: dict):
        """Remove a single duplicate file."""
        file_path = self.root / duplicate_info['file']
        
        logger.info(f"\n{'[DRY RUN] ' if self.dry_run else ''}Processing: {duplicate_info['file']}")
        logger.info(f"  Reason: {duplicate_info['reason']}")
        if duplicate_info['keep']:
            logger.info(f"  Keeping: {duplicate_info['keep']}")
        
        # Check if file exists
        if not file_path.exists():
            logger.info(f"  ⚠️  File not found, skipping")
            return
        
        # Verify it's a file (not directory)
        if not file_path.is_file():
            logger.info(f"  ⚠️  Not a file, skipping")
            return
        
        # Get file size for reporting
        size = file_path.stat().st_size
        logger.info(f"  Size: {size} bytes")
        
        if self.dry_run:
            logger.info(f"  ✅ Would remove this file")
            self.removed_files.append(duplicate_info['file'])
        else:
            # Create backup
            self._backup_file(file_path, duplicate_info['file'])
            
            # Remove the file
            try:
                file_path.unlink()
                logger.info(f"  ✅ Removed successfully")
                self.removed_files.append(duplicate_info['file'])
            except Exception as e:
                logger.error(f"  ❌ Error removing file: {e}")
    
    def _backup_file(self, file_path: Path, relative_path: str):
        """Backup a file before deletion."""
        backup_path = self.backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"  💾 Backed up to: cleanup/backups/...")
        except Exception as e:
            logger.error(f"  ⚠️  Backup failed: {e}")
    
    def _save_manifest(self):
        """Save a manifest of removed files."""
        manifest = {
            'timestamp': datetime.now().isoformat(),
            'removed_files': self.removed_files,
            'backup_location': str(self.backup_dir)
        }
        
        manifest_path = self.backup_dir / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"\nManifest saved: {manifest_path}")


def main():
    import sys
    
    # Check for --execute flag
    execute = '--execute' in sys.argv or '-e' in sys.argv
    dry_run = not execute
    
    if dry_run:
        logger.info("\n⚠️  Running in DRY RUN mode (simulation only)")
        logger.info("To execute for real, add --execute flag\n")
    else:
        logger.info("\n⚠️  Running in EXECUTE mode (files will be deleted)")
        response = input("Are you sure you want to delete duplicate files? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Cancelled.")
            return
        logger.info()
    
    remover = DuplicateRemover(Path.cwd(), dry_run=dry_run)
    remover.remove_duplicates()
    
    if dry_run:
        logger.info("\n📝 Next steps:")
        logger.info("1. Review the files that would be removed above")
        logger.info("2. Run with --execute flag to actually remove them")
        logger.info("3. Run tests: pytest")
        logger.info("4. Commit changes: git add -u && git commit -m 'Remove duplicate files'")
    else:
        logger.info("\n📝 Next steps:")
        logger.info("1. Run tests: pytest")
        logger.info("2. Verify nothing broke")
        logger.info("3. Commit changes: git add -u && git commit -m 'Remove duplicate files'")


if __name__ == "__main__":
    main()
