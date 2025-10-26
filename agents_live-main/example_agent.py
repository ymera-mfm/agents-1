# example_agent.py - Example implementation of an agent

import asyncio
import logging
from agent_client import AgentClient, AgentStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def task_handler_example(parameters):
    """Example task handler"""
    logger.info(f"Executing task with parameters: {parameters}")
    
    # Simulate task work
    await asyncio.sleep(2)
    
    return {
        "status": "success",
        "output": "Task executed successfully",
        "processed_parameters": parameters
    }

async def main():
    """Main function"""
    # Create agent client
    agent = AgentClient(
        manager_url="https://manager.example.com",
        agent_id="example-agent-001",
        api_key="YOUR_API_KEY_HERE",
        cert_path="./certs/agent.crt",
        key_path="./certs/agent.key",
        ca_path="./certs/ca.crt"
    )
    
    # Register capabilities
    agent.register_capability("example.task", task_handler_example)
    agent.register_capability("example.analysis", task_handler_example)
    
    # Connect to manager
    if await agent.connect():
        logger.info("Agent connected successfully")
        
        # Keep agent running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            # Shutdown gracefully
            await agent.shutdown()
    else:
        logger.error("Failed to connect to manager")

if __name__ == "__main__":
    asyncio.run(main())