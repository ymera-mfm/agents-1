"""Add performance indexes

Revision ID: 001_add_indexes
Revises: 
Create Date: 2025-10-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes to existing tables"""
    
    # Tasks table indexes
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_user_id', 'tasks', ['user_id'])
    op.create_index('idx_tasks_agent_id', 'tasks', ['agent_id'])
    op.create_index('idx_tasks_priority', 'tasks', ['priority'])
    op.create_index('idx_tasks_task_type', 'tasks', ['task_type'])
    op.create_index('idx_tasks_created_at', 'tasks', ['created_at'])
    op.create_index('idx_tasks_status_priority', 'tasks', ['status', 'priority'])
    op.create_index('idx_tasks_user_status', 'tasks', ['user_id', 'status'])
    
    # Agents table indexes
    op.create_index('idx_agents_status', 'agents', ['status'])
    op.create_index('idx_agents_owner_id', 'agents', ['owner_id'])
    op.create_index('idx_agents_name', 'agents', ['name'])
    op.create_index('idx_agents_last_heartbeat', 'agents', ['last_heartbeat'])
    op.create_index('idx_agents_owner_status', 'agents', ['owner_id', 'status'])
    
    # Users table - email and username already have unique constraints which create indexes
    # Add index for common queries
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])


def downgrade():
    """Remove performance indexes"""
    
    # Tasks table indexes
    op.drop_index('idx_tasks_status', table_name='tasks')
    op.drop_index('idx_tasks_user_id', table_name='tasks')
    op.drop_index('idx_tasks_agent_id', table_name='tasks')
    op.drop_index('idx_tasks_priority', table_name='tasks')
    op.drop_index('idx_tasks_task_type', table_name='tasks')
    op.drop_index('idx_tasks_created_at', table_name='tasks')
    op.drop_index('idx_tasks_status_priority', table_name='tasks')
    op.drop_index('idx_tasks_user_status', table_name='tasks')
    
    # Agents table indexes
    op.drop_index('idx_agents_status', table_name='agents')
    op.drop_index('idx_agents_owner_id', table_name='agents')
    op.drop_index('idx_agents_name', table_name='agents')
    op.drop_index('idx_agents_last_heartbeat', table_name='agents')
    op.drop_index('idx_agents_owner_status', table_name='agents')
    
    # Users table indexes
    op.drop_index('idx_users_is_active', table_name='users')
    op.drop_index('idx_users_created_at', table_name='users')
