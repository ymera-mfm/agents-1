"""
DevOps Automation Agent - Specialized agent for DevOps tasks and automation
"""
from typing import Any, Dict, Optional, List
import asyncio
import json
from datetime import datetime, timezone

from base_agent import BaseAgent, MessageType, AgentState
from logger import logger


class DevOpsAgent(BaseAgent):
    """
    Specialized agent for DevOps automation and infrastructure management.
    
    Capabilities:
    - CI/CD pipeline management
    - Infrastructure provisioning
    - Deployment automation
    - Health monitoring and alerting
    - Log analysis
    - Performance optimization
    """
    
    def __init__(self, agent_id: str = "devops_agent", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.deployment_history: List[Dict[str, Any]] = []
        self.infrastructure_state: Dict[str, Any] = {}
        self.monitoring_alerts: List[Dict[str, Any]] = []
        self.automation_stats = {
            "total_deployments": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
            "infrastructure_changes": 0,
            "alerts_processed": 0
        }
        
    async def initialize(self) -> bool:
        """Initialize DevOps automation agent"""
        try:
            self.logger.info("Initializing DevOps Automation Agent")
            
            # Initialize infrastructure state
            self.infrastructure_state = {
                "environments": ["development", "staging", "production"],
                "services": {},
                "last_update": datetime.now(timezone.utc).isoformat()
            }
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}", exc_info=True)
            return False
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process DevOps automation requests.
        
        Message format:
        {
            "type": "deploy" | "provision" | "monitor" | "analyze_logs" | "rollback",
            "environment": "development" | "staging" | "production",
            "service": "...",
            "options": {...}
        }
        """
        try:
            msg_type = message.get("type")
            environment = message.get("environment", "development")
            service = message.get("service")
            options = message.get("options", {})
            
            if msg_type == "deploy":
                return await self.deploy_service(environment, service, options)
            elif msg_type == "provision":
                return await self.provision_infrastructure(environment, options)
            elif msg_type == "monitor":
                return await self.monitor_health(environment, service)
            elif msg_type == "analyze_logs":
                return await self.analyze_logs(environment, service, options)
            elif msg_type == "rollback":
                return await self.rollback_deployment(environment, service, options)
            elif msg_type == "get_status":
                return await self.get_infrastructure_status(environment)
            else:
                return {
                    "status": "error",
                    "error": f"Unknown message type: {msg_type}"
                }
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def execute(self) -> Any:
        """Execute periodic monitoring and maintenance tasks"""
        # Perform health checks
        await self._perform_health_checks()
        
        # Clean up old deployment history (keep last 100)
        if len(self.deployment_history) > 100:
            self.deployment_history = self.deployment_history[-100:]
        
        # Clean up old alerts (keep last 50)
        if len(self.monitoring_alerts) > 50:
            self.monitoring_alerts = self.monitoring_alerts[-50:]
        
        await asyncio.sleep(30)  # Run every 30 seconds
    
    async def deploy_service(
        self,
        environment: str,
        service: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy a service to specified environment.
        
        Args:
            environment: Target environment
            service: Service name
            options: Deployment options
            
        Returns:
            Deployment result
        """
        try:
            self.logger.info(f"Deploying {service} to {environment}")
            
            deployment_id = f"deploy-{len(self.deployment_history) + 1}"
            
            # Validate environment
            if environment not in self.infrastructure_state["environments"]:
                return {
                    "status": "error",
                    "error": f"Invalid environment: {environment}"
                }
            
            # Simulate deployment process
            deployment_result = await self._execute_deployment(
                deployment_id,
                environment,
                service,
                options
            )
            
            # Record deployment
            deployment_record = {
                "deployment_id": deployment_id,
                "service": service,
                "environment": environment,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": deployment_result["status"],
                "version": options.get("version", "latest"),
                "duration_seconds": deployment_result.get("duration", 0)
            }
            
            self.deployment_history.append(deployment_record)
            
            # Update stats
            self.automation_stats["total_deployments"] += 1
            if deployment_result["status"] == "success":
                self.automation_stats["successful_deployments"] += 1
            else:
                self.automation_stats["failed_deployments"] += 1
            
            # Update infrastructure state
            if service not in self.infrastructure_state["services"]:
                self.infrastructure_state["services"][service] = {}
            
            self.infrastructure_state["services"][service][environment] = {
                "version": options.get("version", "latest"),
                "last_deployed": deployment_record["timestamp"],
                "status": "running" if deployment_result["status"] == "success" else "failed"
            }
            
            return {
                "status": "success",
                "deployment_id": deployment_id,
                "deployment": deployment_record,
                "message": f"Successfully deployed {service} to {environment}"
            }
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}", exc_info=True)
            self.automation_stats["failed_deployments"] += 1
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def provision_infrastructure(
        self,
        environment: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Provision infrastructure for environment.
        
        Args:
            environment: Target environment
            options: Provisioning options
            
        Returns:
            Provisioning result
        """
        try:
            self.logger.info(f"Provisioning infrastructure for {environment}")
            
            # Simulate infrastructure provisioning
            resources = options.get("resources", [])
            provisioned = []
            
            for resource in resources:
                result = await self._provision_resource(environment, resource)
                provisioned.append(result)
            
            self.automation_stats["infrastructure_changes"] += len(resources)
            
            return {
                "status": "success",
                "environment": environment,
                "provisioned_resources": provisioned,
                "message": f"Successfully provisioned {len(provisioned)} resources"
            }
            
        except Exception as e:
            self.logger.error(f"Provisioning failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def monitor_health(
        self,
        environment: str,
        service: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Monitor health of services.
        
        Args:
            environment: Target environment
            service: Optional specific service
            
        Returns:
            Health status
        """
        try:
            self.logger.info(f"Monitoring health for {environment}/{service or 'all'}")
            
            health_data = {
                "environment": environment,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "services": {}
            }
            
            if service:
                # Monitor specific service
                service_health = await self._check_service_health(environment, service)
                health_data["services"][service] = service_health
            else:
                # Monitor all services
                for svc in self.infrastructure_state["services"].keys():
                    service_health = await self._check_service_health(environment, svc)
                    health_data["services"][svc] = service_health
            
            # Determine overall health
            health_data["overall_status"] = self._calculate_overall_health(health_data["services"])
            
            return {
                "status": "success",
                "health": health_data
            }
            
        except Exception as e:
            self.logger.error(f"Health monitoring failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def analyze_logs(
        self,
        environment: str,
        service: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze logs for issues and patterns.
        
        Args:
            environment: Target environment
            service: Service name
            options: Analysis options
            
        Returns:
            Log analysis results
        """
        try:
            self.logger.info(f"Analyzing logs for {environment}/{service}")
            
            # Simulate log analysis
            analysis = {
                "service": service,
                "environment": environment,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "errors_found": 3,
                "warnings_found": 12,
                "patterns": [
                    {
                        "type": "error",
                        "pattern": "Connection timeout",
                        "occurrences": 3,
                        "severity": "high"
                    },
                    {
                        "type": "warning",
                        "pattern": "Slow query detected",
                        "occurrences": 12,
                        "severity": "medium"
                    }
                ],
                "recommendations": [
                    "Increase connection timeout values",
                    "Optimize database queries",
                    "Consider adding connection pooling"
                ]
            }
            
            return {
                "status": "success",
                "analysis": analysis
            }
            
        except Exception as e:
            self.logger.error(f"Log analysis failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def rollback_deployment(
        self,
        environment: str,
        service: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Rollback a deployment to previous version.
        
        Args:
            environment: Target environment
            service: Service name
            options: Rollback options
            
        Returns:
            Rollback result
        """
        try:
            self.logger.info(f"Rolling back {service} in {environment}")
            
            # Find previous deployment
            previous_deployments = [
                d for d in self.deployment_history
                if d["service"] == service and d["environment"] == environment
                and d["status"] == "success"
            ]
            
            if len(previous_deployments) < 2:
                return {
                    "status": "error",
                    "error": "No previous successful deployment found"
                }
            
            previous = previous_deployments[-2]
            
            # Perform rollback (essentially a deployment to previous version)
            rollback_result = await self.deploy_service(
                environment,
                service,
                {"version": previous["version"], "rollback": True}
            )
            
            return {
                "status": "success",
                "rollback": rollback_result,
                "message": f"Rolled back {service} to version {previous['version']}"
            }
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_infrastructure_status(self, environment: str) -> Dict[str, Any]:
        """Get current infrastructure status"""
        return {
            "status": "success",
            "infrastructure": {
                "environment": environment,
                "services": self.infrastructure_state["services"],
                "last_update": self.infrastructure_state["last_update"]
            }
        }
    
    # Helper methods
    
    async def _execute_deployment(
        self,
        deployment_id: str,
        environment: str,
        service: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the actual deployment"""
        # Simulate deployment time
        await asyncio.sleep(0.2)
        
        # For rollbacks or testing, always succeed
        # In production, this would have real success/failure logic
        is_rollback = options.get("rollback", False)
        
        # Simulate success/failure (95% success rate, 100% for rollbacks)
        import random
        success = is_rollback or random.random() > 0.05
        
        return {
            "status": "success" if success else "failed",
            "duration": 0.2,
            "deployment_id": deployment_id
        }
    
    async def _provision_resource(
        self,
        environment: str,
        resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Provision a single resource"""
        await asyncio.sleep(0.1)
        
        return {
            "resource_type": resource.get("type", "unknown"),
            "resource_id": f"{environment}-{resource.get('name', 'resource')}",
            "status": "provisioned"
        }
    
    async def _check_service_health(
        self,
        environment: str,
        service: str
    ) -> Dict[str, Any]:
        """Check health of a specific service"""
        await asyncio.sleep(0.05)
        
        service_data = self.infrastructure_state["services"].get(service, {})
        env_data = service_data.get(environment, {})
        
        return {
            "status": env_data.get("status", "unknown"),
            "version": env_data.get("version", "unknown"),
            "last_deployed": env_data.get("last_deployed", "never"),
            "health_check": "passing"
        }
    
    def _calculate_overall_health(self, services: Dict[str, Any]) -> str:
        """Calculate overall health status"""
        if not services:
            return "unknown"
        
        statuses = [s.get("health_check", "unknown") for s in services.values()]
        
        if all(s == "passing" for s in statuses):
            return "healthy"
        elif any(s == "failing" for s in statuses):
            return "degraded"
        else:
            return "warning"
    
    async def _perform_health_checks(self) -> None:
        """Perform periodic health checks"""
        for environment in self.infrastructure_state["environments"]:
            for service in self.infrastructure_state["services"].keys():
                health = await self._check_service_health(environment, service)
                
                if health["health_check"] != "passing":
                    # Create alert
                    alert = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "environment": environment,
                        "service": service,
                        "severity": "high",
                        "message": f"Health check failed for {service} in {environment}"
                    }
                    self.monitoring_alerts.append(alert)
                    self.automation_stats["alerts_processed"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get DevOps automation statistics"""
        return {
            "agent_id": self.agent_id,
            "stats": self.automation_stats,
            "deployment_count": len(self.deployment_history),
            "alert_count": len(self.monitoring_alerts)
        }
    
    async def get_checkpoint_state(self) -> Dict[str, Any]:
        """Save custom state for checkpointing"""
        return {
            "automation_stats": self.automation_stats,
            "deployment_history": self.deployment_history[-10:],  # Keep last 10
            "infrastructure_state": self.infrastructure_state
        }
    
    async def restore_checkpoint_state(self, state: Dict[str, Any]) -> None:
        """Restore custom state from checkpoint"""
        self.automation_stats = state.get("automation_stats", self.automation_stats)
        self.deployment_history = state.get("deployment_history", [])
        self.infrastructure_state = state.get("infrastructure_state", self.infrastructure_state)
