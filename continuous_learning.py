"""
YMERA Continuous Learning Engine
Enables online learning and incremental model updates
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class DriftType(Enum):
    """Types of concept drift"""
    NONE = "none"
    GRADUAL = "gradual"
    SUDDEN = "sudden"
    RECURRING = "recurring"


@dataclass
class DriftDetection:
    """Represents detected concept drift"""
    drift_type: DriftType
    confidence: float
    detected_at: datetime
    affected_features: List[str]
    severity: float  # 0.0 to 1.0
    

class ContinuousLearningEngine:
    """
    Continuous Learning Engine with concept drift detection and incremental updates
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize continuous learning engine"""
        self.config = config
        self.enabled = config.get("enabled", True)
        self.update_interval = config.get("update_interval_seconds", 300)
        self.drift_detection_enabled = config.get("drift_detection_enabled", True)
        
        # Component references (injected)
        self.learning_engine = None
        self.knowledge_base = None
        self.pattern_recognizer = None
        
        # State
        self.is_running = False
        self.update_task = None
        self.drift_history: List[DriftDetection] = []
        self.model_performance_history: List[Dict[str, float]] = []
        
        # Drift detection parameters
        self.drift_window_size = config.get("drift_window_size", 100)
        self.drift_threshold = config.get("drift_threshold", 0.3)
        
        logger.info(f"Continuous Learning Engine initialized")
    
    def set_learning_engine(self, learning_engine):
        """Inject learning engine dependency"""
        self.learning_engine = learning_engine
    
    def set_knowledge_base(self, knowledge_base):
        """Inject knowledge base dependency"""
        self.knowledge_base = knowledge_base
    
    def set_pattern_recognizer(self, pattern_recognizer):
        """Inject pattern recognizer dependency"""
        self.pattern_recognizer = pattern_recognizer
    
    async def start(self):
        """Start continuous learning"""
        if not self.enabled:
            logger.warning("Continuous learning is disabled")
            return
        
        if self.is_running:
            logger.warning("Continuous learning already running")
            return
        
        self.is_running = True
        self.update_task = asyncio.create_task(self._continuous_update_loop())
        logger.info("Continuous learning started")
    
    async def stop(self):
        """Stop continuous learning"""
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        logger.info("Continuous learning stopped")
    
    async def _continuous_update_loop(self):
        """Main continuous learning loop"""
        while self.is_running:
            try:
                await asyncio.sleep(self.update_interval)
                
                # Perform continuous learning update
                await self._perform_update()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in continuous learning loop: {str(e)}", exc_info=True)
    
    async def _perform_update(self):
        """Perform a continuous learning update cycle"""
        logger.info("Performing continuous learning update")
        
        # Check for concept drift
        if self.drift_detection_enabled:
            drift = await self._detect_drift()
            if drift and drift.drift_type != DriftType.NONE:
                logger.warning(f"Drift detected: {drift.drift_type.value} (confidence: {drift.confidence:.2f})")
                self.drift_history.append(drift)
                
                # Trigger model retraining if drift is significant
                if drift.severity > 0.7:
                    await self._handle_drift(drift)
        
        # Perform incremental update
        await self._incremental_update()
        
        # Update knowledge base with new learnings
        if self.knowledge_base:
            await self.knowledge_base.store({
                "type": "continuous_learning_update",
                "timestamp": datetime.utcnow().isoformat(),
                "drift_detections": len(self.drift_history),
                "performance_trend": self._calculate_performance_trend()
            }, category="continuous_learning")
    
    async def _detect_drift(self) -> Optional[DriftDetection]:
        """
        Detect concept drift in the data stream
        
        This implementation uses a simple statistical approach.
        In production, you might use more sophisticated methods like:
        - ADWIN (Adaptive Windowing)
        - DDM (Drift Detection Method)
        - EDDM (Early Drift Detection Method)
        - Page-Hinkley Test
        """
        if len(self.model_performance_history) < self.drift_window_size:
            return None
        
        # Get recent performance metrics
        recent_window = self.model_performance_history[-self.drift_window_size:]
        
        # Calculate statistics
        recent_performance = [p.get("accuracy", 0.0) for p in recent_window]
        current_mean = np.mean(recent_performance)
        current_std = np.std(recent_performance)
        
        # Compare with historical baseline
        if len(self.model_performance_history) > self.drift_window_size * 2:
            baseline_window = self.model_performance_history[-self.drift_window_size*2:-self.drift_window_size]
            baseline_performance = [p.get("accuracy", 0.0) for p in baseline_window]
            baseline_mean = np.mean(baseline_performance)
            
            # Detect drift using statistical test
            performance_drop = baseline_mean - current_mean
            
            if performance_drop > self.drift_threshold:
                drift_type = DriftType.SUDDEN if performance_drop > self.drift_threshold * 2 else DriftType.GRADUAL
                confidence = min(1.0, performance_drop / (self.drift_threshold * 3))
                
                return DriftDetection(
                    drift_type=drift_type,
                    confidence=confidence,
                    detected_at=datetime.utcnow(),
                    affected_features=[],  # Would need feature-level analysis
                    severity=confidence
                )
        
        return None
    
    async def _handle_drift(self, drift: DriftDetection):
        """Handle detected drift"""
        logger.info(f"Handling drift: {drift.drift_type.value}")
        
        # Strategy depends on drift type and severity
        if drift.drift_type == DriftType.SUDDEN and drift.severity > 0.8:
            # Trigger full model retraining
            logger.warning("Severe sudden drift detected - triggering full retraining")
            # In production, this would trigger a retraining pipeline
        
        elif drift.drift_type == DriftType.GRADUAL:
            # Increase learning rate for faster adaptation
            logger.info("Gradual drift detected - increasing adaptation rate")
            # Adjust incremental learning parameters
        
        # Store drift information in knowledge base
        if self.knowledge_base:
            await self.knowledge_base.store({
                "drift_type": drift.drift_type.value,
                "confidence": drift.confidence,
                "severity": drift.severity,
                "detected_at": drift.detected_at.isoformat()
            }, category="drift_detection", tags=["concept_drift", drift.drift_type.value])
    
    async def _incremental_update(self):
        """Perform incremental model update"""
        logger.debug("Performing incremental update")
        
        # In a real implementation, this would:
        # 1. Fetch recent data
        # 2. Update model incrementally
        # 3. Validate performance
        # 4. Rollback if performance degrades
        
        # Simulate performance metric
        current_performance = {
            "accuracy": 0.85 + np.random.normal(0, 0.05),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.model_performance_history.append(current_performance)
        
        # Keep history bounded
        if len(self.model_performance_history) > self.drift_window_size * 3:
            self.model_performance_history = self.model_performance_history[-self.drift_window_size * 2:]
    
    def _calculate_performance_trend(self) -> str:
        """Calculate overall performance trend"""
        if len(self.model_performance_history) < 10:
            return "insufficient_data"
        
        recent_perf = [p.get("accuracy", 0.0) for p in self.model_performance_history[-10:]]
        older_perf = [p.get("accuracy", 0.0) for p in self.model_performance_history[-20:-10]]
        
        if not older_perf:
            return "stable"
        
        recent_mean = np.mean(recent_perf)
        older_mean = np.mean(older_perf)
        
        diff = recent_mean - older_mean
        
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "degrading"
        else:
            return "stable"
    
    async def update_with_feedback(self, feedback_data: Dict[str, Any]):
        """Update models with user feedback"""
        logger.info("Updating with feedback")
        
        # In production, this would update models based on user feedback
        # For now, we just store in knowledge base
        if self.knowledge_base:
            await self.knowledge_base.store(
                feedback_data,
                category="user_feedback",
                tags=["feedback", "continuous_learning"]
            )
    
    async def get_drift_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get drift detection history"""
        recent_drifts = self.drift_history[-limit:]
        return [
            {
                "drift_type": d.drift_type.value,
                "confidence": d.confidence,
                "detected_at": d.detected_at.isoformat(),
                "severity": d.severity
            }
            for d in recent_drifts
        ]
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get continuous learning statistics"""
        return {
            "enabled": self.enabled,
            "is_running": self.is_running,
            "total_updates": len(self.model_performance_history),
            "drift_detections": len(self.drift_history),
            "performance_trend": self._calculate_performance_trend(),
            "current_performance": self.model_performance_history[-1] if self.model_performance_history else None
        }
