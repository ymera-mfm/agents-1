
"""
Advanced Orchestrator Agent
Intelligent task routing with load balancing, health awareness, and workflow orchestration
"""

import asyncio
import json
import time
import traceback
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import heapq
import random

from base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResponse, Priority, AgentStatus
from opentelemetry import trace

@dataclass
class AgentCapability:
    agent_id: str
    agent_name: str
    agent_type: str
    capabilities: List[str]
    current_load: int = 0
    max_load: int = 10
    health_score: float = 1.0
    last_seen: float = field(default_factory=time.time)
    average_response_time: float = 0.0
    success_rate: float = 1.0
    
    @property
    def load_percentage(self) -> float:
        return (self.current_load / max(self.max_load, 1)) * 100
    
    @property
    def is_healthy(self) -> bool:
        # An agent is healthy if it's been seen recently, has a good health score, and is not overloaded
        return (
            time.time() - self.last_seen < 30 and  # Seen in last 30 seconds
            self.health_score > 0.5 and
            self.load_percentage < 90
        )
    
    @property
    def priority_score(self) -> float:
        """Calculate routing priority score (higher is better)"""
        if not self.is_healthy:
            return 0.0
        
        # Factors influencing priority: lower load, higher health, faster response, higher success rate
        load_factor = max(0.1, 1.0 - (self.load_percentage / 100))
        health_factor = self.health_score
        # Normalize response time: assume 10s is a bad response time, 0s is perfect
        response_factor = max(0.1, 1.0 - min(1.0, self.average_response_time / 10.0))
        success_factor = self.success_rate
        
        # Combine factors. Weights can be adjusted based on system priorities.
        return load_factor * health_factor * response_factor * success_factor

@dataclass 
class TaskQueue:
    priority: Priority
    tasks: deque = field(default_factory=deque)
    
    def put(self, task: TaskRequest):
        self.tasks.append(task)
    
    def get(self) -> Optional[TaskRequest]:
        return self.tasks.popleft() if self.tasks else None
    
    def size(self) -> int:
        return len(self.tasks)

@dataclass
class WorkflowInstance:
    workflow_id: str
    instance_id: str
    steps: List[Dict]
    current_step: int = 0
    status: str = "running"
    results: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)

class OrchestratorAgent(BaseAgent):
    """
    Advanced Orchestrator with:
    - Intelligent load-based routing
    - Health-aware task distribution  
    - Multi-priority task queues
    - Workflow orchestration
    - Real-time agent discovery
    - Circuit breaker integration
    - Performance optimization
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Agent registry and capabilities
        self.agents: Dict[str, AgentCapability] = {}
        self.capability_map: Dict[str, List[str]] = defaultdict(list)  # capability -> [agent_names]
        
        # Task queues by priority
        self.task_queues: Dict[Priority, TaskQueue] = {
            priority: TaskQueue(priority) for priority in Priority
        }
        
        # Active task tracking
        self.active_tasks_orchestrator: Dict[str, Dict] = {}  # task_id -> task_info (to avoid conflict with BaseAgent.active_tasks)
        self.agent_tasks: Dict[str, Set[str]] = defaultdict(set)  # agent_id -> task_ids
        
        # Workflow management
        self.active_workflows: Dict[str, WorkflowInstance] = {}
        self.workflow_definitions: Dict[str, Dict] = {}
        
        # Performance metrics
        self.routing_stats = {
            'total_routed': 0,
            'routing_failures': 0,
            'average_routing_time': 0.0,
            'agent_utilization': defaultdict(list)
        }
        
        # Load balancing algorithms
        self.load_balancer_strategies = {
            'round_robin': self._round_robin_selection,
            'least_loaded': self._least_loaded_selection,
            'weighted_random': self._weighted_random_selection,
            'performance_based': self._performance_based_selection
        }
        
        self.default_strategy = 'performance_based'
        self.strategy_counters = defaultdict(int)  # Track strategy usage
        
    async def start(self):
        """Start orchestrator services"""
        # Subscribe to agent heartbeats (from METRICS stream)
        await self._subscribe(
            "agent.heartbeat",
            self._handle_agent_heartbeat
        )
        
        # Subscribe to task responses (from TASKS stream)
        await self._subscribe(
            "task.completed",
            self._handle_task_response
        )
        
        # Subscribe to agent registration (from METRICS stream)
        await self._subscribe(
            "agent.register",
            self._handle_agent_registration
        )

        # Subscribe to workflow requests
        await self._subscribe(
            "workflow.start",
            self._handle_workflow_start,
            queue_group="orchestrators"
        )
        
        # Load workflow definitions from database
        await self._load_workflow_definitions()
        
        # Start background tasks
        asyncio.create_task(self._task_dispatcher())
        asyncio.create_task(self._health_monitor())
        asyncio.create_task(self._workflow_monitor())
        
        self.logger.info("Orchestrator started",
                        capabilities=list(self.capability_map.keys()),
                        agents=len(self.agents))

    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Implement the actual task logic for the Orchestrator agent"""
        task_type = request.task_type
        payload = request.payload

        try:
            result: Dict[str, Any] = {}
            if task_type == "route_task":
                # This is the primary task for the orchestrator: routing other tasks
                # The payload for 'route_task' should contain the actual task to be routed
                task_to_route = TaskRequest(**payload["task_to_route"])
                routed = await self._handle_task_request_internal(task_to_route)
                result = {"routed": routed, "task_id": task_to_route.task_id}
            elif task_type == "register_agent":
                # This task type is handled by _handle_agent_registration directly from NATS
                # If an external system wants to register an agent via a task, this can be used.
                # For now, we assume agent registration happens via NATS heartbeat/register messages.
                raise NotImplementedError("Agent registration via task not yet implemented.")
            elif task_type == "get_agent_status":
                agent_name = payload["agent_name"]
                agent_info = self.agents.get(agent_name)
                if agent_info:
                    result = asdict(agent_info)
                else:
                    raise ValueError(f"Agent {agent_name} not found.")
            else:
                raise ValueError(f"Unknown orchestrator task type: {task_type}")
            
            return result

        except Exception as e:
            self.logger.error(f"Error executing orchestrator task {task_type}", error=str(e), traceback=traceback.format_exc())
            raise # Re-raise to be caught by BaseAgent's _handle_task_request

    async def _load_workflow_definitions(self):
        """Load workflow definitions from database"""
        if not self.db_pool:
            self.logger.warning("Database pool not initialized, cannot load workflow definitions.")
            return
            
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT workflow_id, name, definition FROM workflows WHERE status = 'active'"
                )
                
                for row in rows:
                    self.workflow_definitions[row['name']] = {
                        'id': str(row['workflow_id']),
                        'definition': row['definition']
                    }
                
                self.logger.info("Loaded workflow definitions", count=len(self.workflow_definitions))
        except Exception as e:
            self.logger.error("Failed to load workflow definitions", error=str(e), traceback=traceback.format_exc())
    
    async def _handle_task_request_internal(self, request: TaskRequest) -> bool:
        """Handle incoming task requests with intelligent routing"""
        with self.tracer.start_as_current_span("task_routing") as span:
            span.set_attribute("task_id", request.task_id)
            span.set_attribute("task_type", request.task_type)
            span.set_attribute("priority", request.priority.value)
            
            self.logger.info("Received task request for routing",
                           task_id=request.task_id,
                           task_type=request.task_type,
                           priority=request.priority.name)
            
            # Add to appropriate priority queue
            self.task_queues[request.priority].put(request)
            
            # Update metrics
            self.routing_stats['total_routed'] += 1
            
            # Immediate routing attempt if agents available
            return await self._try_immediate_routing(request)
                
    async def _try_immediate_routing(self, request: TaskRequest) -> bool:
        """Try to route task immediately if suitable agent available"""
        suitable_agents = self._find_suitable_agents(request.task_type)
        
        if not suitable_agents:
            self.logger.warning("No suitable agents available for immediate routing",
                              task_type=request.task_type,
                              queued_for_later=True)
            return False
        
        # Select best agent using configured strategy
        selected_agent = await self._select_agent(suitable_agents, request.task_type)
        
        if selected_agent:
            await self._route_task_to_agent(request, selected_agent)
            # Task is routed, remove from queue if it was there (it should be)
            self._remove_from_queue(request)
            return True
        
        return False
    
    async def _task_dispatcher(self):
        """Background task dispatcher - processes queues in priority order"""
        while not self._shutdown_event.is_set():
            try:
                dispatched_any_task_in_cycle = False
                
                # Process queues in priority order (highest priority first)
                for priority in sorted(Priority, key=lambda p: p.value, reverse=True):
                    queue = self.task_queues[priority]
                    
                    # Iterate through tasks in the queue
                    tasks_to_requeue = deque()
                    while queue.size() > 0:
                        task = queue.get()
                        if not task:
                            continue # Should not happen if size() > 0
                        
                        suitable_agents = self._find_suitable_agents(task.task_type)
                        
                        if suitable_agents:
                            selected_agent = await self._select_agent(suitable_agents, task.task_type)
                            if selected_agent:
                                await self._route_task_to_agent(task, selected_agent)
                                dispatched_any_task_in_cycle = True
                            else:
                                # No suitable agent found for this task right now, requeue it
                                tasks_to_requeue.append(task)
                        else:
                            # No suitable agents at all for this task type, requeue it
                            tasks_to_requeue.append(task)
                    
                    # Put back tasks that couldn't be dispatched in this cycle
                    for task in tasks_to_requeue:
                        queue.put(task)
                
                # If no tasks were dispatched in this cycle, sleep to prevent busy-waiting
                if not dispatched_any_task_in_cycle:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                self.logger.error("Task dispatcher error", error=str(e), traceback=traceback.format_exc())
                await asyncio.sleep(1)
    
    def _remove_from_queue(self, request: TaskRequest):
        """Remove task from its queue. This is a linear scan, consider optimizing for large queues if needed."""
        queue = self.task_queues[request.priority]
        # Rebuild the deque without the target task
        queue.tasks = deque([t for t in queue.tasks if t.task_id != request.task_id])
    
    def _find_suitable_agents(self, task_type: str) -> List[AgentCapability]:
        """Find agents capable of handling the task type and are healthy"""
        suitable_agents = []
        
        # Iterate through agents that registered for this task_type capability
        for agent_name in self.capability_map.get(task_type, []):
            agent = self.agents.get(agent_name)
            if agent and agent.is_healthy:
                suitable_agents.append(agent)
        
        return suitable_agents
    
    async def _select_agent(self, agents: List[AgentCapability], task_type: str) -> Optional[AgentCapability]:
        """Select best agent using configured strategy"""
        if not agents:
            return None
        
        strategy_func = self.load_balancer_strategies.get(self.default_strategy)
        if not strategy_func:
            self.logger.warning(f"Unknown load balancing strategy: {self.default_strategy}. Falling back to performance_based.")
            strategy_func = self._performance_based_selection
        
        selected = await strategy_func(agents, task_type)
        if selected:
            self.strategy_counters[self.default_strategy] += 1
        
        return selected
    
    async def _performance_based_selection(self, agents: List[AgentCapability], task_type: str) -> Optional[AgentCapability]:
        """Select agent based on performance metrics (priority score)"""
        if not agents:
            return None
        
        # Sort by priority score (higher is better)
        sorted_agents = sorted(agents, key=lambda a: a.priority_score, reverse=True)
        
        # Return the best performing agent if its score is positive
        return sorted_agents[0] if sorted_agents[0].priority_score > 0 else None
    
    async def _least_loaded_selection(self, agents: List[AgentCapability], task_type: str) -> Optional[AgentCapability]:
        """Select least loaded agent"""
        if not agents:
            return None
        
        # Filter out agents that are at max load to avoid division by zero or incorrect load calculation
        available_agents = [a for a in agents if a.current_load < a.max_load]
        if not available_agents:
            return None

        return min(available_agents, key=lambda a: a.load_percentage)
    
    async def _weighted_random_selection(self, agents: List[AgentCapability], task_type: str) -> Optional[AgentCapability]:
        """Select an agent using weighted random selection based on priority score"""
        if not agents:
            return None
        
        weights = [agent.priority_score for agent in agents]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return random.choice(agents) # Fallback to random if no agent has positive score
            
        return random.choices(agents, weights=weights, k=1)[0]

    async def _round_robin_selection(self, agents: List[AgentCapability], task_type: str) -> Optional[AgentCapability]:
        """Select agent using round-robin. Requires stateful tracking per capability."""
        # This is a simplified round-robin. A more robust one would need to track last selected agent per capability.
        # For now, it just picks the first available healthy agent.
        if agents:
            return agents[0]
        return None

    async def _route_task_to_agent(self, request: TaskRequest, agent: AgentCapability):
        """Route the task to the selected agent via NATS"""
        with self.tracer.start_as_current_span("route_task_to_agent") as span:
            span.set_attribute("task.id", request.task_id)
            span.set_attribute("agent.name", agent.agent_name)
            
            subject = f"agent.{agent.agent_name}.task"
            self.logger.info("Routing task to agent", task_id=request.task_id, agent_name=agent.agent_name)
            
            try:
                # Store task in active tasks before sending
                self.active_tasks_orchestrator[request.task_id] = {
                    "request": asdict(request),
                    "agent_id": agent.agent_id,
                    "routed_at": time.time()
                }
                self.agent_tasks[agent.agent_id].add(request.task_id)
                agent.current_load += 1

                # Publish task to agent's NATS subject
                await self._publish(subject, json.dumps(asdict(request)).encode())
                self.logger.debug("Task sent to agent", task_id=request.task_id, agent_name=agent.agent_name)
                
                # Store task in DB
                if self.db_pool:
                    await self._store_task_in_db(request, agent.agent_id)

            except Exception as e:
                self.logger.error("Failed to route task", task_id=request.task_id, agent_name=agent.agent_name, error=str(e), traceback=traceback.format_exc())
                self.routing_stats['routing_failures'] += 1
                # If routing fails, decrement load and remove from active tasks
                if request.task_id in self.active_tasks_orchestrator:
                    del self.active_tasks_orchestrator[request.task_id]
                if agent.agent_id in self.agent_tasks and request.task_id in self.agent_tasks[agent.agent_id]:
                    self.agent_tasks[agent.agent_id].remove(request.task_id)
                if agent.current_load > 0:
                    agent.current_load -= 1

    async def _handle_agent_heartbeat(self, msg):
        """Process agent heartbeats to update agent registry and health"""
        try:
            data = json.loads(msg.data.decode())
            agent_id = data["agent_id"]
            agent_name = data["agent_name"]
            agent_type = data["agent_type"]
            capabilities = data["capabilities"]
            status = AgentStatus(data["status"])
            current_load = data["current_load"]
            max_load = data["max_load"]
            health_score = data["health_score"]
            average_response_time = data.get("average_response_time", 0.0)
            success_rate = data.get("success_rate", 1.0)

            if agent_name not in self.agents:
                self.logger.info("New agent detected via heartbeat", agent_name=agent_name, agent_id=agent_id)
                agent_capability = AgentCapability(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    agent_type=agent_type,
                    capabilities=capabilities,
                    current_load=current_load,
                    max_load=max_load,
                    health_score=health_score,
                    average_response_time=average_response_time,
                    success_rate=success_rate
                )
                self.agents[agent_name] = agent_capability
            else:
                agent_capability = self.agents[agent_name]
                agent_capability.agent_id = agent_id # Update ID in case it changed
                agent_capability.capabilities = capabilities
                agent_capability.current_load = current_load
                agent_capability.max_load = max_load
                agent_capability.health_score = health_score
                agent_capability.last_seen = time.time()
                agent_capability.average_response_time = average_response_time
                agent_capability.success_rate = success_rate
            
            # Update capability map
            for cap in capabilities:
                if agent_name not in self.capability_map[cap]:
                    self.capability_map[cap].append(agent_name)
            
            # Remove agent from capabilities it no longer reports
            caps_to_remove = []
            for cap, agent_list in self.capability_map.items():
                if agent_name in agent_list and cap not in capabilities:
                    caps_to_remove.append((cap, agent_name))
            for cap, name in caps_to_remove:
                self.capability_map[cap].remove(name)

            # Update agent status in DB
            if self.db_pool:
                await self._update_agent_status_in_db(agent_capability)

            # Publish agent presence update for API Gateway
            await self._publish_to_stream("agent.presence.update", {
                "agent_id": agent_name, # Use agent_name for external identification
                "status": status.value,
                "timestamp": time.time()
            })

        except Exception as e:
            self.logger.error("Error processing agent heartbeat", error=str(e), traceback=traceback.format_exc())

    async def _handle_agent_registration(self, msg):
        """Handle agent registration messages"""
        try:
            data = json.loads(msg.data.decode())
            agent_id = data["agent_id"]
            agent_name = data["agent_name"]
            agent_type = data["agent_type"]
            capabilities = data["capabilities"]
            version = data.get("version", "1.0.0")
            description = data.get("description", "")
            max_concurrent_tasks = data.get("max_concurrent_tasks", 10)

            if agent_name not in self.agents:
                self.logger.info("Registering new agent", agent_name=agent_name, agent_id=agent_id)
                agent_capability = AgentCapability(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    agent_type=agent_type,
                    capabilities=capabilities,
                    max_load=max_concurrent_tasks
                )
                self.agents[agent_name] = agent_capability

                for cap in capabilities:
                    if agent_name not in self.capability_map[cap]:
                        self.capability_map[cap].append(agent_name)
                
                # Store in DB
                if self.db_pool:
                    await self._register_agent_in_db(agent_id, agent_name, agent_type, version, description, capabilities, max_concurrent_tasks)
            else:
                self.logger.debug("Agent already registered, updating capabilities", agent_name=agent_name)
                agent_capability = self.agents[agent_name]
                agent_capability.capabilities = capabilities
                agent_capability.max_load = max_concurrent_tasks
                # Update capability map
                for cap in capabilities:
                    if agent_name not in self.capability_map[cap]:
                        self.capability_map[cap].append(agent_name)
                # Remove agent from capabilities it no longer reports
                caps_to_remove = []
                for cap, agent_list in self.capability_map.items():
                    if agent_name in agent_list and cap not in capabilities:
                        caps_to_remove.append((cap, agent_name))
                for cap, name in caps_to_remove:
                    self.capability_map[cap].remove(name)
                
                # Update in DB
                if self.db_pool:
                    await self._update_agent_registration_in_db(agent_id, agent_name, agent_type, version, description, capabilities, max_concurrent_tasks)

            # Publish agent presence update for API Gateway
            await self._publish_to_stream("agent.presence.update", {
                "agent_id": agent_name, # Use agent_name for external identification
                "status": AgentStatus.ACTIVE.value,
                "timestamp": time.time()
            })

        except Exception as e:
            self.logger.error("Error processing agent registration", error=str(e), traceback=traceback.format_exc())

    async def _handle_task_response(self, msg):
        """Process task responses from agents"""
        try:
            data = json.loads(msg.data.decode())
            response = TaskResponse(**data)
            
            if response.task_id in self.active_tasks_orchestrator:
                task_info = self.active_tasks_orchestrator.pop(response.task_id)
                agent_id = task_info["agent_id"]
                self.agent_tasks[agent_id].discard(response.task_id)
                
                # Decrement agent load
                agent_name = next((name for name, agent in self.agents.items() if agent.agent_id == agent_id), None)
                if agent_name and self.agents[agent_name].current_load > 0:
                    self.agents[agent_name].current_load -= 1

                self.logger.info("Task completed",
                               task_id=response.task_id,
                               success=response.success,
                               agent_id=agent_id)
                
                # Store task result in DB
                if self.db_pool:
                    await self._update_task_status_in_db(response.task_id, response.success, response.result, response.error)

                # Check for workflow tasks
                if "workflow_instance_id" in task_info["request"]["metadata"]:
                    workflow_instance_id = task_info["request"]["metadata"]["workflow_instance_id"]
                    await self._advance_workflow(workflow_instance_id, response)

            else:
                self.logger.warning("Received response for unknown or already completed task", task_id=response.task_id)

        except Exception as e:
            self.logger.error("Error processing task response", error=str(e), traceback=traceback.format_exc())

    async def _handle_workflow_start(self, msg):
        """Handle requests to start a new workflow instance"""
        try:
            data = json.loads(msg.data.decode())
            workflow_name = data["workflow_name"]
            instance_id = data.get("instance_id", str(uuid.uuid4()))
            input_data = data.get("input_data", {})
            metadata = data.get("metadata", {})

            workflow_def = self.workflow_definitions.get(workflow_name)
            if not workflow_def:
                self.logger.error("Workflow definition not found", workflow_name=workflow_name)
                return
            
            # Store workflow instance in DB
            if self.db_pool:
                await self._create_workflow_instance_in_db(instance_id, workflow_def['id'], metadata.get("submitted_by"), input_data)

            instance = WorkflowInstance(
                workflow_id=workflow_def['id'],
                instance_id=instance_id,
                steps=workflow_def['definition']['steps'],
                results={"input": input_data, "metadata": metadata}
            )
            self.active_workflows[instance_id] = instance
            self.logger.info("Workflow instance started", workflow_name=workflow_name, instance_id=instance_id)

            await self._advance_workflow(instance_id)

        except Exception as e:
            self.logger.error("Error starting workflow instance", error=str(e), traceback=traceback.format_exc())

    async def _advance_workflow(self, instance_id: str, last_task_response: Optional[TaskResponse] = None):
        """Advance the workflow to the next step"""
        instance = self.active_workflows.get(instance_id)
        if not instance:
            self.logger.warning("Attempted to advance unknown workflow instance", instance_id=instance_id)
            return

        if last_task_response:
            # Store result of the last task
            current_step_name = instance.steps[instance.current_step - 1]["name"]
            instance.results[current_step_name] = {
                "success": last_task_response.success,
                "result": last_task_response.result,
                "error": last_task_response.error
            }
            # Update workflow instance in DB
            if self.db_pool:
                await self._update_workflow_instance_in_db(instance_id, instance.current_step - 1, instance.status, instance.results, last_task_response.error)

            if not last_task_response.success:
                instance.status = "failed"
                self.logger.error("Workflow failed at step", instance_id=instance_id, step=instance.current_step - 1, error=last_task_response.error)
                # Update workflow instance in DB
                if self.db_pool:
                    await self._update_workflow_instance_in_db(instance_id, instance.current_step - 1, instance.status, instance.results, last_task_response.error)
                return

        if instance.current_step >= len(instance.steps):
            instance.status = "completed"
            self.logger.info("Workflow completed", instance_id=instance_id)
            # Update workflow instance in DB
            if self.db_pool:
                await self._update_workflow_instance_in_db(instance_id, instance.current_step, instance.status, instance.results)
            del self.active_workflows[instance_id]
            return

        current_step_def = instance.steps[instance.current_step]
        task_type = current_step_def["task_type"]
        agent_capability_needed = current_step_def.get("agent_capability", task_type) # Default to task_type
        step_payload = current_step_def.get("payload", {})

        # Merge workflow context into task payload
        task_payload = {**instance.results, **step_payload, "workflow_instance_id": instance_id}

        # Create a new TaskRequest for this step
        task_request = TaskRequest(
            task_id=str(uuid.uuid4()),
            task_type=agent_capability_needed, # Route based on capability
            sender_id=self.config.name,
            payload=task_payload,
            priority=Priority.NORMAL, # Workflows tasks can have default priority
            metadata={
                "workflow_instance_id": instance_id,
                "workflow_step_index": instance.current_step,
                "workflow_step_name": current_step_def.get("name", f"step_{instance.current_step}")
            }
        )

        self.logger.info("Dispatching workflow step task", instance_id=instance_id, step=instance.current_step, task_type=task_type)
        # Add to orchestrator's internal queue for routing
        self.task_queues[task_request.priority].put(task_request)
        instance.current_step += 1
        # Update workflow instance in DB
        if self.db_pool:
            await self._update_workflow_instance_in_db(instance_id, instance.current_step, instance.status, instance.results)

    async def _workflow_monitor(self):
        """Background task to monitor active workflows and advance them"""
        while not self._shutdown_event.is_set():
            try:
                # This loop primarily handles workflows that might be waiting for external triggers
                # or need periodic checks. For now, _advance_workflow is called directly on task completion.
                # This can be extended for timeout handling, conditional branching, etc.
                await asyncio.sleep(5) # Check every 5 seconds
            except Exception as e:
                self.logger.error(f"Workflow monitor failed: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(10)

    async def _health_monitor(self):
        """Periodically check agent health and remove inactive agents"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                inactive_threshold = 60 # Agents inactive for 60 seconds are considered offline
                
                agents_to_remove = []
                for agent_name, agent_cap in list(self.agents.items()):
                    if current_time - agent_cap.last_seen > inactive_threshold:
                        self.logger.warning("Agent considered offline due to inactivity", agent_name=agent_name)
                        agents_to_remove.append(agent_name)
                        # Update agent status in DB
                        if self.db_pool:
                            await self._update_agent_status_in_db(agent_cap, AgentStatus.OFFLINE)
                        # Publish agent presence update for API Gateway
                        await self._publish_to_stream("agent.presence.update", {
                            "agent_id": agent_name,
                            "status": AgentStatus.OFFLINE.value,
                            "timestamp": time.time()
                        })

                for agent_name in agents_to_remove:
                    agent_cap = self.agents.pop(agent_name)
                    for cap in agent_cap.capabilities:
                        if agent_name in self.capability_map[cap]:
                            self.capability_map[cap].remove(agent_name)
                    self.logger.info("Removed inactive agent", agent_name=agent_name)
                
                await asyncio.sleep(10) # Check every 10 seconds
            except Exception as e:
                self.logger.error(f"Health monitor failed: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(30)

    # Database Operations
    async def _store_task_in_db(self, request: TaskRequest, assigned_agent_id: str):
        """Store a task in the database"""
        if not self.db_pool:
            self.logger.warning("Database pool not initialized. Task not stored.")
            return
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("""
                        INSERT INTO tasks (task_id, workflow_instance_id, agent_id, task_type, payload, status, priority, created_at, timeout_at, correlation_id)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    request.task_id,
                    request.metadata.get("workflow_instance_id"),
                    assigned_agent_id,
                    request.task_type,
                    json.dumps(request.payload),
                    TaskStatus.RUNNING.value, # Initially running once routed
                    request.priority.value,
                    time.time(),
                    time.time() + request.timeout_seconds,
                    request.correlation_id
                    )
        except Exception as e:
            self.logger.error("Failed to store task in DB", task_id=request.task_id, error=str(e), traceback=traceback.format_exc())

    async def _update_task_status_in_db(self, task_id: str, success: bool, result: Dict[str, Any], error: Optional[str]):
        """Update task status in the database"""
        if not self.db_pool:
            self.logger.warning("Database pool not initialized. Task status not updated.")
            return
        try:
            status = TaskStatus.COMPLETED.value if success else TaskStatus.FAILED.value
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE tasks
                    SET status = $1, result = $2, error = $3, completed_at = $4
                    WHERE task_id = $5
                """,
                status,
                json.dumps(result),
                error,
                time.time(),
                task_id
                )
        except Exception as e:
            self.logger.error("Failed to update task status in DB", task_id=task_id, error=str(e), traceback=traceback.format_exc())

    async def _register_agent_in_db(self, agent_id: str, agent_name: str, agent_type: str, version: str, description: str, capabilities: List[str], max_concurrent_tasks: int):
        """Register agent in the database"""
        if not self.db_pool:
            self.logger.warning("Database pool not initialized. Agent not registered.")
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agents (agent_id, name, type, version, description, capabilities, max_concurrent_tasks, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (agent_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        type = EXCLUDED.type,
                        version = EXCLUDED.version,
                        description = EXCLUDED.description,
                        capabilities = EXCLUDED.capabilities,
                        max_concurrent_tasks = EXCLUDED.max_concurrent_tasks,
                        status = EXCLUDED.status,
                        updated_at = CURRENT_TIMESTAMP
                """,
                agent_id,
                agent_name,
                agent_type,
                version,
                description,
                json.dumps(capabilities),
                max_concurrent_tasks,
                AgentStatus.ACTIVE.value
                )
        except Exception as e:
            self.logger.error("Failed to register agent in DB", agent_id=agent_id, error=str(e), traceback=traceback.format_exc())

    async def _update_agent_registration_in_db(self, agent_id: str, agent_name: str, agent_type: str, version: str, description: str, capabilities: List[str], max_concurrent_tasks: int):
        """Update agent registration in the database"""
        if not self.db_pool:
            self.logger.warning("Database pool not initialized. Agent registration not updated.")
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE agents
                    SET name = $1, type = $2, version = $3, description = $4, capabilities = $5, max_concurrent_tasks = $6, updated_at = CURRENT_TIMESTAMP
                    WHERE agent_id = $7
                """,
                agent_name,
                agent_type,
                version,
                description,
                json.dumps(capabilities),
                max_concurrent_tasks,
                agent_id
                )
        except Exception as e:
            self.logger.error("Failed to update agent registration in DB", agent_id=agent_id, error=str(e), traceback=traceback.format_exc())

    async def _update_agent_status_in_db(self, agent_capability: AgentCapability, status: Optional[AgentStatus] = None):
        """Update agent status and load in the database"""
        if not self.db_pool:
            self.logger.warning("Database pool not initialized. Agent status not updated.")
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE agents
                    SET status = $1, current_load = $2, health_score = $3, last_seen = $4, average_response_time = $5, success_rate = $6, updated_at = CURRENT_TIMESTAMP
                    WHERE agent_id = $7
                """,
                (status or agent_capability.status).value,
                agent_capability.current_load,
                agent_capability.health_score,
                agent_capability.last_seen,
                agent_capability.average_response_time,
                agent_capability.success_rate,
                agent_capability.agent_id
                )
        except Exception as e:
            self.logger.error("Failed to update agent status in DB", agent_id=agent_capability.agent_id, error=str(e), traceback=traceback.format_exc())

    async def _create_workflow_instance_in_db(self, instance_id: str, workflow_id: str, submitted_by: Optional[str], input_data: Dict[str, Any]):
        """Create a new workflow instance record in the database"""
        if not self.db_pool:
            self.logger.warning("Database pool not initialized. Workflow instance not created.")
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO workflow_instances (instance_id, workflow_id, submitted_by, input_data, status, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                instance_id,
                workflow_id,
                submitted_by,
                json.dumps(input_data),
                "running",
                time.time()
                )
        except Exception as e:
            self.logger.error("Failed to create workflow instance in DB", instance_id=instance_id, error=str(e), traceback=traceback.format_exc())

    async def _update_workflow_instance_in_db(self, instance_id: str, current_step: int, status: str, results: Dict[str, Any], error: Optional[str] = None):
        """Update an existing workflow instance record in the database"""
        if not self.db_pool:
            self.logger.warning("Database pool not initialized. Workflow instance not updated.")
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE workflow_instances
                    SET current_step = $1, status = $2, results = $3, error = $4, updated_at = CURRENT_TIMESTAMP
                    WHERE instance_id = $5
                """,
                current_step,
                status,
                json.dumps(results),
                error,
                instance_id
                )
        except Exception as e:
            self.logger.error("Failed to update workflow instance in DB", instance_id=instance_id, error=str(e), traceback=traceback.format_exc())


if __name__ == "__main__":
    config = AgentConfig(
        name="orchestrator",
        agent_type="orchestrator",
        capabilities=["route_task", "manage_workflow"],
        nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://agent:secure_password@postgres:5432/ymera"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
        consul_url=os.getenv("CONSUL_URL", "http://consul:8500"),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )
    
    agent = OrchestratorAgent(config)
    asyncio.run(agent.run())

