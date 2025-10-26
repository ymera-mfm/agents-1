
"""
Advanced Drafting Agent
Content creation, document generation, template management, and collaborative writing
"""

import asyncio
import json
import time
import re
import uuid
import difflib
import traceback # Added for detailed error logging
import os # Added for environment variables
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict # Added asdict for easier serialization
from enum import Enum
from datetime import datetime
# Optional dependencies - Natural language processing

# Optional dependencies
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    HAS_NLTK = True
except ImportError:
    nltk = None
    sent_tokenize = None
    word_tokenize = None
    stopwords = None
    HAS_NLTK = False

# Optional dependencies - Readability metrics
try:
    from textstat import flesch_reading_ease, flesch_kincaid_grade
    HAS_TEXTSTAT = True
except ImportError:
    flesch_reading_ease = None
    flesch_kincaid_grade = None
    HAS_TEXTSTAT = False

# Optional dependencies - Advanced NLP
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    spacy = None
    HAS_SPACY = False

from base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResponse, Priority, AgentStatus, TaskStatus # Added TaskStatus

# Optional dependencies - OpenTelemetry
try:
    from opentelemetry import trace
    HAS_OPENTELEMETRY = True
except ImportError:
    trace = None
    HAS_OPENTELEMETRY = False

class DocumentType(Enum):
    REPORT = "report"
    EMAIL = "email"
    PROPOSAL = "proposal"
    TECHNICAL_DOC = "technical_doc"
    MARKETING_COPY = "marketing_copy"
    LEGAL_DOCUMENT = "legal_document"
    BLOG_POST = "blog_post"
    API_DOCUMENTATION = "api_documentation"
    USER_MANUAL = "user_manual"
    PRESENTATION = "presentation"

class ContentTone(Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    PERSUASIVE = "persuasive"
    INFORMATIVE = "informative"
    CREATIVE = "creative"

class DraftStatus(Enum):
    DRAFT = "draft"
    REVIEW = "review"
    REVISION = "revision"
    APPROVED = "approved"
    PUBLISHED = "published"

@dataclass
class ContentTemplate:
    template_id: str
    name: str
    document_type: DocumentType
    sections: List[Dict[str, Any]]
    variables: Dict[str, str]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DocumentDraft:
    draft_id: str
    title: str
    document_type: DocumentType
    content: str
    template_id: Optional[str]
    author_id: str
    status: DraftStatus
    version: int
    tone: ContentTone
    target_audience: str
    created_at: float
    updated_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    collaborators: List[str] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    revision_history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ContentAnalysis:
    readability_score: float
    grade_level: float
    word_count: int
    sentence_count: int
    paragraph_count: int
    avg_sentence_length: float
    complexity_score: float
    tone_analysis: Dict[str, float]
    keyword_density: Dict[str, float]
    suggestions: List[str]

class DraftingAgent(BaseAgent):
    """
    Advanced Drafting Agent with:
    - Template-based content generation
    - Multi-format document support
    - Real-time collaborative editing
    - Content analysis and optimization
    - Version control and revision tracking
    - Style guide enforcement
    - Automated proofreading and suggestions
    - Integration with LLM for content enhancement
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Content templates
        self.templates: Dict[str, ContentTemplate] = {}
        
        # Active drafts
        self.drafts: Dict[str, DocumentDraft] = {}
        
        # Collaborative sessions
        self.collaborative_sessions: Dict[str, Dict] = {}
        
        # Style guides
        self.style_guides: Dict[str, Dict] = {}
        
        # Content generation models
        self.nlp = None
        
        # Drafting statistics
        self.drafting_stats = {
            "documents_created": 0,
            "templates_used": 0,
            "collaborations": 0,
            "revisions_made": 0,
            "content_optimizations": 0
        }
        
        # Load templates and initialize NLP
        self._load_default_templates()
        self._load_style_guides()
        asyncio.create_task(self._initialize_nlp())
    
    async def start(self):
        """Start drafting agent services"""
        # The BaseAgent already subscribes to agent.{self.config.name}.task
        
        # Subscribe to collaborative editing
        await self._subscribe(
            "drafting.collaborate",
            self._handle_collaboration
        )
        
        # Subscribe to template requests
        await self._subscribe(
            "drafting.template",
            self._handle_template_request
        )
        
        # Subscribe to content analysis requests
        await self._subscribe(
            "drafting.analyze",
            self._handle_content_analysis
        )
        
        # Start background tasks
        asyncio.create_task(self._auto_save_drafts())
        asyncio.create_task(self._cleanup_sessions())
        
        self.logger.info("Drafting Agent started",
                        template_count=len(self.templates))
    
    def _load_default_templates(self):
        """Load default document templates"""
        
        # Technical Report Template
        tech_report = ContentTemplate(
            template_id="tech_report_v1",
            name="Technical Report",
            document_type=DocumentType.TECHNICAL_DOC,
            sections=[
                {"id": "executive_summary", "title": "Executive Summary", "required": True},
                {"id": "introduction", "title": "Introduction", "required": True},
                {"id": "methodology", "title": "Methodology", "required": False},
                {"id": "findings", "title": "Findings", "required": True},
                {"id": "analysis", "title": "Analysis", "required": True},
                {"id": "recommendations", "title": "Recommendations", "required": True},
                {"id": "conclusion", "title": "Conclusion", "required": True},
                {"id": "appendices", "title": "Appendices", "required": False}
            ],
            variables={
                "report_title": "Report Title",
                "author": "Author Name",
                "date": "Date",
                "department": "Department",
                "project_id": "Project ID"
            }
        )
        self.templates[tech_report.template_id] = tech_report
        
        # Business Proposal Template
        proposal = ContentTemplate(
            template_id="business_proposal_v1",
            name="Business Proposal",
            document_type=DocumentType.PROPOSAL,
            sections=[
                {"id": "cover_page", "title": "Cover Page", "required": True},
                {"id": "executive_summary", "title": "Executive Summary", "required": True},
                {"id": "problem_statement", "title": "Problem Statement", "required": True},
                {"id": "proposed_solution", "title": "Proposed Solution", "required": True},
                {"id": "implementation_plan", "title": "Implementation Plan", "required": True},
                {"id": "budget", "title": "Budget", "required": True},
                {"id": "timeline", "title": "Timeline", "required": True},
                {"id": "team", "title": "Team", "required": False},
                {"id": "references", "title": "References", "required": False}
            ],
            variables={
                "proposal_title": "Proposal Title",
                "client_name": "Client Name",
                "company": "Company Name",
                "contact_person": "Contact Person",
                "submission_date": "Submission Date"
            }
        )
        self.templates[proposal.template_id] = proposal
        
        # API Documentation Template
        api_doc = ContentTemplate(
            template_id="api_documentation_v1",
            name="API Documentation",
            document_type=DocumentType.API_DOCUMENTATION,
            sections=[
                {"id": "overview", "title": "API Overview", "required": True},
                {"id": "authentication", "title": "Authentication", "required": True},
                {"id": "endpoints", "title": "Endpoints", "required": True},
                {"id": "request_format", "title": "Request Format", "required": True},
                {"id": "response_format", "title": "Response Format", "required": True},
                {"id": "error_codes", "title": "Error Codes", "required": True},
                {"id": "examples", "title": "Examples", "required": True},
                {"id": "rate_limits", "title": "Rate Limits", "required": False},
                {"id": "changelog", "title": "Changelog", "required": False}
            ],
            variables={
                "api_name": "API Name",
                "version": "API Version",
                "base_url": "Base URL",
                "contact_email": "Contact Email"
            }
        )
        self.templates[api_doc.template_id] = api_doc
    
    def _load_style_guides(self):
        """Load style guides for different document types"""
        self.style_guides = {
            "technical": {
                "tone": "formal",
                "sentence_length": {"max": 25, "preferred": 15},
                "paragraph_length": {"max": 6, "preferred": 4},
                "passive_voice": {"max_percentage": 10},
                "jargon_level": "moderate",
                "formatting": {
                    "headings": "title_case",
                    "lists": "parallel_structure",
                    "numbers": "spell_out_below_10"
                }
            },
            "business": {
                "tone": "professional",
                "sentence_length": {"max": 20, "preferred": 12},
                "paragraph_length": {"max": 5, "preferred": 3},
                "passive_voice": {"max_percentage": 15},
                "jargon_level": "minimal",
                "formatting": {
                    "headings": "title_case",
                    "currency": "spell_out_rounded",
                    "dates": "full_format"
                }
            },
            "marketing": {
                "tone": "persuasive",
                "sentence_length": {"max": 18, "preferred": 10},
                "paragraph_length": {"max": 4, "preferred": 2},
                "passive_voice": {"max_percentage": 5},
                "call_to_action": "required",
                "formatting": {
                    "headings": "sentence_case",
                    "emphasis": "bold_for_benefits"
                }
            }
        }
    
    async def _initialize_nlp(self):
        """Initialize NLP models for content analysis"""
        try:
            # Download required NLTK data
            import ssl
            try:
                _create_unverified_https_context = ssl._create_unverified_context
            except AttributeError:
                pass
            else:
                ssl._create_default_https_context = _create_unverified_https_context
            
            nltk.download("punkt", quiet=True)
            nltk.download("stopwords", quiet=True)
            nltk.download("averaged_perceptron_tagger", quiet=True)
            
            # Load spaCy model
            # Ensure the model is downloaded: python -m spacy download en_core_web_sm
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                self.logger.warning("spaCy model 'en_core_web_sm' not found. Downloading...")
                spacy.cli.download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
            
            self.logger.info("NLP models initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize NLP models", error=str(e), traceback=traceback.format_exc())
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute drafting-specific tasks"""
        task_type = request.task_type
        payload = request.payload
        
        try:
            result: Dict[str, Any] = {}
            if task_type == "create_draft":
                result = await self._create_draft(payload)
            
            elif task_type == "update_draft":
                result = await self._update_draft(payload)
            
            elif task_type == "generate_content":
                result = await self._generate_content(payload)
            
            elif task_type == "analyze_content":
                result = await self._analyze_content(payload)
            
            elif task_type == "apply_template":
                result = await self._apply_template(payload)
            
            elif task_type == "collaborate":
                result = await self._start_collaboration(payload)
            
            elif task_type == "review_draft":
                result = await self._review_draft(payload)
            
            elif task_type == "optimize_content":
                result = await self._optimize_content(payload)
            
            elif task_type == "export_document":
                result = await self._export_document(payload)
            
            else:
                raise ValueError(f"Unknown drafting task type: {task_type}")
            
            return TaskResponse(task_id=request.task_id, status=TaskStatus.COMPLETED, result=result).dict()

        except Exception as e:
            self.logger.error(f"Error executing drafting task {task_type}", error=str(e), traceback=traceback.format_exc())
            return TaskResponse(task_id=request.task_id, status=TaskStatus.FAILED, error=str(e)).dict()
    
    async def _create_draft(self, payload: Dict) -> Dict[str, Any]:
        """Create a new document draft"""
        title = payload.get("title", "Untitled Document")
        document_type_str = payload.get("document_type", "report")
        template_id = payload.get("template_id")
        author_id = payload.get("author_id", "anonymous")
        tone_str = payload.get("tone", "professional")
        target_audience = payload.get("target_audience", "general")
        
        try:
            document_type = DocumentType(document_type_str)
            tone = ContentTone(tone_str)
        except ValueError as e:
            raise ValueError(f"Invalid document_type or tone: {e}")

        draft_id = f"draft_{uuid.uuid4().hex[:8]}"
        current_time = time.time()
        
        # Initialize content from template if provided
        content = ""
        if template_id and template_id in self.templates:
            template = self.templates[template_id]
            content = self._generate_template_content(template, payload.get("variables", {}))
        else:
            content = payload.get("initial_content", "")
        
        draft = DocumentDraft(
            draft_id=draft_id,
            title=title,
            document_type=document_type,
            content=content,
            template_id=template_id,
            author_id=author_id,
            status=DraftStatus.DRAFT,
            version=1,
            tone=tone,
            target_audience=target_audience,
            created_at=current_time,
            updated_at=current_time,
            metadata=payload.get("metadata", {})
        )
        
        self.drafts[draft_id] = draft
        self.drafting_stats["documents_created"] += 1
        
        if template_id:
            self.drafting_stats["templates_used"] += 1
        
        # Persist to database
        if self.db_pool:
            await self._persist_draft(draft)
        
        self.logger.info("Draft created",
                        draft_id=draft_id,
                        title=title,
                        document_type=document_type.value)
        
        return {
            "draft_id": draft_id,
            "title": title,
            "status": "created",
            "word_count": len(content.split()),
            "version": 1,
            "created_at": current_time
        }
    
    async def _update_draft(self, payload: Dict) -> Dict[str, Any]:
        """Update an existing draft"""
        draft_id = payload.get("draft_id")
        if not draft_id or draft_id not in self.drafts:
            raise ValueError("Draft not found")
        
        draft = self.drafts[draft_id]
        
        # Create revision history entry
        revision_entry = {
            "version": draft.version,
            "content": draft.content,
            "updated_at": draft.updated_at,
            "editor_id": payload.get("editor_id", "system"),
            "changes": {}
        }
        draft.revision_history.append(revision_entry)

        # Apply updates
        if "title" in payload: draft.title = payload["title"]
        if "content" in payload:
            old_content = draft.content
            draft.content = payload["content"]
            # Calculate diff for changes
            diff = list(difflib.unified_diff(old_content.splitlines(), draft.content.splitlines()))
            revision_entry["changes"]["content_diff"] = "\n".join(diff)

        if "status" in payload: draft.status = DraftStatus(payload["status"])
        if "tone" in payload: draft.tone = ContentTone(payload["tone"])
        if "target_audience" in payload: draft.target_audience = payload["target_audience"]
        if "metadata" in payload: draft.metadata.update(payload["metadata"])
        if "collaborators" in payload: draft.collaborators = list(set(draft.collaborators + payload["collaborators"]))
        if "comments" in payload: draft.comments.extend(payload["comments"])

        draft.version += 1
        draft.updated_at = time.time()
        self.drafting_stats["revisions_made"] += 1

        # Persist to database
        if self.db_pool:
            await self._update_persisted_draft(draft)

        self.logger.info("Draft updated", draft_id=draft_id, version=draft.version)
        
        return {
            "draft_id": draft_id,
            "title": draft.title,
            "status": draft.status.value,
            "version": draft.version,
            "updated_at": draft.updated_at
        }

    async def _generate_content(self, payload: Dict) -> Dict[str, Any]:
        """Generate content using LLM integration"""
        draft_id = payload.get("draft_id")
        prompt = payload.get("prompt")
        section_id = payload.get("section_id")
        length = payload.get("length", "medium") # short, medium, long
        creativity = payload.get("creativity", 0.7) # 0.0 to 1.0
        
        if not draft_id or draft_id not in self.drafts:
            raise ValueError("Draft not found")
        if not prompt:
            raise ValueError("Prompt is required for content generation.")
        
        draft = self.drafts[draft_id]
        
        self.logger.info("Generating content for draft", draft_id=draft_id, section_id=section_id)
        
        # This would involve calling the LLM agent to generate content
        # For now, a placeholder:
        generated_text = f"[Generated content for '{prompt}' (length: {length}, creativity: {creativity}) for {draft.document_type.value} in {draft.tone.value} tone.]"
        
        # Integrate generated content into the draft
        if section_id:
            # Find and replace/insert into specific section
            # This requires more sophisticated content structure management
            draft.content += f"\n\n### {section_id.replace('_', ' ').title()}\n{generated_text}"
        else:
            draft.content += f"\n\n{generated_text}"
        
        draft.updated_at = time.time()
        draft.version += 1
        self.drafting_stats["content_optimizations"] += 1 # Count as optimization for now

        # Persist to database
        if self.db_pool:
            await self._update_persisted_draft(draft)

        return {
            "draft_id": draft_id,
            "generated_length": len(generated_text),
            "updated_content_preview": draft.content[:500] + "..." if len(draft.content) > 500 else draft.content
        }

    async def _analyze_content(self, payload: Dict) -> Dict[str, Any]:
        """Analyze content for readability, tone, keywords, etc."""
        draft_id = payload.get("draft_id")
        content = payload.get("content")
        
        if not draft_id and not content:
            raise ValueError("Either draft_id or content must be provided for analysis.")
        
        if draft_id and draft_id in self.drafts:
            content_to_analyze = self.drafts[draft_id].content
        elif content:
            content_to_analyze = content
        else:
            raise ValueError("Content not found for analysis.")
        
        if not content_to_analyze.strip():
            return {"analysis": {"error": "No content to analyze"}}

        self.logger.info("Analyzing content for draft", draft_id=draft_id)
        
        # Readability
        readability_score = flesch_reading_ease(content_to_analyze)
        grade_level = flesch_kincaid_grade(content_to_analyze)
        
        # Word, sentence, paragraph counts
        words = word_tokenize(content_to_analyze)
        sentences = sent_tokenize(content_to_analyze)
        paragraphs = [p for p in content_to_analyze.split("\n\n") if p.strip()]
        
        word_count = len(words)
        sentence_count = len(sentences)
        paragraph_count = len(paragraphs)
        avg_sentence_length = word_count / max(1, sentence_count)
        
        # Tone analysis (placeholder, would involve LLM or dedicated NLP)
        tone_analysis = await self._analyze_tone_llm(content_to_analyze)
        
        # Keyword density (simple example)
        stop_words = set(stopwords.words("english"))
        filtered_words = [word.lower() for word in words if word.isalpha() and word.lower() not in stop_words]
        word_freq = Counter(filtered_words)
        total_filtered_words = len(filtered_words)
        keyword_density = {word: count / total_filtered_words for word, count in word_freq.most_common(10)}
        
        # Complexity score (placeholder)
        complexity_score = (grade_level + (100 - readability_score) / 10) / 2
        
        # Suggestions (placeholder, would involve LLM or rule-based system)
        suggestions = []
        if readability_score < 60: suggestions.append("Consider simplifying language for better readability.")
        if avg_sentence_length > 20: suggestions.append("Break down long sentences to improve flow.")
        
        analysis = ContentAnalysis(
            readability_score=readability_score,
            grade_level=grade_level,
            word_count=word_count,
            sentence_count=sentence_count,
            paragraph_count=paragraph_count,
            avg_sentence_length=avg_sentence_length,
            complexity_score=complexity_score,
            tone_analysis=tone_analysis,
            keyword_density=keyword_density,
            suggestions=suggestions
        )
        
        return {"draft_id": draft_id, "analysis": asdict(analysis)}

    async def _analyze_tone_llm(self, text: str) -> Dict[str, float]:
        """Placeholder for LLM-based tone analysis"""
        # In a real system, this would call the LLM agent
        self.logger.debug("Performing dummy LLM tone analysis.")
        # Simulate some tone detection
        tones = {"formal": 0.0, "professional": 0.0, "friendly": 0.0}
        if "sincerely" in text.lower() or "regards" in text.lower():
            tones["formal"] = 0.8
            tones["professional"] = 0.7
        if "hi there" in text.lower() or "cheers" in text.lower():
            tones["friendly"] = 0.8
        return tones

    async def _apply_template(self, payload: Dict) -> Dict[str, Any]:
        """Apply a template to an existing draft"""
        draft_id = payload.get("draft_id")
        template_id = payload.get("template_id")
        variables = payload.get("variables", {})

        if not draft_id or draft_id not in self.drafts:
            raise ValueError("Draft not found")
        if not template_id or template_id not in self.templates:
            raise ValueError("Template not found")
        
        draft = self.drafts[draft_id]
        template = self.templates[template_id]
        
        generated_content = self._generate_template_content(template, variables)
        
        # Append or replace content based on payload instruction
        if payload.get("replace_content", False):
            draft.content = generated_content
        else:
            draft.content += f"\n\n{generated_content}"
        
        draft.template_id = template_id
        draft.updated_at = time.time()
        draft.version += 1
        self.drafting_stats["templates_used"] += 1

        # Persist to database
        if self.db_pool:
            await self._update_persisted_draft(draft)

        self.logger.info("Template applied to draft", draft_id=draft_id, template_id=template_id)
        
        return {"draft_id": draft_id, "template_id": template_id, "status": "template_applied"}

    def _generate_template_content(self, template: ContentTemplate, variables: Dict) -> str:
        """Generate content from a template and variables"""
        content_parts = []
        for section in template.sections:
            content_parts.append(f"## {section['title']}\n")
            # Placeholder for actual content generation based on section type
            content_parts.append(f"[Content for {section['title']}]\n")
        
        full_content = "\n".join(content_parts)
        
        # Replace variables
        for key, value in variables.items():
            full_content = full_content.replace(f"{{{{{key}}}}}", str(value))
        
        return full_content

    async def _start_collaboration(self, payload: Dict) -> Dict[str, Any]:
        """Start or manage a collaborative editing session"""
        draft_id = payload.get("draft_id")
        user_id = payload.get("user_id")
        action = payload.get("action", "join") # join, leave, update
        
        if not draft_id or draft_id not in self.drafts:
            raise ValueError("Draft not found")
        
        draft = self.drafts[draft_id]
        
        if action == "join":
            if draft_id not in self.collaborative_sessions:
                self.collaborative_sessions[draft_id] = {
                    "participants": set(),
                    "last_activity": time.time()
                }
            self.collaborative_sessions[draft_id]["participants"].add(user_id)
            draft.collaborators.append(user_id) # Add to draft's list
            self.drafting_stats["collaborations"] += 1
            self.logger.info("User joined collaboration", draft_id=draft_id, user_id=user_id)
            return {"draft_id": draft_id, "user_id": user_id, "status": "joined_collaboration"}
        
        elif action == "leave":
            if draft_id in self.collaborative_sessions and user_id in self.collaborative_sessions[draft_id]["participants"]:
                self.collaborative_sessions[draft_id]["participants"].remove(user_id)
                self.logger.info("User left collaboration", draft_id=draft_id, user_id=user_id)
                return {"draft_id": draft_id, "user_id": user_id, "status": "left_collaboration"}
            else:
                raise ValueError("User not in collaboration session.")
        
        elif action == "update":
            # This would involve applying real-time changes from a collaborator
            # Similar to EditingAgent's collaborative_edit, but for drafting
            self.logger.info("Collaborative update received (placeholder)", draft_id=draft_id, user_id=user_id)
            draft.content = payload.get("new_content", draft.content) # Simple update
            draft.updated_at = time.time()
            draft.version += 1
            self.collaborative_sessions[draft_id]["last_activity"] = time.time()
            
            # Persist to database
            if self.db_pool:
                await self._update_persisted_draft(draft)

            return {"draft_id": draft_id, "user_id": user_id, "status": "collaboration_updated"}
        
        else:
            raise ValueError(f"Unknown collaboration action: {action}")

    async def _review_draft(self, payload: Dict) -> Dict[str, Any]:
        """Submit a draft for review or add review comments"""
        draft_id = payload.get("draft_id")
        reviewer_id = payload.get("reviewer_id")
        comments = payload.get("comments", [])
        status_update = payload.get("status_update") # e.g., 
