"""
YMERA Database Migration Manager
Handles schema migrations, versioning, and rollbacks
"""

import asyncio
import importlib.util
import hashlib
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from database_core_integrated import (
    get_database_manager,
    DatabaseConfig,
    BaseMigration,
    MigrationInfo
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class MigrationStatus:
    """Status of a migration"""
    version: int
    name: str
    status: str
    applied_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, migrations_dir: Optional[Path] = None):
        self.config = DatabaseConfig()
        self.migrations_dir = migrations_dir or self.config.migrations_dir
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
    
    async def discover_migrations(self) -> List[MigrationInfo]:
        """Discover all migration files"""
        migrations = []
        
        for file_path in sorted(self.migrations_dir.glob("*.py")):
            if file_path.name.startswith("_"):
                continue
            
            # Extract version from filename (e.g., 001_initial_schema.py)
            parts = file_path.stem.split("_", 1)
            if len(parts) != 2:
                continue
            
            try:
                version = int(parts[0])
                name = parts[1]
                
                # Calculate checksum
                checksum = hashlib.sha256(file_path.read_bytes()).hexdigest()
                
                migrations.append(MigrationInfo(
                    version=version,
                    name=name,
                    filename=file_path.name,
                    filepath=file_path,
                    checksum=checksum
                ))
            except ValueError:
                continue
        
        return sorted(migrations, key=lambda m: m.version)
    
    async def get_applied_migrations(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Get list of applied migrations"""
        try:
            result = await session.execute(text(f"""
                SELECT version, name, checksum, status, completed_at, execution_time_ms
                FROM {self.config.migration_table}
                ORDER BY version
            """))
            
            return [
                {
                    'version': row[0],
                    'name': row[1],
                    'checksum': row[2],
                    'status': row[3],
                    'completed_at': row[4],
                    'execution_time_ms': row[5]
                }
                for row in result.fetchall()
            ]
        except:
            return []
    
    async def load_migration(self, migration_info: MigrationInfo) -> BaseMigration:
        """Load a migration module"""
        spec = importlib.util.spec_from_file_location(
            f"migration_{migration_info.version}",
            migration_info.filepath
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        
        # Get Migration class
        migration_class = getattr(module, 'Migration')
        return migration_class()
    
    async def apply_migration(
        self,
        session: AsyncSession,
        migration_info: MigrationInfo,
        migration: BaseMigration
    ) -> bool:
        """Apply a single migration"""
        import uuid
        
        start_time = datetime.utcnow()
        migration_id = str(uuid.uuid4())
        
        try:
            # Record migration start
            await session.execute(text(f"""
                INSERT INTO {self.config.migration_table}
                (id, version, name, filename, checksum, status, started_at)
                VALUES (:id, :version, :name, :filename, :checksum, 'running', :started_at)
            """), {
                'id': migration_id,
                'version': migration_info.version,
                'name': migration_info.name,
                'filename': migration_info.filename,
                'checksum': migration_info.checksum,
                'started_at': start_time
            })
            await session.commit()
            
            # Validate preconditions
            if not await migration.validate_preconditions(session):
                raise Exception("Migration preconditions not met")
            
            # Apply migration
            await migration.up(session)
            
            # Validate postconditions
            if not await migration.validate_postconditions(session):
                raise Exception("Migration postconditions not met")
            
            # Record success
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            await session.execute(text(f"""
                UPDATE {self.config.migration_table}
                SET status = 'completed',
                    completed_at = :completed_at,
                    execution_time_ms = :execution_time_ms,
                    updated_at = :updated_at
                WHERE id = :id
            """), {
                'id': migration_id,
                'completed_at': end_time,
                'execution_time_ms': execution_time_ms,
                'updated_at': end_time
            })
            await session.commit()
            
            print(f"✓ Applied migration {migration_info.version}: {migration_info.name} ({execution_time_ms}ms)")
            return True
            
        except Exception as e:
            # Record failure
            await session.rollback()
            
            try:
                await session.execute(text(f"""
                    UPDATE {self.config.migration_table}
                    SET status = 'failed',
                        error_message = :error,
                        updated_at = :updated_at
                    WHERE id = :id
                """), {
                    'id': migration_id,
                    'error': str(e),
                    'updated_at': datetime.utcnow()
                })
                await session.commit()
            except:
                pass
            
            print(f"✗ Failed to apply migration {migration_info.version}: {e}")
            return False
    
    async def rollback_migration(
        self,
        session: AsyncSession,
        migration_info: MigrationInfo,
        migration: BaseMigration
    ) -> bool:
        """Rollback a single migration"""
        try:
            # Apply rollback
            await migration.down(session)
            
            # Mark as rolled back
            await session.execute(text(f"""
                UPDATE {self.config.migration_table}
                SET rollback_executed = 1,
                    updated_at = :updated_at
                WHERE version = :version
            """), {
                'version': migration_info.version,
                'updated_at': datetime.utcnow()
            })
            await session.commit()
            
            print(f"✓ Rolled back migration {migration_info.version}: {migration_info.name}")
            return True
            
        except Exception as e:
            await session.rollback()
            print(f"✗ Failed to rollback migration {migration_info.version}: {e}")
            return False
    
    async def migrate(self, target_version: Optional[int] = None) -> bool:
        """Run migrations up to target version"""
        db_manager = await get_database_manager()
        
        # Get all migrations
        all_migrations = await self.discover_migrations()
        
        if not all_migrations:
            print("No migrations found")
            return True
        
        async with db_manager.get_session() as session:
            # Get applied migrations
            applied = await self.get_applied_migrations(session)
            applied_versions = {m['version'] for m in applied if m['status'] == 'completed'}
            
            # Determine which migrations to apply
            pending_migrations = [
                m for m in all_migrations
                if m.version not in applied_versions
                and (target_version is None or m.version <= target_version)
            ]
            
            if not pending_migrations:
                print("All migrations are up to date")
                return True
            
            print(f"\nApplying {len(pending_migrations)} migration(s)...")
            
            # Apply pending migrations
            for migration_info in pending_migrations:
                migration = await self.load_migration(migration_info)
                
                success = await self.apply_migration(session, migration_info, migration)
                if not success:
                    return False
            
            print(f"\n✓ Successfully applied {len(pending_migrations)} migration(s)")
            return True
    
    async def rollback(self, steps: int = 1) -> bool:
        """Rollback the last N migrations"""
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            # Get applied migrations
            applied = await self.get_applied_migrations(session)
            applied = [m for m in applied if m['status'] == 'completed']
            
            if not applied:
                print("No migrations to rollback")
                return True
            
            # Get migrations to rollback
            to_rollback = sorted(applied, key=lambda m: m['version'], reverse=True)[:steps]
            
            print(f"\nRolling back {len(to_rollback)} migration(s)...")
            
            # Rollback migrations
            all_migrations = await self.discover_migrations()
            migration_map = {m.version: m for m in all_migrations}
            
            for migration_record in to_rollback:
                version = migration_record['version']
                
                if version not in migration_map:
                    print(f"✗ Migration file not found for version {version}")
                    continue
                
                migration_info = migration_map[version]
                migration = await self.load_migration(migration_info)
                
                success = await self.rollback_migration(session, migration_info, migration)
                if not success:
                    return False
            
            print(f"\n✓ Successfully rolled back {len(to_rollback)} migration(s)")
            return True
    
    async def status(self) -> List[MigrationStatus]:
        """Get migration status"""
        db_manager = await get_database_manager()
        
        all_migrations = await self.discover_migrations()
        
        async with db_manager.get_session() as session:
            applied = await self.get_applied_migrations(session)
            applied_map = {m['version']: m for m in applied}
        
        statuses = []
        
        for migration_info in all_migrations:
            if migration_info.version in applied_map:
                record = applied_map[migration_info.version]
                statuses.append(MigrationStatus(
                    version=migration_info.version,
                    name=migration_info.name,
                    status=record['status'],
                    applied_at=record.get('completed_at'),
                    execution_time_ms=record.get('execution_time_ms')
                ))
            else:
                statuses.append(MigrationStatus(
                    version=migration_info.version,
                    name=migration_info.name,
                    status='pending'
                ))
        
        return statuses
    
    async def create_migration(self, name: str, description: str = "") -> Path:
        """Create a new migration file"""
        # Find next version number
        all_migrations = await self.discover_migrations()
        next_version = max([m.version for m in all_migrations], default=0) + 1
        
        # Create filename
        filename = f"{next_version:03d}_{name}.py"
        filepath = self.migrations_dir / filename
        
        # Generate migration template
        template = f'''"""
Migration {next_version:03d}: {name}
{description}
"""

from database_core_integrated import BaseMigration
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class Migration(BaseMigration):
    """Migration: {name}"""
    
    def __init__(self):
        super().__init__()
        self.version = {next_version}
        self.name = "{name}"
        self.description = "{description}"
        self.dependencies = []
    
    async def up(self, session: AsyncSession) -> None:
        """Apply migration"""
        # TODO: Implement migration logic
        pass
    
    async def down(self, session: AsyncSession) -> None:
        """Rollback migration"""
        # TODO: Implement rollback logic
        pass
    
    async def validate_preconditions(self, session: AsyncSession) -> bool:
        """Validate before migration"""
        return True
    
    async def validate_postconditions(self, session: AsyncSession) -> bool:
        """Validate after migration"""
        return True
'''
        
        filepath.write_text(template)
        print(f"✓ Created migration: {filepath}")
        return filepath


async def main():
    """CLI for migration manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="YMERA Database Migration Manager")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Run pending migrations')
    migrate_parser.add_argument('--target', type=int, help='Target version')
    
    # rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback migrations')
    rollback_parser.add_argument('--steps', type=int, default=1, help='Number of migrations to rollback')
    
    # status command
    subparsers.add_parser('status', help='Show migration status')
    
    # create command
    create_parser = subparsers.add_parser('create', help='Create new migration')
    create_parser.add_argument('name', help='Migration name')
    create_parser.add_argument('--description', default='', help='Migration description')
    
    args = parser.parse_args()
    
    manager = MigrationManager()
    
    if args.command == 'migrate':
        success = await manager.migrate(args.target)
        sys.exit(0 if success else 1)
    
    elif args.command == 'rollback':
        success = await manager.rollback(args.steps)
        sys.exit(0 if success else 1)
    
    elif args.command == 'status':
        statuses = await manager.status()
        
        print("\nMigration Status:")
        print("=" * 80)
        print(f"{'Version':<10} {'Name':<30} {'Status':<15} {'Applied At':<20} {'Time (ms)':<10}")
        print("-" * 80)
        
        for status in statuses:
            applied_at = status.applied_at.strftime('%Y-%m-%d %H:%M:%S') if status.applied_at else '-'
            exec_time = str(status.execution_time_ms) if status.execution_time_ms else '-'
            
            print(f"{status.version:<10} {status.name:<30} {status.status:<15} {applied_at:<20} {exec_time:<10}")
        
        print("=" * 80)
        print()
    
    elif args.command == 'create':
        await manager.create_migration(args.name, args.description)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
