
"""
Advanced Editing Agent
Handles content editing, proofreading, style improvement, and collaborative editing
"""

import asyncio
import json
import time
import re
import os
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import difflib
from datetime import datetime
# Optional dependencies - Advanced NLP

# Optional dependencies
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    spacy = None
    HAS_SPACY = False

# Optional dependencies - Natural language processing
try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    HAS_NLTK = True
except ImportError:
    nltk = None
    SentimentIntensityAnalyzer = None
    HAS_NLTK = False

# Optional dependencies - Readability metrics
try:
    from textstat import flesch_reading_ease, flesch_kincaid_grade
    HAS_TEXTSTAT = True
except ImportError:
    flesch_reading_ease = None
    flesch_kincaid_grade = None
    HAS_TEXTSTAT = False

# Optional dependencies - Grammar checking
try:
    import language_tool_python
    HAS_LANGUAGE_TOOL = True
except ImportError:
    language_tool_python = None
    HAS_LANGUAGE_TOOL = False

from base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResponse, Priority, AgentStatus

# Optional dependencies - OpenTelemetry
try:
    from opentelemetry import trace
    HAS_OPENTELEMETRY = True
except ImportError:
    trace = None
    HAS_OPENTELEMETRY = False

class EditType(Enum):
    GRAMMAR = "grammar"
    STYLE = "style"
    CLARITY = "clarity"
    TONE = "tone"
    STRUCTURE = "structure"
    FACT_CHECK = "fact_check"
    PLAGIARISM = "plagiarism"
    TRANSLATION = "translation"

class ContentType(Enum):
    ARTICLE = "article"
    EMAIL = "email"
    PROPOSAL = "proposal"
    REPORT = "report"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    MARKETING = "marketing"
    ACADEMIC = "academic"

class EditingMode(Enum):
    LIGHT = "light"        # Minor corrections only
    MODERATE = "moderate"   # Grammar and clarity improvements
    HEAVY = "heavy"        # Significant restructuring and rewriting
    COLLABORATIVE = "collaborative"  # Track changes mode

@dataclass
class EditSuggestion:
    id: str
    edit_type: EditType
    original_text: str
    suggested_text: str
    reason: str
    confidence: float
    position: tuple  # (start, end)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EditingSession:
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

@dataclass
class ContentAnalysis:
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
    - Fact-checking integration
    - Plagiarism detection
    - Real-time collaborative editing
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Editing sessions
        self.active_sessions: Dict[str, EditingSession] = {}
        
        # Language tools
        self.grammar_tool = None
        self.nlp_models = {}
        self.sentiment_analyzer = None
        
        # Style guides and preferences
        self.style_guides = {
            "ap": self._load_ap_style(),
            "chicago": self._load_chicago_style(),
            "mla": self._load_mla_style(),
            "apa": self._load_apa_style(),
            "technical": self._load_technical_style()
        }
        
        # Content templates and patterns
        self.content_patterns = {
            ContentType.EMAIL: self._load_email_patterns(),
            ContentType.PROPOSAL: self._load_proposal_patterns(),
            ContentType.REPORT: self._load_report_patterns(),
            ContentType.MARKETING: self._load_marketing_patterns()
        }
        
        # Performance metrics
        self.editing_metrics = {
            "total_sessions": 0,
            "suggestions_generated": 0,
            "suggestions_accepted": 0,
            "average_improvement_score": 0.0,
            "processing_time_avg": 0.0
        }
        
        # Initialize language tools (run as a background task)
        asyncio.create_task(self._initialize_tools())
    
    async def _initialize_tools(self):
        """Initialize NLP and language tools"""
        try:
            # Initialize LanguageTool for grammar checking
            self.grammar_tool = language_tool_python.LanguageTool("en-US")
            
            # Initialize spaCy models
            # Ensure the model is downloaded: python -m spacy download en_core_web_sm
            try:
                self.nlp_models["en"] = spacy.load("en_core_web_sm")
            except OSError:
                self.logger.warning("spaCy model 'en_core_web_sm' not found. Downloading...")
                spacy.cli.download("en_core_web_sm")
                self.nlp_models["en"] = spacy.load("en_core_web_sm")
            
            # Initialize sentiment analyzer
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
            
            # Download required NLTK data
            try:
                nltk.data.find("sentiment/vader_lexicon.zip")
            except nltk.downloader.DownloadError:
                nltk.download("vader_lexicon", quiet=True)
            try:
                nltk.data.find("tokenizers/punkt.zip")
            except nltk.downloader.DownloadError:
                nltk.download("punkt", quiet=True)
            
            self.logger.info("Language tools initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize language tools", error=str(e))

    # Placeholder methods for style guide loading and content patterns
    def _load_ap_style(self): return {} # Implement actual style guide loading
    def _load_chicago_style(self): return {}
    def _load_mla_style(self): return {}
    def _load_apa_style(self): return {}
    def _load_technical_style(self): return {}
    def _load_email_patterns(self): return {}
    def _load_proposal_patterns(self): return {}
    def _load_report_patterns(self): return {}
    def _load_marketing_patterns(self): return {}

    async def start(self):
        """Start editing agent services"""
        # Subscribe to collaborative editing events
        await self._subscribe(
            "editing.collaborative.*",
            self._handle_collaborative_event
        )
        
        # Subscribe to document events
        await self._subscribe(
            "document.*",
            self._handle_document_event
        )
        
        # Start background tasks
        asyncio.create_task(self._session_manager())
        asyncio.create_task(self._content_analyzer_monitor())
        
        self.logger.info("Editing Agent started")
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Implement the actual task logic for the Editing agent"""
        task_type = request.task_type
        payload = request.payload
        
        if task_type == "start_editing_session":
            return await self._start_editing_session(payload)
        
        elif task_type == "analyze_content":
            return await self._analyze_content(payload)
        
        elif task_type == "generate_suggestions":
            return await self._generate_suggestions(payload)
        
        elif task_type == "apply_edits":
            return await self._apply_edits(payload)
        
        elif task_type == "check_grammar":
            return await self._check_grammar(payload)
        
        elif task_type == "improve_style":
            return await self._improve_style(payload)
        
        elif task_type == "optimize_readability":
            return await self._optimize_readability(payload)
        
        elif task_type == "collaborative_edit":
            return await self._collaborative_edit(payload)
        
        elif task_type == "version_control":
            return await self._version_control(payload)
        
        else:
            raise ValueError(f"Unknown editing task type: {task_type}")
    
    async def _start_editing_session(self, payload: Dict) -> Dict[str, Any]:
        """Start a new editing session"""
        document_id = payload.get("document_id", f"doc_{uuid.uuid4().hex[:8]}")
        user_id = payload.get("user_id")
        content = payload.get("content", "")
        content_type_str = payload.get("content_type", "article")
        editing_mode_str = payload.get("editing_mode", "moderate")

        try:
            content_type = ContentType(content_type_str)
            editing_mode = EditingMode(editing_mode_str)
        except ValueError as e:
            raise ValueError(f"Invalid content_type or editing_mode: {e}")
        
        session_id = f"edit_sess_{uuid.uuid4().hex[:8]}"
        
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
        
        # Perform initial analysis
        analysis_result = await self._analyze_content({
            "content": content,
            "content_type": content_type.value
        })
        analysis = analysis_result.get("analysis", {})
        
        # Generate initial suggestions
        suggestions_result = await self._generate_suggestions({
            "session_id": session_id,
            "content": content,
            "editing_mode": editing_mode.value,
            "content_type": content_type.value
        })
        suggestions = suggestions_result.get("suggestions", [])
        
        self.logger.info("Editing session started",
                        session_id=session_id,
                        content_type=content_type.value,
                        editing_mode=editing_mode.value)
        
        return {
            "session_id": session_id,
            "document_id": document_id,
            "content_analysis": analysis,
            "initial_suggestions": suggestions,
            "session_created": True
        }
    
    async def _analyze_content(self, payload: Dict) -> Dict[str, Any]:
        """Analyze content for various metrics"""
        content = payload.get("content", "")
        content_type = payload.get("content_type", "article")
        
        if not content.strip():
            return {"analysis": {"error": "No content provided"}}
        
        try:
            # Basic metrics
            word_count = len(content.split())
            # Use NLTK for sentence tokenization for better accuracy
            sentences = nltk.sent_tokenize(content)
            sentence_count = len(sentences)
            paragraph_count = len([p for p in content.split("\n\n") if p.strip()])
            
            # Readability analysis
            readability_score = flesch_reading_ease(content)
            grade_level = flesch_kincaid_grade(content)
            
            # Sentiment analysis
            sentiment_scores = self.sentiment_analyzer.polarity_scores(content) if self.sentiment_analyzer else {}
            
            # Tone analysis (using a placeholder or LLM call)
            tone_analysis = await self._analyze_tone(content)
            
            # Grammar and style issues
            issues = []
            if self.grammar_tool:
                matches = self.grammar_tool.check(content)
                issues = [
                    {
                        "type": "grammar",
                        "message": match.message,
                        "offset": match.offset,
                        "length": match.errorLength,
                        "suggestions": match.replacements[:3],
                        "category": match.category
                    }
                    for match in matches[:20]  # Limit to first 20 issues for brevity
                ]
            
            # Content-specific analysis
            content_specific = await self._analyze_content_specific(content, content_type)
            
            analysis = ContentAnalysis(
                readability_score=readability_score,
                grade_level=grade_level,
                sentiment_score=sentiment_scores.get("compound", 0.0),
                tone_analysis=tone_analysis,
                word_count=word_count,
                sentence_count=sentence_count,
                paragraph_count=paragraph_count,
                issues_found=issues,
                suggestions_count=len(issues)
            )
            
            return {
                "analysis": {
                    "readability": {
                        "score": analysis.readability_score,
                        "grade_level": analysis.grade_level,
                        "interpretation": self._interpret_readability(analysis.readability_score)
                    },
                    "sentiment": {
                        "overall_score": analysis.sentiment_score,
                        "detailed_scores": sentiment_scores,
                        "tone": tone_analysis
                    },
                    "structure": {
                        "word_count": analysis.word_count,
                        "sentence_count": analysis.sentence_count,
                        "paragraph_count": analysis.paragraph_count,
                        "avg_words_per_sentence": analysis.word_count / max(analysis.sentence_count, 1),
                        "avg_sentences_per_paragraph": analysis.sentence_count / max(analysis.paragraph_count, 1)
                    },
                    "issues": {
                        "grammar_issues": len([i for i in issues if i["type"] == "grammar"]),
                        "style_issues": len([i for i in issues if i["type"] == "style"]),
                        "total_issues": len(issues),
                        "details": issues
                    },
                    "content_specific": content_specific
                }
            }
            
        except Exception as e:
            self.logger.error("Content analysis failed", error=str(e), traceback=traceback.format_exc())
            return {"analysis": {"error": f"Analysis failed: {str(e)}"}}
    
    def _interpret_readability(self, score: float) -> str:
        if score >= 90: return "Very Easy"
        elif score >= 80: return "Easy"
        elif score >= 70: return "Fairly Easy"
        elif score >= 60: return "Standard"
        elif score >= 50: return "Fairly Difficult"
        elif score >= 30: return "Difficult"
        else: return "Very Difficult"

    async def _analyze_tone(self, content: str) -> Dict[str, float]:
        """Analyze tone of content using a more sophisticated approach (e.g., LLM call or advanced NLP)"""
        # This is a placeholder. For a real-world scenario, you would integrate with an LLM
        # or a dedicated NLP service for tone analysis.
        self.logger.debug("Performing dummy tone analysis.")
        tones = {
            "formal": 0.0,
            "casual": 0.0,
            "professional": 0.0,
            "friendly": 0.0,
            "persuasive": 0.0,
            "informative": 0.0
        }
        
        content_lower = content.lower()
        
        # Simple keyword-based tone detection (can be replaced by LLM call)
        if re.search(r"(dear sir|madam|sincerely|regards|furthermore|therefore)", content_lower):
            tones["formal"] = 0.8
            tones["professional"] = 0.7
        if re.search(r"(hi there|hey|cheers|lol|btw)", content_lower):
            tones["casual"] = 0.8
            tones["friendly"] = 0.7
        if re.search(r"(recommend|propose|strategy|objective)", content_lower):
            tones["professional"] = 0.9
            tones["informative"] = 0.6
        if re.search(r"(please|thank you|appreciate|glad)", content_lower):
            tones["friendly"] = 0.8
        if re.search(r"(should|must|benefit|advantage)", content_lower):
            tones["persuasive"] = 0.8
        if re.search(r"(according to|research shows|data indicates)", content_lower):
            tones["informative"] = 0.8

        # Normalize (simple max-based normalization)
        total_tone_score = sum(tones.values())
        if total_tone_score > 0:
            for k in tones:
                tones[k] /= total_tone_score

        return tones

    async def _analyze_content_specific(self, content: str, content_type: str) -> Dict[str, Any]:
        """Perform content-type specific analysis"""
        analysis_results = {}
        # Example: For marketing content, check for call-to-actions
        if content_type == ContentType.MARKETING.value:
            cta_patterns = [r"buy now", r"learn more", r"sign up", r"get started"]
            found_ctas = [p for p in cta_patterns if re.search(p, content.lower())]
            analysis_results["call_to_actions_found"] = len(found_ctas)
            analysis_results["cta_phrases"] = found_ctas
        
        # Example: For technical content, check for code blocks or specific terminology
        if content_type == ContentType.TECHNICAL.value:
            code_block_count = len(re.findall(r"```.*?```", content, re.DOTALL))
            analysis_results["code_block_count"] = code_block_count
            # Placeholder for terminology check
            analysis_results["technical_terms_density"] = 0.0 # Requires a lexicon

        return analysis_results

    async def _generate_suggestions(self, payload: Dict) -> Dict[str, Any]:
        """Generate editing suggestions based on content, mode, and type"""
        session_id = payload.get("session_id")
        content = payload.get("content")
        editing_mode_str = payload.get("editing_mode", "moderate")
        content_type_str = payload.get("content_type", "article")

        if not session_id or session_id not in self.active_sessions:
            raise ValueError("Invalid or expired editing session.")
        if not content:
            raise ValueError("Content is required to generate suggestions.")

        session = self.active_sessions[session_id]
        editing_mode = EditingMode(editing_mode_str)
        content_type = ContentType(content_type_str)

        suggestions: List[EditSuggestion] = []

        # Grammar and spelling suggestions
        if self.grammar_tool:
            matches = self.grammar_tool.check(content)
            for match in matches:
                if editing_mode == EditingMode.LIGHT and match.category not in ["Grammar", "Spelling"]:
                    continue # Only critical grammar/spelling for light mode
                
                if match.replacements:
                    suggestions.append(EditSuggestion(
                        id=str(uuid.uuid4()),
                        edit_type=EditType.GRAMMAR if match.category in ["Grammar", "Spelling"] else EditType.STYLE,
                        original_text=content[match.offset:match.offset + match.errorLength],
                        suggested_text=match.replacements[0],
                        reason=match.message,
                        confidence=1.0, # LanguageTool usually high confidence
                        position=(match.offset, match.offset + match.errorLength),
                        metadata={
                            "category": match.category,
                            "rule_id": match.ruleId
                        }
                    ))
        
        # Style and clarity suggestions (can be enhanced with LLM calls)
        if editing_mode in [EditingMode.MODERATE, EditingMode.HEAVY]:
            # Example: Suggest simplifying complex sentences
            doc = self.nlp_models["en"](content) if "en" in self.nlp_models else None
            if doc:
                for sent in doc.sents:
                    if len(sent.text.split()) > 25 and " and " in sent.text.lower():
                        suggestions.append(EditSuggestion(
                            id=str(uuid.uuid4()),
                            edit_type=EditType.CLARITY,
                            original_text=sent.text,
                            suggested_text=f"Consider rephrasing or splitting this long sentence for clarity: {sent.text}",
                            reason="Long sentence detected, may impact readability.",
                            confidence=0.7,
                            position=(sent.start_char, sent.end_char),
                            metadata={
                                "suggestion_type": "sentence_simplification"
                            }
                        ))
            
            # Example: Suggest active voice over passive voice (LLM integration)
            # This would typically involve sending a snippet to an LLM for rephrasing
            # For now, a placeholder:
            if "was done by" in content.lower() and editing_mode == EditingMode.HEAVY:
                 suggestions.append(EditSuggestion(
                    id=str(uuid.uuid4()),
                    edit_type=EditType.STYLE,
                    original_text="Passive voice detected",
                    suggested_text="Consider using active voice for stronger impact.",
                    reason="Passive voice can make writing less direct.",
                    confidence=0.6,
                    position=(0,0), # General suggestion
                    metadata={
                        "suggestion_type": "active_voice"
                    }
                ))

        # Tone and content-type specific suggestions (LLM integration)
        if editing_mode == EditingMode.HEAVY:
            # This would involve calling the LLM agent to get suggestions for tone adjustment
            # or content enhancement based on the content_type and desired outcome.
            self.logger.debug("Generating heavy editing suggestions (placeholder for LLM integration).")
            # Example: Call LLM for a more engaging opening for marketing copy
            if content_type == ContentType.MARKETING:
                suggestions.append(EditSuggestion(
                    id=str(uuid.uuid4()),
                    edit_type=EditType.TONE,
                    original_text="Initial opening paragraph",
                    suggested_text="Consider a more engaging hook for your marketing copy.",
                    reason="Marketing content benefits from strong opening hooks.",
                    confidence=0.8,
                    position=(0, 50), # Example position
                    metadata={
                        "suggestion_type": "marketing_hook_improvement"
                    }
                ))

        session.suggestions.extend(suggestions)
        self.editing_metrics["suggestions_generated"] += len(suggestions)

        return {"session_id": session_id, "suggestions": [asdict(s) for s in suggestions]}

    async def _apply_edits(self, payload: Dict) -> Dict[str, Any]:
        """Apply selected edits to the current content"""
        session_id = payload.get("session_id")
        edit_ids_to_apply = payload.get("edit_ids", [])

        if not session_id or session_id not in self.active_sessions:
            raise ValueError("Invalid or expired editing session.")
        
        session = self.active_sessions[session_id]
        original_content = session.current_content
        new_content = list(original_content) # Work with a list of characters for easier manipulation
        
        # Sort edits by position in reverse order to avoid index shifting issues
        edits_to_apply = sorted(
            [s for s in session.suggestions if s.id in edit_ids_to_apply],
            key=lambda x: x.position[0], reverse=True
        )

        applied_count = 0
        for edit in edits_to_apply:
            start, end = edit.position
            # Ensure edit is still valid given previous changes
            if start >= 0 and end <= len(original_content):
                # Replace the original text with the suggested text
                new_content[start:end] = list(edit.suggested_text)
                session.applied_edits.append(edit)
                session.suggestions.remove(edit) # Remove applied suggestion
                applied_count += 1
        
        session.current_content = "".join(new_content)
        session.updated_at = time.time()
        session.version_history.append({
            "timestamp": time.time(),
            "content": session.current_content,
            "applied_edits": [s.id for s in edits_to_apply]
        })
        self.editing_metrics["suggestions_accepted"] += applied_count

        return {
            "session_id": session_id,
            "applied_count": applied_count,
            "new_content_preview": session.current_content[:500] + "..." if len(session.current_content) > 500 else session.current_content,
            "diff": difflib.unified_diff(original_content.splitlines(), session.current_content.splitlines())
        }

    async def _check_grammar(self, payload: Dict) -> Dict[str, Any]:
        """Perform grammar and spelling check"""
        content = payload.get("content")
        if not content:
            raise ValueError("Content is required for grammar check.")
        
        if not self.grammar_tool:
            raise RuntimeError("Grammar tool not initialized.")
        
        matches = self.grammar_tool.check(content)
        issues = [
            {
                "message": match.message,
                "replacements": match.replacements,
                "offset": match.offset,
                "length": match.errorLength,
                "context": match.context,
                "rule_id": match.ruleId,
                "category": match.category
            }
            for match in matches
        ]
        return {"issues": issues, "issue_count": len(issues)}

    async def _improve_style(self, payload: Dict) -> Dict[str, Any]:
        """Improve writing style using LLM or rule-based systems"""
        content = payload.get("content")
        style_guide_name = payload.get("style_guide", "technical")
        
        if not content:
            raise ValueError("Content is required for style improvement.")
        
        # This would typically involve sending the content to an LLM agent
        # with instructions to rewrite according to a specific style guide.
        self.logger.info(f"Improving style for content using {style_guide_name} guide (LLM integration placeholder).")
        
        # Placeholder for LLM call
        improved_content = f"[LLM-improved content based on {style_guide_name} guide]: {content}"
        
        return {"original_content": content, "improved_content": improved_content}

    async def _optimize_readability(self, payload: Dict) -> Dict[str, Any]:
        """Optimize content for better readability"""
        content = payload.get("content")
        target_grade_level = payload.get("target_grade_level", 8)

        if not content:
            raise ValueError("Content is required for readability optimization.")

        # This would involve iterative calls to an LLM to simplify sentences, replace complex words, etc.
        self.logger.info(f"Optimizing readability for target grade level {target_grade_level} (LLM integration placeholder).")

        # Placeholder for LLM call
        optimized_content = f"[LLM-optimized content for readability, target grade {target_grade_level}]: {content}"

        return {"original_content": content, "optimized_content": optimized_content}

    async def _collaborative_edit(self, payload: Dict) -> Dict[str, Any]:
        """Handle real-time collaborative editing events"""
        session_id = payload.get("session_id")
        user_id = payload.get("user_id")
        change_type = payload.get("change_type") # e.g., insert, delete, replace
        position = payload.get("position")
        text = payload.get("text")

        if not session_id or session_id not in self.active_sessions:
            raise ValueError("Invalid or expired editing session.")
        
        session = self.active_sessions[session_id]
        
        # Apply changes to session.current_content
        # This would require careful handling of concurrent edits and CRDTs or similar
        self.logger.info("Applying collaborative edit (placeholder for CRDT implementation).",
                        session_id=session_id, user_id=user_id, change_type=change_type)
        
        # For simplicity, just update content (not truly collaborative)
        if change_type == "replace_all":
            session.current_content = text
        
        session.updated_at = time.time()
        session.version_history.append({
            "timestamp": time.time(),
            "user_id": user_id,
            "change_type": change_type,
            "details": payload # Store full payload for history
        })

        # Broadcast change to other collaborators (via NATS)
        await self._publish(f"editing.collaborative.{session_id}.update", json.dumps({
            "session_id": session_id,
            "user_id": user_id,
            "change": payload,
            "new_content_preview": session.current_content[:100]
        }).encode())

        return {"status": "change_received", "session_id": session_id}

    async def _version_control(self, payload: Dict) -> Dict[str, Any]:
        """Manage document versions and history"""
        session_id = payload.get("session_id")
        operation = payload.get("operation") # e.g., get_history, revert, save_version
        version_id = payload.get("version_id")

        if not session_id or session_id not in self.active_sessions:
            raise ValueError("Invalid or expired editing session.")
        
        session = self.active_sessions[session_id]

        if operation == "get_history":
            return {"session_id": session_id, "version_history": session.version_history}
        
        elif operation == "revert":
            # Find the version to revert to
            target_version = next((v for v in session.version_history if v.get("version_id") == version_id), None)
            if target_version:
                session.current_content = target_version["content"]
                session.updated_at = time.time()
                self.logger.info("Reverted session content", session_id=session_id, version_id=version_id)
                return {"status": "reverted", "session_id": session_id, "new_content_preview": session.current_content[:500]}
            else:
                raise ValueError(f"Version {version_id} not found.")
        
        elif operation == "save_version":
            new_version_id = str(uuid.uuid4())
            session.version_history.append({
                "timestamp": time.time(),
                "content": session.current_content,
                "version_id": new_version_id,
                "message": payload.get("message", "Manual save")
            })
            self.logger.info("Saved new version", session_id=session_id, version_id=new_version_id)
            return {"status": "version_saved", "session_id": session_id, "version_id": new_version_id}
        
        else:
            raise ValueError(f"Unknown version control operation: {operation}")

    async def _handle_editing_task(self, msg):
        """Handle incoming editing tasks (deprecated, now uses _execute_task_impl)"""
        self.logger.warning("[_handle_editing_task] called. This method is deprecated. Use _execute_task_impl.")
        # This method should ideally not be called if orchestrator routes to _execute_task_impl
        # For backward compatibility or direct calls, you might parse and call _execute_task_impl
        try:
            data = json.loads(msg.data.decode())
            request = TaskRequest(**data)
            response = await self._execute_task_impl(request)
            await self._publish(msg.reply, json.dumps(response).encode()) # Assuming there's a reply subject
        except Exception as e:
            self.logger.error("Error in deprecated _handle_editing_task", error=str(e))
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_collaborative_event(self, msg):
        """Handle incoming collaborative editing events"""
        try:
            data = json.loads(msg.data.decode())
            session_id = data.get("session_id")
            if session_id and session_id in self.active_sessions:
                # This agent receives a collaborative update, applies it, and potentially re-analyzes
                self.logger.info("Received collaborative event", session_id=session_id, change_type=data.get("change_type"))
                # For a real system, this would involve applying CRDT operations
                # For now, just update the content if it's a full replacement
                if data.get("change_type") == "replace_all":
                    self.active_sessions[session_id].current_content = data.get("new_content")
                    self.active_sessions[session_id].updated_at = time.time()
                    # Trigger re-analysis if needed
                    # asyncio.create_task(self._trigger_analysis(session_id))
            else:
                self.logger.warning("Collaborative event for unknown session", session_id=session_id)
        except Exception as e:
            self.logger.error("Failed to handle collaborative event", error=str(e), traceback=traceback.format_exc())

    async def _handle_document_event(self, msg):
        """Handle document-related events (e.g., document updated, document deleted)"""
        try:
            data = json.loads(msg.data.decode())
            event_type = data.get("event_type")
            document_id = data.get("document_id")

            self.logger.info("Received document event", event_type=event_type, document_id=document_id)

            if event_type == "document_updated":
                # Find sessions related to this document and update their content
                for session_id, session in self.active_sessions.items():
                    if session.document_id == document_id:
                        self.logger.info("Updating session content due to document update", session_id=session_id)
                        session.original_content = data.get("new_content", session.original_content)
                        session.current_content = data.get("new_content", session.current_content)
                        session.updated_at = time.time()
                        # Trigger re-analysis if needed
                        # asyncio.create_task(self._trigger_analysis(session_id))
            elif event_type == "document_deleted":
                # Remove sessions related to this document
                sessions_to_remove = [s_id for s_id, s in self.active_sessions.items() if s.document_id == document_id]
                for s_id in sessions_to_remove:
                    del self.active_sessions[s_id]
                    self.logger.info("Removed session due to document deletion", session_id=s_id, document_id=document_id)
        except Exception as e:
            self.logger.error("Failed to handle document event", error=str(e), traceback=traceback.format_exc())

    async def _session_manager(self):
        """Background task to manage and clean up old editing sessions"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                session_timeout = 3600 * 24 # 24 hours for a session to be considered stale
                
                sessions_to_remove = []
                for session_id, session in self.active_sessions.items():
                    if current_time - session.updated_at > session_timeout:
                        sessions_to_remove.append(session_id)
                
                for session_id in sessions_to_remove:
                    del self.active_sessions[session_id]
                    self.logger.info("Cleaned up stale editing session", session_id=session_id)
                
                await asyncio.sleep(3600) # Check every hour
            except Exception as e:
                self.logger.error(f"Session manager failed: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(300)

    async def _content_analyzer_monitor(self):
        """Periodically re-analyze content of active sessions for real-time feedback"""
        while not self._shutdown_event.is_set():
            try:
                for session_id, session in list(self.active_sessions.items()):
                    # Re-analyze content if it has been updated recently or on a schedule
                    if time.time() - session.updated_at < 60: # Re-analyze if updated in last minute
                        self.logger.debug(f"Re-analyzing content for session {session_id}")
                        analysis_result = await self._analyze_content({
                            "content": session.current_content,
                            "content_type": session.content_type.value
                        })
                        # Update session with new analysis, potentially generate new suggestions
                        # For now, just log the analysis
                        self.logger.debug(f"Updated analysis for session {session_id}: {analysis_result['analysis']['issues']['total_issues']} issues")
                await asyncio.sleep(30) # Re-analyze every 30 seconds
            except Exception as e:
                self.logger.error(f"Content analyzer monitor failed: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(60)

    def _get_agent_metrics(self) -> Dict[str, Any]:
        """Provide Editing agent specific metrics."""
        base_metrics = super()._get_agent_metrics()
        base_metrics.update({
            "total_sessions": self.editing_metrics["total_sessions"],
            "active_sessions": len(self.active_sessions),
            "suggestions_generated": self.editing_metrics["suggestions_generated"],
            "suggestions_accepted": self.editing_metrics["suggestions_accepted"],
            "grammar_tool_initialized": self.grammar_tool is not None,
            "nlp_models_loaded": len(self.nlp_models)
        })
        return base_metrics


if __name__ == "__main__":
    config = AgentConfig(
        name="editing_agent",
        agent_type="editing",
        capabilities=["edit_content", "analyze_text", "grammar_check", "style_improve", "readability_optimize", "collaborative_edit", "version_control"],
        nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://agent:secure_password@postgres:5432/ymera"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
        consul_url=os.getenv("CONSUL_URL", "http://consul:8500"),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )
    
    agent = EditingAgent(config)
    asyncio.run(agent.run())

