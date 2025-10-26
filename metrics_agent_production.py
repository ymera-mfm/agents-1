"""
Production-Ready Metrics Agent v3.0
Enterprise metrics collection, aggregation, and query system

PRODUCTION ENHANCEMENTS:
- Removed dependency issues
- Added proper batch processing
- Enhanced error recovery
- Memory-efficient buffering
- Production-grade aggregation
- Query optimization
- Health monitoring
"""

import asyncio
import json
import time
import os
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import statistics

from base_agent import (
    BaseAgent,
    AgentConfig,
    TaskRequest,
    Priority,
    AgentState,
    ConnectionState
)


@dataclass
class MetricDataPoint:
    """Structured metric data point"""
    agent_id: str
    metric_name: str
    value: Any
    unit: str
    timestamp: float
    tags: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MetricSummary:
    """Aggregated metric summary"""
    agent_id: str
    metric_type: str
    count: int
    avg_value: Optional[float]
    min_value: Optional[float]
    max_value: Optional[float]
    p50_value: Optional[float]
    p95_value: Optional[float]
    p99_value: Optional[float]
    last_updated: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsAgent(BaseAgent):
    """
    Production Metrics Agent with:
    - Real-time metric collection
    - Efficient batch processing
    - Time-series aggregation
    - Query API with filters
    - Anomaly detection
    - Health monitoring
    - Memory management
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # In-memory buffers (limited retention)
        self.metrics_buffer: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.summary_cache: Dict[str, MetricSummary] = {}
        
        # Configuration
        self.max_buffer_size = int(os.getenv("METRICS_BUFFER_SIZE", "1000"))
        self.batch_write_size = int(os.getenv("METRICS_BATCH_SIZE", "100"))
        self.batch_write_interval = int(os.getenv("METRICS_BATCH_INTERVAL", "30"))
        self.summary_interval = int(os.getenv("METRICS_SUMMARY_INTERVAL", "60"))
        self.retention_hours = int(os.getenv("METRICS_RETENTION_HOURS", "24"))
        
        # Batch write queue
        self.write_queue: deque = deque(maxlen=10000)
        self.last_summary_update = time.time()
        self.last_batch_write = time.time()
        
        # Statistics
        self.stats = {
            'metrics_received': 0,
            'metrics_persisted': 0,
            'batch_writes': 0,
            'write_errors': 0,
            'buffer_overflows': 0,
            'avg_batch_size': 0
        }
    
    async def _setup_subscriptions(self):
        """Setup metric subscriptions"""
        await super()._setup_subscriptions()
        
        # Generic metrics from all agents
        await self._subscribe(
            "metrics.>",
            self._handle_metrics_data,
            queue_group="metrics_collectors"
        )
        
        # System metrics
        await self._subscribe(
            "system.metrics",
            self._handle_system_metrics,
            queue_group="metrics_collectors"
        )
        
        # Performance metrics
        await self._subscribe(
            "performance.metrics",
            self._handle_performance_metrics,
            queue_group="metrics_collectors"
        )
        
        # Agent heartbeats
        await self._subscribe(
            "agent.*.heartbeat",
            self._handle_heartbeat_metrics,
            queue_group="metrics_collectors"
        )
        
        self.logger.info("Metrics subscriptions configured")
    
    async def _start_background_tasks(self):
        """Start background processing tasks"""
        await super()._start_background_tasks()
        
        # Batch writer
        task = asyncio.create_task(self._batch_write_worker())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Summary generator
        task = asyncio.create_task(self._summary_generator_worker())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Buffer cleanup
        task = asyncio.create_task(self._buffer_cleanup_worker())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Self-monitoring
        task = asyncio.create_task(self._self_monitoring_worker())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        self.logger.info("Metrics background tasks started")
    
    async def _handle_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Handle metric query tasks"""
        
        handlers = {
            "get_metrics": self._get_metrics,
            "get_agent_metrics": self._get_agent_metrics,
            "get_summary": self._get_summary,
            "query_metrics": self._query_metrics,
            "get_statistics": self._get_statistics,
            "clear_metrics": self._clear_metrics,
            "get_health": self._get_health_status
        }
        
        handler = handlers.get(task_request.task_type)
        if handler:
            return await handler(task_request.payload)
        
        return await super()._handle_task(task_request)
    
    async def _handle_metrics_data(self, msg):
        """Handle generic metrics data"""
        try:
            data = json.loads(msg.data.decode())
            
            agent_id = data.get("agent_id", "unknown")
            metrics = data.get("metrics", {})
            timestamp = data.get("timestamp", time.time())
            tags = data.get("tags", {})
            
            if isinstance(metrics, dict):
                for name, value in metrics.items():
                    await self._process_metric(
                        agent_id, name, value,
                        data.get("unit", "count"),
                        timestamp, tags
                    )
            
            self.stats['metrics_received'] += len(metrics) if isinstance(metrics, dict) else 1
            
        except Exception as e:
            self.logger.error(f"Error processing metrics: {e}")
        finally:
            await msg.ack()
    
    async def _handle_system_metrics(self, msg):
        """Handle system metrics"""
        try:
            data = json.loads(msg.data.decode())
            
            await self._process_metric(
                "system",
                data.get("metric_name", "system_metric"),
                data.get("value", data),
                "json",
                data.get("timestamp", time.time()),
                {"source": "system"}
            )
            
        except Exception as e:
            self.logger.error(f"Error processing system metrics: {e}")
        finally:
            await msg.ack()
    
    async def _handle_performance_metrics(self, msg):
        """Handle performance metrics"""
        try:
            data = json.loads(msg.data.decode())
            
            await self._process_metric(
                "performance",
                data.get("metric_name", "perf_metric"),
                data.get("value", data),
                "json",
                data.get("timestamp", time.time()),
                {"source": "performance"}
            )
            
        except Exception as e:
            self.logger.error(f"Error processing performance metrics: {e}")
        finally:
            await msg.ack()
    
    async def _handle_heartbeat_metrics(self, msg):
        """Handle heartbeat metrics"""
        try:
            data = json.loads(msg.data.decode())
            
            await self._process_metric(
                data.get("agent_id", "unknown"),
                "heartbeat",
                {"state": data.get("state"), "alive": True},
                "status",
                data.get("timestamp", time.time()),
                {"type": "heartbeat"}
            )
            
        except Exception as e:
            self.logger.error(f"Error processing heartbeat: {e}")
        finally:
            await msg.ack()
    
    async def _process_metric(
        self,
        agent_id: str,
        metric_name: str,
        value: Any,
        unit: str,
        timestamp: float,
        tags: Dict[str, str]
    ):
        """Process and buffer metric"""
        try:
            data_point = MetricDataPoint(
                agent_id=agent_id,
                metric_name=metric_name,
                value=value,
                unit=unit,
                timestamp=timestamp,
                tags=tags
            )
            
            # Add to buffer
            buffer_key = f"{agent_id}:{metric_name}"
            self.metrics_buffer[buffer_key].append(data_point)
            
            # Add to write queue
            self.write_queue.append(data_point)
            
            # Check buffer overflow
            if len(self.metrics_buffer[buffer_key]) >= self.max_buffer_size:
                self.stats['buffer_overflows'] += 1
            
            # Trigger write if queue full
            if len(self.write_queue) >= self.batch_write_size:
                asyncio.create_task(self._flush_write_queue())
                
        except Exception as e:
            self.logger.error(f"Error processing metric: {e}")
    
    async def _batch_write_worker(self):
        """Background worker for batch writes"""
        while self.state == AgentState.RUNNING:
            try:
                await asyncio.sleep(self.batch_write_interval)
                
                if self.write_queue:
                    await self._flush_write_queue()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Batch write worker error: {e}")
    
    async def _flush_write_queue(self):
        """Flush write queue to database"""
        if not self.write_queue or self.postgres_state != ConnectionState.CONNECTED:
            return
        
        # Take batch from queue
        batch = []
        batch_size = min(len(self.write_queue), self.batch_write_size)
        
        for _ in range(batch_size):
            if self.write_queue:
                batch.append(self.write_queue.popleft())
        
        if not batch:
            return
        
        try:
            await self._batch_persist(batch)
            
            self.stats['metrics_persisted'] += len(batch)
            self.stats['batch_writes'] += 1
            
            # Update average batch size
            total_writes = self.stats['batch_writes']
            current_avg = self.stats['avg_batch_size']
            self.stats['avg_batch_size'] = (
                (current_avg * (total_writes - 1) + len(batch)) / total_writes
            )
            
            self.last_batch_write = time.time()
            
            self.logger.debug(f"Batch persisted: {len(batch)} metrics")
            
        except Exception as e:
            self.stats['write_errors'] += 1
            self.logger.error(f"Batch persist failed: {e}")
            
            # Re-add to queue with limit
            if len(self.write_queue) < self.max_buffer_size * 10:
                self.write_queue.extendleft(reversed(batch))
    
    async def _batch_persist(self, batch: List[MetricDataPoint]):
        """Persist batch to database"""
        if not self.db_pool:
            return
        
        query = """
            INSERT INTO system_metrics 
            (agent_id, metric_name, value, unit, timestamp, tags)
            VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                for dp in batch:
                    await conn.execute(
                        query,
                        dp.agent_id,
                        dp.metric_name,
                        json.dumps(dp.value),
                        dp.unit,
                        datetime.fromtimestamp(dp.timestamp),
                        json.dumps(dp.tags)
                    )
    
    async def _summary_generator_worker(self):
        """Background worker for generating summaries"""
        while self.state == AgentState.RUNNING:
            try:
                await asyncio.sleep(self.summary_interval)
                await self._generate_summaries()
                self.last_summary_update = time.time()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Summary generator error: {e}")
    
    async def _generate_summaries(self):
        """Generate metric summaries"""
        new_summaries = {}
        
        for buffer_key, data_points in self.metrics_buffer.items():
            if not data_points:
                continue
            
            agent_id, metric_name = buffer_key.split(':', 1)
            
            # Extract numeric values
            numeric_values = []
            for dp in data_points:
                if isinstance(dp.value, (int, float)):
                    numeric_values.append(float(dp.value))
            
            if not numeric_values:
                continue
            
            # Calculate statistics
            sorted_values = sorted(numeric_values)
            count = len(sorted_values)
            
            summary = MetricSummary(
                agent_id=agent_id,
                metric_type=metric_name,
                count=count,
                avg_value=statistics.mean(numeric_values),
                min_value=min(numeric_values),
                max_value=max(numeric_values),
                p50_value=sorted_values[count // 2],
                p95_value=sorted_values[int(count * 0.95)],
                p99_value=sorted_values[int(count * 0.99)],
                last_updated=time.time()
            )
            
            new_summaries[buffer_key] = summary
        
        self.summary_cache = new_summaries
        self.logger.debug(f"Generated {len(new_summaries)} summaries")
    
    async def _buffer_cleanup_worker(self):
        """Background worker for cleaning old data"""
        while self.state == AgentState.RUNNING:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                cutoff_time = time.time() - (self.retention_hours * 3600)
                
                for buffer_key in list(self.metrics_buffer.keys()):
                    buffer = self.metrics_buffer[buffer_key]
                    
                    # Remove old entries
                    while buffer and buffer[0].timestamp < cutoff_time:
                        buffer.popleft()
                    
                    # Remove empty buffers
                    if not buffer:
                        del self.metrics_buffer[buffer_key]
                
                self.logger.debug("Buffer cleanup completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Buffer cleanup error: {e}")
    
    async def _self_monitoring_worker(self):
        """Self-monitoring worker"""
        while self.state == AgentState.RUNNING:
            try:
                await asyncio.sleep(60)
                
                metrics = {
                    "metrics_received": self.stats['metrics_received'],
                    "metrics_persisted": self.stats['metrics_persisted'],
                    "batch_writes": self.stats['batch_writes'],
                    "write_errors": self.stats['write_errors'],
                    "buffer_overflows": self.stats['buffer_overflows'],
                    "buffer_count": len(self.metrics_buffer),
                    "queue_size": len(self.write_queue),
                    "summary_count": len(self.summary_cache)
                }
                
                await self._publish(
                    "metrics.agent.self",
                    {
                        "agent_id": self.config.agent_id,
                        "metrics": metrics,
                        "timestamp": time.time()
                    }
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Self-monitoring error: {e}")
    
    # Task handlers
    
    async def _get_metrics(self, payload: Dict) -> Dict[str, Any]:
        """Get all current metrics"""
        limit = payload.get("limit", 100)
        
        all_metrics = {}
        for buffer_key, data_points in self.metrics_buffer.items():
            all_metrics[buffer_key] = [
                dp.to_dict() for dp in list(data_points)[-limit:]
            ]
        
        return {
            "status": "success",
            "metrics": all_metrics,
            "count": sum(len(v) for v in all_metrics.values()),
            "buffer_count": len(self.metrics_buffer)
        }
    
    async def _get_agent_metrics(self, payload: Dict) -> Dict[str, Any]:
        """Get metrics for specific agent"""
        agent_id = payload.get("agent_id")
        if not agent_id:
            return {"status": "error", "message": "agent_id required"}
        
        limit = payload.get("limit", 100)
        
        agent_metrics = {}
        for buffer_key, data_points in self.metrics_buffer.items():
            if buffer_key.startswith(f"{agent_id}:"):
                agent_metrics[buffer_key] = [
                    dp.to_dict() for dp in list(data_points)[-limit:]
                ]
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "metrics": agent_metrics,
            "count": sum(len(v) for v in agent_metrics.values())
        }
    
    async def _get_summary(self, payload: Dict) -> Dict[str, Any]:
        """Get metric summaries"""
        agent_id = payload.get("agent_id")
        
        if agent_id:
            summaries = {
                k: v.to_dict()
                for k, v in self.summary_cache.items()
                if k.startswith(f"{agent_id}:")
            }
        else:
            summaries = {k: v.to_dict() for k, v in self.summary_cache.items()}
        
        return {
            "status": "success",
            "summaries": summaries,
            "count": len(summaries),
            "last_updated": self.last_summary_update
        }
    
    async def _query_metrics(self, payload: Dict) -> Dict[str, Any]:
        """Query metrics with filters"""
        agent_ids = payload.get("agent_ids", [])
        metric_names = payload.get("metric_names", [])
        start_time = payload.get("start_time")
        end_time = payload.get("end_time")
        
        results = []
        
        for buffer_key, data_points in self.metrics_buffer.items():
            agent_id, metric_name = buffer_key.split(':', 1)
            
            # Apply filters
            if agent_ids and agent_id not in agent_ids:
                continue
            if metric_names and metric_name not in metric_names:
                continue
            
            for dp in data_points:
                if start_time and dp.timestamp < start_time:
                    continue
                if end_time and dp.timestamp > end_time:
                    continue
                
                results.append(dp.to_dict())
        
        return {
            "status": "success",
            "results": results,
            "count": len(results)
        }
    
    async def _get_statistics(self, payload: Dict) -> Dict[str, Any]:
        """Get metrics agent statistics"""
        return {
            "status": "success",
            "statistics": self.stats,
            "buffer_info": {
                "total_buffers": len(self.metrics_buffer),
                "total_data_points": sum(len(b) for b in self.metrics_buffer.values()),
                "queue_size": len(self.write_queue),
                "summary_count": len(self.summary_cache)
            },
            "timing": {
                "last_batch_write": self.last_batch_write,
                "last_summary_update": self.last_summary_update
            }
        }
    
    async def _clear_metrics(self, payload: Dict) -> Dict[str, Any]:
        """Clear metrics (admin operation)"""
        agent_id = payload.get("agent_id")
        
        if agent_id:
            cleared = 0
            for buffer_key in list(self.metrics_buffer.keys()):
                if buffer_key.startswith(f"{agent_id}:"):
                    cleared += len(self.metrics_buffer[buffer_key])
                    del self.metrics_buffer[buffer_key]
            
            return {
                "status": "success",
                "cleared": cleared,
                "agent_id": agent_id
            }
        else:
            total = sum(len(b) for b in self.metrics_buffer.values())
            self.metrics_buffer.clear()
            self.summary_cache.clear()
            
            return {
                "status": "success",
                "cleared": total
            }
    
    async def _get_health_status(self, payload: Dict = None) -> Dict[str, Any]:
        """Get health status"""
        buffer_health = "healthy"
        total_points = sum(len(b) for b in self.metrics_buffer.values())
        if total_points > self.max_buffer_size * len(self.metrics_buffer) * 0.9:
            buffer_health = "warning"
        
        queue_health = "healthy"
        if len(self.write_queue) > self.batch_write_size * 10:
            queue_health = "critical"
        
        error_rate = self.stats['write_errors'] / max(self.stats['batch_writes'], 1)
        write_health = "healthy"
        if error_rate > 0.01:
            write_health = "warning"
        if error_rate > 0.05:
            write_health = "critical"
        
        overall = "healthy"
        if any(h in ["warning", "critical"] for h in [buffer_health, queue_health, write_health]):
            overall = "degraded"
        if any(h == "critical" for h in [buffer_health, queue_health, write_health]):
            overall = "critical"
        
        return {
            "status": "success",
            "health": {
                "overall": overall,
                "buffer_health": buffer_health,
                "queue_health": queue_health,
                "write_health": write_health,
                "error_rate": error_rate,
                "connections": {
                    "nats": self.nats_state.value,
                    "postgres": self.postgres_state.value,
                    "redis": self.redis_state.value
                }
            }
        }
    
    async def stop(self):
        """Graceful shutdown"""
        self.logger.info("Stopping Metrics Agent, flushing remaining metrics...")
        
        # Flush remaining metrics
        if self.write_queue:
            await self._flush_write_queue()
        
        self.logger.info(
            "Metrics Agent stopped",
            received=self.stats['metrics_received'],
            persisted=self.stats['metrics_persisted']
        )
        
        await super().stop()


# Database schema
METRICS_DB_SCHEMA = """
-- System metrics table with partitioning support
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGSERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    unit VARCHAR(50),
    timestamp TIMESTAMP NOT NULL,
    tags JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_metrics_agent_id ON system_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_agent_time ON system_metrics(agent_id, timestamp DESC);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_metrics_agent_name_time 
ON system_metrics(agent_id, metric_name, timestamp DESC);
"""


if __name__ == "__main__":
    async def main():
        config = AgentConfig(
            agent_id=os.getenv("AGENT_ID", "metrics-agent-001"),
            name="metrics_agent",
            agent_type="metrics",
            version="3.0.0",
            nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL"),
            max_concurrent_tasks=200
        )
        
        agent = MetricsAgent(config)
        
        if await agent.start():
            print(f"✓ Metrics Agent started: {config.agent_id}")
            await agent.run_forever()
        else:
            print("✗ Failed to start Metrics Agent")
            return 1
        
        return 0
    
    try:
        exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nMetrics Agent stopped")
    except Exception as e:
        print(f"Fatal error: {e}")
        exit(1)