"""
YMERA Database Backup and Recovery System
Automated backup, restore, and disaster recovery utilities
"""

import asyncio
import os
import shutil
import subprocess
import gzip
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

from database_core_integrated import DatabaseConfig, get_database_manager


@dataclass
class BackupMetadata:
    """Backup metadata"""
    backup_id: str
    timestamp: datetime
    database_type: str
    database_name: str
    backup_size_bytes: int
    backup_path: Path
    compression: str
    checksum: str
    version: str = "5.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['backup_path'] = str(self.backup_path)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupMetadata':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['backup_path'] = Path(data['backup_path'])
        return cls(**data)


class BackupManager:
    """Manages database backups"""
    
    def __init__(self, backup_dir: Optional[Path] = None):
        self.config = DatabaseConfig()
        self.backup_dir = backup_dir or Path("./database/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_backup(
        self,
        compress: bool = True,
        include_data: bool = True
    ) -> BackupMetadata:
        """Create database backup"""
        import uuid
        import hashlib
        
        backup_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Determine backup filename
        db_name = self._get_database_name()
        filename = f"backup_{db_name}_{timestamp_str}_{backup_id}"
        
        if self.config.is_postgres:
            backup_path = await self._backup_postgresql(filename, include_data)
        elif self.config.is_sqlite:
            backup_path = await self._backup_sqlite(filename)
        else:
            raise NotImplementedError(f"Backup not implemented for {self.config.db_type}")
        
        # Compress if requested
        if compress:
            backup_path = await self._compress_backup(backup_path)
            compression = "gzip"
        else:
            compression = "none"
        
        # Calculate checksum
        checksum = self._calculate_checksum(backup_path)
        
        # Get backup size
        backup_size = backup_path.stat().st_size
        
        # Create metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            timestamp=timestamp,
            database_type=self.config.db_type,
            database_name=db_name,
            backup_size_bytes=backup_size,
            backup_path=backup_path,
            compression=compression,
            checksum=checksum
        )
        
        # Save metadata
        self._save_metadata(metadata)
        
        print(f"✓ Backup created: {backup_path.name}")
        print(f"  Size: {backup_size / 1024 / 1024:.2f} MB")
        print(f"  Checksum: {checksum[:16]}...")
        
        return metadata
    
    async def _backup_postgresql(self, filename: str, include_data: bool) -> Path:
        """Backup PostgreSQL database"""
        backup_path = self.backup_dir / f"{filename}.sql"
        
        # Parse connection URL
        db_url = self.config.database_url
        # postgresql+asyncpg://user:pass@host:port/dbname
        parts = db_url.replace("postgresql+asyncpg://", "").split("/")
        connection_part = parts[0]
        dbname = parts[1] if len(parts) > 1 else "postgres"
        
        # Build pg_dump command
        cmd = [
            "pg_dump",
            "--host", connection_part.split("@")[1].split(":")[0],
            "--username", connection_part.split(":")[0],
            "--dbname", dbname,
            "--file", str(backup_path),
            "--format", "plain",
            "--verbose"
        ]
        
        if not include_data:
            cmd.append("--schema-only")
        
        # Run pg_dump
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"pg_dump failed: {stderr.decode()}")
        
        return backup_path
    
    async def _backup_sqlite(self, filename: str) -> Path:
        """Backup SQLite database"""
        backup_path = self.backup_dir / f"{filename}.db"
        
        # Get source database path
        db_path = self.config.database_url.replace("sqlite+aiosqlite:///", "").replace("./", "")
        source_path = Path(db_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Database file not found: {source_path}")
        
        # Copy database file
        shutil.copy2(source_path, backup_path)
        
        return backup_path
    
    async def _compress_backup(self, backup_path: Path) -> Path:
        """Compress backup file"""
        compressed_path = backup_path.with_suffix(backup_path.suffix + ".gz")
        
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        backup_path.unlink()
        
        return compressed_path
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum"""
        import hashlib
        
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def _save_metadata(self, metadata: BackupMetadata) -> None:
        """Save backup metadata"""
        metadata_path = metadata.backup_path.with_suffix('.meta.json')
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
    
    def _load_metadata(self, metadata_path: Path) -> BackupMetadata:
        """Load backup metadata"""
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        
        return BackupMetadata.from_dict(data)
    
    def _get_database_name(self) -> str:
        """Extract database name from URL"""
        db_url = self.config.database_url
        
        if ":///" in db_url:
            # SQLite
            return Path(db_url.split("///")[1]).stem
        else:
            # PostgreSQL/MySQL
            return db_url.split("/")[-1]
    
    async def restore_backup(
        self,
        backup_path: Path,
        verify_checksum: bool = True
    ) -> bool:
        """Restore database from backup"""
        
        # Load metadata
        metadata_path = backup_path.with_suffix('.meta.json')
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        
        metadata = self._load_metadata(metadata_path)
        
        # Verify checksum
        if verify_checksum:
            current_checksum = self._calculate_checksum(backup_path)
            if current_checksum != metadata.checksum:
                raise ValueError("Backup checksum mismatch - file may be corrupted")
        
        # Decompress if needed
        if metadata.compression == "gzip":
            backup_path = await self._decompress_backup(backup_path)
        
        # Restore based on database type
        if metadata.database_type == "postgresql":
            await self._restore_postgresql(backup_path)
        elif metadata.database_type == "sqlite":
            await self._restore_sqlite(backup_path)
        else:
            raise NotImplementedError(f"Restore not implemented for {metadata.database_type}")
        
        print(f"✓ Database restored from backup: {backup_path.name}")
        return True
    
    async def _decompress_backup(self, backup_path: Path) -> Path:
        """Decompress backup file"""
        decompressed_path = backup_path.with_suffix('')
        
        with gzip.open(backup_path, 'rb') as f_in:
            with open(decompressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return decompressed_path
    
    async def _restore_postgresql(self, backup_path: Path) -> None:
        """Restore PostgreSQL database"""
        # Parse connection URL
        db_url = self.config.database_url
        parts = db_url.replace("postgresql+asyncpg://", "").split("/")
        connection_part = parts[0]
        dbname = parts[1] if len(parts) > 1 else "postgres"
        
        # Build psql command
        cmd = [
            "psql",
            "--host", connection_part.split("@")[1].split(":")[0],
            "--username", connection_part.split(":")[0],
            "--dbname", dbname,
            "--file", str(backup_path)
        ]
        
        # Run psql
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"psql restore failed: {stderr.decode()}")
    
    async def _restore_sqlite(self, backup_path: Path) -> None:
        """Restore SQLite database"""
        # Get target database path
        db_path = self.config.database_url.replace("sqlite+aiosqlite:///", "").replace("./", "")
        target_path = Path(db_path)
        
        # Backup current database if it exists
        if target_path.exists():
            backup_current = target_path.with_suffix('.db.bak')
            shutil.copy2(target_path, backup_current)
        
        # Copy backup to database location
        shutil.copy2(backup_path, target_path)
    
    async def list_backups(self) -> List[BackupMetadata]:
        """List all available backups"""
        backups = []
        
        for metadata_file in self.backup_dir.glob("*.meta.json"):
            try:
                metadata = self._load_metadata(metadata_file)
                backups.append(metadata)
            except Exception as e:
                print(f"Warning: Could not load metadata from {metadata_file}: {e}")
        
        return sorted(backups, key=lambda b: b.timestamp, reverse=True)
    
    async def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """Remove backups older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        backups = await self.list_backups()
        
        removed_count = 0
        
        for backup in backups:
            if backup.timestamp < cutoff_date:
                # Remove backup file
                if backup.backup_path.exists():
                    backup.backup_path.unlink()
                
                # Remove metadata file
                metadata_path = backup.backup_path.with_suffix('.meta.json')
                if metadata_path.exists():
                    metadata_path.unlink()
                
                removed_count += 1
                print(f"✓ Removed old backup: {backup.backup_path.name}")
        
        return removed_count
    
    async def verify_backup(self, backup_path: Path) -> bool:
        """Verify backup integrity"""
        metadata_path = backup_path.with_suffix('.meta.json')
        
        if not metadata_path.exists():
            print("✗ Metadata file not found")
            return False
        
        metadata = self._load_metadata(metadata_path)
        
        # Verify checksum
        current_checksum = self._calculate_checksum(backup_path)
        if current_checksum != metadata.checksum:
            print("✗ Checksum mismatch - backup may be corrupted")
            return False
        
        # Verify file size
        current_size = backup_path.stat().st_size
        if current_size != metadata.backup_size_bytes:
            print("✗ File size mismatch")
            return False
        
        print("✓ Backup verification passed")
        return True


async def main():
    """CLI for backup manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="YMERA Database Backup Manager")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--no-compress', action='store_true', help='Do not compress backup')
    backup_parser.add_argument('--schema-only', action='store_true', help='Backup schema only (no data)')
    
    # restore command
    restore_parser = subparsers.add_parser('restore', help='Restore database from backup')
    restore_parser.add_argument('backup_file', help='Backup file path')
    restore_parser.add_argument('--no-verify', action='store_true', help='Skip checksum verification')
    
    # list command
    subparsers.add_parser('list', help='List all backups')
    
    # cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Remove old backups')
    cleanup_parser.add_argument('--days', type=int, default=30, help='Days to keep (default: 30)')
    
    # verify command
    verify_parser = subparsers.add_parser('verify', help='Verify backup integrity')
    verify_parser.add_argument('backup_file', help='Backup file path')
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    if args.command == 'backup':
        await manager.create_backup(
            compress=not args.no_compress,
            include_data=not args.schema_only
        )
    
    elif args.command == 'restore':
        await manager.restore_backup(
            Path(args.backup_file),
            verify_checksum=not args.no_verify
        )
    
    elif args.command == 'list':
        backups = await manager.list_backups()
        
        print("\nAvailable Backups:")
        print("=" * 100)
        print(f"{'Timestamp':<20} {'ID':<10} {'Database':<20} {'Size (MB)':<12} {'Compression':<12} {'File':<25}")
        print("-" * 100)
        
        for backup in backups:
            size_mb = backup.backup_size_bytes / 1024 / 1024
            timestamp = backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"{timestamp:<20} {backup.backup_id:<10} {backup.database_name:<20} {size_mb:>10.2f} {backup.compression:<12} {backup.backup_path.name:<25}")
        
        print("=" * 100)
        print()
    
    elif args.command == 'cleanup':
        removed = await manager.cleanup_old_backups(args.days)
        print(f"\n✓ Removed {removed} old backup(s)")
    
    elif args.command == 'verify':
        await manager.verify_backup(Path(args.backup_file))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
