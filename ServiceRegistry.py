# Service Discovery and Configuration
class ServiceRegistry:
    def __init__(self):
        self.services = {}
        self.consul_client = None
        self.init_consul()
    
    def init_consul(self):
        """Initialize Consul for service discovery"""
        try:
            import consul
            self.consul_client = consul.Consul(
                host=os.getenv('CONSUL_HOST', 'localhost'),
                port=os.getenv('CONSUL_PORT', 8500)
            )
        except ImportError:
            logger.warning("Consul not available, using local service registry")
    
    async def register_service(self, service_name: str, service_url: str, tags: List[str] = None):
        """Register a service with the registry"""
        if self.consul_client:
            self.consul_client.agent.service.register(
                service_name,
                address=service_url,
                tags=tags or []
            )
        self.services[service_name] = service_url
    
    async def discover_service(self, service_name: str) -> str:
        """Discover service URL"""
        if self.consul_client:
            try:
                _, services = self.consul_client.health.service(service_name)
                if services:
                    return random.choice([s['Service']['Address'] for s in services])
            except Exception:
                logger.warning(f"Consul discovery failed for {service_name}")
        
        return self.services.get(service_name)

# Service base class
class MicroService:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.service_registry = ServiceRegistry()
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def call_service(self, target_service: str, endpoint: str, method: str = "GET", 
                         data: Any = None, headers: Dict[str, str] = None) -> Any:
        """Call another microservice"""
        service_url = await self.service_registry.discover_service(target_service)
        if not service_url:
            raise ServiceUnavailableError(f"Service {target_service} not available")
        
        url = f"{service_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = await self.http_client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await self.http_client.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = await self.http_client.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = await self.http_client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.RequestError as e:
            logger.error(f"Service call failed to {target_service}: {e}")
            raise ServiceUnavailableError(f"Service {target_service} unavailable")
    
    async def health_check(self) -> Dict[str, Any]:
        """Service health check"""
        return {
            "status": "healthy",
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat()
        }

# Authentication Service
class AuthenticationService(MicroService):
    def __init__(self):
        super().__init__("authentication-service")
        self.oauth_providers = self._init_oauth_providers()
    
    def _init_oauth_providers(self) -> Dict[str, Any]:
        """Initialize OAuth providers"""
        return {
            "google": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "authorize_url": "https://accounts.google.com/o/oauth2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo"
            },
            # Add other providers...
        }
    
    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user with credentials"""
        # Implementation would validate credentials and return JWT
        pass
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token"""
        # Implementation would validate token and return user info
        pass

# Project Management Service
class ProjectManagementService(MicroService):
    def __init__(self):
        super().__init__("project-management-service")
        self.db = DatabaseUtils()
    
    async def create_project(self, project_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new project"""
        async with self.db.get_session() as session:
            project = ProjectRecord(
                **project_data,
                owner_id=user_id,
                created_at=datetime.utcnow()
            )
            session.add(project)
            await session.commit()
            await session.refresh(project)
            return project.to_dict()
    
    async def get_project(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """Get project details"""
        async with self.db.get_session() as session:
            project = await session.get(ProjectRecord, project_id)
            if not project or project.owner_id != user_id:
                raise NotFoundError("Project not found")
            return project.to_dict()

# Task Orchestration Service
class TaskOrchestrationService(MicroService):
    def __init__(self):
        super().__init__("task-orchestration-service")
        self.task_queue = asyncio.Queue()
        self.worker_pool = []
        self.init_workers()
    
    def init_workers(self):
        """Initialize task workers"""
        for i in range(int(os.getenv('TASK_WORKERS', '5'))):
            worker = asyncio.create_task(self._task_worker(f"worker-{i+1}"))
            self.worker_pool.append(worker)
    
    async def _task_worker(self, worker_id: str):
        """Background task worker"""
        while True:
            try:
                task = await self.task_queue.get()
                logger.info(f"Worker {worker_id} processing task {task['id']}")
                
                # Process task
                await self.process_task(task)
                
                self.task_queue.task_done()
            except Exception as e:
                logger.error(f"Worker {worker_id} failed: {e}")
                await asyncio.sleep(1)  # Prevent tight error loop
    
    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create and queue a new task"""
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "data": task_data,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat()
        }
        
        await self.task_queue.put(task)
        return task
    
    async def process_task(self, task: Dict[str, Any]):
        """Process a task"""
        # Task processing logic would go here
        await asyncio.sleep(random.uniform(0.1, 1.0))  # Simulate work
        
        # Update task status
        task["status"] = "completed"
        task["completed_at"] = datetime.utcnow().isoformat()

# File Management Service
class FileManagementService(MicroService):
    def __init__(self):
        super().__init__("file-management-service")
        self.storage_backend = self._init_storage_backend()
    
    def _init_storage_backend(self):
        """Initialize storage backend (S3, Azure Blob, etc.)"""
        storage_type = os.getenv('FILE_STORAGE_TYPE', 'local')
        
        if storage_type == 's3':
            import boto3
            return boto3.client('s3')
        elif storage_type == 'azure':
            from azure.storage.blob import BlobServiceClient
            return BlobServiceClient.from_connection_string(
                os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            )
        else:
            # Local filesystem
            return None
    
    async def upload_file(self, file_data: bytes, filename: str, metadata: Dict[str, Any] = None) -> str:
        """Upload file to storage"""
        file_id = str(uuid.uuid4())
        
        if self.storage_backend:
            # Cloud storage upload
            if hasattr(self.storage_backend, 'upload_fileobj'):  # S3
                import io
                file_obj = io.BytesIO(file_data)
                self.storage_backend.upload_fileobj(
                    file_obj,
                    os.getenv('S3_BUCKET_NAME'),
                    f"{file_id}/{filename}"
                )
            # Other cloud providers...
        else:
            # Local filesystem
            os.makedirs('uploads', exist_ok=True)
            with open(f"uploads/{file_id}_{filename}", 'wb') as f:
                f.write(file_data)
        
        return file_id
    
    async def download_file(self, file_id: str) -> bytes:
        """Download file from storage"""
        # Implementation would retrieve file from storage
        pass

# Notification Service
class NotificationService(MicroService):
    def __init__(self):
        super().__init__("notification-service")
        self.notification_channels = self._init_channels()
    
    def _init_channels(self) -> Dict[str, Any]:
        """Initialize notification channels"""
        return {
            "email": {
                "enabled": os.getenv('EMAIL_NOTIFICATIONS_ENABLED', 'false').lower() == 'true',
                "provider": os.getenv('EMAIL_PROVIDER', 'smtp')
            },
            "sms": {
                "enabled": os.getenv('SMS_NOTIFICATIONS_ENABLED', 'false').lower() == 'true',
                "provider": os.getenv('SMS_PROVIDER', 'twilio')
            },
            "push": {
                "enabled": os.getenv('PUSH_NOTIFICATIONS_ENABLED', 'false').lower() == 'true',
                "provider": os.getenv('PUSH_PROVIDER', 'fcm')
            }
        }
    
    async def send_notification(self, user_id: str, message: str, 
                              channels: List[str] = None, priority: str = "medium") -> bool:
        """Send notification to user"""
        channels = channels or ["email"]
        
        for channel in channels:
            if channel in self.notification_channels and self.notification_channels[channel]["enabled"]:
                try:
                    if channel == "email":
                        await self._send_email(user_id, message, priority)
                    elif channel == "sms":
                        await self._send_sms(user_id, message, priority)
                    elif channel == "push":
                        await self._send_push(user_id, message, priority)
                except Exception as e:
                    logger.error(f"Failed to send {channel} notification: {e}")
        
        return True
    
    async def _send_email(self, user_id: str, message: str, priority: str):
        """Send email notification"""
        # Email sending implementation
        pass
    
    async def _send_sms(self, user_id: str, message: str, priority: str):
        """Send SMS notification"""
        # SMS sending implementation
        pass
    
    async def _send_push(self, user_id: str, message: str, priority: str):
        """Send push notification"""
        # Push notification implementation
        pass

# Audit Service
class AuditService(MicroService):
    def __init__(self):
        super().__init__("audit-service")
        self.db = DatabaseUtils()
    
    async def log_event(self, event_type: str, user_id: str, resource_type: str, 
                      resource_id: str, details: Dict[str, Any] = None) -> str:
        """Log audit event"""
        event_id = str(uuid.uuid4())
        
        async with self.db.get_session() as session:
            audit_log = AuditLogRecord(
                id=event_id,
                user_id=user_id,
                action=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                timestamp=datetime.utcnow()
            )
            session.add(audit_log)
            await session.commit()
        
        return event_id
    
    async def query_events(self, filters: Dict[str, Any] = None, 
                         limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Query audit events"""
        async with self.db.get_session() as session:
            query = select(AuditLogRecord)
            
            if filters:
                if 'user_id' in filters:
                    query = query.where(AuditLogRecord.user_id == filters['user_id'])
                if 'action' in filters:
                    query = query.where(AuditLogRecord.action == filters['action'])
                if 'start_time' in filters:
                    query = query.where(AuditLogRecord.timestamp >= filters['start_time'])
                if 'end_time' in filters:
                    query = query.where(AuditLogRecord.timestamp <= filters['end_time'])
            
            result = await session.execute(
                query.order_by(AuditLogRecord.timestamp.desc())
                .limit(limit)
                .offset(offset)
            )
            events = result.scalars().all()
            return [event.to_dict() for event in events]

# Analytics Service
class AnalyticsService(MicroService):
    def __init__(self):
        super().__init__("analytics-service")
        self.elasticsearch = self._init_elasticsearch()
    
    def _init_elasticsearch(self):
        """Initialize Elasticsearch client"""
        try:
            from elasticsearch import AsyncElasticsearch
            return AsyncElasticsearch(
                [os.getenv('ELASTICSEARCH_HOST', 'localhost:9200')],
                http_auth=(
                    os.getenv('ELASTICSEARCH_USERNAME'),
                    os.getenv('ELASTICSEARCH_PASSWORD')
                ) if os.getenv('ELASTICSEARCH_USERNAME') else None
            )
        except ImportError:
            logger.warning("Elasticsearch not available")
            return None
    
    async def index_document(self, index_name: str, document: Dict[str, Any], doc_id: str = None):
        """Index document in Elasticsearch"""
        if not self.elasticsearch:
            return
        
        try:
            await self.elasticsearch.index(
                index=index_name,
                id=doc_id or str(uuid.uuid4()),
                document=document
            )
        except Exception as e:
            logger.error(f"Failed to index document: {e}")
    
    async def search_documents(self, index_name: str, query: Dict[str, Any], 
                            size: int = 10, from_: int = 0) -> Dict[str, Any]:
        """Search documents in Elasticsearch"""
        if not self.elasticsearch:
            return {"hits": {"hits": [], "total": {"value": 0}}}
        
        try:
            response = await self.elasticsearch.search(
                index=index_name,
                body={"query": query},
                size=size,
                from_=from_
            )
            return response
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return {"hits": {"hits": [], "total": {"value": 0}}}

# Integration Service
class IntegrationService(MicroService):
    def __init__(self):
        super().__init__("integration-service")
        self.integrations = self._init_integrations()
    
    def _init_integrations(self) -> Dict[str, Any]:
        """Initialize third-party integrations"""
        return {
            "slack": {
                "enabled": os.getenv('SLACK_INTEGRATION_ENABLED', 'false').lower() == 'true',
                "webhook_url": os.getenv('SLACK_WEBHOOK_URL')
            },
            "jira": {
                "enabled": os.getenv('JIRA_INTEGRATION_ENABLED', 'false').lower() == 'true',
                "base_url": os.getenv('JIRA_BASE_URL'),
                "username": os.getenv('JIRA_USERNAME'),
                "api_token": os.getenv('JIRA_API_TOKEN')
            },
            "salesforce": {
                "enabled": os.getenv('SALESFORCE_INTEGRATION_ENABLED', 'false').lower() == 'true',
                "instance_url": os.getenv('SALESFORCE_INSTANCE_URL'),
                "client_id": os.getenv('SALESFORCE_CLIENT_ID'),
                "client_secret": os.getenv('SALESFORCE_CLIENT_SECRET')
            }
        }
    
    async def send_to_slack(self, channel: str, message: str, attachments: List[Dict] = None) -> bool:
        """Send message to Slack"""
        if not self.integrations["slack"]["enabled"]:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "channel": channel,
                    "text": message,
                    "attachments": attachments or []
                }
                response = await client.post(
                    self.integrations["slack"]["webhook_url"],
                    json=payload
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to send to Slack: {e}")
            return False
    
    async def create_jira_issue(self, project_key: str, issue_type: str, 
                              summary: str, description: str) -> Dict[str, Any]:
        """Create JIRA issue"""
        if not self.integrations["jira"]["enabled"]:
            return {"error": "JIRA integration not enabled"}
        
        try:
            async with httpx.AsyncClient() as client:
                auth = (self.integrations["jira"]["username"], 
                       self.integrations["jira"]["api_token"])
                
                payload = {
                    "fields": {
                        "project": {"key": project_key},
                        "issuetype": {"name": issue_type},
                        "summary": summary,
                        "description": description
                    }
                }
                
                response = await client.post(
                    f"{self.integrations['jira']['base_url']}/rest/api/2/issue",
                    json=payload,
                    auth=auth
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to create JIRA issue: {e}")
            return {"error": str(e)}