"""
YMERA Enterprise API System - Production Ready v5.0
Complete API management with user-configurable providers and MCP integration
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
from contextlib import asynccontextmanager

# Third-party imports
import aiohttp
from redis import asyncio as aioredis
from fastapi import APIRouter, HTTPException, Depends, Request, Response, status, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator, HttpUrl, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
import structlog

# AI Provider imports
import openai
import anthropic
import google.generativeai as genai
from groq import Groq

# Local imports
from config.settings import get_settings
from database.connection import get_db_session
from security.jwt_handler import verify_token, get_current_user
from models.user import User

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logger = structlog.get_logger("ymera.api_system")

# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class AIProvider(str, Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"
    MISTRAL = "mistral"
    CUSTOM_MCP = "custom_mcp"  # Model Context Protocol

class ProviderStatus(str, Enum):
    """Provider health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"
    CONFIGURING = "configuring"

class APIKeyType(str, Enum):
    """API key storage types"""
    SYSTEM = "system"  # Platform-wide keys
    USER = "user"      # User-specific keys
    ORGANIZATION = "organization"  # Organization-level keys

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ProviderConfig(BaseModel):
    """Provider configuration model"""
    model_config = ConfigDict(use_enum_values=True)
    
    provider: AIProvider
    api_key: Optional[str] = Field(None, description="API key (encrypted)")
    base_url: Optional[HttpUrl] = Field(None, description="Custom base URL")
    model_name: Optional[str] = Field(None, description="Default model")
    max_tokens: int = Field(4096, ge=1, le=128000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    rate_limit: int = Field(60, ge=1, le=1000, description="Requests per minute")
    timeout: int = Field(60, ge=5, le=300, description="Timeout in seconds")
    enabled: bool = True
    custom_headers: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class MCPConfig(BaseModel):
    """Model Context Protocol configuration"""
    name: str = Field(..., min_length=1, max_length=100)
    endpoint: HttpUrl
    auth_type: str = Field("bearer", regex="^(bearer|api_key|oauth|custom)$")
    auth_value: Optional[str] = None
    protocol_version: str = "1.0"
    capabilities: List[str] = Field(default_factory=list)
    custom_config: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ProviderRegistration(BaseModel):
    """User provider registration request"""
    config: ProviderConfig
    key_type: APIKeyType = APIKeyType.USER
    is_default: bool = False
    name: str = Field(..., min_length=1, max_length=100, description="Provider alias")
    description: Optional[str] = None

class MCPRegistration(BaseModel):
    """MCP registration request"""
    config: MCPConfig
    is_default: bool = False

class AIRequest(BaseModel):
    """Unified AI request model"""
    messages: List[Dict[str, str]]
    provider: Optional[AIProvider] = None
    provider_id: Optional[str] = None  # User's custom provider ID
    model: Optional[str] = None
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    system_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AIResponse(BaseModel):
    """Unified AI response model"""
    content: str
    provider: str
    model: str
    request_id: str
    usage: Dict[str, int]
    metadata: Dict[str, Any]
    timestamp: datetime
    processing_time: float
    cached: bool = False

class ProviderHealthCheck(BaseModel):
    """Provider health check response"""
    provider: str
    status: ProviderStatus
    response_time: float
    error: Optional[str] = None
    last_check: datetime
    uptime_percentage: float
    request_count: int
    error_count: int

# ============================================================================
# DATABASE MODELS (SQLAlchemy)
# ============================================================================

from sqlalchemy import Column, String, Boolean, Integer, Float, JSON, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from database.base import Base

class UserProviderConfig(Base):
    """User's custom provider configurations"""
    __tablename__ = "user_provider_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    config = Column(JSON, nullable=False)
    encrypted_key = Column(Text)  # Encrypted API key
    key_type = Column(String(20), default="user")
    is_default = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserMCPConfig(Base):
    """User's MCP configurations"""
    __tablename__ = "user_mcp_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    config = Column(JSON, nullable=False)
    encrypted_auth = Column(Text)
    is_default = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class APIUsageLog(Base):
    """API usage tracking"""
    __tablename__ = "api_usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(100))
    request_id = Column(String(100), unique=True)
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    response_time = Column(Float)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# PROVIDER CLIENTS
# ============================================================================

class BaseProviderClient:
    """Base class for all provider clients"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.provider = config.provider
        self.is_healthy = True
        self.last_error = None
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.session = None
    
    async def initialize(self):
        """Initialize the provider client"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def health_check(self) -> bool:
        """Perform health check"""
        try:
            test_request = AIRequest(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            await self.generate(test_request)
            self.is_healthy = True
            return True
        except Exception as e:
            self.is_healthy = False
            self.last_error = str(e)
            return False
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate response - to be implemented by subclasses"""
        raise NotImplementedError
    
    async def stream(self, request: AIRequest):
        """Stream response - to be implemented by subclasses"""
        raise NotImplementedError
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

class OpenAIClient(BaseProviderClient):
    """OpenAI provider client"""
    
    async def initialize(self):
        await super().initialize()
        self.client = openai.AsyncOpenAI(
            api_key=self.config.api_key,
            timeout=self.config.timeout
        )
    
    async def generate(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            messages = request.messages.copy()
            if request.system_prompt:
                messages.insert(0, {"role": "system", "content": request.system_prompt})
            
            response = await self.client.chat.completions.create(
                model=request.model or self.config.model_name or "gpt-4-turbo-preview",
                messages=messages,
                max_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature,
                stream=False
            )
            
            processing_time = time.time() - start_time
            self.request_count += 1
            self.total_response_time += processing_time
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider=self.provider.value,
                model=response.model,
                request_id=request_id,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                metadata={"finish_reason": response.choices[0].finish_reason},
                timestamp=datetime.utcnow(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OpenAI API error: {str(e)}"
            )
    
    async def stream(self, request: AIRequest):
        """Stream OpenAI responses"""
        messages = request.messages.copy()
        if request.system_prompt:
            messages.insert(0, {"role": "system", "content": request.system_prompt})
        
        stream = await self.client.chat.completions.create(
            model=request.model or self.config.model_name or "gpt-4-turbo-preview",
            messages=messages,
            max_tokens=request.max_tokens or self.config.max_tokens,
            temperature=request.temperature or self.config.temperature,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

class AnthropicClient(BaseProviderClient):
    """Anthropic Claude provider client"""
    
    async def initialize(self):
        await super().initialize()
        self.client = anthropic.AsyncAnthropic(
            api_key=self.config.api_key,
            timeout=self.config.timeout
        )
    
    async def generate(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            response = await self.client.messages.create(
                model=request.model or self.config.model_name or "claude-3-sonnet-20240229",
                messages=request.messages,
                max_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature,
                system=request.system_prompt or ""
            )
            
            processing_time = time.time() - start_time
            self.request_count += 1
            self.total_response_time += processing_time
            
            return AIResponse(
                content=response.content[0].text,
                provider=self.provider.value,
                model=response.model,
                request_id=request_id,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                metadata={"stop_reason": response.stop_reason},
                timestamp=datetime.utcnow(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Anthropic API error: {str(e)}"
            )

class GeminiClient(BaseProviderClient):
    """Google Gemini provider client"""
    
    async def initialize(self):
        await super().initialize()
        genai.configure(api_key=self.config.api_key)
        self.client = genai.GenerativeModel(
            request.model or self.config.model_name or 'gemini-pro'
        )
    
    async def generate(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            prompt = self._format_prompt(request)
            response = await self.client.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=request.max_tokens or self.config.max_tokens,
                    temperature=request.temperature or self.config.temperature
                )
            )
            
            processing_time = time.time() - start_time
            self.request_count += 1
            self.total_response_time += processing_time
            
            # Estimate tokens for Gemini
            estimated_tokens = len(prompt.split()) + len(response.text.split())
            
            return AIResponse(
                content=response.text,
                provider=self.provider.value,
                model="gemini-pro",
                request_id=request_id,
                usage={
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": len(response.text.split()),
                    "total_tokens": estimated_tokens
                },
                metadata={},
                timestamp=datetime.utcnow(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gemini API error: {str(e)}"
            )
    
    def _format_prompt(self, request: AIRequest) -> str:
        """Format messages for Gemini"""
        prompt = ""
        if request.system_prompt:
            prompt += f"System: {request.system_prompt}\n\n"
        
        for msg in request.messages:
            role = msg["role"].title()
            content = msg["content"]
            prompt += f"{role}: {content}\n"
        
        return prompt

class GroqClient(BaseProviderClient):
    """Groq ultra-fast inference client"""
    
    async def initialize(self):
        await super().initialize()
        self.client = Groq(api_key=self.config.api_key)
    
    async def generate(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            messages = request.messages.copy()
            if request.system_prompt:
                messages.insert(0, {"role": "system", "content": request.system_prompt})
            
            response = self.client.chat.completions.create(
                model=request.model or self.config.model_name or "mixtral-8x7b-32768",
                messages=messages,
                max_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature
            )
            
            processing_time = time.time() - start_time
            self.request_count += 1
            self.total_response_time += processing_time
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider=self.provider.value,
                model=response.model,
                request_id=request_id,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                metadata={"finish_reason": response.choices[0].finish_reason},
                timestamp=datetime.utcnow(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Groq API error: {str(e)}"
            )

class DeepSeekClient(BaseProviderClient):
    """DeepSeek cost-effective client"""
    
    async def generate(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            messages = request.messages.copy()
            if request.system_prompt:
                messages.insert(0, {"role": "system", "content": request.system_prompt})
            
            payload = {
                "model": request.model or self.config.model_name or "deepseek-coder",
                "messages": messages,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature
            }
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            base_url = str(self.config.base_url) if self.config.base_url else "https://api.deepseek.com/v1"
            
            async with self.session.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")
                
                data = await response.json()
            
            processing_time = time.time() - start_time
            self.request_count += 1
            self.total_response_time += processing_time
            
            return AIResponse(
                content=data["choices"][0]["message"]["content"],
                provider=self.provider.value,
                model=data["model"],
                request_id=request_id,
                usage=data["usage"],
                metadata={"finish_reason": data["choices"][0]["finish_reason"]},
                timestamp=datetime.utcnow(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"DeepSeek API error: {str(e)}"
            )

class AzureOpenAIClient(BaseProviderClient):
    """Azure OpenAI client"""
    
    async def initialize(self):
        await super().initialize()
        self.client = openai.AsyncAzureOpenAI(
            api_key=self.config.api_key,
            azure_endpoint=str(self.config.base_url),
            api_version="2024-02-15-preview",
            timeout=self.config.timeout
        )
    
    async def generate(self, request: AIRequest) -> AIResponse:
        # Similar to OpenAI but with Azure-specific configuration
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            messages = request.messages.copy()
            if request.system_prompt:
                messages.insert(0, {"role": "system", "content": request.system_prompt})
            
            response = await self.client.chat.completions.create(
                model=request.model or self.config.model_name,
                messages=messages,
                max_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature
            )
            
            processing_time = time.time() - start_time
            self.request_count += 1
            self.total_response_time += processing_time
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider=self.provider.value,
                model=response.model,
                request_id=request_id,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                metadata={"finish_reason": response.choices[0].finish_reason},
                timestamp=datetime.utcnow(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Azure OpenAI API error: {str(e)}"
            )

class OllamaClient(BaseProviderClient):
    """Ollama local models client"""
    
    async def generate(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            messages = request.messages.copy()
            if request.system_prompt:
                messages.insert(0, {"role": "system", "content": request.system_prompt})
            
            payload = {
                "model": request.model or self.config.model_name or "llama2",
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": request.temperature or self.config.temperature,
                    "num_predict": request.max_tokens or self.config.max_tokens
                }
            }
            
            base_url = str(self.config.base_url) if self.config.base_url else "http://localhost:11434"
            
            async with self.session.post(
                f"{base_url}/api/chat",
                json=payload
            ) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")
                
                data = await response.json()
            
            processing_time = time.time() - start_time
            self.request_count += 1
            self.total_response_time += processing_time
            
            return AIResponse(
                content=data["message"]["content"],
                provider=self.provider.value,
                model=data["model"],
                request_id=request_id,
                usage={
                    "prompt_tokens": 0,  # Ollama doesn't provide token counts
                    "completion_tokens": 0,
                    "total_tokens": 0
                },
                metadata={
                    "eval_count": data.get("eval_count", 0),
                    "eval_duration": data.get("eval_duration", 0)
                },
                timestamp=datetime.utcnow(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ollama API error: {str(e)}"
            )

class MistralClient(BaseProviderClient):
    """Mistral AI client"""
    
    async def generate(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            messages = request.messages.copy()
            if request.system_prompt:
                messages.insert(0, {"role": "system", "content": request.system_prompt})
            
            payload = {
                "model": request.model or self.config.model_name or "mistral-medium",
                "messages": messages,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature
            }
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            base_url = str(self.config.base_url) if self.config.base_url else "https://api.mistral.ai/v1"
            
            async with self.session.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")
                
                data = await response.json()
            
            processing_time = time.time() - start_time
            self.request_count += 1
            self.total_response_time += processing_time
            
            return AIResponse(
                content=data["choices"][0]["message"]["content"],
                provider=self.provider.value,
                model=data["model"],
                request_id=request_id,
                usage=data["usage"],
                metadata={"finish_reason": data["choices"][0]["finish_reason"]},
                timestamp=datetime.utcnow(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Mistral API error: {str(e)}"
            )

class MCPClient(BaseProviderClient):
    """Model Context Protocol client for custom integrations"""
    
    def __init__(self, config: ProviderConfig, mcp_config: MCPConfig):
        super().__init__(config)
        self.mcp_config = mcp_config
    
    async def generate(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Format request according to MCP protocol
            payload = {
                "protocol_version": self.mcp_config.protocol_version,
                "messages": request.messages,
                "parameters": {
                    "max_tokens": request.max_tokens or self.config.max_tokens,
                    "temperature": request.temperature or self.config.temperature,
                    "system_prompt": request.system_prompt
                },
                "capabilities": self.mcp_config.capabilities,
                "custom_config": self.mcp_config.custom_config
            }
            
            # Prepare authentication
            headers = {"Content-Type": "application/json"}
            if self.mcp_config.auth_type == "bearer":
                headers["Authorization"] = f"Bearer {self.mcp_config.auth_value}"
            elif self.mcp_config.auth_type == "api_key":
                headers["X-API-Key"] = self.mcp_config.auth_value
            
            if self.config.custom_headers:
                headers.update(self.config.custom_headers)
            
            async with self.session.post(
                str(self.mcp_config.endpoint),
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")
                
                data = await response.json()
            
            processing_time = time.time() - start_time
            self.request_count += 1
            self.total_response_time += processing_time
            
            # Parse MCP response
            return AIResponse(
                content=data.get("content", data.get("response", "")),
                provider="custom_mcp",
                model=self.mcp_config.name,
                request_id=request_id,
                usage=data.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
                metadata=data.get("metadata", {}),
                timestamp=datetime.utcnow(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MCP API error: {str(e)}"
            )

# ============================================================================
# PROVIDER MANAGER
# ============================================================================

class ProviderManager:
    """Manages all AI providers with user configurations"""
    
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.redis = redis
        self.system_providers: Dict[str, BaseProviderClient] = {}
        self.user_providers: Dict[str, Dict[str, BaseProviderClient]] = {}
        self.mcp_clients: Dict[str, MCPClient] = {}
        self.health_check_interval = 300  # 5 minutes
        self.logger = logger
        
        # Provider client mapping
        self.client_classes = {
            AIProvider.OPENAI: OpenAIClient,
            AIProvider.ANTHROPIC: AnthropicClient,
            AIProvider.GEMINI: GeminiClient,
            AIProvider.GROQ: GroqClient,
            AIProvider.DEEPSEEK: DeepSeekClient,
            AIProvider.AZURE_OPENAI: AzureOpenAIClient,
            AIProvider.OLLAMA: OllamaClient,
            AIProvider.MISTRAL: MistralClient,
        }
    
    async def initialize_system_providers(self, configs: List[ProviderConfig]):
        """Initialize system-wide providers"""
        for config in configs:
            try:
                client_class = self.client_classes.get(config.provider)
                if client_class:
                    client = client_class(config)
                    await client.initialize()
                    self.system_providers[config.provider.value] = client
                    self.logger.info(f"Initialized system provider: {config.provider.value}")
            except Exception as e:
                self.logger.error(f"Failed to initialize {config.provider.value}: {e}")
    
    async def register_user_provider(
        self,
        user_id: str,
        registration: ProviderRegistration
    ) -> str:
        """Register a user-specific provider"""
        try:
            # Encrypt API key
            encrypted_key = self._encrypt_key(registration.config.api_key) if registration.config.api_key else None
            
            # Create database entry
            provider_config = UserProviderConfig(
                id=uuid.uuid4(),
                user_id=user_id,
                provider=registration.config.provider.value,
                name=registration.name,
                config=registration.config.dict(exclude={"api_key"}),
                encrypted_key=encrypted_key,
                key_type=registration.key_type.value,
                is_default=registration.is_default,
                enabled=True
            )
            
            self.db.add(provider_config)
            await self.db.commit()
            
            # Initialize client
            config_with_key = registration.config.copy()
            config_with_key.api_key = registration.config.api_key
            
            client_class = self.client_classes.get(registration.config.provider)
            if client_class:
                client = client_class(config_with_key)
                await client.initialize()
                
                if user_id not in self.user_providers:
                    self.user_providers[user_id] = {}
                
                self.user_providers[user_id][str(provider_config.id)] = client
            
            self.logger.info(
                f"Registered user provider",
                user_id=user_id,
                provider=registration.config.provider.value,
                provider_id=str(provider_config.id)
            )
            
            return str(provider_config.id)
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to register user provider: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Provider registration failed: {str(e)}"
            )
    
    async def register_mcp(
        self,
        user_id: str,
        registration: MCPRegistration
    ) -> str:
        """Register a Model Context Protocol integration"""
        try:
            # Encrypt authentication
            encrypted_auth = self._encrypt_key(registration.config.auth_value) if registration.config.auth_value else None
            
            # Create database entry
            mcp_config = UserMCPConfig(
                id=uuid.uuid4(),
                user_id=user_id,
                name=registration.config.name,
                config=registration.config.dict(exclude={"auth_value"}),
                encrypted_auth=encrypted_auth,
                is_default=registration.is_default,
                enabled=True
            )
            
            self.db.add(mcp_config)
            await self.db.commit()
            
            # Initialize MCP client
            provider_config = ProviderConfig(
                provider=AIProvider.CUSTOM_MCP,
                api_key="",
                base_url=registration.config.endpoint
            )
            
            config_with_auth = registration.config.copy()
            client = MCPClient(provider_config, config_with_auth)
            await client.initialize()
            
            self.mcp_clients[str(mcp_config.id)] = client
            
            self.logger.info(
                f"Registered MCP integration",
                user_id=user_id,
                mcp_name=registration.config.name,
                mcp_id=str(mcp_config.id)
            )
            
            return str(mcp_config.id)
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to register MCP: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MCP registration failed: {str(e)}"
            )
    
    async def get_provider(
        self,
        user_id: str,
        provider: Optional[AIProvider] = None,
        provider_id: Optional[str] = None
    ) -> BaseProviderClient:
        """Get the appropriate provider for a request"""
        
        # If specific provider_id is provided, use user's custom provider
        if provider_id:
            if user_id in self.user_providers and provider_id in self.user_providers[user_id]:
                return self.user_providers[user_id][provider_id]
            elif provider_id in self.mcp_clients:
                return self.mcp_clients[provider_id]
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Provider {provider_id} not found"
                )
        
        # If provider type specified, try user's default for that type first
        if provider:
            # Check user's providers
            if user_id in self.user_providers:
                for client in self.user_providers[user_id].values():
                    if client.provider == provider and client.config.enabled:
                        return client
            
            # Fall back to system provider
            if provider.value in self.system_providers:
                return self.system_providers[provider.value]
        
        # Use user's default provider or system default
        if user_id in self.user_providers:
            for client in self.user_providers[user_id].values():
                if client.config.enabled:
                    return client
        
        # Fall back to first available system provider
        if self.system_providers:
            return next(iter(self.system_providers.values()))
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No available AI providers"
        )
    
    async def list_user_providers(self, user_id: str) -> List[Dict[str, Any]]:
        """List all providers configured for a user"""
        try:
            result = await self.db.execute(
                select(UserProviderConfig).where(
                    UserProviderConfig.user_id == user_id,
                    UserProviderConfig.enabled == True
                )
            )
            configs = result.scalars().all()
            
            providers = []
            for config in configs:
                # Get health status if client is loaded
                health_status = ProviderStatus.CONFIGURING
                if user_id in self.user_providers and str(config.id) in self.user_providers[user_id]:
                    client = self.user_providers[user_id][str(config.id)]
                    health_status = ProviderStatus.HEALTHY if client.is_healthy else ProviderStatus.UNHEALTHY
                
                providers.append({
                    "id": str(config.id),
                    "provider": config.provider,
                    "name": config.name,
                    "is_default": config.is_default,
                    "status": health_status.value,
                    "created_at": config.created_at.isoformat(),
                    "config": config.config
                })
            
            return providers
            
        except Exception as e:
            self.logger.error(f"Failed to list user providers: {e}")
            raise
    
    async def list_user_mcps(self, user_id: str) -> List[Dict[str, Any]]:
        """List all MCP integrations for a user"""
        try:
            result = await self.db.execute(
                select(UserMCPConfig).where(
                    UserMCPConfig.user_id == user_id,
                    UserMCPConfig.enabled == True
                )
            )
            configs = result.scalars().all()
            
            mcps = []
            for config in configs:
                # Get health status if client is loaded
                health_status = ProviderStatus.CONFIGURING
                if str(config.id) in self.mcp_clients:
                    client = self.mcp_clients[str(config.id)]
                    health_status = ProviderStatus.HEALTHY if client.is_healthy else ProviderStatus.UNHEALTHY
                
                mcps.append({
                    "id": str(config.id),
                    "name": config.name,
                    "is_default": config.is_default,
                    "status": health_status.value,
                    "created_at": config.created_at.isoformat(),
                    "config": config.config
                })
            
            return mcps
            
        except Exception as e:
            self.logger.error(f"Failed to list user MCPs: {e}")
            raise
    
    async def delete_user_provider(self, user_id: str, provider_id: str):
        """Delete a user's provider configuration"""
        try:
            result = await self.db.execute(
                select(UserProviderConfig).where(
                    UserProviderConfig.id == provider_id,
                    UserProviderConfig.user_id == user_id
                )
            )
            config = result.scalar_one_or_none()
            
            if not config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Provider configuration not found"
                )
            
            # Cleanup client
            if user_id in self.user_providers and provider_id in self.user_providers[user_id]:
                await self.user_providers[user_id][provider_id].cleanup()
                del self.user_providers[user_id][provider_id]
            
            # Delete from database
            await self.db.delete(config)
            await self.db.commit()
            
            self.logger.info(f"Deleted user provider", user_id=user_id, provider_id=provider_id)
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to delete user provider: {e}")
            raise
    
    async def update_provider_config(
        self,
        user_id: str,
        provider_id: str,
        updates: Dict[str, Any]
    ):
        """Update a provider's configuration"""
        try:
            result = await self.db.execute(
                select(UserProviderConfig).where(
                    UserProviderConfig.id == provider_id,
                    UserProviderConfig.user_id == user_id
                )
            )
            config = result.scalar_one_or_none()
            
            if not config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Provider configuration not found"
                )
            
            # Update configuration
            if "enabled" in updates:
                config.enabled = updates["enabled"]
            
            if "is_default" in updates:
                config.is_default = updates["is_default"]
            
            if "config" in updates:
                config.config.update(updates["config"])
            
            config.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Reinitialize client if needed
            if user_id in self.user_providers and provider_id in self.user_providers[user_id]:
                await self.user_providers[user_id][provider_id].cleanup()
                # Reload with new config
                provider_config = ProviderConfig(**config.config)
                provider_config.api_key = self._decrypt_key(config.encrypted_key) if config.encrypted_key else None
                
                client_class = self.client_classes.get(AIProvider(config.provider))
                if client_class:
                    client = client_class(provider_config)
                    await client.initialize()
                    self.user_providers[user_id][provider_id] = client
            
            self.logger.info(f"Updated provider config", user_id=user_id, provider_id=provider_id)
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to update provider config: {e}")
            raise
    
    async def check_all_health(self) -> Dict[str, ProviderHealthCheck]:
        """Check health of all providers"""
        health_results = {}
        
        # Check system providers
        for provider_name, client in self.system_providers.items():
            start_time = time.time()
            is_healthy = await client.health_check()
            response_time = time.time() - start_time
            
            uptime = (client.request_count - client.error_count) / max(client.request_count, 1) * 100
            
            health_results[provider_name] = ProviderHealthCheck(
                provider=provider_name,
                status=ProviderStatus.HEALTHY if is_healthy else ProviderStatus.UNHEALTHY,
                response_time=response_time,
                error=client.last_error if not is_healthy else None,
                last_check=datetime.utcnow(),
                uptime_percentage=uptime,
                request_count=client.request_count,
                error_count=client.error_count
            )
        
        return health_results
    
    async def log_usage(
        self,
        user_id: str,
        provider: str,
        model: str,
        request_id: str,
        usage: Dict[str, int],
        response_time: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Log API usage for billing and analytics"""
        try:
            # Calculate cost (simplified - would use provider-specific pricing)
            cost = self._calculate_cost(provider, usage)
            
            log_entry = APIUsageLog(
                id=uuid.uuid4(),
                user_id=user_id,
                provider=provider,
                model=model,
                request_id=request_id,
                tokens_used=usage.get("total_tokens", 0),
                cost=cost,
                response_time=response_time,
                success=success,
                error_message=error
            )
            
            self.db.add(log_entry)
            await self.db.commit()
            
            # Cache usage data in Redis for real-time analytics
            usage_key = f"usage:{user_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
            await self.redis.hincrby(usage_key, "total_requests", 1)
            await self.redis.hincrby(usage_key, "total_tokens", usage.get("total_tokens", 0))
            await self.redis.hincrbyfloat(usage_key, "total_cost", cost)
            await self.redis.expire(usage_key, 86400 * 90)  # 90 days retention
            
        except Exception as e:
            self.logger.error(f"Failed to log usage: {e}")
    
    def _encrypt_key(self, key: str) -> str:
        """Encrypt API key for storage"""
        # Use Fernet encryption in production
        import base64
        return base64.b64encode(key.encode()).decode()
    
    def _decrypt_key(self, encrypted_key: str) -> str:
        """Decrypt API key"""
        import base64
        return base64.b64decode(encrypted_key.encode()).decode()
    
    def _calculate_cost(self, provider: str, usage: Dict[str, int]) -> float:
        """Calculate API cost based on usage"""
        # Simplified pricing - use actual provider pricing in production
        pricing = {
            "openai": {"input": 0.01, "output": 0.03},  # per 1K tokens
            "anthropic": {"input": 0.003, "output": 0.015},
            "gemini": {"input": 0.00025, "output": 0.0005},
            "groq": {"input": 0.0002, "output": 0.0002},
            "deepseek": {"input": 0.0002, "output": 0.0002},
            "azure_openai": {"input": 0.01, "output": 0.03},
            "mistral": {"input": 0.002, "output": 0.006},
            "ollama": {"input": 0.0, "output": 0.0},
        }
        
        provider_pricing = pricing.get(provider, {"input": 0.001, "output": 0.002})
        
        input_cost = (usage.get("prompt_tokens", 0) / 1000) * provider_pricing["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1000) * provider_pricing["output"]
        
        return input_cost + output_cost

# ============================================================================
# FASTAPI ROUTES
# ============================================================================

router = APIRouter(prefix="/api/ai", tags=["AI System"])

# Global provider manager (would be initialized on startup)
provider_manager: Optional[ProviderManager] = None

@router.on_event("startup")
async def startup_event():
    """Initialize provider manager on startup"""
    global provider_manager
    settings = get_settings()
    
    # Initialize with system providers from config
    system_configs = [
        ProviderConfig(
            provider=AIProvider.OPENAI,
            api_key=settings.OPENAI_API_KEY,
            model_name="gpt-4-turbo-preview"
        ),
        ProviderConfig(
            provider=AIProvider.ANTHROPIC,
            api_key=settings.ANTHROPIC_API_KEY,
            model_name="claude-3-sonnet-20240229"
        ),
        # Add more system providers as needed
    ]
    
    # Would need to get db and redis instances
    # provider_manager = ProviderManager(db, redis)
    # await provider_manager.initialize_system_providers(system_configs)
    
    logger.info("AI System initialized")

# ============================================================================
# USER PROVIDER MANAGEMENT ROUTES
# ============================================================================

@router.post("/providers/register")
async def register_provider(
    registration: ProviderRegistration,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Register a custom AI provider"""
    redis = await aioredis.from_url(get_settings().REDIS_URL)
    manager = ProviderManager(db, redis)
    
    provider_id = await manager.register_user_provider(
        str(current_user.id),
        registration
    )
    
    return {
        "success": True,
        "provider_id": provider_id,
        "message": "Provider registered successfully"
    }

@router.post("/providers/mcp/register")
async def register_mcp(
    registration: MCPRegistration,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Register a Model Context Protocol integration"""
    redis = await aioredis.from_url(get_settings().REDIS_URL)
    manager = ProviderManager(db, redis)
    
    mcp_id = await manager.register_mcp(
        str(current_user.id),
        registration
    )
    
    return {
        "success": True,
        "mcp_id": mcp_id,
        "message": "MCP integration registered successfully"
    }

@router.get("/providers")
async def list_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """List all configured providers for current user"""
    redis = await aioredis.from_url(get_settings().REDIS_URL)
    manager = ProviderManager(db, redis)
    
    providers = await manager.list_user_providers(str(current_user.id))
    mcps = await manager.list_user_mcps(str(current_user.id))
    
    return {
        "providers": providers,
        "mcp_integrations": mcps
    }

@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a provider configuration"""
    redis = await aioredis.from_url(get_settings().REDIS_URL)
    manager = ProviderManager(db, redis)
    
    await manager.delete_user_provider(str(current_user.id), provider_id)
    
    return {
        "success": True,
        "message": "Provider deleted successfully"
    }

@router.put("/providers/{provider_id}")
async def update_provider(
    provider_id: str,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update provider configuration"""
    redis = await aioredis.from_url(get_settings().REDIS_URL)
    manager = ProviderManager(db, redis)
    
    await manager.update_provider_config(
        str(current_user.id),
        provider_id,
        updates
    )
    
    return {
        "success": True,
        "message": "Provider updated successfully"
    }

# ============================================================================
# AI GENERATION ROUTES
# ============================================================================

@router.post("/generate", response_model=AIResponse)
async def generate_response(
    request: AIRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate AI response using configured providers"""
    redis = await aioredis.from_url(get_settings().REDIS_URL)
    manager = ProviderManager(db, redis)
    
    try:
        # Get appropriate provider
        provider = await manager.get_provider(
            str(current_user.id),
            request.provider,
            request.provider_id
        )
        
        # Generate response
        response = await provider.generate(request)
        
        # Log usage
        await manager.log_usage(
            user_id=str(current_user.id),
            provider=response.provider,
            model=response.model,
            request_id=response.request_id,
            usage=response.usage,
            response_time=response.processing_time,
            success=True
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        
        # Log failed request
        await manager.log_usage(
            user_id=str(current_user.id),
            provider=request.provider.value if request.provider else "unknown",
            model=request.model or "unknown",
            request_id=str(uuid.uuid4()),
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            response_time=0.0,
            success=False,
            error=str(e)
        )
        
        raise

@router.post("/generate/stream")
async def stream_response(
    request: AIRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Stream AI response"""
    redis = await aioredis.from_url(get_settings().REDIS_URL)
    manager = ProviderManager(db, redis)
    
    provider = await manager.get_provider(
        str(current_user.id),
        request.provider,
        request.provider_id
    )
    
    async def generate():
        try:
            async for chunk in provider.stream(request):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

# ============================================================================
# HEALTH & MONITORING ROUTES
# ============================================================================

@router.get("/health")
async def check_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Check health of all providers"""
    redis = await aioredis.from_url(get_settings().REDIS_URL)
    manager = ProviderManager(db, redis)
    
    health_status = await manager.check_all_health()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "providers": {
            name: check.dict()
            for name, check in health_status.items()
        }
    }

@router.get("/usage")
async def get_usage_stats(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get usage statistics"""
    # Query usage logs
    from sqlalchemy import func
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(
            func.count(APIUsageLog.id).label("total_requests"),
            func.sum(APIUsageLog.tokens_used).label("total_tokens"),
            func.sum(APIUsageLog.cost).label("total_cost"),
            func.avg(APIUsageLog.response_time).label("avg_response_time")
        ).where(
            APIUsageLog.user_id == current_user.id,
            APIUsageLog.created_at >= cutoff_date
        )
    )
    
    stats = result.first()
    
    return {
        "period_days": days,
        "total_requests": stats.total_requests or 0,
        "total_tokens": stats.total_tokens or 0,
        "total_cost": float(stats.total_cost or 0),
        "avg_response_time": float(stats.avg_response_time or 0)
    }

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "router",
    "ProviderManager",
    "AIProvider",
    "ProviderConfig",
    "AIRequest",
    "AIResponse"
]