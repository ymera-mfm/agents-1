
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID

try:
    from database import Database
except ImportError:
    Database = None

try:
    from models import KnowledgeItem
except ImportError:
    KnowledgeItem = None

logger = logging.getLogger(__name__)

class KnowledgeManager:
    def __init__(self, database):
        self.database = database
        self.is_initialized = False
        self.search_cache = {}
    
    async def initialize(self):
        """Initialize knowledge manager"""
        self.is_initialized = True
        logger.info("Knowledge Manager initialized")
    
    async def create_knowledge_item(self, title: str, content: str,
                                   tags: List[str] = None, category: str = None) -> KnowledgeItem:
        """Create new knowledge item"""
        query = """
            INSERT INTO knowledge_items (title, content, tags, category)
            VALUES ($1, $2, $3, $4)
            RETURNING id, title, content, tags, category, confidence_score, usage_count, created_at, updated_at
        """
        
        result = await self.database.execute_single(
            query, title, content, tags or [], category
        )
        
        return KnowledgeItem(**result)
    
    async def search_knowledge(self, query: str, limit: int = 5) -> List[Dict]:
        """Search knowledge base"""
        # Simple text search - in production you'd use full-text search
        search_query = """
            SELECT id, title, content, tags, category, confidence_score, usage_count
            FROM knowledge_items
            WHERE 
                title ILIKE $1 
                OR content ILIKE $1
                OR $2 = ANY(tags)
            ORDER BY confidence_score DESC, usage_count DESC
            LIMIT $3
        """
        
        search_term = f"%{query}%"
        results = await self.database.execute_query(search_query, search_term, query, limit)
        
        # Update usage counts
        if results:
            ids = [result["id"] for result in results]
            await self._update_usage_counts(ids)
        
        return results
    
    async def get_knowledge_item(self, knowledge_id: UUID) -> Optional[Dict]:
        """Get specific knowledge item"""
        query = """
            SELECT id, title, content, tags, category, confidence_score, usage_count, created_at, updated_at
            FROM knowledge_items
            WHERE id = $1
        """
        
        result = await self.database.execute_single(query, knowledge_id)
        
        if result:
            # Update usage count
            await self._update_usage_counts([knowledge_id])
        
        return result
    
    async def update_knowledge_scores(self):
        """Update knowledge confidence scores based on usage and feedback"""
        # Simple scoring algorithm - you'd make this more sophisticated
        query = """
            UPDATE knowledge_items
            SET confidence_score = LEAST(1.0, 
                (usage_count * 0.1) + 
                (EXTRACT(DAYS FROM NOW() - created_at) * -0.01) + 0.5
            )
            WHERE confidence_score != LEAST(1.0, 
                (usage_count * 0.1) + 
                (EXTRACT(DAYS FROM NOW() - created_at) * -0.01) + 0.5
            )
        """
        
        await self.database.execute_command(query)
        logger.info("Knowledge scores updated")
    
    async def _update_usage_counts(self, knowledge_ids: List[UUID]):
        """Update usage counts for knowledge items"""
        if not knowledge_ids:
            return
        
        query = """
            UPDATE knowledge_items
            SET usage_count = usage_count + 1, updated_at = NOW()
            WHERE id = ANY($1)
        """
        
        await self.database.execute_command(query, knowledge_ids)
    
    async def health_check(self) -> bool:
        """Check knowledge manager health"""
        return self.is_initialized
    
    async def shutdown(self):
        """Shutdown knowledge manager"""
        logger.info("Knowledge Manager shutdown complete")

