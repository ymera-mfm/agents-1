"""
Project Log Manager
Comprehensive logging system for tracking all activities, file locations, and knowledge flow
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class ProjectLogManager:
    """
    Comprehensive Project Logging System
    
    Features:
    - Project event logging
    - File location tracking
    - Module integration history
    - Knowledge request/contribution logging
    - Build process logging
    - Directory structure tracking
    - Daily summary generation
    - Agent interaction logging
    """
    
    def __init__(self, database, settings):
        self.database = database
        self.settings = settings
        
        # In-memory caches for fast access
        self.file_location_cache: Dict[str, Dict[str, Any]] = {}
        self.directory_structure_cache: Dict[str, Dict] = {}
        self.recent_logs_cache: Dict[str, List] = defaultdict(list)
        
        # Log retention
        self.log_retention_days = 90
        
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize log manager and create tables"""
        try:
            # Ensure log tables exist
            await self._create_log_tables()
            
            # Load recent data into cache
            await self._load_caches()
            
            self.is_initialized = True
            logger.info("✓ Log manager initialized")
            
        except Exception as e:
            logger.error(f"Log manager initialization failed: {e}")
            raise
    
    async def _create_log_tables(self):
        """Create logging tables if they don't exist"""
        await self.database.execute_command("""
            -- Project event logs
            CREATE TABLE IF NOT EXISTS project_event_logs (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                project_id UUID NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                event_category VARCHAR(50) DEFAULT 'general',
                severity VARCHAR(20) DEFAULT 'info',
                details JSONB DEFAULT '{}',
                user_id UUID,
                agent_id VARCHAR(255),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_project_logs_project (project_id),
                INDEX idx_project_logs_type (event_type),
                INDEX idx_project_logs_timestamp (timestamp DESC)
            );
            
            -- File location tracking
            CREATE TABLE IF NOT EXISTS file_location_logs (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                project_id UUID NOT NULL,
                file_path TEXT NOT NULL,
                module_id UUID,
                file_type VARCHAR(50),
                size BIGINT,
                checksum VARCHAR(255),
                location_type VARCHAR(50) DEFAULT 'integrated',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_file_logs_project (project_id),
                INDEX idx_file_logs_path (file_path),
                UNIQUE(project_id, file_path)
            );
            
            -- Module integration history
            CREATE TABLE IF NOT EXISTS module_integration_logs (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                project_id UUID NOT NULL,
                module_id UUID NOT NULL,
                submission_id UUID,
                module_name VARCHAR(255),
                integration_status VARCHAR(50),
                integration_method VARCHAR(50),
                file_paths JSONB DEFAULT '[]',
                dependencies JSONB DEFAULT '[]',
                quality_score FLOAT,
                integration_time_seconds FLOAT,
                error_message TEXT,
                metadata JSONB DEFAULT '{}',
                integrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_module_logs_project (project_id),
                INDEX idx_module_logs_module (module_id),
                INDEX idx_module_logs_status (integration_status)
            );
            
            -- Knowledge flow logs
            CREATE TABLE IF NOT EXISTS knowledge_flow_logs (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                request_type VARCHAR(50) NOT NULL,
                source_agent VARCHAR(255),
                target_agent VARCHAR(255),
                knowledge_type VARCHAR(100),
                query TEXT,
                response JSONB,
                approval_status VARCHAR(50) DEFAULT 'pending',
                approved_by VARCHAR(255),
                processing_time_ms INTEGER,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_knowledge_logs_source (source_agent),
                INDEX idx_knowledge_logs_type (knowledge_type),
                INDEX idx_knowledge_logs_status (approval_status)
            );
            
            -- Build process logs
            CREATE TABLE IF NOT EXISTS build_process_logs (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                build_id VARCHAR(255) UNIQUE NOT NULL,
                project_id UUID NOT NULL,
                build_status VARCHAR(50),
                modules_count INTEGER,
                modules_integrated INTEGER,
                modules_failed INTEGER,
                build_time_seconds FLOAT,
                artifacts JSONB DEFAULT '[]',
                error_log TEXT,
                metadata JSONB DEFAULT '{}',
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                INDEX idx_build_logs_project (project_id),
                INDEX idx_build_logs_build (build_id),
                INDEX idx_build_logs_status (build_status)
            );
            
            -- Agent interaction logs
            CREATE TABLE IF NOT EXISTS agent_interaction_logs (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                interaction_type VARCHAR(100) NOT NULL,
                source_agent VARCHAR(255),
                target_agent VARCHAR(255),
                action VARCHAR(100),
                request_data JSONB,
                response_data JSONB,
                status_code INTEGER,
                response_time_ms INTEGER,
                success BOOLEAN,
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_interaction_logs_source (source_agent),
                INDEX idx_interaction_logs_target (target_agent),
                INDEX idx_interaction_logs_type (interaction_type)
            );
            
            -- Directory structure snapshots
            CREATE TABLE IF NOT EXISTS directory_structure_snapshots (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                project_id UUID NOT NULL,
                structure JSONB NOT NULL,
                file_count INTEGER,
                total_size BIGINT,
                snapshot_type VARCHAR(50) DEFAULT 'periodic',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_directory_snapshots_project (project_id),
                INDEX idx_directory_snapshots_created (created_at DESC)
            );
        """)
    
    async def _load_caches(self):
        """Load recent data into memory caches"""
        # Load recent file locations
        recent_files = await self.database.execute_query("""
            SELECT * FROM file_location_logs
            WHERE created_at > NOW() - INTERVAL '7 days'
            ORDER BY created_at DESC
            LIMIT 1000
        """)
        
        for file_log in recent_files:
            self.file_location_cache[str(file_log['id'])] = dict(file_log)
    
    # =========================================================================
    # PROJECT EVENT LOGGING
    # =========================================================================
    
    async def log_project_event(
        self,
        project_id: str,
        event_type: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        severity: str = "info",
        category: str = "general"
    ):
        """Log project event"""
        try:
            query = """
                INSERT INTO project_event_logs 
                (project_id, event_type, event_category, severity, details, user_id, agent_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """
            
            result = await self.database.execute_single(
                query,
                project_id,
                event_type,
                category,
                severity,
                json.dumps(details),
                user_id,
                agent_id
            )
            
            # Add to recent cache
            self.recent_logs_cache[project_id].append({
                'id': str(result['id']),
                'event_type': event_type,
                'details': details,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Keep cache size limited
            if len(self.recent_logs_cache[project_id]) > 100:
                self.recent_logs_cache[project_id] = self.recent_logs_cache[project_id][-100:]
            
        except Exception as e:
            logger.error(f"Failed to log project event: {e}")
    
    async def get_project_logs(
        self,
        project_id: str,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[str] = None
    ) -> List[Dict]:
        """Get project logs with filtering"""
        query = "SELECT * FROM project_event_logs WHERE project_id = $1"
        params = [project_id]
        
        if event_type:
            query += " AND event_type = $2"
            params.append(event_type)
        
        query += f" ORDER BY timestamp DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])
        
        logs = await self.database.execute_query(query, *params)
        return [dict(log) for log in logs]
    
    # =========================================================================
    # FILE LOCATION TRACKING
    # =========================================================================
    
    async def track_file_location(
        self,
        project_id: str,
        file_path: str,
        module_id: Optional[str] = None,
        file_type: Optional[str] = None,
        size: Optional[int] = None,
        checksum: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track file location in project"""
        try:
            query = """
                INSERT INTO file_location_logs 
                (project_id, file_path, module_id, file_type, size, checksum, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (project_id, file_path) 
                DO UPDATE SET 
                    module_id = EXCLUDED.module_id,
                    file_type = EXCLUDED.file_type,
                    size = EXCLUDED.size,
                    checksum = EXCLUDED.checksum,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """
            
            result = await self.database.execute_single(
                query,
                project_id,
                file_path,
                module_id,
                file_type,
                size,
                checksum,
                json.dumps(metadata or {})
            )
            
            # Update cache
            cache_key = str(result['id'])
            self.file_location_cache[cache_key] = {
                'project_id': project_id,
                'file_path': file_path,
                'module_id': module_id,
                'file_type': file_type,
                'size': size,
                'checksum': checksum
            }
            
            # Update directory structure
            await self._update_directory_structure(project_id, file_path, 'add')
            
        except Exception as e:
            logger.error(f"Failed to track file location: {e}")
    
    async def get_file_location(self, project_id: str, file_path: str) -> Optional[Dict]:
        """Get file location info"""
        query = """
            SELECT * FROM file_location_logs 
            WHERE project_id = $1 AND file_path = $2
        """
        
        result = await self.database.execute_single(query, project_id, file_path)
        return dict(result) if result else None
    
    async def get_project_files(self, project_id: str) -> List[Dict]:
        """Get all files in project"""
        query = """
            SELECT * FROM file_location_logs 
            WHERE project_id = $1
            ORDER BY file_path
        """
        
        files = await self.database.execute_query(query, project_id)
        return [dict(f) for f in files]
    
    # =========================================================================
    # MODULE INTEGRATION LOGGING
    # =========================================================================
    
    async def log_module_integration(
        self,
        project_id: str,
        module_id: str,
        submission_id: Optional[str],
        module_name: str,
        integration_status: str,
        integration_method: str,
        file_paths: List[str],
        dependencies: List[str],
        quality_score: Optional[float] = None,
        integration_time: Optional[float] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log module integration"""
        try:
            query = """
                INSERT INTO module_integration_logs (
                    project_id, module_id, submission_id, module_name,
                    integration_status, integration_method, file_paths,
                    dependencies, quality_score, integration_time_seconds,
                    error_message, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id
            """
            
            await self.database.execute_single(
                query,
                project_id,
                module_id,
                submission_id,
                module_name,
                integration_status,
                integration_method,
                json.dumps(file_paths),
                json.dumps(dependencies),
                quality_score,
                integration_time,
                error_message,
                json.dumps(metadata or {})
            )
            
            # Log as project event
            await self.log_project_event(
                project_id=project_id,
                event_type="module_integrated",
                details={
                    'module_id': module_id,
                    'module_name': module_name,
                    'status': integration_status,
                    'files': file_paths
                },
                category="integration",
                severity="info" if integration_status == "integrated" else "error"
            )
            
        except Exception as e:
            logger.error(f"Failed to log module integration: {e}")
    
    async def get_module_logs(self, module_id: str) -> List[Dict]:
        """Get logs for specific module"""
        query = """
            SELECT * FROM module_integration_logs 
            WHERE module_id = $1
            ORDER BY integrated_at DESC
        """
        
        logs = await self.database.execute_query(query, module_id)
        return [dict(log) for log in logs]
    
    # =========================================================================
    # KNOWLEDGE FLOW LOGGING
    # =========================================================================
    
    async def log_knowledge_request(
        self,
        agent_id: str,
        knowledge_type: str,
        query: str,
        target_agent: str = "learning_agent"
    ):
        """Log knowledge request"""
        try:
            sql = """
                INSERT INTO knowledge_flow_logs (
                    request_type, source_agent, target_agent, 
                    knowledge_type, query
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """
            
            result = await self.database.execute_single(
                sql,
                "request",
                agent_id,
                target_agent,
                knowledge_type,
                query
            )
            
            return str(result['id'])
            
        except Exception as e:
            logger.error(f"Failed to log knowledge request: {e}")
            return None
    
    async def log_knowledge_response(
        self,
        request_id: str,
        response: Dict[str, Any],
        approval_status: str,
        approved_by: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ):
        """Log knowledge response"""
        try:
            query = """
                UPDATE knowledge_flow_logs
                SET response = $1,
                    approval_status = $2,
                    approved_by = $3,
                    processing_time_ms = $4
                WHERE id = $5
            """
            
            await self.database.execute_command(
                query,
                json.dumps(response),
                approval_status,
                approved_by,
                processing_time_ms,
                request_id
            )
            
        except Exception as e:
            logger.error(f"Failed to log knowledge response: {e}")
    
    async def log_knowledge_contribution(
        self,
        module_id: str,
        knowledge_data: Dict[str, Any]
    ):
        """Log knowledge contribution"""
        try:
            query = """
                INSERT INTO knowledge_flow_logs (
                    request_type, source_agent, target_agent,
                    knowledge_type, query, response, approval_status
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            
            await self.database.execute_single(
                query,
                "contribution",
                "project_agent",
                "learning_agent",
                knowledge_data.get('type', 'module_knowledge'),
                f"Contribution from module {module_id}",
                json.dumps(knowledge_data),
                "auto_approved"
            )
            
        except Exception as e:
            logger.error(f"Failed to log knowledge contribution: {e}")
    
    async def get_knowledge_flow_logs(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get knowledge flow logs"""
        if agent_id:
            query = """
                SELECT * FROM knowledge_flow_logs 
                WHERE source_agent = $1 OR target_agent = $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            logs = await self.database.execute_query(query, agent_id, limit)
        else:
            query = """
                SELECT * FROM knowledge_flow_logs 
                ORDER BY created_at DESC
                LIMIT $1
            """
            logs = await self.database.execute_query(query, limit)
        
        return [dict(log) for log in logs]
    
    # =========================================================================
    # BUILD PROCESS LOGGING
    # =========================================================================
    
    async def log_build_event(
        self,
        build_id: str,
        project_id: str,
        event_type: str,
        details: Dict[str, Any]
    ):
        """Log build event"""
        try:
            # Check if build record exists
            existing = await self.database.execute_single(
                "SELECT id FROM build_process_logs WHERE build_id = $1",
                build_id
            )
            
            if not existing:
                # Create new build record
                query = """
                    INSERT INTO build_process_logs (
                        build_id, project_id, build_status, started_at, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5)
                """
                
                await self.database.execute_command(
                    query,
                    build_id,
                    project_id,
                    "started",
                    datetime.utcnow(),
                    json.dumps(details)
                )
            else:
                # Update existing record based on event type
                if event_type == "build_completed":
                    query = """
                        UPDATE build_process_logs
                        SET build_status = 'completed',
                            completed_at = $1,
                            build_time_seconds = $2,
                            modules_integrated = $3,
                            artifacts = $4
                        WHERE build_id = $5
                    """
                    
                    await self.database.execute_command(
                        query,
                        datetime.utcnow(),
                        details.get('build_time_seconds'),
                        details.get('modules_integrated'),
                        json.dumps(details.get('artifacts', [])),
                        build_id
                    )
                
                elif event_type == "build_failed":
                    query = """
                        UPDATE build_process_logs
                        SET build_status = 'failed',
                            completed_at = $1,
                            error_log = $2,
                            modules_failed = $3
                        WHERE build_id = $4
                    """
                    
                    await self.database.execute_command(
                        query,
                        datetime.utcnow(),
                        details.get('error_message'),
                        details.get('modules_failed', 0),
                        build_id
                    )
            
            # Also log as project event
            await self.log_project_event(
                project_id=project_id,
                event_type=event_type,
                details=details,
                category="build"
            )
            
        except Exception as e:
            logger.error(f"Failed to log build event: {e}")
    
    async def get_build_logs(self, project_id: str) -> List[Dict]:
        """Get build logs for project"""
        query = """
            SELECT * FROM build_process_logs 
            WHERE project_id = $1
            ORDER BY started_at DESC
        """
        
        logs = await self.database.execute_query(query, project_id)
        return [dict(log) for log in logs]
    
    # =========================================================================
    # AGENT INTERACTION LOGGING
    # =========================================================================
    
    async def log_agent_interaction(
        self,
        interaction_type: str,
        source_agent: str,
        target_agent: str,
        action: str,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log agent interaction"""
        try:
            query = """
                INSERT INTO agent_interaction_logs (
                    interaction_type, source_agent, target_agent, action,
                    request_data, response_data, status_code, response_time_ms,
                    success, error_message
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """
            
            await self.database.execute_command(
                query,
                interaction_type,
                source_agent,
                target_agent,
                action,
                json.dumps(request_data or {}),
                json.dumps(response_data or {}),
                status_code,
                response_time_ms,
                success,
                error_message
            )
            
        except Exception as e:
            logger.error(f"Failed to log agent interaction: {e}")
    
    async def get_agent_interactions(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get agent interaction logs"""
        if agent_id:
            query = """
                SELECT * FROM agent_interaction_logs 
                WHERE source_agent = $1 OR target_agent = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """
            logs = await self.database.execute_query(query, agent_id, limit)
        else:
            query = """
                SELECT * FROM agent_interaction_logs 
                ORDER BY timestamp DESC
                LIMIT $1
            """
            logs = await self.database.execute_query(query, limit)
        
        return [dict(log) for log in logs]
    
    # =========================================================================
    # DIRECTORY STRUCTURE TRACKING
    # =========================================================================
    
    async def _update_directory_structure(
        self,
        project_id: str,
        file_path: str,
        operation: str
    ):
        """Update directory structure tracking"""
        if project_id not in self.directory_structure_cache:
            self.directory_structure_cache[project_id] = {
                'files': {},
                'directories': set()
            }
        
        structure = self.directory_structure_cache[project_id]
        
        if operation == 'add':
            structure['files'][file_path] = {
                'added_at': datetime.utcnow().isoformat()
            }
            
            # Track directories
            path_parts = Path(file_path).parts
            for i in range(1, len(path_parts)):
                dir_path = str(Path(*path_parts[:i]))
                structure['directories'].add(dir_path)
        
        elif operation == 'remove':
            if file_path in structure['files']:
                del structure['files'][file_path]
    
    async def save_directory_snapshot(self, project_id: str):
        """Save directory structure snapshot"""
        try:
            if project_id not in self.directory_structure_cache:
                return
            
            structure = self.directory_structure_cache[project_id]
            structure_json = {
                'files': structure['files'],
                'directories': list(structure['directories'])
            }
            
            query = """
                INSERT INTO directory_structure_snapshots (
                    project_id, structure, file_count, snapshot_type
                )
                VALUES ($1, $2, $3, $4)
            """
            
            await self.database.execute_command(
                query,
                project_id,
                json.dumps(structure_json),
                len(structure['files']),
                'periodic'
            )
            
        except Exception as e:
            logger.error(f"Failed to save directory snapshot: {e}")
    
    async def get_directory_structure(self, project_id: str) -> Dict:
        """Get current directory structure"""
        # Try cache first
        if project_id in self.directory_structure_cache:
            return self.directory_structure_cache[project_id]
        
        # Get all files for project
        files = await self.get_project_files(project_id)
        
        structure = {
            'files': {},
            'directories': set()
        }
        
        for file_info in files:
            file_path = file_info['file_path']
            structure['files'][file_path] = {
                'module_id': str(file_info.get('module_id')) if file_info.get('module_id') else None,
                'file_type': file_info.get('file_type'),
                'size': file_info.get('size'),
                'created_at': file_info['created_at'].isoformat()
            }
            
            # Track directories
            path_parts = Path(file_path).parts
            for i in range(1, len(path_parts)):
                dir_path = str(Path(*path_parts[:i]))
                structure['directories'].add(dir_path)
        
        # Convert set to list for JSON serialization
        structure['directories'] = list(structure['directories'])
        
        # Update cache
        self.directory_structure_cache[project_id] = structure
        
        return structure
    
    # =========================================================================
    # SUBMISSION LOGGING
    # =========================================================================
    
    async def log_submission_event(
        self,
        submission_id: str,
        project_id: str,
        agent_id: str,
        event_type: str,
        details: Dict[str, Any]
    ):
        """Log submission event"""
        await self.log_project_event(
            project_id=project_id,
            event_type=event_type,
            details={
                'submission_id': submission_id,
                'agent_id': agent_id,
                **details
            },
            agent_id=agent_id,
            category="submission"
        )
    
    # =========================================================================
    # DAILY SUMMARY & SYNCHRONIZATION
    # =========================================================================
    
    async def get_daily_summary(self) -> Dict[str, Any]:
        """Get comprehensive daily summary for synchronization"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        summary = {
            'period': 'daily',
            'start_time': cutoff_time.isoformat(),
            'end_time': datetime.utcnow().isoformat(),
            'project_events': [],
            'module_integrations': [],
            'knowledge_flow': [],
            'builds': [],
            'agent_interactions': [],
            'statistics': {}
        }
        
        # Get project events
        events_query = """
            SELECT * FROM project_event_logs 
            WHERE timestamp > $1
            ORDER BY timestamp DESC
        """
        summary['project_events'] = [
            dict(e) for e in await self.database.execute_query(events_query, cutoff_time)
        ]
        
        # Get module integrations
        modules_query = """
            SELECT * FROM module_integration_logs 
            WHERE integrated_at > $1
            ORDER BY integrated_at DESC
        """
        summary['module_integrations'] = [
            dict(m) for m in await self.database.execute_query(modules_query, cutoff_time)
        ]
        
        # Get knowledge flow
        knowledge_query = """
            SELECT * FROM knowledge_flow_logs 
            WHERE created_at > $1
            ORDER BY created_at DESC
        """
        summary['knowledge_flow'] = [
            dict(k) for k in await self.database.execute_query(knowledge_query, cutoff_time)
        ]
        
        # Get builds
        builds_query = """
            SELECT * FROM build_process_logs 
            WHERE started_at > $1
            ORDER BY started_at DESC
        """
        summary['builds'] = [
            dict(b) for b in await self.database.execute_query(builds_query, cutoff_time)
        ]
        
        # Get agent interactions
        interactions_query = """
            SELECT * FROM agent_interaction_logs 
            WHERE timestamp > $1
            ORDER BY timestamp DESC
        """
        summary['agent_interactions'] = [
            dict(i) for i in await self.database.execute_query(interactions_query, cutoff_time)
        ]
        
        # Calculate statistics
        summary['statistics'] = {
            'total_events': len(summary['project_events']),
            'modules_integrated': len([m for m in summary['module_integrations'] 
                                      if m['integration_status'] == 'integrated']),
            'modules_failed': len([m for m in summary['module_integrations'] 
                                  if m['integration_status'] == 'failed']),
            'knowledge_requests': len([k for k in summary['knowledge_flow'] 
                                      if k['request_type'] == 'request']),
            'knowledge_contributions': len([k for k in summary['knowledge_flow'] 
                                           if k['request_type'] == 'contribution']),
            'builds_completed': len([b for b in summary['builds'] 
                                    if b['build_status'] == 'completed']),
            'builds_failed': len([b for b in summary['builds'] 
                                 if b['build_status'] == 'failed']),
            'agent_interactions_total': len(summary['agent_interactions']),
            'agent_interactions_successful': len([i for i in summary['agent_interactions'] 
                                                  if i['success']])
        }
        
        return summary
    
    # =========================================================================
    # CLEANUP & MAINTENANCE
    # =========================================================================
    
    async def cleanup_old_logs(self):
        """Clean up logs older than retention period"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.log_retention_days)
            
            tables = [
                'project_event_logs',
                'agent_interaction_logs',
                'knowledge_flow_logs'
            ]
            
            for table in tables:
                query = f"DELETE FROM {table} WHERE timestamp < $1"
                await self.database.execute_command(query, cutoff_date)
            
            logger.info(f"Cleaned up logs older than {self.log_retention_days} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
    
    async def health_check(self) -> bool:
        """Check log manager health"""
        return self.is_initialized
    
    async def shutdown(self):
        """Shutdown log manager"""
        # Save all cached directory structures
        for project_id in self.directory_structure_cache:
            await self.save_directory_snapshot(project_id)
        
        logger.info("Log manager shutdown complete")