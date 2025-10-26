# agent_client.py - Reference implementation for agents to connect to manager

import asyncio
import logging
import json
import uuid
import platform
import socket
import ssl
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

# Optional dependencies - System monitoring
# Optional dependencies
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False

# Optional dependencies - HTTP client
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    aiohttp = None
    HAS_AIOHTTP = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentStatus(str, Enum):
    INITIALIZING = "initializing"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"

class AgentClient:
    """Agent client for connecting to YMERA Supreme Manager"""
    
    def __init__(self, manager_url: str, agent_id: str, api_key: str,
                 cert_path: Optional[str] = None, key_path: Optional[str] = None,
                 ca_path: Optional[str] = None):
        self.manager_url = manager_url.rstrip('/')
        self.agent_id = agent_id
        self.api_key = api_key
        self.ws_url = f"{manager_url.replace('http', 'ws')}/ws/agents/{agent_id}"
        
        # SSL context for mTLS
        self.ssl_context = None
        if cert_path and key_path and ca_path:
            self.ssl_context = self._create_ssl_context(cert_path, key_path, ca_path)
        
        # Internal state
        self.status = AgentStatus.INITIALIZING
        self.capabilities = []
        self.task_handlers = {}
        self.websocket = None
        self.heartbeat_interval = 30  # seconds
        self.report_interval = 60  # seconds
        self.reporting_schedule = None
        self.running = False
        self.reconnect_delay = 1  # seconds (with exponential backoff)
        
        # Task queue
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
    
    def _create_ssl_context(self, cert_path: str, key_path: str, ca_path: str) -> ssl.SSLContext:
        """Create SSL context for mTLS"""
        context = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=ca_path
        )
        context.load_cert_chain(certfile=cert_path, keyfile=key_path)
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        return context
    
    def register_capability(self, capability: str, handler: Callable):
        """Register agent capability with handler"""
        self.capabilities.append(capability)
        self.task_handlers[capability] = handler
        logger.info(f"Registered capability: {capability}")
    
    async def connect(self):
        """Connect to manager and start agent operation"""
        # First, verify HTTP API connection
        if not await self._verify_api_connection():
            logger.error("Failed to connect to manager API")
            return False
        
        # Start agent operation
        self.running = True
        
        # Start background tasks
        asyncio.create_task(self._websocket_handler())
        asyncio.create_task(self._heartbeat_sender())
        asyncio.create_task(self._status_reporter())
        asyncio.create_task(self._task_processor())
        
        return True
    
    async def _verify_api_connection(self) -> bool:
        """Verify connection to manager API"""
        if not HAS_AIOHTTP:
            logger.warning("aiohttp not available, skipping API connection")
            return False
            
        try:
            # Check health endpoint
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.get(f"{self.manager_url}/health", headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Health check failed: {response.status}")
                        return False
                    return True
        except Exception as e:
            logger.error(f"API connection failed: {e}")
            return False
    
    async def _websocket_handler(self):
        """Handle WebSocket connection and messages"""
        if not HAS_AIOHTTP:
            logger.warning("aiohttp not available, cannot handle WebSocket")
            return
            
        while self.running:
            try:
                # Connect to WebSocket
                async with aiohttp.ClientSession() as session:
                    logger.info(f"Connecting to WebSocket: {self.ws_url}")
                    
                    # Prepare headers with authentication
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    
                    # Connect with proper SSL context if available
                    async with session.ws_connect(
                        self.ws_url,
                        headers=headers,
                        ssl_context=self.ssl_context,
                        heartbeat=30,  # 30 second heartbeat
                        timeout=60
                    ) as websocket:
                        self.websocket = websocket
                        logger.info("WebSocket connection established")
                        self.reconnect_delay = 1  # Reset backoff on successful connection
                        
                        # Process incoming messages
                        async for message in websocket:
                            if message.type == aiohttp.WSMsgType.TEXT:
                                await self._handle_ws_message(message.data)
                            elif message.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                logger.warning(f"WebSocket closed: {message.data}")
                                break
                        
                        self.websocket = None
            
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.websocket = None
                
                # Exponential backoff for reconnection
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, 60)  # Max 60 seconds
    
    async def _handle_ws_message(self, message_data: str):
        """Handle incoming WebSocket message"""
        try:
            message = json.loads(message_data)
            message_type = message.get("type", "")
            
            logger.debug(f"Received message type: {message_type}")
            
            if message_type == "connection_established":
                # Handle connection established
                if "reporting_schedule" in message:
                    self.reporting_schedule = message["reporting_schedule"]
                    self.report_interval = self.reporting_schedule.get("reporting_interval", 60)
                    self.heartbeat_interval = min(30, self.report_interval / 2)
                    logger.info(f"Updated reporting schedule: every {self.report_interval}s")
                
                self.status = AgentStatus.ACTIVE
            
            elif message_type == "task":
                # Queue task for processing
                task_id = message.get("task_id")
                task_type = message.get("task_type")
                parameters = message.get("parameters", {})
                
                logger.info(f"Received task: {task_id} ({task_type})")
                
                if task_type in self.task_handlers:
                    await self.task_queue.put({
                        "task_id": task_id,
                        "task_type": task_type,
                        "parameters": parameters
                    })
                else:
                    # Report inability to handle task
                    await self._send_task_error(
                        task_id,
                        "unsupported_task_type",
                        f"Agent does not support task type: {task_type}"
                    )
            
            elif message_type == "terminate":
                # Handle termination request
                logger.warning(f"Received termination request: {message.get('reason')}")
                self.status = AgentStatus.SHUTTING_DOWN
                self.running = False
            
            elif message_type == "receipt":
                # Acknowledge message receipt
                logger.debug(f"Receipt acknowledged for message: {message.get('message_id')}")
            
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def _heartbeat_sender(self):
        """Send periodic heartbeats"""
        while self.running:
            if self.websocket and self.status != AgentStatus.SHUTTING_DOWN:
                try:
                    heartbeat = {
                        "type": "heartbeat",
                        "message_id": str(uuid.uuid4()),
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": self.status
                    }
                    
                    await self.websocket.send_json(heartbeat)
                    logger.debug("Heartbeat sent")
                    
                except Exception as e:
                    logger.error(f"Failed to send heartbeat: {e}")
            
            await asyncio.sleep(self.heartbeat_interval)
    
    async def _status_reporter(self):
        """Send periodic status reports"""
        while self.running:
            if self.websocket and self.status != AgentStatus.SHUTTING_DOWN:
                try:
                    # Gather system metrics
                    metrics = await self._gather_metrics()
                    
                    # Build report
                    report = {
                        "type": "status_report",
                        "message_id": str(uuid.uuid4()),
                        "timestamp": datetime.utcnow().isoformat(),
                        "report": {
                            "status": self.status,
                            "metrics": metrics,
                            "tasks_active": len(self.active_tasks),
                            "queue_size": self.task_queue.qsize()
                        }
                    }
                    
                    await self.websocket.send_json(report)
                    logger.debug("Status report sent")
                    
                except Exception as e:
                    logger.error(f"Failed to send status report: {e}")
            
            # Use reporting interval from schedule if available
            await asyncio.sleep(self.report_interval)
    
    async def _task_processor(self):
        """Process tasks from queue"""
        while self.running:
            try:
                # Get task from queue
                task = await self.task_queue.get()
                task_id = task["task_id"]
                task_type = task["task_type"]
                parameters = task["parameters"]
                
                logger.info(f"Processing task: {task_id}")
                self.status = AgentStatus.BUSY
                self.active_tasks[task_id] = task
                
                # Handle task
                handler = self.task_handlers.get(task_type)
                if handler:
                    try:
                        # Execute task handler
                        result = await handler(parameters)
                        
                        # Send success result
                        await self._send_task_result(task_id, result)
                        
                    except Exception as e:
                        logger.error(f"Task {task_id} execution error: {e}")
                        
                        # Send error result
                        await self._send_task_error(
                            task_id,
                            "execution_error",
                            str(e)
                        )
                else:
                    await self._send_task_error(
                        task_id,
                        "no_handler",
                        f"No handler for task type: {task_type}"
                    )
                
                # Cleanup
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
                
                # Update status if no more active tasks
                if not self.active_tasks:
                    self.status = AgentStatus.ACTIVE
                
                self.task_queue.task_done()
                
            except asyncio.CancelledError:
                break
                
            except Exception as e:
                logger.error(f"Task processing error: {e}")
                await asyncio.sleep(1)
    
    async def _send_task_result(self, task_id: str, result: Any):
        """Send task result to manager"""
        if self.websocket:
            try:
                message = {
                    "type": "task_result",
                    "message_id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "status": "completed",
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.websocket.send_json(message)
                logger.info(f"Task {task_id} result sent")
                
            except Exception as e:
                logger.error(f"Failed to send task result: {e}")
    
    async def _send_task_error(self, task_id: str, error_type: str, error_message: str):
        """Send task error to manager"""
        if self.websocket:
            try:
                message = {
                    "type": "task_result",
                    "message_id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "status": "failed",
                    "error": {
                        "type": error_type,
                        "message": error_message
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.websocket.send_json(message)
                logger.info(f"Task {task_id} error sent: {error_type}")
                
            except Exception as e:
                logger.error(f"Failed to send task error: {e}")
    
    async def report_error(self, error_type: str, error_message: str, severity: str = "medium"):
        """Report agent error to manager"""
        if self.websocket:
            try:
                message = {
                    "type": "error",
                    "message_id": str(uuid.uuid4()),
                    "error_type": error_type,
                    "error_message": error_message,
                    "severity": severity,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.websocket.send_json(message)
                logger.info(f"Error reported: {error_type}")
                
                if severity == "critical":
                    self.status = AgentStatus.ERROR
                
            except Exception as e:
                logger.error(f"Failed to send error report: {e}")
    
    async def shutdown(self):
        """Gracefully shut down agent"""
        logger.info("Shutting down agent")
        self.status = AgentStatus.SHUTTING_DOWN
        self.running = False
        
        # Wait for tasks to complete
        if self.active_tasks:
            try:
                await asyncio.wait_for(self.task_queue.join(), timeout=30)
            except asyncio.TimeoutError:
                logger.warning("Shutdown timed out waiting for tasks to complete")
        
        # Close websocket
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        logger.info("Agent shutdown complete")
    
    async def _gather_metrics(self) -> Dict:
        """Gather system metrics for reporting"""
        metrics = {
            "load": len(self.active_tasks) + self.task_queue.qsize(),
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "uptime": self._get_process_uptime()
        }
        
        # Add system metrics if psutil is available
        if HAS_PSUTIL:
            try:
                metrics.update({
                    "cpu": psutil.cpu_percent(interval=None),
                    "memory": psutil.virtual_memory().percent,
                    "disk": psutil.disk_usage('/').percent,
                })
            except Exception:
                pass
            
            # Additional metrics
            try:
                metrics["network"] = {
                    "connections": len(psutil.net_connections()),
                    "bytes_sent": psutil.net_io_counters().bytes_sent,
                    "bytes_recv": psutil.net_io_counters().bytes_recv
                }
            except Exception:
                pass
        
        return metrics
    
    def _get_process_uptime(self) -> float:
        """Get process uptime in seconds"""
        if not HAS_PSUTIL:
            return 0.0
        try:
            process = psutil.Process(os.getpid())
            return datetime.now().timestamp() - process.create_time()
        except Exception:
            return 0.0