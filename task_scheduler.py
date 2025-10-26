"""
Task Scheduler
Schedules and manages task assignment to agents
"""

import structlog
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.utils.cache_manager import CacheManager
try:
    from models import Task as AgentTaskModel, TaskStatus
except ImportError:
    AgentTaskModel = None
    TaskStatus = None

logger = structlog.get_logger(__name__)


class TaskScheduler:
    """Schedules tasks for agents"""
    
    def __init__(self, db_session: AsyncSession, cache_manager: CacheManager, agent_manager):
        self.db = db_session
        self.cache = cache_manager
        self.agent_manager = agent_manager
    
    async def start(self):
        """Start the task scheduler"""
        logger.info("Task scheduler started")
    
    async def stop(self):
        """Stop the task scheduler"""
        logger.info("Task scheduler stopped")
    
    async def schedule_task(
        self,
        agent_id: str,
        task_type: str,
        task_data: Dict[str, Any],
        priority: int = 5,
        deadline: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Schedule a task for an agent"""
        try:
            task_id = str(uuid.uuid4())
            
            task = AgentTaskModel(
                task_id=task_id,
                agent_id=agent_id,
                task_type=task_type,
                status=TaskStatus.PENDING,
                priority=priority,
                task_data=task_data,
                created_at=datetime.utcnow(),
                deadline=deadline
            )
            
            self.db.add(task)
            await self.db.commit()
            
            logger.info("Task scheduled", task_id=task_id, agent_id=agent_id)
            
            return {
                "task_id": task_id,
                "status": "scheduled",
                "agent_id": agent_id,
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to schedule task", agent_id=agent_id, error=str(e))
            raise
    
    async def get_agent_tasks(
        self,
        agent_id: str,
        status: Optional[TaskStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get tasks for an agent"""
        try:
            query = select(AgentTaskModel).where(AgentTaskModel.agent_id == agent_id)
            
            if status:
                query = query.where(AgentTaskModel.status == status)
            
            result = await self.db.execute(query)
            tasks = result.scalars().all()
            
            return [
                {
                    "task_id": t.task_id,
                    "task_type": t.task_type,
                    "status": t.status,
                    "priority": t.priority,
                    "created_at": t.created_at.isoformat(),
                    "deadline": t.deadline.isoformat() if t.deadline else None
                }
                for t in tasks
            ]
            
        except Exception as e:
            logger.error("Failed to get agent tasks", agent_id=agent_id, error=str(e))
            return []
    
    async def cancel_agent_tasks(self, agent_id: str):
        """Cancel all active tasks for an agent"""
        try:
            stmt = select(AgentTaskModel).where(
                and_(
                    AgentTaskModel.agent_id == agent_id,
                    AgentTaskModel.status.in_([
                        TaskStatus.PENDING,
                        TaskStatus.ASSIGNED,
                        TaskStatus.IN_PROGRESS
                    ])
                )
            )
            result = await self.db.execute(stmt)
            tasks = result.scalars().all()
            
            for task in tasks:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.utcnow()
                task.error_data = {"reason": "Agent tasks cancelled"}
            
            await self.db.commit()
            
            logger.info(f"Cancelled {len(tasks)} tasks for agent {agent_id}")
            
        except Exception as e:
            logger.error("Failed to cancel agent tasks", agent_id=agent_id, error=str(e))
