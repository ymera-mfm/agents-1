# integrations/manager.py
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import httpx
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from atlassian import Jira
from github import Github
from google.cloud import bigquery
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
import boto3
from simple_salesforce import Salesforce
from celery import Celery
import json

logger = logging.getLogger(__name__)

@dataclass
class IntegrationConfig:
    name: str
    type: str
    enabled: bool
    config: Dict[str, Any]
    webhook_url: Optional[str] = None
    api_key: Optional[str] = None
    oauth_config: Optional[Dict[str, Any]] = None

class IntegrationManager:
    """Comprehensive third-party integration manager"""
    
    def __init__(self):
        self.integrations = {}
        self.celery_app = Celery('integrations', broker=os.getenv('CELERY_BROKER_URL'))
        self._register_integrations()
        self._setup_celery_tasks()
    
    def _register_integrations(self):
        """Register all available integrations"""
        # Communication integrations
        self.integrations['slack'] = {
            'class': SlackIntegration,
            'config': IntegrationConfig(
                name="slack",
                type="communication",
                enabled=os.getenv('SLACK_ENABLED', 'false').lower() == 'true',
                config={
                    'bot_token': os.getenv('SLACK_BOT_TOKEN'),
                    'default_channel': os.getenv('SLACK_DEFAULT_CHANNEL')
                }
            )
        }
        
        self.integrations['microsoft_teams'] = {
            'class': TeamsIntegration,
            'config': IntegrationConfig(
                name="microsoft_teams",
                type="communication",
                enabled=os.getenv('TEAMS_ENABLED', 'false').lower() == 'true',
                config={
                    'webhook_url': os.getenv('TEAMS_WEBHOOK_URL')
                }
            )
        }
        
        # Project management integrations
        self.integrations['jira'] = {
            'class': JiraIntegration,
            'config': IntegrationConfig(
                name="jira",
                type="project_management",
                enabled=os.getenv('JIRA_ENABLED', 'false').lower() == 'true',
                config={
                    'url': os.getenv('JIRA_URL'),
                    'username': os.getenv('JIRA_USERNAME'),
                    'api_token': os.getenv('JIRA_API_TOKEN')
                }
            )
        }
        
        self.integrations['servicenow'] = {
            'class': ServiceNowIntegration,
            'config': IntegrationConfig(
                name="servicenow",
                type="project_management",
                enabled=os.getenv('SERVICENOW_ENABLED', 'false').lower() == 'true',
                config={
                    'instance': os.getenv('SERVICENOW_INSTANCE'),
                    'username': os.getenv('SERVICENOW_USERNAME'),
                    'password': os.getenv('SERVICENOW_PASSWORD')
                }
            )
        }
        
        # Code repository integrations
        self.integrations['github'] = {
            'class': GitHubIntegration,
            'config': IntegrationConfig(
                name="github",
                type="code_repository",
                enabled=os.getenv('GITHUB_ENABLED', 'false').lower() == 'true',
                config={
                    'access_token': os.getenv('GITHUB_ACCESS_TOKEN'),
                    'default_org': os.getenv('GITHUB_DEFAULT_ORG')
                }
            )
        }
        
        self.integrations['gitlab'] = {
            'class': GitLabIntegration,
            'config': IntegrationConfig(
                name="gitlab",
                type="code_repository",
                enabled=os.getenv('GITLAB_ENABLED', 'false').lower() == 'true',
                config={
                    'url': os.getenv('GITLAB_URL'),
                    'access_token': os.getenv('GITLAB_ACCESS_TOKEN')
                }
            )
        }
        
        # Cloud provider integrations
        self.integrations['aws'] = {
            'class': AWSIntegration,
            'config': IntegrationConfig(
                name="aws",
                type="cloud_provider",
                enabled=os.getenv('AWS_ENABLED', 'false').lower() == 'true',
                config={
                    'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
                    'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
                    'region': os.getenv('AWS_REGION', 'us-east-1')
                }
            )
        }
        
        self.integrations['azure'] = {
            'class': AzureIntegration,
            'config': IntegrationConfig(
                name="azure",
                type="cloud_provider",
                enabled=os.getenv('AZURE_ENABLED', 'false').lower() == 'true',
                config={
                    'tenant_id': os.getenv('AZURE_TENANT_ID'),
                    'client_id': os.getenv('AZURE_CLIENT_ID'),
                    'client_secret': os.getenv('AZURE_CLIENT_SECRET'),
                    'subscription_id': os.getenv('AZURE_SUBSCRIPTION_ID')
                }
            )
        }
        
        self.integrations['gcp'] = {
            'class': GCPIntegration,
            'config': IntegrationConfig(
                name="gcp",
                type="cloud_provider",
                enabled=os.getenv('GCP_ENABLED', 'false').lower() == 'true',
                config={
                    'project_id': os.getenv('GCP_PROJECT_ID'),
                    'credentials_path': os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                }
            )
        }
        
        # CRM integration
        self.integrations['salesforce'] = {
            'class': SalesforceIntegration,
            'config': IntegrationConfig(
                name="salesforce",
                type="crm",
                enabled=os.getenv('SALESFORCE_ENABLED', 'false').lower() == 'true',
                config={
                    'username': os.getenv('SALESFORCE_USERNAME'),
                    'password': os.getenv('SALESFORCE_PASSWORD'),
                    'security_token': os.getenv('SALESFORCE_SECURITY_TOKEN'),
                    'domain': os.getenv('SALESFORCE_DOMAIN', 'login')
                }
            )
        }
    
    def _setup_celery_tasks(self):
        """Setup Celery tasks for async integration processing"""
        
        @self.celery_app.task
        def process_integration_async(integration_name: str, action: str, data: Dict[str, Any]):
            """Process integration asynchronously"""
            return asyncio.run(self._process_integration(integration_name, action, data))
        
        self.celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
        )
    
    async def execute_integration(self, integration_name: str, action: str, 
                                data: Dict[str, Any], is_async: bool = False) -> Any:
        """Execute integration action"""
        if integration_name not in self.integrations:
            raise ValueError(f"Integration {integration_name} not found")
        
        integration = self.integrations[integration_name]
        
        if not integration['config'].enabled:
            raise ValueError(f"Integration {integration_name} is not enabled")
        
        if is_async:
            # Process asynchronously via Celery
            return self.celery_app.send_task(
                'process_integration_async',
                args=[integration_name, action, data]
            )
        else:
            # Process synchronously
            return await self._process_integration(integration_name, action, data)
    
    async def _process_integration(self, integration_name: str, action: str, 
                                 data: Dict[str, Any]) -> Any:
        """Process integration action"""
        integration = self.integrations[integration_name]
        integration_class = integration['class']()
        integration_config = integration['config']
        
        try:
            # Initialize integration
            await integration_class.initialize(integration_config)
            
            # Execute action
            if hasattr(integration_class, action):
                result = await getattr(integration_class, action)(data)
                return result
            else:
                raise ValueError(f"Action {action} not supported for {integration_name}")
                
        except Exception as e:
            logger.error(f"Integration {integration_name} failed: {e}")
            raise
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all integrations"""
        status = {}
        
        for name, integration in self.integrations.items():
            try:
                integration_class = integration['class']()
                await integration_class.initialize(integration['config'])
                
                status[name] = {
                    'enabled': integration['config'].enabled,
                    'status': 'connected',
                    'last_checked': datetime.utcnow().isoformat()
                }
            except Exception as e:
                status[name] = {
                    'enabled': integration['config'].enabled,
                    'status': 'disconnected',
                    'error': str(e),
                    'last_checked': datetime.utcnow().isoformat()
                }
        
        return status

# Integration base class
class BaseIntegration:
    """Base class for all integrations"""
    
    async def initialize(self, config: IntegrationConfig):
        """Initialize integration with configuration"""
        self.config = config
        await self._setup_client()
    
    async def _setup_client(self):
        """Setup integration client"""
        raise NotImplementedError("Subclasses must implement _setup_client")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check integration health"""
        return {"status": "unknown"}

# Communication Integrations
class SlackIntegration(BaseIntegration):
    """Slack integration"""
    
    async def _setup_client(self):
        """Setup Slack client"""
        self.client = WebClient(token=self.config.config['bot_token'])
    
    async def send_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to Slack"""
        try:
            channel = data.get('channel', self.config.config['default_channel'])
            message = data['message']
            attachments = data.get('attachments', [])
            
            response = await self.client.chat_postMessage(
                channel=channel,
                text=message,
                attachments=attachments
            )
            
            return {
                'success': True,
                'message_ts': response['ts'],
                'channel': response['channel']
            }
            
        except SlackApiError as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': e.response['error']
            }
    
    async def create_channel(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Slack channel"""
        try:
            response = await self.client.conversations_create(
                name=data['name'],
                is_private=data.get('is_private', False)
            )
            
            return {
                'success': True,
                'channel_id': response['channel']['id'],
                'channel_name': response['channel']['name']
            }
            
        except SlackApiError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Slack integration health"""
        try:
            await self.client.auth_test()
            return {"status": "connected", "workspace": "healthy"}
        except Exception as e:
            return {"status": "disconnected", "error": str(e)}

class TeamsIntegration(BaseIntegration):
    """Microsoft Teams integration"""
    
    async def _setup_client(self):
        """Setup Teams client"""
        self.webhook_url = self.config.config['webhook_url']
    
    async def send_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to Teams"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.webhook_url,
                json=data['message'],
                timeout=30.0
            )
            
            if response.status_code == 200:
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': response.text,
                    'status_code': response.status_code
                }

# Project Management Integrations
class JiraIntegration(BaseIntegration):
    """Jira integration"""
    
    async def _setup_client(self):
        """Setup Jira client"""
        self.client = Jira(
            url=self.config.config['url'],
            username=self.config.config['username'],
            password=self.config.config['api_token'],
            cloud=True
        )
    
    async def create_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Jira issue"""
        try:
            issue = self.client.create_issue(
                project=data['project'],
                summary=data['summary'],
                description=data.get('description', ''),
                issuetype=data.get('issue_type', 'Task'),
                priority=data.get('priority', 'Medium')
            )
            
            return {
                'success': True,
                'issue_key': issue['key'],
                'issue_id': issue['id']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update Jira issue"""
        try:
            self.client.update_issue(
                issue_key=data['issue_key'],
                fields=data['fields']
            )
            
            return {'success': True}
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class ServiceNowIntegration(BaseIntegration):
    """ServiceNow integration"""
    
    async def _setup_client(self):
        """Setup ServiceNow client"""
        self.base_url = f"https://{self.config.config['instance']}.service-now.com"
        self.auth = (self.config.config['username'], self.config.config['password'])
    
    async def create_incident(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create ServiceNow incident"""
        async with httpx.AsyncClient(auth=self.auth) as client:
            response = await client.post(
                f"{self.base_url}/api/now/table/incident",
                json=data,
                timeout=30.0
            )
            
            if response.status_code == 201:
                return {
                    'success': True,
                    'incident_number': response.json()['result']['number']
                }
            else:
                return {
                    'success': False,
                    'error': response.text,
                    'status_code': response.status_code
                }

# Code Repository Integrations
class GitHubIntegration(BaseIntegration):
    """GitHub integration"""
    
    async def _setup_client(self):
        """Setup GitHub client"""
        self.client = Github(self.config.config['access_token'])
    
    async def create_repository(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitHub repository"""
        try:
            org = self.client.get_organization(self.config.config['default_org'])
            repo = org.create_repo(
                name=data['name'],
                description=data.get('description', ''),
                private=data.get('private', True),
                auto_init=data.get('auto_init', True)
            )
            
            return {
                'success': True,
                'repo_name': repo.name,
                'repo_url': repo.html_url
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitHub issue"""
        try:
            repo = self.client.get_repo(data['repository'])
            issue = repo.create_issue(
                title=data['title'],
                body=data.get('body', ''),
                labels=data.get('labels', [])
            )
            
            return {
                'success': True,
                'issue_number': issue.number,
                'issue_url': issue.html_url
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class GitLabIntegration(BaseIntegration):
    """GitLab integration"""
    
    async def _setup_client(self):
        """Setup GitLab client"""
        import gitlab
        self.client = gitlab.GitLab(
            self.config.config['url'],
            private_token=self.config.config['access_token']
        )
    
    async def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitLab project"""
        try:
            project = self.client.projects.create({
                'name': data['name'],
                'description': data.get('description', ''),
                'visibility': 'private' if data.get('private', True) else 'public'
            })
            
            return {
                'success': True,
                'project_id': project.id,
                'project_url': project.web_url
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Cloud Provider Integrations
class AWSIntegration(BaseIntegration):
    """AWS integration"""
    
    async def _setup_client(self):
        """Setup AWS clients"""
        self.session = boto3.Session(
            aws_access_key_id=self.config.config['access_key'],
            aws_secret_access_key=self.config.config['secret_key'],
            region_name=self.config.config['region']
        )
        
        self.s3 = self.session.client('s3')
        self.ec2 = self.session.client('ec2')
        self.lambda_client = self.session.client('lambda')
    
    async def create_s3_bucket(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create S3 bucket"""
        try:
            bucket_name = data['bucket_name']
            self.s3.create_bucket(Bucket=bucket_name)
            
            return {
                'success': True,
                'bucket_name': bucket_name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_lambda_function(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Lambda function"""
        try:
            response = self.lambda_client.create_function(
                FunctionName=data['function_name'],
                Runtime=data['runtime'],
                Role=data['role'],
                Handler=data['handler'],
                Code={'ZipFile': data['code']},
                Description=data.get('description', '')
            )
            
            return {
                'success': True,
                'function_arn': response['FunctionArn']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class AzureIntegration(BaseIntegration):
    """Azure integration"""
    
    async def _setup_client(self):
        """Setup Azure clients"""
        credential = DefaultAzureCredential()
        self.resource_client = ResourceManagementClient(
            credential,
            self.config.config['subscription_id']
        )
    
    async def create_resource_group(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Azure resource group"""
        try:
            rg_result = self.resource_client.resource_groups.create_or_update(
                data['resource_group_name'],
                {"location": data['location']}
            )
            
            return {
                'success': True,
                'resource_group_name': rg_result.name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class GCPIntegration(BaseIntegration):
    """Google Cloud Platform integration"""
    
    async def _setup_client(self):
        """Setup GCP clients"""
        self.bigquery_client = bigquery.Client.from_service_account_json(
            self.config.config['credentials_path']
        )
    
    async def create_bigquery_dataset(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create BigQuery dataset"""
        try:
            dataset_id = f"{self.config.config['project_id']}.{data['dataset_id']}"
            dataset = bigquery.Dataset(dataset_id)
            dataset.location = data.get('location', 'US')
            
            dataset = self.bigquery_client.create_dataset(dataset, timeout=30)
            
            return {
                'success': True,
                'dataset_id': dataset.dataset_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# CRM Integration
class SalesforceIntegration(BaseIntegration):
    """Salesforce integration"""
    
    async def _setup_client(self):
        """Setup Salesforce client"""
        self.client = Salesforce(
            username=self.config.config['username'],
            password=self.config.config['password'],
            security_token=self.config.config['security_token'],
            domain=self.config.config['domain']
        )
    
    async def create_lead(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Salesforce lead"""
        try:
            result = self.client.Lead.create(data)
            
            return {
                'success': True,
                'lead_id': result['id']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_opportunity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Salesforce opportunity"""
        try:
            result = self.client.Opportunity.create(data)
            
            return {
                'success': True,
                'opportunity_id': result['id']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Integration API endpoints
@app.get("/integrations", tags=["Integrations"])
async def list_integrations(
    current_user: UserRecord = Depends(get_current_active_user)
):
    """List all available integrations"""
    manager = IntegrationManager()
    status = await manager.get_integration_status()
    return status

@app.post("/integrations/{integration_name}/{action}", tags=["Integrations"])
async def execute_integration(
    integration_name: str,
    action: str,
    data: Dict[str, Any],
    is_async: bool = Query(False),
    current_user: UserRecord = Depends(get_current_active_user)
):
    """Execute integration action"""
    manager = IntegrationManager()
    result = await manager.execute_integration(integration_name, action, data, is_async)
    return result

@app.get("/integrations/health", tags=["Integrations"])
async def integrations_health(
    current_user: UserRecord = Depends(get_current_active_user)
):
    """Get integrations health status"""
    manager = IntegrationManager()
    status = await manager.get_integration_status()
    return status

# API Gateway initialization
def create_app():
    """Create FastAPI app with API Gateway"""
    app = FastAPI(
        title="YMERA Enterprise API Gateway",
        description="Enterprise-grade API gateway with advanced management features",
        version="2.0.0",
        docs_url=None,  # We'll use custom docs
        redoc_url=None
    )
    
    # Initialize API Gateway
    gateway = EnterpriseAPIGateway(app)
    
    return app