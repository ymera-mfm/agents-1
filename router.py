"""
API Router - Main API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import structlog
import io

logger = structlog.get_logger(__name__)

api_router = APIRouter()


# Request/Response Models
class AgentSubmission(BaseModel):
    """Agent submission model"""
    agent_name: str = Field(..., description="Name of the source agent")
    output_type: str = Field(..., description="Type of output (code, documentation, test)")
    content: str = Field(..., description="Content/code")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class KnowledgeSubmission(BaseModel):
    """Knowledge submission model"""
    source: str = Field(..., description="Source of knowledge")
    knowledge_type: str = Field(..., description="Type of knowledge")
    content: Dict[str, Any] = Field(..., description="Knowledge content")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")


class ChatMessage(BaseModel):
    """Chat message model"""
    user_id: str = Field(..., description="User ID")
    message: str = Field(..., description="Message content")


class KnowledgeRequest(BaseModel):
    """Knowledge request model"""
    agent_name: str = Field(..., description="Requesting agent name")
    task_context: Dict[str, Any] = Field(..., description="Task context")


# Dependency injection helpers
async def get_project_agent(request: Request):
    """Get project agent from app state"""
    return request.app.state.project_agent


async def get_learning_agent(request: Request):
    """Get learning agent from app state"""
    return request.app.state.learning_agent


# Project Agent Endpoints
@api_router.post("/project-agent/submit", tags=["Project Agent"])
async def submit_to_project_agent(
    submission: AgentSubmission,
    project_agent = Depends(get_project_agent)
):
    """Submit output to project agent for verification and integration"""
    try:
        result = await project_agent.receive_agent_output(
            agent_name=submission.agent_name,
            output_type=submission.output_type,
            content=submission.content,
            metadata=submission.metadata
        )
        return result
    except Exception as e:
        logger.error(f"Submission error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/project-agent/chat", tags=["Project Agent"])
async def chat_with_project_agent(
    message: ChatMessage,
    project_agent = Depends(get_project_agent)
):
    """Chat with project agent"""
    try:
        result = await project_agent.chat_with_user(message.user_id, message.message)
        return result
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/project-agent/upload", tags=["Project Agent"])
async def upload_file_to_project_agent(
    file: UploadFile = File(...),
    metadata: str = Form(default="{}"),
    project_agent = Depends(get_project_agent)
):
    """Upload file to project agent"""
    try:
        import json
        file_data = await file.read()
        metadata_dict = json.loads(metadata)
        
        result = await project_agent.upload_file(
            file_data=file_data,
            filename=file.filename,
            metadata=metadata_dict
        )
        return result
    except Exception as e:
        logger.error(f"File upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/project-agent/download/{file_id}", tags=["Project Agent"])
async def download_file_from_project_agent(
    file_id: str,
    project_agent = Depends(get_project_agent)
):
    """Download file from project agent"""
    try:
        file_data, filename = await project_agent.download_file(file_id)
        
        if file_data is None:
            raise HTTPException(status_code=404, detail="File not found")
        
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/project-agent/status/{project_id}", tags=["Project Agent"])
async def get_project_status(
    project_id: str,
    project_agent = Depends(get_project_agent)
):
    """Get project status"""
    try:
        result = await project_agent.get_project_status(project_id)
        return result
    except Exception as e:
        logger.error(f"Status query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Learning Agent Endpoints
@api_router.post("/learning-agent/knowledge", tags=["Learning Agent"])
async def submit_knowledge(
    submission: KnowledgeSubmission,
    learning_agent = Depends(get_learning_agent)
):
    """Submit knowledge to learning agent"""
    try:
        result = await learning_agent.receive_knowledge(
            source=submission.source,
            knowledge_type=submission.knowledge_type,
            content=submission.content,
            tags=submission.tags
        )
        return result
    except Exception as e:
        logger.error(f"Knowledge submission error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/learning-agent/request-knowledge", tags=["Learning Agent"])
async def request_knowledge(
    request: KnowledgeRequest,
    learning_agent = Depends(get_learning_agent)
):
    """Request knowledge from learning agent"""
    try:
        result = await learning_agent.provide_knowledge(
            agent_name=request.agent_name,
            task_context=request.task_context
        )
        return result
    except Exception as e:
        logger.error(f"Knowledge request error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/learning-agent/analyze-code", tags=["Learning Agent"])
async def analyze_code(
    code: str = Form(...),
    metadata: str = Form(default="{}"),
    learning_agent = Depends(get_learning_agent)
):
    """Analyze code using learning agent"""
    try:
        import json
        metadata_dict = json.loads(metadata)
        
        result = await learning_agent.analyze_code(code, metadata_dict)
        return result
    except Exception as e:
        logger.error(f"Code analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/learning-agent/report", tags=["Learning Agent"])
async def get_learning_report(
    learning_agent = Depends(get_learning_agent)
):
    """Get learning agent report"""
    try:
        result = await learning_agent.report_to_manager()
        return result
    except Exception as e:
        logger.error(f"Report generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# System Endpoints
@api_router.get("/system/info", tags=["System"])
async def get_system_info(request: Request):
    """Get system information"""
    return {
        "service": "Unified Agent System",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "agents": {
            "project_agent": {
                "status": "active" if request.app.state.project_agent.is_ready() else "inactive"
            },
            "learning_agent": {
                "status": "active" if request.app.state.learning_agent.is_ready() else "inactive"
            }
        }
    }
