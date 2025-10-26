"""
Workflow Engine - Multi-step workflow orchestration
Supports DAG-based workflows, parallel execution, and dependency management
"""

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import structlog

try:
    from task_orchestrator import TaskOrchestrator, TaskRequest, TaskResult, TaskPriority, TaskStatus
except ImportError:
    # Define stubs if not available
    TaskOrchestrator = None
    TaskRequest = None
    TaskResult = None
    TaskPriority = None
    TaskStatus = None

logger = structlog.get_logger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(Enum):
    """Workflow step status"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Workflow step definition"""
    step_id: str
    step_name: str
    capability: str
    payload: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Step IDs this depends on
    timeout_seconds: int = 300
    retry_count: int = 3
    on_failure: str = "fail"  # fail, skip, retry
    condition: Optional[Callable] = None  # Optional condition to execute step
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """Workflow definition"""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_name: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_seconds: int = 3600
    on_failure: str = "fail"  # fail, continue, rollback
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate workflow definition"""
        # Check for circular dependencies
        visited = set()
        rec_stack = set()
        
        def has_cycle(step_id: str) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)
            
            step = next((s for s in self.steps if s.step_id == step_id), None)
            if not step:
                return False
            
            for dep in step.dependencies:
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(step_id)
            return False
        
        for step in self.steps:
            if step.step_id not in visited:
                if has_cycle(step.step_id):
                    logger.error(f"Circular dependency detected in workflow {self.workflow_id}")
                    return False
        
        return True


@dataclass
class StepExecution:
    """Step execution tracking"""
    step: WorkflowStep
    status: StepStatus = StepStatus.PENDING
    task_id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retries: int = 0


@dataclass
class WorkflowExecution:
    """Workflow execution tracking"""
    workflow_id: str
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    definition: WorkflowDefinition = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: Dict[str, StepExecution] = field(default_factory=dict)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WorkflowEngine:
    """
    Workflow Engine
    
    Features:
    - DAG-based workflow execution
    - Parallel step execution
    - Dependency management
    - Conditional execution
    - Rollback support
    - Workflow templates
    - State persistence
    """
    
    def __init__(self, task_orchestrator: TaskOrchestrator):
        self.orchestrator = task_orchestrator
        
        # Workflow tracking
        self._active_workflows: Dict[str, WorkflowExecution] = {}
        self._completed_workflows: Dict[str, WorkflowExecution] = {}
        self._workflow_templates: Dict[str, WorkflowDefinition] = {}
        
        # Locks
        self._lock = asyncio.Lock()
        
        # Background monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        logger.info("Workflow Engine initialized")
    
    async def start(self):
        """Start workflow engine"""
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Workflow Engine started")
    
    async def stop(self):
        """Stop workflow engine"""
        self._shutdown_event.set()
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            await asyncio.gather(self._monitoring_task, return_exceptions=True)
        
        logger.info("Workflow Engine stopped")
    
    # =========================================================================
    # TEMPLATE MANAGEMENT
    # =========================================================================
    
    async def register_template(self, definition: WorkflowDefinition):
        """Register workflow template"""
        if not definition.validate():
            raise ValueError(f"Invalid workflow definition: {definition.workflow_id}")
        
        async with self._lock:
            self._workflow_templates[definition.workflow_id] = definition
        
        logger.info(f"Workflow template registered", workflow_id=definition.workflow_id)
    
    async def get_template(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow template"""
        return self._workflow_templates.get(workflow_id)
    
    # =========================================================================
    # WORKFLOW EXECUTION
    # =========================================================================
    
    async def execute_workflow(
        self,
        definition: WorkflowDefinition,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Execute workflow
        
        Args:
            definition: Workflow definition
            context: Execution context/parameters
            
        Returns:
            Execution ID
        """
        if not definition.validate():
            raise ValueError(f"Invalid workflow definition: {definition.workflow_id}")
        
        # Create execution
        execution = WorkflowExecution(
            workflow_id=definition.workflow_id,
            definition=definition,
            status=WorkflowStatus.PENDING,
            started_at=time.time()
        )
        
        # Initialize step executions
        for step in definition.steps:
            execution.steps[step.step_id] = StepExecution(step=step)
        
        async with self._lock:
            self._active_workflows[execution.execution_id] = execution
        
        # Start execution in background
        asyncio.create_task(self._execute_workflow(execution, context or {}))
        
        logger.info(
            f"Workflow execution started",
            workflow_id=definition.workflow_id,
            execution_id=execution.execution_id
        )
        
        return execution.execution_id
    
    async def execute_template(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute workflow from template"""
        template = await self.get_template(workflow_id)
        if not template:
            raise ValueError(f"Workflow template not found: {workflow_id}")
        
        return await self.execute_workflow(template, context)
    
    async def _execute_workflow(
        self,
        execution: WorkflowExecution,
        context: Dict[str, Any]
    ):
        """Execute workflow steps"""
        try:
            execution.status = WorkflowStatus.RUNNING
            
            # Track completed and failed steps
            completed_steps = set()
            failed_steps = set()
            
            # Execute steps in dependency order
            while len(completed_steps) + len(failed_steps) < len(execution.steps):
                # Find ready steps
                ready_steps = []
                
                for step_id, step_exec in execution.steps.items():
                    if step_exec.status != StepStatus.PENDING:
                        continue
                    
                    # Check if dependencies are met
                    deps_met = all(
                        dep in completed_steps
                        for dep in step_exec.step.dependencies
                    )
                    
                    if deps_met:
                        # Check condition if present
                        if step_exec.step.condition:
                            try:
                                if not step_exec.step.condition(context):
                                    step_exec.status = StepStatus.SKIPPED
                                    completed_steps.add(step_id)
                                    continue
                            except Exception as e:
                                logger.error(f"Condition evaluation failed: {e}")
                                step_exec.status = StepStatus.FAILED
                                failed_steps.add(step_id)
                                continue
                        
                        step_exec.status = StepStatus.READY
                        ready_steps.append(step_id)
                
                if not ready_steps:
                    # No more ready steps - check for deadlock
                    if len(completed_steps) + len(failed_steps) < len(execution.steps):
                        logger.error("Workflow deadlock detected")
                        execution.status = WorkflowStatus.FAILED
                        execution.error = "Workflow deadlock - unmet dependencies"
                        break
                    else:
                        break
                
                # Execute ready steps in parallel
                tasks = []
                for step_id in ready_steps:
                    step_exec = execution.steps[step_id]
                    task = asyncio.create_task(
                        self._execute_step(execution, step_exec, context)
                    )
                    tasks.append((step_id, task))
                
                # Wait for all parallel steps to complete
                for step_id, task in tasks:
                    try:
                        success = await task
                        if success:
                            completed_steps.add(step_id)
                        else:
                            failed_steps.add(step_id)
                            
                            # Handle step failure
                            step_exec = execution.steps[step_id]
                            if step_exec.step.on_failure == "fail":
                                raise Exception(f"Step {step_id} failed")
                    except Exception as e:
                        failed_steps.add(step_id)
                        if execution.definition.on_failure == "fail":
                            raise
            
            # Workflow completed
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = time.time()
            
            # Collect results
            execution.result = {
                step_id: step_exec.result
                for step_id, step_exec in execution.steps.items()
                if step_exec.result is not None
            }
            
            logger.info(
                f"Workflow completed",
                workflow_id=execution.workflow_id,
                execution_id=execution.execution_id,
                duration_seconds=execution.completed_at - execution.started_at
            )
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = time.time()
            
            logger.error(
                f"Workflow failed",
                workflow_id=execution.workflow_id,
                execution_id=execution.execution_id,
                error=str(e)
            )
        
        finally:
            # Move to completed workflows
            async with self._lock:
                self._completed_workflows[execution.execution_id] = execution
                del self._active_workflows[execution.execution_id]
    
    async def _execute_step(
        self,
        execution: WorkflowExecution,
        step_exec: StepExecution,
        context: Dict[str, Any]
    ) -> bool:
        """Execute single workflow step"""
        step_exec.status = StepStatus.RUNNING
        step_exec.started_at = time.time()
        
        try:
            # Create task request
            task_request = TaskRequest(
                task_type=f"workflow_step_{step_exec.step.step_id}",
                capability=step_exec.step.capability,
                payload={
                    **step_exec.step.payload,
                    "workflow_context": context
                },
                priority=execution.definition.priority,
                timeout_seconds=step_exec.step.timeout_seconds,
                max_retries=step_exec.step.retry_count,
                metadata={
                    "workflow_id": execution.workflow_id,
                    "execution_id": execution.execution_id,
                    "step_id": step_exec.step.step_id
                }
            )
            
            # Submit to orchestrator
            step_exec.task_id = await self.orchestrator.submit_task(task_request)
            
            # Wait for completion
            while True:
                result = await self.orchestrator.get_task_result(step_exec.task_id)
                if result:
                    if result.status == TaskStatus.COMPLETED:
                        step_exec.status = StepStatus.COMPLETED
                        step_exec.result = result.result
                        step_exec.completed_at = time.time()
                        
                        # Update context with step result
                        context[f"step_{step_exec.step.step_id}_result"] = result.result
                        
                        logger.info(
                            f"Step completed",
                            step_id=step_exec.step.step_id,
                            workflow_id=execution.workflow_id
                        )
                        return True
                    
                    elif result.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED]:
                        step_exec.status = StepStatus.FAILED
                        step_exec.error = result.error
                        step_exec.completed_at = time.time()
                        
                        logger.error(
                            f"Step failed",
                            step_id=step_exec.step.step_id,
                            workflow_id=execution.workflow_id,
                            error=result.error
                        )
                        return False
                
                await asyncio.sleep(0.5)
        
        except Exception as e:
            step_exec.status = StepStatus.FAILED
            step_exec.error = str(e)
            step_exec.completed_at = time.time()
            
            logger.error(
                f"Step execution error",
                step_id=step_exec.step.step_id,
                error=str(e),
                exc_info=True
            )
            return False
    
    # =========================================================================
    # WORKFLOW CONTROL
    # =========================================================================
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel running workflow"""
        async with self._lock:
            if execution_id not in self._active_workflows:
                return False
            
            execution = self._active_workflows[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            
            # Cancel all running tasks
            for step_exec in execution.steps.values():
                if step_exec.status == StepStatus.RUNNING and step_exec.task_id:
                    await self.orchestrator.cancel_task(step_exec.task_id)
            
            logger.info(f"Workflow cancelled", execution_id=execution_id)
            return True
    
    async def pause_workflow(self, execution_id: str) -> bool:
        """Pause workflow execution"""
        # TODO: Implement pause functionality
        pass
    
    async def resume_workflow(self, execution_id: str) -> bool:
        """Resume paused workflow"""
        # TODO: Implement resume functionality
        pass
    
    # =========================================================================
    # QUERIES
    # =========================================================================
    
    async def get_workflow_status(self, execution_id: str) -> Optional[WorkflowStatus]:
        """Get workflow status"""
        if execution_id in self._active_workflows:
            return self._active_workflows[execution_id].status
        elif execution_id in self._completed_workflows:
            return self._completed_workflows[execution_id].status
        return None
    
    async def get_workflow_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution"""
        if execution_id in self._active_workflows:
            return self._active_workflows[execution_id]
        return self._completed_workflows.get(execution_id)
    
    async def get_active_workflows(self) -> List[str]:
        """Get list of active workflow execution IDs"""
        return list(self._active_workflows.keys())
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get workflow engine statistics"""
        return {
            'active_workflows': len(self._active_workflows),
            'completed_workflows': len(self._completed_workflows),
            'registered_templates': len(self._workflow_templates)
        }
    
    # =========================================================================
    # MONITORING
    # =========================================================================
    
    async def _monitoring_loop(self):
        """Monitor active workflows"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(30)
                
                # Check for timed out workflows
                current_time = time.time()
                timed_out = []
                
                for execution_id, execution in self._active_workflows.items():
                    if execution.started_at:
                        elapsed = current_time - execution.started_at
                        if elapsed > execution.definition.timeout_seconds:
                            timed_out.append(execution_id)
                
                for execution_id in timed_out:
                    await self.cancel_workflow(execution_id)
                    logger.warning(f"Workflow timed out", execution_id=execution_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
