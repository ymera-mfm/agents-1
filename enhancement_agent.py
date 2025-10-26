
"""
Advanced Enhancement Agent
Content improvement, optimization, and intelligent transformation
"""

import asyncio
import json
import time
import re
import difflib
# Optional dependencies - Numerical computing
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False
import traceback # Added for detailed error logging
import os # Added for environment variables
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field, asdict # Added asdict for easier serialization
from enum import Enum
from collections import defaultdict

# Optional dependencies
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

from base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResponse, Priority, AgentStatus, TaskStatus # Added TaskStatus

try:
    from opentelemetry import trace
    HAS_OPENTELEMETRY = True
except ImportError:
    trace = None
    HAS_OPENTELEMETRY = False

class EnhancementType(Enum):
    GRAMMAR = "grammar"
    STYLE = "style"
    CLARITY = "clarity"
    READABILITY = "readability"
    TONE = "tone"
    STRUCTURE = "structure"
    VOCABULARY = "vocabulary"
    COHERENCE = "coherence"
    ENGAGEMENT = "engagement"
    TECHNICAL = "technical"

class EnhancementLevel(Enum):
    MINIMAL = "minimal"
    MODERATE = "moderate"
    COMPREHENSIVE = "comprehensive"
    CREATIVE = "creative"

@dataclass
class Enhancement:
    enhancement_id: str
    enhancement_type: EnhancementType
    original_text: str
    enhanced_text: str
    confidence_score: float
    explanation: str
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EnhancementResult:
    original_content: str
    enhanced_content: str
    enhancements: List[Enhancement]
    overall_improvement_score: float
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class EnhancementAgent(BaseAgent):
    """
    Advanced Enhancement Agent with:
    - Multi-dimensional content analysis and improvement
    - AI-powered style and tone adaptation
    - Real-time grammar and readability enhancement
    - Context-aware vocabulary optimization
    - Structural reorganization for better flow
    - Intelligent content expansion and compression
    - Domain-specific enhancement patterns
    - Collaborative enhancement with other agents
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Enhancement models and processors
        self.grammar_patterns = self._load_grammar_patterns()
        self.style_analyzers = self._initialize_style_analyzers()
        self.readability_calculators = self._setup_readability_metrics()
        self.vocabulary_enhancers = self._load_vocabulary_tools()
        
        # Enhancement history and learning
        self.enhancement_history: Dict[str, List[Enhancement]] = defaultdict(list)
        self.user_preferences: Dict[str, Dict] = {}
        self.domain_patterns: Dict[str, Dict] = {}
        
        # Performance metrics
        self.enhancement_stats = {
            "total_enhancements": 0,
            "average_improvement_score": 0.0,
            "enhancement_types_count": defaultdict(int),
            "user_satisfaction_rate": 0.0
        }
        
        # Real-time collaboration with LLM Manager
        self.llm_collaboration_enabled = True
        self.collaborative_enhancement_cache = {}
        
    async def start(self):
        """Start enhancement agent services"""
        # The BaseAgent already subscribes to agent.{self.config.name}.task
        
        # Specialized enhancement endpoints
        await self._subscribe(
            "enhancement.grammar",
            self._handle_grammar_enhancement
        )
        
        await self._subscribe(
            "enhancement.style",
            self._handle_style_enhancement
        )
        
        await self._subscribe(
            "enhancement.readability",
            self._handle_readability_enhancement
        )
        
        await self._subscribe(
            "enhancement.batch",
            self._handle_batch_enhancement
        )
        
        # Collaborative enhancement with other agents
        await self._subscribe(
            "enhancement.collaborate",
            self._handle_collaborative_enhancement
        )
        
        # User preference learning
        await self._subscribe(
            "enhancement.feedback",
            self._handle_user_feedback
        )
        
        # Background optimization tasks
        asyncio.create_task(self._optimize_enhancement_patterns())
        asyncio.create_task(self._update_domain_knowledge())
        # Removed _performance_monitoring as BaseAgent handles metrics publishing
        
        self.logger.info("Enhancement Agent started")
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute enhancement-specific tasks"""
        task_type = request.task_type
        payload = request.payload
        
        try:
            result: Dict[str, Any] = {}
            if task_type == "enhance_content":
                result = await self._enhance_content(payload)
            
            elif task_type == "grammar_check":
                result = await self._grammar_check(payload)
            
            elif task_type == "style_adaptation":
                result = await self._style_adaptation(payload)
            
            elif task_type == "readability_optimization":
                result = await self._readability_optimization(payload)
            
            elif task_type == "vocabulary_enhancement":
                result = await self._vocabulary_enhancement(payload)
            
            elif task_type == "structure_improvement":
                result = await self._structure_improvement(payload)
            
            elif task_type == "content_expansion":
                result = await self._content_expansion(payload)
            
            elif task_type == "content_compression":
                result = await self._content_compression(payload)
            
            elif task_type == "tone_adjustment":
                result = await self._tone_adjustment(payload)
            
            elif task_type == "collaborative_enhancement":
                result = await self._collaborative_enhancement(payload)
            
            else:
                raise ValueError(f"Unknown enhancement task type: {task_type}")
            
            return TaskResponse(task_id=request.task_id, status=TaskStatus.COMPLETED, result=result).dict()

        except Exception as e:
            self.logger.error(f"Error executing enhancement task {task_type}", error=str(e), traceback=traceback.format_exc())
            return TaskResponse(task_id=request.task_id, status=TaskStatus.FAILED, error=str(e)).dict()
    
    def _load_grammar_patterns(self) -> Dict[str, Any]:
        """Load advanced grammar correction patterns"""
        return {
            "common_errors": {
                r"\bthere\s+is\s+(\d+)": r"there are \1",  # Subject-verb agreement
                r"\bits\s+": r"it's ",  # Its vs it's
                r"\byour\s+welcome": r"you're welcome",  # Your vs you're
                r"\beffect\b": r"affect",  # Effect vs affect (context-dependent)
                r"\bthen\b(?=\s+\w+\s+will)": r"than",  # Then vs than
            },
            "style_improvements": {
                r"\bvery\s+(\w+)": lambda m: self._intensify_adjective(m.group(1)),
                r"\ba\s+lot\s+of": r"many",
                r"\bin\s+order\s+to": r"to",
                r"\bdue\s+to\s+the\s+fact\s+that": r"because",
            },
            "clarity_patterns": {
                r"\b(the\s+)?fact\s+that\b": r"that",
                r"\bfor\s+the\s+purpose\s+of": r"to",
                r"\bin\s+the\s+event\s+that": r"if",
            },
            "passive_voice": {
                r"\b(\w+)\s+was\s+(\w+ed|known|seen|made)\s+by\s+(\w+)": r"\3 \2 \1",
            }
        }
    
    def _initialize_style_analyzers(self) -> Dict[str, Any]:
        """Initialize style analysis components"""
        return {
            "formal": {
                "indicators": ["shall", "ought", "furthermore", "nevertheless", "consequently"],
                "avoid": ["gonna", "wanna", "kinda", "sorta"],
                "sentence_length": {"min": 15, "max": 30},
                "vocabulary_level": "advanced"
            },
            "casual": {
                "indicators": ["hey", "cool", "awesome", "totally", "basically"],
                "prefer": ["you'll", "we'll", "it's", "that's"],
                "sentence_length": {"min": 8, "max": 20},
                "vocabulary_level": "conversational"
            },
            "academic": {
                "indicators": ["furthermore", "moreover", "consequently", "thus", "hence"],
                "structure": "complex",
                "citations_expected": True,
                "vocabulary_level": "scholarly"
            },
            "creative": {
                "indicators": ["vivid", "imagery", "metaphor", "narrative"],
                "variety": "high",
                "emotion": "expressive",
                "originality_threshold": 0.9,
                "vocabulary_level": "varied"
            }
        }
    
    def _setup_readability_metrics(self) -> Dict[str, Any]:
        """Setup readability calculation methods"""
        return {
            "flesch_kincaid": {
                "target_grade": 8,
                "weight": 0.3
            },
            "gunning_fog": {
                "target_index": 12,
                "weight": 0.3
            },
            "automated_readability": {
                "target_grade": 10,
                "weight": 0.2
            },
            "coleman_liau": {
                "target_grade": 9,
                "weight": 0.2
            }
        }
    
    def _load_vocabulary_tools(self) -> Dict[str, Any]:
        """Load vocabulary enhancement tools"""
        return {
            "synonym_engine": {
                "common_replacements": {
                    "good": ["excellent", "outstanding", "remarkable", "exceptional"],
                    "bad": ["poor", "inadequate", "substandard", "deficient"],
                    "big": ["large", "substantial", "significant", "considerable"],
                    "small": ["minor", "minimal", "compact", "limited"],
                    "very": ["extremely", "remarkably", "exceptionally", "significantly"]
                }
            },
            "domain_vocabulary": {
                "technical": ["implement", "optimize", "configure", "integrate"],
                "business": ["leverage", "synergize", "streamline", "maximize"],
                "academic": ["analyze", "evaluate", "synthesize", "investigate"],
                "creative": ["craft", "envision", "inspire", "innovate"]
            },
            "complexity_levels": {
                "simple": {"syllables": {"max": 2}, "frequency": "high"},
                "moderate": {"syllables": {"max": 4}, "frequency": "medium"},
                "advanced": {"syllables": {"min": 3}, "frequency": "low"}
            }
        }
    
    async def _enhance_content(self, payload: Dict) -> Dict[str, Any]:
        """Comprehensive content enhancement"""
        content = payload.get("content", "")
        enhancement_types = payload.get("enhancement_types", ["grammar", "style", "readability"])
        enhancement_level = EnhancementLevel(payload.get("level", "moderate"))
        target_audience = payload.get("target_audience", "general")
        domain = payload.get("domain", "general")
        
        start_time = time.time()
        
        with self.tracer.start_as_current_span("content_enhancement") as span:
            span.set_attribute("content_length", len(content))
            span.set_attribute("enhancement_level", enhancement_level.value)
            
            enhancements = []
            enhanced_content = content
            
            # Apply enhancements in optimal order
            enhancement_pipeline = self._create_enhancement_pipeline(enhancement_types, enhancement_level)
            
            for enhancement_step in enhancement_pipeline:
                step_result = await enhancement_step(enhanced_content, payload)
                if step_result["enhanced"]:
                    enhanced_content = step_result["content"]
                    enhancements.extend(step_result["enhancements"])
            
            # Calculate overall improvement score
            improvement_score = self._calculate_improvement_score(content, enhanced_content, enhancements)
            
            # Learn from this enhancement
            await self._update_enhancement_patterns(content, enhanced_content, enhancements, payload)
            
            processing_time = (time.time() - start_time) * 1000
            
            result = EnhancementResult(
                original_content=content,
                enhanced_content=enhanced_content,
                enhancements=enhancements,
                overall_improvement_score=improvement_score,
                processing_time_ms=processing_time
            )
            
            # Update statistics
            self._update_enhancement_stats(result)
            
            self.logger.info("Content enhancement completed",
                           improvement_score=improvement_score,
                           enhancements_count=len(enhancements),
                           processing_time=processing_time)
            
            return {
                "enhanced": True,
                "original_content": result.original_content,
                "enhanced_content": result.enhanced_content,
                "improvement_score": result.overall_improvement_score,
                "enhancements": [
                    {
                        "type": e.enhancement_type.value,
                        "original": e.original_text,
                        "enhanced": e.enhanced_text,
                        "confidence": e.confidence_score,
                        "explanation": e.explanation,
                        "suggestions": e.suggestions
                    }
                    for e in result.enhancements
                ],
                "processing_time_ms": result.processing_time_ms,
                "metadata": {
                    "enhancement_level": enhancement_level.value,
                    "target_audience": target_audience,
                    "domain": domain
                }
            }
    
    def _create_enhancement_pipeline(self, enhancement_types: List[str], level: EnhancementLevel) -> List:
        """Create optimal enhancement processing pipeline"""
        pipeline = []
        
        # Order matters for optimal results
        if "grammar" in enhancement_types:
            pipeline.append(self._apply_grammar_enhancement)
        
        if "clarity" in enhancement_types:
            pipeline.append(self._apply_clarity_enhancement)
        
        if "vocabulary" in enhancement_types:
            pipeline.append(self._apply_vocabulary_enhancement)
        
        if "structure" in enhancement_types:
            pipeline.append(self._apply_structure_enhancement)
        
        if "style" in enhancement_types:
            pipeline.append(self._apply_style_enhancement)
        
        if "readability" in enhancement_types:
            pipeline.append(self._apply_readability_enhancement)
        
        if "tone" in enhancement_types:
            pipeline.append(self._apply_tone_enhancement)
        
        if "engagement" in enhancement_types:
            pipeline.append(self._apply_engagement_enhancement)
        
        return pipeline
    
    async def _apply_grammar_enhancement(self, content: str, payload: Dict) -> Dict[str, Any]:
        """Apply grammar corrections and improvements"""
        enhanced_content = content
        enhancements = []
        
        # Apply grammar patterns
        for pattern_type, patterns in self.grammar_patterns.items():
            for pattern, replacement in patterns.items():
                if callable(replacement):
                    # Dynamic replacement
                    matches = re.finditer(pattern, enhanced_content)
                    for match in reversed(list(matches)):
                        original = match.group(0)
                        enhanced = replacement(match)
                        if enhanced != original:
                            enhanced_content = enhanced_content[:match.start()] + enhanced + enhanced_content[match.end():]
                            enhancements.append(Enhancement(
                                enhancement_id=str(uuid.uuid4()),
                                enhancement_type=EnhancementType.GRAMMAR,
                                original_text=original,
                                enhanced_text=enhanced,
                                confidence_score=0.9,
                                explanation=f"Applied dynamic grammar rule: {pattern_type}"
                            ))
                else:
                    # Static replacement
                    new_content, num_subs = re.subn(pattern, replacement, enhanced_content)
                    if num_subs > 0:
                        # This is a simplification; ideally, we'd track exact changes
                        enhancements.append(Enhancement(
                            enhancement_id=str(uuid.uuid4()),
                            enhancement_type=EnhancementType.GRAMMAR,
                            original_text="[multiple changes]",
                            enhanced_text="[multiple changes]",
                            confidence_score=0.9,
                            explanation=f"Applied static grammar rule: {pattern_type}",
                            metadata={"pattern": pattern, "replacement": replacement, "count": num_subs}
                        ))
                        enhanced_content = new_content
        
        return {"enhanced": True, "content": enhanced_content, "enhancements": enhancements}

    def _intensify_adjective(self, adjective: str) -> str:
        """Helper to replace 'very X' with a stronger adjective"""
        stronger_adjectives = {
            "good": "excellent", "bad": "terrible", "happy": "ecstatic",
            "sad": "miserable", "big": "enormous", "small": "tiny",
            "tired": "exhausted", "hungry": "ravenous", "angry": "furious"
        }
        return stronger_adjectives.get(adjective.lower(), adjective) # Return original if no stronger found

    async def _apply_clarity_enhancement(self, content: str, payload: Dict) -> Dict[str, Any]:
        """Apply clarity improvements (e.g., simplifying complex sentences) using LLM"""
        enhanced_content = content
        enhancements = []
        
        # This would involve calling the LLM agent for clarity improvements
        if self.llm_collaboration_enabled:
            self.logger.debug("Calling LLM for clarity enhancement (placeholder).")
            # Simulate LLM call
            llm_response = {"enhanced_text": f"[Clarity enhanced version of: {content[:50]}...]", "changes": []}
            if len(content) > 100 and "complex sentence" in content.lower(): # Simple trigger
                enhanced_content = llm_response["enhanced_text"]
                enhancements.append(Enhancement(
                    enhancement_id=str(uuid.uuid4()),
                    enhancement_type=EnhancementType.CLARITY,
                    original_text=content,
                    enhanced_text=enhanced_content,
                    confidence_score=0.8,
                    explanation="Simplified complex sentences for better clarity."
                ))
        
        return {"enhanced": True, "content": enhanced_content, "enhancements": enhancements}

    async def _apply_vocabulary_enhancement(self, content: str, payload: Dict) -> Dict[str, Any]:
        """Apply vocabulary improvements (e.g., synonym replacement, domain-specific terms) using LLM"""
        enhanced_content = content
        enhancements = []
        
        if self.llm_collaboration_enabled:
            self.logger.debug("Calling LLM for vocabulary enhancement (placeholder).")
            # Simulate LLM call for synonym replacement or domain-specific terms
            llm_response = {"enhanced_text": f"[Vocabulary enhanced version of: {content[:50]}...]", "changes": []}
            if "good" in content.lower(): # Simple trigger
                enhanced_content = content.replace("good", "excellent") # Direct replacement for demo
                enhancements.append(Enhancement(
                    enhancement_id=str(uuid.uuid4()),
                    enhancement_type=EnhancementType.VOCABULARY,
                    original_text="good",
                    enhanced_text="excellent",
                    confidence_score=0.85,
                    explanation="Replaced common word with a stronger synonym."
                ))
        
        return {"enhanced": True, "content": enhanced_content, "enhancements": enhancements}

    async def _apply_structure_enhancement(self, content: str, payload: Dict) -> Dict[str, Any]:
        """Apply structural improvements (e.g., paragraph breaks, logical flow) using LLM"""
        enhanced_content = content
        enhancements = []
        
        if self.llm_collaboration_enabled:
            self.logger.debug("Calling LLM for structure enhancement (placeholder).")
            # Simulate LLM call for structural improvements
            llm_response = {"enhanced_text": f"[Structure enhanced version of: {content[:50]}...]", "changes": []}
            if len(content.split("\n\n")) < 2 and len(content.split()) > 200: # Long single paragraph
                enhanced_content = f"[Intro paragraph]\n\n[Body paragraph]\n\n[Conclusion paragraph]" # Simplified structural change
                enhancements.append(Enhancement(
                    enhancement_id=str(uuid.uuid4()),
                    enhancement_type=EnhancementType.STRUCTURE,
                    original_text=content,
                    enhanced_text=enhanced_content,
                    confidence_score=0.75,
                    explanation="Improved content structure with better paragraphing."
                ))
        
        return {"enhanced": True, "content": enhanced_content, "enhancements": enhancements}

    async def _apply_style_enhancement(self, content: str, payload: Dict) -> Dict[str, Any]:
        """Apply style adaptations based on target style guide using LLM"""
        enhanced_content = content
        enhancements = []
        target_style = payload.get("target_style", "technical")
        
        if self.llm_collaboration_enabled:
            self.logger.debug(f"Calling LLM for style enhancement ({target_style}) (placeholder).")
            # Simulate LLM call for style adaptation
            llm_response = {"enhanced_text": f"[Style ({target_style}) adapted version of: {content[:50]}...]", "changes": []}
            if target_style == "formal" and "lol" in content.lower():
                enhanced_content = content.replace("lol", "chuckle") # Simple style change
                enhancements.append(Enhancement(
                    enhancement_id=str(uuid.uuid4()),
                    enhancement_type=EnhancementType.STYLE,
                    original_text="lol",
                    enhanced_text="chuckle",
                    confidence_score=0.8,
                    explanation="Adjusted informal language to a more formal tone."
                ))
        
        return {"enhanced": True, "content": enhanced_content, "enhancements": enhancements}

    async def _apply_readability_enhancement(self, content: str, payload: Dict) -> Dict[str, Any]:
        """Apply readability optimizations (e.g., simplifying sentences, reducing jargon) using LLM"""
        enhanced_content = content
        enhancements = []
        target_grade = payload.get("target_grade_level", 8)
        
        if self.llm_collaboration_enabled:
            self.logger.debug(f"Calling LLM for readability enhancement (target grade {target_grade}) (placeholder).")
            # Simulate LLM call for readability optimization
            llm_response = {"enhanced_text": f"[Readability enhanced version (grade {target_grade}) of: {content[:50]}...]", "changes": []}
            # Simple check for long sentences
            if len(content.split()) > 50 and len(content.split(".")) < 2: # Very long single sentence
                enhanced_content = f"[Simplified first part]. [Simplified second part]." # Placeholder
                enhancements.append(Enhancement(
                    enhancement_id=str(uuid.uuid4()),
                    enhancement_type=EnhancementType.READABILITY,
                    original_text=content,
                    enhanced_text=enhanced_content,
                    confidence_score=0.85,
                    explanation="Simplified long sentences for improved readability."
                ))
        
        return {"enhanced": True, "content": enhanced_content, "enhancements": enhancements}

    async def _apply_tone_enhancement(self, content: str, payload: Dict) -> Dict[str, Any]:
        """Apply tone adjustments (e.g., making content more persuasive, friendly) using LLM"""
        enhanced_content = content
        enhancements = []
        target_tone = payload.get("target_tone", "persuasive")
        
        if self.llm_collaboration_enabled:
            self.logger.debug(f"Calling LLM for tone enhancement ({target_tone}) (placeholder).")
            # Simulate LLM call for tone adjustment
            llm_response = {"enhanced_text": f"[Tone ({target_tone}) adjusted version of: {content[:50]}...]", "changes": []}
            if target_tone == "persuasive" and "buy this" not in content.lower():
                enhanced_content = f"{content}. You should definitely consider this!" # Simple persuasive addition
                enhancements.append(Enhancement(
                    enhancement_id=str(uuid.uuid4()),
                    enhancement_type=EnhancementType.TONE,
                    original_text=content,
                    enhanced_text=enhanced_content,
                    confidence_score=0.7,
                    explanation="Adjusted tone to be more persuasive."
                ))
        
        return {"enhanced": True, "content": enhanced_content, "enhancements": enhancements}

    async def _apply_engagement_enhancement(self, content: str, payload: Dict) -> Dict[str, Any]:
        """Apply enhancements to increase content engagement using LLM"""
        enhanced_content = content
        enhancements = []
        
        if self.llm_collaboration_enabled:
            self.logger.debug("Calling LLM for engagement enhancement (placeholder).")
            # Simulate LLM call for engagement improvements
            llm_response = {"enhanced_text": f"[Engagement enhanced version of: {content[:50]}...]", "changes": []}
            if "question" not in content.lower() and len(content.split()) > 50:
                enhanced_content = f"{content}\n\nWhat do you think?" # Simple engagement addition
                enhancements.append(Enhancement(
                    enhancement_id=str(uuid.uuid4()),
                    enhancement_type=EnhancementType.ENGAGEMENT,
                    original_text=content,
                    enhanced_text=enhanced_content,
                    confidence_score=0.65,
                    explanation="Added an engaging question to encourage reader interaction."
                ))
        
        return {"enhanced": True, "content": enhanced_content, "enhancements": enhancements}

    async def _grammar_check(self, payload: Dict) -> Dict[str, Any]:
        """Perform grammar check and return suggestions"""
        content = payload.get("content", "")
        enhanced_result = await self._apply_grammar_enhancement(content, payload)
        return {"original_content": content, "enhanced_content": enhanced_result["content"], "enhancements": enhanced_result["enhancements"]}

    async def _style_adaptation(self, payload: Dict) -> Dict[str, Any]:
        """Adapt content style based on target style guide"""
        content = payload.get("content", "")
        enhanced_result = await self._apply_style_enhancement(content, payload)
        return {"original_content": content, "enhanced_content": enhanced_result["content"], "enhancements": enhanced_result["enhancements"]}

    async def _readability_optimization(self, payload: Dict) -> Dict[str, Any]:
        """Optimize content for better readability"""
        content = payload.get("content", "")
        enhanced_result = await self._apply_readability_enhancement(content, payload)
        return {"original_content": content, "enhanced_content": enhanced_result["content"], "enhancements": enhanced_result["enhancements"]}

    async def _vocabulary_enhancement(self, payload: Dict) -> Dict[str, Any]:
        """Enhance vocabulary using synonyms or domain-specific terms"""
        content = payload.get("content", "")
        enhanced_result = await self._apply_vocabulary_enhancement(content, payload)
        return {"original_content": content, "enhanced_content": enhanced_result["content"], "enhancements": enhanced_result["enhancements"]}

    async def _structure_improvement(self, payload: Dict) -> Dict[str, Any]:
        """Improve content structure and flow"""
        content = payload.get("content", "")
        enhanced_result = await self._apply_structure_enhancement(content, payload)
        return {"original_content": content, "enhanced_content": enhanced_result["content"], "enhancements": enhanced_result["enhancements"]}

    async def _content_expansion(self, payload: Dict) -> Dict[str, Any]:
        """Expand content based on a prompt or existing text using LLM"""
        content = payload.get("content", "")
        prompt = payload.get("prompt", "Expand on the following:")
        
        if self.llm_collaboration_enabled:
            self.logger.debug("Calling LLM for content expansion (placeholder).")
            # Simulate LLM call
            expanded_text = f"[Expanded content based on: {content[:50]}... and prompt: {prompt}]. This expansion provides more details and examples to enrich the original text."
            enhancement = Enhancement(
                enhancement_id=str(uuid.uuid4()),
                enhancement_type=EnhancementType.TECHNICAL, # Or a new type like EXPANSION
                original_text=content,
                enhanced_text=expanded_text,
                confidence_score=0.9,
                explanation="Content expanded using LLM to provide more detail."
            )
            return {"original_content": content, "enhanced_content": expanded_text, "enhancements": [enhancement]}
        else:
            raise RuntimeError("LLM collaboration not enabled for content expansion.")

    async def _content_compression(self, payload: Dict) -> Dict[str, Any]:
        """Compress content while retaining key information using LLM"""
        content = payload.get("content", "")
        target_length_ratio = payload.get("target_length_ratio", 0.5) # e.g., 0.5 for 50% reduction
        
        if self.llm_collaboration_enabled:
            self.logger.debug("Calling LLM for content compression (placeholder).")
            # Simulate LLM call
            compressed_text = f"[Compressed content (target {target_length_ratio*100:.0f}%) of: {content[:50]}...]. Key information retained and summarized for brevity."
            enhancement = Enhancement(
                enhancement_id=str(uuid.uuid4()),
                enhancement_type=EnhancementType.TECHNICAL, # Or a new type like COMPRESSION
                original_text=content,
                enhanced_text=compressed_text,
                confidence_score=0.9,
                explanation="Content compressed using LLM to reduce length."
            )
            return {"original_content": content, "enhanced_content": compressed_text, "enhancements": [enhancement]}
        else:
            raise RuntimeError("LLM collaboration not enabled for content compression.")

    async def _tone_adjustment(self, payload: Dict) -> Dict[str, Any]:
        """Adjust the tone of the content using LLM"""
        content = payload.get("content", "")
        enhanced_result = await self._apply_tone_enhancement(content, payload)
        return {"original_content": content, "enhanced_content": enhanced_result["content"], "enhancements": enhanced_result["enhancements"]}

    async def _collaborative_enhancement(self, msg):
        """Handle collaborative enhancement requests from other agents"""
        try:
            data = json.loads(msg.data.decode())
            content_id = data["content_id"]
            original_content = data["original_content"]
            enhancement_types = data.get("enhancement_types", ["grammar", "style"])
            enhancement_level = data.get("level", "moderate")
            
            self.logger.info("Received collaborative enhancement request", content_id=content_id)
            
            # Perform the enhancement
            enhancement_payload = {
                "content": original_content,
                "enhancement_types": enhancement_types,
                "level": enhancement_level
            }
            result = await self._enhance_content(enhancement_payload)
            
            # Cache the result for potential future use or for the requesting agent to fetch
            self.collaborative_enhancement_cache[content_id] = result
            
            # Publish a response or event indicating completion
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"status": "enhancement_completed", "content_id": content_id, "enhanced_content_preview": result["enhanced_content"][:200]}).encode())
            
        except Exception as e:
            self.logger.error("Error handling collaborative enhancement", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_grammar_enhancement(self, msg):
        """Handle direct grammar enhancement requests"""
        try:
            data = json.loads(msg.data.decode())
            content = data["content"]
            result = await self._grammar_check({"content": content})
            await self._publish(msg.reply, json.dumps(result).encode())
        except Exception as e:
            self.logger.error("Error in _handle_grammar_enhancement", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_style_enhancement(self, msg):
        """Handle direct style enhancement requests"""
        try:
            data = json.loads(msg.data.decode())
            content = data["content"]
            target_style = data.get("target_style", "technical")
            result = await self._style_adaptation({"content": content, "target_style": target_style})
            await self._publish(msg.reply, json.dumps(result).encode())
        except Exception as e:
            self.logger.error("Error in _handle_style_enhancement", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_readability_enhancement(self, msg):
        """Handle direct readability enhancement requests"""
        try:
            data = json.loads(msg.data.decode())
            content = data["content"]
            target_grade_level = data.get("target_grade_level", 8)
            result = await self._readability_optimization({"content": content, "target_grade_level": target_grade_level})
            await self._publish(msg.reply, json.dumps(result).encode())
        except Exception as e:
            self.logger.error("Error in _handle_readability_enhancement", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_batch_enhancement(self, msg):
        """Handle batch enhancement requests"""
        try:
            data = json.loads(msg.data.decode())
            batch_items = data.get("batch_items", []) # List of {content_id, content, enhancement_types, ...}
            
            results = []
            for item in batch_items:
                try:
                    content_id = item.get("content_id", str(uuid.uuid4()))
                    content = item["content"]
                    enhancement_types = item.get("enhancement_types", ["grammar", "style"])
                    enhancement_level = item.get("level", "moderate")
                    
                    enhancement_payload = {
                        "content": content,
                        "enhancement_types": enhancement_types,
                        "level": enhancement_level
                    }
                    result = await self._enhance_content(enhancement_payload)
                    results.append({"content_id": content_id, "result": result})
                except Exception as e:
                    self.logger.error(f"Error processing batch item {item.get("content_id")}: {e}", traceback=traceback.format_exc())
                    results.append({"content_id": item.get("content_id"), "error": str(e)})
            
            await self._publish(msg.reply, json.dumps({"batch_results": results, "total_items": len(batch_items)}).encode())
        except Exception as e:
            self.logger.error("Error in _handle_batch_enhancement", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_user_feedback(self, msg):
        """Process user feedback to improve enhancement models"""
        try:
            data = json.loads(msg.data.decode())
            enhancement_id = data["enhancement_id"]
            feedback_type = data["feedback_type"] # e.g., "good", "bad", "irrelevant"
            details = data.get("details", {})

            self.user_preferences[enhancement_id] = self.user_preferences.get(enhancement_id, [])
            self.user_preferences[enhancement_id].append({"type": feedback_type, "details": details, "timestamp": time.time()})
            self.logger.info("Received user feedback for enhancement", enhancement_id=enhancement_id, feedback_type=feedback_type)
            
            # In a real system, this would trigger model retraining or rule adjustments
            await self._publish(msg.reply, json.dumps({"status": "feedback_received"}).encode())
        except Exception as e:
            self.logger.error("Error processing user feedback", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _optimize_enhancement_patterns(self):
        """Background task to optimize enhancement patterns based on feedback and performance"""
        while not self._shutdown_event.is_set():
            try:
                # This would involve analyzing self.enhancement_history and self.user_preferences
                # to refine grammar rules, style guides, and LLM prompts.
                self.logger.debug("Optimizing enhancement patterns (placeholder).")
                await asyncio.sleep(3600 * 6) # Optimize every 6 hours
            except Exception as e:
                self.logger.error(f"Enhancement pattern optimization failed: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(3600)

    async def _update_domain_knowledge(self):
        """Background task to update domain-specific knowledge for targeted enhancements"""
        while not self._shutdown_event.is_set():
            try:
                # This would fetch new domain-specific terminology, style guides, etc.
                self.logger.debug("Updating domain knowledge (placeholder).")
                await asyncio.sleep(3600 * 24) # Update once a day
            except Exception as e:
                self.logger.error(f"Domain knowledge update failed: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(3600)

    def _calculate_improvement_score(self, original: str, enhanced: str, enhancements: List[Enhancement]) -> float:
        """Calculate an overall improvement score based on changes and confidence"""
        # This is a complex metric and would depend on the specific goals of enhancement.
        # For simplicity, we'll use a basic heuristic.
        
        # Difference in content length (longer is not always better, but indicates change)
        len_diff_ratio = abs(len(enhanced) - len(original)) / max(1, len(original))
        
        # Number of enhancements applied and their confidence
        total_confidence = sum(e.confidence_score for e in enhancements)
        avg_confidence = total_confidence / max(1, len(enhancements))
        
        # Simple heuristic: more changes with high confidence -> higher score
        # This needs to be refined with actual quality metrics (e.g., from ExaminationAgent)
        score = (avg_confidence * 0.7) + (min(len_diff_ratio, 0.5) * 0.3) # Cap length diff impact
        
        return min(1.0, score) # Score between 0 and 1

    def _update_enhancement_stats(self, result: EnhancementResult):
        """Update internal statistics based on enhancement result"""
        self.enhancement_stats["total_enhancements"] += 1
        for enhancement in result.enhancements:
            self.enhancement_stats["enhancement_types_count"][enhancement.enhancement_type.value] += 1
        
        # Update average improvement score
        current_avg = self.enhancement_stats["average_improvement_score"]
        total_enh = self.enhancement_stats["total_enhancements"]
        self.enhancement_stats["average_improvement_score"] = \
            (current_avg * (total_enh - 1) + result.overall_improvement_score) / total_enh

    def _get_agent_metrics(self) -> Dict[str, Any]:
        """Provide Enhancement agent specific metrics."""
        base_metrics = super()._get_agent_metrics()
        base_metrics.update({
            "total_enhancements": self.enhancement_stats["total_enhancements"],
            "average_improvement_score": self.enhancement_stats["average_improvement_score"],
            "enhancement_types_count": dict(self.enhancement_stats["enhancement_types_count"]),
            "active_user_preferences_count": len(self.user_preferences)
        })
        return base_metrics


if __name__ == "__main__":
    config = AgentConfig(
        name="enhancement_agent",
        agent_type="enhancement",
        capabilities=[
            "enhance_content", "grammar_check", "style_adaptation",
            "readability_optimization", "vocabulary_enhancement", "structure_improvement",
            "content_expansion", "content_compression", "tone_adjustment",
            "collaborative_enhancement"
        ],
        nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://agent:secure_password@postgres:5432/ymera"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
        consul_url=os.getenv("CONSUL_URL", "http://consul:8500"),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )
    
    agent = EnhancementAgent(config)
    asyncio.run(agent.run())

