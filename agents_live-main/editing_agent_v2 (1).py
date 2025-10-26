"""
Advanced Editing Agent - Production Ready v2.0
Handles content editing, proofreading, style improvement, and collaborative editing
Upgraded to use enhanced BaseAgent with full production features
"""

import asyncio
import json
import time
import re
import os
import traceback
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import difflib
from datetime import datetime

# External libraries (ensure these are in requirements.txt)
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    from textstat import flesch_reading_ease, flesch_kincaid_grade
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False

try:
    import language_tool_python
    LANGUAGETOOL_AVAILABLE = True
except ImportError:
    LANGUAGETOOL_AVAILABLE = False

from base_agent import (
    BaseAgent, 
    AgentConfig, 
    TaskRequest, 
    Priority, 
    AgentState,
    ConnectionState
)


class EditType(Enum):
    """Types of edits that can be suggested"""
    GRAMMAR = "grammar"
    STYLE = "style"
    CLARITY = "clarity"
    TONE = "tone"
    STRUCTURE = "structure"
    FACT_CHECK = "fact_check"
    PLAGIARISM = "plagiarism"
    TRANSLATION = "translation"


class ContentType(Enum):
    """Types of content that can be edited"""
    ARTICLE = "article"
    EMAIL = "email"
    PROPOSAL = "proposal"
    REPORT = "report"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    MARKETING = "marketing"
    ACADEMIC = "academic"


class EditingMode(Enum):
    """Intensity levels for editing"""
    LIGHT = "light"              # Minor corrections only
    MODERATE = "moderate"         # Grammar and clarity improvements
    HEAVY = "heavy"              # Significant restructuring and rewriting
    COLLABORATIVE = "collaborative"  # Track changes mode


@dataclass
class EditSuggestion:
    """Represents a single editing suggestion"""
    id: str
    edit_type: EditType
    original_text: str
    suggested_text: str
    reason: str
    confidence: float
    position: tuple  # (start, end)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "edit_type": self.edit_type.value,
            "original_text": self.original_text,
            "suggested_text": self.suggested_text,
            "reason": self.reason,
            "confidence": self.confidence,
            "position": self.position,
            "metadata": self.metadata
        }


@dataclass
class EditingSession:
    """Represents an active editing session"""
    session_id: str
    document_id: str
    user_id: str
    content_type: ContentType
    editing_mode: EditingMode
    original_content: str
    current_content: str
    suggestions: List[EditSuggestion] = field(default_factory=list)
    applied_edits: List[EditSuggestion] = field(default_factory=list)
    version_history: List[Dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "content_type": self.content_type.value,
            "editing_mode": self.editing_mode.value,
            "original_content": self.original_content,
            "current_content": self.current_content,
            "suggestions_count": len(self.suggestions),
            "applied_edits_count": len(self.applied_edits),
            "version_count": len(self.version_history),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class ContentAnalysis:
    """Results of content analysis"""
    readability_score: float
    grade_level: float
    sentiment_score: float
    tone_analysis: Dict[str, float]
    word_count: int
    sentence_count: int
    paragraph_count: int
    issues_found: List[Dict]
    suggestions_count: int


class EditingAgent(BaseAgent):
    """
    Advanced Editing Agent with:
    - Multi-language grammar and style checking
    - AI-powered content improvement suggestions
    - Collaborative editing with version control
    - Tone and style analysis
    - Readability optimization
    - Real-time collaborative editing
    - Full integration with enhanced BaseAgent
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Editing sessions
        self.active_sessions: Dict[str, EditingSession] = {}
        
        # Language tools (initialized asynchronously)
        self.grammar_tool = None
        self.nlp_models = {}
        self.sentiment_analyzer = None
        self.tools_initialized = False
        
        # Style guides and preferences
        self.style_guides = {
            "ap": {},
            "chicago": {},
            "mla": {},
            "apa": {},
            "technical": {}
        }
        
        # Content patterns
        self.content_patterns = {}
        
        # Performance metrics
        self.editing_metrics = {
            "total_sessions": 0,
            "active_sessions": 0,
            "suggestions_generated": 0,
            "suggestions_accepted": 0,
            "average_improvement_score": 0.0,
            "processing_time_avg": 0.0,
            "analysis_count": 0,
            "errors_encountered": 0
        }
    
    async def _setup_subscriptions(self):
        """Override to add custom subscriptions"""
        await super()._setup_subscriptions()
        
        # Subscribe to editing tasks
        await self._subscribe(
            f"agent.{self.config.name}.edit",
            self._handle_edit_request,
            queue_group=f"{self.config.agent_type}-edit"
        )
        
        # Subscribe to collaborative editing events
        await self._subscribe(
            f"editing.collaborative.*.update",
            self._handle_collaborative_event,
            queue_group=f"{self.config.agent_type}-collab"
        )
        
        # Subscribe to document events
        await self._subscribe(
            f"document.*",
            self._handle_document_event,
            queue_group=f"{self.config.agent_type}-docs"
        )
        
        self.logger.info("Editing agent subscriptions configured")
    
    async def _start_background_tasks(self):
        """Override to add custom background tasks"""
        await super()._start_background_tasks()
        
        # Initialize language tools
        task = asyncio.create_task(self._initialize_tools())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Session cleanup manager
        task = asyncio.create_task(self._session_manager())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Content analyzer monitor
        task = asyncio.create_task(self._content_analyzer_monitor())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Metrics reporter
        task = asyncio.create_task(self._metrics_reporter())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        self.logger.info("Editing agent background tasks started")
    
    async def _initialize_tools(self):
        """Initialize NLP and language tools"""
        try:
            self.logger.info("Initializing language tools...")
            
            # Initialize LanguageTool for grammar checking
            if LANGUAGETOOL_AVAILABLE:
                try:
                    self.grammar_tool = language_tool_python.LanguageTool("en-US")
                    self.logger.info("LanguageTool initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize LanguageTool: {e}")
            else:
                self.logger.warning("language_tool_python not available")
            
            # Initialize spaCy models
            if SPACY_AVAILABLE:
                try:
                    self.nlp_models["en"] = spacy.load("en_core_web_sm")
                    self.logger.info("spaCy model loaded successfully")
                except OSError:
                    self.logger.warning("spaCy model 'en_core_web_sm' not found")
                except Exception as e:
                    self.logger.error(f"Failed to load spaCy model: {e}")
            else:
                self.logger.warning("spaCy not available")
            
            # Initialize sentiment analyzer
            if NLTK_AVAILABLE:
                try:
                    # Download required NLTK data
                    try:
                        nltk.data.find("sentiment/vader_lexicon.zip")
                    except LookupError:
                        nltk.download("vader_lexicon", quiet=True)
                    
                    try:
                        nltk.data.find("tokenizers/punkt")
                    except LookupError:
                        nltk.download("punkt", quiet=True)
                    
                    self.sentiment_analyzer = SentimentIntensityAnalyzer()
                    self.logger.info("NLTK sentiment analyzer initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize NLTK: {e}")
            else:
                self.logger.warning("NLTK not available")
            
            self.tools_initialized = True
            self.logger.info("Language tools initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize language tools: {e}")
            self.tools_initialized = False
    
    async def _handle_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Handle incoming tasks with proper structure"""
        
        try:
            task_type = task_request.task_type
            payload = task_request.payload
            
            self.logger.info(
                f"Processing editing task",
                task_id=task_request.task_id,
                task_type=task_type,
                priority=task_request.priority.name
            )
            
            # Route to appropriate handler
            if task_type == "start_editing_session":
                result = await self._start_editing_session(payload)
            
            elif task_type == "analyze_content":
                result = await self._analyze_content(payload)
            
            elif task_type == "generate_suggestions":
                result = await self._generate_suggestions(payload)
            
            elif task_type == "apply_edits":
                result = await self._apply_edits(payload)
            
            elif task_type == "check_grammar":
                result = await self._check_grammar(payload)
            
            elif task_type == "improve_style":
                result = await self._improve_style(payload)
            
            elif task_type == "optimize_readability":
                result = await self._optimize_readability(payload)
            
            elif task_type == "collaborative_edit":
                result = await self._collaborative_edit(payload)
            
            elif task_type == "version_control":
                result = await self._version_control(payload)
            
            elif task_type == "get_session_status":
                result = await self._get_session_status(payload)
            
            elif task_type == "close_session":
                result = await self._close_session(payload)
            
            else:
                # Call parent for unhandled tasks
                return await super()._handle_task(task_request)
            
            return {
                "status": "success",
                "task_id": task_request.task_id,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(
                f"Task processing failed",
                task_id=task_request.task_id,
                task_type=task_request.task_type,
                error=str(e),
                traceback=traceback.format_exc()
            )
            self.editing_metrics["errors_encountered"] += 1
            
            return {
                "status": "error",
                "task_id": task_request.task_id,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _start_editing_session(self, payload: Dict) -> Dict[str, Any]:
        """Start a new editing session"""
        document_id = payload.get("document_id", f"doc_{uuid.uuid4().hex[:8]}")
        user_id = payload.get("user_id", "anonymous")
        content = payload.get("content", "")
        content_type_str = payload.get("content_type", "article")
        editing_mode_str = payload.get("editing_mode", "moderate")
        
        try:
            content_type = ContentType(content_type_str)
            editing_mode = EditingMode(editing_mode_str)
        except ValueError as e:
            raise ValueError(f"Invalid content_type or editing_mode: {e}")
        
        session_id = f"edit_sess_{uuid.uuid4().hex[:12]}"
        
        session = EditingSession(
            session_id=session_id,
            document_id=document_id,
            user_id=user_id,
            content_type=content_type,
            editing_mode=editing_mode,
            original_content=content,
            current_content=content
        )
        
        self.active_sessions[session_id] = session
        self.editing_metrics["total_sessions"] += 1
        self.editing_metrics["active_sessions"] = len(self.active_sessions)
        
        # Store session in database for persistence
        await self._store_session(session)
        
        # Perform initial analysis
        analysis_result = await self._analyze_content({
            "content": content,
            "content_type": content_type.value
        })
        
        # Generate initial suggestions
        suggestions_result = await self._generate_suggestions({
            "session_id": session_id,
            "content": content,
            "editing_mode": editing_mode.value,
            "content_type": content_type.value
        })
        
        self.logger.info(
            "Editing session started",
            session_id=session_id,
            content_type=content_type.value,
            editing_mode=editing_mode.value,
            user_id=user_id
        )
        
        # Publish session created event
        await self._publish(
            f"editing.session.created",
            {
                "session_id": session_id,
                "document_id": document_id,
                "user_id": user_id,
                "timestamp": time.time()
            }
        )
        
        return {
            "session_id": session_id,
            "document_id": document_id,
            "content_analysis": analysis_result.get("analysis", {}),
            "initial_suggestions": suggestions_result.get("suggestions", []),
            "session_created": True
        }
    
    async def _analyze_content(self, payload: Dict) -> Dict[str, Any]:
        """Analyze content for various metrics"""
        content = payload.get("content", "")
        content_type = payload.get("content_type", "article")
        
        if not content.strip():
            return {"analysis": {"error": "No content provided"}}
        
        self.editing_metrics["analysis_count"] += 1
        
        try:
            # Basic metrics
            words = content.split()
            word_count = len(words)
            
            # Sentence tokenization
            if NLTK_AVAILABLE:
                sentences = nltk.sent_tokenize(content)
                sentence_count = len(sentences)
            else:
                sentence_count = content.count('.') + content.count('!') + content.count('?')
            
            paragraphs = [p for p in content.split("\n\n") if p.strip()]
            paragraph_count = len(paragraphs)
            
            # Readability analysis
            readability_score = 0.0
            grade_level = 0.0
            if TEXTSTAT_AVAILABLE and sentence_count > 0:
                try:
                    readability_score = flesch_reading_ease(content)
                    grade_level = flesch_kincaid_grade(content)
                except:
                    readability_score = 50.0
                    grade_level = 10.0
            
            # Sentiment analysis
            sentiment_scores = {}
            if self.sentiment_analyzer:
                try:
                    sentiment_scores = self.sentiment_analyzer.polarity_scores(content)
                except:
                    sentiment_scores = {"compound": 0.0}
            
            # Tone analysis
            tone_analysis = await self._analyze_tone(content)
            
            # Grammar and style issues
            issues = []
            if self.grammar_tool:
                try:
                    matches = self.grammar_tool.check(content)
                    issues = [
                        {
                            "type": "grammar" if match.category in ["Grammar", "Spelling"] else "style",
                            "message": match.message,
                            "offset": match.offset,
                            "length": match.errorLength,
                            "suggestions": match.replacements[:3] if match.replacements else [],
                            "category": match.category,
                            "rule_id": match.ruleId
                        }
                        for match in matches[:50]  # Limit to 50 issues
                    ]
                except Exception as e:
                    self.logger.warning(f"Grammar check failed: {e}")
            
            # Content-specific analysis
            content_specific = await self._analyze_content_specific(content, content_type)
            
            return {
                "analysis": {
                    "readability": {
                        "score": readability_score,
                        "grade_level": grade_level,
                        "interpretation": self._interpret_readability(readability_score)
                    },
                    "sentiment": {
                        "overall_score": sentiment_scores.get("compound", 0.0),
                        "detailed_scores": sentiment_scores,
                        "tone": tone_analysis
                    },
                    "structure": {
                        "word_count": word_count,
                        "sentence_count": sentence_count,
                        "paragraph_count": paragraph_count,
                        "avg_words_per_sentence": word_count / max(sentence_count, 1),
                        "avg_sentences_per_paragraph": sentence_count / max(paragraph_count, 1)
                    },
                    "issues": {
                        "grammar_issues": len([i for i in issues if i["type"] == "grammar"]),
                        "style_issues": len([i for i in issues if i["type"] == "style"]),
                        "total_issues": len(issues),
                        "details": issues[:20]  # Return top 20 for API response
                    },
                    "content_specific": content_specific
                }
            }
            
        except Exception as e:
            self.logger.error(f"Content analysis failed: {e}")
            return {"analysis": {"error": f"Analysis failed: {str(e)}"}}
    
    def _interpret_readability(self, score: float) -> str:
        """Interpret readability score"""
        if score >= 90:
            return "Very Easy"
        elif score >= 80:
            return "Easy"
        elif score >= 70:
            return "Fairly Easy"
        elif score >= 60:
            return "Standard"
        elif score >= 50:
            return "Fairly Difficult"
        elif score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"
    
    async def _analyze_tone(self, content: str) -> Dict[str, float]:
        """Analyze tone of content"""
        tones = {
            "formal": 0.0,
            "casual": 0.0,
            "professional": 0.0,
            "friendly": 0.0,
            "persuasive": 0.0,
            "informative": 0.0
        }
        
        content_lower = content.lower()
        
        # Simple keyword-based tone detection
        formal_patterns = r"(dear sir|madam|sincerely|regards|furthermore|therefore|hereby)"
        casual_patterns = r"(hi there|hey|cheers|lol|btw|gonna|wanna)"
        professional_patterns = r"(recommend|propose|strategy|objective|analysis|implement)"
        friendly_patterns = r"(please|thank you|appreciate|glad|happy|welcome)"
        persuasive_patterns = r"(should|must|benefit|advantage|essential|critical)"
        informative_patterns = r"(according to|research shows|data indicates|studies suggest)"
        
        if re.search(formal_patterns, content_lower):
            tones["formal"] = 0.8
            tones["professional"] = 0.7
        if re.search(casual_patterns, content_lower):
            tones["casual"] = 0.8
            tones["friendly"] = 0.6
        if re.search(professional_patterns, content_lower):
            tones["professional"] = 0.9
            tones["informative"] = 0.5
        if re.search(friendly_patterns, content_lower):
            tones["friendly"] = 0.8
        if re.search(persuasive_patterns, content_lower):
            tones["persuasive"] = 0.8
        if re.search(informative_patterns, content_lower):
            tones["informative"] = 0.9
        
        # Normalize
        total = sum(tones.values())
        if total > 0:
            tones = {k: v/total for k, v in tones.items()}
        
        return tones
    
    async def _analyze_content_specific(self, content: str, content_type: str) -> Dict[str, Any]:
        """Perform content-type specific analysis"""
        results = {}
        
        if content_type == ContentType.MARKETING.value:
            cta_patterns = [r"buy now", r"learn more", r"sign up", r"get started", r"try free"]
            found_ctas = [p for p in cta_patterns if re.search(p, content.lower())]
            results["call_to_actions_found"] = len(found_ctas)
            results["cta_phrases"] = found_ctas
        
        elif content_type == ContentType.TECHNICAL.value:
            code_blocks = len(re.findall(r"```.*?```", content, re.DOTALL))
            results["code_block_count"] = code_blocks
        
        elif content_type == ContentType.EMAIL.value:
            has_greeting = bool(re.search(r"^(dear|hi|hello)", content.lower()))
            has_closing = bool(re.search(r"(sincerely|regards|best|thanks)", content.lower()))
            results["has_greeting"] = has_greeting
            results["has_closing"] = has_closing
        
        return results
    
    async def _generate_suggestions(self, payload: Dict) -> Dict[str, Any]:
        """Generate editing suggestions"""
        session_id = payload.get("session_id")
        content = payload.get("content")
        editing_mode_str = payload.get("editing_mode", "moderate")
        content_type_str = payload.get("content_type", "article")
        
        if session_id and session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            editing_mode = session.editing_mode
            content_type = session.content_type
        else:
            try:
                editing_mode = EditingMode(editing_mode_str)
                content_type = ContentType(content_type_str)
            except ValueError:
                editing_mode = EditingMode.MODERATE
                content_type = ContentType.ARTICLE
        
        suggestions: List[EditSuggestion] = []
        
        # Grammar and spelling suggestions
        if self.grammar_tool:
            try:
                matches = self.grammar_tool.check(content)
                for match in matches:
                    if editing_mode == EditingMode.LIGHT and match.category not in ["Grammar", "Spelling"]:
                        continue
                    
                    if match.replacements:
                        suggestion = EditSuggestion(
                            id=str(uuid.uuid4()),
                            edit_type=EditType.GRAMMAR if match.category in ["Grammar", "Spelling"] else EditType.STYLE,
                            original_text=content[match.offset:match.offset + match.errorLength],
                            suggested_text=match.replacements[0],
                            reason=match.message,
                            confidence=0.9,
                            position=(match.offset, match.offset + match.errorLength),
                            metadata={
                                "category": match.category,
                                "rule_id": match.ruleId,
                                "all_suggestions": match.replacements[:5]
                            }
                        )
                        suggestions.append(suggestion)
            except Exception as e:
                self.logger.warning(f"Grammar check failed: {e}")
        
        # Style and clarity suggestions for moderate/heavy modes
        if editing_mode in [EditingMode.MODERATE, EditingMode.HEAVY]:
            if "en" in self.nlp_models:
                try:
                    doc = self.nlp_models["en"](content)
                    for sent in doc.sents:
                        # Long sentence detection
                        if len(sent.text.split()) > 30:
                            suggestion = EditSuggestion(
                                id=str(uuid.uuid4()),
                                edit_type=EditType.CLARITY,
                                original_text=sent.text,
                                suggested_text="[Consider splitting this sentence]",
                                reason="Long sentence detected. Consider breaking into shorter sentences for clarity.",
                                confidence=0.7,
                                position=(sent.start_char, sent.end_char),
                                metadata={"suggestion_type": "sentence_simplification"}
                            )
                            suggestions.append(suggestion)
                except Exception as e:
                    self.logger.warning(f"NLP analysis failed: {e}")
        
        # Update session suggestions if session exists
        if session_id and session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.suggestions = suggestions
            session.updated_at = time.time()
        
        self.editing_metrics["suggestions_generated"] += len(suggestions)
        
        return {
            "session_id": session_id,
            "suggestions": [s.to_dict() for s in suggestions],
            "suggestion_count": len(suggestions)
        }
    
    async def _apply_edits(self, payload: Dict) -> Dict[str, Any]:
        """Apply selected edits to content"""
        session_id = payload.get("session_id")
        edit_ids = payload.get("edit_ids", [])
        
        if not session_id or session_id not in self.active_sessions:
            raise ValueError("Invalid or expired editing session")
        
        session = self.active_sessions[session_id]
        original_content = session.current_content
        
        # Get edits to apply
        edits_to_apply = [s for s in session.suggestions if s.id in edit_ids]
        
        # Sort by position (reverse order to avoid index shifting)
        edits_to_apply.sort(key=lambda x: x.position[0], reverse=True)
        
        # Apply edits
        new_content = list(original_content)
        applied_count = 0
        
        for edit in edits_to_apply:
            start, end = edit.position
            if 0 <= start < len(original_content) and end <= len(original_content):
                new_content[start:end] = list(edit.suggested_text)
                session.applied_edits.append(edit)
                session.suggestions.remove(edit)
                applied_count += 1
        
        session.current_content = "".join(new_content)
        session.updated_at = time.time()
        
        # Add to version history
        session.version_history.append({
            "timestamp": time.time(),
            "content": session.current_content,
            "applied_edits": edit_ids,
            "version_id": str(uuid.uuid4())
        })
        
        # Update in database
        await self._update_session(session)
        
        self.editing_metrics["suggestions_accepted"] += applied_count
        
        return {
            "session_id": session_id,
            "applied_count": applied_count,
            "new_content": session.current_content,
            "version_id": session.version_history[-1]["version_id"]
        }
    
    async def _check_grammar(self, payload: Dict) -> Dict[str, Any]:
        """Perform grammar check"""
        content = payload.get("content", "")
        
        if not self.grammar_tool:
            return {"error": "Grammar tool not initialized", "issues": []}
        
        try:
            matches = self.grammar_tool.check(content)
            issues = [
                {
                    "message": match.message,
                    "replacements": match.replacements[:5],
                    "offset": match.offset,
                    "length": match.errorLength,
                    "context": match.context,
                    "rule_id": match.ruleId,
                    "category": match.category
                }
                for match in matches
            ]
            return {"issues": issues, "issue_count": len(issues)}
        except Exception as e:
            self.logger.error(f"Grammar check failed: {e}")
            return {"error": str(e), "issues": []}
    
    async def _improve_style(self, payload: Dict) -> Dict[str, Any]:
        """Improve writing style"""
        content = payload.get("content", "")
        style_guide = payload.get("style_guide", "technical")
        
        # This would integrate with LLM for actual style improvement
        self.logger.info(f"Style improvement requested with {style_guide} guide")
        
        return {
            "original_content": content,
            "improved_content": f"[Style improved according to {style_guide} guidelines]",
            "note": "LLM integration required for actual style improvement"
        }
    
    async def _optimize_readability(self, payload: Dict) -> Dict[str, Any]:
        """Optimize content for readability"""
        content = payload.get("content", "")
        target_grade = payload.get("target_grade_level", 8)
        
        # This would integrate with LLM for actual optimization
        self.logger.info(f"Readability optimization requested for grade level {target_grade}")
        
        return {
            "original_content": content,
            "optimized_content": f"[Content optimized for grade level {target_grade}]",
            "note": "LLM integration required for actual readability optimization"
        }
    
    async def _collaborative_edit(self, payload: Dict) -> Dict[str, Any]:
        """Handle collaborative editing events"""
        session_id = payload.get("session_id")
        user_id = payload.get("user_id")
        change_type = payload.get("change_type")
        position = payload.get("position")
        text = payload.get("text", "")
        
        if not session_id or session_id not in self.active_sessions:
            raise ValueError("Invalid or expired editing session")
        
        session = self.active_sessions[session_id]
        
        # Apply change based on type
        if change_type == "insert":
            pos = position or 0
            session.current_content = (
                session.current_content[:pos] + 
                text + 
                session.current_content[pos:]
            )
        elif change_type == "delete":
            start, end = position if isinstance(position, tuple) else (position, position + len(text))
            session.current_content = (
                session.current_content[:start] + 
                session.current_content[end:]
            )
        elif change_type == "replace":
            start, end = position if isinstance(position, tuple) else (position, position + len(text))
            session.current_content = (
                session.current_content[:start] + 
                text + 
                session.current_content[end:]
            )
        elif change_type == "replace_all":
            session.current_content = text
        
        session.updated_at = time.time()
        
        # Add to version history
        session.version_history.append({
            "timestamp": time.time(),
            "user_id": user_id,
            "change_type": change_type,
            "details": payload
        })
        
        # Broadcast to other collaborators
        await self._publish(
            f"editing.collaborative.{session_id}.update",
            {
                "session_id": session_id,
                "user_id": user_id,
                "change_type": change_type,
                "timestamp": time.time(),
                "content_preview": session.current_content[:200]
            }
        )
        
        return {
            "status": "change_applied",
            "session_id": session_id,
            "timestamp": time.time()
        }
    
    async def _version_control(self, payload: Dict) -> Dict[str, Any]:
        """Manage document versions"""
        session_id = payload.get("session_id")
        operation = payload.get("operation")
        version_id = payload.get("version_id")
        
        if not session_id or session_id not in self.active_sessions:
            raise ValueError("Invalid or expired editing session")
        
        session = self.active_sessions[session_id]
        
        if operation == "get_history":
            return {
                "session_id": session_id,
                "version_history": session.version_history,
                "current_version": len(session.version_history)
            }
        
        elif operation == "revert":
            version = next(
                (v for v in session.version_history if v.get("version_id") == version_id),
                None
            )
            if not version:
                raise ValueError(f"Version {version_id} not found")
            
            session.current_content = version["content"]
            session.updated_at = time.time()
            
            await self._update_session(session)
            
            return {
                "status": "reverted",
                "session_id": session_id,
                "version_id": version_id,
                "content_preview": session.current_content[:200]
            }
        
        elif operation == "save_version":
            new_version_id = str(uuid.uuid4())
            session.version_history.append({
                "timestamp": time.time(),
                "content": session.current_content,
                "version_id": new_version_id,
                "message": payload.get("message", "Manual save")
            })
            
            await self._update_session(session)
            
            return {
                "status": "version_saved",
                "session_id": session_id,
                "version_id": new_version_id
            }
        
        else:
            raise ValueError(f"Unknown version control operation: {operation}")
    
    async def _get_session_status(self, payload: Dict) -> Dict[str, Any]:
        """Get status of an editing session"""
        session_id = payload.get("session_id")
        
        if not session_id or session_id not in self.active_sessions:
            raise ValueError("Invalid or expired editing session")
        
        session = self.active_sessions[session_id]
        
        return {
            "session": session.to_dict(),
            "pending_suggestions": len(session.suggestions),
            "applied_edits": len(session.applied_edits),
            "versions": len(session.version_history)
        }
    
    async def _close_session(self, payload: Dict) -> Dict[str, Any]:
        """Close an editing session"""
        session_id = payload.get("session_id")
        
        if not session_id or session_id not in self.active_sessions:
            raise ValueError("Invalid or expired editing session")
        
        session = self.active_sessions[session_id]
        
        # Archive session to database
        await self._archive_session(session)
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        self.editing_metrics["active_sessions"] = len(self.active_sessions)
        
        # Publish session closed event
        await self._publish(
            f"editing.session.closed",
            {
                "session_id": session_id,
                "document_id": session.document_id,
                "timestamp": time.time()
            }
        )
        
        self.logger.info(f"Editing session closed", session_id=session_id)
        
        return {
            "status": "session_closed",
            "session_id": session_id,
            "final_content": session.current_content
        }
    
    async def _handle_edit_request(self, msg):
        """Handle direct edit requests"""
        try:
            data = json.loads(msg.data.decode())
            
            # Convert to TaskRequest format
            task_request = TaskRequest(
                task_id=data.get("task_id", str(uuid.uuid4())),
                task_type=data.get("task_type", "analyze_content"),
                payload=data.get("payload", {}),
                priority=Priority(data.get("priority", "medium"))
            )
            
            result = await self._handle_task(task_request)
            
            if msg.reply:
                await self._publish_raw(msg.reply, json.dumps(result).encode())
            
        except Exception as e:
            self.logger.error(f"Failed to handle edit request: {e}")
            if msg.reply:
                error_response = {
                    "status": "error",
                    "error": str(e)
                }
                await self._publish_raw(msg.reply, json.dumps(error_response).encode())
    
    async def _handle_collaborative_event(self, msg):
        """Handle collaborative editing events"""
        try:
            data = json.loads(msg.data.decode())
            session_id = data.get("session_id")
            
            if session_id and session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                # Update session based on event
                change_type = data.get("change_type")
                if change_type and data.get("new_content"):
                    session.current_content = data["new_content"]
                    session.updated_at = time.time()
                
                self.logger.info(
                    "Processed collaborative event",
                    session_id=session_id,
                    change_type=change_type
                )
        
        except Exception as e:
            self.logger.error(f"Failed to handle collaborative event: {e}")
    
    async def _handle_document_event(self, msg):
        """Handle document-related events"""
        try:
            data = json.loads(msg.data.decode())
            event_type = data.get("event_type")
            document_id = data.get("document_id")
            
            if event_type == "document_updated":
                # Update sessions related to this document
                for session_id, session in list(self.active_sessions.items()):
                    if session.document_id == document_id:
                        new_content = data.get("new_content")
                        if new_content:
                            session.current_content = new_content
                            session.updated_at = time.time()
                            
                            self.logger.info(
                                "Updated session from document event",
                                session_id=session_id,
                                document_id=document_id
                            )
            
            elif event_type == "document_deleted":
                # Close sessions related to this document
                sessions_to_close = [
                    s_id for s_id, s in self.active_sessions.items()
                    if s.document_id == document_id
                ]
                
                for session_id in sessions_to_close:
                    await self._archive_session(self.active_sessions[session_id])
                    del self.active_sessions[session_id]
                    
                    self.logger.info(
                        "Closed session due to document deletion",
                        session_id=session_id,
                        document_id=document_id
                    )
                
                self.editing_metrics["active_sessions"] = len(self.active_sessions)
        
        except Exception as e:
            self.logger.error(f"Failed to handle document event: {e}")
    
    async def _session_manager(self):
        """Background task to manage and cleanup sessions"""
        while self.state == AgentState.RUNNING:
            try:
                current_time = time.time()
                session_timeout = 3600 * 24  # 24 hours
                
                sessions_to_remove = []
                
                for session_id, session in list(self.active_sessions.items()):
                    # Check for stale sessions
                    if current_time - session.updated_at > session_timeout:
                        sessions_to_remove.append(session_id)
                
                # Archive and remove stale sessions
                for session_id in sessions_to_remove:
                    session = self.active_sessions[session_id]
                    await self._archive_session(session)
                    del self.active_sessions[session_id]
                    
                    self.logger.info(
                        "Cleaned up stale session",
                        session_id=session_id,
                        idle_time=current_time - session.updated_at
                    )
                
                if sessions_to_remove:
                    self.editing_metrics["active_sessions"] = len(self.active_sessions)
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                self.logger.error(f"Session manager error: {e}")
                await asyncio.sleep(300)
    
    async def _content_analyzer_monitor(self):
        """Periodically re-analyze active sessions"""
        while self.state == AgentState.RUNNING:
            try:
                for session_id, session in list(self.active_sessions.items()):
                    # Re-analyze if recently updated
                    if time.time() - session.updated_at < 120:  # Updated in last 2 minutes
                        analysis = await self._analyze_content({
                            "content": session.current_content,
                            "content_type": session.content_type.value
                        })
                        
                        # Could store analysis results or trigger notifications
                        self.logger.debug(
                            "Re-analyzed session content",
                            session_id=session_id,
                            issues=analysis.get("analysis", {}).get("issues", {}).get("total_issues", 0)
                        )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Content analyzer monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _metrics_reporter(self):
        """Report editing metrics periodically"""
        while self.state == AgentState.RUNNING:
            try:
                # Calculate additional metrics
                if self.editing_metrics["suggestions_generated"] > 0:
                    acceptance_rate = (
                        self.editing_metrics["suggestions_accepted"] / 
                        self.editing_metrics["suggestions_generated"]
                    ) * 100
                else:
                    acceptance_rate = 0.0
                
                metrics = {
                    **self.editing_metrics,
                    "suggestion_acceptance_rate": acceptance_rate,
                    "tools_initialized": self.tools_initialized,
                    "timestamp": time.time()
                }
                
                # Publish metrics
                await self._publish(
                    f"metrics.{self.config.name}",
                    metrics
                )
                
                await asyncio.sleep(300)  # Report every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Metrics reporter error: {e}")
                await asyncio.sleep(300)
    
    async def _store_session(self, session: EditingSession):
        """Store session in database"""
        try:
            query = """
                INSERT INTO editing_sessions 
                (session_id, document_id, user_id, content_type, editing_mode, 
                 original_content, current_content, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (session_id) 
                DO UPDATE SET 
                    current_content = EXCLUDED.current_content,
                    updated_at = EXCLUDED.updated_at
            """
            
            await self._db_execute(
                query,
                session.session_id,
                session.document_id,
                session.user_id,
                session.content_type.value,
                session.editing_mode.value,
                session.original_content,
                session.current_content,
                session.created_at,
                session.updated_at
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store session: {e}")
    
    async def _update_session(self, session: EditingSession):
        """Update session in database"""
        try:
            query = """
                UPDATE editing_sessions 
                SET current_content = $1,
                    updated_at = $2,
                    version_count = $3,
                    suggestions_count = $4,
                    applied_edits_count = $5
                WHERE session_id = $6
            """
            
            await self._db_execute(
                query,
                session.current_content,
                session.updated_at,
                len(session.version_history),
                len(session.suggestions),
                len(session.applied_edits),
                session.session_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update session: {e}")
    
    async def _archive_session(self, session: EditingSession):
        """Archive session to database"""
        try:
            query = """
                INSERT INTO editing_sessions_archive 
                (session_id, document_id, user_id, content_type, editing_mode,
                 original_content, final_content, suggestions_generated, 
                 suggestions_accepted, version_count, created_at, closed_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """
            
            await self._db_execute(
                query,
                session.session_id,
                session.document_id,
                session.user_id,
                session.content_type.value,
                session.editing_mode.value,
                session.original_content,
                session.current_content,
                len(session.suggestions) + len(session.applied_edits),
                len(session.applied_edits),
                len(session.version_history),
                session.created_at,
                time.time()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to archive session: {e}")
    
    def _get_agent_metrics(self) -> Dict[str, Any]:
        """Get agent-specific metrics"""
        base_metrics = super()._get_agent_metrics()
        
        base_metrics.update({
            "editing_metrics": self.editing_metrics,
            "tools_status": {
                "grammar_tool": self.grammar_tool is not None,
                "nlp_models": list(self.nlp_models.keys()),
                "sentiment_analyzer": self.sentiment_analyzer is not None,
                "initialized": self.tools_initialized
            }
        })
        
        return base_metrics
    
    async def stop(self):
        """Cleanup before shutdown"""
        try:
            # Archive all active sessions
            self.logger.info(f"Archiving {len(self.active_sessions)} active sessions")
            
            for session in list(self.active_sessions.values()):
                await self._archive_session(session)
            
            # Cleanup language tools
            if self.grammar_tool:
                try:
                    self.grammar_tool.close()
                except:
                    pass
            
            self.logger.info("Editing agent cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
        finally:
            await super().stop()


async def main():
    """Main entry point"""
    config = AgentConfig(
        agent_id=os.getenv("AGENT_ID", f"editing-{uuid.uuid4().hex[:8]}"),
        name=os.getenv("AGENT_NAME", "editing_agent"),
        agent_type=os.getenv("AGENT_TYPE", "editing"),
        version="2.0.0",
        nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://user:password@localhost:5432/agentdb"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        max_concurrent_tasks=int(os.getenv("MAX_CONCURRENT_TASKS", "100")),
        status_publish_interval_seconds=int(os.getenv("STATUS_PUBLISH_INTERVAL", "30")),
        heartbeat_interval_seconds=int(os.getenv("HEARTBEAT_INTERVAL", "10")),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )
    
    agent = EditingAgent(config)
    
    try:
        if await agent.start():
            await agent.run_forever()
        else:
            print("Failed to start editing agent")
            return 1
    except KeyboardInterrupt:
        print("\nShutting down editing agent...")
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1
    finally:
        await agent.stop()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))