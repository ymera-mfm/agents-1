"""
Production-Ready Configuration Manager
Centralized, dynamic configuration management with versioning and hot-reload
Version: 2.0.0
"""

import asyncio
import json
import os
import hashlib
import time
import traceback
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

from base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResponse, TaskStatus
from opentelemetry import trace

# Constants
CONFIG_CACHE_TTL = 300  # 5 minutes
MAX_CONFIG_SIZE = 1024 * 1024  # 1MB
CONFIG_VERSION_LIMIT = 10  # Keep last 10 versions

@dataclass
class ConfigVersion:
    """Configuration version tracking"""
    version: int
    config_data: Dict[str, Any]
    created_at: float
    created_by: str
    checksum: str
    description: str = ""
    
    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum of configuration"""
        config_str = json.dumps(self.config_data, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()

@dataclass
class ConfigMetadata:
    """Configuration metadata"""
    agent_name: str
    current_version: int
    versions: List[ConfigVersion] = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)
    update_count: int = 0
    subscribers: Set[str] = field(default_factory=set)
    validation_schema: Optional[Dict] = None

class ConfigManager(BaseAgent):
    """
    Production-Ready Configuration Manager with:
    - Version control and rollback
    - Configuration validation
    - Hot-reload notifications
    - Configuration caching
    - Audit logging
    - Configuration inheritance
    - Environment-specific configs
    - Encryption support
    - Configuration templates
    - Health checks
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Configuration storage
        self.configurations: Dict[str, Dict[str, Any]] = {}
        self.config_metadata: Dict[str, ConfigMetadata] = {}
        self.config_cache: Dict[str, Dict] = {}
        self.cache_timestamps: Dict[str, float] = {}
        
        # Configuration templates
        self.config_templates: Dict[str, Dict] = {}
        
        # Configuration schemas for validation
        self.config_schemas: Dict[str, Dict] = {}
        
        # Environment-specific configs
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.environment_configs: Dict[str, Dict] = defaultdict(dict)
        
        # Change tracking
        self.change_log: List[Dict] = []
        self.config_watchers: Dict[str, Set[str]] = defaultdict(set)
        
        # Metrics
        self.config_metrics = {
            'total_configs': 0,
            'get_requests': 0,
            'set_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_failures': 0,
            'hot_reloads': 0,
            'rollbacks': 0
        }
        
        # Health status
        self._health_status = {
            'status': 'initializing',
            'last_check': time.time(),
            'issues': []
        }
        
        # Initialize default configurations
        self._initialize_default_configs()
        self._load_config_schemas()
        self._load_config_templates()
    
    def _initialize_default_configs(self):
        """Initialize comprehensive default configurations"""
        try:
            # Intelligence Engine config
            self._register_default_config("intelligence_engine", {
                "decision_strategy": "adaptive",
                "ml_model_path": "/app/models/intelligence_engine_model.pkl",
                "optimization_interval_seconds": 300,
                "learning_rate": 0.001,
                "confidence_threshold": 0.85,
                "fallback_strategy": "conservative",
                "feature_flags": {
                    "enable_ml_predictions": True,
                    "enable_auto_tuning": True,
                    "enable_model_updating": False
                },
                "resource_limits": {
                    "max_memory_mb": 2048,
                    "max_cpu_percent": 70,
                    "max_concurrent_operations": 10
                }
            })
            
            # Optimizing Engine config
            self._register_default_config("optimizing_engine", {
                "optimization_rules_path": "/app/rules/optimization_rules.json",
                "default_optimization_level": "standard",
                "optimization_strategies": ["performance", "cost", "reliability"],
                "reoptimization_interval_seconds": 600,
                "enable_auto_optimization": True,
                "optimization_thresholds": {
                    "min_improvement_percent": 5,
                    "max_degradation_percent": 2
                }
            })
            
            # Performance Engine config
            self._register_default_config("performance_engine_agent", {
                "monitoring_interval_seconds": 10,
                "alert_thresholds": {
                    "cpu_usage": {"warning": 70, "critical": 90},
                    "memory_usage": {"warning": 80, "critical": 95},
                    "response_time_ms": {"warning": 1000, "critical": 5000},
                    "error_rate_percent": {"warning": 1, "critical": 5}
                },
                "collection_window_seconds": 60,
                "retention_hours": 24,
                "enable_predictive_alerts": True
            })
            
            # Validation Agent config
            self._register_default_config("validation_agent", {
                "validation_rules_path": "/app/rules/validation_rules.json",
                "default_schema_path": "/app/schemas/default_schema.json",
                "strict_mode": True,
                "enable_async_validation": True,
                "max_validation_time_ms": 500,
                "validation_levels": ["syntax", "semantic", "business"],
                "custom_validators": []
            })
            
            # Static Analysis Agent config
            self._register_default_config("static_analysis_agent", {
                "analysis_tools": ["pylint", "flake8", "mypy", "bandit"],
                "default_severity_threshold": "medium",
                "enable_security_scanning": True,
                "code_quality_threshold": 8.0,
                "max_analysis_time_seconds": 300,
                "parallel_analysis": True,
                "ignore_patterns": ["*/tests/*", "*/migrations/*"]
            })
            
            # Real-time Monitoring Agent config
            self._register_default_config("real_time_monitoring_agent", {
                "metric_collection_interval_seconds": 5,
                "health_check_interval_seconds": 15,
                "anomaly_detection_enabled": True,
                "anomaly_threshold": 3.0,  # Standard deviations
                "metrics_retention_hours": 48,
                "enable_distributed_tracing": True,
                "alert_channels": ["email", "slack", "pagerduty"]
            })
            
            # Communication Agent config
            self._register_default_config("communication_agent", {
                "max_message_size_mb": 10,
                "max_queue_size": 10000,
                "default_message_ttl_seconds": 3600,
                "enable_message_encryption": False,
                "enable_message_compression": True,
                "rate_limit_per_minute": 1000,
                "circuit_breaker_threshold": 5,
                "circuit_breaker_timeout_seconds": 60
            })
            
            # LLM Agent config
            self._register_default_config("llm_agent", {
                "model_name": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000,
                "timeout_seconds": 30,
                "retry_attempts": 3,
                "enable_caching": True,
                "cache_ttl_seconds": 3600,
                "rate_limit_rpm": 60,
                "fallback_model": "gpt-3.5-turbo"
            })
            
            # Drafting Agent config
            self._register_default_config("drafting_agent", {
                "default_template": "technical_report",
                "auto_save_interval_seconds": 30,
                "max_draft_size_mb": 5,
                "enable_version_control": True,
                "enable_collaboration": True,
                "spell_check_enabled": True,
                "grammar_check_enabled": True
            })
            
            # Editing Agent config
            self._register_default_config("editing_agent", {
                "default_editing_mode": "moderate",
                "max_session_duration_minutes": 120,
                "auto_save_interval_seconds": 30,
                "enable_ai_suggestions": True,
                "suggestion_confidence_threshold": 0.7,
                "max_concurrent_sessions": 50
            })
            
            self.logger.info("Default configurations initialized",
                           config_count=len(self.configurations))
            
        except Exception as e:
            self.logger.error("Failed to initialize default configs", error=str(e))
            raise
    
    def _register_default_config(self, agent_name: str, config_data: Dict[str, Any]):
        """Register a default configuration with metadata"""
        self.configurations[agent_name] = config_data
        
        version = ConfigVersion(
            version=1,
            config_data=config_data,
            created_at=time.time(),
            created_by="system",
            checksum="",
            description="Initial default configuration"
        )
        
        self.config_metadata[agent_name] = ConfigMetadata(
            agent_name=agent_name,
            current_version=1,
            versions=[version]
        )
        
        self.config_metrics['total_configs'] += 1
    
    def _load_config_schemas(self):
        """Load validation schemas for configurations"""
        try:
            # Example schema for validation
            self.config_schemas["performance_engine_agent"] = {
                "type": "object",
                "required": ["monitoring_interval_seconds", "alert_thresholds"],
                "properties": {
                    "monitoring_interval_seconds": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 300
                    },
                    "alert_thresholds": {
                        "type": "object",
                        "required": ["cpu_usage", "memory_usage"]
                    }
                }
            }
            
            self.logger.info("Configuration schemas loaded",
                           schema_count=len(self.config_schemas))
            
        except Exception as e:
            self.logger.error("Failed to load config schemas", error=str(e))
    
    def _load_config_templates(self):
        """Load configuration templates"""
        try:
            # Example template
            self.config_templates["monitoring_agent"] = {
                "monitoring_interval_seconds": 10,
                "alert_thresholds": {
                    "cpu_usage": {"warning": 70, "critical": 90},
                    "memory_usage": {"warning": 80, "critical": 95}
                },
                "enable_predictive_alerts": True
            }
            
            self.logger.info("Configuration templates loaded",
                           template_count=len(self.config_templates))
            
        except Exception as e:
            self.logger.error("Failed to load config templates", error=str(e))
    
    async def start(self):
        """Start configuration manager services"""
        try:
            # Load configurations from database
            await self._load_all_configurations()
            
            # Subscribe to configuration requests
            await self._subscribe(
                "config.get",
                self._handle_get_config_request
            )
            
            await self._subscribe(
                "config.set",
                self._handle_set_config_request
            )
            
            await self._subscribe(
                "config.reload",
                self._handle_reload_config_request
            )
            
            await self._subscribe(
                "config.rollback",
                self._handle_rollback_request
            )
            
            await self._subscribe(
                "config.watch",
                self._handle_watch_request
            )
            
            await self._subscribe(
                "config.validate",
                self._handle_validate_request
            )
            
            await self._subscribe(
                "config.list",
                self._handle_list_configs_request
            )
            
            await self._subscribe(
                "config.health",
                self._handle_health_check
            )
            
            # Background tasks
            asyncio.create_task(self._cache_cleanup_loop())
            asyncio.create_task(self._health_check_loop())
            asyncio.create_task(self._config_sync_loop())
            
            self._health_status['status'] = 'healthy'
            self._health_status['last_check'] = time.time()
            
            self.logger.info("Config Manager started successfully",
                           total_configs=len(self.configurations),
                           environment=self.environment)
            
        except Exception as e:
            self._health_status['status'] = 'unhealthy'
            self._health_status['issues'].append(f"Startup failed: {str(e)}")
            self.logger.error("Failed to start Config Manager", error=str(e))
            raise
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute configuration management tasks"""
        task_type = request.task_type
        payload = request.payload
        
        try:
            result: Dict[str, Any] = {}
            
            if task_type == "get_config":
                result = await self._get_config_task(payload)
            
            elif task_type == "set_config":
                result = await self._set_config_task(payload)
            
            elif task_type == "reload_all_configs":
                result = await self._reload_all_configs_task()
            
            elif task_type == "rollback_config":
                result = await self._rollback_config_task(payload)
            
            elif task_type == "validate_config":
                result = await self._validate_config_task(payload)
            
            elif task_type == "get_config_history":
                result = await self._get_config_history_task(payload)
            
            elif task_type == "export_configs":
                result = await self._export_configs_task(payload)
            
            elif task_type == "import_configs":
                result = await self._import_configs_task(payload)
            
            else:
                raise ValueError(f"Unknown config manager task type: {task_type}")
            
            return TaskResponse(
                task_id=request.task_id,
                status=TaskStatus.COMPLETED,
                result=result
            ).dict()
        
        except Exception as e:
            self.logger.error(f"Error executing config task {task_type}",
                            error=str(e),
                            traceback=traceback.format_exc())
            return TaskResponse(
                task_id=request.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            ).dict()
    
    async def _get_config_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get configuration for an agent"""
        agent_name = payload.get("agent_name")
        if not agent_name:
            raise ValueError("agent_name is required")
        
        use_cache = payload.get("use_cache", True)
        include_metadata = payload.get("include_metadata", False)
        
        self.config_metrics['get_requests'] += 1
        
        # Check cache
        if use_cache and agent_name in self.config_cache:
            cache_age = time.time() - self.cache_timestamps.get(agent_name, 0)
            if cache_age < CONFIG_CACHE_TTL:
                self.config_metrics['cache_hits'] += 1
                config = self.config_cache[agent_name]
                
                result = {"config": config}
                if include_metadata and agent_name in self.config_metadata:
                    result["metadata"] = {
                        "version": self.config_metadata[agent_name].current_version,
                        "last_updated": self.config_metadata[agent_name].last_updated,
                        "checksum": self.config_metadata[agent_name].versions[-1].checksum
                    }
                
                return result
        
        self.config_metrics['cache_misses'] += 1
        
        # Get configuration
        default_config = self.configurations.get(agent_name, {})
        persisted_config = await self._get_persisted_config(agent_name)
        
        # Merge configurations: default < environment < persisted
        env_config = self.environment_configs.get(self.environment, {}).get(agent_name, {})
        merged_config = {**default_config, **env_config, **persisted_config}
        
        # Update cache
        self.config_cache[agent_name] = merged_config
        self.cache_timestamps[agent_name] = time.time()
        
        result = {"config": merged_config}
        if include_metadata and agent_name in self.config_metadata:
            result["metadata"] = {
                "version": self.config_metadata[agent_name].current_version,
                "last_updated": self.config_metadata[agent_name].last_updated,
                "environment": self.environment
            }
        
        return result
    
    async def _set_config_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Set configuration for an agent"""
        agent_name = payload.get("agent_name")
        config_data = payload.get("config_data")
        
        if not agent_name or config_data is None:
            raise ValueError("agent_name and config_data are required")
        
        validate = payload.get("validate", True)
        notify = payload.get("notify", True)
        description = payload.get("description", "Configuration update")
        updated_by = payload.get("updated_by", "system")
        
        self.config_metrics['set_requests'] += 1
        
        # Validate configuration
        if validate:
            validation_result = await self._validate_configuration(agent_name, config_data)
            if not validation_result["valid"]:
                self.config_metrics['validation_failures'] += 1
                raise ValueError(f"Configuration validation failed: {validation_result['errors']}")
        
        # Check size
        config_size = len(json.dumps(config_data))
        if config_size > MAX_CONFIG_SIZE:
            raise ValueError(f"Configuration size {config_size} exceeds maximum {MAX_CONFIG_SIZE}")
        
        # Create new version
        await self._create_config_version(agent_name, config_data, updated_by, description)
        
        # Persist to database
        await self._set_configuration(agent_name, config_data, updated_by)
        
        # Invalidate cache
        if agent_name in self.config_cache:
            del self.config_cache[agent_name]
        
        # Notify watchers
        if notify:
            await self._notify_config_change(agent_name, config_data)
            self.config_metrics['hot_reloads'] += 1
        
        return {
            "status": "success",
            "agent_name": agent_name,
            "version": self.config_metadata[agent_name].current_version,
            "checksum": self.config_metadata[agent_name].versions[-1].checksum
        }
    
    async def _reload_all_configs_task(self) -> Dict[str, Any]:
        """Reload all configurations from database"""
        await self._load_all_configurations()
        
        # Clear cache
        self.config_cache.clear()
        self.cache_timestamps.clear()
        
        return {
            "status": "success",
            "message": "All configurations reloaded",
            "config_count": len(self.configurations)
        }
    
    async def _rollback_config_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback configuration to previous version"""
        agent_name = payload.get("agent_name")
        target_version = payload.get("version")
        
        if not agent_name:
            raise ValueError("agent_name is required")
        
        if agent_name not in self.config_metadata:
            raise ValueError(f"No configuration found for {agent_name}")
        
        metadata = self.config_metadata[agent_name]
        
        # Find target version
        if target_version is None:
            # Rollback to previous version
            if len(metadata.versions) < 2:
                raise ValueError("No previous version available")
            target_version = metadata.current_version - 1
        
        target_config_version = next(
            (v for v in metadata.versions if v.version == target_version),
            None
        )
        
        if not target_config_version:
            raise ValueError(f"Version {target_version} not found")
        
        # Restore configuration
        await self._set_configuration(agent_name, target_config_version.config_data, "system_rollback")
        metadata.current_version = target_version
        
        # Invalidate cache
        if agent_name in self.config_cache:
            del self.config_cache[agent_name]
        
        # Notify
        await self._notify_config_change(agent_name, target_config_version.config_data)
        
        self.config_metrics['rollbacks'] += 1
        
        self.logger.info("Configuration rolled back",
                       agent_name=agent_name,
                       from_version=metadata.current_version,
                       to_version=target_version)
        
        return {
            "status": "success",
            "agent_name": agent_name,
            "rolled_back_to_version": target_version
        }
    
    async def _validate_config_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a configuration"""
        agent_name = payload.get("agent_name")
        config_data = payload.get("config_data")
        
        if not agent_name or config_data is None:
            raise ValueError("agent_name and config_data are required")
        
        validation_result = await self._validate_configuration(agent_name, config_data)
        
        return {
            "agent_name": agent_name,
            **validation_result
        }
    
    async def _get_config_history_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get configuration version history"""
        agent_name = payload.get("agent_name")
        limit = payload.get("limit", 10)
        
        if not agent_name:
            raise ValueError("agent_name is required")
        
        if agent_name not in self.config_metadata:
            return {"agent_name": agent_name, "versions": []}
        
        metadata = self.config_metadata[agent_name]
        versions = metadata.versions[-limit:]
        
        version_info = [
            {
                "version": v.version,
                "created_at": v.created_at,
                "created_by": v.created_by,
                "checksum": v.checksum,
                "description": v.description,
                "is_current": v.version == metadata.current_version
            }
            for v in versions
        ]
        
        return {
            "agent_name": agent_name,
            "current_version": metadata.current_version,
            "versions": version_info
        }
    
    async def _export_configs_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Export configurations"""
        agent_names = payload.get("agent_names", list(self.configurations.keys()))
        include_metadata = payload.get("include_metadata", True)
        
        export_data = {}
        
        for agent_name in agent_names:
            if agent_name in self.configurations:
                config = await self._get_config_task({"agent_name": agent_name, "include_metadata": include_metadata})
                export_data[agent_name] = config
        
        return {
            "status": "success",
            "exported_count": len(export_data),
            "configurations": export_data,
            "environment": self.environment,
            "exported_at": time.time()
        }
    
    async def _import_configs_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Import configurations"""
        configurations = payload.get("configurations")
        overwrite = payload.get("overwrite", False)
        validate = payload.get("validate", True)
        
        if not configurations:
            raise ValueError("configurations are required")
        
        imported_count = 0
        failed_count = 0
        errors = []
        
        for agent_name, config_data in configurations.items():
            try:
                # Check if exists and overwrite flag
                if agent_name in self.configurations and not overwrite:
                    errors.append(f"{agent_name}: Already exists (use overwrite=True)")
                    failed_count += 1
                    continue
                
                # Set configuration
                await self._set_config_task({
                    "agent_name": agent_name,
                    "config_data": config_data.get("config", config_data),
                    "validate": validate,
                    "description": "Imported configuration"
                })
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"{agent_name}: {str(e)}")
                failed_count += 1
        
        return {
            "status": "completed",
            "imported_count": imported_count,
            "failed_count": failed_count,
            "errors": errors if errors else None
        }
    
    async def _create_config_version(self, agent_name: str, config_data: Dict[str, Any],
                                    created_by: str, description: str):
        """Create a new configuration version"""
        if agent_name not in self.config_metadata:
            self.config_metadata[agent_name] = ConfigMetadata(
                agent_name=agent_name,
                current_version=0
            )
        
        metadata = self.config_metadata[agent_name]
        new_version = metadata.current_version + 1
        
        version = ConfigVersion(
            version=new_version,
            config_data=config_data,
            created_at=time.time(),
            created_by=created_by,
            checksum="",
            description=description
        )
        
        metadata.versions.append(version)
        metadata.current_version = new_version
        metadata.last_updated = time.time()
        metadata.update_count += 1
        
        # Keep only last N versions
        if len(metadata.versions) > CONFIG_VERSION_LIMIT:
            metadata.versions = metadata.versions[-CONFIG_VERSION_LIMIT:]
        
        # Log change
        self.change_log.append({
            "agent_name": agent_name,
            "version": new_version,
            "created_by": created_by,
            "timestamp": time.time(),
            "description": description,
            "checksum": version.checksum
        })
    
    async def _validate_configuration(self, agent_name: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration against schema"""
        errors = []
        warnings = []
        
        # Check if schema exists
        if agent_name in self.config_schemas:
            schema = self.config_schemas[agent_name]
            
            # Basic validation (in production, use jsonschema library)
            if "required" in schema:
                for required_field in schema["required"]:
                    if required_field not in config_data:
                        errors.append(f"Missing required field: {required_field}")
            
            if "properties" in schema:
                for prop_name, prop_schema in schema["properties"].items():
                    if prop_name in config_data:
                        value = config_data[prop_name]
                        prop_type = prop_schema.get("type")
                        
                        # Type checking
                        if prop_type == "integer" and not isinstance(value, int):
                            errors.append(f"Field '{prop_name}' must be an integer")
                        elif prop_type == "string" and not isinstance(value, str):
                            errors.append(f"Field '{prop_name}' must be a string")
                        elif prop_type == "object" and not isinstance(value, dict):
                            errors.append(f"Field '{prop_name}' must be an object")
                        
                        # Range checking for integers
                        if prop_type == "integer" and isinstance(value, int):
                            if "minimum" in prop_schema and value < prop_schema["minimum"]:
                                errors.append(f"Field '{prop_name}' must be >= {prop_schema['minimum']}")
                            if "maximum" in prop_schema and value > prop_schema["maximum"]:
                                errors.append(f"Field '{prop_name}' must be <= {prop_schema['maximum']}")
        else:
            warnings.append(f"No schema defined for {agent_name}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors if errors else None,
            "warnings": warnings if warnings else None
        }
    
    async def _notify_config_change(self, agent_name: str, config_data: Dict[str, Any]):
        """Notify subscribers of configuration change"""
        try:
            # Publish to NATS
            notification = {
                "agent_name": agent_name,
                "config": config_data,
                "timestamp": time.time(),
                "version": self.config_metadata[agent_name].current_version,
                "checksum": self.config_metadata[agent_name].versions[-1].checksum
            }
            
            # Publish to specific agent
            await self._publish(
                f"config.{agent_name}.updated",
                json.dumps(notification).encode()
            )
            
            # Publish to general config update channel
            await self._publish(
                "config.updated",
                json.dumps(notification).encode()
            )
            
            # Notify watchers
            if agent_name in self.config_watchers:
                for watcher in self.config_watchers[agent_name]:
                    await self._publish(
                        f"config.watcher.{watcher}",
                        json.dumps(notification).encode()
                    )
            
            self.logger.info("Configuration change notified",
                           agent_name=agent_name,
                           watchers=len(self.config_watchers.get(agent_name, [])))
            
        except Exception as e:
            self.logger.error("Failed to notify config change", error=str(e))
    
    async def _get_persisted_config(self, agent_name: str) -> Dict[str, Any]:
        """Retrieve configuration from database"""
        if not self.db_pool:
            return {}
        
        try:
            row = await self._db_query(
                "SELECT config_data FROM agent_configurations WHERE agent_name = $1",
                agent_name,
                fetch_one=True
            )
            
            if row and row["config_data"]:
                return json.loads(row["config_data"]) if isinstance(row["config_data"], str) else row["config_data"]
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve config for {agent_name}", error=str(e))
            return {}
    
    async def _load_all_configurations(self):
        """Load all configurations from database"""
        if not self.db_pool:
            self.logger.warning("Database not available, using default configs only")
            return
        
        try:
            rows = await self._db_query(
                "SELECT agent_name, config_data, updated_at, updated_by FROM agent_configurations"
            )
            
            loaded_count = 0
            for row in rows:
                agent_name = row["agent_name"]
                config_data = json.loads(row["config_data"]) if isinstance(row["config_data"], str) else row["config_data"]
                
                # Merge with default
                default_config = self.configurations.get(agent_name, {})
                merged_config = {**default_config, **config_data}
                self.configurations[agent_name] = merged_config
                
                # Update metadata
                if agent_name not in self.config_metadata:
                    self.config_metadata[agent_name] = ConfigMetadata(
                        agent_name=agent_name,
                        current_version=1
                    )
                
                loaded_count += 1
            
            self.logger.info(f"Loaded {loaded_count} configurations from database")
            
        except Exception as e:
            self.logger.error("Failed to load configurations", error=str(e))
    
    async def _set_configuration(self, agent_name: str, config_data: Dict[str, Any], updated_by: str = "system"):
        """Persist configuration to database"""
        if not self.db_pool:
            self.logger.warning("Database not available, config not persisted")
            return
        
        try:
            await self._db_query(
                """
                INSERT INTO agent_configurations (agent_name, config_data, updated_by)
                VALUES ($1, $2, $3)
                ON CONFLICT (agent_name) DO UPDATE SET
                    config_data = EXCLUDED.config_data,
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = EXCLUDED.updated_by
                """,
                agent_name,
                json.dumps(config_data),
                updated_by
            )
            
            # Update in-memory
            default_config = self.configurations.get(agent_name, {})
            self.configurations[agent_name] = {**default_config, **config_data}
            
            self.logger.info(f"Configuration for {agent_name} persisted")
            
        except Exception as e:
            self.logger.error(f"Failed to persist config for {agent_name}", error=str(e))
            raise
    
    # Event handlers
    
    async def _handle_get_config_request(self, msg):
        """Handle get configuration request"""
        try:
            data = json.loads(msg.data.decode())
            result = await self._get_config_task(data)
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps(result).encode())
        
        except Exception as e:
            self.logger.error("Get config request failed", error=str(e))
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e)}).encode())
    
    async def _handle_validate_request(self, msg):
        """Handle configuration validation request"""
        try:
            data = json.loads(msg.data.decode())
            result = await self._validate_config_task(data)
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps(result).encode())
        
        except Exception as e:
            self.logger.error("Validate request failed", error=str(e))
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e)}).encode())
    
    async def _handle_list_configs_request(self, msg):
        """Handle list configurations request"""
        try:
            data = json.loads(msg.data.decode())
            include_data = data.get("include_data", False)
            agent_type = data.get("agent_type")
            
            configs_list = []
            
            for agent_name, config in self.configurations.items():
                # Filter by type if specified
                if agent_type:
                    agent_info = self.agent_directory.get(agent_name, {})
                    if agent_info.get("agent_type") != agent_type:
                        continue
                
                config_info = {
                    "agent_name": agent_name,
                    "has_config": bool(config),
                    "size_bytes": len(json.dumps(config))
                }
                
                if agent_name in self.config_metadata:
                    metadata = self.config_metadata[agent_name]
                    config_info.update({
                        "version": metadata.current_version,
                        "last_updated": metadata.last_updated,
                        "update_count": metadata.update_count,
                        "subscriber_count": len(metadata.subscribers)
                    })
                
                if include_data:
                    config_info["config"] = config
                
                configs_list.append(config_info)
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps({
                    "status": "success",
                    "count": len(configs_list),
                    "configurations": configs_list
                }).encode())
        
        except Exception as e:
            self.logger.error("List configs request failed", error=str(e))
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e)}).encode())
    
    async def _handle_health_check(self, msg):
        """Handle health check request"""
        try:
            health_data = {
                **self._health_status,
                'metrics': self.config_metrics,
                'total_configs': len(self.configurations),
                'cached_configs': len(self.config_cache),
                'watchers_count': sum(len(w) for w in self.config_watchers.values()),
                'environment': self.environment
            }
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps(health_data).encode())
        
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
    
    # Background tasks
    
    async def _cache_cleanup_loop(self):
        """Periodic cache cleanup"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                expired_entries = []
                
                for agent_name, timestamp in self.cache_timestamps.items():
                    if current_time - timestamp > CONFIG_CACHE_TTL:
                        expired_entries.append(agent_name)
                
                for agent_name in expired_entries:
                    if agent_name in self.config_cache:
                        del self.config_cache[agent_name]
                    if agent_name in self.cache_timestamps:
                        del self.cache_timestamps[agent_name]
                
                if expired_entries:
                    self.logger.debug("Cache cleanup completed",
                                    expired_count=len(expired_entries))
                
                await asyncio.sleep(CONFIG_CACHE_TTL)
                
            except Exception as e:
                self.logger.error("Cache cleanup failed", error=str(e))
                await asyncio.sleep(300)
    
    async def _health_check_loop(self):
        """Periodic health checks"""
        while not self._shutdown_event.is_set():
            try:
                issues = []
                
                # Check database connectivity
                if self.db_pool:
                    try:
                        await self._db_query("SELECT 1")
                    except Exception as e:
                        issues.append(f"Database connectivity issue: {str(e)}")
                
                # Check cache health
                cache_size = sum(len(json.dumps(c)) for c in self.config_cache.values())
                if cache_size > 10 * 1024 * 1024:  # 10MB
                    issues.append(f"Cache size excessive: {cache_size / 1024 / 1024:.2f}MB")
                
                # Check configuration count
                if len(self.configurations) == 0:
                    issues.append("No configurations loaded")
                
                # Update health status
                self._health_status['last_check'] = time.time()
                self._health_status['issues'] = issues
                self._health_status['status'] = 'healthy' if not issues else 'degraded'
                
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error("Health check failed", error=str(e))
                self._health_status['status'] = 'unhealthy'
                self._health_status['issues'].append(f"Health check error: {str(e)}")
                await asyncio.sleep(120)
    
    async def _config_sync_loop(self):
        """Periodic configuration synchronization"""
        while not self._shutdown_event.is_set():
            try:
                # Reload from database periodically to catch external changes
                await self._load_all_configurations()
                
                self.logger.debug("Configuration sync completed")
                
                await asyncio.sleep(600)  # Every 10 minutes
                
            except Exception as e:
                self.logger.error("Config sync failed", error=str(e))
                await asyncio.sleep(1800)
    
    def _get_agent_metrics(self) -> Dict[str, Any]:
        """Enhanced metrics reporting"""
        base_metrics = super()._get_agent_metrics()
        
        # Calculate cache hit rate
        total_requests = self.config_metrics['cache_hits'] + self.config_metrics['cache_misses']
        cache_hit_rate = (self.config_metrics['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        base_metrics.update({
            **self.config_metrics,
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'cached_configs_count': len(self.config_cache),
            'total_watchers': sum(len(w) for w in self.config_watchers.values()),
            'environment': self.environment,
            'health_status': self._health_status['status']
        })
        
        return base_metrics


if __name__ == "__main__":
    config = AgentConfig(
        name="config_manager",
        agent_type="utility",
        capabilities=[
            "configuration_management",
            "version_control",
            "hot_reload",
            "validation",
            "rollback",
            "export_import"
        ],
        nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://agent:secure_password@postgres:5432/ymera"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
        consul_url=os.getenv("CONSUL_URL", "http://consul:8500"),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )
    
    agent = ConfigManager(config)
    asyncio.run(agent.run())
    
    async def _handle_reload_config_request(self, msg):
        """Handle reload configuration request"""
        try:
            result = await self._reload_all_configs_task()
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps(result).encode())
        
        except Exception as e:
            self.logger.error("Reload config request failed", error=str(e))
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e)}).encode())
    
    async def _handle_rollback_request(self, msg):
        """Handle configuration rollback request"""
        try:
            data = json.loads(msg.data.decode())
            result = await self._rollback_config_task(data)
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps(result).encode())
        
        except Exception as e:
            self.logger.error("Rollback request failed", error=str(e))
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e)}).encode())
    
    async def _handle_watch_request(self, msg):
        """Handle configuration watch request"""
        try:
            data = json.loads(msg.data.decode())
            agent_name = data.get("agent_name")
            watcher_id = data.get("watcher_id")
            
            if not agent_name or not watcher_id:
                raise ValueError("agent_name and watcher_id are required")
            
            self.config_watchers[agent_name].add(watcher_id)
            
            if agent_name in self.config_metadata:
                self.config_metadata[agent_name].subscribers.add(watcher_id)
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps({
                    "status": "watching",
                    "agent_name": agent_name,
                    "watcher_id": watcher_id
                }).encode())
        
        except Exception as e:
            self.logger.error("Watch request failed", error=str(e))
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e)}).encode())