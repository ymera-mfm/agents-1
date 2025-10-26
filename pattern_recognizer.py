"""
Pattern Recognizer
Detects patterns in agent activities, code, and outcomes
"""

import structlog
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.utils.cache_manager import CacheManager
from ..models import InteractionLogModel, KnowledgeEntryModel, KnowledgeCategory


logger = structlog.get_logger(__name__)


class PatternRecognizer:
    """
    Pattern recognition system for detecting trends, anomalies, and insights
    """
    
    def __init__(self, db_session: AsyncSession, cache_manager: CacheManager):
        self.db = db_session
        self.cache = cache_manager
        self.pattern_templates = self._load_pattern_templates()
    
    async def detect(
        self,
        data_source: str,
        time_window: timedelta
    ) -> List[Dict[str, Any]]:
        """
        Detect patterns in specified data source
        
        Args:
            data_source: Data source (interactions, tasks, etc.)
            time_window: Time window for analysis
            
        Returns:
            List of detected patterns
        """
        try:
            patterns = []
            
            if data_source == 'interactions':
                patterns.extend(await self._detect_interaction_patterns(time_window))
            elif data_source == 'tasks':
                patterns.extend(await self._detect_task_patterns(time_window))
            elif data_source == 'knowledge':
                patterns.extend(await self._detect_knowledge_patterns(time_window))
            else:
                logger.warning(f"Unknown data source: {data_source}")
            
            # Filter by confidence
            high_confidence_patterns = [
                p for p in patterns if p.get('confidence', 0) > 0.5
            ]
            
            logger.info(f"Detected {len(high_confidence_patterns)} patterns",
                       source=data_source)
            
            return high_confidence_patterns
            
        except Exception as e:
            logger.error("Pattern detection failed", error=str(e))
            return []
    
    async def extract_patterns(
        self,
        content: str,
        category: KnowledgeCategory
    ) -> List[Dict[str, Any]]:
        """
        Extract patterns from content
        
        Args:
            content: Content to analyze
            category: Content category
            
        Returns:
            List of extracted patterns
        """
        try:
            patterns = []
            
            if category == KnowledgeCategory.CODE_PATTERNS:
                patterns.extend(self._extract_code_patterns(content))
            elif category == KnowledgeCategory.ERROR_PATTERNS:
                patterns.extend(self._extract_error_patterns(content))
            elif category == KnowledgeCategory.BEST_PRACTICES:
                patterns.extend(self._extract_practice_patterns(content))
            
            # Add general patterns
            patterns.extend(self._extract_general_patterns(content))
            
            return patterns
            
        except Exception as e:
            logger.error("Pattern extraction failed", error=str(e))
            return []
    
    async def analyze_interaction(
        self,
        interaction_type: str,
        interaction_data: Dict[str, Any],
        outcome: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Analyze interaction for patterns
        
        Args:
            interaction_type: Type of interaction
            interaction_data: Interaction details
            outcome: Interaction outcome
            
        Returns:
            List of detected patterns
        """
        try:
            patterns = []
            
            # Check for success/failure patterns
            if outcome:
                pattern = self._analyze_outcome_pattern(
                    interaction_type,
                    interaction_data,
                    outcome
                )
                if pattern:
                    patterns.append(pattern)
            
            # Check for timing patterns
            if 'duration' in interaction_data:
                timing_pattern = self._analyze_timing_pattern(
                    interaction_type,
                    interaction_data['duration']
                )
                if timing_pattern:
                    patterns.append(timing_pattern)
            
            # Check for data patterns
            data_patterns = self._analyze_data_patterns(interaction_data)
            patterns.extend(data_patterns)
            
            return patterns
            
        except Exception as e:
            logger.error("Interaction analysis failed", error=str(e))
            return []
    
    # Pattern Detection Methods
    
    async def _detect_interaction_patterns(
        self,
        time_window: timedelta
    ) -> List[Dict[str, Any]]:
        """Detect patterns in agent interactions"""
        patterns = []
        cutoff = datetime.utcnow() - time_window
        
        # Get interactions in time window
        stmt = select(InteractionLogModel).where(
            InteractionLogModel.timestamp >= cutoff
        )
        result = await self.db.execute(stmt)
        interactions = result.scalars().all()
        
        if not interactions:
            return patterns
        
        # Analyze interaction frequencies
        type_counter = Counter(i.interaction_type for i in interactions)
        
        for interaction_type, count in type_counter.items():
            if count > len(interactions) * 0.2:  # More than 20%
                patterns.append({
                    "type": "frequent_interaction",
                    "pattern_type": "frequency",
                    "interaction_type": interaction_type,
                    "frequency": count,
                    "percentage": (count / len(interactions)) * 100,
                    "confidence": 0.8,
                    "description": f"Frequent {interaction_type} interactions detected"
                })
        
        # Analyze success/failure patterns
        outcome_patterns = self._analyze_outcomes(interactions)
        patterns.extend(outcome_patterns)
        
        # Analyze temporal patterns
        temporal_patterns = self._analyze_temporal_patterns(interactions)
        patterns.extend(temporal_patterns)
        
        # Analyze agent collaboration patterns
        collab_patterns = self._analyze_collaboration_patterns(interactions)
        patterns.extend(collab_patterns)
        
        return patterns
    
    async def _detect_task_patterns(
        self,
        time_window: timedelta
    ) -> List[Dict[str, Any]]:
        """Detect patterns in task execution"""
        patterns = []
        
        # This would query task data
        # Implementation depends on task storage
        
        return patterns
    
    async def _detect_knowledge_patterns(
        self,
        time_window: timedelta
    ) -> List[Dict[str, Any]]:
        """Detect patterns in knowledge usage"""
        patterns = []
        cutoff = datetime.utcnow() - time_window
        
        # Get recently accessed knowledge
        stmt = select(KnowledgeEntryModel).where(
            and_(
                KnowledgeEntryModel.last_accessed_at >= cutoff,
                KnowledgeEntryModel.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(stmt)
        entries = result.scalars().all()
        
        if not entries:
            return patterns
        
        # Analyze category trends
        category_counter = Counter(e.category for e in entries)
        
        for category, count in category_counter.most_common(3):
            patterns.append({
                "type": "knowledge_trend",
                "pattern_type": "usage",
                "category": category,
                "access_count": count,
                "confidence": 0.7,
                "description": f"High interest in {category} knowledge"
            })
        
        # Analyze tag trends
        all_tags = []
        for entry in entries:
            if entry.tags:
                all_tags.extend(entry.tags)
        
        if all_tags:
            tag_counter = Counter(all_tags)
            trending_tags = tag_counter.most_common(5)
            
            patterns.append({
                "type": "trending_topics",
                "pattern_type": "tags",
                "trending_tags": [{"tag": tag, "count": count} for tag, count in trending_tags],
                "confidence": 0.75,
                "description": "Trending topics identified"
            })
        
        return patterns
    
    # Pattern Extraction Methods
    
    def _extract_code_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Extract code patterns"""
        patterns = []
        
        # Detect common code structures
        if 'class ' in content:
            class_pattern = {
                "type": "code_structure",
                "pattern_type": "class_definition",
                "confidence": 0.9,
                "description": "Class definition pattern"
            }
            patterns.append(class_pattern)
        
        if 'def ' in content or 'function ' in content:
            function_pattern = {
                "type": "code_structure",
                "pattern_type": "function_definition",
                "confidence": 0.9,
                "description": "Function definition pattern"
            }
            patterns.append(function_pattern)
        
        # Detect design patterns
        design_patterns = self._detect_design_patterns(content)
        patterns.extend(design_patterns)
        
        # Detect API usage patterns
        api_patterns = self._detect_api_patterns(content)
        patterns.extend(api_patterns)
        
        return patterns
    
    def _extract_error_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Extract error patterns"""
        patterns = []
        
        # Common error indicators
        error_keywords = [
            'error', 'exception', 'failed', 'timeout',
            'null', 'undefined', 'crash'
        ]
        
        content_lower = content.lower()
        detected_errors = [kw for kw in error_keywords if kw in content_lower]
        
        if detected_errors:
            patterns.append({
                "type": "error_pattern",
                "pattern_type": "error_indicators",
                "keywords": detected_errors,
                "confidence": 0.7,
                "description": "Common error indicators detected"
            })
        
        # Extract stack trace patterns
        if 'traceback' in content_lower or 'stack trace' in content_lower:
            patterns.append({
                "type": "error_pattern",
                "pattern_type": "stack_trace",
                "confidence": 0.85,
                "description": "Stack trace pattern detected"
            })
        
        return patterns
    
    def _extract_practice_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Extract best practice patterns"""
        patterns = []
        
        # Best practice indicators
        practice_keywords = [
            'best practice', 'recommended', 'should',
            'guideline', 'convention', 'standard'
        ]
        
        content_lower = content.lower()
        detected_practices = [kw for kw in practice_keywords if kw in content_lower]
        
        if detected_practices:
            patterns.append({
                "type": "best_practice",
                "pattern_type": "practice_indicators",
                "keywords": detected_practices,
                "confidence": 0.75,
                "description": "Best practice indicators detected"
            })
        
        return patterns
    
    def _extract_general_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Extract general patterns"""
        patterns = []
        
        # Detect lists/sequences
        if re.search(r'(\d+\.|[\*\-]\s)', content):
            patterns.append({
                "type": "structure",
                "pattern_type": "list",
                "confidence": 0.6,
                "description": "List structure detected"
            })
        
        # Detect code blocks
        if '```' in content or '    ' in content[:50]:
            patterns.append({
                "type": "structure",
                "pattern_type": "code_block",
                "confidence": 0.8,
                "description": "Code block detected"
            })
        
        return patterns
    
    def _detect_design_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Detect design patterns in code"""
        patterns = []
        
        design_pattern_indicators = {
            'singleton': ['__instance', 'getInstance', '_instance = None'],
            'factory': ['create', 'Factory', 'Builder'],
            'observer': ['subscribe', 'notify', 'Observer', 'listener'],
            'strategy': ['Strategy', 'algorithm', 'execute'],
            'decorator': ['@', 'wrapper', 'Decorator']
        }
        
        content_lower = content.lower()
        
        for pattern_name, indicators in design_pattern_indicators.items():
            if any(ind.lower() in content_lower for ind in indicators):
                patterns.append({
                    "type": "design_pattern",
                    "pattern_type": pattern_name,
                    "confidence": 0.6,
                    "description": f"{pattern_name.capitalize()} pattern detected"
                })
        
        return patterns
    
    def _detect_api_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Detect API usage patterns"""
        patterns = []
        
        # HTTP method patterns
        http_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        for method in http_methods:
            if method in content:
                patterns.append({
                    "type": "api_pattern",
                    "pattern_type": "http_method",
                    "method": method,
                    "confidence": 0.7,
                    "description": f"HTTP {method} usage detected"
                })
        
        # REST API patterns
        if '/api/' in content or re.search(r'/v\d+/', content):
            patterns.append({
                "type": "api_pattern",
                "pattern_type": "rest_api",
                "confidence": 0.8,
                "description": "REST API pattern detected"
            })
        
        return patterns
    
    # Analysis Methods
    
    def _analyze_outcomes(
        self,
        interactions: List[InteractionLogModel]
    ) -> List[Dict[str, Any]]:
        """Analyze interaction outcomes"""
        patterns = []
        
        # Group by interaction type and outcome
        type_outcomes = defaultdict(lambda: {'success': 0, 'failure': 0})
        
        for interaction in interactions:
            if interaction.success is not None:
                itype = interaction.interaction_type
                if interaction.success:
                    type_outcomes[itype]['success'] += 1
                else:
                    type_outcomes[itype]['failure'] += 1
        
        # Identify patterns
        for itype, outcomes in type_outcomes.items():
            total = outcomes['success'] + outcomes['failure']
            if total > 5:  # Minimum sample size
                success_rate = outcomes['success'] / total
                
                if success_rate < 0.5:
                    patterns.append({
                        "type": "outcome_pattern",
                        "pattern_type": "high_failure_rate",
                        "interaction_type": itype,
                        "failure_rate": (1 - success_rate) * 100,
                        "sample_size": total,
                        "confidence": 0.75,
                        "description": f"High failure rate for {itype}"
                    })
                elif success_rate > 0.9:
                    patterns.append({
                        "type": "outcome_pattern",
                        "pattern_type": "high_success_rate",
                        "interaction_type": itype,
                        "success_rate": success_rate * 100,
                        "sample_size": total,
                        "confidence": 0.8,
                        "description": f"High success rate for {itype}"
                    })
        
        return patterns
    
    def _analyze_temporal_patterns(
        self,
        interactions: List[InteractionLogModel]
    ) -> List[Dict[str, Any]]:
        """Analyze temporal patterns"""
        patterns = []
        
        # Group by hour
        hourly_counts = defaultdict(int)
        for interaction in interactions:
            hour = interaction.timestamp.hour
            hourly_counts[hour] += 1
        
        if hourly_counts:
            # Find peak hours
            max_count = max(hourly_counts.values())
            peak_hours = [h for h, c in hourly_counts.items() if c == max_count]
            
            patterns.append({
                "type": "temporal_pattern",
                "pattern_type": "peak_hours",
                "peak_hours": peak_hours,
                "peak_count": max_count,
                "confidence": 0.7,
                "description": f"Peak activity at hours: {', '.join(map(str, peak_hours))}"
            })
        
        return patterns
    
    def _analyze_collaboration_patterns(
        self,
        interactions: List[InteractionLogModel]
    ) -> List[Dict[str, Any]]:
        """Analyze agent collaboration patterns"""
        patterns = []
        
        # Build collaboration graph
        collaborations = defaultdict(int)
        
        for interaction in interactions:
            if interaction.target_agent_id:
                pair = tuple(sorted([
                    interaction.source_agent_id,
                    interaction.target_agent_id
                ]))
                collaborations[pair] += 1
        
        # Find frequent collaborations
        if collaborations:
            total_interactions = len(interactions)
            frequent_collabs = [
                (pair, count) 
                for pair, count in collaborations.items()
                if count > total_interactions * 0.1
            ]
            
            if frequent_collabs:
                patterns.append({
                    "type": "collaboration_pattern",
                    "pattern_type": "frequent_pairs",
                    "collaborations": [
                        {
                            "agents": list(pair),
                            "interaction_count": count
                        }
                        for pair, count in frequent_collabs
                    ],
                    "confidence": 0.75,
                    "description": "Frequent agent collaborations detected"
                })
        
        return patterns
    
    def _analyze_outcome_pattern(
        self,
        interaction_type: str,
        interaction_data: Dict[str, Any],
        outcome: str
    ) -> Optional[Dict[str, Any]]:
        """Analyze specific outcome pattern"""
        # Determine if outcome is success or failure
        is_success = self._is_successful_outcome(outcome)
        
        return {
            "type": "outcome",
            "pattern_type": "success" if is_success else "failure",
            "interaction_type": interaction_type,
            "outcome": outcome,
            "confidence": 0.7,
            "description": f"{'Successful' if is_success else 'Failed'} {interaction_type}"
        }
    
    def _analyze_timing_pattern(
        self,
        interaction_type: str,
        duration: int
    ) -> Optional[Dict[str, Any]]:
        """Analyze timing patterns"""
        # Classify duration
        if duration > 5000:  # > 5 seconds
            return {
                "type": "timing",
                "pattern_type": "slow_operation",
                "interaction_type": interaction_type,
                "duration_ms": duration,
                "confidence": 0.75,
                "description": f"Slow {interaction_type} operation detected"
            }
        elif duration < 100:  # < 100ms
            return {
                "type": "timing",
                "pattern_type": "fast_operation",
                "interaction_type": interaction_type,
                "duration_ms": duration,
                "confidence": 0.7,
                "description": f"Fast {interaction_type} operation"
            }
        
        return None
    
    def _analyze_data_patterns(
        self,
        interaction_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze data patterns in interaction"""
        patterns = []
        
        # Check for large payloads
        data_str = json.dumps(interaction_data)
        if len(data_str) > 10000:  # > 10KB
            patterns.append({
                "type": "data_pattern",
                "pattern_type": "large_payload",
                "size_bytes": len(data_str),
                "confidence": 0.8,
                "description": "Large data payload detected"
            })
        
        # Check for specific data structures
        if 'error' in interaction_data or 'exception' in interaction_data:
            patterns.append({
                "type": "data_pattern",
                "pattern_type": "error_data",
                "confidence": 0.85,
                "description": "Error data present in interaction"
            })
        
        return patterns
    
    # Utility Methods
    
    def _is_successful_outcome(self, outcome: str) -> bool:
        """Determine if outcome indicates success"""
        success_keywords = ['success', 'completed', 'done', 'ok', 'passed']
        failure_keywords = ['error', 'failed', 'timeout', 'exception']
        
        outcome_lower = outcome.lower()
        
        if any(kw in outcome_lower for kw in success_keywords):
            return True
        if any(kw in outcome_lower for kw in failure_keywords):
            return False
        
        # Default to success if unclear
        return True
    
    def _load_pattern_templates(self) -> Dict[str, Any]:
        """Load pattern recognition templates"""
        return {
            "code_patterns": {
                "class": r"class\s+\w+",
                "function": r"def\s+\w+|function\s+\w+",
                "import": r"import\s+\w+|from\s+\w+"
            },
            "error_patterns": {
                "exception": r"Exception|Error",
                "traceback": r"Traceback|Stack trace"
            }
        }
