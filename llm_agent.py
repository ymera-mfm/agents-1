
"""
Advanced LLM Agent with RAG capabilities
Multi-provider LLM support, vector search, memory, and intelligent routing
"""

import asyncio
import json
import time
import uuid
import traceback
import os
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
# Optional dependencies - Token counting
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    tiktoken = None
    HAS_TIKTOKEN = False
import re

# Optional dependencies - OpenAI API
import re

# Optional dependencies
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    tiktoken = None
    HAS_TIKTOKEN = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    openai = None
    HAS_OPENAI = False
# Optional dependencies - Anthropic API

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    anthropic = None
    HAS_ANTHROPIC = False
# Optional dependencies - Vector database

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    HAS_QDRANT = True
except ImportError:
    QdrantClient = None
    Distance = None
    VectorParams = None
    PointStruct = None
    Filter = None
    FieldCondition = None
    MatchValue = None
    HAS_QDRANT = False
# Optional dependencies - Text embeddings

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    SentenceTransformer = None
    HAS_SENTENCE_TRANSFORMERS = False
# Optional dependencies - Numerical computing

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

from base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResponse, Priority, AgentStatus

try:
    from opentelemetry import trace
    HAS_OPENTELEMETRY = True
except ImportError:
    trace = None
    HAS_OPENTELEMETRY = False

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"

class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class ConversationMessage:
    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConversationMemory:
    conversation_id: str
    messages: List[ConversationMessage] = field(default_factory=list)
    summary: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RAGDocument:
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: float = field(default_factory=time.time)

@dataclass
class LLMConfig:
    provider: LLMProvider
    model: str
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    system_prompt: Optional[str] = None
    use_streaming: bool = False
    timeout: int = 30

class LLMAgent(BaseAgent):
    """
    Advanced LLM Agent with:
    - Multi-provider support (OpenAI, Anthropic, Local)
    - RAG (Retrieval Augmented Generation) capabilities
    - Conversation memory and context management
    - Intelligent model routing based on task complexity
    - Vector embeddings and semantic search
    - Streaming responses for real-time applications
    - Token optimization and cost tracking
    - Fine-tuning integration
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # LLM clients
        self.openai_client = None
        self.anthropic_client = None
        
        # Vector database
        self.qdrant_client = None
        self.embedding_model = None
        
        # Model configurations
        self.llm_configs = {
            "openai_gpt4": LLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4-turbo-preview",
                max_tokens=4096,
                system_prompt="You are a helpful AI assistant in the YMERA agent system."
            ),
            "openai_gpt35": LLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-3.5-turbo",
                max_tokens=4096,
                temperature=0.7
            ),
            "anthropic_claude": LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                temperature=0.7
            ),
            "openai_embedding": LLMConfig(
                provider=LLMProvider.OPENAI,
                model="text-embedding-ada-002",
                max_tokens=8191
            )
        }
        
        # Conversation memory
        self.conversations: Dict[str, ConversationMemory] = {}
        self.max_conversation_age = 3600 * 24  # 24 hours
        
        # RAG collections
        self.rag_collections = {
            "knowledge_base": "general_knowledge",
            "code_snippets": "code_examples", 
            "documentation": "system_docs"
        }
        
        # Performance tracking
        self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_cost": 0.0}
        self.model_usage_stats = {model: {"requests": 0, "tokens": 0, "errors": 0} for model in self.llm_configs}
        
        # Tokenizer for token counting
        self.tokenizer = None
        
        # Model router for intelligent task distribution
        self.model_router_rules = {
            "simple_qa": "openai_gpt35",
            "complex_reasoning": "openai_gpt4",
            "creative_writing": "anthropic_claude",
            "code_generation": "openai_gpt4",
            "data_analysis": "openai_gpt4",
            "chat_conversation": "openai_gpt35",
            "technical_documentation": "anthropic_claude",
            "summarization": "openai_gpt35"
        }
    
    async def start(self):
        """Initialize LLM agent services"""
        await self._initialize_clients()
        await self._setup_vector_database()
        await self._load_knowledge_base()
        
        # Subscribe to RAG document indexing
        await self._subscribe(
            "llm.index_document",
            self._handle_document_indexing
        )
        
        # Subscribe to conversation management
        await self._subscribe(
            "llm.conversation.*",
            self._handle_conversation_management
        )
        
        # Start background tasks
        asyncio.create_task(self._conversation_cleanup())
        
        self.logger.info("LLM Agent started",
                        providers=list({cfg.provider.value for cfg in self.llm_configs.values()}),
                        models=list(self.llm_configs.keys()))
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Implement the actual task logic for the LLM agent"""
        task_type = request.task_type
        payload = request.payload

        try:
            result: Dict[str, Any] = {}
            if task_type == "generate_text":
                result = await self._generate_text_task(payload)
            elif task_type == "chat_completion":
                result = await self._chat_completion_task(payload)
            elif task_type == "create_embedding":
                result = await self._create_embedding_task(payload)
            elif task_type == "semantic_search":
                result = await self._semantic_search_task(payload)
            elif task_type == "summarize_text":
                result = await self._summarize_text_task(payload)
            elif task_type == "llm.chat.generate_response": # Task from LiveChattingManager
                result = await self._handle_live_chat_response_request(payload)
            else:
                raise ValueError(f"Unknown LLM task type: {task_type}")
            
            return result

        except Exception as e:
            self.logger.error(f"Error executing LLM task {task_type}", error=str(e), traceback=traceback.format_exc())
            raise # Re-raise to be caught by BaseAgent's _handle_task_request

    async def _generate_text_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to generate text using an LLM"""
        prompt = payload["prompt"]
        model_key = payload.get("model_key", "openai_gpt35")
        max_tokens = payload.get("max_tokens", 500)
        temperature = payload.get("temperature", 0.7)
        system_prompt = payload.get("system_prompt")

        llm_config = self.llm_configs.get(model_key)
        if not llm_config:
            raise ValueError(f"LLM configuration for {model_key} not found.")

        messages = []
        if system_prompt or llm_config.system_prompt:
            messages.append({"role": "system", "content": system_prompt or llm_config.system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._call_llm_api(llm_config, messages, max_tokens, temperature)
        return {"content": response["choices"][0]["message"]["content"]}

    async def _chat_completion_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method for chat-based completion"""
        conversation_id = payload.get("conversation_id")
        user_message_content = payload["user_message"]
        model_key = payload.get("model_key", "openai_gpt35")
        max_tokens = payload.get("max_tokens", 500)
        temperature = payload.get("temperature", 0.7)
        system_prompt = payload.get("system_prompt")
        rag_query = payload.get("rag_query")
        rag_collections = payload.get("rag_collections", ["knowledge_base"])

        llm_config = self.llm_configs.get(model_key)
        if not llm_config:
            raise ValueError(f"LLM configuration for {model_key} not found.")

        conversation = self.conversations.get(conversation_id)
        if not conversation:
            conversation = ConversationMemory(conversation_id=conversation_id)
            self.conversations[conversation_id] = conversation
        
        conversation.messages.append(ConversationMessage(role=MessageRole.USER, content=user_message_content))
        conversation.updated_at = time.time()

        # Prepare messages for LLM, including RAG context if applicable
        llm_messages = []
        if system_prompt or llm_config.system_prompt:
            llm_messages.append({"role": "system", "content": system_prompt or llm_config.system_prompt})
        
        # Add RAG context
        if rag_query and self.qdrant_client and self.embedding_model:
            retrieved_docs = await self._perform_rag_search(rag_query, rag_collections)
            if retrieved_docs:
                rag_context = "\n\nRelevant Information:\n" + "\n---\n".join([doc.content for doc in retrieved_docs])
                llm_messages.append({"role": "system", "content": rag_context})

        # Add conversation history
        for msg in conversation.messages:
            llm_messages.append({"role": msg.role.value, "content": msg.content})

        response = await self._call_llm_api(llm_config, llm_messages, max_tokens, temperature)
        ai_content = response["choices"][0]["message"]["content"]
        
        conversation.messages.append(ConversationMessage(role=MessageRole.ASSISTANT, content=ai_content))
        conversation.updated_at = time.time()

        return {"content": ai_content, "conversation_id": conversation_id}

    async def _create_embedding_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to create embeddings for text"""
        text = payload["text"]
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized.")
        embedding = self.embedding_model.encode(text).tolist()
        return {"embedding": embedding}

    async def _semantic_search_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to perform semantic search"""
        query_text = payload["query_text"]
        collection_name = payload.get("collection_name", "general_knowledge")
        limit = payload.get("limit", 5)

        if not self.qdrant_client or not self.embedding_model:
            raise RuntimeError("Vector database or embedding model not initialized.")
        
        query_embedding = self.embedding_model.encode(query_text).tolist()
        
        search_result = self.qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit,
            with_payload=True
        )
        
        return {"results": [{
            "content": hit.payload["content"],
            "metadata": hit.payload["metadata"],
            "score": hit.score
        } for hit in search_result]}

    async def _summarize_text_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to summarize a given text"""
        text_to_summarize = payload["text"]
        model_key = payload.get("model_key", "summarization") # Use a model suitable for summarization
        max_tokens = payload.get("max_tokens", 200)
        temperature = payload.get("temperature", 0.3)

        llm_config = self.llm_configs.get(model_key)
        if not llm_config:
            raise ValueError(f"LLM configuration for {model_key} not found.")

        prompt = f"Please summarize the following text concisely:\n\n{text_to_summarize}\n\nSummary:"
        messages = []
        if llm_config.system_prompt:
            messages.append({"role": "system", "content": llm_config.system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._call_llm_api(llm_config, messages, max_tokens, temperature)
        return {"summary": response["choices"][0]["message"]["content"]}

    async def _handle_live_chat_response_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests from LiveChattingManager to generate an AI response."""
        session_id = payload["session_id"]
        user_message = payload["user_message"]
        conversation_history = payload.get("conversation_history", [])
        context = payload.get("context", {})

        # Reconstruct conversation for LLM
        llm_messages = []
        # Add system prompt if available
        default_llm_config = self.llm_configs.get("chat_conversation")
        if default_llm_config and default_llm_config.system_prompt:
            llm_messages.append({"role": "system", "content": default_llm_config.system_prompt})

        # Add historical messages
        for msg_data in conversation_history:
            # Ensure message_type is correctly mapped to role
            role = msg_data["message_type"].lower()
            if role == "user":
                llm_messages.append({"role": "user", "content": msg_data["content"]})
            elif role == "assistant":
                llm_messages.append({"role": "assistant", "content": msg_data["content"]})
            # Ignore other message types for LLM context

        # Add current user message
        llm_messages.append({"role": "user", "content": user_message["content"]})

        # Perform RAG if context suggests it or if a specific query is present
        rag_context_content = ""
        if context.get("rag_enabled", False) and user_message["content"]:
            retrieved_docs = await self._perform_rag_search(user_message["content"], context.get("rag_collections", ["knowledge_base"]))
            if retrieved_docs:
                rag_context_content = "\n\nRelevant Information:\n" + "\n---\n".join([doc.content for doc in retrieved_docs])
                llm_messages.insert(0, {"role": "system", "content": rag_context_content}) # Insert at the beginning as system context

        model_key = self._select_model("chat_conversation", "medium")
        llm_config = self.llm_configs.get(model_key)
        if not llm_config:
            raise ValueError(f"LLM configuration for {model_key} not found.")

        response = await self._call_llm_api(llm_config, llm_messages, llm_config.max_tokens, llm_config.temperature)
        ai_content = response["choices"][0]["message"]["content"]

        # Publish the AI response back to the communication agent (or directly to LiveChattingManager)
        # This assumes the LiveChattingManager is subscribed to 'chat.ai.response'
        await self._publish(
            "chat.ai.response",
            json.dumps({
                "session_id": session_id,
                "response": ai_content,
                "original_message_id": user_message["id"],
                "model_used": model_key
            }).encode()
        )
        self.logger.info(f"Generated AI response for session {session_id} using {model_key}.")
        return {"ai_response": ai_content, "model_used": model_key}

    async def _initialize_clients(self):
        """Initialize LLM provider clients"""
        
        # OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        
        # Anthropic client
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)

        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4") # Use a common tokenizer
        except Exception as e:
            self.logger.warning(f"Could not initialize tiktoken tokenizer: {e}")
            self.tokenizer = None

        self.logger.info("LLM clients initialized.")

    async def _setup_vector_database(self):
        """Initialize Qdrant client and embedding model"""
        qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        self.qdrant_client = QdrantClient(url=qdrant_url)
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.logger.info("SentenceTransformer embedding model loaded.")
        except Exception as e:
            self.logger.error(f"Failed to load SentenceTransformer: {e}. RAG features will be limited.")
            self.embedding_model = None

        # Ensure Qdrant collections exist
        for alias, collection_name in self.rag_collections.items():
            try:
                self.qdrant_client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE) # all-MiniLM-L6-v2 has 384 dimensions
                )
                self.logger.info(f"Qdrant collection \'{collection_name}\' ensured.")
            except Exception as e:
                self.logger.error(f"Failed to create Qdrant collection {collection_name}: {e}")

    async def _load_knowledge_base(self):
        """Load initial knowledge base documents into Qdrant"""
        # This is a placeholder. In a real system, this would load from files or a DB.
        documents = [
            RAGDocument(
                id="doc1",
                content="The YMERA platform is a multi-agent system designed for scalable and intelligent automation.",
                metadata={"source": "internal_docs", "category": "platform_overview"}
            ),
            RAGDocument(
                id="doc2",
                content="Agents communicate via NATS, an open-source messaging system, and use PostgreSQL for persistence.",
                metadata={"source": "internal_docs", "category": "architecture"}
            ),
            RAGDocument(
                id="doc3",
                content="The LLM Agent supports OpenAI and Anthropic models, and integrates with Qdrant for RAG.",
                metadata={"source": "llm_agent_docs", "category": "agent_details"}
            )
        ]
        
        for doc in documents:
            await self._index_document(doc, "general_knowledge")
        self.logger.info(f"Loaded {len(documents)} initial knowledge base documents.")

    async def _handle_document_indexing(self, msg):
        """Handle requests to index a new document for RAG"""
        try:
            data = json.loads(msg.data.decode())
            doc_id = data.get("id", str(uuid.uuid4()))
            content = data["content"]
            metadata = data.get("metadata", {})
            collection_name = data.get("collection_name", "general_knowledge")

            doc = RAGDocument(id=doc_id, content=content, metadata=metadata)
            await self._index_document(doc, collection_name)
            self.logger.info(f"Document {doc_id} indexed into {collection_name}.")
        except Exception as e:
            self.logger.error(f"Error indexing document: {e}", traceback=traceback.format_exc())

    async def _index_document(self, doc: RAGDocument, collection_name: str):
        """Create embedding and index document in Qdrant"""
        if not self.qdrant_client or not self.embedding_model:
            self.logger.warning("Cannot index document: Qdrant or embedding model not available.")
            return
        
        try:
            embedding = self.embedding_model.encode(doc.content).tolist()
            
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=doc.id,
                        vector=embedding,
                        payload={
                            "id": doc.id,
                            "content": doc.content,
                            "metadata": doc.metadata,
                            "indexed_at": time.time()
                        }
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"Failed to index document {doc.id} into {collection_name}: {e}", traceback=traceback.format_exc())

    async def _handle_conversation_management(self, msg):
        """Handle conversation management operations"""
        try:
            subject_parts = msg.subject.split(".")
            operation = subject_parts[-1] if len(subject_parts) > 2 else "unknown"
            
            data = json.loads(msg.data.decode())
            conversation_id = data.get("conversation_id")
            
            if not conversation_id:
                self.logger.error("Conversation management request missing conversation_id")
                return

            if operation == "get":
                # Get conversation history
                conversation = self.conversations.get(conversation_id)
                if conversation:
                    response_data = {
                        "conversation_id": conversation_id,
                        "messages": [
                            {
                                "role": msg.role.value,
                                "content": msg.content,
                                "timestamp": msg.timestamp,
                                "metadata": msg.metadata
                            }
                            for msg in conversation.messages
                        ],
                        "summary": conversation.summary,
                        "created_at": conversation.created_at,
                        "updated_at": conversation.updated_at
                    }
                else:
                    response_data = {"error": "Conversation not found"}
                
                await self._publish(msg.reply, json.dumps(response_data).encode())
            
            elif operation == "clear":
                # Clear conversation history
                if conversation_id in self.conversations:
                    del self.conversations[conversation_id]
                    self.logger.info("Conversation cleared", conversation_id=conversation_id)
                    await self._publish(msg.reply, json.dumps({"conversation_id": conversation_id, "status": "success"}).encode())
                else:
                    await self._publish(msg.reply, json.dumps({"conversation_id": conversation_id, "status": "not_found"}).encode())
            
            elif operation == "summarize":
                # Summarize conversation
                conversation = self.conversations.get(conversation_id)
                if conversation:
                    await self._summarize_conversation(conversation)
                    
                    await self._publish(msg.reply, json.dumps({
                        "conversation_id": conversation_id,
                        "summary": conversation.summary
                    }).encode())
                else:
                    self.logger.warning("Attempted to summarize non-existent conversation", conversation_id=conversation_id)
                    await self._publish(msg.reply, json.dumps({"error": "Conversation not found"}).encode())
            
            else:
                self.logger.warning("Unknown conversation management operation", operation=operation, conversation_id=conversation_id)
            
        except Exception as e:
            self.logger.error("Conversation management failed", error=str(e), traceback=traceback.format_exc())
    
    async def _summarize_conversation(self, conversation: ConversationMemory):
        """Summarize a conversation to compress memory"""
        if len(conversation.messages) < 5:
            return  # Too short to summarize
        
        # Take older messages (excluding recent ones) for summarization
        messages_to_summarize = conversation.messages[:-5]
        
        # Create summarization prompt
        conversation_text = "\n".join([
            f"{msg.role.value}: {msg.content}"
            for msg in messages_to_summarize
        ])
        
        prompt = f"""Please summarize the following conversation concisely, capturing the key topics, decisions, and context:

{conversation_text}

Summary:"""
        
        try:
            model_key = self._select_model("summarization", "medium") # Use auto-selection for summarization
            response = await self._generate_text_task(
                payload={
                    "prompt": prompt,
                    "model_key": model_key,
                    "max_tokens": 200,
                    "temperature": 0.3
                }
            )
            
            conversation.summary = response["content"]
            conversation.messages = conversation.messages[-5:]  # Keep only recent messages
            conversation.updated_at = time.time()
            
            self.logger.info("Conversation summarized", 
                           conversation_id=conversation.conversation_id,
                           original_messages=len(messages_to_summarize))
            
        except Exception as e:
            self.logger.error("Conversation summarization failed", error=str(e), traceback=traceback.format_exc())
    
    async def _store_conversation(self, conversation_id: str, messages: List[ConversationMessage]):
        """Store conversation in memory and potentially persist to DB"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationMemory(conversation_id=conversation_id)
        
        self.conversations[conversation_id].messages.extend(messages)
        self.conversations[conversation_id].updated_at = time.time()
        
        # TODO: Persist to database if self.db_pool is available

    async def _perform_rag_search(self, query_text: str, collections: List[str], limit: int = 3) -> List[RAGDocument]:
        """Perform RAG search across specified collections"""
        if not self.qdrant_client or not self.embedding_model:
            self.logger.warning("RAG search skipped: Qdrant or embedding model not available.")
            return []
        
        try:
            query_embedding = self.embedding_model.encode(query_text).tolist()
            
            all_results = []
            for collection_alias in collections:
                collection_name = self.rag_collections.get(collection_alias, collection_alias)
                search_result = self.qdrant_client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    limit=limit,
                    with_payload=True
                )
                all_results.extend(search_result)
            
            # Sort by score and take top N unique documents
            all_results.sort(key=lambda x: x.score, reverse=True)
            
            unique_docs = {}
            for hit in all_results:
                doc_id = hit.payload.get("id", str(uuid.uuid4())) # Use ID from payload if available
                if doc_id not in unique_docs:
                    unique_docs[doc_id] = RAGDocument(
                        id=doc_id,
                        content=hit.payload["content"],
                        metadata=hit.payload["metadata"],
                        embedding=hit.vector,
                        created_at=hit.payload.get("indexed_at", time.time())
                    )
            
            return list(unique_docs.values())[:limit]
        
        except Exception as e:
            self.logger.error(f"RAG search failed: {e}", traceback=traceback.format_exc())
            return []

    async def _call_llm_api(self, llm_config: LLMConfig, messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Generic method to call LLM APIs based on configuration"""
        start_time = time.time()
        response = None
        try:
            if llm_config.provider == LLMProvider.OPENAI:
                if not self.openai_client:
                    raise RuntimeError("OpenAI client not initialized.")
                response = await self.openai_client.chat.completions.create(
                    model=llm_config.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=llm_config.top_p,
                    frequency_penalty=llm_config.frequency_penalty,
                    presence_penalty=llm_config.presence_penalty,
                    stream=llm_config.use_streaming,
                    timeout=llm_config.timeout
                )
            elif llm_config.provider == LLMProvider.ANTHROPIC:
                if not self.anthropic_client:
                    raise RuntimeError("Anthropic client not initialized.")
                # Anthropic API expects system message separately
                system_message = next((m["content"] for m in messages if m["role"] == "system"), None)
                user_messages = [m for m in messages if m["role"] != "system"]
                
                response = await self.anthropic_client.messages.create(
                    model=llm_config.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=user_messages,
                    system=system_message,
                    stream=llm_config.use_streaming,
                    timeout=llm_config.timeout
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {llm_config.provider.value}")
            
            # Update metrics
            self.model_usage_stats[llm_config.model]["requests"] += 1
            if hasattr(response, "usage") and response.usage:
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                self.token_usage["prompt_tokens"] += prompt_tokens
                self.token_usage["completion_tokens"] += completion_tokens
                self.model_usage_stats[llm_config.model]["tokens"] += (prompt_tokens + completion_tokens)
                # TODO: Calculate cost based on model and token usage

            return asdict(response) # Convert Pydantic model to dict

        except Exception as e:
            self.logger.error(f"LLM API call failed for {llm_config.model}: {e}", traceback=traceback.format_exc())
            self.model_usage_stats[llm_config.model]["errors"] += 1
            raise
        finally:
            self.logger.debug(f"LLM call to {llm_config.model} took {time.time() - start_time:.2f}s")

    def _select_model(self, task_complexity: str, urgency: str) -> str:
        """Intelligently select an LLM model based on task complexity and urgency"""
        # This is a simplified routing logic. Can be expanded with more sophisticated rules.
        # For example, use cheaper models for low urgency/simple tasks, more powerful for complex.
        
        if task_complexity in self.model_router_rules:
            return self.model_router_rules[task_complexity]
        
        # Fallback logic
        if urgency == "high":
            return "openai_gpt4" # Use a powerful model for urgent tasks
        elif task_complexity == "complex":
            return "openai_gpt4"
        elif task_complexity == "medium":
            return "openai_gpt35"
        else:
            return "openai_gpt35" # Default to a general-purpose model

    async def _conversation_cleanup(self):
        """Background task to clean up old conversations from memory"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                conversations_to_remove = []
                for conv_id, conv in self.conversations.items():
                    if current_time - conv.updated_at > self.max_conversation_age:
                        conversations_to_remove.append(conv_id)
                
                for conv_id in conversations_to_remove:
                    del self.conversations[conv_id]
                    self.logger.info("Cleaned up old conversation", conversation_id=conv_id)
                
                await asyncio.sleep(3600) # Check every hour
            except Exception as e:
                self.logger.error(f"Conversation cleanup failed: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(300)

    def _get_agent_metrics(self) -> Dict[str, Any]:
        """Provide LLM agent specific metrics."""
        base_metrics = super()._get_agent_metrics()
        base_metrics.update({
            "token_usage": self.token_usage,
            "model_usage_stats": self.model_usage_stats,
            "active_conversations": len(self.conversations),
            "qdrant_collections": {alias: name for alias, name in self.rag_collections.items()}
        })
        return base_metrics


if __name__ == "__main__":
    
    config = AgentConfig(
        name="llm_agent",
        agent_type="llm",
        capabilities=["text_generation", "chat_completion", "embeddings", "semantic_search", "summarization", "llm.chat.generate_response"],
        nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://agent:secure_password@postgres:5432/ymera"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
        consul_url=os.getenv("CONSUL_URL", "http://consul:8500")
    )
    
    agent = LLMAgent(config)
    asyncio.run(agent.run())

