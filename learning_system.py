"""
Unified Learning System - Production Ready
Integrates all learning components into a cohesive system
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LearningTaskType(Enum):
    """Types of learning tasks"""
    PATTERN_RECOGNITION = "pattern_recognition"
    KNOWLEDGE_EXTRACTION = "knowledge_extraction"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    CONTINUOUS_LEARNING = "continuous_learning"
    EXTERNAL_LEARNING = "external_learning"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"


class PatternType(Enum):
    """Types of patterns"""
    SEQUENTIAL = "sequential"
    STRUCTURAL = "structural"
    BEHAVIORAL = "behavioral"
    TEMPORAL = "temporal"


class EntityType(Enum):
    """Types of knowledge entities"""
    CONCEPT = "concept"
    FACT = "fact"
    PROCEDURE = "procedure"
    PATTERN = "pattern"


class RelationType(Enum):
    """Types of relationships"""
    IS_A = "is_a"
    HAS_A = "has_a"
    USES = "uses"
    RELATED_TO = "related_to"


@dataclass
class LearningResult:
    """Result of a learning operation"""
    success: bool
    task_type: LearningTaskType
    data: Any
    metrics: Dict[str, float]
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class UnifiedLearningSystem:
    """
    Unified Learning System - Orchestrates all learning capabilities
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the unified learning system"""
        self.config = config
        self.components = {}
        self.initialized = False
        
        logger.info("Initializing Unified Learning System...")
    
    async def initialize(self):
        """Initialize all learning components"""
        try:
            # Import and initialize components dynamically
            self._initialize_pattern_recognition()
            self._initialize_knowledge_base()
            self._initialize_continuous_learning()
            self._initialize_external_learning()
            
            self.initialized = True
            logger.info("Unified Learning System initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize learning system: {e}", exc_info=True)
            raise
    
    def _initialize_pattern_recognition(self):
        """Initialize pattern recognition component"""
        try:
            from .pattern_recognition import PatternRecognizer
            self.components['pattern_recognition'] = PatternRecognizer(self.config)
            logger.info("Pattern recognition initialized")
        except ImportError as e:
            logger.warning(f"Pattern recognition not available: {e}")
            self.components['pattern_recognition'] = None
    
    def _initialize_knowledge_base(self):
        """Initialize knowledge base component"""
        try:
            from .knowledge_base import KnowledgeBase
            self.components['knowledge_base'] = KnowledgeBase(self.config)
            logger.info("Knowledge base initialized")
        except ImportError as e:
            logger.warning(f"Knowledge base not available: {e}")
            self.components['knowledge_base'] = None
    
    def _initialize_continuous_learning(self):
        """Initialize continuous learning component"""
        try:
            from .continuous_learning import ContinuousLearner
            self.components['continuous_learning'] = ContinuousLearner(self.config)
            logger.info("Continuous learning initialized")
        except ImportError as e:
            logger.warning(f"Continuous learning not available: {e}")
            self.components['continuous_learning'] = None
    
    def _initialize_external_learning(self):
        """Initialize external learning component"""
        try:
            from .external_learning import ExternalLearner
            self.components['external_learning'] = ExternalLearner(self.config)
            logger.info("External learning initialized")
        except ImportError as e:
            logger.warning(f"External learning not available: {e}")
            self.components['external_learning'] = None
    
    async def learn_from_data(self, data: Dict[str, Any], task_type: LearningTaskType) -> LearningResult:
        """
        Learn from provided data
        
        Args:
            data: Data to learn from
            task_type: Type of learning task
            
        Returns:
            LearningResult with outcomes
        """
        if not self.initialized:
            return LearningResult(
                success=False,
                task_type=task_type,
                data=None,
                metrics={},
                error="Learning system not initialized"
            )
        
        try:
            if task_type == LearningTaskType.PATTERN_RECOGNITION:
                return await self._recognize_patterns(data)
            elif task_type == LearningTaskType.KNOWLEDGE_EXTRACTION:
                return await self._extract_knowledge(data)
            elif task_type == LearningTaskType.CONTINUOUS_LEARNING:
                return await self._continuous_learn(data)
            elif task_type == LearningTaskType.EXTERNAL_LEARNING:
                return await self._external_learn(data)
            else:
                return LearningResult(
                    success=False,
                    task_type=task_type,
                    data=None,
                    metrics={},
                    error=f"Unsupported task type: {task_type}"
                )
                
        except Exception as e:
            logger.error(f"Learning failed: {e}", exc_info=True)
            return LearningResult(
                success=False,
                task_type=task_type,
                data=None,
                metrics={},
                error=str(e)
            )
    
    async def _recognize_patterns(self, data: Dict[str, Any]) -> LearningResult:
        """Recognize patterns in data"""
        component = self.components.get('pattern_recognition')
        if not component:
            return LearningResult(
                success=False,
                task_type=LearningTaskType.PATTERN_RECOGNITION,
                data=None,
                metrics={},
                error="Pattern recognition component not available"
            )
        
        try:
            patterns = await component.recognize(data)
            return LearningResult(
                success=True,
                task_type=LearningTaskType.PATTERN_RECOGNITION,
                data=patterns,
                metrics={'patterns_found': len(patterns)}
            )
        except Exception as e:
            return LearningResult(
                success=False,
                task_type=LearningTaskType.PATTERN_RECOGNITION,
                data=None,
                metrics={},
                error=str(e)
            )
    
    async def _extract_knowledge(self, data: Dict[str, Any]) -> LearningResult:
        """Extract knowledge from data"""
        component = self.components.get('knowledge_base')
        if not component:
            return LearningResult(
                success=False,
                task_type=LearningTaskType.KNOWLEDGE_EXTRACTION,
                data=None,
                metrics={},
                error="Knowledge base component not available"
            )
        
        try:
            knowledge = await component.extract(data)
            return LearningResult(
                success=True,
                task_type=LearningTaskType.KNOWLEDGE_EXTRACTION,
                data=knowledge,
                metrics={'entities_extracted': len(knowledge.get('entities', []))}
            )
        except Exception as e:
            return LearningResult(
                success=False,
                task_type=LearningTaskType.KNOWLEDGE_EXTRACTION,
                data=None,
                metrics={},
                error=str(e)
            )
    
    async def _continuous_learn(self, data: Dict[str, Any]) -> LearningResult:
        """Perform continuous learning"""
        component = self.components.get('continuous_learning')
        if not component:
            return LearningResult(
                success=False,
                task_type=LearningTaskType.CONTINUOUS_LEARNING,
                data=None,
                metrics={},
                error="Continuous learning component not available"
            )
        
        try:
            result = await component.learn(data)
            return LearningResult(
                success=True,
                task_type=LearningTaskType.CONTINUOUS_LEARNING,
                data=result,
                metrics=result.get('metrics', {})
            )
        except Exception as e:
            return LearningResult(
                success=False,
                task_type=LearningTaskType.CONTINUOUS_LEARNING,
                data=None,
                metrics={},
                error=str(e)
            )
    
    async def _external_learn(self, data: Dict[str, Any]) -> LearningResult:
        """Learn from external sources"""
        component = self.components.get('external_learning')
        if not component:
            return LearningResult(
                success=False,
                task_type=LearningTaskType.EXTERNAL_LEARNING,
                data=None,
                metrics={},
                error="External learning component not available"
            )
        
        try:
            result = await component.learn(data)
            return LearningResult(
                success=True,
                task_type=LearningTaskType.EXTERNAL_LEARNING,
                data=result,
                metrics=result.get('metrics', {})
            )
        except Exception as e:
            return LearningResult(
                success=False,
                task_type=LearningTaskType.EXTERNAL_LEARNING,
                data=None,
                metrics={},
                error=str(e)
            )
    
    async def retrieve_knowledge(self, query: str, entity_type: Optional[EntityType] = None) -> Dict[str, Any]:
        """
        Retrieve knowledge from knowledge base
        
        Args:
            query: Search query
            entity_type: Optional entity type filter
            
        Returns:
            Dictionary with retrieved knowledge
        """
        component = self.components.get('knowledge_base')
        if not component:
            return {'success': False, 'error': 'Knowledge base not available'}
        
        try:
            results = await component.query(query, entity_type)
            return {'success': True, 'results': results}
        except Exception as e:
            logger.error(f"Knowledge retrieval failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def shutdown(self):
        """Shutdown all learning components"""
        logger.info("Shutting down Unified Learning System...")
        
        for name, component in self.components.items():
            if component and hasattr(component, 'shutdown'):
                try:
                    await component.shutdown()
                    logger.info(f"Shutdown {name}")
                except Exception as e:
                    logger.error(f"Error shutting down {name}: {e}")
        
        self.initialized = False
        logger.info("Unified Learning System shutdown complete")


def create_unified_learning_system(config: Dict[str, Any]) -> UnifiedLearningSystem:
    """Factory function to create unified learning system"""
    return UnifiedLearningSystem(config)
