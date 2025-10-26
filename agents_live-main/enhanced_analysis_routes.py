"""
YMERA Enterprise Analysis API Routes - Production Ready
Enhanced with comprehensive error handling, validation, and monitoring
Version: 2.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Path, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import asyncio
import uuid
from enum import Enum
import json
from functools import wraps
import time

# Core system imports
from ymera_core.database.manager import DatabaseManager
from ymera_core.logging.structured_logger import StructuredLogger
from ymera_core.cache.redis_cache import RedisCacheManager
from ymera_core.security.auth_manager import AuthManager
from ymera_core.exceptions import YMERAException, ValidationError, AnalysisError
from ymera_core.monitoring.metrics import MetricsCollector

# Agent system imports
from ymera_agents.orchestrator import AgentOrchestrator
from ymera_agents.core.analysis_agent import AnalysisAgent
from ymera_agents.learning.learning_engine import LearningEngine
from ymera_agents.communication.message_bus import MessageBus

# Service imports
from ymera_services.ai.multi_llm_manager import MultiLLMManager
from ymera_services.github.repository_analyzer import GitHubRepositoryAnalyzer
from ymera_services.code_analysis.quality_analyzer import CodeQualityAnalyzer
from ymera_services.vector_db.pinecone_manager import PineconeManager

# Initialize logger
logger = StructuredLogger(__name__)

# Security
security = HTTPBearer()

# Router with version prefix
router = APIRouter(prefix="/api/v1/analysis", tags=["Code Analysis"])

# Constants
MAX_CODE_SIZE = 500_000  # 500KB
MAX_FILE_SIZE = 100_000  # 100KB per file
MAX_BATCH_SIZE = 10
MAX_REPO_FILES = 1000
TOTAL_FILE_SIZE_LIMIT = 10_000_000  # 10MB

# Rate limiting configuration
RATE_LIMITS = {
    "free": {"requests_per_minute": 10, "requests_per_day": 100},
    "pro": {"requests_per_minute": 60, "requests_per_day": 1000},
    "enterprise": {"requests_per_minute": 300, "requests_per_day": 10000}
}

# Enums
class AnalysisType(str, Enum):
    """Supported analysis types"""
    FULL = "full"
    QUICK = "quick"
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    ARCHITECTURE = "architecture"
    DEPENDENCIES = "dependencies"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    COMPLEXITY = "complexity"

class AnalysisStatus(str, Enum):
    """Analysis status states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class AnalysisPriority(str, Enum):
    """Analysis priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class CodeLanguage(str, Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SCALA = "scala"
    AUTO_DETECT = "auto_detect"

# Request Models
class AnalysisRequestBase(BaseModel):
    """Base analysis request model with enhanced validation"""
    analysis_type: AnalysisType = Field(..., description="Type of analysis to perform")
    priority: AnalysisPriority = Field(default=AnalysisPriority.MEDIUM, description="Analysis priority")
    include_suggestions: bool = Field(default=True, description="Include enhancement suggestions")
    include_metrics: bool = Field(default=True, description="Include detailed metrics")
    learning_context: Optional[str] = Field(None, max_length=1000, description="Additional context for learning engine")
    timeout_seconds: Optional[int] = Field(300, ge=30, le=3600, description="Analysis timeout in seconds")
    
    class Config:
        use_enum_values = True

class CodeAnalysisRequest(AnalysisRequestBase):
    """Direct code analysis request with strict validation"""
    code: str = Field(..., min_length=1, max_length=MAX_CODE_SIZE, description="Source code to analyze")
    language: CodeLanguage = Field(default=CodeLanguage.AUTO_DETECT, description="Programming language")
    filename: Optional[str] = Field(None, max_length=255, description="Optional filename for context")
    project_context: Optional[str] = Field(None, max_length=2000, description="Project context information")
    
    @validator('code')
    def validate_code(cls, v):
        if not v or not v.strip():
            raise ValueError("Code cannot be empty or whitespace only")
        
        # Check for suspicious patterns
        suspicious_patterns = ['eval(', 'exec(', '__import__', 'os.system']
        if any(pattern in v for pattern in suspicious_patterns):
            logger.warning("Suspicious code pattern detected in submission")
        
        return v
    
    @validator('filename')
    def validate_filename(cls, v):
        if v:
            # Sanitize filename
            import re
            if not re.match(r'^[a-zA-Z0-9_\-\.]+$', v):
                raise ValueError("Filename contains invalid characters")
        return v

class RepositoryAnalysisRequest(AnalysisRequestBase):
    """Repository analysis request with enhanced validation"""
    repository_url: str = Field(..., max_length=500, description="GitHub repository URL")
    branch: Optional[str] = Field(default="main", max_length=100, description="Branch to analyze")
    include_history: bool = Field(default=False, description="Include commit history analysis")
    max_files: Optional[int] = Field(default=1000, ge=1, le=MAX_REPO_FILES, description="Maximum files to analyze")
    file_patterns: Optional[List[str]] = Field(None, max_items=20, description="File patterns to include")
    exclude_patterns: Optional[List[str]] = Field(None, max_items=20, description="File patterns to exclude")
    
    @validator('repository_url')
    def validate_repo_url(cls, v):
        import re
        
        # Strict GitHub URL validation
        github_pattern = r'^https://github\.com/[\w\-]+/[\w\-\.]+/?$'
        if not re.match(github_pattern, v):
            raise ValueError("Invalid GitHub repository URL format")
        
        # Prevent private token exposure
        if '@' in v:
            raise ValueError("Authentication tokens in URL are not allowed")
        
        return v.rstrip('/')
    
    @validator('file_patterns', 'exclude_patterns')
    def validate_patterns(cls, v):
        if v:
            for pattern in v:
                if len(pattern) > 100:
                    raise ValueError("Pattern too long")
        return v

class FileAnalysisRequest(AnalysisRequestBase):
    """File-based analysis request with strict validation"""
    files: List[Dict[str, Any]] = Field(..., min_items=1, max_items=50, description="Files to analyze")
    project_name: Optional[str] = Field(None, max_length=100, description="Project name")
    project_description: Optional[str] = Field(None, max_length=500, description="Project description")
    
    @validator('files')
    def validate_files(cls, v):
        if not v:
            raise ValueError("At least one file must be provided")
        
        total_size = 0
        seen_filenames = set()
        
        for idx, file_info in enumerate(v):
            # Validate required fields
            if 'content' not in file_info or 'filename' not in file_info:
                raise ValueError(f"File at index {idx}: missing 'content' or 'filename'")
            
            # Validate filename
            filename = file_info['filename']
            if filename in seen_filenames:
                raise ValueError(f"Duplicate filename: {filename}")
            seen_filenames.add(filename)
            
            # Validate file size
            content_size = len(file_info['content'])
            if content_size > MAX_FILE_SIZE:
                raise ValueError(f"File {filename} exceeds size limit ({MAX_FILE_SIZE} bytes)")
            
            total_size += content_size
        
        # Check total size
        if total_size > TOTAL_FILE_SIZE_LIMIT:
            raise ValueError(f"Total file size exceeds limit ({TOTAL_FILE_SIZE_LIMIT} bytes)")
        
        return v

class BatchAnalysisRequest(BaseModel):
    """Batch analysis request with validation"""
    requests: List[Union[CodeAnalysisRequest, RepositoryAnalysisRequest, FileAnalysisRequest]] = Field(
        ..., min_items=1, max_items=MAX_BATCH_SIZE, description="Analysis requests"
    )
    batch_priority: AnalysisPriority = Field(default=AnalysisPriority.MEDIUM)
    parallel_execution: bool = Field(default=True, description="Execute in parallel")
    
    @validator('requests')
    def validate_requests(cls, v):
        if not v:
            raise ValueError("At least one analysis request required")
        return v

# Response Models (Enhanced with additional metadata)
class QualityMetrics(BaseModel):
    """Code quality metrics with validation"""
    overall_score: float = Field(..., ge=0, le=100)
    maintainability_score: float = Field(..., ge=0, le=100)
    complexity_score: float = Field(..., ge=0, le=100)
    readability_score: float = Field(..., ge=0, le=100)
    test_coverage: Optional[float] = Field(None, ge=0, le=100)
    duplication_percentage: float = Field(..., ge=0, le=100)
    technical_debt_hours: float = Field(..., ge=0)
    code_smells: int = Field(default=0, ge=0)
    bugs: int = Field(default=0, ge=0)
    vulnerabilities: int = Field(default=0, ge=0)

class SecurityIssue(BaseModel):
    """Security issue with comprehensive details"""
    issue_id: str
    severity: str = Field(..., regex="^(critical|high|medium|low|info)$")
    category: str
    title: str
    description: str
    location: Dict[str, Any]
    recommendation: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = Field(None, ge=0, le=10)
    references: List[str] = Field(default_factory=list)

class PerformanceInsight(BaseModel):
    """Performance analysis insight"""
    category: str
    impact: str = Field(..., regex="^(critical|high|medium|low)$")
    description: str
    recommendation: str
    estimated_improvement: Optional[str] = None
    affected_lines: Optional[List[int]] = None

class EnhancementSuggestion(BaseModel):
    """Code enhancement suggestion"""
    suggestion_id: str
    category: str
    priority: str
    title: str
    description: str
    before_code: Optional[str] = None
    after_code: Optional[str] = None
    benefits: List[str] = Field(default_factory=list)
    effort_estimate: Optional[str] = None
    confidence: float = Field(default=0.8, ge=0, le=1)

class LearningInsights(BaseModel):
    """Learning engine insights"""
    patterns_identified: List[str] = Field(default_factory=list)
    knowledge_gaps: List[str] = Field(default_factory=list)
    learning_confidence: float = Field(..., ge=0, le=100)
    similar_cases: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    improvement_trajectory: Optional[Dict[str, Any]] = None

class AnalysisResult(BaseModel):
    """Complete analysis result with metadata"""
    analysis_id: str
    status: AnalysisStatus
    analysis_type: AnalysisType
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Core Results
    quality_metrics: Optional[QualityMetrics] = None
    security_issues: List[SecurityIssue] = Field(default_factory=list)
    performance_insights: List[PerformanceInsight] = Field(default_factory=list)
    enhancement_suggestions: List[EnhancementSuggestion] = Field(default_factory=list)
    
    # Metadata
    language_detected: Optional[str] = None
    files_analyzed: int = Field(default=0)
    lines_of_code: int = Field(default=0)
    
    # Learning Integration
    learning_insights: Optional[LearningInsights] = None
    confidence_score: float = Field(..., ge=0, le=100)
    
    # Additional Data
    raw_metrics: Dict[str, Any] = Field(default_factory=dict)
    agent_feedback: Dict[str, Any] = Field(default_factory=dict)
    processing_notes: List[str] = Field(default_factory=list)
    error_details: Optional[str] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AnalysisListResponse(BaseModel):
    """Paginated analysis list"""
    analyses: List[AnalysisResult]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool

class BatchAnalysisResponse(BaseModel):
    """Batch analysis response"""
    batch_id: str
    status: str
    total_requests: int
    completed_requests: int = 0
    failed_requests: int = 0
    results: List[AnalysisResult] = Field(default_factory=list)
    created_at: datetime
    estimated_completion: Optional[datetime] = None
    errors: List[Dict[str, str]] = Field(default_factory=list)

# Utility Functions
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_manager: AuthManager = Depends()
) -> dict:
    """Get current authenticated user with enhanced validation"""
    try:
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        payload = await auth_manager.verify_token(credentials.credentials)
        
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def validate_rate_limit(
    user: dict,
    cache_manager: RedisCacheManager,
    endpoint: str
) -> None:
    """Validate rate limiting for user"""
    user_id = user.get("sub")
    tier = user.get("tier", "free")
    limits = RATE_LIMITS.get(tier, RATE_LIMITS["free"])
    
    # Check per-minute limit
    minute_key = f"rate_limit:{user_id}:{endpoint}:minute:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
    minute_count = await cache_manager.increment(minute_key, expire=60)
    
    if minute_count > limits["requests_per_minute"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {limits['requests_per_minute']} requests per minute",
            headers={"Retry-After": "60"}
        )
    
    # Check per-day limit
    day_key = f"rate_limit:{user_id}:{endpoint}:day:{datetime.utcnow().strftime('%Y%m%d')}"
    day_count = await cache_manager.increment(day_key, expire=86400)
    
    if day_count > limits["requests_per_day"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit exceeded: {limits['requests_per_day']} requests per day",
            headers={"Retry-After": str(86400 - (int(time.time()) % 86400))}
        )

async def validate_analysis_limits(
    user: dict,
    db_manager: DatabaseManager
) -> None:
    """Validate user analysis limits"""
    user_id = user.get("sub")
    tier = user.get("tier", "free")
    
    # Get current usage
    today = datetime.utcnow().date()
    daily_count = await db_manager.get_user_daily_analysis_count(user_id, today)
    
    # Tier limits
    limits = {
        "free": {"daily": 10, "concurrent": 2},
        "pro": {"daily": 100, "concurrent": 5},
        "enterprise": {"daily": 1000, "concurrent": 20}
    }
    
    tier_limits = limits.get(tier, limits["free"])
    
    # Check daily limit
    if daily_count >= tier_limits["daily"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily analysis limit reached ({tier_limits['daily']} analyses)",
            headers={"X-Daily-Limit": str(tier_limits["daily"]), "X-Daily-Used": str(daily_count)}
        )
    
    # Check concurrent analyses
    concurrent_count = await db_manager.get_user_concurrent_analyses(user_id)
    if concurrent_count >= tier_limits["concurrent"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Concurrent analysis limit reached ({tier_limits['concurrent']} concurrent)",
            headers={"X-Concurrent-Limit": str(tier_limits["concurrent"])}
        )

def track_metrics(endpoint: str):
    """Decorator to track endpoint metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            metrics = MetricsCollector()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                await metrics.record_request(
                    endpoint=endpoint,
                    status="success",
                    duration=duration
                )
                
                return result
                
            except HTTPException as e:
                duration = time.time() - start_time
                await metrics.record_request(
                    endpoint=endpoint,
                    status="error",
                    duration=duration,
                    error_code=e.status_code
                )
                raise
                
            except Exception as e:
                duration = time.time() - start_time
                await metrics.record_request(
                    endpoint=endpoint,
                    status="error",
                    duration=duration,
                    error_type=type(e).__name__
                )
                raise
        
        return wrapper
    return decorator

# Main API Endpoints

@router.post("/code", response_model=AnalysisResult, status_code=status.HTTP_202_ACCEPTED)
@track_metrics("analyze_code")
async def analyze_code_direct(
    request: CodeAnalysisRequest,
    background_tasks: BackgroundTasks,
    req: Request,
    user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(),
    orchestrator: AgentOrchestrator = Depends(),
    learning_engine: LearningEngine = Depends(),
    cache_manager: RedisCacheManager = Depends()
):
    """
    Analyze source code with comprehensive quality, security, and performance analysis.
    
    - **Supports all major programming languages** with intelligent auto-detection
    - **Real-time streaming analysis** with WebSocket support
    - **Learning-driven insights** that improve over time
    - **Detailed metrics** including quality scores, security issues, and performance insights
    
    Rate Limits:
    - Free: 10/minute, 100/day
    - Pro: 60/minute, 1000/day
    - Enterprise: 300/minute, 10000/day
    """
    try:
        # Rate limiting
        await validate_rate_limit(user, cache_manager, "analyze_code")
        
        # Validate limits
        await validate_analysis_limits(user, db_manager)
        
        analysis_id = str(uuid.uuid4())
        user_id = user.get("sub")
        
        logger.info(f"Starting code analysis {analysis_id} for user {user_id}")
        
        # Create analysis record with transaction
        async with db_manager.transaction() as tx:
            analysis_data = {
                "analysis_id": analysis_id,
                "user_id": user_id,
                "analysis_type": request.analysis_type,
                "status": AnalysisStatus.PENDING,
                "created_at": datetime.utcnow(),
                "request_data": request.dict(exclude={'code'}),  # Don't store full code
                "priority": request.priority,
                "timeout_at": datetime.utcnow() + timedelta(seconds=request.timeout_seconds),
                "client_ip": req.client.host if req.client else None
            }
            
            await db_manager.create_analysis_record(analysis_data, transaction=tx)
        
        # Prepare context
        context = {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "code": request.code,
            "language": request.language,
            "filename": request.filename,
            "project_context": request.project_context,
            "analysis_type": request.analysis_type,
            "include_suggestions": request.include_suggestions,
            "include_metrics": request.include_metrics,
            "learning_context": request.learning_context,
            "priority": request.priority,
            "timeout_seconds": request.timeout_seconds
        }
        
        # Start background processing with timeout
        background_tasks.add_task(
            process_code_analysis_safe,
            analysis_id=analysis_id,
            context=context,
            orchestrator=orchestrator,
            learning_engine=learning_engine,
            db_manager=db_manager
        )
        
        # Return immediate response
        return AnalysisResult(
            analysis_id=analysis_id,
            status=AnalysisStatus.IN_PROGRESS,
            analysis_type=request.analysis_type,
            created_at=datetime.utcnow(),
            confidence_score=0.0,  # Will be updated
            processing_notes=[
                "Analysis initiated successfully",
                f"Priority: {request.priority}",
                "Processing through multi-agent system"
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis initiation failed: {str(e)}", exc_info=True)
        
        if 'analysis_id' in locals():
            try:
                await db_manager.update_analysis_status(
                    analysis_id, 
                    AnalysisStatus.FAILED, 
                    str(e)
                )
            except:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis initiation failed: {str(e)}"
        )

@router.get("/{analysis_id}", response_model=AnalysisResult)
@track_metrics("get_analysis")
async def get_analysis_result(
    analysis_id: str = Path(..., regex="^[a-f0-9-]{36}$"),
    user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(),
    cache_manager: RedisCacheManager = Depends()
):
    """
    Retrieve detailed results for a specific analysis.
    
    Returns comprehensive metrics, suggestions, and learning insights.
    Results are cached for improved performance.
    """
    try:
        user_id = user.get("sub")
        
        # Try cache first
        cache_key = f"analysis:{analysis_id}:{user_id}"
        cached_result = await cache_manager.get(cache_key)
        
        if cached_result:
            logger.debug(f"Analysis {analysis_id} served from cache")
            return AnalysisResult(**json.loads(cached_result))
        
        # Get from database
        analysis = await db_manager.get_analysis_by_id(analysis_id, user_id)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found or access denied"
            )
        
        # Cache completed analyses
        if analysis.status == AnalysisStatus.COMPLETED:
            await cache_manager.set(
                cache_key,
                json.dumps(analysis.dict()),
                expire=3600  # 1 hour
            )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis"
        )

@router.get("/", response_model=AnalysisListResponse)
@track_metrics("list_analyses")
async def list_user_analyses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[AnalysisStatus] = Query(None, description="Filter by status"),
    type_filter: Optional[AnalysisType] = Query(None, description="Filter by type"),
    sort_by: str = Query("created_at", regex="^(created_at|completed_at|confidence_score)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends()
):
    """
    List all analyses for the authenticated user with filtering and pagination.
    
    Supports:
    - Status and type filtering
    - Flexible sorting
    - Pagination with metadata
    """
    try:
        user_id = user.get("sub")
        
        analyses, total_count = await db_manager.get_user_analyses(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status_filter=status_filter,
            type_filter=type_filter,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        has_next = (page * page_size) < total_count
        has_previous = page > 1
        
        return AnalysisListResponse(
            analyses=analyses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except Exception as e:
        logger.error(f"Failed to list analyses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analyses"
        )

@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
@track_metrics("delete_analysis")
async def delete_analysis(
    analysis_id: str = Path(..., regex="^[a-f0-9-]{36}$"),
    user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(),
    orchestrator: AgentOrchestrator = Depends(),
    cache_manager: RedisCacheManager = Depends()
):
    """
    Delete an analysis and cancel if still in progress.
    
    This operation cannot be undone.
    """
    try:
        user_id = user.get("sub")
        
        # Verify ownership
        analysis = await db_manager.get_analysis_by_id(analysis_id, user_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found or access denied"
            )
        
        # Cancel if in progress
        if analysis.status in [AnalysisStatus.PENDING, AnalysisStatus.IN_PROGRESS]:
            await orchestrator.cancel_analysis(analysis_id)
            logger.info(f"Cancelled in-progress analysis {analysis_id}")
        
        # Delete from database
        await db_manager.delete_analysis(analysis_id, user_id)
        
        # Clear cache
        cache_key = f"analysis:{analysis_id}:{user_id}"
        await cache_manager.delete(cache_key)
        
        logger.info(f"Deleted analysis {analysis_id} for user {user_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete analysis"
        )

@router.get("/stats/user")
@track_metrics("get_user_stats")
async def get_user_analysis_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(),
    cache_manager: RedisCacheManager = Depends()
):
    """
    Get comprehensive analysis statistics for the authenticated user.
    
    Includes:
    - Usage patterns
    - Success rates
    - Language distribution
    - Learning progress
    """
    try:
        user_id = user.get("sub")
        
        # Try cache
        cache_key = f"user_stats:{user_id}:{days}"
        cached_stats = await cache_manager.get(cache_key)
        
        if cached_stats:
            return json.loads(cached_stats)
        
        stats = await db_manager.get_user_analysis_stats(user_id, days)
        
        result = {
            "user_id": user_id,
            "period_days": days,
            "total_analyses": stats.get("total_analyses", 0),
            "completed_analyses": stats.get("completed_analyses", 0),
            "failed_analyses": stats.get("failed_analyses", 0),
            "success_rate": round(stats.get("success_rate", 0.0), 2),
            "average_duration": round(stats.get("average_duration", 0.0), 2),
            "most_used_types": stats.get("most_used_types", []),
            "languages_analyzed": stats.get("languages_analyzed", []),
            "total_lines_analyzed": stats.get("total_lines_analyzed", 0),
            "improvement_score": round(stats.get("improvement_score", 0.0), 2),
            "learning_progress": stats.get("learning_progress", {}),
            "trend": stats.get("trend", "stable")
        }
        
        # Cache for 5 minutes
        await cache_manager.set(cache_key, json.dumps(result), expire=300)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to retrieve user stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )

# Background Processing Functions with Error Handling

async def process_code_analysis_safe(
    analysis_id: str,
    context: Dict[str, Any],
    orchestrator: AgentOrchestrator,
    learning_engine: LearningEngine,
    db_manager: DatabaseManager
):
    """
    Safely process code analysis with comprehensive error handling and timeout
    """
    try:
        # Set timeout
        timeout_seconds = context.get("timeout_seconds", 300)
        
        # Update status
        await db_manager.update_analysis_status(analysis_id, AnalysisStatus.IN_PROGRESS)
        
        # Execute with timeout
        result = await asyncio.wait_for(
            process_code_analysis(
                analysis_id=analysis_id,
                context=context,
                orchestrator=orchestrator,
                learning_engine=learning_engine,
                db_manager=db_manager
            ),
            timeout=timeout_seconds
        )
        
        logger.info(f"Analysis {analysis_id} completed successfully")
        
    except asyncio.TimeoutError:
        logger.warning(f"Analysis {analysis_id} timed out")
        await db_manager.update_analysis_status(
            analysis_id, 
            AnalysisStatus.TIMEOUT,
            "Analysis exceeded timeout limit"
        )
        await learning_engine.record_analysis_failure(
            analysis_id,
            "timeout",
            context
        )
        
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {str(e)}", exc_info=True)
        await db_manager.update_analysis_status(
            analysis_id,
            AnalysisStatus.FAILED,
            str(e)
        )
        await learning_engine.record_analysis_failure(
            analysis_id,
            str(e),
            context
        )

async def process_code_analysis(
    analysis_id: str,
    context: Dict[str, Any],
    orchestrator: AgentOrchestrator,
    learning_engine: LearningEngine,
    db_manager: DatabaseManager
) -> Dict[str, Any]:
    """Process code analysis with learning integration"""
    try:
        # Execute through orchestrator
        result = await orchestrator.process_code_analysis(context)
        
        # Validate result
        if not result or "status" not in result:
            raise ValueError("Invalid analysis result format")
        
        # Process through learning engine
        learning_insights = await learning_engine.analyze_code_patterns(
            analysis_id=analysis_id,
            code=context["code"],
            language=context["language"],
            analysis_result=result
        )
        
        # Enhance result with learning insights
        result["learning_insights"] = learning_insights
        result["confidence_score"] = learning_insights.get("confidence", 85.0)
        
        # Calculate comprehensive metrics
        if "quality_metrics" in result:
            result["quality_metrics"]["overall_score"] = calculate_overall_score(
                result["quality_metrics"]
            )
        
        # Store final result with completion time
        result["completed_at"] = datetime.utcnow().isoformat()
        result["duration_seconds"] = (
            datetime.utcnow() - datetime.fromisoformat(result.get("created_at", datetime.utcnow().isoformat()))
        ).total_seconds()
        
        await db_manager.update_analysis_result(
            analysis_id,
            AnalysisStatus.COMPLETED,
            result
        )
        
        # Feed back to learning engine for continuous improvement
        await learning_engine.record_analysis_success(analysis_id, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Code analysis processing error: {str(e)}", exc_info=True)
        raise

def calculate_overall_score(metrics: Dict[str, Any]) -> float:
    """Calculate weighted overall quality score"""
    weights = {
        "maintainability_score": 0.3,
        "complexity_score": 0.25,
        "readability_score": 0.25,
        "test_coverage": 0.2
    }
    
    total_score = 0.0
    total_weight = 0.0
    
    for metric, weight in weights.items():
        if metric in metrics and metrics[metric] is not None:
            total_score += metrics[metric] * weight
            total_weight += weight
    
    return round(total_score / total_weight if total_weight > 0 else 0.0, 2)

# Additional utility endpoints

@router.post("/{analysis_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
@track_metrics("cancel_analysis")
async def cancel_analysis(
    analysis_id: str = Path(..., regex="^[a-f0-9-]{36}$"),
    user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(),
    orchestrator: AgentOrchestrator = Depends()
):
    """
    Cancel an in-progress analysis.
    """
    try:
        user_id = user.get("sub")
        
        # Verify ownership and status
        analysis = await db_manager.get_analysis_by_id(analysis_id, user_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found or access denied"
            )
        
        if analysis.status not in [AnalysisStatus.PENDING, AnalysisStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel analysis with status: {analysis.status}"
            )
        
        # Cancel through orchestrator
        await orchestrator.cancel_analysis(analysis_id)
        
        # Update status
        await db_manager.update_analysis_status(
            analysis_id,
            AnalysisStatus.CANCELLED,
            "Cancelled by user"
        )
        
        logger.info(f"Analysis {analysis_id} cancelled by user {user_id}")
        
        return {
            "message": "Analysis cancelled successfully",
            "analysis_id": analysis_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel analysis"
        )

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(
    db_manager: DatabaseManager = Depends(),
    cache_manager: RedisCacheManager = Depends(),
    orchestrator: AgentOrchestrator = Depends()
):
    """
    Health check endpoint for monitoring.
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Check database
        try:
            await db_manager.health_check()
            health_status["components"]["database"] = "healthy"
        except Exception as e:
            health_status["components"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check cache
        try:
            await cache_manager.health_check()
            health_status["components"]["cache"] = "healthy"
        except Exception as e:
            health_status["components"]["cache"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check orchestrator
        try:
            orchestrator_status = await orchestrator.health_check()
            health_status["components"]["orchestrator"] = orchestrator_status
        except Exception as e:
            health_status["components"]["orchestrator"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        status_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/limits", status_code=status.HTTP_200_OK)
async def get_user_limits(
    user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends()
):
    """
    Get current usage and limits for the authenticated user.
    """
    try:
        user_id = user.get("sub")
        tier = user.get("tier", "free")
        
        # Get current usage
        today = datetime.utcnow().date()
        daily_count = await db_manager.get_user_daily_analysis_count(user_id, today)
        concurrent_count = await db_manager.get_user_concurrent_analyses(user_id)
        
        # Get tier limits
        tier_limits = {
            "free": {"daily": 10, "concurrent": 2},
            "pro": {"daily": 100, "concurrent": 5},
            "enterprise": {"daily": 1000, "concurrent": 20}
        }
        
        limits = tier_limits.get(tier, tier_limits["free"])
        rate_limits = RATE_LIMITS.get(tier, RATE_LIMITS["free"])
        
        return {
            "user_id": user_id,
            "tier": tier,
            "usage": {
                "daily_analyses": daily_count,
                "concurrent_analyses": concurrent_count
            },
            "limits": {
                "daily_analyses": limits["daily"],
                "concurrent_analyses": limits["concurrent"],
                "requests_per_minute": rate_limits["requests_per_minute"],
                "requests_per_day": rate_limits["requests_per_day"]
            },
            "remaining": {
                "daily_analyses": max(0, limits["daily"] - daily_count),
                "concurrent_analyses": max(0, limits["concurrent"] - concurrent_count)
            },
            "reset_time": datetime.combine(
                today + timedelta(days=1),
                datetime.min.time()
            ).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get user limits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user limits"
        )

# Error handlers
@router.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {str(exc)}")
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(exc)
    )

@router.exception_handler(AnalysisError)
async def analysis_error_handler(request: Request, exc: AnalysisError):
    """Handle analysis-specific errors"""
    logger.error(f"Analysis error: {str(exc)}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Analysis error: {str(exc)}"
    )