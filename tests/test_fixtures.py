"""
YMERA Database Test Fixtures
Provides test data generators and fixtures for testing
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from faker import Faker

from database_core_integrated import (
    get_database_manager,
    User, Project, Agent, Task, File, AuditLog,
    BaseRepository
)


class TestDataGenerator:
    """Generate realistic test data"""
    
    def __init__(self, seed: int = 42):
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)
    
    def generate_user(self, **overrides) -> Dict[str, Any]:
        """Generate user data"""
        import hashlib
        
        password = self.fake.password()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        data = {
            'username': self.fake.user_name(),
            'email': self.fake.email(),
            'password_hash': password_hash,
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'bio': self.fake.text(max_nb_chars=200),
            'location': self.fake.city(),
            'timezone': random.choice(['UTC', 'US/Eastern', 'US/Pacific', 'Europe/London']),
            'language': random.choice(['en', 'es', 'fr', 'de']),
            'role': random.choice(['user', 'developer', 'admin']),
            'is_active': random.choice([True, True, True, False]),  # 75% active
            'preferences': {
                'theme': random.choice(['light', 'dark', 'auto']),
                'notifications': random.choice([True, False]),
                'language': 'en'
            }
        }
        
        data.update(overrides)
        return data
    
    def generate_project(self, owner_id: str, **overrides) -> Dict[str, Any]:
        """Generate project data"""
        programming_languages = ['Python', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'Java']
        frameworks = ['FastAPI', 'Flask', 'Django', 'React', 'Vue', 'Angular', 'Express']
        
        data = {
            'name': f"{self.fake.catch_phrase()} {random.choice(['Platform', 'System', 'App', 'Service'])}",
            'description': self.fake.text(max_nb_chars=500),
            'owner_id': owner_id,
            'project_type': random.choice(['web_app', 'mobile_app', 'api', 'library', 'tool']),
            'programming_language': random.choice(programming_languages),
            'framework': random.choice(frameworks),
            'status': random.choice(['active', 'active', 'active', 'paused', 'completed']),
            'priority': random.choice(['low', 'medium', 'high', 'urgent']),
            'progress': round(random.uniform(0, 100), 2),
            'total_tasks': random.randint(0, 100),
            'completed_tasks': 0,  # Will be calculated
            'success_rate': round(random.uniform(70, 100), 2),
            'tags': random.sample(['ai', 'ml', 'web', 'mobile', 'api', 'automation', 'testing'], k=random.randint(2, 4)),
            'settings': {
                'auto_deploy': random.choice([True, False]),
                'notifications_enabled': True,
                'max_concurrent_tasks': random.randint(5, 20)
            }
        }
        
        data['completed_tasks'] = int(data['total_tasks'] * (data['progress'] / 100))
        data.update(overrides)
        return data
    
    def generate_agent(self, **overrides) -> Dict[str, Any]:
        """Generate agent data"""
        agent_types = ['code_generation', 'testing', 'documentation', 'analysis', 'deployment']
        capabilities_map = {
            'code_generation': ['python', 'javascript', 'api_design', 'refactoring'],
            'testing': ['unit_testing', 'integration_testing', 'e2e_testing', 'performance_testing'],
            'documentation': ['api_docs', 'user_guides', 'technical_writing'],
            'analysis': ['code_review', 'security_scan', 'performance_analysis'],
            'deployment': ['ci_cd', 'docker', 'kubernetes', 'cloud_deployment']
        }
        
        agent_type = random.choice(agent_types)
        
        data = {
            'name': f"{self.fake.first_name()}{random.choice(['Bot', 'Agent', 'AI', 'Assistant'])}",
            'agent_type': agent_type,
            'description': self.fake.text(max_nb_chars=300),
            'capabilities': capabilities_map.get(agent_type, []),
            'configuration': {
                'model': random.choice(['gpt-4', 'gpt-3.5-turbo', 'claude-3']),
                'temperature': round(random.uniform(0.3, 0.9), 2),
                'max_tokens': random.choice([1000, 2000, 4000])
            },
            'status': random.choice(['active', 'active', 'active', 'idle', 'maintenance']),
            'health_status': random.choice(['healthy', 'healthy', 'healthy', 'degraded']),
            'success_rate': round(random.uniform(85, 100), 2),
            'tasks_completed': random.randint(0, 500),
            'tasks_failed': random.randint(0, 20),
            'learning_model_version': f"{random.randint(1, 5)}.{random.randint(0, 9)}"
        }
        
        data.update(overrides)
        return data
    
    def generate_task(
        self,
        user_id: str,
        project_id: str = None,
        agent_id: str = None,
        **overrides
    ) -> Dict[str, Any]:
        """Generate task data"""
        task_types = ['code_generation', 'bug_fix', 'feature_request', 'refactoring', 'testing', 'documentation']
        statuses = ['pending', 'in_progress', 'completed', 'failed', 'cancelled']
        
        status = random.choice(statuses)
        
        data = {
            'title': self.fake.sentence(nb_words=8),
            'description': self.fake.text(max_nb_chars=500),
            'task_type': random.choice(task_types),
            'user_id': user_id,
            'project_id': project_id,
            'agent_id': agent_id,
            'status': status,
            'priority': random.choice(['low', 'medium', 'high', 'urgent']),
            'urgency': random.randint(1, 10),
            'progress': round(random.uniform(0, 100), 2) if status == 'in_progress' else (100.0 if status == 'completed' else 0.0),
            'execution_time': round(random.uniform(1, 300), 2) if status == 'completed' else 0.0,
            'input_data': {
                'requirements': self.fake.text(max_nb_chars=200),
                'context': self.fake.text(max_nb_chars=100)
            },
            'output_data': {} if status != 'completed' else {
                'result': 'Task completed successfully',
                'metrics': {'lines_changed': random.randint(10, 500)}
            },
            'quality_score': round(random.uniform(70, 100), 2) if status == 'completed' else 0.0,
            'retry_count': random.randint(0, 2),
            'tags': random.sample(['urgent', 'bug', 'feature', 'enhancement', 'critical'], k=random.randint(1, 3))
        }
        
        # Set timestamps based on status
        if status == 'completed':
            completed_at = datetime.utcnow() - timedelta(hours=random.randint(1, 72))
            started_at = completed_at - timedelta(minutes=int(data['execution_time'] / 60))
            data['started_at'] = started_at
            data['completed_at'] = completed_at
        elif status == 'in_progress':
            data['started_at'] = datetime.utcnow() - timedelta(hours=random.randint(1, 12))
        
        data.update(overrides)
        return data
    
    def generate_file(
        self,
        user_id: str,
        project_id: str = None,
        **overrides
    ) -> Dict[str, Any]:
        """Generate file data"""
        import hashlib
        
        extensions = {
            'document': ['.pdf', '.docx', '.txt', '.md'],
            'code': ['.py', '.js', '.ts', '.java', '.go'],
            'image': ['.png', '.jpg', '.svg', '.gif'],
            'data': ['.json', '.csv', '.xml', '.yaml']
        }
        
        category = random.choice(list(extensions.keys()))
        extension = random.choice(extensions[category])
        filename = f"{self.fake.word()}_{random.randint(1000, 9999)}{extension}"
        
        # Generate fake file content for checksum
        content = self.fake.text(max_nb_chars=1000).encode()
        
        data = {
            'filename': f"files/{datetime.utcnow().strftime('%Y%m%d')}/{filename}",
            'original_filename': filename,
            'file_path': f"/storage/{filename}",
            'file_size': random.randint(1024, 10485760),  # 1KB to 10MB
            'mime_type': self._get_mime_type(extension),
            'file_extension': extension,
            'checksum_sha256': hashlib.sha256(content).hexdigest(),
            'checksum_md5': hashlib.md5(content).hexdigest(),
            'user_id': user_id,
            'project_id': project_id,
            'file_category': category,
            'access_level': random.choice(['private', 'team', 'public']),
            'virus_scan_status': random.choice(['passed', 'passed', 'passed', 'pending']),
            'download_count': random.randint(0, 100),
            'tags': random.sample(['important', 'draft', 'final', 'review'], k=random.randint(1, 2))
        }
        
        data.update(overrides)
        return data
    
    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type from extension"""
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.py': 'text/x-python',
            '.js': 'application/javascript',
            '.ts': 'application/typescript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg'
        }
        return mime_types.get(extension, 'application/octet-stream')
    
    def generate_audit_log(
        self,
        user_id: str = None,
        **overrides
    ) -> Dict[str, Any]:
        """Generate audit log data"""
        actions = [
            'user.login', 'user.logout', 'project.create', 'project.update',
            'task.create', 'task.complete', 'file.upload', 'file.download'
        ]
        
        data = {
            'user_id': user_id,
            'action': random.choice(actions),
            'resource_type': random.choice(['user', 'project', 'task', 'file']),
            'resource_id': str(random.randint(1, 1000)),
            'ip_address': self.fake.ipv4(),
            'user_agent': self.fake.user_agent(),
            'success': random.choice([True, True, True, False]),  # 75% success
            'execution_time': round(random.uniform(0.1, 2.0), 3),
            'action_details': {
                'method': random.choice(['GET', 'POST', 'PUT', 'DELETE']),
                'endpoint': f"/api/v1/{random.choice(['users', 'projects', 'tasks'])}"
            }
        }
        
        data.update(overrides)
        return data


class DatabaseFixtures:
    """Database fixtures for testing"""
    
    def __init__(self):
        self.generator = TestDataGenerator()
    
    async def create_test_dataset(
        self,
        num_users: int = 10,
        num_projects: int = 20,
        num_agents: int = 5,
        num_tasks: int = 100,
        num_files: int = 50,
        num_audit_logs: int = 200
    ) -> Dict[str, List]:
        """Create a complete test dataset"""
        print(f"\nCreating test dataset...")
        print(f"  Users: {num_users}")
        print(f"  Projects: {num_projects}")
        print(f"  Agents: {num_agents}")
        print(f"  Tasks: {num_tasks}")
        print(f"  Files: {num_files}")
        print(f"  Audit Logs: {num_audit_logs}")
        
        db_manager = await get_database_manager()
        
        created = {
            'users': [],
            'projects': [],
            'agents': [],
            'tasks': [],
            'files': [],
            'audit_logs': []
        }
        
        async with db_manager.get_session() as session:
            # Create users
            user_repo = BaseRepository(session, User)
            for i in range(num_users):
                user_data = self.generator.generate_user()
                user = await user_repo.create(**user_data)
                created['users'].append(user)
                if (i + 1) % 10 == 0:
                    print(f"  Created {i + 1} users...")
            
            # Create projects
            project_repo = BaseRepository(session, Project)
            for i in range(num_projects):
                owner = random.choice(created['users'])
                project_data = self.generator.generate_project(owner.id)
                project = await project_repo.create(**project_data)
                created['projects'].append(project)
                if (i + 1) % 10 == 0:
                    print(f"  Created {i + 1} projects...")
            
            # Create agents
            agent_repo = BaseRepository(session, Agent)
            for i in range(num_agents):
                agent_data = self.generator.generate_agent()
                agent = await agent_repo.create(**agent_data)
                created['agents'].append(agent)
            print(f"  Created {num_agents} agents...")
            
            # Create tasks
            task_repo = BaseRepository(session, Task)
            for i in range(num_tasks):
                user = random.choice(created['users'])
                project = random.choice(created['projects']) if random.random() > 0.2 else None
                agent = random.choice(created['agents']) if random.random() > 0.3 else None
                
                task_data = self.generator.generate_task(
                    user_id=user.id,
                    project_id=project.id if project else None,
                    agent_id=agent.id if agent else None
                )
                task = await task_repo.create(**task_data)
                created['tasks'].append(task)
                if (i + 1) % 20 == 0:
                    print(f"  Created {i + 1} tasks...")
            
            # Create files
            file_repo = BaseRepository(session, File)
            for i in range(num_files):
                user = random.choice(created['users'])
                project = random.choice(created['projects']) if random.random() > 0.3 else None
                
                file_data = self.generator.generate_file(
                    user_id=user.id,
                    project_id=project.id if project else None
                )
                file = await file_repo.create(**file_data)
                created['files'].append(file)
                if (i + 1) % 10 == 0:
                    print(f"  Created {i + 1} files...")
            
            # Create audit logs
            audit_repo = BaseRepository(session, AuditLog)
            for i in range(num_audit_logs):
                user = random.choice(created['users']) if random.random() > 0.1 else None
                
                audit_data = self.generator.generate_audit_log(
                    user_id=user.id if user else None
                )
                audit = await audit_repo.create(**audit_data)
                created['audit_logs'].append(audit)
                if (i + 1) % 50 == 0:
                    print(f"  Created {i + 1} audit logs...")
            
            await session.commit()
        
        print(f"\n✓ Test dataset created successfully!")
        return created
    
    async def cleanup_test_data(self) -> None:
        """Remove all test data"""
        print("\nCleaning up test data...")
        
        db_manager = await get_database_manager()
        
        from sqlalchemy import delete
        
        async with db_manager.get_session() as session:
            # Delete in reverse order of dependencies
            await session.execute(delete(AuditLog))
            await session.execute(delete(File))
            await session.execute(delete(Task))
            await session.execute(delete(Agent))
            await session.execute(delete(Project))
            await session.execute(delete(User))
            
            await session.commit()
        
        print("✓ Test data cleaned up")


async def main():
    """CLI for fixtures"""
    import argparse
    
    parser = argparse.ArgumentParser(description="YMERA Database Test Fixtures")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # generate command
    generate_parser = subparsers.add_parser('generate', help='Generate test data')
    generate_parser.add_argument('--users', type=int, default=10, help='Number of users')
    generate_parser.add_argument('--projects', type=int, default=20, help='Number of projects')
    generate_parser.add_argument('--agents', type=int, default=5, help='Number of agents')
    generate_parser.add_argument('--tasks', type=int, default=100, help='Number of tasks')
    generate_parser.add_argument('--files', type=int, default=50, help='Number of files')
    generate_parser.add_argument('--audit-logs', type=int, default=200, help='Number of audit logs')
    
    # cleanup command
    subparsers.add_parser('cleanup', help='Remove all test data')
    
    args = parser.parse_args()
    
    fixtures = DatabaseFixtures()
    
    if args.command == 'generate':
        await fixtures.create_test_dataset(
            num_users=args.users,
            num_projects=args.projects,
            num_agents=args.agents,
            num_tasks=args.tasks,
            num_files=args.files,
            num_audit_logs=args.audit_logs
        )
    
    elif args.command == 'cleanup':
        await fixtures.cleanup_test_data()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
