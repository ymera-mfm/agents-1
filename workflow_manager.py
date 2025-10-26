# workflow_manager.py - Complete workflow management system
"""
Comprehensive workflow management system with distribution, prioritization,
step validation, and advanced execution monitoring
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass
import networkx as nx
from async_timeout import timeout

from models import Task, Agent, User, Workflow, WorkflowExecution, WorkflowStep, StepExecution
from security.rbac_manager import Permission, require_permission

logger = logging.getLogger(__name__)

class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    PAUSED = "paused"

class StepStatus(str, Enum):
    """Workflow step execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class StepType(str, Enum):
    """Types of workflow steps"""
    AGENT_TASK = "agent_task"
    APPROVAL = "approval"
    CONDITION = "condition"
    NOTIFICATION = "notification"
    WAIT = "wait"
    PARALLEL = "parallel"
    LOOP = "loop"
    EXTERNAL_API = "external_api"
    SCRIPT = "script"
    DECISION = "decision"

class WorkflowPriority(str, Enum):
    """Workflow priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

@dataclass
class WorkflowMetrics:
    """Workflow execution metrics"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0  # seconds
    longest_execution_time: float = 0  # seconds
    shortest_execution_time: float = 0  # seconds

class WorkflowManager:
    """
    Comprehensive workflow management system with distribution,
    monitoring, and execution
    """
    
    def __init__(self, db_manager, task_queue, agent_manager, 
                 notification_manager, analytics_engine, cache_manager):
        self.db_manager = db_manager
        self.task_queue = task_queue
        self.agent_manager = agent_manager
        self.notification_manager = notification_manager
        self.analytics_engine = analytics_engine
        self.cache_manager = cache_manager
        
        self.active_executions = {}
        self.workflow_registry = {}
        self.execution_monitors = set()
        self.metrics = {}  # workflow_id -> WorkflowMetrics
        
        # Workflow hooks
        self.pre_execution_hooks = []
        self.post_execution_hooks = []
        self.step_completion_hooks = []
        self.error_hooks = []
        
        logger.info("WorkflowManager initialized")
    
    async def register_workflow(self, workflow_def: Dict) -> str:
        """
        Register a new workflow definition
        """
        async with self.db_manager.get_session() as session:
            # Validate workflow DAG structure
            valid, error = self._validate_workflow_dag(workflow_def)
            if not valid:
                raise ValueError(f"Invalid workflow structure: {error}")
            
            # Create workflow record
            workflow = Workflow(
                id=workflow_def.get("id", str(uuid.uuid4())),
                name=workflow_def["name"],
                description=workflow_def.get("description", ""),
                version=workflow_def.get("version", "1.0.0"),
                tenant_id=workflow_def["tenant_id"],
                creator_id=workflow_def["creator_id"],
                definition=workflow_def,
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(workflow)
            await session.commit()
            
            # Cache workflow definition
            await self.cache_manager.set(
                f"workflow:{workflow.id}", 
                workflow.definition,
                ttl=3600
            )
            
            # Register in local registry
            self.workflow_registry[workflow.id] = workflow_def
            
            # Initialize metrics
            self.metrics[workflow.id] = WorkflowMetrics()
            
            return workflow.id
    
    async def start_workflow(self, workflow_id: str, parameters: Dict = None,
                           initiator_id: str = None, priority: WorkflowPriority = None) -> Dict:
        """
        Start a workflow execution
        """
        # Get workflow definition
        workflow_def = await self._get_workflow_definition(workflow_id)
        if not workflow_def:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Create execution record
        execution_id = str(uuid.uuid4())
        
        async with self.db_manager.get_session() as session:
            execution = WorkflowExecution(
                id=execution_id,
                workflow_id=workflow_id,
                status=WorkflowStatus.PENDING,
                parameters=parameters or {},
                initiator_id=initiator_id,
                tenant_id=workflow_def["tenant_id"],
                priority=priority or workflow_def.get("priority", WorkflowPriority.NORMAL),
                started_at=datetime.utcnow(),
                current_step=workflow_def.get("start_step")
            )
            
            session.add(execution)
            await session.commit()
        
        # Run pre-execution hooks
        for hook in self.pre_execution_hooks:
            try:
                await hook(execution_id, workflow_id, parameters)
            except Exception as e:
                logger.error(f"Pre-execution hook error: {e}")
        
        # Start background execution
        asyncio.create_task(self._execute_workflow(execution_id, workflow_def, parameters))
        
        # Update metrics
        if workflow_id in self.metrics:
            self.metrics[workflow_id].total_executions += 1
        
        return {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "status": WorkflowStatus.PENDING
        }
    
    async def _execute_workflow(self, execution_id: str, workflow_def: Dict, parameters: Dict):
        """
        Execute workflow steps
        """
        start_time = datetime.utcnow()
        self.active_executions[execution_id] = {
            "workflow_id": workflow_def["id"],
            "status": WorkflowStatus.RUNNING,
            "steps": {},
            "current_step": workflow_def.get("start_step"),
            "parameters": parameters,
            "context": {},
            "errors": []
        }
        
        try:
            # Update status to running
            await self._update_execution_status(execution_id, WorkflowStatus.RUNNING)
            
            # Start execution from first step
            current_step = workflow_def.get("start_step")
            result = await self._execute_workflow_step(
                execution_id, workflow_def, current_step, parameters
            )
            
            # Check final status
            final_status = WorkflowStatus.COMPLETED if result["success"] else WorkflowStatus.FAILED
            
            # Update execution record with results
            await self._update_execution_completion(execution_id, final_status, result)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update metrics
            workflow_id = workflow_def["id"]
            if workflow_id in self.metrics:
                metrics = self.metrics[workflow_id]
                if final_status == WorkflowStatus.COMPLETED:
                    metrics.successful_executions += 1
                else:
                    metrics.failed_executions += 1
                
                # Update execution time stats
                n = metrics.successful_executions + metrics.failed_executions
                metrics.average_execution_time = ((metrics.average_execution_time * (n - 1)) + execution_time) / n
                metrics.longest_execution_time = max(metrics.longest_execution_time, execution_time)
                if metrics.shortest_execution_time == 0 or execution_time < metrics.shortest_execution_time:
                    metrics.shortest_execution_time = execution_time
            
            # Run post-execution hooks
            for hook in self.post_execution_hooks:
                try:
                    await hook(execution_id, workflow_id, final_status, result)
                except Exception as e:
                    logger.error(f"Post-execution hook error: {e}")
            
            # Clean up active execution
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            
            # Update status to failed
            await self._update_execution_status(execution_id, WorkflowStatus.FAILED, str(e))
            
            # Run error hooks
            for hook in self.error_hooks:
                try:
                    await hook(execution_id, workflow_def["id"], str(e))
                except Exception as hook_error:
                    logger.error(f"Error hook failed: {hook_error}")
            
            # Clean up
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    async def _execute_workflow_step(self, execution_id: str, workflow_def: Dict, 
                                  step_id: str, parameters: Dict) -> Dict:
        """
        Execute a single workflow step
        """
        if step_id is None or step_id not in workflow_def.get("steps", {}):
            return {"success": False, "error": f"Invalid step ID: {step_id}"}
        
        step_def = workflow_def["steps"][step_id]
        step_type = step_def.get("type", StepType.AGENT_TASK)
        step_execution_id = str(uuid.uuid4())
        
        # Update active execution
        self.active_executions[execution_id]["current_step"] = step_id
        self.active_executions[execution_id]["steps"][step_id] = {
            "status": StepStatus.RUNNING,
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Create step execution record
        await self._create_step_execution(
            step_execution_id, execution_id, step_id, step_def
        )
        
        try:
            # Execute based on step type
            if step_type == StepType.AGENT_TASK:
                result = await self._execute_agent_task(execution_id, step_def, parameters)
            elif step_type == StepType.APPROVAL:
                result = await self._execute_approval_step(execution_id, step_def, parameters)
            elif step_type == StepType.CONDITION:
                result = await self._execute_condition_step(execution_id, step_def, parameters)
            elif step_type == StepType.NOTIFICATION:
                result = await self._execute_notification_step(execution_id, step_def, parameters)
            elif step_type == StepType.WAIT:
                result = await self._execute_wait_step(execution_id, step_def, parameters)
            elif step_type == StepType.PARALLEL:
                result = await self._execute_parallel_step(execution_id, step_def, parameters)
            elif step_type == StepType.EXTERNAL_API:
                result = await self._execute_external_api_step(execution_id, step_def, parameters)
            elif step_type == StepType.SCRIPT:
                result = await self._execute_script_step(execution_id, step_def, parameters)
            elif step_type == StepType.DECISION:
                result = await self._execute_decision_step(execution_id, step_def, parameters)
            else:
                result = {"success": False, "error": f"Unsupported step type: {step_type}"}
            
            # Update step status
            step_status = StepStatus.COMPLETED if result["success"] else StepStatus.FAILED
            await self._update_step_status(step_execution_id, step_status, result)
            
            # Update active execution
            self.active_executions[execution_id]["steps"][step_id].update({
                "status": step_status,
                "completed_at": datetime.utcnow().isoformat(),
                "result": result
            })
            
            # Run step completion hooks
            for hook in self.step_completion_hooks:
                try:
                    await hook(execution_id, step_id, step_status, result)
                except Exception as e:
                    logger.error(f"Step completion hook error: {e}")
            
            # Continue to next step if successful
            if result["success"]:
                next_step = self._determine_next_step(workflow_def, step_def, result, parameters)
                
                if next_step:
                    return await self._execute_workflow_step(
                        execution_id, workflow_def, next_step, parameters
                    )
                else:
                    # Workflow completed successfully
                    return {"success": True, "message": "Workflow completed successfully"}
            
            return result
            
        except Exception as e:
            logger.error(f"Step execution error in {step_id}: {e}")
            
            # Update step status
            await self._update_step_status(
                step_execution_id, StepStatus.FAILED, {"error": str(e)}
            )
            
            # Update active execution
            self.active_executions[execution_id]["steps"][step_id].update({
                "status": StepStatus.FAILED,
                "completed_at": datetime.utcnow().isoformat(),
                "error": str(e)
            })
            
            return {"success": False, "error": str(e)}
    
    async def _execute_agent_task(self, execution_id: str, step_def: Dict, parameters: Dict) -> Dict:
        """Execute task assigned to an agent"""
        try:
            # Extract task parameters
            task_params = self._extract_parameters(step_def.get("parameters", {}), parameters)
            
            # Find appropriate agent
            agent_id = await self._select_agent_for_task(
                step_def.get("agent_type"), 
                step_def.get("agent_id"),
                step_def.get("agent_capabilities", [])
            )
            
            if not agent_id:
                return {"success": False, "error": "No suitable agent found for task"}
            
            # Create task
            task_data = {
                "type": step_def.get("task_type", "default"),
                "parameters": task_params,
                "workflow_execution_id": execution_id,
                "step_id": step_def.get("id"),
                "priority": step_def.get("priority", "normal"),
                "timeout_seconds": step_def.get("timeout_seconds", 300)
            }
            
            # Queue task and wait for result
            result = await self._queue_and_wait_for_task(agent_id, task_data)
            
            # Process result
            if result.get("status") == "completed":
                return {
                    "success": True,
                    "result": result.get("result", {}),
                    "agent_id": agent_id
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Task execution failed"),
                    "agent_id": agent_id
                }
                
        except asyncio.TimeoutError:
            return {"success": False, "error": "Task execution timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_approval_step(self, execution_id: str, step_def: Dict, parameters: Dict) -> Dict:
        """Execute approval step"""
        try:
            # Create approval request
            approver_ids = step_def.get("approvers", [])
            approval_groups = step_def.get("approval_groups", [])
            
            # Determine final approvers list
            final_approvers = await self._resolve_approvers(approver_ids, approval_groups)
            
            if not final_approvers:
                return {"success": False, "error": "No approvers configured"}
            
            approval_request = {
                "workflow_execution_id": execution_id,
                "step_id": step_def.get("id"),
                "title": self._extract_value(step_def.get("title", "Approval Required"), parameters),
                "description": self._extract_value(step_def.get("description", ""), parameters),
                "approvers": final_approvers,
                "min_approvals": step_def.get("min_approvals", len(final_approvers)),
                "expiry_hours": step_def.get("expiry_hours", 24),
                "parameters": parameters,
                "created_at": datetime.utcnow()
            }
            
            # Store approval request
            request_id = await self._create_approval_request(approval_request)
            
            # Notify approvers
            await self._notify_approvers(request_id, final_approvers, approval_request)
            
            # Wait for approval result (with timeout)
            timeout_seconds = step_def.get("timeout_seconds", 3600 * approval_request["expiry_hours"])
            
            try:
                async with timeout(timeout_seconds):
                    result = await self._wait_for_approval_result(request_id)
                    
                    return {
                        "success": result["approved"],
                        "request_id": request_id,
                        "result": result
                    }
                    
            except asyncio.TimeoutError:
                # Handle timeout - check if default action is specified
                default_action = step_def.get("timeout_action", "reject")
                
                await self._update_approval_request(request_id, {
                    "status": "expired",
                    "updated_at": datetime.utcnow()
                })
                
                return {
                    "success": default_action == "approve",
                    "request_id": request_id,
                    "result": {
                        "approved": default_action == "approve",
                        "reason": "Approval request expired",
                        "expired": True
                    }
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_condition_step(self, execution_id: str, step_def: Dict, parameters: Dict) -> Dict:
        """Execute conditional step"""
        try:
            # Extract condition parameters
            condition_params = self._extract_parameters(step_def.get("condition_parameters", {}), parameters)
            condition_type = step_def.get("condition_type", "expression")
            
            # Evaluate condition
            if condition_type == "expression":
                # Simple expression evaluation
                condition_result = await self._evaluate_condition_expression(
                    step_def.get("condition"), parameters
                )
            elif condition_type == "script":
                # Custom script evaluation
                condition_result = await self._evaluate_condition_script(
                    step_def.get("condition_script"), condition_params
                )
            else:
                return {"success": False, "error": f"Unsupported condition type: {condition_type}"}
            
            # Store condition result in workflow context
            self.active_executions[execution_id]["context"]["conditions"] = {
                **(self.active_executions[execution_id]["context"].get("conditions", {})),
                step_def.get("id"): condition_result
            }
            
            return {
                "success": True,
                "condition_result": condition_result,
                "next_step": "true_step" if condition_result else "false_step"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Condition evaluation failed: {str(e)}"}
    
    async def _execute_notification_step(self, execution_id: str, step_def: Dict, parameters: Dict) -> Dict:
        """Execute notification step"""
        try:
            # Extract notification parameters
            notification_params = self._extract_parameters(step_def.get("notification_parameters", {}), parameters)
            
            # Get recipients
            recipients = step_def.get("recipients", [])
            recipient_groups = step_def.get("recipient_groups", [])
            
            # Resolve final recipients
            final_recipients = await self._resolve_recipients(recipients, recipient_groups)
            
            if not final_recipients:
                return {"success": False, "error": "No notification recipients configured"}
            
            # Prepare notification
            notification = {
                "workflow_execution_id": execution_id,
                "step_id": step_def.get("id"),
                "title": self._extract_value(step_def.get("title", "Workflow Notification"), parameters),
                "message": self._extract_value(step_def.get("message", ""), parameters),
                "recipients": final_recipients,
                "channels": step_def.get("channels", ["email"]),
                "priority": step_def.get("priority", "normal"),
                "parameters": notification_params,
                "created_at": datetime.utcnow()
            }
            
            # Send notification
            results = await self.notification_manager.send_notification_to_many(
                final_recipients, notification
            )
            
            # Check if critical notification must succeed
            if step_def.get("critical", False) and not all(r.get("success") for r in results):
                failed_count = sum(1 for r in results if not r.get("success"))
                return {
                    "success": False,
                    "error": f"Failed to send {failed_count} critical notifications",
                    "results": results
                }
            
            return {
                "success": True,
                "notification_count": len(results),
                "success_count": sum(1 for r in results if r.get("success")),
                "results": results
            }
            
        except Exception as e:
            return {"success": False, "error": f"Notification failed: {str(e)}"}
    
    async def _execute_wait_step(self, execution_id: str, step_def: Dict, parameters: Dict) -> Dict:
        """Execute wait step"""
        try:
            # Determine wait time
            wait_seconds = self._extract_value(step_def.get("wait_seconds", 60), parameters)
            
            # Wait
            await asyncio.sleep(float(wait_seconds))
            
            return {"success": True, "waited_seconds": wait_seconds}
            
        except Exception as e:
            return {"success": False, "error": f"Wait failed: {str(e)}"}
    
    async def _execute_parallel_step(self, execution_id: str, step_def: Dict, parameters: Dict) -> Dict:
        """Execute parallel steps"""
        try:
            # Get parallel branches
            branches = step_def.get("branches", [])
            
            if not branches:
                return {"success": False, "error": "No parallel branches configured"}
            
            # Execute all branches in parallel
            branch_tasks = []
            for i, branch in enumerate(branches):
                branch_id = branch.get("id", f"branch_{i}")
                branch_step = branch.get("start_step")
                branch_parameters = self._extract_parameters(
                    branch.get("parameters", {}), parameters
                )
                
                # Combine parameters
                combined_params = {**parameters, **branch_parameters}
                
                # Create task for branch execution
                branch_tasks.append(
                    self._execute_workflow_step(
                        execution_id, 
                        workflow_def={"steps": step_def.get("steps", {}), "id": step_def.get("id")},
                        step_id=branch_step,
                        parameters=combined_params
                    )
                )
            
            # Wait for all branches to complete
            branch_results = await asyncio.gather(*branch_tasks, return_exceptions=True)
            
            # Process results
            success_count = 0
            results = {}
            
            for i, result in enumerate(branch_results):
                branch_id = branches[i].get("id", f"branch_{i}")
                
                if isinstance(result, Exception):
                    results[branch_id] = {
                        "success": False,
                        "error": str(result)
                    }
                else:
                    results[branch_id] = result
                    if result.get("success", False):
                        success_count += 1
            
            # Determine overall success based on join condition
            join_condition = step_def.get("join_condition", "all")
            
            if join_condition == "all":
                success = success_count == len(branches)
            elif join_condition == "any":
                success = success_count > 0
            else:
                # Custom threshold
                try:
                    threshold = int(join_condition)
                    success = success_count >= threshold
                except ValueError:
                    success = False
                    results["error"] = f"Invalid join condition: {join_condition}"
            
            return {
                "success": success,
                "branch_results": results,
                "success_count": success_count,
                "total_branches": len(branches)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Parallel execution failed: {str(e)}"}
    
    async def _execute_external_api_step(self, execution_id: str, step_def: Dict, parameters: Dict) -> Dict:
        """Execute external API step"""
        try:
            # Extract API parameters
            api_params = self._extract_parameters(step_def.get("api_parameters", {}), parameters)
            
            # Get API configuration
            api_url = self._extract_value(step_def.get("api_url"), parameters)
            api_method = step_def.get("api_method", "GET")
            api_headers = self._extract_parameters(step_def.get("api_headers", {}), parameters)
            api_timeout = step_def.get("timeout_seconds", 60)
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.request(
                        method=api_method,
                        url=api_url,
                        headers=api_headers,
                        json=api_params if api_method in ["POST", "PUT", "PATCH"] else None,
                        params=api_params if api_method == "GET" else None,
                        timeout=api_timeout
                    ) as response:
                        response_status = response.status
                        
                        try:
                            response_data = await response.json()
                        except:
                            response_data = await response.text()
                        
                        # Check for success based on expected status code
                        expected_status = step_def.get("expected_status_code", 200)
                        success = response_status == expected_status
                        
                        return {
                            "success": success,
                            "status_code": response_status,
                            "response": response_data,
                            "headers": dict(response.headers)
                        }
                        
                except asyncio.TimeoutError:
                    return {
                        "success": False,
                        "error": f"API request timed out after {api_timeout} seconds"
                    }
                    
        except Exception as e:
            return {"success": False, "error": f"External API request failed: {str(e)}"}
    
    async def _execute_script_step(self, execution_id: str, step_def: Dict, parameters: Dict) -> Dict:
        """Execute script step with sandboxing"""
        try:
            # Extract script parameters
            script_params = self._extract_parameters(step_def.get("script_parameters", {}), parameters)
            
            # Get script content and type
            script_content = step_def.get("script_content")
            script_type = step_def.get("script_type", "python")
            
            if not script_content:
                return {"success": False, "error": "No script content provided"}
            
            # Execute script in sandbox
            script_context = {
                "parameters": script_params,
                "execution_id": execution_id,
                "workflow_context": self.active_executions[execution_id]["context"],
                "step_id": step_def.get("id")
            }
            
            result = await self._execute_script_in_sandbox(
                script_content, script_type, script_context
            )
            
            return result
            
        except Exception as e:
            return {"success": False, "error": f"Script execution failed: {str(e)}"}
    
    async def _execute_decision_step(self, execution_id: str, step_def: Dict, parameters: Dict) -> Dict:
        """Execute decision step with multiple paths"""
        try:
            decisions = step_def.get("decisions", [])
            
            if not decisions:
                return {"success": False, "error": "No decisions configured"}
            
            # Evaluate each decision condition in order
            for decision in decisions:
                condition = decision.get("condition")
                condition_result = await self._evaluate_condition_expression(condition, parameters)
                
                if condition_result:
                    # First matching condition wins
                    return {
                        "success": True,
                        "decision_result": decision.get("id"),
                        "next_step": decision.get("next_step"),
                        "description": decision.get("description", "")
                    }
            
            # If no condition matches, use default
            default = step_def.get("default")
            if default:
                return {
                    "success": True,
                    "decision_result": "default",
                    "next_step": default.get("next_step"),
                    "description": default.get("description", "Default path")
                }
            
            # No decision matched and no default
            return {"success": False, "error": "No decision condition matched and no default provided"}
            
        except Exception as e:
            return {"success": False, "error": f"Decision step failed: {str(e)}"}
    
    async def pause_workflow(self, execution_id: str, reason: str = None) -> Dict:
        """
        Pause a running workflow
        """
        if execution_id not in self.active_executions:
            raise ValueError(f"Workflow execution {execution_id} not active")
        
        self.active_executions[execution_id]["status"] = WorkflowStatus.PAUSED
        self.active_executions[execution_id]["paused_at"] = datetime.utcnow().isoformat()
        self.active_executions[execution_id]["pause_reason"] = reason
        
        await self._update_execution_status(execution_id, WorkflowStatus.PAUSED, reason)
        
        return {
            "execution_id": execution_id,
            "status": WorkflowStatus.PAUSED,
            "paused_at": datetime.utcnow().isoformat(),
            "reason": reason
        }
    
    async def resume_workflow(self, execution_id: str) -> Dict:
        """
        Resume a paused workflow
        """
        if execution_id not in self.active_executions:
            raise ValueError(f"Workflow execution {execution_id} not active")
        
        if self.active_executions[execution_id]["status"] != WorkflowStatus.PAUSED:
            raise ValueError(f"Workflow execution {execution_id} is not paused")
        
        # Get current step and workflow definition
        current_step = self.active_executions[execution_id]["current_step"]
        workflow_id = self.active_executions[execution_id]["workflow_id"]
        parameters = self.active_executions[execution_id]["parameters"]
        
        workflow_def = await self._get_workflow_definition(workflow_id)
        if not workflow_def:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Update status
        self.active_executions[execution_id]["status"] = WorkflowStatus.RUNNING
        self.active_executions[execution_id]["resumed_at"] = datetime.utcnow().isoformat()
        
        await self._update_execution_status(execution_id, WorkflowStatus.RUNNING)
        
        # Continue execution from current step
        asyncio.create_task(self._execute_workflow_step(
            execution_id, workflow_def, current_step, parameters
        ))
        
        return {
            "execution_id": execution_id,
            "status": WorkflowStatus.RUNNING,
            "resumed_at": datetime.utcnow().isoformat(),
            "current_step": current_step
        }
    
    async def cancel_workflow(self, execution_id: str, reason: str = None) -> Dict:
        """
        Cancel a running workflow
        """
        if execution_id not in self.active_executions:
            raise ValueError(f"Workflow execution {execution_id} not active")
        
        # Update status
        self.active_executions[execution_id]["status"] = WorkflowStatus.CANCELED
        self.active_executions[execution_id]["canceled_at"] = datetime.utcnow().isoformat()
        self.active_executions[execution_id]["cancel_reason"] = reason
        
        await self._update_execution_status(execution_id, WorkflowStatus.CANCELED, reason)
        
        # Clean up
        del self.active_executions[execution_id]
        
        return {
            "execution_id": execution_id,
            "status": WorkflowStatus.CANCELED,
            "canceled_at": datetime.utcnow().isoformat(),
            "reason": reason
        }
    
    async def get_workflow_status(self, execution_id: str) -> Dict:
        """
        Get workflow execution status and details
        """
        if execution_id in self.active_executions:
            # Active workflow
            return {
                "execution_id": execution_id,
                "workflow_id": self.active_executions[execution_id]["workflow_id"],
                "status": self.active_executions[execution_id]["status"],
                "current_step": self.active_executions[execution_id]["current_step"],
                "steps": self.active_executions[execution_id]["steps"],
                "active": True
            }
        
        # Check database for completed workflow
        async with self.db_manager.get_session() as session:
            execution = await session.get(WorkflowExecution, execution_id)
            
            if not execution:
                raise ValueError(f"Workflow execution {execution_id} not found")
            
            # Get step executions
            steps_result = await session.execute(
                select(StepExecution).where(StepExecution.execution_id == execution_id)
            )
            steps = steps_result.scalars().all()
            
            return {
                "execution_id": execution_id,
                "workflow_id": execution.workflow_id,
                "status": execution.status,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "parameters": execution.parameters,
                "result": execution.result,
                "steps": {
                    step.step_id: {
                        "status": step.status,
                        "started_at": step.started_at.isoformat() if step.started_at else None,
                        "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                        "result": step.result
                    }
                    for step in steps
                },
                "active": False
            }
    
    async def get_workflow_metrics(self, workflow_id: str = None) -> Dict:
        """
        Get workflow execution metrics
        """
        if workflow_id:
            # Get metrics for specific workflow
            if workflow_id in self.metrics:
                metrics = self.metrics[workflow_id]
                return {
                    "workflow_id": workflow_id,
                    "total_executions": metrics.total_executions,
                    "successful_executions": metrics.successful_executions,
                    "failed_executions": metrics.failed_executions,
                    "success_rate": metrics.successful_executions / max(metrics.total_executions, 1),
                    "average_execution_time": metrics.average_execution_time,
                    "longest_execution_time": metrics.longest_execution_time,
                    "shortest_execution_time": metrics.shortest_execution_time
                }
            else:
                raise ValueError(f"Workflow {workflow_id} not found in metrics")
        else:
            # Get aggregated metrics for all workflows
            total = 0
            successful = 0
            failed = 0
            exec_times = []
            
            for wf_id, metrics in self.metrics.items():
                total += metrics.total_executions
                successful += metrics.successful_executions
                failed += metrics.failed_executions
                
                if metrics.average_execution_time > 0:
                    exec_times.append(metrics.average_execution_time)
            
            return {
                "total_workflows": len(self.metrics),
                "total_executions": total,
                "successful_executions": successful,
                "failed_executions": failed,
                "success_rate": successful / max(total, 1),
                "average_execution_time": sum(exec_times) / max(len(exec_times), 1) if exec_times else 0,
                "active_executions": len(self.active_executions)
            }
    
    def register_hook(self, hook_type: str, hook_function: Callable) -> None:
        """
        Register a hook function for workflow events
        """
        if hook_type == "pre_execution":
            self.pre_execution_hooks.append(hook_function)
        elif hook_type == "post_execution":
            self.post_execution_hooks.append(hook_function)
        elif hook_type == "step_completion":
            self.step_completion_hooks.append(hook_function)
        elif hook_type == "error":
            self.error_hooks.append(hook_function)
        else:
            raise ValueError(f"Invalid hook type: {hook_type}")
    
    # Helper methods
    
    def _validate_workflow_dag(self, workflow_def: Dict) -> Tuple[bool, Optional[str]]:
        """Validate workflow DAG structure"""
        try:
            steps = workflow_def.get("steps", {})
            if not steps:
                return False, "No steps defined in workflow"
            
            # Create graph
            G = nx.DiGraph()
            
            # Add all steps as nodes
            for step_id in steps:
                G.add_node(step_id)
            
            # Add edges based on next steps
            for step_id, step in steps.items():
                if step.get("type") == StepType.CONDITION:
                    # Add both true and false paths
                    true_step = step.get("true_step")
                    false_step = step.get("false_step")
                    
                    if true_step:
                        if true_step not in steps:
                            return False, f"True step '{true_step}' not defined"
                        G.add_edge(step_id, true_step)
                    
                    if false_step:
                        if false_step not in steps:
                            return False, f"False step '{false_step}' not defined"
                        G.add_edge(step_id, false_step)
                
                elif step.get("type") == StepType.DECISION:
                    # Add all decision paths
                    for decision in step.get("decisions", []):
                        next_step = decision.get("next_step")
                        if next_step:
                            if next_step not in steps:
                                return False, f"Decision step '{next_step}' not defined"
                            G.add_edge(step_id, next_step)
                    
                    # Add default path
                    default = step.get("default")
                    if default:
                        default_step = default.get("next_step")
                        if default_step:
                            if default_step not in steps:
                                return False, f"Default step '{default_step}' not defined"
                            G.add_edge(step_id, default_step)
                
                else:
                    # Regular next step
                    next_step = step.get("next_step")
                    if next_step:
                        if next_step not in steps:
                            return False, f"Next step '{next_step}' not defined"
                        G.add_edge(step_id, next_step)
            
            # Check for cycles
            if not nx.is_directed_acyclic_graph(G):
                return False, "Workflow contains cycles"
            
            # Check for unreachable steps
            start_step = workflow_def.get("start_step")
            if start_step not in steps:
                return False, f"Start step '{start_step}' not defined"
            
            reachable = nx.descendants(G, start_step)
            reachable.add(start_step)
            
            unreachable = set(steps.keys()) - reachable
            if unreachable:
                return False, f"Unreachable steps: {', '.join(unreachable)}"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    async def _get_workflow_definition(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow definition from cache or database"""
        # Try cache first
        cached = await self.cache_manager.get(f"workflow:{workflow_id}")
        if cached:
            return cached
        
        # Get from database
        async with self.db_manager.get_session() as session:
            workflow = await session.get(Workflow, workflow_id)
            
            if workflow:
                # Cache for future use
                await self.cache_manager.set(
                    f"workflow:{workflow_id}", 
                    workflow.definition,
                    ttl=3600
                )
                return workflow.definition
        
        return None
    
    async def _update_execution_status(self, execution_id: str, status: WorkflowStatus, message: str = None):
        """Update workflow execution status"""
        async with self.db_manager.get_session() as session:
            execution = await session.get(WorkflowExecution, execution_id)
            
            if execution:
                execution.status = status
                
                if status == WorkflowStatus.RUNNING:
                    if not execution.started_at:
                        execution.started_at = datetime.utcnow()
                
                if status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELED]:
                    execution.completed_at = datetime.utcnow()
                
                if message:
                    execution.message = message
                
                await session.commit()
    
    async def _update_execution_completion(self, execution_id: str, status: WorkflowStatus, result: Dict):
        """Update workflow execution with final results"""
        async with self.db_manager.get_session() as session:
            execution = await session.get(WorkflowExecution, execution_id)
            
            if execution:
                execution.status = status
                execution.completed_at = datetime.utcnow()
                execution.result = result
                
                await session.commit()
    
    async def _create_step_execution(self, step_execution_id: str, execution_id: str, 
                                  step_id: str, step_def: Dict):
        """Create step execution record"""
        async with self.db_manager.get_session() as session:
            step_execution = StepExecution(
                id=step_execution_id,
                execution_id=execution_id,
                step_id=step_id,
                step_type=step_def.get("type", StepType.AGENT_TASK),
                status=StepStatus.RUNNING,
                started_at=datetime.utcnow(),
                parameters=step_def.get("parameters", {})
            )
            
            session.add(step_execution)
            await session.commit()
    
    async def _update_step_status(self, step_execution_id: str, status: StepStatus, result: Dict = None):
        """Update step execution status"""
        async with self.db_manager.get_session() as session:
            step_execution = await session.get(StepExecution, step_execution_id)
            
            if step_execution:
                step_execution.status = status
                
                if status in [StepStatus.COMPLETED, StepStatus.FAILED]:
                    step_execution.completed_at = datetime.utcnow()
                    step_execution.result = result
                
                await session.commit()
    
    def _determine_next_step(self, workflow_def: Dict, step_def: Dict, 
                           step_result: Dict, parameters: Dict) -> Optional[str]:
        """Determine the next step based on step result"""
        step_type = step_def.get("type", StepType.AGENT_TASK)
        
        if step_type == StepType.CONDITION:
            # For condition step, use true or false path
            condition_result = step_result.get("condition_result", False)
            return step_def.get("true_step") if condition_result else step_def.get("false_step")
        
        elif step_type == StepType.DECISION:
            # For decision step, use the chosen path
            return step_result.get("next_step")
        
        # Default to regular next step
        return step_def.get("next_step")
    
    def _extract_parameters(self, parameter_template: Dict, parameters: Dict) -> Dict:
        """Extract parameters from template, substituting variables"""
        if not parameter_template:
            return {}
        
        result = {}
        for key, value_template in parameter_template.items():
            result[key] = self._extract_value(value_template, parameters)
        
        return result
    
    def _extract_value(self, template: Any, parameters: Dict) -> Any:
        """Extract value from template, substituting variables"""
        if isinstance(template, str):
            # Handle string templates with variable substitution
            if template.startswith("$"):
                var_name = template[1:]
                if var_name in parameters:
                    return parameters[var_name]
                return template
            
            # Handle string interpolation ${var} syntax
            if "${" in template:
                result = template
                for param_name, param_value in parameters.items():
                    if isinstance(param_value, (str, int, float, bool)):
                        result = result.replace(f"${{{param_name}}}", str(param_value))
                return result
            
            return template
        
        elif isinstance(template, dict):
            # Recursively process dictionaries
            return {k: self._extract_value(v, parameters) for k, v in template.items()}
        
        elif isinstance(template, list):
            # Recursively process lists
            return [self._extract_value(item, parameters) for item in template]
        
        # Return other types as-is
        return template
    
    async def _select_agent_for_task(self, agent_type: Optional[str], 
                                  agent_id: Optional[str],
                                  required_capabilities: List[str]) -> Optional[str]:
        """Select appropriate agent for task"""
        if agent_id:
            # Specific agent requested
            return agent_id
        
        # Find agent by type and capabilities
        return await self.agent_manager.find_agent_for_task(
            agent_type, required_capabilities
        )
    
    async def _queue_and_wait_for_task(self, agent_id: str, task_data: Dict) -> Dict:
        """Queue task and wait for result"""
        # Create task
        task_id = await self.task_queue.enqueue_task(agent_id, task_data)
        
        # Wait for task completion
        timeout_seconds = task_data.get("timeout_seconds", 300)
        
        try:
            result = await self.task_queue.wait_for_task_result(
                task_id, timeout_seconds
            )
            return result
        except asyncio.TimeoutError:
            # Handle timeout
            await self.task_queue.mark_task_as_failed(
                task_id, "Task execution timed out"
            )
            raise
    
    async def _resolve_approvers(self, approver_ids: List[str], 
                               approval_groups: List[str]) -> List[str]:
        """Resolve approvers from IDs and groups"""
        final_approvers = set(approver_ids)
        
        # Add users from groups
        async with self.db_manager.get_session() as session:
            for group in approval_groups:
                result = await session.execute(
                    select(User.id).where(User.groups.contains([group]))
                )
                group_users = result.scalars().all()
                final_approvers.update(group_users)
        
        return list(final_approvers)
    
    async def _resolve_recipients(self, recipients: List[str], 
                                recipient_groups: List[str]) -> List[str]:
        """Resolve notification recipients from IDs and groups"""
        final_recipients = set(recipients)
        
        # Add users from groups (same as resolving approvers)
        final_recipients.update(
            await self._resolve_approvers([], recipient_groups)
        )
        
        return list(final_recipients)
    
    async def _create_approval_request(self, request_data: Dict) -> str:
        """Create approval request"""
        request_id = str(uuid.uuid4())
        
        # Store in Redis
        await self.redis.set(
            f"approval:{request_id}", 
            json.dumps(request_data),
            ex=3600 * request_data.get("expiry_hours", 24)
        )
        
        return request_id
    
    async def _notify_approvers(self, request_id: str, approvers: List[str], request_data: Dict):
        """Notify approvers about approval request"""
        notification = {
            "title": f"Approval Request: {request_data['title']}",
            "message": request_data["description"],
            "priority": "high",
            "data": {
                "request_id": request_id,
                "workflow_execution_id": request_data["workflow_execution_id"],
                "step_id": request_data["step_id"],
                "expiry": datetime.utcnow() + timedelta(hours=request_data["expiry_hours"])
            }
        }
        
        for approver_id in approvers:
            await self.notification_manager.send_notification(approver_id, notification)
    
    async def _wait_for_approval_result(self, request_id: str) -> Dict:
        """Wait for approval request to be approved or rejected"""
        queue_name = f"approval_result:{request_id}"
        
        # Create Redis pubsub pattern for receiving result
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(queue_name)
        
        try:
            # Wait for message
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    result = json.loads(message['data'])
                    return result
        finally:
            await pubsub.unsubscribe(queue_name)
    
    async def _update_approval_request(self, request_id: str, update_data: Dict):
        """Update approval request data"""
        current_data = await self.redis.get(f"approval:{request_id}")
        if not current_data:
            return
        
        request_data = json.loads(current_data)
        request_data.update(update_data)
        
        await self.redis.set(
            f"approval:{request_id}", 
            json.dumps(request_data),
            ex=3600 * request_data.get("expiry_hours", 24)
        )
    
    async def _evaluate_condition_expression(self, condition: str, parameters: Dict) -> bool:
        """Evaluate condition expression"""
        if not condition:
            return False
        
        # For security, limit the condition expressions to simple comparisons
        # A proper implementation would use a secure expression evaluator
        
        # Process simple comparison conditions with parameter substitution
        condition = self._extract_value(condition, parameters)
        
        try:
            # Use a sandboxed environment for evaluation
            condition_result = await self._evaluate_condition_in_sandbox(condition, parameters)
            return bool(condition_result)
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False
    
    async def _evaluate_condition_in_sandbox(self, condition: str, parameters: Dict) -> bool:
        """Evaluate condition in a restricted sandbox"""
        # Implementation would use a secure sandbox like PyPy or RestrictedPython
        # This is a simplified version
        
        safe_globals = {
            "params": parameters,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "min": min,
            "max": max,
            "sum": sum,
            "list": list
        }
        
        # Replace common parameter references
        for param_name, param_value in parameters.items():
            condition = condition.replace(f"${{{param_name}}}", repr(param_value))
        
        # Execute in sandbox
        result = eval(condition, {"__builtins__": {}}, safe_globals)
        return bool(result)
    
    async def _evaluate_condition_script(self, script: str, parameters: Dict) -> bool:
        """Evaluate condition using custom script"""
        result = await self._execute_script_in_sandbox(script, "python", {"parameters": parameters})
        return bool(result.get("result", False))
    
    async def _execute_script_in_sandbox(self, script: str, script_type: str, context: Dict) -> Dict:
        """Execute script in a secure sandbox"""
        # Implementation would use a secure sandbox like PyPy or RestrictedPython
        # This is a simplified version
        
        if script_type != "python":
            return {
                "success": False,
                "error": f"Unsupported script type: {script_type}"
            }
        
        try:
            # Create safe globals
            safe_globals = {
                "params": context.get("parameters", {}),
                "context": context.get("workflow_context", {}),
                "execution_id": context.get("execution_id"),
                "step_id": context.get("step_id"),
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "min": min,
                "max": max,
                "sum": sum,
                "list": list,
                "dict": dict,
                "result": None
            }
            
            # Execute script
            exec(script, {"__builtins__": {}}, safe_globals)
            
            return {
                "success": True,
                "result": safe_globals.get("result")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Script execution error: {str(e)}"
            }