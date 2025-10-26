
"""
Configuration Manager for Multi-Agent Platform
Provides centralized, dynamic configuration management for all agents.
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional

from base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResponse

class ConfigManager(BaseAgent):
    """
    The ConfigManager is responsible for:
    - Storing and managing configuration for all agents and the platform.
    - Providing a centralized interface for agents to fetch their configurations.
    - Allowing dynamic updates to configurations without restarting agents.
    - Persisting configurations to a database or configuration store.
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.configurations: Dict[str, Dict[str, Any]] = {}
        self.last_config_update: Dict[str, float] = {}

    async def start(self):
        # Load initial configurations from DB or file
        await self._load_all_configurations()

        # Subscribe to configuration update requests
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

        self.logger.info("Config Manager started.")

    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Implement the actual task logic for the Config Manager agent"""
        task_type = request.task_type
        payload = request.payload

        try:
            result: Dict[str, Any] = {}
            if task_type == "get_config":
                agent_name = payload["agent_name"]
                result = {"config": self.configurations.get(agent_name, {})}
            elif task_type == "set_config":
                agent_name = payload["agent_name"]
                new_config = payload["config"]
                await self._set_configuration(agent_name, new_config)
                result = {"status": "success", "agent_name": agent_name}
            elif task_type == "reload_all_configs":
                await self._load_all_configurations()
                result = {"status": "success", "message": "All configurations reloaded."}
            else:
                raise ValueError(f"Unknown config manager task type: {task_type}")
            
            return TaskResponse(task_id=request.task_id, success=True, result=result).dict()

        except Exception as e:
            self.logger.error(f"Error executing config manager task {task_type}", error=str(e))
            return TaskResponse(task_id=request.task_id, success=False, error=str(e)).dict()

    async def _load_all_configurations(self):
        """Load all configurations from the database."""
        if not self.db_pool:
            self.logger.warning("Database pool not initialized. Cannot load configurations.")
            return
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT agent_name, config_data FROM agent_configurations")
                for row in rows:
                    self.configurations[row["agent_name"]] = row["config_data"]
                    self.last_config_update[row["agent_name"]] = time.time()
            self.logger.info(f"Loaded {len(self.configurations)} configurations from DB.")
        except Exception as e:
            self.logger.error(f"Failed to load configurations from DB: {e}")

    async def _set_configuration(self, agent_name: str, config_data: Dict[str, Any]):
        """Set and persist a configuration for a specific agent."""
        if not self.db_pool:
            self.logger.warning("Database pool not initialized. Cannot save configuration.")
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_configurations (agent_name, config_data)
                    VALUES ($1, $2)
                    ON CONFLICT (agent_name) DO UPDATE SET
                        config_data = EXCLUDED.config_data,
                        updated_at = CURRENT_TIMESTAMP
                """,
                agent_name,
                json.dumps(config_data)
                )
            self.configurations[agent_name] = config_data
            self.last_config_update[agent_name] = time.time()
            self.logger.info(f"Configuration for {agent_name} updated and persisted.")
            # Notify the agent about the update
            await self._publish(f"config.{agent_name}.updated", json.dumps(config_data).encode())
        except Exception as e:
            self.logger.error(f"Failed to set configuration for {agent_name}: {e}")

    async def _handle_get_config_request(self, msg):
        try:
            data = json.loads(msg.data.decode())
            agent_name = data["agent_name"]
            config = self.configurations.get(agent_name, {})
            await self._publish(msg.reply, json.dumps(config).encode())
            self.logger.debug(f"Sent config for {agent_name}")
        except Exception as e:
            self.logger.error(f"Error handling get config request: {e}")
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e)}).encode())

    async def _handle_set_config_request(self, msg):
        try:
            data = json.loads(msg.data.decode())
            agent_name = data["agent_name"]
            config_data = data["config_data"]
            await self._set_configuration(agent_name, config_data)
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"status": "success"}).encode())
        except Exception as e:
            self.logger.error(f"Error handling set config request: {e}")
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e)}).encode())

    async def _handle_reload_config_request(self, msg):
        try:
            await self._load_all_configurations()
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"status": "success", "message": "All configurations reloaded."}).encode())
        except Exception as e:
            self.logger.error(f"Error handling reload config request: {e}")
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e)}).encode())


if __name__ == "__main__":
    config = AgentConfig(
        name="config_manager",
        agent_type="utility",
        capabilities=["configuration_management"],
        nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://agent:secure_password@postgres:5432/ymera"),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )
    
    agent = ConfigManager(config)
    asyncio.run(agent.run())

