"""
YMERA Enhanced Pattern Recognition Engine
Robust pattern detection, analysis, and evolution tracking with real implementations.
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import hashlib

logger = logging.getLogger("ymera.pattern_recognition")


class PatternType(Enum):
    """Types of patterns that can be detected"""
    TEMPORAL = "temporal"
    BEHAVIORAL = "behavioral"
    ANOMALY = "anomaly"
    SEQUENTIAL = "sequential"
    CYCLICAL = "cyclical"
    CORRELATION = "correlation"


@dataclass
class Pattern:
    """Represents a detected pattern"""
    pattern_id: str
    pattern_type: PatternType
    confidence: float
    description: str
    detected_at: datetime = field(default_factory=datetime.utcnow)
    frequency: int = 1
    last_seen: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "confidence": self.confidence,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "frequency": self.frequency,
            "last_seen": self.last_seen.isoformat(),
            "metadata": self.metadata
        }


class PatternRecognitionEngine:
    """
    Enhanced Pattern Recognition Engine with robust implementations for
    temporal, behavioral, and anomaly detection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Pattern Recognition Engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.patterns: Dict[str, Pattern] = {}
        self.event_history: deque = deque(maxlen=config.get("history_size", 10000))
        self.temporal_window = config.get("temporal_window_seconds", 3600)
        self.anomaly_threshold = config.get("anomaly_threshold", 2.5)  # Z-score threshold
        
        # Statistics for anomaly detection
        self.metric_stats: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            "mean": 0.0,
            "std": 0.0,
            "count": 0,
            "sum": 0.0,
            "sum_sq": 0.0
        })
        
        logger.info(f"Pattern Recognition Engine initialized with config: {config}")
    
    async def detect_patterns(self, event: Dict[str, Any]) -> List[Pattern]:
        """
        Detect patterns in an event.
        
        Args:
            event: Event data to analyze
            
        Returns:
            List of detected patterns
        """
        # Add event to history
        event["timestamp"] = datetime.utcnow()
        self.event_history.append(event)
        
        detected_patterns = []
        
        # Run different pattern detection algorithms
        try:
            temporal_patterns = await self._detect_temporal_patterns(event)
            detected_patterns.extend(temporal_patterns)
        except Exception as e:
            logger.error(f"Temporal pattern detection failed: {str(e)}")
        
        try:
            behavioral_patterns = await self._detect_behavioral_patterns(event)
            detected_patterns.extend(behavioral_patterns)
        except Exception as e:
            logger.error(f"Behavioral pattern detection failed: {str(e)}")
        
        try:
            anomalies = await self._detect_anomalies(event)
            detected_patterns.extend(anomalies)
        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
        
        try:
            sequential_patterns = await self._detect_sequential_patterns(event)
            detected_patterns.extend(sequential_patterns)
        except Exception as e:
            logger.error(f"Sequential pattern detection failed: {str(e)}")
        
        # Update pattern registry
        for pattern in detected_patterns:
            await self._update_pattern_registry(pattern)
        
        return detected_patterns
    
    async def _detect_temporal_patterns(self, event: Dict[str, Any]) -> List[Pattern]:
        """
        Detect temporal patterns (time-based patterns, periodicity).
        
        This implementation uses a sliding window approach to detect recurring events.
        """
        patterns = []
        
        if not self.event_history or len(self.event_history) < 10:
            return patterns
        
        # Extract events within the temporal window
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=self.temporal_window)
        
        recent_events = [
            e for e in self.event_history 
            if e.get("timestamp", current_time) >= window_start
        ]
        
        if len(recent_events) < 5:
            return patterns
        
        # Detect high-frequency events (events occurring more than expected)
        event_type = event.get("task_type", "unknown")
        event_type_count = sum(1 for e in recent_events if e.get("task_type") == event_type)
        
        expected_frequency = len(recent_events) / 10  # Assume 10 different event types
        if event_type_count > expected_frequency * 2:
            pattern_id = self._generate_pattern_id(f"temporal_{event_type}")
            pattern = Pattern(
                pattern_id=pattern_id,
                pattern_type=PatternType.TEMPORAL,
                confidence=min(0.95, event_type_count / (expected_frequency * 3)),
                description=f"High frequency of {event_type} events detected",
                metadata={
                    "event_type": event_type,
                    "count": event_type_count,
                    "window_seconds": self.temporal_window
                }
            )
            patterns.append(pattern)
        
        # Detect cyclical patterns (events at regular intervals)
        if len(recent_events) >= 10:
            timestamps = [e.get("timestamp", current_time) for e in recent_events if e.get("task_type") == event_type]
            if len(timestamps) >= 5:
                intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps)-1)]
                if intervals:
                    avg_interval = np.mean(intervals)
                    std_interval = np.std(intervals)
                    
                    # If intervals are consistent (low std), it's a cyclical pattern
                    if std_interval < avg_interval * 0.3:  # 30% variation threshold
                        pattern_id = self._generate_pattern_id(f"cyclical_{event_type}")
                        pattern = Pattern(
                            pattern_id=pattern_id,
                            pattern_type=PatternType.CYCLICAL,
                            confidence=1.0 - (std_interval / avg_interval),
                            description=f"Cyclical pattern detected for {event_type} with {avg_interval:.1f}s interval",
                            metadata={
                                "event_type": event_type,
                                "avg_interval_seconds": avg_interval,
                                "std_interval_seconds": std_interval
                            }
                        )
                        patterns.append(pattern)
        
        return patterns
    
    async def _detect_behavioral_patterns(self, event: Dict[str, Any]) -> List[Pattern]:
        """
        Detect behavioral patterns (user/system behavior patterns).
        
        This implementation analyzes sequences of actions to identify common behaviors.
        """
        patterns = []
        
        if len(self.event_history) < 20:
            return patterns
        
        # Extract recent event sequence
        recent_events = list(self.event_history)[-20:]
        event_sequence = [e.get("task_type", "unknown") for e in recent_events]
        
        # Detect common subsequences (n-grams)
        for n in [2, 3]:
            ngrams = [tuple(event_sequence[i:i+n]) for i in range(len(event_sequence)-n+1)]
            ngram_counts = defaultdict(int)
            for ngram in ngrams:
                ngram_counts[ngram] += 1
            
            # Identify frequent n-grams
            for ngram, count in ngram_counts.items():
                if count >= 3:  # Appears at least 3 times
                    pattern_id = self._generate_pattern_id(f"behavioral_{'_'.join(ngram)}")
                    pattern = Pattern(
                        pattern_id=pattern_id,
                        pattern_type=PatternType.BEHAVIORAL,
                        confidence=min(0.95, count / len(ngrams)),
                        description=f"Behavioral pattern: {' -> '.join(ngram)} (repeated {count} times)",
                        metadata={
                            "sequence": list(ngram),
                            "count": count,
                            "ngram_size": n
                        }
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _detect_anomalies(self, event: Dict[str, Any]) -> List[Pattern]:
        """
        Detect anomalies using statistical methods (Z-score based).
        
        This implementation uses online statistics to detect anomalous metric values.
        """
        patterns = []
        
        metrics = event.get("metrics", {})
        if not metrics:
            return patterns
        
        for metric_name, metric_value in metrics.items():
            if not isinstance(metric_value, (int, float)):
                continue
            
            # Update statistics
            stats = self.metric_stats[metric_name]
            stats["count"] += 1
            stats["sum"] += metric_value
            stats["sum_sq"] += metric_value ** 2
            
            # Calculate mean and std (online algorithm)
            n = stats["count"]
            stats["mean"] = stats["sum"] / n
            if n > 1:
                variance = (stats["sum_sq"] / n) - (stats["mean"] ** 2)
                stats["std"] = np.sqrt(max(0, variance))
            
            # Detect anomaly if we have enough data
            if n >= 10 and stats["std"] > 0:
                z_score = abs((metric_value - stats["mean"]) / stats["std"])
                
                if z_score > self.anomaly_threshold:
                    pattern_id = self._generate_pattern_id(f"anomaly_{metric_name}")
                    pattern = Pattern(
                        pattern_id=pattern_id,
                        pattern_type=PatternType.ANOMALY,
                        confidence=min(0.99, z_score / (self.anomaly_threshold * 2)),
                        description=f"Anomaly detected in {metric_name}: {metric_value:.4f} (z-score: {z_score:.2f})",
                        metadata={
                            "metric_name": metric_name,
                            "metric_value": metric_value,
                            "mean": stats["mean"],
                            "std": stats["std"],
                            "z_score": z_score
                        }
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _detect_sequential_patterns(self, event: Dict[str, Any]) -> List[Pattern]:
        """
        Detect sequential patterns (ordered sequences of events).
        
        This implementation looks for specific sequences that indicate a workflow or process.
        """
        patterns = []
        
        if len(self.event_history) < 10:
            return patterns
        
        # Define known sequential patterns to look for
        known_sequences = [
            ["classification", "explainability", "deployment"],
            ["data_preprocessing", "feature_engineering", "model_training"],
            ["anomaly_detection", "alert", "remediation"]
        ]
        
        recent_events = list(self.event_history)[-20:]
        event_sequence = [e.get("task_type", "unknown") for e in recent_events]
        
        for known_seq in known_sequences:
            # Check if the known sequence appears in recent events
            if self._is_subsequence(known_seq, event_sequence):
                pattern_id = self._generate_pattern_id(f"sequential_{'_'.join(known_seq)}")
                pattern = Pattern(
                    pattern_id=pattern_id,
                    pattern_type=PatternType.SEQUENTIAL,
                    confidence=0.9,
                    description=f"Sequential pattern detected: {' -> '.join(known_seq)}",
                    metadata={
                        "sequence": known_seq
                    }
                )
                patterns.append(pattern)
        
        return patterns
    
    def _is_subsequence(self, subseq: List[str], seq: List[str]) -> bool:
        """Check if subseq is a subsequence of seq"""
        it = iter(seq)
        return all(item in it for item in subseq)
    
    async def _update_pattern_registry(self, pattern: Pattern):
        """Update the pattern registry with a detected pattern"""
        if pattern.pattern_id in self.patterns:
            # Update existing pattern
            existing = self.patterns[pattern.pattern_id]
            existing.frequency += 1
            existing.last_seen = datetime.utcnow()
            existing.confidence = (existing.confidence + pattern.confidence) / 2
        else:
            # Register new pattern
            self.patterns[pattern.pattern_id] = pattern
            logger.info(f"New pattern registered: {pattern.description}")
    
    def _generate_pattern_id(self, pattern_key: str) -> str:
        """Generate a unique pattern ID based on pattern key"""
        return hashlib.md5(pattern_key.encode()).hexdigest()[:16]
    
    async def get_pattern(self, pattern_id: str) -> Optional[Pattern]:
        """Get a pattern by ID"""
        return self.patterns.get(pattern_id)
    
    async def get_all_patterns(self, pattern_type: Optional[PatternType] = None) -> List[Pattern]:
        """Get all patterns, optionally filtered by type"""
        if pattern_type:
            return [p for p in self.patterns.values() if p.pattern_type == pattern_type]
        return list(self.patterns.values())
    
    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected patterns"""
        patterns_by_type = defaultdict(int)
        for pattern in self.patterns.values():
            patterns_by_type[pattern.pattern_type.value] += 1
        
        return {
            "total_patterns": len(self.patterns),
            "patterns_by_type": dict(patterns_by_type),
            "event_history_size": len(self.event_history),
            "metric_stats_count": len(self.metric_stats)
        }
    
    async def clear_old_patterns(self, days: int = 30):
        """Clear patterns older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_patterns = [
            pid for pid, pattern in self.patterns.items()
            if pattern.last_seen < cutoff_date
        ]
        
        for pid in old_patterns:
            del self.patterns[pid]
        
        logger.info(f"Cleared {len(old_patterns)} old patterns")
        return len(old_patterns)
