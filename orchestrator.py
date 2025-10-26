"""
Workflow Orchestrator
Manages agent workflow execution and output routing
"""

import structlog
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from shared.utils.message_broker import MessageBroker
except ImportError:
    MessageBroker = None

try:
    from core.sqlalchemy_models import Base as WorkflowExecutionModel
except ImportError:
    WorkflowExecutionModel = None

logger = structlog.get_logger(__name__)


class WorkflowOrchestrator:
    """Orchestrates workflows between agents"""
    
    def __init__(self, db_session: AsyncSession, message_broker: MessageBroker, agent_manager):
        self.db = db_session
        self.broker = message_broker
        self.agent_manager = agent_manager
        self.active_workflows = {}
    
    async def start(self):
        """Start the workflow orchestrator"""
        logger.info("Workflow orchestrator started")
    
    async def stop(self):
        """Stop the workflow orchestrator"""
        logger.info("Workflow orchestrator stopped")
    
    async def route_output(
        self,
        source_agent_id: str,
        target_agent_id: str,
        output_type: str,
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route output from one agent to another"""
        try:
            execution_id = str(uuid.uuid4())
            
            # Create workflow execution record
            execution = WorkflowExecutionModel(
                execution_id=execution_id,
                workflow_name=f"{output_type}_routing",
                source_agent_id=source_agent_id,
                target_agent_id=target_agent_id,
                status="in_progress",
                input_data=output_data,
                started_at=datetime.utcnow(),
                total_steps=1
            )
            
            self.db.add(execution)
            await self.db.commit()
            
            # Route through message broker
            await self.broker.publish(
                f"agent.{target_agent_id}.input",
                {
                    "routing_id": execution_id,
                    "source": source_agent_id,
                    "output_type": output_type,
                    "data": output_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info("Output routed",
                       routing_id=execution_id,
                       source=source_agent_id,
                       target=target_agent_id)
            
            return {
                "status": "routed",
                "routing_id": execution_id,
                "source": source_agent_id,
                "target": target_agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to route output", error=str(e))
            raise
    
    async def isolate_agent(self, agent_id: str):
        """Isolate an agent from workflows"""
        try:
            # Cancel all workflows involving this agent
            stmt = select(WorkflowExecutionModel).where(
                (WorkflowExecutionModel.source_agent_id == agent_id) |
                (WorkflowExecutionModel.target_agent_id == agent_id)
            ).where(WorkflowExecutionModel.status == "in_progress")
            
            result = await self.db.execute(stmt)
            workflows = result.scalars().all()
            
            for workflow in workflows:
                workflow.status = "cancelled"
                workflow.error_data = {"reason": "Agent isolated"}
                workflow.completed_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Agent {agent_id} isolated from {len(workflows)} workflows")
            
        except Exception as e:
            logger.error("Failed to isolate agent", agent_id=agent_id, error=str(e))
    
    async def remove_agent(self, agent_id: str):
        """Remove agent from workflow system"""
        await self.isolate_agent(agent_id)
        logger.info(f"Agent {agent_id} removed from workflow system")
