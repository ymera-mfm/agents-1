# monitoring/alerting.py
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import smtplib
from email.mime.text import MIMEText
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import httpx
import logging

logger = logging.getLogger(__name__)

@dataclass
class Alert:
    id: str
    severity: str  # critical, warning, info
    component: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None

@dataclass
class AlertRule:
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: str
    message_template: str
    cooldown_minutes: int = 5
    last_triggered: Optional[datetime] = None

class IntelligentAlertingSystem:
    """Intelligent alerting system with ML anomaly detection"""
    
    def __init__(self):
        self.active_alerts = {}
        self.alert_rules = self._initialize_alert_rules()
        self.alert_channels = self._initialize_alert_channels()
        self.alert_history = []
        self.anomaly_detector = AnomalyDetector()
    
    def _initialize_alert_rules(self) -> List[AlertRule]:
        """Initialize alert rules"""
        return [
            AlertRule(
                name="high_cpu_usage",
                condition=lambda metrics: metrics.get('cpu_usage', 0) > 90,
                severity="critical",
                message_template="CPU usage exceeded 90%: {cpu_usage}%",
                cooldown_minutes=10
            ),
            AlertRule(
                name="high_memory_usage",
                condition=lambda metrics: metrics.get('memory_usage', 0) > 85,
                severity="critical",
                message_template="Memory usage exceeded 85%: {memory_usage}%",
                cooldown_minutes=10
            ),
            AlertRule(
                name="high_error_rate",
                condition=lambda metrics: metrics.get('error_rate', 0) > 5,
                severity="critical",
                message_template="Error rate exceeded 5%: {error_rate}%",
                cooldown_minutes=5
            ),
            AlertRule(
                name="high_response_time",
                condition=lambda metrics: metrics.get('response_time_avg', 0) > 500,
                severity="warning",
                message_template="High response time: {response_time_avg}ms",
                cooldown_minutes=15
            ),
            AlertRule(
                name="service_down",
                condition=lambda metrics: metrics.get('status') == 'unhealthy',
                severity="critical",
                message_template="Service {component} is down: {error}",
                cooldown_minutes=1
            )
        ]
    
    def _initialize_alert_channels(self) -> Dict[str, Callable]:
        """Initialize alert channels"""
        return {
            'email': self._send_email_alert,
            'slack': self._send_slack_alert,
            'pagerduty': self._send_pagerduty_alert,
            'sms': self._send_sms_alert
        }
    
    async def evaluate_metrics(self, metrics: Dict[str, Any]):
        """Evaluate metrics against alert rules"""
        current_time = datetime.utcnow()
        
        for rule in self.alert_rules:
            # Check cooldown period
            if (rule.last_triggered and 
                (current_time - rule.last_triggered).total_seconds() < rule.cooldown_minutes * 60):
                continue
            
            # Check rule condition
            if rule.condition(metrics):
                # Check for anomalies to reduce false positives
                if await self.anomaly_detector.is_anomaly(metrics, rule.name):
                    alert_id = f"{rule.name}_{int(current_time.timestamp())}"
                    
                    # Create alert message
                    message = rule.message_template.format(**metrics)
                    
                    # Create alert
                    alert = Alert(
                        id=alert_id,
                        severity=rule.severity,
                        component=metrics.get('component', 'unknown'),
                        message=message,
                        timestamp=current_time
                    )
                    
                    # Store alert
                    self.active_alerts[alert_id] = alert
                    self.alert_history.append(alert)
                    
                    # Send alerts through configured channels
                    await self._dispatch_alert(alert)
                    
                    # Update rule last triggered
                    rule.last_triggered = current_time
                    
                    logger.warning(f"Alert triggered: {rule.name} - {message}")
    
    async def _dispatch_alert(self, alert: Alert):
        """Dispatch alert through configured channels"""
        # Determine which channels to use based on severity
        channels = []
        if alert.severity == "critical":
            channels = ['pagerduty', 'slack', 'email', 'sms']
        elif alert.severity == "warning":
            channels = ['slack', 'email']
        else:
            channels = ['slack']
        
        for channel in channels:
            if channel in self.alert_channels:
                try:
                    await self.alert_channels[channel](alert)
                except Exception as e:
                    logger.error(f"Failed to send alert via {channel}: {e}")
    
    async def _send_email_alert(self, alert: Alert):
        """Send alert via email"""
        smtp_host = os.getenv('SMTP_HOST')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        msg = MIMEText(f"""
        Alert: {alert.severity.upper()}
        Component: {alert.component}
        Message: {alert.message}
        Time: {alert.timestamp}
        """)
        
        msg['Subject'] = f"[{alert.severity}] Ymera Alert: {alert.component}"
        msg['From'] = smtp_user
        msg['To'] = os.getenv('ALERT_EMAIL_RECIPIENTS', 'alerts@ymera.example.com')
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
    
    async def _send_slack_alert(self, alert: Alert):
        """Send alert via Slack"""
        slack_token = os.getenv('SLACK_BOT_TOKEN')
        channel_id = os.getenv('SLACK_ALERT_CHANNEL')
        
        if not slack_token or not channel_id:
            return
        
        client = WebClient(token=slack_token)
        
        # Determine color based on severity
        color = "#FF0000" if alert.severity == "critical" else "#FFA500" if alert.severity == "warning" else "#36A64F"
        
        try:
            response = client.chat_postMessage(
                channel=channel_id,
                text=f"Alert: {alert.message}",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{alert.severity.upper()} Alert*: {alert.component}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": alert.message
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Time: {alert.timestamp}"
                            }
                        ]
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Acknowledge"
                                },
                                "value": f"ack_{alert.id}",
                                "action_id": "acknowledge_alert"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Resolve"
                                },
                                "value": f"resolve_{alert.id}",
                                "action_id": "resolve_alert"
                            }
                        ]
                    }
                ]
            )
        except SlackApiError as e:
            logger.error(f"Slack API error: {e}")
    
    async def _send_pagerduty_alert(self, alert: Alert):
        """Send alert via PagerDuty"""
        integration_key = os.getenv('PAGERDUTY_INTEGRATION_KEY')
        
        if not integration_key:
            return
        
        payload = {
            "routing_key": integration_key,
            "event_action": "trigger",
            "dedup_key": alert.id,
            "payload": {
                "summary": f"{alert.severity.upper()}: {alert.component} - {alert.message}",
                "source": "ymera-api",
                "severity": alert.severity,
                "component": alert.component,
                "timestamp": alert.timestamp.isoformat()
            }
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                timeout=10.0
            )
    
    async def _send_sms_alert(self, alert: Alert):
        """Send alert via SMS (Twilio)"""
        # Implementation would use Twilio API
        pass
    
    async def resolve_alert(self, alert_id: str, resolved_by: str):
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            
            # Send resolution notification
            await self._send_resolution_notification(alert, resolved_by)
            
            logger.info(f"Alert {alert_id} resolved by {resolved_by}")
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_by = acknowledged_by
            
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
    
    async def _send_resolution_notification(self, alert: Alert, resolved_by: str):
        """Send alert resolution notification"""
        # Similar to _dispatch_alert but for resolution
        pass

class AnomalyDetector:
    """ML-based anomaly detection for reducing false positives"""
    
    def __init__(self):
        self.history = {}
        self.window_size = 100  # Number of data points to keep
    
    async def is_anomaly(self, metrics: Dict[str, Any], rule_name: str) -> bool:
        """Check if metrics represent an anomaly"""
        # Store historical data
        if rule_name not in self.history:
            self.history[rule_name] = []
        
        self.history[rule_name].append(metrics)
        if len(self.history[rule_name]) > self.window_size:
            self.history[rule_name].pop(0)
        
        # Simple statistical anomaly detection
        # In production, this would use more sophisticated ML models
        
        if len(self.history[rule_name]) < 10:  # Need minimum data points
            return True
        
        # Extract relevant metric values
        metric_values = []
        for data_point in self.history[rule_name]:
            if 'cpu_usage' in data_point:
                metric_values.append(data_point['cpu_usage'])
            elif 'memory_usage' in data_point:
                metric_values.append(data_point['memory_usage'])
            elif 'error_rate' in data_point:
                metric_values.append(data_point['error_rate'])
            elif 'response_time_avg' in data_point:
                metric_values.append(data_point['response_time_avg'])
        
        if not metric_values:
            return True
        
        # Calculate mean and standard deviation
        mean = sum(metric_values) / len(metric_values)
        std_dev = (sum((x - mean) ** 2 for x in metric_values) / len(metric_values)) ** 0.5
        
        if std_dev == 0:  # No variation
            return False
        
        # Check if current value is an outlier (3 sigma rule)
        current_value = next(iter(metrics.values()))  # Get first metric value
        z_score = abs(current_value - mean) / std_dev
        
        return z_score > 3  # 99.7% confidence interval

# Incident management integration
class IncidentManager:
    """Integration with incident management tools"""
    
    def __init__(self):
        self.incident_tools = {
            'pagerduty': self._pagerduty_integration,
            'opsgenie': self._opsgenie_integration,
            'victorops': self._victorops_integration
        }
    
    async def create_incident(self, alert: Alert) -> str:
        """Create incident in incident management tool"""
        tool = os.getenv('INCIDENT_MANAGEMENT_TOOL', 'pagerduty')
        
        if tool in self.incident_tools:
            incident_id = await self.incident_tools[tool](alert)
            return incident_id
        
        return None
    
    async def _pagerduty_integration(self, alert: Alert) -> str:
        """Integrate with PagerDuty"""
        # Implementation would use PagerDuty API
        return f"pd_{alert.id}"
    
    async def _opsgenie_integration(self, alert: Alert) -> str:
        """Integrate with OpsGenie"""
        # Implementation would use OpsGenie API
        return f"og_{alert.id}"
    
    async def _victorops_integration(self, alert: Alert) -> str:
        """Integrate with VictorOps"""
        # Implementation would use VictorOps API
        return f"vo_{alert.id}"

# Alert management endpoints
@app.post("/alerts/{alert_id}/acknowledge", tags=["Monitoring"])
async def acknowledge_alert(
    alert_id: str,
    user: UserRecord = Depends(get_current_active_user)
):
    """Acknowledge an alert"""
    alerting_system = IntelligentAlertingSystem()
    await alerting_system.acknowledge_alert(alert_id, user.username)
    
    return {"status": "acknowledged", "alert_id": alert_id}

@app.post("/alerts/{alert_id}/resolve", tags=["Monitoring"])
async def resolve_alert(
    alert_id: str,
    user: UserRecord = Depends(get_current_active_user)
):
    """Resolve an alert"""
    alerting_system = IntelligentAlertingSystem()
    await alerting_system.resolve_alert(alert_id, user.username)
    
    return {"status": "resolved", "alert_id": alert_id}

@app.get("/alerts/active", tags=["Monitoring"])
async def get_active_alerts():
    """Get active alerts"""
    alerting_system = IntelligentAlertingSystem()
    return {
        "alerts": [
            alert.__dict__ for alert in alerting_system.active_alerts.values()
        ]
    }

@app.get("/alerts/history", tags=["Monitoring"])
async def get_alert_history(
    start_time: datetime = Query(None),
    end_time: datetime = Query(None),
    severity: str = Query(None)
):
    """Get alert history"""
    alerting_system = IntelligentAlertingSystem()
    
    alerts = alerting_system.alert_history
    
    # Apply filters
    if start_time:
        alerts = [a for a in alerts if a.timestamp >= start_time]
    if end_time:
        alerts = [a for a in alerts if a.timestamp <= end_time]
    if severity:
        alerts = [a for a in alerts if a.severity == severity]
    
    return {
        "alerts": [
            alert.__dict__ for alert in alerts
        ]
    }