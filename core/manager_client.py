
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from core.config import Settings

logger = logging.getLogger(__name__)

class ManagerClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.AsyncClient()
        self.manager_url = settings.manager_agent_url

    async def send_heartbeat(self, agent_id: str, status: str) -> bool:
        if not self.manager_url:
            logger.warning("Manager Agent URL not configured. Skipping heartbeat.")
            return False
        
        try:
            response = await self.client.post(
                f"{self.manager_url}/agents/{agent_id}/heartbeat",
                json={
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            response.raise_for_status()
            logger.info(f"Heartbeat sent to Manager Agent for agent {agent_id}. Status: {status}")
            return True
        except httpx.RequestError as e:
            logger.error(f"Error sending heartbeat to Manager Agent: {e}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"Manager Agent returned error for heartbeat: {e.response.status_code} - {e.response.text}")
            return False

    async def register_agent(self, agent_data: Dict[str, Any]) -> Optional[str]:
        if not self.manager_url:
            logger.warning("Manager Agent URL not configured. Skipping agent registration.")
            return None
        
        try:
            response = await self.client.post(
                f"{self.manager_url}/agents",
                json=agent_data
            )
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"Agent registered with Manager Agent. ID: {response_data.get('agent_id')}")
            return response_data.get('agent_id')
        except httpx.RequestError as e:
            logger.error(f"Error registering agent with Manager Agent: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Manager Agent returned error for agent registration: {e.response.status_code} - {e.response.text}")
            return None

    async def shutdown(self):
        await self.client.aclose()

