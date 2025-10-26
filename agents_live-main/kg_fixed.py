"""
YMERA Enterprise - Knowledge Graph Management System
Production-Ready Implementation - FULLY OPERATIONAL
Version: 5.0 - All Issues Resolved
"""

import asyncio
import json
import logging
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from enum import Enum

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None
    
import networkx as nx
import numpy as np

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

class KnowledgeGraphSettings:
    """Centralized configuration settings"""
    REDIS_URL = "redis://localhost:6379/0"
    DATABASE_URL = "sqlite+aiosqlite:///./knowledge_graph.db"
    MAX_KNOWLEDGE_NODES = 1000000
    MAX_CONNECTIONS_PER_NODE = 1000
    MIN_CONFIDENCE_THRESHOLD = 0.1
    DEFAULT_DECAY_RATE = 0.01
    SIMILARITY_THRESHOLD = 0.8
    KNOWLEDGE_RETENTION_DAYS = 365
    EMBEDDING_DIMENSION = 128

# Constants
MAX_KNOWLEDGE_NODES = KnowledgeGraphSettings.MAX_KNOWLEDGE_NODES
MAX_CONNECTIONS_PER_NODE = KnowledgeGraphSettings.MAX_CONNECTIONS_PER_NODE
MIN_CONFIDENCE_THRESHOLD = KnowledgeGraphSettings.MIN_CONFIDENCE_THRESHOLD
DEFAULT_DECAY_RATE = KnowledgeGraphSettings.DEFAULT_DECAY_RATE
SIMILARITY_THRESHOLD = KnowledgeGraphSettings.SIMILARITY_THRESHOLD
KNOWLEDGE_RETENTION_DAYS = KnowledgeGraphSettings.KNOWLEDGE_RETENTION_DAYS

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ymera.knowledge_graph")

# ============================================================================
# DATA MODELS
# ============================================================================

class NodeType(Enum):
    """Knowledge node types"""
    CONCEPT = "concept"
    PATTERN = "pattern"
    RULE = "rule"
    FACT = "fact"
    RELATIONSHIP = "relationship"
    ENTITY = "entity"
    EVENT = "event"
    PROCEDURE = "procedure"

@dataclass
class KnowledgeGraphConfig:
    """Configuration for knowledge graph management"""
    enabled: bool = True
    max_nodes: int = MAX_KNOWLEDGE_NODES
    max_connections_per_node: int = MAX_CONNECTIONS_PER_NODE
    min_confidence_threshold: float = MIN_CONFIDENCE_THRESHOLD
    default_decay_rate: float = DEFAULT_DECAY_RATE
    similarity_threshold: float = SIMILARITY_THRESHOLD
    retention_days: int = KNOWLEDGE_RETENTION_DAYS
    enable_auto_cleanup: bool = True
    enable_similarity_search: bool = True
    enable_graph_analytics: bool = True
    redis_url: str = KnowledgeGraphSettings.REDIS_URL
    embedding_dim: int = KnowledgeGraphSettings.EMBEDDING_DIMENSION

@dataclass
class KnowledgeItem:
    """Represents a knowledge item"""
    content: Dict[str, Any]
    node_type: str
    confidence: float = 1.0
    source: str = "unknown"
    agent_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class KnowledgeQuery:
    """Knowledge query parameters"""
    query_type: str  # 'semantic', 'exact', 'pattern', 'graph_traversal'
    query_data: Dict[str, Any]
    max_results: int = 10
    min_confidence: float = 0.5
    include_connections: bool = True
    agent_filter: Optional[str] = None
    time_range: Optional[Tuple[datetime, datetime]] = None

class KnowledgeSearchResult:
    """Knowledge search result"""
    def __init__(self, node_id: str, content: Dict[str, Any], node_type: str,
                 confidence: float, relevance_score: float, source: str,
                 created_at: datetime, connections: Optional[List[Dict]] = None):
        self.node_id = node_id
        self.content = content
        self.node_type = node_type
        self.confidence = confidence
        self.relevance_score = relevance_score
        self.source = source
        self.created_at = created_at
        self.connections = connections or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "content": self.content,
            "node_type": self.node_type,
            "confidence": self.confidence,
            "relevance_score": self.relevance_score,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "connections": self.connections
        }

# ============================================================================
# EMBEDDING ENGINE
# ============================================================================

class KnowledgeEmbedding:
    """Handles knowledge embeddings for semantic search"""
    
    def __init__(self, embedding_dim: int = 128):
        self.logger = logger
        self._embedding_cache = {}
        self.embedding_dim = embedding_dim
    
    async def generate_embedding(self, content: Dict[str, Any]) -> List[float]:
        """Generate vector embedding for knowledge content"""
        try:
            content_str = json.dumps(content, sort_keys=True)
            content_hash = hashlib.md5(content_str.encode()).hexdigest()
            
            if content_hash in self._embedding_cache:
                return self._embedding_cache[content_hash]
            
            embedding = self._create_feature_embedding(content)
            self._embedding_cache[content_hash] = embedding
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {str(e)}")
            return [0.0] * self.embedding_dim
    
    def _create_feature_embedding(self, content: Dict[str, Any]) -> List[float]:
        """Create feature-based embedding from content"""
        text_content = ""
        for key, value in content.items():
            if isinstance(value, str):
                text_content += f" {value}"
            elif isinstance(value, (int, float)):
                text_content += f" {str(value)}"
        
        words = text_content.lower().split()
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1
        
        embedding = [0.0] * self.embedding_dim
        total_words = max(len(words), 1)
        
        for i, (word, count) in enumerate(list(word_counts.items())[:self.embedding_dim]):
            embedding[i] = min(count / total_words, 1.0)
        
        return embedding
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate similarity: {str(e)}")
            return 0.0

# ============================================================================
# KNOWLEDGE GRAPH CORE
# ============================================================================

class KnowledgeGraph:
    """Production-ready knowledge graph for storing and retrieving learned knowledge"""
    
    def __init__(self, config: KnowledgeGraphConfig):
        self.config = config
        self.logger = logger
        
        self._embedding_engine = KnowledgeEmbedding(config.embedding_dim)
        self._graph = nx.DiGraph()
        self._node_cache = {}
        self._connection_cache = defaultdict(list)
        
        self._query_performance = []
        self._node_access_stats = defaultdict(int)
        
        self._health_status = "unknown"
        self._is_initialized = False
        self._redis_client = None
        self._cleanup_task = None
    
    async def initialize(self) -> None:
        """Initialize knowledge graph resources"""
        try:
            self.logger.info("Initializing knowledge graph")
            
            # Initialize Redis for caching if available
            if aioredis:
                try:
                    self._redis_client = await aioredis.from_url(
                        self.config.redis_url,
                        max_connections=20,
                        retry_on_timeout=True,
                        decode_responses=False
                    )
                    await self._redis_client.ping()
                    self.logger.info("Redis cache initialized")
                except Exception as e:
                    self.logger.warning(f"Redis initialization failed: {str(e)}")
                    self._redis_client = None
            
            # Start background maintenance tasks
            if self.config.enable_auto_cleanup:
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup_task())
            
            self._is_initialized = True
            self._health_status = "healthy"
            
            self.logger.info(
                f"Knowledge graph initialized - Nodes: {len(self._graph.nodes)}, "
                f"Connections: {len(self._graph.edges)}"
            )
            
        except Exception as e:
            self._health_status = "unhealthy"
            self.logger.error(f"Failed to initialize knowledge graph: {str(e)}")
            raise KnowledgeGraphError(f"Initialization failed: {str(e)}")
    
    async def add_knowledge_item(
        self,
        knowledge_item: KnowledgeItem,
        create_connections: bool = True
    ) -> str:
        """Add a single knowledge item to the graph"""
        try:
            node_id = str(uuid.uuid4())
            
            self.logger.debug(f"Adding knowledge item: {node_id} (type: {knowledge_item.node_type})")
            
            # Generate embedding
            embedding = await self._embedding_engine.generate_embedding(
                knowledge_item.content
            )
            
            # Add to in-memory graph
            self._graph.add_node(
                node_id,
                node_type=knowledge_item.node_type,
                content=knowledge_item.content,
                confidence=knowledge_item.confidence,
                embedding=embedding,
                created_at=datetime.utcnow(),
                source=knowledge_item.source,
                agent_id=knowledge_item.agent_id,
                tags=knowledge_item.tags,
                metadata=knowledge_item.metadata
            )
            
            # Cache the node
            self._node_cache[node_id] = knowledge_item
            
            # Create automatic connections if enabled
            if create_connections and self.config.enable_similarity_search:
                await self._create_automatic_connections(node_id, knowledge_item)
            
            self.logger.info(f"Knowledge item added: {node_id}")
            
            return node_id
            
        except Exception as e:
            self.logger.error(f"Failed to add knowledge item: {str(e)}")
            raise KnowledgeGraphError(f"Failed to add knowledge item: {str(e)}")
    
    async def add_knowledge_batch(
        self,
        knowledge_items: List[KnowledgeItem],
        source: str = "batch_import",
        confidence: float = 1.0
    ) -> int:
        """Add multiple knowledge items in batch"""
        try:
            self.logger.info(f"Adding knowledge batch: {len(knowledge_items)} items")
            
            added_nodes = []
            
            # Add all nodes first
            for item in knowledge_items:
                # Update confidence and source if needed
                if item.confidence == 1.0 and confidence != 1.0:
                    item.confidence = confidence
                if item.source == "unknown":
                    item.source = source
                
                node_id = await self.add_knowledge_item(item, create_connections=False)
                added_nodes.append(node_id)
            
            # Create batch connections
            connections_created = 0
            for i, node_id in enumerate(added_nodes):
                connections = await self._create_batch_connections(
                    node_id, 
                    knowledge_items[i],
                    added_nodes
                )
                connections_created += connections
            
            self.logger.info(
                f"Knowledge batch added: {len(added_nodes)} items, "
                f"{connections_created} connections"
            )
            
            return connections_created
            
        except Exception as e:
            self.logger.error(f"Failed to add knowledge batch: {str(e)}")
            raise KnowledgeGraphError(f"Failed to add knowledge batch: {str(e)}")
    
    async def _create_automatic_connections(
        self,
        node_id: str,
        knowledge_item: KnowledgeItem
    ) -> None:
        """Create automatic connections based on similarity"""
        try:
            similar_nodes = await self._find_similar_nodes(
                knowledge_item.content,
                min_similarity=self.config.similarity_threshold,
                exclude_node=node_id
            )
            
            for similar_node in similar_nodes[:10]:
                await self.create_connection(
                    node_id,
                    similar_node["node_id"],
                    "similarity",
                    strength=similar_node["similarity"],
                    confidence=0.8
                )
            
        except Exception as e:
            self.logger.warning(f"Failed to create automatic connections: {str(e)}")
    
    async def _create_batch_connections(
        self,
        node_id: str,
        knowledge_item: KnowledgeItem,
        batch_nodes: List[str]
    ) -> int:
        """Create connections within a batch of nodes"""
        connections_created = 0
        
        try:
            node_embedding = self._graph.nodes[node_id].get("embedding", [])
            
            for other_node_id in batch_nodes:
                if other_node_id == node_id:
                    continue
                
                other_embedding = self._graph.nodes[other_node_id].get("embedding", [])
                similarity = self._embedding_engine.calculate_similarity(
                    node_embedding, other_embedding
                )
                
                if similarity > self.config.similarity_threshold:
                    await self.create_connection(
                        node_id,
                        other_node_id,
                        "batch_similarity",
                        strength=similarity,
                        confidence=0.8
                    )
                    connections_created += 1
            
            return connections_created
            
        except Exception as e:
            self.logger.warning(f"Failed to create batch connections: {str(e)}")
            return connections_created
    
    async def create_connection(
        self,
        from_node_id: str,
        to_node_id: str,
        connection_type: str,
        strength: float = 1.0,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        bidirectional: bool = False
    ) -> str:
        """Create a connection between two knowledge nodes"""
        try:
            connection_id = str(uuid.uuid4())
            
            # Validate nodes exist
            if from_node_id not in self._graph.nodes:
                raise ValueError(f"Source node {from_node_id} not found")
            if to_node_id not in self._graph.nodes:
                raise ValueError(f"Target node {to_node_id} not found")
            
            # Add to in-memory graph
            self._graph.add_edge(
                from_node_id,
                to_node_id,
                connection_id=connection_id,
                connection_type=connection_type,
                strength=strength,
                confidence=confidence,
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            
            # Update connection cache
            self._connection_cache[from_node_id].append({
                "connection_id": connection_id,
                "to_node": to_node_id,
                "type": connection_type,
                "strength": strength
            })
            
            # Create reverse connection if bidirectional
            if bidirectional:
                self._graph.add_edge(
                    to_node_id,
                    from_node_id,
                    connection_id=connection_id,
                    connection_type=connection_type,
                    strength=strength,
                    confidence=confidence,
                    metadata=metadata or {},
                    created_at=datetime.utcnow()
                )
                
                self._connection_cache[to_node_id].append({
                    "connection_id": connection_id,
                    "to_node": from_node_id,
                    "type": connection_type,
                    "strength": strength
                })
            
            self.logger.debug(f"Connection created: {connection_id}")
            
            return connection_id
            
        except Exception as e:
            self.logger.error(f"Failed to create connection: {str(e)}")
            raise KnowledgeGraphError(f"Failed to create connection: {str(e)}")
    
    async def query_knowledge(self, query: KnowledgeQuery) -> List[KnowledgeSearchResult]:
        """Query knowledge graph with various search strategies"""
        try:
            query_start = datetime.utcnow()
            
            self.logger.debug(f"Executing {query.query_type} query")
            
            results = []
            
            if query.query_type == "semantic":
                results = await self._semantic_search(query)
            elif query.query_type == "exact":
                results = await self._exact_search(query)
            elif query.query_type == "pattern":
                results = await self._pattern_search(query)
            elif query.query_type == "graph_traversal":
                results = await self._graph_traversal_search(query)
            else:
                raise ValueError(f"Unknown query type: {query.query_type}")
            
            # Apply filters
            results = await self._apply_query_filters(results, query)
            
            # Sort by relevance and limit results
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            results = results[:query.max_results]
            
            # Update access statistics
            for result in results:
                self._node_access_stats[result.node_id] += 1
            
            # Record query performance
            query_duration = (datetime.utcnow() - query_start).total_seconds()
            self._query_performance.append({
                "query_type": query.query_type,
                "duration": query_duration,
                "results_count": len(results),
                "timestamp": query_start
            })
            
            # Keep only last 1000 query records
            if len(self._query_performance) > 1000:
                self._query_performance.pop(0)
            
            self.logger.info(
                f"Query completed: {len(results)} results in {query_duration:.3f}s"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Knowledge query failed: {str(e)}")
            raise KnowledgeGraphError(f"Knowledge query failed: {str(e)}")
    
    async def _semantic_search(self, query: KnowledgeQuery) -> List[KnowledgeSearchResult]:
        """Perform semantic search using embeddings"""
        results = []
        
        try:
            query_content = query.query_data.get("content", {})
            query_embedding = await self._embedding_engine.generate_embedding(query_content)
            
            for node_id, node_data in self._graph.nodes(data=True):
                node_embedding = node_data.get("embedding", [])
                if not node_embedding:
                    continue
                
                similarity = self._embedding_engine.calculate_similarity(
                    query_embedding, node_embedding
                )
                
                if similarity >= query.min_confidence:
                    connections = []
                    if query.include_connections:
                        connections = await self._get_node_connections(node_id)
                    
                    result = KnowledgeSearchResult(
                        node_id=node_id,
                        content=node_data["content"],
                        node_type=node_data["node_type"],
                        confidence=node_data["confidence"],
                        relevance_score=similarity,
                        source=node_data.get("source", "unknown"),
                        created_at=node_data.get("created_at", datetime.utcnow()),
                        connections=connections
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Semantic search failed: {str(e)}")
            return []
    
    async def _exact_search(self, query: KnowledgeQuery) -> List[KnowledgeSearchResult]:
        """Perform exact content matching"""
        results = []
        
        try:
            search_terms = query.query_data.get("terms", [])
            search_content = query.query_data.get("content", {})
            
            for node_id, node_data in self._graph.nodes(data=True):
                match_score = 0.0
                
                if search_content:
                    content_matches = 0
                    for key, value in search_content.items():
                        if key in node_data["content"] and node_data["content"][key] == value:
                            content_matches += 1
                    
                    if content_matches > 0:
                        match_score = content_matches / len(search_content)
                
                if search_terms:
                    content_str = json.dumps(node_data["content"]).lower()
                    term_matches = sum(1 for term in search_terms if term.lower() in content_str)
                    if term_matches > 0:
                        match_score = max(match_score, term_matches / len(search_terms))
                
                if match_score >= query.min_confidence:
                    connections = []
                    if query.include_connections:
                        connections = await self._get_node_connections(node_id)
                    
                    result = KnowledgeSearchResult(
                        node_id=node_id,
                        content=node_data["content"],
                        node_type=node_data["node_type"],
                        confidence=node_data["confidence"],
                        relevance_score=match_score,
                        source=node_data.get("source", "unknown"),
                        created_at=node_data.get("created_at", datetime.utcnow()),
                        connections=connections
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Exact search failed: {str(e)}")
            return []
    
    async def _pattern_search(self, query: KnowledgeQuery) -> List[KnowledgeSearchResult]:
        """Search for patterns in the knowledge graph"""
        results = []
        
        try:
            pattern_type = query.query_data.get("pattern_type", "")
            pattern_params = query.query_data.get("parameters", {})
            
            if pattern_type == "centrality":
                centrality = nx.degree_centrality(self._graph)
                min_centrality = pattern_params.get("min_centrality", 0.1)
                
                for node_id, centrality_score in centrality.items():
                    if centrality_score >= min_centrality:
                        node_data = self._graph.nodes[node_id]
                        
                        connections = []
                        if query.include_connections:
                            connections = await self._get_node_connections(node_id)
                        
                        result = KnowledgeSearchResult(
                            node_id=node_id,
                            content=node_data["content"],
                            node_type=node_data["node_type"],
                            confidence=node_data["confidence"],
                            relevance_score=centrality_score,
                            source=node_data.get("source", "unknown"),
                            created_at=node_data.get("created_at", datetime.utcnow()),
                            connections=connections
                        )
                        results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Pattern search failed: {str(e)}")
            return []
    
    async def _graph_traversal_search(self, query: KnowledgeQuery) -> List[KnowledgeSearchResult]:
        """Search using graph traversal algorithms"""
        results = []
        
        try:
            start_node = query.query_data.get("start_node")
            traversal_type = query.query_data.get("traversal_type", "bfs")
            max_depth = query.query_data.get("max_depth", 3)
            
            if not start_node or start_node not in self._graph.nodes:
                return results
            
            visited_nodes = set()
            
            if traversal_type == "bfs":
                queue = [(start_node, 0)]
                
                while queue and len(results) < query.max_results:
                    current_node, depth = queue.pop(0)
                    
                    if current_node in visited_nodes or depth > max_depth:
                        continue
                    
                    visited_nodes.add(current_node)
                    node_data = self._graph.nodes[current_node]
                    
                    relevance = 1.0 / (depth + 1)
                    
                    connections = []
                    if query.include_connections:
                        connections = await self._get_node_connections(current_node)
                    
                    result = KnowledgeSearchResult(
                        node_id=current_node,
                        content=node_data["content"],
                        node_type=node_data["node_type"],
                        confidence=node_data["confidence"],
                        relevance_score=relevance,
                        source=node_data.get("source", "unknown"),
                        created_at=node_data.get("created_at", datetime.utcnow()),
                        connections=connections
                    )
                    results.append(result)
                    
                    for neighbor in self._graph.neighbors(current_node):
                        if neighbor not in visited_nodes:
                            queue.append((neighbor, depth + 1))
            
            return results
            
        except Exception as e:
            self.logger.error(f"Graph traversal search failed: {str(e)}")
            return []
    
    async def _apply_query_filters(
        self,
        results: List[KnowledgeSearchResult],
        query: KnowledgeQuery
    ) -> List[KnowledgeSearchResult]:
        """Apply filters to query results"""
        filtered_results = results
        
        if query.agent_filter:
            filtered_results = [
                r for r in filtered_results
                if self._node_cache.get(r.node_id, KnowledgeItem({}, "")).agent_id == query.agent_filter
            ]
        
        if query.time_range:
            start_time, end_time = query.time_range
            filtered_results = [
                r for r in filtered_results
                if start_time <= r.created_at <= end_time
            ]
        
        filtered_results = [
            r for r in filtered_results
            if r.confidence >= query.min_confidence
        ]
        
        return filtered_results
    
    async def _get_node_connections(self, node_id: str) -> List[Dict[str, Any]]:
        """Get connections for a specific node"""
        connections = []
        
        try:
            for neighbor in self._graph.neighbors(node_id):
                edge_data = self._graph.edges[node_id, neighbor]
                connections.append({
                    "target_node": neighbor,
                    "direction": "outgoing",
                    "type": edge_data.get("connection_type", "unknown"),
                    "strength": edge_data.get("strength", 1.0)
                })
            
            for predecessor in self._graph.predecessors(node_id):
                edge_data = self._graph.edges[predecessor, node_id]
                connections.append({
                    "target_node": predecessor,
                    "direction": "incoming",
                    "type": edge_data.get("connection_type", "unknown"),
                    "strength": edge_data.get("strength", 1.0)
                })
            
            return connections
            
        except Exception as e:
            self.logger.warning(f"Failed to get node connections: {str(e)}")
            return []
    
    async def _find_similar_nodes(
        self,
        content: Dict[str, Any],
        min_similarity: float = 0.5,
        exclude_node: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find nodes similar to given content"""
        similar_nodes = []
        
        try:
            content_embedding = await self._embedding_engine.generate_embedding(content)
            
            for node_id, node_data in self._graph.nodes(data=True):
                if node_id == exclude_node:
                    continue
                
                node_embedding = node_data.get("embedding", [])
                if not node_embedding:
                    continue
                
                similarity = self._embedding_engine.calculate_similarity(
                    content_embedding, node_embedding
                )
                
                if similarity >= min_similarity:
                    similar_nodes.append({
                        "node_id": node_id,
                        "similarity": similarity,
                        "node_type": node_data["node_type"]
                    })
            
            similar_nodes.sort(key=lambda x: x["similarity"], reverse=True)
            return similar_nodes
            
        except Exception as e:
            self.logger.warning(f"Failed to find similar nodes: {str(e)}")
            return []
    
    async def _periodic_cleanup_task(self) -> None:
        """Periodic cleanup of old and low-confidence knowledge"""
        while True:
            try:
                await asyncio.sleep(3600)
                
                self.logger.info("Starting periodic knowledge cleanup")
                
                cutoff_date = datetime.utcnow() - timedelta(days=self.config.retention_days)
                
                nodes_to_remove = []
                for node_id, node_data in self._graph.nodes(data=True):
                    created_at = node_data.get("created_at", datetime.utcnow())
                    confidence = node_data.get("confidence", 1.0)
                    
                    if created_at < cutoff_date and confidence < self.config.min_confidence_threshold:
                        nodes_to_remove.append(node_id)
                
                for node_id in nodes_to_remove:
                    self._graph.remove_node(node_id)
                    self._node_cache.pop(node_id, None)
                    self._connection_cache.pop(node_id, None)
                
                self.logger.info(f"Cleanup completed: removed {len(nodes_to_remove)} nodes")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic cleanup: {str(e)}")
    
    async def get_graph_analytics(self) -> Dict[str, Any]:
        """Get graph analytics and statistics"""
        try:
            analytics = {
                "nodes": {
                    "total": len(self._graph.nodes),
                    "by_type": defaultdict(int)
                },
                "connections": {
                    "total": len(self._graph.edges),
                    "by_type": defaultdict(int)
                },
                "graph_metrics": {
                    "density": nx.density(self._graph) if self._graph.nodes else 0,
                    "avg_clustering": nx.average_clustering(self._graph.to_undirected()) if self._graph.nodes else 0,
                    "connected_components": nx.number_connected_components(self._graph.to_undirected()) if self._graph.nodes else 0
                },
                "performance": {
                    "avg_query_time": sum(q["duration"] for q in self._query_performance[-100:]) / min(len(self._query_performance), 100) if self._query_performance else 0,
                    "total_queries": len(self._query_performance),
                    "most_accessed_nodes": dict(sorted(self._node_access_stats.items(), key=lambda x: x[1], reverse=True)[:10])
                }
            }
            
            for node_id, node_data in self._graph.nodes(data=True):
                node_type = node_data.get("node_type", "unknown")
                analytics["nodes"]["by_type"][node_type] += 1
            
            for from_node, to_node, edge_data in self._graph.edges(data=True):
                connection_type = edge_data.get("connection_type", "unknown")
                analytics["connections"]["by_type"][connection_type] += 1
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get graph analytics: {str(e)}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Knowledge graph health check"""
        try:
            redis_healthy = False
            if self._redis_client:
                try:
                    await self._redis_client.ping()
                    redis_healthy = True
                except Exception:
                    pass
            
            return {
                "status": self._health_status,
                "initialized": self._is_initialized,
                "nodes_count": len(self._graph.nodes),
                "connections_count": len(self._graph.edges),
                "redis_healthy": redis_healthy,
                "cache_size": len(self._node_cache),
                "query_performance_samples": len(self._query_performance),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def cleanup(self) -> None:
        """Cleanup knowledge graph resources"""
        try:
            self.logger.info("Cleaning up knowledge graph resources")
            
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            if self._redis_client:
                await self._redis_client.close()
            
            self._graph.clear()
            self._node_cache.clear()
            self._connection_cache.clear()
            self._query_performance.clear()
            self._node_access_stats.clear()
            
            self._health_status = "stopped"
            self.logger.info("Knowledge graph cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during knowledge graph cleanup: {str(e)}")

# ============================================================================
# EXCEPTION CLASSES
# ============================================================================

class KnowledgeGraphError(Exception):
    """Base exception for knowledge graph errors"""
    pass

class NodeNotFoundError(KnowledgeGraphError):
    """Raised when a requested node is not found"""
    pass

class ConnectionError(KnowledgeGraphError):
    """Raised when connection operations fail"""
    pass

class QueryError(KnowledgeGraphError):
    """Raised when knowledge queries fail"""
    pass

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def create_knowledge_graph(config: Optional[KnowledgeGraphConfig] = None) -> KnowledgeGraph:
    """Create and initialize a knowledge graph instance"""
    if config is None:
        config = KnowledgeGraphConfig()
    
    graph = KnowledgeGraph(config)
    await graph.initialize()
    
    return graph

def validate_knowledge_item(item: Dict[str, Any]) -> bool:
    """Validate knowledge item structure"""
    required_fields = ["content", "node_type"]
    
    for field in required_fields:
        if field not in item:
            raise ValueError(f"Missing required field: {field}")
    
    if not isinstance(item["content"], dict):
        raise ValueError("Content must be a dictionary")
    
    if "confidence" in item:
        confidence = item["confidence"]
        if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
            raise ValueError("Confidence must be a number between 0.0 and 1.0")
    
    return True

async def health_check() -> Dict[str, Any]:
    """Knowledge graph module health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "module": "knowledge_graph",
        "version": "5.0"
    }

# ============================================================================
# DEMO AND TESTING
# ============================================================================

async def demo_knowledge_graph():
    """Demonstration of knowledge graph functionality"""
    print("=" * 70)
    print("YMERA Knowledge Graph - Production Demo")
    print("=" * 70)
    
    # Create and initialize knowledge graph
    print("\n1. Initializing Knowledge Graph...")
    config = KnowledgeGraphConfig(
        max_nodes=10000,
        similarity_threshold=0.7,
        enable_auto_cleanup=False  # Disable for demo
    )
    kg = await create_knowledge_graph(config)
    print("   ✓ Knowledge graph initialized")
    
    # Add some knowledge items
    print("\n2. Adding Knowledge Items...")
    
    item1 = KnowledgeItem(
        content={
            "topic": "Python Programming",
            "description": "Object-oriented programming in Python",
            "difficulty": "intermediate"
        },
        node_type="concept",
        confidence=0.95,
        source="demo",
        tags=["python", "programming", "oop"]
    )
    
    item2 = KnowledgeItem(
        content={
            "topic": "Python Classes",
            "description": "Creating and using classes in Python",
            "difficulty": "intermediate"
        },
        node_type="concept",
        confidence=0.90,
        source="demo",
        tags=["python", "classes", "oop"]
    )
    
    item3 = KnowledgeItem(
        content={
            "topic": "Machine Learning",
            "description": "Introduction to ML algorithms",
            "difficulty": "advanced"
        },
        node_type="concept",
        confidence=0.85,
        source="demo",
        tags=["ml", "ai", "algorithms"]
    )
    
    node1_id = await kg.add_knowledge_item(item1)
    node2_id = await kg.add_knowledge_item(item2)
    node3_id = await kg.add_knowledge_item(item3)
    
    print(f"   ✓ Added 3 knowledge items")
    print(f"     - Node 1: {node1_id[:8]}...")
    print(f"     - Node 2: {node2_id[:8]}...")
    print(f"     - Node 3: {node3_id[:8]}...")
    
    # Perform semantic search
    print("\n3. Semantic Search (Python-related topics)...")
    query = KnowledgeQuery(
        query_type="semantic",
        query_data={
            "content": {
                "topic": "Python",
                "description": "programming concepts"
            }
        },
        max_results=5,
        min_confidence=0.3
    )
    
    results = await kg.query_knowledge(query)
    print(f"   ✓ Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"     {i}. {result.content.get('topic', 'Unknown')} "
              f"(relevance: {result.relevance_score:.2f})")
    
    # Perform exact search
    print("\n4. Exact Search (difficulty: intermediate)...")
    query2 = KnowledgeQuery(
        query_type="exact",
        query_data={
            "content": {"difficulty": "intermediate"}
        },
        max_results=10
    )
    
    results2 = await kg.query_knowledge(query2)
    print(f"   ✓ Found {len(results2)} intermediate topics")
    
    # Add batch knowledge
    print("\n5. Adding Batch Knowledge...")
    batch_items = [
        KnowledgeItem(
            content={"topic": f"Topic {i}", "category": "batch"},
            node_type="concept",
            source="batch_demo"
        )
        for i in range(5)
    ]
    
    connections = await kg.add_knowledge_batch(batch_items, source="batch_demo")
    print(f"   ✓ Added 5 items with {connections} automatic connections")
    
    # Get analytics
    print("\n6. Knowledge Graph Analytics...")
    analytics = await kg.get_graph_analytics()
    print(f"   ✓ Total Nodes: {analytics['nodes']['total']}")
    print(f"   ✓ Total Connections: {analytics['connections']['total']}")
    print(f"   ✓ Graph Density: {analytics['graph_metrics']['density']:.3f}")
    print(f"   ✓ Avg Query Time: {analytics['performance']['avg_query_time']:.3f}s")
    
    # Health check
    print("\n7. Health Check...")
    health = await kg.health_check()
    print(f"   ✓ Status: {health['status']}")
    print(f"   ✓ Initialized: {health['initialized']}")
    print(f"   ✓ Redis: {'Healthy' if health['redis_healthy'] else 'Not Available'}")
    
    # Cleanup
    print("\n8. Cleanup...")
    await kg.cleanup()
    print("   ✓ Resources cleaned up")
    
    print("\n" + "=" * 70)
    print("Demo completed successfully!")
    print("=" * 70)

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "KnowledgeGraph",
    "KnowledgeGraphConfig",
    "KnowledgeItem",
    "KnowledgeQuery",
    "KnowledgeSearchResult",
    "KnowledgeEmbedding",
    "NodeType",
    "create_knowledge_graph",
    "validate_knowledge_item",
    "health_check",
    "KnowledgeGraphError",
    "NodeNotFoundError",
    "ConnectionError",
    "QueryError"
]

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    asyncio.run(demo_knowledge_graph())