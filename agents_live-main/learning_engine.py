"""
Multi-Agent Learning Engine - Production Ready
Advanced learning and knowledge management for multi-agent systems
Integrates with existing production infrastructure
"""

import asyncio
import logging
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue, PriorityQueue
import pickle
import hashlib
import numpy as np
from enum import Enum
import traceback

# Vector storage imports
try:
    import pinecone
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logging.warning("Pinecone not available - vector storage will be limited")

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logging.warning("ChromaDB not available - using fallback storage")

# AI provider imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Local imports
from base_agent import BaseAgent, AgentCapability
from intelligence_engine import IntelligenceEngine
from config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of learning agents"""
    REASONING = "reasoning"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    CODING = "coding"
    RESEARCH = "research"
    SYNTHESIS = "synthesis"


class LearningMode(Enum):
    """Learning methodologies"""
    SUPERVISED = "supervised"
    REINFORCEMENT = "reinforcement"
    SELF_SUPERVISED = "self_supervised"
    META_LEARNING = "meta_learning"
    TRANSFER_LEARNING = "transfer_learning"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Experience:
    """Represents a learning experience"""
    experience_id: str
    agent_id: str
    task_type: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    feedback_score: float
    execution_time: float
    timestamp: datetime
    context: Dict[str, Any]
    success: bool
    learned_patterns: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class Task:
    """Represents a task in the system"""
    task_id: str
    task_type: str
    priority: TaskPriority
    data: Dict[str, Any]
    created_at: datetime
    deadline: Optional[datetime]
    assigned_agent: Optional[str]
    dependencies: List[str]
    status: str = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['deadline'] = self.deadline.isoformat() if self.deadline else None
        data['priority'] = self.priority.value
        return data


class KnowledgeGraph:
    """Advanced knowledge graph for pattern storage"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.patterns = {}
        self.embeddings = {}
        self.lock = threading.RLock()
    
    def add_knowledge(self, concept: str, properties: Dict[str, Any], 
                     embedding: Optional[List[float]] = None):
        """Add knowledge to graph"""
        with self.lock:
            self.nodes[concept] = {
                'properties': properties,
                'created_at': datetime.now().isoformat(),
                'access_count': 0,
                'last_accessed': None
            }
            
            if embedding:
                self.embeddings[concept] = embedding
    
    def add_relationship(self, source: str, target: str, 
                        relationship_type: str, weight: float = 1.0):
        """Add relationship between concepts"""
        with self.lock:
            edge_key = f"{source}->{target}"
            self.edges[edge_key] = {
                'type': relationship_type,
                'weight': weight,
                'created_at': datetime.now().isoformat()
            }
    
    def query(self, concept: str, depth: int = 2) -> Dict[str, Any]:
        """Query knowledge graph"""
        with self.lock:
            if concept not in self.nodes:
                return {}
            
            # Update access stats
            self.nodes[concept]['access_count'] += 1
            self.nodes[concept]['last_accessed'] = datetime.now().isoformat()
            
            result = {'concept': concept, 'data': self.nodes[concept]}
            
            if depth > 0:
                # Find related concepts
                related = []
                for edge_key, edge_data in self.edges.items():
                    if edge_key.startswith(f"{concept}->"):
                        target = edge_key.split("->")[1]
                        related.append({
                            'concept': target,
                            'relationship': edge_data['type'],
                            'weight': edge_data['weight']
                        })
                
                result['related'] = related
            
            return result
    
    def find_similar(self, embedding: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """Find similar concepts by embedding"""
        if not self.embeddings:
            return []
        
        with self.lock:
            similarities = []
            for concept, concept_embedding in self.embeddings.items():
                # Cosine similarity
                similarity = np.dot(embedding, concept_embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(concept_embedding)
                )
                similarities.append((concept, float(similarity)))
            
            # Sort and return top-k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]


class VectorStore:
    """Unified vector storage interface"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.store_type = config.get('vector_store_type', 'memory')
        self.vectors = {}  # Fallback in-memory storage
        self.client = None
        
        # Initialize based on available backends
        if self.store_type == 'pinecone' and PINECONE_AVAILABLE:
            self._init_pinecone()
        elif self.store_type == 'chroma' and CHROMA_AVAILABLE:
            self._init_chroma()
        else:
            logger.info("Using in-memory vector storage")
    
    def _init_pinecone(self):
        """Initialize Pinecone"""
        try:
            api_key = self.config.get('pinecone_api_key')
            if api_key:
                self.client = Pinecone(api_key=api_key)
                logger.info("Pinecone initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
    
    def _init_chroma(self):
        """Initialize ChromaDB"""
        try:
            self.client = chromadb.Client()
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
    
    async def store(self, vector_id: str, embedding: List[float], metadata: Dict[str, Any]):
        """Store vector embedding"""
        self.vectors[vector_id] = {
            'embedding': embedding,
            'metadata': metadata,
            'created_at': datetime.now().isoformat()
        }
    
    async def query(self, embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query similar vectors"""
        if not self.vectors:
            return []
        
        similarities = []
        for vector_id, data in self.vectors.items():
            stored_embedding = data['embedding']
            similarity = np.dot(embedding, stored_embedding) / (
                np.linalg.norm(embedding) * np.linalg.norm(stored_embedding)
            )
            similarities.append({
                'id': vector_id,
                'similarity': float(similarity),
                'metadata': data['metadata']
            })
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]


class LearningAgent(BaseAgent):
    """Learning-enabled agent"""
    
    def __init__(self, agent_id: str, agent_type: AgentType, config: Dict[str, Any]):
        super().__init__(agent_id, agent_type.value, config)
        self.agent_type = agent_type
        self.experiences = []
        self.learning_rate = config.get('learning_rate', 0.01)
        self.performance_history = []
    
    async def learn_from_experience(self, experience: Experience):
        """Learn from an experience"""
        self.experiences.append(experience)
        
        # Update performance metrics
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'success': experience.success,
            'feedback_score': experience.feedback_score,
            'execution_time': experience.execution_time
        })
        
        # Keep only recent history
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
        
        logger.info(f"Agent {self.agent_id} learned from experience {experience.experience_id}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        if not self.performance_history:
            return {'experience_count': 0}
        
        recent_history = self.performance_history[-100:]
        
        return {
            'experience_count': len(self.experiences),
            'success_rate': sum(1 for h in recent_history if h['success']) / len(recent_history),
            'avg_feedback_score': np.mean([h['feedback_score'] for h in recent_history]),
            'avg_execution_time': np.mean([h['execution_time'] for h in recent_history]),
            'total_experiences': len(self.performance_history)
        }


class MultiAgentLearningEngine:
    """
    Advanced multi-agent learning engine with knowledge management
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.agents: Dict[str, LearningAgent] = {}
        self.knowledge_graph = KnowledgeGraph()
        self.vector_store = VectorStore(self.config)
        self.task_queue = PriorityQueue()
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        logger.info("MultiAgentLearningEngine initialized")
    
    def register_agent(self, agent_id: str, agent_type: AgentType, 
                      agent_config: Optional[Dict[str, Any]] = None) -> LearningAgent:
        """Register a new learning agent"""
        config = agent_config or {}
        agent = LearningAgent(agent_id, agent_type, config)
        self.agents[agent_id] = agent
        
        logger.info(f"Registered learning agent: {agent_id} (type: {agent_type.value})")
        return agent
    
    async def submit_task(self, task: Task) -> str:
        """Submit a task for execution"""
        # Add to priority queue
        priority = task.priority.value
        self.task_queue.put((-priority, task.task_id, task))
        self.active_tasks[task.task_id] = task
        
        logger.info(f"Task submitted: {task.task_id} (priority: {task.priority.name})")
        return task.task_id
    
    async def assign_task_to_agent(self, task: Task) -> Optional[str]:
        """Assign task to best-suited agent"""
        if not self.agents:
            return None
        
        # Simple assignment strategy - can be enhanced with ML
        best_agent = None
        best_score = -1
        
        for agent_id, agent in self.agents.items():
            # Score based on agent type and task type
            score = 0
            
            # Check capabilities
            if agent.can_handle(task.task_type):
                score += 10
            
            # Check performance history
            metrics = agent.get_performance_metrics()
            score += metrics.get('success_rate', 0) * 5
            
            if score > best_score:
                best_score = score
                best_agent = agent_id
        
        if best_agent:
            task.assigned_agent = best_agent
            logger.info(f"Task {task.task_id} assigned to agent {best_agent}")
        
        return best_agent
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a task"""
        start_time = time.time()
        
        try:
            # Assign to agent if not already assigned
            if not task.assigned_agent:
                agent_id = await self.assign_task_to_agent(task)
                if not agent_id:
                    raise Exception("No suitable agent available")
            
            agent = self.agents.get(task.assigned_agent)
            if not agent:
                raise Exception(f"Agent {task.assigned_agent} not found")
            
            # Execute task
            task.status = "running"
            result = await agent.execute_task({
                'task_id': task.task_id,
                'type': task.task_type,
                'data': task.data
            })
            
            task.status = "completed"
            execution_time = time.time() - start_time
            
            # Create experience for learning
            experience = Experience(
                experience_id=str(uuid.uuid4()),
                agent_id=agent.agent_id,
                task_type=task.task_type,
                input_data=task.data,
                output_data=result,
                feedback_score=result.get('quality_score', 0.5),
                execution_time=execution_time,
                timestamp=datetime.now(),
                context={'priority': task.priority.value},
                success=result.get('success', False),
                learned_patterns=[]
            )
            
            # Agent learns from experience
            await agent.learn_from_experience(experience)
            
            # Store in knowledge graph
            await self._store_experience(experience)
            
            # Move to completed
            self.completed_tasks.append(task)
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            
            logger.info(f"Task {task.task_id} completed in {execution_time:.2f}s")
            
            return {
                'success': True,
                'task_id': task.task_id,
                'result': result,
                'execution_time': execution_time,
                'agent_id': agent.agent_id
            }
            
        except Exception as e:
            task.status = "failed"
            execution_time = time.time() - start_time
            
            logger.error(f"Task {task.task_id} failed: {str(e)}")
            logger.debug(traceback.format_exc())
            
            return {
                'success': False,
                'task_id': task.task_id,
                'error': str(e),
                'execution_time': execution_time
            }
    
    async def _store_experience(self, experience: Experience):
        """Store experience in knowledge graph"""
        try:
            concept_id = f"exp_{experience.experience_id}"
            
            # Add to knowledge graph
            self.knowledge_graph.add_knowledge(
                concept_id,
                {
                    'agent_id': experience.agent_id,
                    'task_type': experience.task_type,
                    'success': experience.success,
                    'feedback_score': experience.feedback_score,
                    'execution_time': experience.execution_time
                }
            )
            
            # Create relationships
            self.knowledge_graph.add_relationship(
                f"agent_{experience.agent_id}",
                concept_id,
                "executed",
                weight=experience.feedback_score
            )
            
        except Exception as e:
            logger.error(f"Failed to store experience: {e}")
    
    async def get_agent_statistics(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics for an agent"""
        if agent_id not in self.agents:
            return {}
        
        agent = self.agents[agent_id]
        metrics = agent.get_performance_metrics()
        
        return {
            'agent_id': agent_id,
            'agent_type': agent.agent_type.value,
            'metrics': metrics,
            'status': agent.status.value if hasattr(agent, 'status') else 'active'
        }
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        return {
            'total_agents': len(self.agents),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'pending_tasks': self.task_queue.qsize(),
            'knowledge_nodes': len(self.knowledge_graph.nodes),
            'knowledge_edges': len(self.knowledge_graph.edges)
        }
    
    async def query_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Query the knowledge graph"""
        try:
            # Simple keyword-based query for now
            results = []
            
            for concept, data in self.knowledge_graph.nodes.items():
                if query.lower() in str(data).lower():
                    results.append({
                        'concept': concept,
                        'data': data
                    })
                    
                    if len(results) >= top_k:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Knowledge query failed: {e}")
            return []
    
    async def start(self):
        """Start the learning engine"""
        self.running = True
        logger.info("MultiAgentLearningEngine started")
    
    async def stop(self):
        """Stop the learning engine"""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("MultiAgentLearningEngine stopped")


# Factory function for easy instantiation
def create_learning_engine(config: Optional[Dict[str, Any]] = None) -> MultiAgentLearningEngine:
    """Create and initialize a learning engine"""
    return MultiAgentLearningEngine(config)


if __name__ == "__main__":
    # Example usage
    async def main():
        # Create engine
        engine = create_learning_engine({
            'vector_store_type': 'memory',
            'learning_rate': 0.01
        })
        
        await engine.start()
        
        # Register agents
        coding_agent = engine.register_agent(
            "coding_agent_1",
            AgentType.CODING,
            {'learning_rate': 0.02}
        )
        
        analytical_agent = engine.register_agent(
            "analytical_agent_1",
            AgentType.ANALYTICAL,
            {'learning_rate': 0.015}
        )
        
        # Create and submit a task
        task = Task(
            task_id=str(uuid.uuid4()),
            task_type="code_analysis",
            priority=TaskPriority.HIGH,
            data={'code': 'def hello(): print("Hello")'},
            created_at=datetime.now(),
            deadline=None,
            assigned_agent=None,
            dependencies=[]
        )
        
        task_id = await engine.submit_task(task)
        result = await engine.execute_task(task)
        
        print(f"Task result: {result}")
        
        # Get statistics
        stats = await engine.get_system_statistics()
        print(f"System stats: {stats}")
        
        await engine.stop()
    
    asyncio.run(main())
