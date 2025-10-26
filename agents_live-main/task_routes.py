# api/task_routes.py
"""
API routes for task management and execution
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi import Query, Path, Body
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import uuid

from models import (
    Task, TaskCreate, TaskUpdate, TaskResponse, TaskStatus, TaskPriority,
    TaskResult, TaskQuery
)

from services import (
    auth_service, agent_manager, task_manager, audit_system
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user = Depends(auth_service.get_current_user)
):
    """Create a new task"""
    # Create task
    task = await task_manager.create_task({
        "name": task_data.name,
        "description": task_data.description,
        "task_type": task_data.task_type,
        "parameters": task_data.parameters,
        "priority": task_data.priority,
        "user_id": current_user.id,
        "agent_id": task_data.agent_id
    })
    
    # Log audit event
    background_tasks.add_task(
        audit_system.log_event,
        "task_creation",
        "task",
        task.id,
        "create",
        current_user.id,
        {"task_type": task.task_type, "priority": task.priority}
    )
    
    return task

@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[List[str]] = Query(None),
    agent_id: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = Query(100, gt=0, le=1000),
    offset: int = Query(0, ge=0),
    current_user = Depends(auth_service.get_current_user)
):
    """List user's tasks with filtering"""
    query = TaskQuery(
        status=status,
        agent_id=agent_id,
        task_type=task_type,
        limit=limit,
        offset=offset
    )
    return await task_manager.list_tasks(current_user.id, query)

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str = Path(...),
    current_user = Depends(auth_service.get_current_user)
):
    """Get task details"""
    task = await task_manager.get_task(task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str = Path(...),
    background_tasks: BackgroundTasks = None,
    current_user = Depends(auth_service.get_current_user)
):
    """Cancel a pending or running task"""
    task = await task_manager.cancel_task(task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Log audit event
    if background_tasks:
        background_tasks.add_task(
            audit_system.log_event,
            "task_cancellation",
            "task",
            task_id,
            "cancel",
            current_user.id,
            {"previous_status": task.previous_status}
        )
    
    return task

@router.post("/{task_id}/result", response_model=Dict[str, Any])
async def submit_task_result(
    task_id: str = Path(...),
    result: TaskResult = Body(...),
    current_agent = Depends(auth_service.get_current_agent)
):
    """Submit task result from agent"""
    # Process task result
    processed_result = await task_manager.handle_task_result(
        task_id, current_agent["id"], result.dict()
    )
    
    return processed_result

@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_task_stats(
    days: int = Query(7, ge=1, le=90),
    current_user = Depends(auth_service.get_current_user)
):
    """Get task statistics for user"""
    return await task_manager.get_task_statistics(current_user.id, days)

@router.post("/batch", response_model=Dict[str, Any])
async def create_batch_tasks(
    tasks: List[TaskCreate],
    background_tasks: BackgroundTasks,
    current_user = Depends(auth_service.get_current_user)
):
    """Create multiple tasks in batch"""
    result = await task_manager.create_batch_tasks(tasks, current_user.id)
    
    # Log audit event
    if background_tasks:
        background_tasks.add_task(
            audit_system.log_event,
            "task_batch_creation",
            "task",
            "batch",
            "create",
            current_user.id,
            {"count": len(tasks), "task_ids": result["task_ids"]}
        )
    
    return result