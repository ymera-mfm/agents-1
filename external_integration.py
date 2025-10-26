# monitoring/external_integration.py
"""
Integration with enterprise monitoring and observability platforms
including Datadog, New Relic, Grafana, and Splunk
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import os

import datadog
from newrelic.agent import record_custom_metric, record_custom_event
import splunklib.client as splunkclient
import aiohttp

from monitoring.telemetry_manager import TelemetryManager

logger = logging.getLogger(__name__)

class ExternalMonitoringIntegration:
    """Integration with enterprise monitoring platforms"""
    
    def __init__(self, telemetry_manager: TelemetryManager):
        self.telemetry = telemetry_manager
        self.config = self._load_config()
        self.initialized_platforms = set()
        
        # Initialize monitoring platforms
        self._initialize_platforms()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        config = {
            "datadog": {
                "enabled": os.getenv("DATADOG_ENABLED", "false").lower() == "true",
                "api_key": os.getenv("DATADOG_API_KEY", ""),
                "app_key": os.getenv("DATADOG_APP_KEY", ""),
                "environment": os.getenv("ENVIRONMENT", "production")
            },
            "new_relic": {
                "enabled": os.getenv("NEW_RELIC_ENABLED", "false").lower() == "true",
                "license_key": os.getenv("NEW_RELIC_LICENSE_KEY", ""),
                "app_name": os.getenv("NEW_RELIC_APP_NAME", "YMERA Agent Manager")
            },
            "splunk": {
                "enabled": os.getenv("SPLUNK_ENABLED", "false").lower() == "true",
                "host": os.getenv("SPLUNK_HOST", "localhost"),
                "port": int(os.getenv("SPLUNK_PORT", "8089")),
                "username": os.getenv("SPLUNK_USERNAME", ""),
                "password": os.getenv("SPLUNK_PASSWORD", ""),
                "index": os.getenv("SPLUNK_INDEX", "main")
            },
            "grafana": {
                "enabled": os.getenv("GRAFANA_ENABLED", "false").lower() == "true",
                "api_url": os.getenv("GRAFANA_API_URL", ""),
                "api_key": os.getenv("GRAFANA_API_KEY", "")
            }
        }
        
        return config
    
    def _initialize_platforms(self) -> None:
        """Initialize connections to monitoring platforms"""
        # Initialize Datadog
        if self.config["datadog"]["enabled"] and self.config["datadog"]["api_key"]:
            try:
                datadog.initialize(
                    api_key=self.config["datadog"]["api_key"],
                    app_key=self.config["datadog"]["app_key"]
                )
                self.initialized_platforms.add("datadog")
                logger.info("Datadog integration initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Datadog: {e}")
        
        # Initialize New Relic
        if self.config["new_relic"]["enabled"] and self.config["new_relic"]["license_key"]:
            try:
                # New Relic is typically initialized via the newrelic.ini file
                # or environment variables, so we just log success here
                self.initialized_platforms.add("new_relic")
                logger.info("New Relic integration initialized")
            except Exception as e:
                logger.error(f"Failed to initialize New Relic: {e}")
        
        # Initialize Splunk
        if self.config["splunk"]["enabled"]:
            try:
                # We'll create the client on-demand rather than keeping persistent connection
                self.initialized_platforms.add("splunk")
                logger.info("Splunk integration initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Splunk: {e}")
    
    async def export_health_data(self, health_data: Dict[str, Any]) -> None:
        """Export health check data to monitoring platforms"""
        tasks = []
        
        # Metrics from health data
        metrics = {
            "system.cpu_usage": health_data["system"].get("cpu_usage", 0),
            "system.memory_usage": health_data["system"].get("memory_usage", 0),
            "system.disk_usage": health_data["system"].get("disk_usage", 0),
            "agents.active": health_data.get("agents", {}).get("active", 0),
            "tasks.pending": health_data.get("tasks", {}).get("pending", 0)
        }
        
        # Status for components
        for component, status in health_data.get("components", {}).items():
            metrics[f"component.{component}.healthy"] = 1 if status == "healthy" else 0
        
        # Export to each platform
        if "datadog" in self.initialized_platforms:
            tasks.append(self._export_to_datadog(metrics, health_data))
        
        if "new_relic" in self.initialized_platforms:
            tasks.append(self._export_to_new_relic(metrics, health_data))
        
        if "splunk" in self.initialized_platforms:
            tasks.append(self._export_to_splunk("health_check", health_data))
        
        if "grafana" in self.initialized_platforms:
            tasks.append(self._export_to_grafana_loki("health_check", health_data))
        
        # Execute all export tasks
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def export_security_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Export security event to monitoring platforms"""
        tasks = []
        
        event_data["event_type"] = event_type
        event_data["timestamp"] = event_data.get("timestamp", datetime.utcnow().isoformat())
        
        # Export to each platform
        if "datadog" in self.initialized_platforms:
            tasks.append(self._export_security_event_to_datadog(event_type, event_data))
        
        if "new_relic" in self.initialized_platforms:
            tasks.append(self._export_security_event_to_new_relic(event_type, event_data))
        
        if "splunk" in self.initialized_platforms:
            tasks.append(self._export_to_splunk("security_event", event_data))
        
        if "grafana" in self.initialized_platforms:
            tasks.append(self._export_to_grafana_loki("security_event", event_data))
        
        # Execute all export tasks
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _export_to_datadog(self, metrics: Dict[str, float], attributes: Dict[str, Any]) -> None:
        """Export metrics to Datadog"""
        try:
            # Prepare tags
            tags = [
                f"environment:{self.config['datadog']['environment']}",
                f"service:ymera-agent-manager"
            ]
            
            # Add custom tags
            for key, value in attributes.get("tags", {}).items():
                tags.append(f"{key}:{value}")
            
            # Send metrics
            timestamp = int(time.time())
            metric_list = []
            
            for metric_name, value in metrics.items():
                metric_list.append({
                    'metric': f'ymera.{metric_name}',
                    'points': [(timestamp, float(value))],
                    'tags': tags
                })
            
            if metric_list:
                datadog.api.Metric.send(metric_list)
                logger.debug(f"Sent {len(metric_list)} metrics to Datadog")
                
            # Send health status as event if unhealthy
            overall_status = attributes.get("status", "healthy")
            if overall_status != "healthy":
                datadog.api.Event.create(
                    title=f"YMERA Agent Manager Health Status: {overall_status.upper()}",
                    text=json.dumps(attributes, indent=2),
                    alert_type="error" if overall_status == "critical" else "warning",
                    tags=tags,
                    aggregation_key="ymera_health_check"
                )
        
        except Exception as e:
            logger.error(f"Failed to export to Datadog: {e}")
    
    async def _export_to_new_relic(self, metrics: Dict[str, float], attributes: Dict[str, Any]) -> None:
        """Export metrics to New Relic"""
        try:
            # Send metrics
            for metric_name, value in metrics.items():
                record_custom_metric(f'custom/ymera/{metric_name}', float(value))
            
            # Send event
            record_custom_event(
                'YmeraHealthCheck', 
                {
                    'status': attributes.get("status", "healthy"),
                    'environment': os.getenv("ENVIRONMENT", "production"),
                    **{k: json.dumps(v) if isinstance(v, dict) else v 
                       for k, v in attributes.items() if k != "components"}
                }
            )
            
            logger.debug(f"Sent metrics and event to New Relic")
            
        except Exception as e:
            logger.error(f"Failed to export to New Relic: {e}")
    
    async def _export_to_splunk(self, event_type: str, data: Dict[str, Any]) -> None:
        """Export event to Splunk"""
        try:
            # Add metadata
            event_data = {
                **data,
                "event_type": event_type,
                "environment": os.getenv("ENVIRONMENT", "production"),
                "service": "ymera-agent-manager",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Connect to Splunk
            service = splunkclient.connect(
                host=self.config["splunk"]["host"],
                port=self.config["splunk"]["port"],
                username=self.config["splunk"]["username"],
                password=self.config["splunk"]["password"]
            )
            
            # Send event
            index = service.indexes[self.config["splunk"]["index"]]
            index.submit(json.dumps(event_data), sourcetype="ymera:agent_manager")
            
            logger.debug(f"Sent {event_type} event to Splunk")
            
        except Exception as e:
            logger.error(f"Failed to export to Splunk: {e}")
    
    async def _export_to_grafana_loki(self, event_type: str, data: Dict[str, Any]) -> None:
        """Export logs to Grafana Loki"""
        try:
            # Add metadata
            log_data = {
                **data,
                "event_type": event_type,
                "environment": os.getenv("ENVIRONMENT", "production"),
                "service": "ymera-agent-manager",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Format for Loki
            loki_payload = {
                "streams": [
                    {
                        "stream": {
                            "service": "ymera-agent-manager",
                            "event_type": event_type,
                            "environment": os.getenv("ENVIRONMENT", "production"),
                        },
                        "values": [
                            [str(int(time.time() * 1000000000)), json.dumps(log_data)]
                        ]
                    }
                ]
            }
            
            # Send to Loki
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config['grafana']['api_url']}/loki/api/v1/push",
                    json=loki_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.config['grafana']['api_key']}"
                    }
                ) as response:
                    if response.status != 204:
                        logger.warning(f"Loki responded with {response.status}: {await response.text()}")
                    else:
                        logger.debug(f"Sent {event_type} log to Loki")
                    
        except Exception as e:
            logger.error(f"Failed to export to Grafana Loki: {e}")