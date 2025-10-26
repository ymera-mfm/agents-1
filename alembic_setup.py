"""
alembic/env.py - Production-ready migration configuration
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Import your models
from app.models import Base  # Import all your models
from app.database import DatabaseConfig

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata


def get_url():
    """Get database URL from environment"""
    db_config = DatabaseConfig()
    return db_config.get_connection_string()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with connection pooling"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Don't use connection pooling for migrations
    )

    with connectable.connect() as connection:
        # Create schema if it doesn't exist
        connection.execute(text("IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo') BEGIN EXEC('CREATE SCHEMA dbo') END"))
        connection.commit()
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
            version_table_schema='dbo',
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
