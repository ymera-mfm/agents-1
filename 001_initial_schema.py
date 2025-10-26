"""
Migration 001: Initial Schema Setup
Creates all core tables for YMERA database system
"""

from database_core_integrated import BaseMigration
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class Migration(BaseMigration):
    """Initial database schema migration"""
    
    def __init__(self):
        super().__init__()
        self.version = 1
        self.name = "initial_schema"
        self.description = "Create initial database schema with all core tables"
        self.dependencies = []
    
    async def up(self, session: AsyncSession) -> None:
        """Create initial schema"""
        
        # Users table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                avatar_url VARCHAR(500),
                bio TEXT,
                location VARCHAR(100),
                timezone VARCHAR(50) DEFAULT 'UTC',
                language VARCHAR(10) DEFAULT 'en',
                email_verified BOOLEAN DEFAULT FALSE,
                two_factor_enabled BOOLEAN DEFAULT FALSE,
                two_factor_secret VARCHAR(32),
                role VARCHAR(50) DEFAULT 'user',
                permissions JSON,
                is_active BOOLEAN DEFAULT TRUE,
                last_login TIMESTAMP,
                login_count INTEGER DEFAULT 0,
                preferences JSON,
                api_key VARCHAR(64) UNIQUE,
                api_key_expires TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT username_min_length CHECK (length(username) >= 3)
            )
        """))
        
        # Create indexes for users
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_email_active ON users(email, is_active)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_is_deleted ON users(is_deleted)
        """))
        
        # Projects table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                owner_id VARCHAR(36) NOT NULL,
                github_url VARCHAR(500),
                project_type VARCHAR(50) DEFAULT 'general',
                programming_language VARCHAR(50),
                framework VARCHAR(100),
                status VARCHAR(50) DEFAULT 'active',
                priority VARCHAR(20) DEFAULT 'medium',
                progress FLOAT DEFAULT 0.0,
                estimated_completion TIMESTAMP,
                settings JSON,
                environment_variables JSON,
                dependencies JSON,
                total_tasks INTEGER DEFAULT 0,
                completed_tasks INTEGER DEFAULT 0,
                success_rate FLOAT DEFAULT 0.0,
                total_lines_of_code INTEGER DEFAULT 0,
                test_coverage FLOAT DEFAULT 0.0,
                tags JSON,
                metadata_info JSON,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT progress_range CHECK (progress >= 0 AND progress <= 100),
                CONSTRAINT success_rate_range CHECK (success_rate >= 0 AND success_rate <= 100)
            )
        """))
        
        # Create indexes for projects
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_project_owner_status ON projects(owner_id, status)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_projects_priority ON projects(priority)
        """))
        
        # Agents table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS agents (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                agent_type VARCHAR(100) NOT NULL,
                description TEXT,
                capabilities JSON,
                configuration JSON,
                api_endpoints JSON,
                status VARCHAR(50) DEFAULT 'active',
                health_status VARCHAR(50) DEFAULT 'healthy',
                load_factor FLOAT DEFAULT 0.0,
                response_time_avg FLOAT DEFAULT 0.0,
                success_rate FLOAT DEFAULT 100.0,
                learning_model_version VARCHAR(50) DEFAULT '1.0',
                knowledge_base JSON,
                learning_history JSON,
                performance_metrics JSON,
                tasks_completed INTEGER DEFAULT 0,
                tasks_failed INTEGER DEFAULT 0,
                total_execution_time FLOAT DEFAULT 0.0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT load_factor_range CHECK (load_factor >= 0 AND load_factor <= 100),
                CONSTRAINT agent_success_rate_range CHECK (success_rate >= 0 AND success_rate <= 100)
            )
        """))
        
        # Create indexes for agents
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agents_agent_type ON agents(agent_type)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agent_type_status ON agents(agent_type, status)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agents_health_status ON agents(health_status)
        """))
        
        # Tasks table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS tasks (
                id VARCHAR(36) PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                task_type VARCHAR(100) NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                project_id VARCHAR(36),
                agent_id VARCHAR(36),
                parent_task_id VARCHAR(36),
                status VARCHAR(50) DEFAULT 'pending',
                priority VARCHAR(20) DEFAULT 'medium',
                urgency INTEGER DEFAULT 5,
                input_data JSON,
                output_data JSON,
                execution_config JSON,
                error_details JSON,
                scheduled_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                execution_time FLOAT DEFAULT 0.0,
                timeout INTEGER DEFAULT 3600,
                progress FLOAT DEFAULT 0.0,
                result_summary TEXT,
                quality_score FLOAT DEFAULT 0.0,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                dependencies JSON,
                context_data JSON,
                tags JSON,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL,
                FOREIGN KEY (parent_task_id) REFERENCES tasks(id) ON DELETE SET NULL,
                CONSTRAINT task_progress_range CHECK (progress >= 0 AND progress <= 100),
                CONSTRAINT urgency_range CHECK (urgency >= 1 AND urgency <= 10)
            )
        """))
        
        # Create indexes for tasks
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks(title)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tasks_task_type ON tasks(task_type)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_task_status_priority ON tasks(status, priority)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_task_agent_status ON tasks(agent_id, status)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_at ON tasks(scheduled_at)
        """))
        
        # Files table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS files (
                id VARCHAR(36) PRIMARY KEY,
                filename VARCHAR(500) NOT NULL,
                original_filename VARCHAR(500) NOT NULL,
                file_path VARCHAR(1000) NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type VARCHAR(200),
                file_extension VARCHAR(20),
                encoding VARCHAR(50),
                checksum_md5 VARCHAR(32),
                checksum_sha256 VARCHAR(64),
                virus_scan_status VARCHAR(50) DEFAULT 'pending',
                user_id VARCHAR(36) NOT NULL,
                project_id VARCHAR(36),
                access_level VARCHAR(50) DEFAULT 'private',
                file_category VARCHAR(50),
                tags JSON,
                metadata_extracted JSON,
                content_summary TEXT,
                download_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                CONSTRAINT positive_file_size CHECK (file_size > 0)
            )
        """))
        
        # Create indexes for files
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_files_filename ON files(filename)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_file_user_project ON files(user_id, project_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_files_checksum_md5 ON files(checksum_md5)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_files_checksum_sha256 ON files(checksum_sha256)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_files_mime_type ON files(mime_type)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_files_access_level ON files(access_level)
        """))
        
        # Audit logs table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36),
                action VARCHAR(200) NOT NULL,
                resource_type VARCHAR(100) NOT NULL,
                resource_id VARCHAR(36),
                ip_address VARCHAR(45),
                user_agent VARCHAR(500),
                session_id VARCHAR(100),
                request_id VARCHAR(100),
                action_details JSON,
                before_state JSON,
                after_state JSON,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                execution_time FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """))
        
        # Create indexes for audit_logs
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_id ON audit_logs(resource_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_action_time ON audit_logs(action, created_at)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_session_id ON audit_logs(session_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_success ON audit_logs(success)
        """))
        
        # Project-Agents association table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_agents (
                project_id VARCHAR(36) NOT NULL,
                agent_id VARCHAR(36) NOT NULL,
                role VARCHAR(50) DEFAULT 'member',
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (project_id, agent_id),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
            )
        """))
        
        await session.commit()
    
    async def down(self, session: AsyncSession) -> None:
        """Rollback initial schema"""
        # Drop tables in reverse order of dependencies
        tables = [
            'audit_logs',
            'project_agents',
            'files',
            'tasks',
            'agents',
            'projects',
            'users'
        ]
        
        for table in tables:
            await session.execute(text(f"DROP TABLE IF EXISTS {table}"))
        
        await session.commit()
    
    async def validate_preconditions(self, session: AsyncSession) -> bool:
        """Validate before migration - check no tables exist"""
        try:
            # For SQLite
            result = await session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            ))
            return result.fetchone() is None
        except:
            # For PostgreSQL/MySQL
            try:
                result = await session.execute(text(
                    "SELECT 1 FROM information_schema.tables WHERE table_name='users'"
                ))
                return result.fetchone() is None
            except:
                return True
    
    async def validate_postconditions(self, session: AsyncSession) -> bool:
        """Validate after migration - check all tables exist"""
        try:
            required_tables = ['users', 'projects', 'agents', 'tasks', 'files', 'audit_logs']
            
            # For SQLite
            try:
                for table in required_tables:
                    result = await session.execute(text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
                    ).bindparams(table_name=table))
                    if result.fetchone() is None:
                        return False
                return True
            except:
                # For PostgreSQL/MySQL
                for table in required_tables:
                    result = await session.execute(text(
                        "SELECT 1 FROM information_schema.tables WHERE table_name=:table_name"
                    ).bindparams(table_name=table))
                    if result.fetchone() is None:
                        return False
                return True
        except:
            return False
