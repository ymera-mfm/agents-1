
"""
Metrics Agent for Multi-Agent Platform
Collects, aggregates, and visualizes metrics from all agents and components.
"""

import asyncio
import json
import time
import os
from typing import Dict, List, Any
from collections import defaultdict

from base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResponse

class MetricsAgent(BaseAgent):
    """
    The Metrics Agent is responsible for:
    - Subscribing to metrics streams from all agents.
    - Aggregating and storing metrics data.
    - Providing an API for metrics visualization and querying.
    - Detecting anomalies and triggering alerts (future).
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.metrics_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.summary_metrics: Dict[str, Any] = {}
        self.last_summary_update = time.time()

    async def start(self):
        await self._subscribe(
            "METRICS",
            self._handle_metrics_data,
            queue_group="metrics_agents"
        )
        self.logger.info("Metrics Agent started, subscribing to METRICS stream.")
        asyncio.create_task(self._summarize_metrics_periodically())

    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Implement the actual task logic for the Metrics agent"""
        task_type = request.task_type
        payload = request.payload

        try:
            result: Dict[str, Any] = {}
            if task_type == "get_all_metrics":
                result = {"metrics": self.metrics_data, "summary": self.summary_metrics}
            elif task_type == "get_agent_metrics":
                agent_id = payload["agent_id"]
                result = {"metrics": self.metrics_data.get(agent_id, []), "summary": self.summary_metrics.get(agent_id)}
            elif task_type == "get_summary_metrics":
                result = {"summary": self.summary_metrics}
            else:
                raise ValueError(f"Unknown metrics task type: {task_type}")
            
            return TaskResponse(task_id=request.task_id, success=True, result=result).dict()

        except Exception as e:
            self.logger.error(f"Error executing metrics task {task_type}", error=str(e))
            return TaskResponse(task_id=request.task_id, success=False, error=str(e)).dict()

    async def _handle_metrics_data(self, msg):
        try:
            data = json.loads(msg.data.decode())
            agent_id = data.get("agent_id", "unknown_agent")
            metrics = data.get("metrics", {})
            timestamp = data.get("timestamp", time.time())

            self.metrics_data[agent_id].append({"timestamp": timestamp, "metrics": metrics})
            # Keep only a certain amount of historical data, e.g., last 1000 entries per agent
            if len(self.metrics_data[agent_id]) > 1000:
                self.metrics_data[agent_id].pop(0)
            
            self.logger.debug(f"Received metrics from {agent_id}")

        except Exception as e:
            self.logger.error(f"Error processing metrics data: {e}")

    async def _summarize_metrics_periodically(self):
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(30) # Summarize every 30 seconds
                self._generate_summary_metrics()
                self.last_summary_update = time.time()
                self.logger.debug("Metrics summarized.")
            except Exception as e:
                self.logger.error(f"Error in periodic metrics summarization: {e}")
                await asyncio.sleep(60)

    def _generate_summary_metrics(self):
        new_summary = {}
        for agent_id, data_points in self.metrics_data.items():
            if not data_points:
                continue
            
            # Simple aggregation: take the latest metrics as summary
            latest_data = data_points[-1]["metrics"]
            new_summary[agent_id] = latest_data
            
            # Example: Calculate average load for orchestrator
            if agent_id == "orchestrator" and "agent_loads" in latest_data:
                total_load = sum(latest_data["agent_loads"].values())
                num_agents = len(latest_data["agent_loads"])
                new_summary[agent_id]["average_agent_load"] = total_load / num_agents if num_agents > 0 else 0

            # Example: Total token usage for LLM agent
            if agent_id == "llm_agent" and "token_usage" in latest_data:
                new_summary[agent_id]["total_tokens_used"] = latest_data["token_usage"]["prompt_tokens"] + latest_data["token_usage"]["completion_tokens"]

        self.summary_metrics = new_summary


if __name__ == "__main__":
    config = AgentConfig(
        name="metrics_agent",
        agent_type="metrics",
        capabilities=["metrics_collection", "metrics_aggregation", "metrics_query"],
        nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )
    
    agent = MetricsAgent(config)
    asyncio.run(agent.run())

