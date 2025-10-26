"""
Knowledge Store
Manages storage, retrieval, and indexing of knowledge entries
"""

import uuid
import json
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from shared.utils.cache_manager import CacheManager
except ImportError:
    CacheManager = None

try:
    from models import KnowledgeItem as KnowledgeEntryModel
    KnowledgeCategory = None
except ImportError:
    KnowledgeEntryModel = None
    KnowledgeCategory = None


logger = structlog.get_logger(__name__)


class KnowledgeStore:
    """
    Knowledge storage and retrieval system
    Implements efficient storage, search, and versioning of knowledge
    """
    
    def __init__(self, db_session: AsyncSession, cache_manager: CacheManager):
        self.db = db_session
        self.cache = cache_manager
        self.search_index = {}
    
    async def store(
        self,
        content: str,
        category: KnowledgeCategory,
        source_agent_id: str,
        metadata: Dict[str, Any],
        tags: List[str],
        title: Optional[str] = None,
        summary: Optional[str] = None
    ) -> str:
        """
        Store a new knowledge entry
        
        Args:
            content: Knowledge content
            category: Knowledge category
            source_agent_id: Source agent
            metadata: Additional metadata
            tags: Knowledge tags
            title: Optional title
            summary: Optional summary
            
        Returns:
            Entry ID
        """
        try:
            entry_id = str(uuid.uuid4())
            
            # Generate summary if not provided
            if not summary and len(content) > 200:
                summary = self._generate_summary(content)
            
            # Create knowledge entry
            entry = KnowledgeEntryModel(
                entry_id=entry_id,
                category=category,
                title=title or self._generate_title(content),
                content=content,
                summary=summary,
                source_agent_id=source_agent_id,
                tags=tags,
                metadata=metadata,
                confidence_score=0.7,  # Initial confidence
                created_at=datetime.utcnow()
            )
            
            self.db.add(entry)
            await self.db.commit()
            await self.db.refresh(entry)
            
            # Cache the entry
            await self._cache_entry(entry)
            
            # Update search index
            await self._index_entry(entry)
            
            logger.info("Knowledge stored", entry_id=entry_id, category=category)
            
            return entry_id
            
        except Exception as e:
            logger.error("Failed to store knowledge", error=str(e))
            raise
    
    async def get(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a knowledge entry by ID
        
        Args:
            entry_id: Entry ID
            
        Returns:
            Knowledge entry or None
        """
        try:
            # Try cache first
            cached = await self.cache.get(f"knowledge:{entry_id}")
            if cached:
                return cached
            
            # Query database
            stmt = select(KnowledgeEntryModel).where(
                and_(
                    KnowledgeEntryModel.entry_id == entry_id,
                    KnowledgeEntryModel.deleted_at.is_(None)
                )
            )
            result = await self.db.execute(stmt)
            entry = result.scalar_one_or_none()
            
            if entry:
                # Update access timestamp
                entry.last_accessed_at = datetime.utcnow()
                entry.usage_count += 1
                await self.db.commit()
                
                # Cache it
                entry_data = self._entry_to_dict(entry)
                await self._cache_entry_data(entry_id, entry_data)
                
                return entry_data
            
            return None
            
        except Exception as e:
            logger.error("Failed to get knowledge", entry_id=entry_id, error=str(e))
            return None
    
    async def search(
        self,
        query: str,
        category: Optional[KnowledgeCategory] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        min_confidence: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge entries
        
        Args:
            query: Search query
            category: Optional category filter
            tags: Optional tag filters
            limit: Maximum results
            min_confidence: Minimum confidence score
            
        Returns:
            List of matching knowledge entries
        """
        try:
            # Build query
            conditions = [KnowledgeEntryModel.deleted_at.is_(None)]
            
            if category:
                conditions.append(KnowledgeEntryModel.category == category)
            
            if min_confidence:
                conditions.append(KnowledgeEntryModel.confidence_score >= min_confidence)
            
            # Text search (simplified - would use full-text search in production)
            query_lower = query.lower()
            conditions.append(
                or_(
                    func.lower(KnowledgeEntryModel.content).contains(query_lower),
                    func.lower(KnowledgeEntryModel.title).contains(query_lower),
                    func.lower(KnowledgeEntryModel.summary).contains(query_lower)
                )
            )
            
            stmt = (
                select(KnowledgeEntryModel)
                .where(and_(*conditions))
                .order_by(
                    desc(KnowledgeEntryModel.confidence_score),
                    desc(KnowledgeEntryModel.usage_count),
                    desc(KnowledgeEntryModel.created_at)
                )
                .limit(limit)
            )
            
            result = await self.db.execute(stmt)
            entries = result.scalars().all()
            
            # Convert to dicts and calculate relevance
            results = []
            for entry in entries:
                entry_data = self._entry_to_dict(entry)
                entry_data['relevance_score'] = self._calculate_relevance(
                    entry, query, tags
                )
                results.append(entry_data)
            
            # Sort by relevance
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            logger.info(f"Search returned {len(results)} results", query=query)
            
            return results
            
        except Exception as e:
            logger.error("Search failed", query=query, error=str(e))
            return []
    
    async def update(
        self,
        entry_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        title: Optional[str] = None,
        summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a knowledge entry
        
        Args:
            entry_id: Entry ID
            content: New content (optional)
            metadata: New metadata (optional)
            tags: New tags (optional)
            title: New title (optional)
            summary: New summary (optional)
            
        Returns:
            Update result
        """
        try:
            stmt = select(KnowledgeEntryModel).where(
                KnowledgeEntryModel.entry_id == entry_id
            )
            result = await self.db.execute(stmt)
            entry = result.scalar_one_or_none()
            
            if not entry:
                raise ValueError(f"Knowledge entry {entry_id} not found")
            
            # Create new version if content changed significantly
            if content and content != entry.content:
                # Store old version
                old_version_id = await self._create_version(entry)
                
                # Update with new content
                entry.content = content
                entry.version += 1
                entry.parent_entry_id = old_version_id
                
                if not summary:
                    entry.summary = self._generate_summary(content)
                
                # Re-index
                await self._index_entry(entry)
            
            # Update other fields
            if metadata:
                entry.metadata.update(metadata)
            if tags:
                entry.tags = tags
            if title:
                entry.title = title
            if summary:
                entry.summary = summary
            
            entry.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Invalidate cache
            await self.cache.delete(f"knowledge:{entry_id}")
            
            logger.info("Knowledge updated", entry_id=entry_id)
            
            return {
                "status": "updated",
                "entry_id": entry_id,
                "version": entry.version,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to update knowledge", entry_id=entry_id, error=str(e))
            raise
    
    async def delete(
        self,
        entry_id: str,
        reason: str,
        deleted_by: str
    ) -> Dict[str, Any]:
        """
        Soft delete a knowledge entry
        
        Args:
            entry_id: Entry ID
            reason: Deletion reason
            deleted_by: Who deleted it
            
        Returns:
            Deletion result
        """
        try:
            stmt = select(KnowledgeEntryModel).where(
                KnowledgeEntryModel.entry_id == entry_id
            )
            result = await self.db.execute(stmt)
            entry = result.scalar_one_or_none()
            
            if not entry:
                raise ValueError(f"Knowledge entry {entry_id} not found")
            
            # Soft delete
            entry.deleted_at = datetime.utcnow()
            entry.deleted_by = deleted_by
            entry.deletion_reason = reason
            
            await self.db.commit()
            
            # Clear cache
            await self.cache.delete(f"knowledge:{entry_id}")
            
            logger.info("Knowledge deleted", entry_id=entry_id, reason=reason)
            
            return {
                "status": "deleted",
                "entry_id": entry_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to delete knowledge", entry_id=entry_id, error=str(e))
            raise
    
    async def get_by_category(
        self,
        category: KnowledgeCategory,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all knowledge entries in a category"""
        try:
            stmt = (
                select(KnowledgeEntryModel)
                .where(
                    and_(
                        KnowledgeEntryModel.category == category,
                        KnowledgeEntryModel.deleted_at.is_(None)
                    )
                )
                .order_by(desc(KnowledgeEntryModel.created_at))
                .limit(limit)
            )
            
            result = await self.db.execute(stmt)
            entries = result.scalars().all()
            
            return [self._entry_to_dict(entry) for entry in entries]
            
        except Exception as e:
            logger.error("Failed to get category entries", category=category, error=str(e))
            return []
    
    async def get_by_tags(
        self,
        tags: List[str],
        match_all: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get knowledge entries by tags"""
        try:
            stmt = select(KnowledgeEntryModel).where(
                KnowledgeEntryModel.deleted_at.is_(None)
            )
            
            # This is simplified - in production, use proper JSON array queries
            conditions = []
            for tag in tags:
                conditions.append(
                    func.json_contains(KnowledgeEntryModel.tags, json.dumps([tag]))
                )
            
            if match_all:
                stmt = stmt.where(and_(*conditions))
            else:
                stmt = stmt.where(or_(*conditions))
            
            stmt = stmt.order_by(desc(KnowledgeEntryModel.created_at)).limit(limit)
            
            result = await self.db.execute(stmt)
            entries = result.scalars().all()
            
            return [self._entry_to_dict(entry) for entry in entries]
            
        except Exception as e:
            logger.error("Failed to get tagged entries", tags=tags, error=str(e))
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            # Total entries
            total_stmt = select(func.count(KnowledgeEntryModel.entry_id)).where(
                KnowledgeEntryModel.deleted_at.is_(None)
            )
            total_result = await self.db.execute(total_stmt)
            total = total_result.scalar() or 0
            
            # By category
            category_stmt = (
                select(
                    KnowledgeEntryModel.category,
                    func.count(KnowledgeEntryModel.entry_id)
                )
                .where(KnowledgeEntryModel.deleted_at.is_(None))
                .group_by(KnowledgeEntryModel.category)
            )
            category_result = await self.db.execute(category_stmt)
            by_category = {cat: count for cat, count in category_result.fetchall()}
            
            # Average confidence
            avg_stmt = select(func.avg(KnowledgeEntryModel.confidence_score)).where(
                KnowledgeEntryModel.deleted_at.is_(None)
            )
            avg_result = await self.db.execute(avg_stmt)
            avg_confidence = avg_result.scalar() or 0.0
            
            # Most used
            most_used_stmt = (
                select(KnowledgeEntryModel)
                .where(KnowledgeEntryModel.deleted_at.is_(None))
                .order_by(desc(KnowledgeEntryModel.usage_count))
                .limit(10)
            )
            most_used_result = await self.db.execute(most_used_stmt)
            most_used = [
                {
                    "entry_id": e.entry_id,
                    "title": e.title,
                    "usage_count": e.usage_count
                }
                for e in most_used_result.scalars().all()
            ]
            
            return {
                "total_entries": total,
                "by_category": by_category,
                "average_confidence": round(avg_confidence, 2),
                "most_used": most_used,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to get statistics", error=str(e))
            return {}
    
    async def get_index(self) -> Dict[str, List[str]]:
        """Get knowledge index for quick lookup"""
        try:
            # Get all entries grouped by category
            stmt = select(
                KnowledgeEntryModel.category,
                KnowledgeEntryModel.entry_id
            ).where(KnowledgeEntryModel.deleted_at.is_(None))
            
            result = await self.db.execute(stmt)
            
            index = {}
            for category, entry_id in result.fetchall():
                if category not in index:
                    index[category] = []
                index[category].append(entry_id)
            
            return index
            
        except Exception as e:
            logger.error("Failed to get index", error=str(e))
            return {}
    
    async def rebuild_index(self):
        """Rebuild search index"""
        try:
            # Get all entries
            stmt = select(KnowledgeEntryModel).where(
                KnowledgeEntryModel.deleted_at.is_(None)
            )
            result = await self.db.execute(stmt)
            entries = result.scalars().all()
            
            # Rebuild index
            self.search_index = {}
            for entry in entries:
                await self._index_entry(entry)
            
            logger.info(f"Rebuilt search index with {len(entries)} entries")
            
        except Exception as e:
            logger.error("Failed to rebuild index", error=str(e))
    
    # Helper methods
    
    def _entry_to_dict(self, entry: KnowledgeEntryModel) -> Dict[str, Any]:
        """Convert entry model to dictionary"""
        return {
            "entry_id": entry.entry_id,
            "category": entry.category,
            "title": entry.title,
            "content": entry.content,
            "summary": entry.summary,
            "source_agent_id": entry.source_agent_id,
            "tags": entry.tags,
            "metadata": entry.metadata,
            "confidence_score": entry.confidence_score,
            "usage_count": entry.usage_count,
            "success_rate": entry.success_rate,
            "version": entry.version,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
            "last_accessed_at": entry.last_accessed_at.isoformat() if entry.last_accessed_at else None
        }
    
    async def _cache_entry(self, entry: KnowledgeEntryModel):
        """Cache a knowledge entry"""
        entry_data = self._entry_to_dict(entry)
        await self.cache.set(
            f"knowledge:{entry.entry_id}",
            entry_data,
            ttl=3600
        )
    
    async def _cache_entry_data(self, entry_id: str, entry_data: Dict[str, Any]):
        """Cache entry data"""
        await self.cache.set(
            f"knowledge:{entry_id}",
            entry_data,
            ttl=3600
        )
    
    async def _index_entry(self, entry: KnowledgeEntryModel):
        """Index an entry for search"""
        # Extract keywords from content
        keywords = self._extract_keywords(entry.content)
        
        # Add to index
        for keyword in keywords:
            if keyword not in self.search_index:
                self.search_index[keyword] = []
            if entry.entry_id not in self.search_index[keyword]:
                self.search_index[keyword].append(entry.entry_id)
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content"""
        # Simplified keyword extraction
        # In production, use NLP libraries
        words = content.lower().split()
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return list(set(keywords[:50]))  # Top 50 unique keywords
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """Generate summary from content"""
        # Simplified summary generation
        # In production, use NLP summarization
        if len(content) <= max_length:
            return content
        
        # Take first sentence or max_length chars
        sentences = content.split('.')
        if sentences and len(sentences[0]) <= max_length:
            return sentences[0].strip() + '.'
        
        return content[:max_length].rsplit(' ', 1)[0] + '...'
    
    def _generate_title(self, content: str, max_length: int = 100) -> str:
        """Generate title from content"""
        # Take first line or first N characters
        lines = content.split('\n')
        first_line = lines[0].strip()
        
        if first_line and len(first_line) <= max_length:
            return first_line
        
        # Extract from content
        words = content.split()[:10]
        title = ' '.join(words)
        
        if len(title) > max_length:
            title = title[:max_length].rsplit(' ', 1)[0] + '...'
        
        return title
    
    def _calculate_relevance(
        self,
        entry: KnowledgeEntryModel,
        query: str,
        tags: Optional[List[str]]
    ) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        
        # Base score from confidence
        score += entry.confidence_score * 0.3
        
        # Usage popularity
        score += min(entry.usage_count / 100, 0.2)
        
        # Success rate
        score += entry.success_rate * 0.2
        
        # Query match (simplified)
        query_lower = query.lower()
        content_lower = entry.content.lower()
        
        if query_lower in content_lower:
            score += 0.3
        elif any(word in content_lower for word in query_lower.split()):
            score += 0.15
        
        # Tag match
        if tags and entry.tags:
            matching_tags = set(tags) & set(entry.tags)
            if matching_tags:
                score += len(matching_tags) / len(tags) * 0.1
        
        return min(score, 1.0)
    
    async def _create_version(self, entry: KnowledgeEntryModel) -> str:
        """Create a version snapshot of an entry"""
        version_id = str(uuid.uuid4())
        
        version_entry = KnowledgeEntryModel(
            entry_id=version_id,
            category=entry.category,
            title=f"{entry.title} (v{entry.version})",
            content=entry.content,
            summary=entry.summary,
            source_agent_id=entry.source_agent_id,
            tags=entry.tags,
            metadata={**entry.metadata, "is_version": True, "original_id": entry.entry_id},
            confidence_score=entry.confidence_score,
            usage_count=0,
            success_rate=entry.success_rate,
            version=entry.version,
            parent_entry_id=None,
            created_at=entry.created_at
        )
        
        self.db.add(version_entry)
        await self.db.commit()
        
        return version_id
