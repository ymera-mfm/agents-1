
"""
Advanced Examination Agent
Comprehensive content analysis, quality assessment, and intelligent evaluation
"""

import asyncio
import json
import time
import re
import hashlib
import statistics
import traceback
import os # Added for environment variables
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, Counter
# Optional dependencies - Numerical computing
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False
from datetime import datetime, timedelta

# Optional dependencies
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

# External libraries for NLP/ML tasks (placeholders for actual integration)
# import spacy # For advanced NLP tasks like entity recognition, dependency parsing
# import transformers # For more sophisticated sentiment, bias, toxicity models
# import textstat # For readability metrics
# import nltk # For tokenization, stemming, lemmatization

from base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResponse, Priority, AgentStatus, TaskStatus # Added TaskStatus

try:
    from opentelemetry import trace
    HAS_OPENTELEMETRY = True
except ImportError:
    trace = None
    HAS_OPENTELEMETRY = False

class ExaminationType(Enum):
    CONTENT_QUALITY = "content_quality"
    PLAGIARISM = "plagiarism"
    SENTIMENT = "sentiment"
    READABILITY = "readability"
    STRUCTURE = "structure"
    FACTUAL_ACCURACY = "factual_accuracy"
    BIAS_DETECTION = "bias_detection"
    TOXICITY = "toxicity"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"

class QualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class ExaminationResult:
    examination_id: str
    examination_type: ExaminationType
    content_id: str
    score: float
    quality_level: QualityLevel
    details: Dict[str, Any]
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: float = 0.0
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComprehensiveAnalysis:
    content_id: str
    overall_score: float
    overall_quality: QualityLevel
    examinations: List[ExaminationResult]
    summary: Dict[str, Any]
    recommendations: List[str]
    processing_time_ms: float
    timestamp: float = field(default_factory=time.time)

class ExaminationAgent(BaseAgent):
    """
    Advanced Examination Agent with:
    - Multi-dimensional content quality assessment
    - AI-powered plagiarism detection and similarity analysis
    - Advanced sentiment and emotion analysis
    - Bias detection and fairness evaluation
    - Structural and coherence analysis
    - Real-time toxicity and safety screening
    - Factual accuracy verification with knowledge graphs
    - Content completeness and gap analysis
    - Intelligent reporting and recommendation system
    - Learning-based quality improvement
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Analysis engines (placeholders for actual implementations)
        self.quality_analyzers = self._initialize_quality_analyzers()
        self.plagiarism_engine = self._setup_plagiarism_detection()
        self.sentiment_analyzer = self._initialize_sentiment_analysis()
        self.bias_detector = self._setup_bias_detection()
        self.toxicity_filter = self._initialize_toxicity_detection()
        self.fact_checker = self._setup_fact_checking()
        
        # Knowledge bases and references
        self.reference_corpus = {}
        self.quality_benchmarks = self._load_quality_benchmarks()
        self.domain_standards = self._load_domain_standards()
        
        # Learning and adaptation
        self.examination_history = defaultdict(list)
        self.quality_patterns = {}
        self.user_feedback = defaultdict(list)
        
        # Performance tracking
        self.examination_stats = {
            "total_examinations": 0,
            "average_processing_time": 0.0,
            "accuracy_rate": 0.0,
            "examination_types_count": defaultdict(int)
        }
        
        # Collaborative features
        self.peer_review_network = {}
        self.expert_validation_cache = {}
    
    async def start(self):
        """Start examination agent services"""
        # Core examination services
        # The _handle_examination_task method will now route to _execute_task_impl
        # Subscribing to agent.name.task is handled by BaseAgent, no need to resubscribe here.
        
        # Specialized examination endpoints (these can be handled by _execute_task_impl if needed)
        # For now, keeping them as direct subscriptions for flexibility or if they need specific queueing
        await self._subscribe(
            "examination.quality",
            self._handle_quality_examination
        )
        
        await self._subscribe(
            "examination.plagiarism",
            self._handle_plagiarism_check
        )
        
        await self._subscribe(
            "examination.sentiment",
            self._handle_sentiment_analysis
        )
        
        await self._subscribe(
            "examination.bias",
            self._handle_bias_detection
        )
        
        await self._subscribe(
            "examination.comprehensive",
            self._handle_comprehensive_analysis
        )
        
        await self._subscribe(
            "examination.batch",
            self._handle_batch_examination
        )
        
        # Feedback and learning
        await self._subscribe(
            "examination.feedback",
            self._handle_user_feedback
        )
        
        # Collaborative examination
        await self._subscribe(
            "examination.peer_review",
            self._handle_peer_review
        )
        
        # Background tasks
        asyncio.create_task(self._update_reference_corpus())
        asyncio.create_task(self._learn_from_feedback())
        # Removed _performance_monitoring as BaseAgent handles metrics publishing
        
        self.logger.info("Examination Agent started")
    
    def _initialize_quality_analyzers(self) -> Dict[str, Any]:
        """Initialize quality analysis components. These are configuration, not active analyzers."""
        return {
            "readability": {
                "flesch_kincaid": {"weight": 0.3, "target_range": (8, 12)},
                "gunning_fog": {"weight": 0.25, "target_range": (8, 14)},
                "automated_readability": {"weight": 0.2, "target_range": (8, 12)},
                "coleman_liau": {"weight": 0.25, "target_range": (8, 12)}
            },
            "structure": {
                "paragraph_count": {"min": 3, "ideal_range": (5, 15)},
                "sentence_variety": {"min_variation": 0.3},
                "transition_words": {"min_density": 0.02},
                "heading_hierarchy": {"proper_nesting": True}
            },
            "content_depth": {
                "concept_density": {"min_threshold": 0.1},
                "detail_level": {"min_depth": 3},
                "example_ratio": {"target": 0.2},
                "evidence_support": {"min_citations": 0.05}
            },
            "engagement": {
                "question_ratio": {"target": 0.03},
                "active_voice": {"min_percentage": 0.7},
                "concrete_language": {"target": 0.6},
                "emotional_appeal": {"balance": 0.3}
            }
        }
    
    def _setup_plagiarism_detection(self) -> Dict[str, Any]:
        """Setup plagiarism detection engine configuration"""
        return {
            "similarity_threshold": 0.15,
            "chunk_size": 50,  # words
            "overlap_threshold": 0.8,
            "algorithms": {
                "shingling": {"k": 5, "weight": 0.4},
                "jaccard": {"weight": 0.3},
                "cosine_similarity": {"weight": 0.3}
            },
            "exclusions": {
                "common_phrases": [
                    "in conclusion", "furthermore", "however", "therefore",
                    "on the other hand", "in addition", "as a result"
                ],
                "citation_patterns": [
                    r"according to \w+",
                    r"\w+ states that",
                    r"as mentioned by \w+"
                ]
            }
        }
    
    def _initialize_sentiment_analysis(self) -> Dict[str, Any]:
        """Initialize sentiment analysis engine configuration"""
        return {
            "lexicons": {
                "positive_words": [
                    "excellent", "outstanding", "remarkable", "exceptional",
                    "brilliant", "fantastic", "wonderful", "amazing"
                ],
                "negative_words": [
                    "terrible", "awful", "horrible", "disappointing",
                    "poor", "bad", "inadequate", "unsatisfactory"
                ],
                "intensity_modifiers": {
                    "very": 1.5, "extremely": 2.0, "quite": 1.2,
                    "somewhat": 0.8, "slightly": 0.6, "barely": 0.4
                }
            },
            "emotion_categories": {
                "joy": ["happy", "delighted", "pleased", "satisfied"],
                "anger": ["angry", "furious", "irritated", "annoyed"],
                "sadness": ["sad", "disappointed", "depressed", "melancholy"],
                "fear": ["afraid", "worried", "anxious", "concerned"],
                "surprise": ["surprised", "amazed", "astonished", "shocked"],
                "trust": ["confident", "certain", "secure", "assured"]
            },
            "context_weights": {
                "negation": -1.0,
                "emphasis": 1.3,
                "conditional": 0.7,
                "question": 0.8
            }
        }
    
    def _setup_bias_detection(self) -> Dict[str, Any]:
        """Setup bias detection systems configuration"""
        return {
            "bias_types": {
                "gender": {
                    "indicators": [
                        r"\b(he|she)\s+is\s+(naturally|typically|usually)",
                        r"\b(men|women)\s+are\s+(better|worse)\s+at",
                        r"\b(his|her)\s+(emotional|logical)\s+(nature|tendencies)"
                    ],
                    "gendered_terms": {
                        "inclusive": ["they", "person", "individual", "professional"],
                        "exclusive": ["guys", "mankind", "manpower", "chairman"]
                    }
                },
                "racial": {
                    "indicators": [
                        r"\b(race|ethnicity)\s+(determines|influences)\s+",
                        r"\b(cultural|ethnic)\s+stereotypes?",
                        r"\b(minority|majority)\s+groups?\s+(tend to|usually)"
                    ]
                },
                "age": {
                    "indicators": [
                        r"\b(young|old)\s+people\s+(are|can't|don't)",
                        r"\b(generation|generational)\s+(gap|differences?)",
                        r"\bmillennials?\s+(are|don't|can't)"
                    ]
                },
                "confirmation": {
                    "indicators": [
                        r"\bobviously\b", r"\bclearly\b", r"\bundoubtedly\b",
                        r"\bof course\b", r"\beveryone knows\b"
                    ]
                }
            },
            "fairness_metrics": {
                "representation": {"min_threshold": 0.3},
                "perspective_balance": {"required": True},
                "inclusive_language": {"score_weight": 0.4}
            }
        }
    
    def _initialize_toxicity_detection(self) -> Dict[str, Any]:
        """Initialize toxicity detection system configuration"""
        return {
            "toxicity_categories": {
                "hate_speech": {
                    "patterns": [
                        r"\b(hate|despise|loathe)\s+\w+\s+(people|group)",
                        r"\b(kill|destroy|eliminate)\s+all\s+\w+",
                    ],
                    "severity": "critical"
                },
                "harassment": {
                    "patterns": [
                        r"\byou\s+(are|should)\s+(stupid|worthless|useless)",
                        r"\bshut\s+up\b", r"\bstop\s+talking\b"
                    ],
                    "severity": "high"
                },
                "profanity": {
                    "patterns": [
                        r"\b(damn|hell|crap)\b"  # Mild profanity examples
                    ],
                    "severity": "medium"
                },
                "threats": {
                    "patterns": [
                        r"\b(will|gonna)\s+(hurt|harm|kill)\s+you",
                        r"\bwatch\s+your\s+back\b"
                    ],
                    "severity": "critical"
                }
            },
            "context_modifiers": {
                "quotation": 0.5,  # Reduce severity if in quotes
                "hypothetical": 0.6,  # "if someone said..."
                "academic": 0.3,  # Academic discussion
                "creative": 0.4   # Creative writing context
            }
        }
    
    def _setup_fact_checking(self) -> Dict[str, Any]:
        """Setup fact-checking system configuration"""
        return {
            "claim_patterns": [
                r"\b(according to|studies show|research indicates)\b",
                r"\b(\d+%|\d+\s+percent)\s+of\b",
                r"\bin\s+\d{4}\b",  # Years
                r"\b(scientists|experts|researchers)\s+(found|discovered|concluded)\b"
            ],
            "verification_sources": {
                "academic": {"weight": 0.9, "reliability": "high"},
                "government": {"weight": 0.8, "reliability": "high"},
                "news": {"weight": 0.6, "reliability": "medium"},
                "social": {"weight": 0.2, "reliability": "low"}
            },
            "confidence_thresholds": {
                "verified": 0.8,
                "likely": 0.6,
                "uncertain": 0.4,
                "disputed": 0.2
            }
        }
    
    def _load_quality_benchmarks(self) -> Dict[str, Any]:
        """Load quality benchmarks for different content types"""
        return {
            "academic": {
                "min_readability_grade": 12,
                "min_citations_per_1000_words": 5,
                "structure_requirements": ["abstract", "introduction", "methodology", "results", "conclusion"],
                "objectivity_threshold": 0.8
            },
            "business": {
                "min_readability_grade": 10,
                "action_orientation": 0.3,
                "clarity_threshold": 0.8,
                "professional_tone": 0.9
            },
            "creative": {
                "creativity_score": 0.7,
                "engagement_level": 0.8,
                "emotional_range": 0.6,
                "originality_threshold": 0.9
            },
            "technical": {
                "accuracy_requirement": 0.95,
                "completeness_threshold": 0.9,
                "clarity_for_audience": 0.8,
                "example_coverage": 0.6
            }
        }
    
    def _load_domain_standards(self) -> Dict[str, Any]:
        """Load domain-specific quality standards"""
        return {
            "journalism": {
                "fact_check_requirement": True,
                "source_attribution": True,
                "objectivity_score": 0.8,
                "timeliness": True
            },
            "education": {
                "pedagogical_structure": True,
                "learning_objectives": True,
                "assessment_alignment": 0.9,
                "accessibility": 0.8
            },
            "marketing": {
                "persuasion_ethics": 0.8,
                "claim_substantiation": 0.9,
                "audience_targeting": 0.7,
                "call_to_action": True
            },
            "legal": {
                "precision_requirement": 0.95,
                "citation_completeness": 0.95,
                "logical_structure": 0.9,
                "precedent_alignment": 0.8
            }
        }
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute examination-specific tasks"""
        task_type = request.task_type
        payload = request.payload
        content_id = payload.get("content_id", str(uuid.uuid4()))
        content = payload.get("content")
        examination_id = str(uuid.uuid4())
        start_time = time.time()

        if not content:
            raise ValueError("Content is required for examination.")

        result: Optional[ExaminationResult] = None
        if task_type == ExaminationType.CONTENT_QUALITY.value:
            result = await self._examine_content_quality(content_id, content, examination_id, payload)
        elif task_type == ExaminationType.PLAGIARISM.value:
            result = await self._check_plagiarism(content_id, content, examination_id, payload)
        elif task_type == ExaminationType.SENTIMENT.value:
            result = await self._analyze_sentiment(content_id, content, examination_id, payload)
        elif task_type == ExaminationType.READABILITY.value:
            result = await self._analyze_readability(content_id, content, examination_id, payload)
        elif task_type == ExaminationType.STRUCTURE.value:
            result = await self._analyze_structure(content_id, content, examination_id, payload)
        elif task_type == ExaminationType.FACTUAL_ACCURACY.value:
            result = await self._check_factual_accuracy(content_id, content, examination_id, payload)
        elif task_type == ExaminationType.BIAS_DETECTION.value:
            result = await self._detect_bias(content_id, content, examination_id, payload)
        elif task_type == ExaminationType.TOXICITY.value:
            result = await self._detect_toxicity(content_id, content, examination_id, payload)
        elif task_type == ExaminationType.CONSISTENCY.value:
            result = await self._check_consistency(content_id, content, examination_id, payload)
        elif task_type == ExaminationType.COMPLETENESS.value:
            result = await self._check_completeness(content_id, content, examination_id, payload)
        elif task_type == "comprehensive_analysis":
            return await self._perform_comprehensive_analysis(content_id, content, payload)
        elif task_type == "batch_examination":
            return await self._perform_batch_examination(payload)
        else:
            raise ValueError(f"Unknown examination task type: {task_type}")

        if result:
            result.processing_time_ms = (time.time() - start_time) * 1000
            self.examination_stats["total_examinations"] += 1
            self.examination_stats["examination_types_count"][task_type] += 1
            # Update average processing time (simple moving average)
            current_avg = self.examination_stats["average_processing_time"]
            total_exams = self.examination_stats["total_examinations"]
            self.examination_stats["average_processing_time"] = \
                (current_avg * (total_exams - 1) + result.processing_time_ms) / total_exams
            
            # Store result in DB
            if self.db_pool:
                await self._store_examination_result(result)

            return asdict(result)
        else:
            raise RuntimeError(f"Examination for {task_type} failed to produce a result.")

    async def _examine_content_quality(self, content_id: str, content: str, examination_id: str, payload: Dict) -> ExaminationResult:
        """Perform a general content quality examination"""
        self.logger.info(f"Examining content quality for {content_id}")
        
        # Combine multiple examination types for a holistic quality score
        readability_res = await self._analyze_readability(content_id, content, str(uuid.uuid4()), payload)
        sentiment_res = await self._analyze_sentiment(content_id, content, str(uuid.uuid4()), payload)
        structure_res = await self._analyze_structure(content_id, content, str(uuid.uuid4()), payload)
        # Add more sub-examinations as needed

        overall_score = (readability_res.score + sentiment_res.score + structure_res.score) / 3
        quality_level = self._determine_quality_level(overall_score)

        details = {
            "readability": asdict(readability_res),
            "sentiment": asdict(sentiment_res),
            "structure": asdict(structure_res)
        }
        issues = readability_res.issues + sentiment_res.issues + structure_res.issues
        suggestions = readability_res.suggestions + sentiment_res.suggestions + structure_res.suggestions

        return ExaminationResult(
            examination_id=examination_id,
            examination_type=ExaminationType.CONTENT_QUALITY,
            content_id=content_id,
            score=overall_score,
            quality_level=quality_level,
            details=details,
            issues=issues,
            suggestions=suggestions,
            confidence=0.95 # High confidence for combined analysis
        )

    async def _check_plagiarism(self, content_id: str, content: str, examination_id: str, payload: Dict) -> ExaminationResult:
        """Check for plagiarism against a reference corpus or external services"""
        self.logger.info(f"Checking plagiarism for {content_id}")
        
        # Placeholder for actual plagiarism detection logic
        # This would involve comparing content against self.reference_corpus or external APIs
        
        similarity_score = 0.0 # Placeholder
        issues = []
        suggestions = []

        # Simulate some plagiarism detection
        if "copy-paste" in content.lower():
            similarity_score = 0.75
            issues.append({"type": "plagiarism", "message": "High similarity detected in a section.", "severity": "critical"})
            suggestions.append("Paraphrase the identified sections and cite sources.")
        
        quality_level = self._determine_quality_level(1.0 - similarity_score) # Higher similarity -> lower quality

        return ExaminationResult(
            examination_id=examination_id,
            examination_type=ExaminationType.PLAGIARISM,
            content_id=content_id,
            score=similarity_score,
            quality_level=quality_level,
            details={
                "similarity_score": similarity_score,
                "matched_sources": [] # In a real system, this would list sources
            },
            issues=issues,
            suggestions=suggestions,
            confidence=0.8
        )

    async def _analyze_sentiment(self, content_id: str, content: str, examination_id: str, payload: Dict) -> ExaminationResult:
        """Analyze the sentiment of the content"""
        self.logger.info(f"Analyzing sentiment for {content_id}")
        
        # Placeholder for actual sentiment analysis using an NLP library or LLM
        # For now, a simple keyword-based approach
        positive_words = ["good", "great", "excellent", "happy", "positive"]
        negative_words = ["bad", "poor", "terrible", "sad", "negative"]
        
        sentiment_score = 0.0
        words = content.lower().split()
        
        for word in words:
            if word in positive_words:
                sentiment_score += 0.1
            elif word in negative_words:
                sentiment_score -= 0.1
        
        # Normalize score to be between 0 and 1
        sentiment_score = max(0.0, min(1.0, (sentiment_score + 1) / 2))

        sentiment_label = "neutral"
        if sentiment_score > 0.6:
            sentiment_label = "positive"
        elif sentiment_score < 0.4:
            sentiment_label = "negative"
        
        quality_level = self._determine_quality_level(sentiment_score)

        return ExaminationResult(
            examination_id=examination_id,
            examination_type=ExaminationType.SENTIMENT,
            content_id=content_id,
            score=sentiment_score,
            quality_level=quality_level,
            details={"sentiment_label": sentiment_label, "raw_score": sentiment_score},
            confidence=0.7
        )

    async def _analyze_readability(self, content_id: str, content: str, examination_id: str, payload: Dict) -> ExaminationResult:
        """Analyze the readability of the content"""
        self.logger.info(f"Analyzing readability for {content_id}")
        
        # Placeholder for textstat integration
        try:
            flesch_ease = flesch_reading_ease(content)
            flesch_kincaid = flesch_kincaid_grade(content)
        except Exception:
            flesch_ease = 50.0 # Default if textstat fails
            flesch_kincaid = 8.0

        # Score based on Flesch-Kincaid (lower grade level is often better for general audience)
        # Target grade level can be configured
        target_grade = payload.get("target_grade_level", 8)
        score = max(0.0, 1.0 - abs(flesch_kincaid - target_grade) / 10.0) # Simple scoring
        
        issues = []
        suggestions = []
        if flesch_kincaid > target_grade + 2:
            issues.append({"type": "readability", "message": f"Content is too complex (Grade {flesch_kincaid:.1f}).", "severity": "medium"})
            suggestions.append("Simplify sentence structures and use more common vocabulary.")
        elif flesch_kincaid < target_grade - 2:
            issues.append({"type": "readability", "message": f"Content might be too simplistic (Grade {flesch_kincaid:.1f}).", "severity": "low"})
            suggestions.append("Consider adding more detail or complex ideas if appropriate for the audience.")

        quality_level = self._determine_quality_level(score)

        return ExaminationResult(
            examination_id=examination_id,
            examination_type=ExaminationType.READABILITY,
            content_id=content_id,
            score=score,
            quality_level=quality_level,
            details={
                "flesch_reading_ease": flesch_ease,
                "flesch_kincaid_grade": flesch_kincaid,
                "target_grade_level": target_grade
            },
            issues=issues,
            suggestions=suggestions,
            confidence=0.9
        )

    async def _analyze_structure(self, content_id: str, content: str, examination_id: str, payload: Dict) -> ExaminationResult:
        """Analyze the structural integrity and coherence of the content"""
        self.logger.info(f"Analyzing structure for {content_id}")
        
        # Placeholder for structural analysis
        paragraphs = [p for p in content.split("\n\n") if p.strip()]
        sentences = re.split(r'[.!?]\s*', content)
        
        paragraph_count = len(paragraphs)
        sentence_count = len(sentences)
        
        issues = []
        suggestions = []

        if paragraph_count < 3:
            issues.append({"type": "structure", "message": "Content lacks sufficient paragraph breaks.", "severity": "low"})
            suggestions.append("Break down long blocks of text into smaller, more digestible paragraphs.")
        
        avg_sentences_per_paragraph = sentence_count / max(1, paragraph_count)
        if avg_sentences_per_paragraph > 10:
            issues.append({"type": "structure", "message": "Paragraphs are too long on average.", "severity": "medium"})
            suggestions.append("Reduce sentence count per paragraph for better flow.")

        # Score based on structural adherence (placeholder)
        score = max(0.0, 1.0 - (len(issues) * 0.1)) # Simple inverse relationship with issues
        quality_level = self._determine_quality_level(score)

        return ExaminationResult(
            examination_id=examination_id,
            examination_type=ExaminationType.STRUCTURE,
            content_id=content_id,
            score=score,
            quality_level=quality_level,
            details={
                "paragraph_count": paragraph_count,
                "sentence_count": sentence_count,
                "avg_sentences_per_paragraph": avg_sentences_per_paragraph
            },
            issues=issues,
            suggestions=suggestions,
            confidence=0.85
        )

    async def _check_factual_accuracy(self, content_id: str, content: str, examination_id: str, payload: Dict) -> ExaminationResult:
        """Check factual accuracy against knowledge graphs or external sources"""
        self.logger.info(f"Checking factual accuracy for {content_id}")
        
        # This would involve extracting claims and querying a knowledge base or LLM for verification
        # Placeholder for now
        claims_found = re.findall(r"\b(The capital of France is Paris|Water boils at 100 degrees Celsius)\b", content)
        verified_claims = [c for c in claims_found if c == "The capital of France is Paris"]
        
        accuracy_score = len(verified_claims) / max(1, len(claims_found))
        
        issues = []
        suggestions = []
        if accuracy_score < 1.0 and claims_found:
            issues.append({"type": "factual_accuracy", "message": "Some claims could not be verified or were incorrect.", "severity": "high"})
            suggestions.append("Verify all factual claims with credible sources.")

        quality_level = self._determine_quality_level(accuracy_score)

        return ExaminationResult(
            examination_id=examination_id,
            examination_type=ExaminationType.FACTUAL_ACCURACY,
            content_id=content_id,
            score=accuracy_score,
            quality_level=quality_level,
            details={
                "claims_found": claims_found,
                "verified_claims": verified_claims,
                "unverified_claims": [c for c in claims_found if c not in verified_claims]
            },
            issues=issues,
            suggestions=suggestions,
            confidence=0.75
        )

    async def _detect_bias(self, content_id: str, content: str, examination_id: str, payload: Dict) -> ExaminationResult:
        """Detect bias and evaluate fairness in the content"""
        self.logger.info(f"Detecting bias for {content_id}")
        
        # Placeholder for bias detection logic using self.bias_detector config
        bias_score = 0.0
        issues = []
        suggestions = []

        for bias_type, config in self.bias_detector["bias_types"].items():
            for pattern in config["indicators"]:
                if re.search(pattern, content, re.IGNORECASE):
                    bias_score += 0.2 # Arbitrary increment
                    issues.append({"type": "bias_detection", "message": f"Potential {bias_type} bias detected.", "severity": "medium"})
                    suggestions.append(f"Review language for {bias_type} bias and use inclusive terminology.")
        
        bias_score = min(1.0, bias_score) # Cap at 1.0
        quality_level = self._determine_quality_level(1.0 - bias_score) # Higher bias -> lower quality

        return ExaminationResult(
            examination_id=examination_id,
            examination_type=ExaminationType.BIAS_DETECTION,
            content_id=content_id,
            score=1.0 - bias_score,
            quality_level=quality_level,
            details={
                "detected_bias_types": [issue["message"] for issue in issues if issue["type"] == "bias_detection"]
            },
            issues=issues,
            suggestions=suggestions,
            confidence=0.6
        )

    async def _detect_toxicity(self, content_id: str, content: str, examination_id: str, payload: Dict) -> ExaminationResult:
        """Detect toxicity and inappropriate content"""
        self.logger.info(f"Detecting toxicity for {content_id}")
        
        # Placeholder for toxicity detection logic using self.toxicity_filter config
        toxicity_score = 0.0
        issues = []
        suggestions = []

        for category, config in self.toxicity_filter["toxicity_categories"].items():
            for pattern in config["patterns"]:
                if re.search(pattern, content, re.IGNORECASE):
                    toxicity_score += 0.3 # Arbitrary increment
                    issues.append({"type": "toxicity", "message": f"Potential {category} detected.", "severity": config["severity"]})
                    suggestions.append(f"Remove or rephrase content identified as {category}.")
        
        toxicity_score = min(1.0, toxicity_score) # Cap at 1.0
        quality_level = self._determine_quality_level(1.0 - toxicity_score) # Higher toxicity -> lower quality

        return ExaminationResult(
            examination_id=examination_id,
            examination_type=ExaminationType.TOXICITY,
            content_id=content_id,
            score=1.0 - toxicity_score,
            quality_level=quality_level,
            details={
                "detected_toxicity_categories": [issue["message"] for issue in issues if issue["type"] == "toxicity"]
            },
            issues=issues,
            suggestions=suggestions,
            confidence=0.7
        )

    async def _check_consistency(self, content_id: str, content: str, examination_id: str, payload: Dict) -> ExaminationResult:
        """Check for consistency in terminology, formatting, and style"""
        self.logger.info(f"Checking consistency for {content_id}")
        
        # Placeholder for consistency checks
        # Example: Check for consistent capitalization of a specific term
        term = payload.get("term_to_check", "AI")
        inconsistent_caps = re.findall(rf"\b(?!{term}\b)([a-z]*{term[1:]}|{term.lower()})\b", content, re.IGNORECASE)
        
        issues = []
        suggestions = []
        consistency_score = 1.0

        if inconsistent_caps:
            consistency_score -= 0.2
            issues.append({"type": "consistency", "message": f"Inconsistent capitalization for ‘{term}’ detected.", "severity": "low"})
            suggestions.append(f"Ensure consistent capitalization for the term ‘{term}’.")
        
        # Add more consistency checks (e.g., date formats, number formats, use of contractions)

        quality_level = self._determine_quality_level(consistency_score)

        return ExaminationResult(
            examination_id=examination_id,
            examination_type=ExaminationType.CONSISTENCY,
            content_id=content_id,
            score=consistency_score,
            quality_level=quality_level,
            details={
                "inconsistent_terms": list(set(inconsistent_caps))
            },
            issues=issues,
            suggestions=suggestions,
            confidence=0.8
        )

    async def _check_completeness(self, content_id: str, content: str, examination_id: str, payload: Dict) -> ExaminationResult:
        """Check if the content covers all required aspects or topics"""
        self.logger.info(f"Checking completeness for {content_id}")
        
        # This would typically involve comparing content against a predefined checklist or outline
        # or using an LLM to determine if all aspects of a prompt have been addressed.
        
        required_keywords = payload.get("required_keywords", ["introduction", "conclusion", "data", "analysis"])
        missing_keywords = [kw for kw in required_keywords if kw.lower() not in content.lower()]
        
        completeness_score = (len(required_keywords) - len(missing_keywords)) / max(1, len(required_keywords))
        
        issues = []
        suggestions = []
        if missing_keywords:
            issues.append({"type": "completeness", "message": f"Missing key sections or topics: {', '.join(missing_keywords)}.", "severity": "high"})
            suggestions.append(f"Ensure the content addresses all required keywords: {', '.join(required_keywords)}.")

        quality_level = self._determine_quality_level(completeness_score)

        return ExaminationResult(
            examination_id=examination_id,
            examination_type=ExaminationType.COMPLETENESS,
            content_id=content_id,
            score=completeness_score,
            quality_level=quality_level,
            details={
                "required_keywords": required_keywords,
                "missing_keywords": missing_keywords
            },
            issues=issues,
            suggestions=suggestions,
            confidence=0.85
        )

    async def _perform_comprehensive_analysis(self, content_id: str, content: str, payload: Dict) -> Dict[str, Any]:
        """Perform a comprehensive analysis by running multiple examination types"""
        self.logger.info(f"Performing comprehensive analysis for {content_id}")
        start_time = time.time()

        examination_types = payload.get("examination_types", [
            ExaminationType.CONTENT_QUALITY.value,
            ExaminationType.PLAGIARISM.value,
            ExaminationType.SENTIMENT.value,
            ExaminationType.READABILITY.value,
            ExaminationType.STRUCTURE.value,
            ExaminationType.FACTUAL_ACCURACY.value,
            ExaminationType.BIAS_DETECTION.value,
            ExaminationType.TOXICITY.value,
            ExaminationType.CONSISTENCY.value,
            ExaminationType.COMPLETENESS.value
        ])

        results: List[ExaminationResult] = []
        for exam_type_str in examination_types:
            try:
                exam_type = ExaminationType(exam_type_str)
                # Call the corresponding examination method
                if exam_type == ExaminationType.CONTENT_QUALITY:
                    result = await self._examine_content_quality(content_id, content, str(uuid.uuid4()), payload)
                elif exam_type == ExaminationType.PLAGIARISM:
                    result = await self._check_plagiarism(content_id, content, str(uuid.uuid4()), payload)
                elif exam_type == ExaminationType.SENTIMENT:
                    result = await self._analyze_sentiment(content_id, content, str(uuid.uuid4()), payload)
                elif exam_type == ExaminationType.READABILITY:
                    result = await self._analyze_readability(content_id, content, str(uuid.uuid4()), payload)
                elif exam_type == ExaminationType.STRUCTURE:
                    result = await self._analyze_structure(content_id, content, str(uuid.uuid4()), payload)
                elif exam_type == ExaminationType.FACTUAL_ACCURACY:
                    result = await self._check_factual_accuracy(content_id, content, str(uuid.uuid4()), payload)
                elif exam_type == ExaminationType.BIAS_DETECTION:
                    result = await self._detect_bias(content_id, content, str(uuid.uuid4()), payload)
                elif exam_type == ExaminationType.TOXICITY:
                    result = await self._detect_toxicity(content_id, content, str(uuid.uuid4()), payload)
                elif exam_type == ExaminationType.CONSISTENCY:
                    result = await self._check_consistency(content_id, content, str(uuid.uuid4()), payload)
                elif exam_type == ExaminationType.COMPLETENESS:
                    result = await self._check_completeness(content_id, content, str(uuid.uuid4()), payload)
                else:
                    self.logger.warning(f"Unhandled examination type in comprehensive analysis: {exam_type_str}")
                    continue
                
                results.append(result)
                # Update global stats
                self.examination_stats["total_examinations"] += 1
                self.examination_stats["examination_types_count"][exam_type_str] += 1

            except Exception as e:
                self.logger.error(f"Error during comprehensive analysis for {exam_type_str}", error=str(e), traceback=traceback.format_exc())
        
        if not results:
            raise RuntimeError("No examination results generated for comprehensive analysis.")

        overall_score = statistics.mean([r.score for r in results]) if results else 0.0
        overall_quality = self._determine_quality_level(overall_score)
        all_issues = [issue for r in results for issue in r.issues]
        all_suggestions = [s for r in results for s in r.suggestions]

        summary = {"overall_score": overall_score, "overall_quality": overall_quality.value}
        for r in results:
            summary[r.examination_type.value] = {"score": r.score, "quality_level": r.quality_level.value, "issues_count": len(r.issues)}

        comprehensive_analysis = ComprehensiveAnalysis(
            content_id=content_id,
            overall_score=overall_score,
            overall_quality=overall_quality,
            examinations=results,
            summary=summary,
            recommendations=all_suggestions,
            processing_time_ms=(time.time() - start_time) * 1000
        )
        
        # Store comprehensive analysis in DB
        if self.db_pool:
            await self._store_comprehensive_analysis(comprehensive_analysis)

        return asdict(comprehensive_analysis)

    async def _perform_batch_examination(self, payload: Dict) -> Dict[str, Any]:
        """Perform examinations on a batch of content items"""
        self.logger.info("Performing batch examination")
        batch_items = payload.get("batch_items", []) # List of {content_id, content, examination_types, ...}
        
        results = []
        for item in batch_items:
            try:
                content_id = item["content_id"]
                content = item["content"]
                examination_types = item.get("examination_types", [ExaminationType.CONTENT_QUALITY.value])
                
                # Call comprehensive analysis for each item in the batch
                comp_analysis = await self._perform_comprehensive_analysis(content_id, content, {"examination_types": examination_types})
                results.append(comp_analysis)
            except Exception as e:
                self.logger.error(f"Error processing batch item {item.get("content_id")}: {e}", traceback=traceback.format_exc())
                results.append({"content_id": item.get("content_id"), "error": str(e)})
        
        return {"batch_results": results, "total_items": len(batch_items), "processed_items": len(results)}

    def _determine_quality_level(self, score: float) -> QualityLevel:
        """Determine quality level based on a score (0-1)"""
        if score >= 0.9: return QualityLevel.EXCELLENT
        elif score >= 0.75: return QualityLevel.GOOD
        elif score >= 0.5: return QualityLevel.AVERAGE
        elif score >= 0.25: return QualityLevel.POOR
        else: return QualityLevel.CRITICAL

    async def _handle_quality_examination(self, msg):
        """Handle direct quality examination requests"""
        try:
            data = json.loads(msg.data.decode())
            content_id = data["content_id"]
            content = data["content"]
            examination_id = data.get("examination_id", str(uuid.uuid4()))
            
            result = await self._examine_content_quality(content_id, content, examination_id, data)
            await self._publish(msg.reply, json.dumps(asdict(result)).encode())
        except Exception as e:
            self.logger.error("Error in _handle_quality_examination", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_plagiarism_check(self, msg):
        """Handle direct plagiarism check requests"""
        try:
            data = json.loads(msg.data.decode())
            content_id = data["content_id"]
            content = data["content"]
            examination_id = data.get("examination_id", str(uuid.uuid4()))
            
            result = await self._check_plagiarism(content_id, content, examination_id, data)
            await self._publish(msg.reply, json.dumps(asdict(result)).encode())
        except Exception as e:
            self.logger.error("Error in _handle_plagiarism_check", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_sentiment_analysis(self, msg):
        """Handle direct sentiment analysis requests"""
        try:
            data = json.loads(msg.data.decode())
            content_id = data["content_id"]
            content = data["content"]
            examination_id = data.get("examination_id", str(uuid.uuid4()))
            
            result = await self._analyze_sentiment(content_id, content, examination_id, data)
            await self._publish(msg.reply, json.dumps(asdict(result)).encode())
        except Exception as e:
            self.logger.error("Error in _handle_sentiment_analysis", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_bias_detection(self, msg):
        """Handle direct bias detection requests"""
        try:
            data = json.loads(msg.data.decode())
            content_id = data["content_id"]
            content = data["content"]
            examination_id = data.get("examination_id", str(uuid.uuid4()))
            
            result = await self._detect_bias(content_id, content, examination_id, data)
            await self._publish(msg.reply, json.dumps(asdict(result)).encode())
        except Exception as e:
            self.logger.error("Error in _handle_bias_detection", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_comprehensive_analysis(self, msg):
        """Handle direct comprehensive analysis requests"""
        try:
            data = json.loads(msg.data.decode())
            content_id = data["content_id"]
            content = data["content"]
            
            result = await self._perform_comprehensive_analysis(content_id, content, data)
            await self._publish(msg.reply, json.dumps(result).encode())
        except Exception as e:
            self.logger.error("Error in _handle_comprehensive_analysis", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_batch_examination(self, msg):
        """Handle direct batch examination requests"""
        try:
            data = json.loads(msg.data.decode())
            
            result = await self._perform_batch_examination(data)
            await self._publish(msg.reply, json.dumps(result).encode())
        except Exception as e:
            self.logger.error("Error in _handle_batch_examination", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_user_feedback(self, msg):
        """Process user feedback to improve examination models"""
        try:
            data = json.loads(msg.data.decode())
            examination_id = data["examination_id"]
            feedback_type = data["feedback_type"] # e.g., "correct", "incorrect", "helpful"
            details = data.get("details", {})

            self.user_feedback[examination_id].append({"type": feedback_type, "details": details, "timestamp": time.time()})
            self.logger.info("Received user feedback", examination_id=examination_id, feedback_type=feedback_type)
            
            # In a real system, this would trigger model retraining or rule adjustments
            await self._publish(msg.reply, json.dumps({"status": "feedback_received"}).encode())
        except Exception as e:
            self.logger.error("Error processing user feedback", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_peer_review(self, msg):
        """Handle peer review requests for content"""
        try:
            data = json.loads(msg.data.decode())
            content_id = data["content_id"]
            reviewer_id = data["reviewer_id"]
            review_comments = data["review_comments"]
            review_score = data.get("review_score")

            self.peer_review_network[content_id] = self.peer_review_network.get(content_id, [])
            self.peer_review_network[content_id].append({
                "reviewer_id": reviewer_id,
                "comments": review_comments,
                "score": review_score,
                "timestamp": time.time()
            })
            self.logger.info("Received peer review", content_id=content_id, reviewer_id=reviewer_id)
            
            # Potentially trigger re-examination or validation based on review
            await self._publish(msg.reply, json.dumps({"status": "review_received"}).encode())
        except Exception as e:
            self.logger.error("Error processing peer review", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _update_reference_corpus(self):
        """Background task to update reference corpus for plagiarism and factual checks"""
        while not self._shutdown_event.is_set():
            try:
                # In a real system, this would fetch new documents from a data source
                # and update self.reference_corpus or a dedicated search index.
                self.logger.debug("Updating reference corpus (placeholder).")
                await asyncio.sleep(3600 * 24) # Update once a day
            except Exception as e:
                self.logger.error(f"Reference corpus update failed: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(3600)

    async def _learn_from_feedback(self):
        """Background task to learn from user feedback and adapt models"""
        while not self._shutdown_event.is_set():
            try:
                # This would involve processing self.user_feedback to fine-tune models
                # or adjust rule weights for quality assessment.
                if self.user_feedback:
                    self.logger.debug("Learning from user feedback (placeholder).")
                    # Clear feedback after processing
                    self.user_feedback.clear()
                await asyncio.sleep(3600) # Learn every hour
            except Exception as e:
                self.logger.error(f"Learning from feedback failed: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(300)

    # Database Operations
    async def _store_examination_result(self, result: ExaminationResult):
        """Store a single examination result in the database"""
        if not self.db_pool:
            self.logger.warning("Database pool not initialized. Examination result not stored.")
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO examination_results (examination_id, content_id, examination_type, score, quality_level, details, issues, suggestions, confidence, processing_time_ms, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """,
                result.examination_id,
                result.content_id,
                result.examination_type.value,
                result.score,
                result.quality_level.value,
                json.dumps(result.details),
                json.dumps(result.issues),
                json.dumps(result.suggestions),
                result.confidence,
                result.processing_time_ms,
                time.time()
                )
        except Exception as e:
            self.logger.error("Failed to store examination result in DB", examination_id=result.examination_id, error=str(e), traceback=traceback.format_exc())

    async def _store_comprehensive_analysis(self, analysis: ComprehensiveAnalysis):
        """Store a comprehensive analysis result in the database"""
        if not self.db_pool:
            self.logger.warning("Database pool not initialized. Comprehensive analysis not stored.")
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO comprehensive_analyses (content_id, overall_score, overall_quality, summary, recommendations, processing_time_ms, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                analysis.content_id,
                analysis.overall_score,
                analysis.overall_quality.value,
                json.dumps(analysis.summary),
                json.dumps(analysis.recommendations),
                analysis.processing_time_ms,
                time.time()
                )
            # Also store individual examination results if not already done by _store_examination_result
            for exam_result in analysis.examinations:
                await self._store_examination_result(exam_result)

        except Exception as e:
            self.logger.error("Failed to store comprehensive analysis in DB", content_id=analysis.content_id, error=str(e), traceback=traceback.format_exc())

    def _get_agent_metrics(self) -> Dict[str, Any]:
        """Provide Examination agent specific metrics."""
        base_metrics = super()._get_agent_metrics()
        base_metrics.update({
            "total_examinations": self.examination_stats["total_examinations"],
            "average_processing_time": self.examination_stats["average_processing_time"],
            "examination_types_count": dict(self.examination_stats["examination_types_count"]),
            "active_feedback_count": sum(len(v) for v in self.user_feedback.values())
        })
        return base_metrics


if __name__ == "__main__":
    config = AgentConfig(
        name="examination_agent",
        agent_type="examination",
        capabilities=[
            "content_quality_check", "plagiarism_check", "sentiment_analysis",
            "readability_analysis", "structure_analysis", "factual_accuracy_check",
            "bias_detection", "toxicity_detection", "consistency_check", "completeness_check",
            "comprehensive_analysis", "batch_examination"
        ],
        nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://agent:secure_password@postgres:5432/ymera"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
        consul_url=os.getenv("CONSUL_URL", "http://consul:8500"),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )
    
    agent = ExaminationAgent(config)
    asyncio.run(agent.run())

