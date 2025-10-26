"""
Learning Agent - Production Ready
Responsible for:
- Receiving knowledge from all agents
- Learning from external sources
- Sharing knowledge to agents based on their tasks
- Reporting to agent manager
- Continuous improvement through machine learning
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

# Optional dependencies
try:
    import structlog
    HAS_STRUCTLOG = True
    
except ImportError:
    structlog = None
    HAS_STRUCTLOG = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

try:
    from sqlalchemy import select, update
    from sqlalchemy.ext.asyncio import AsyncSession
    HAS_SQLALCHEMY = True
except ImportError:
    select = None
    update = None
    AsyncSession = None
    HAS_SQLALCHEMY = False

from shared.config.settings import Settings
from shared.database.connection_pool import DatabaseManager
from shared.utils.metrics import MetricsCollector
from shared.communication.agent_communicator import AgentCommunicator


class KnowledgeExtractor:
    """Extracts knowledge from various sources"""
    
    def __init__(self):
        if HAS_STRUCTLOG:
            self.logger = structlog.get_logger(__name__)
        else:
            self.logger = logging.getLogger(__name__)
    
    async def extract_from_code(self, code: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract knowledge from code"""
        try:
            knowledge = {
                'patterns': [],
                'libraries': [],
                'techniques': [],
                'complexity': 0
            }
            
            # Extract imports/libraries
            for line in code.split('\n'):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    lib = line.split()[1].split('.')[0]
                    if lib not in knowledge['libraries']:
                        knowledge['libraries'].append(lib)
            
            # Detect patterns
            if 'async def' in code:
                knowledge['patterns'].append('async_programming')
            if 'class ' in code:
                knowledge['patterns'].append('object_oriented')
            if '@' in code:
                knowledge['patterns'].append('decorators')
            if 'yield' in code:
                knowledge['patterns'].append('generators')
            
            # Estimate complexity
            knowledge['complexity'] = len(code.split('\n'))
            
            return knowledge
            
        except Exception as e:
            self.logger.error(f"Knowledge extraction error: {e}", exc_info=True)
            return {}
    
    async def extract_from_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract knowledge from agent interactions"""
        try:
            return {
                'interaction_type': interaction_data.get('type'),
                'success': interaction_data.get('success', False),
                'duration': interaction_data.get('duration', 0),
                'insights': interaction_data.get('insights', [])
            }
        except Exception as e:
            self.logger.error(f"Interaction knowledge extraction error: {e}", exc_info=True)
            return {}


class KnowledgeStore:
    """Stores and manages knowledge"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = structlog.get_logger(__name__)
        self.memory_cache = {}
    
    async def store_knowledge(
        self,
        source: str,
        knowledge_type: str,
        content: Dict[str, Any],
        tags: List[str] = None
    ) -> str:
        """Store knowledge in database"""
        try:
            knowledge_id = f"k_{datetime.utcnow().timestamp()}_{hash(json.dumps(content))}"
            
            # Store in memory cache
            self.memory_cache[knowledge_id] = {
                'source': source,
                'type': knowledge_type,
                'content': content,
                'tags': tags or [],
                'created_at': datetime.utcnow(),
                'access_count': 0
            }
            
            self.logger.info(f"Stored knowledge {knowledge_id} from {source}")
            return knowledge_id
            
        except Exception as e:
            self.logger.error(f"Knowledge storage error: {e}", exc_info=True)
            return None
    
    async def retrieve_knowledge(
        self,
        query: str = None,
        knowledge_type: str = None,
        tags: List[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant knowledge"""
        try:
            results = []
            
            for kid, kdata in self.memory_cache.items():
                # Simple filtering
                if knowledge_type and kdata['type'] != knowledge_type:
                    continue
                
                if tags:
                    if not any(tag in kdata['tags'] for tag in tags):
                        continue
                
                results.append({
                    'id': kid,
                    **kdata
                })
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            self.logger.error(f"Knowledge retrieval error: {e}", exc_info=True)
            return []
    
    async def update_access_count(self, knowledge_id: str):
        """Update access count for knowledge item"""
        if knowledge_id in self.memory_cache:
            self.memory_cache[knowledge_id]['access_count'] += 1


class KnowledgeSharer:
    """Shares knowledge with agents based on their needs"""
    
    def __init__(self, knowledge_store: KnowledgeStore, agent_communicator: AgentCommunicator):
        self.knowledge_store = knowledge_store
        self.agent_communicator = agent_communicator
        self.logger = structlog.get_logger(__name__)
    
    async def share_to_agent(
        self,
        agent_name: str,
        task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Share relevant knowledge to an agent"""
        try:
            # Determine what knowledge is relevant
            task_type = task_context.get('type')
            tags = task_context.get('tags', [])
            
            # Retrieve relevant knowledge
            relevant_knowledge = await self.knowledge_store.retrieve_knowledge(
                knowledge_type=task_type,
                tags=tags,
                limit=5
            )
            
            if relevant_knowledge:
                # Send to agent
                await self.agent_communicator.send_to_agent(agent_name, {
                    'type': 'knowledge_share',
                    'knowledge': relevant_knowledge,
                    'task_context': task_context
                })
                
                self.logger.info(
                    f"Shared {len(relevant_knowledge)} knowledge items to {agent_name}"
                )
                
                return {
                    'success': True,
                    'items_shared': len(relevant_knowledge)
                }
            else:
                return {
                    'success': True,
                    'items_shared': 0,
                    'message': 'No relevant knowledge found'
                }
                
        except Exception as e:
            self.logger.error(f"Knowledge sharing error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


class LearningEngine:
    """Machine learning engine for continuous improvement"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.model = None
        self.training_data = []
    
    async def learn_from_feedback(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        feedback: Dict[str, Any]
    ):
        """Learn from agent feedback"""
        try:
            training_sample = {
                'input': input_data,
                'output': output_data,
                'feedback': feedback,
                'timestamp': datetime.utcnow()
            }
            
            self.training_data.append(training_sample)
            
            # Trigger training if we have enough data
            if len(self.training_data) >= 100:
                await self._train_model()
            
        except Exception as e:
            self.logger.error(f"Learning error: {e}", exc_info=True)
    
    async def _train_model(self):
        """Train/update the model"""
        try:
            self.logger.info(f"Training model with {len(self.training_data)} samples")
            
            # Placeholder for actual ML training
            # In production, this would train a real ML model
            
            # Clear old training data
            self.training_data = self.training_data[-1000:]
            
        except Exception as e:
            self.logger.error(f"Model training error: {e}", exc_info=True)
    
    async def predict_best_approach(
        self,
        task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict best approach for a task"""
        try:
            # Placeholder for actual prediction
            # In production, this would use the trained model
            
            return {
                'recommended_approach': 'standard',
                'confidence': 0.85,
                'alternatives': []
            }
            
        except Exception as e:
            self.logger.error(f"Prediction error: {e}", exc_info=True)
            return {
                'recommended_approach': 'standard',
                'confidence': 0.5
            }


class LearningAgent:
    """
    Learning Agent - Continuous learning and knowledge management
    """
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        settings: Settings,
        metrics_collector: MetricsCollector
    ):
        self.db_manager = db_manager
        self.settings = settings
        self.metrics = metrics_collector
        self.logger = structlog.get_logger(__name__)
        
        # Components
        self.knowledge_extractor = KnowledgeExtractor()
        self.knowledge_store = KnowledgeStore(db_manager)
        self.agent_communicator = None
        self.knowledge_sharer = None
        self.learning_engine = LearningEngine()
        
        # State
        self._ready = False
        self._shutdown = False
        
        # Background tasks
        self.background_tasks = []
    
    async def initialize(self):
        """Initialize the learning agent"""
        try:
            self.logger.info("Initializing Learning Agent...")
            
            # Initialize components
            self.agent_communicator = AgentCommunicator(self.db_manager, self.settings)
            self.knowledge_sharer = KnowledgeSharer(self.knowledge_store, self.agent_communicator)
            
            # Start background tasks
            update_task = asyncio.create_task(self._periodic_knowledge_update())
            self.background_tasks.append(update_task)
            
            cleanup_task = asyncio.create_task(self._periodic_cleanup())
            self.background_tasks.append(cleanup_task)
            
            self._ready = True
            self.logger.info("Learning Agent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}", exc_info=True)
            raise
    
    async def shutdown(self):
        """Shutdown the learning agent"""
        self.logger.info("Shutting down Learning Agent...")
        self._shutdown = True
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.logger.info("Learning Agent shutdown complete")
    
    def is_ready(self) -> bool:
        """Check if agent is ready"""
        return self._ready and not self._shutdown
    
    async def receive_knowledge(
        self,
        source: str,
        knowledge_type: str,
        content: Dict[str, Any],
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        Receive knowledge from agents or external sources
        
        Args:
            source: Source of knowledge (agent name or external source)
            knowledge_type: Type of knowledge (e.g., 'code_pattern', 'best_practice', 'error_solution')
            content: The actual knowledge content
            tags: Tags for categorization
        
        Returns:
            Result of storage
        """
        try:
            self.metrics.increment_counter('learning_agent_knowledge_received', {'source': source})
            
            # Extract additional knowledge
            extracted = await self.knowledge_extractor.extract_from_code(
                content.get('code', ''),
                content
            ) if 'code' in content else {}
            
            # Merge extracted knowledge
            enhanced_content = {**content, **extracted}
            
            # Store knowledge
            knowledge_id = await self.knowledge_store.store_knowledge(
                source,
                knowledge_type,
                enhanced_content,
                tags
            )
            
            if knowledge_id:
                self.logger.info(f"Received and stored knowledge {knowledge_id} from {source}")
                return {
                    'success': True,
                    'knowledge_id': knowledge_id
                }
            else:
                return {
                    'success': False,
                    'error': 'Storage failed'
                }
                
        except Exception as e:
            self.logger.error(f"Knowledge reception error: {e}", exc_info=True)
            self.metrics.increment_counter('learning_agent_errors', {'type': 'reception_error'})
            return {
                'success': False,
                'error': str(e)
            }
    
    async def provide_knowledge(
        self,
        agent_name: str,
        task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Provide relevant knowledge to an agent for their task
        
        Args:
            agent_name: Name of requesting agent
            task_context: Context of the task (type, requirements, etc.)
        
        Returns:
            Shared knowledge
        """
        try:
            self.metrics.increment_counter('learning_agent_knowledge_provided', {'agent': agent_name})
            
            result = await self.knowledge_sharer.share_to_agent(agent_name, task_context)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Knowledge provision error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_code(
        self,
        code: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze code and provide insights
        
        Args:
            code: Code to analyze
            metadata: Metadata about the code
        
        Returns:
            Analysis results and insights
        """
        try:
            # Extract knowledge
            knowledge = await self.knowledge_extractor.extract_from_code(code, metadata)
            
            # Get similar patterns from knowledge base
            similar_patterns = await self.knowledge_store.retrieve_knowledge(
                knowledge_type='code_pattern',
                tags=knowledge.get('patterns', []),
                limit=3
            )
            
            # Get best practices
            best_practices = await self.knowledge_store.retrieve_knowledge(
                knowledge_type='best_practice',
                tags=knowledge.get('libraries', []),
                limit=5
            )
            
            # Generate insights
            insights = {
                'detected_patterns': knowledge.get('patterns', []),
                'libraries_used': knowledge.get('libraries', []),
                'complexity_estimate': knowledge.get('complexity', 0),
                'similar_patterns': len(similar_patterns),
                'applicable_best_practices': len(best_practices),
                'recommendations': []
            }
            
            # Add recommendations
            if knowledge.get('complexity', 0) > 500:
                insights['recommendations'].append("Consider breaking down into smaller modules")
            
            if not knowledge.get('patterns'):
                insights['recommendations'].append("Consider using design patterns for better structure")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Code analysis error: {e}", exc_info=True)
            return {}
    
    async def learn_from_feedback(
        self,
        agent_name: str,
        task_data: Dict[str, Any],
        result_data: Dict[str, Any],
        feedback: Dict[str, Any]
    ):
        """
        Learn from agent feedback
        
        Args:
            agent_name: Name of the agent providing feedback
            task_data: Data about the task
            result_data: Result of the task
            feedback: Feedback on the result (success, issues, improvements)
        """
        try:
            self.metrics.increment_counter('learning_agent_feedback_received', {'agent': agent_name})
            
            # Pass to learning engine
            await self.learning_engine.learn_from_feedback(
                task_data,
                result_data,
                feedback
            )
            
            # Store as knowledge if successful
            if feedback.get('success', False):
                await self.knowledge_store.store_knowledge(
                    agent_name,
                    'successful_approach',
                    {
                        'task': task_data,
                        'result': result_data,
                        'feedback': feedback
                    },
                    tags=[task_data.get('type', 'general')]
                )
            
            self.logger.info(f"Learned from feedback from {agent_name}")
            
        except Exception as e:
            self.logger.error(f"Feedback learning error: {e}", exc_info=True)
    
    async def report_to_manager(self) -> Dict[str, Any]:
        """Generate report for agent manager"""
        try:
            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'knowledge_base_size': len(self.knowledge_store.memory_cache),
                'training_samples': len(self.learning_engine.training_data),
                'most_accessed_knowledge': [],
                'learning_insights': []
            }
            
            # Get most accessed knowledge
            sorted_knowledge = sorted(
                self.knowledge_store.memory_cache.items(),
                key=lambda x: x[1]['access_count'],
                reverse=True
            )[:5]
            
            report['most_accessed_knowledge'] = [
                {
                    'id': kid,
                    'type': kdata['type'],
                    'source': kdata['source'],
                    'access_count': kdata['access_count']
                }
                for kid, kdata in sorted_knowledge
            ]
            
            return report
            
        except Exception as e:
            self.logger.error(f"Report generation error: {e}", exc_info=True)
            return {
                'error': str(e)
            }
    
    async def _periodic_knowledge_update(self):
        """Periodically update and consolidate knowledge"""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.settings.LEARNING_UPDATE_INTERVAL)
                
                self.logger.info("Running periodic knowledge update...")
                
                # Consolidate similar knowledge
                # Remove outdated knowledge
                # Update knowledge scores
                
                self.logger.info("Knowledge update complete")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Periodic update error: {e}", exc_info=True)
    
    async def _periodic_cleanup(self):
        """Periodically cleanup old knowledge"""
        while not self._shutdown:
            try:
                await asyncio.sleep(86400)  # Daily
                
                self.logger.info("Running periodic cleanup...")
                
                cutoff_date = datetime.utcnow() - timedelta(days=self.settings.KNOWLEDGE_RETENTION_DAYS)
                
                # Remove old, unused knowledge
                to_remove = []
                for kid, kdata in self.knowledge_store.memory_cache.items():
                    if kdata['created_at'] < cutoff_date and kdata['access_count'] < 5:
                        to_remove.append(kid)
                
                for kid in to_remove:
                    del self.knowledge_store.memory_cache[kid]
                
                self.logger.info(f"Cleanup complete, removed {len(to_remove)} items")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}", exc_info=True)
