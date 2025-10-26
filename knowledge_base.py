"""
YMERA Enhanced Knowledge Base
Persistent knowledge storage with semantic search and graph capabilities.
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib
from collections import defaultdict

logger = logging.getLogger("ymera.knowledge_base")


@dataclass
class KnowledgeEntry:
    """Represents a knowledge entry"""
    entry_id: str
    content: Dict[str, Any]
    category: str
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    relevance_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "access_count": self.access_count,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata
        }


class KnowledgeBase:
    """
    Enhanced Knowledge Base with persistent storage, semantic search, and graph capabilities.
    
    In production, this would integrate with:
    - NoSQL database (MongoDB/Cassandra) for scalable storage
    - Vector database (FAISS/Pinecone) for semantic search
    - Graph database (Neo4j) for relationship modeling
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Knowledge Base.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.entries: Dict[str, KnowledgeEntry] = {}
        self.category_index: Dict[str, List[str]] = defaultdict(list)
        self.tag_index: Dict[str, List[str]] = defaultdict(list)
        self.relationships: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Database connections (placeholders for production)
        self.db_connection = None
        self.vector_db = None
        self.graph_db = None
        
        logger.info(f"Knowledge Base initialized with config: {config}")
    
    async def initialize_storage(self):
        """Initialize persistent storage connections"""
        # In production, this would establish connections to:
        # - MongoDB/Cassandra for document storage
        # - FAISS/Pinecone for vector embeddings
        # - Neo4j for graph relationships
        logger.info("Storage initialization placeholder - would connect to databases in production")
    
    async def store(self, content: Dict[str, Any], 
                   category: str = "general",
                   tags: List[str] = None,
                   metadata: Dict[str, Any] = None) -> str:
        """
        Store knowledge in the knowledge base.
        
        Args:
            content: Content to store
            category: Category for the knowledge
            tags: Tags for categorization
            metadata: Additional metadata
            
        Returns:
            Entry ID
        """
        entry_id = self._generate_entry_id(content)
        
        if entry_id in self.entries:
            # Update existing entry
            entry = self.entries[entry_id]
            entry.content.update(content)
            entry.updated_at = datetime.utcnow()
            entry.access_count += 1
            if tags:
                entry.tags = list(set(entry.tags + tags))
            if metadata:
                entry.metadata.update(metadata)
            logger.info(f"Updated knowledge entry {entry_id}")
        else:
            # Create new entry
            entry = KnowledgeEntry(
                entry_id=entry_id,
                content=content,
                category=category,
                tags=tags or [],
                metadata=metadata or {}
            )
            self.entries[entry_id] = entry
            
            # Update indices
            self.category_index[category].append(entry_id)
            for tag in entry.tags:
                self.tag_index[tag].append(entry_id)
            
            logger.info(f"Stored new knowledge entry {entry_id} in category {category}")
        
        # In production, persist to database
        await self._persist_entry(entry)
        
        return entry_id
    
    async def retrieve(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """
        Retrieve knowledge by entry ID.
        
        Args:
            entry_id: Entry identifier
            
        Returns:
            KnowledgeEntry or None
        """
        entry = self.entries.get(entry_id)
        if entry:
            entry.access_count += 1
            entry.updated_at = datetime.utcnow()
        return entry
    
    async def search(self, query: Dict[str, Any], 
                    category: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    limit: int = 10) -> List[KnowledgeEntry]:
        """
        Search knowledge base with filters.
        
        Args:
            query: Search query
            category: Filter by category
            tags: Filter by tags
            limit: Maximum results
            
        Returns:
            List of matching KnowledgeEntry objects
        """
        results = []
        
        # Start with all entries or filtered by category
        if category:
            candidate_ids = self.category_index.get(category, [])
        else:
            candidate_ids = list(self.entries.keys())
        
        # Filter by tags if provided
        if tags:
            tag_filtered_ids = set()
            for tag in tags:
                tag_filtered_ids.update(self.tag_index.get(tag, []))
            candidate_ids = [eid for eid in candidate_ids if eid in tag_filtered_ids]
        
        # Score and rank results
        scored_results = []
        for entry_id in candidate_ids:
            entry = self.entries[entry_id]
            score = self._calculate_relevance_score(entry, query)
            if score > 0:
                scored_results.append((score, entry))
        
        # Sort by score and return top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        results = [entry for score, entry in scored_results[:limit]]
        
        logger.info(f"Search returned {len(results)} results")
        return results
    
    async def semantic_search(self, query_text: str, 
                             top_k: int = 10) -> List[KnowledgeEntry]:
        """
        Perform semantic search using vector embeddings.
        
        In production, this would:
        1. Generate embedding for query_text
        2. Query vector database (FAISS/Pinecone)
        3. Retrieve top-k similar entries
        
        Args:
            query_text: Natural language query
            top_k: Number of results
            
        Returns:
            List of semantically similar KnowledgeEntry objects
        """
        # Placeholder for semantic search
        # In production, this would use actual embeddings and vector search
        logger.info(f"Semantic search placeholder for query: {query_text}")
        
        # For now, fall back to keyword-based search
        query_words = query_text.lower().split()
        results = []
        
        for entry in self.entries.values():
            content_str = json.dumps(entry.content).lower()
            match_count = sum(1 for word in query_words if word in content_str)
            if match_count > 0:
                entry.relevance_score = match_count / len(query_words)
                results.append(entry)
        
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_k]
    
    async def add_relationship(self, source_id: str, target_id: str, 
                              relationship_type: str,
                              properties: Dict[str, Any] = None):
        """
        Add a relationship between two knowledge entries.
        
        In production, this would create edges in a graph database (Neo4j).
        
        Args:
            source_id: Source entry ID
            target_id: Target entry ID
            relationship_type: Type of relationship
            properties: Additional relationship properties
        """
        if source_id not in self.entries or target_id not in self.entries:
            logger.warning(f"Cannot create relationship: entry not found")
            return
        
        relationship = {
            "target_id": target_id,
            "type": relationship_type,
            "properties": properties or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.relationships[source_id].append(relationship)
        logger.info(f"Added {relationship_type} relationship from {source_id} to {target_id}")
    
    async def get_related(self, entry_id: str, 
                         relationship_type: Optional[str] = None) -> List[KnowledgeEntry]:
        """
        Get related knowledge entries.
        
        Args:
            entry_id: Entry ID to find relationships for
            relationship_type: Filter by relationship type
            
        Returns:
            List of related KnowledgeEntry objects
        """
        if entry_id not in self.relationships:
            return []
        
        relationships = self.relationships[entry_id]
        if relationship_type:
            relationships = [r for r in relationships if r["type"] == relationship_type]
        
        related_entries = []
        for rel in relationships:
            target_id = rel["target_id"]
            if target_id in self.entries:
                related_entries.append(self.entries[target_id])
        
        return related_entries
    
    async def get_by_category(self, category: str, limit: int = 100) -> List[KnowledgeEntry]:
        """Get all entries in a category"""
        entry_ids = self.category_index.get(category, [])
        return [self.entries[eid] for eid in entry_ids[:limit]]
    
    async def get_by_tags(self, tags: List[str], limit: int = 100) -> List[KnowledgeEntry]:
        """Get all entries with specified tags"""
        matching_ids = set()
        for tag in tags:
            matching_ids.update(self.tag_index.get(tag, []))
        
        return [self.entries[eid] for eid in list(matching_ids)[:limit]]
    
    async def update_entry(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing entry"""
        if entry_id not in self.entries:
            return False
        
        entry = self.entries[entry_id]
        entry.content.update(updates)
        entry.updated_at = datetime.utcnow()
        
        await self._persist_entry(entry)
        logger.info(f"Updated entry {entry_id}")
        return True
    
    async def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry"""
        if entry_id not in self.entries:
            return False
        
        entry = self.entries[entry_id]
        
        # Remove from indices
        self.category_index[entry.category].remove(entry_id)
        for tag in entry.tags:
            if entry_id in self.tag_index[tag]:
                self.tag_index[tag].remove(entry_id)
        
        # Remove relationships
        if entry_id in self.relationships:
            del self.relationships[entry_id]
        
        # Remove entry
        del self.entries[entry_id]
        
        logger.info(f"Deleted entry {entry_id}")
        return True
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        categories = defaultdict(int)
        tags = defaultdict(int)
        
        for entry in self.entries.values():
            categories[entry.category] += 1
            for tag in entry.tags:
                tags[tag] += 1
        
        return {
            "total_entries": len(self.entries),
            "categories": dict(categories),
            "tags": dict(tags),
            "total_relationships": sum(len(rels) for rels in self.relationships.values())
        }
    
    def _generate_entry_id(self, content: Dict[str, Any]) -> str:
        """Generate a unique entry ID based on content"""
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _calculate_relevance_score(self, entry: KnowledgeEntry, query: Dict[str, Any]) -> float:
        """Calculate relevance score for an entry given a query"""
        score = 0.0
        
        # Simple keyword matching
        query_str = json.dumps(query).lower()
        content_str = json.dumps(entry.content).lower()
        
        query_words = set(query_str.split())
        content_words = set(content_str.split())
        
        if query_words and content_words:
            intersection = query_words.intersection(content_words)
            score = len(intersection) / len(query_words)
        
        # Boost by access count (popular entries)
        score *= (1 + min(entry.access_count / 100, 0.5))
        
        return score
    
    async def _persist_entry(self, entry: KnowledgeEntry):
        """Persist entry to database (placeholder)"""
        # In production, this would write to MongoDB/Cassandra
        logger.debug(f"Persisting entry {entry.entry_id} to database")
    
    async def export_to_json(self, filepath: str):
        """Export knowledge base to JSON file"""
        export_data = {
            "entries": [entry.to_dict() for entry in self.entries.values()],
            "relationships": dict(self.relationships),
            "exported_at": datetime.utcnow().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported knowledge base to {filepath}")
    
    async def import_from_json(self, filepath: str):
        """Import knowledge base from JSON file"""
        with open(filepath, 'r') as f:
            import_data = json.load(f)
        
        for entry_data in import_data.get("entries", []):
            entry = KnowledgeEntry(
                entry_id=entry_data["entry_id"],
                content=entry_data["content"],
                category=entry_data["category"],
                tags=entry_data["tags"],
                created_at=datetime.fromisoformat(entry_data["created_at"]),
                updated_at=datetime.fromisoformat(entry_data["updated_at"]),
                access_count=entry_data["access_count"],
                relevance_score=entry_data["relevance_score"],
                metadata=entry_data["metadata"]
            )
            self.entries[entry.entry_id] = entry
            
            # Rebuild indices
            self.category_index[entry.category].append(entry.entry_id)
            for tag in entry.tags:
                self.tag_index[tag].append(entry.entry_id)
        
        # Import relationships
        for source_id, rels in import_data.get("relationships", {}).items():
            self.relationships[source_id] = rels
        
        logger.info(f"Imported knowledge base from {filepath}")
