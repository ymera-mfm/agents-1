"""
YMERA External Learning Integrator
Integrates external knowledge sources for continuous improvement
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class ExternalSource(Enum):
    """External knowledge sources"""
    ARXIV = "arxiv"
    GITHUB = "github"
    HUGGINGFACE = "huggingface"
    PAPERS_WITH_CODE = "papers_with_code"
    KAGGLE = "kaggle"


@dataclass
class ExternalKnowledge:
    """Represents knowledge from external source"""
    source: ExternalSource
    title: str
    description: str
    url: str
    retrieved_at: datetime
    relevance_score: float
    metadata: Dict[str, Any]


class ExternalLearningIntegrator:
    """
    Integrates external knowledge sources for continuous learning
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize external learning integrator"""
        self.config = config
        self.enabled = config.get("enabled", True)
        self.update_interval = config.get("update_interval_hours", 24) * 3600
        self.sources = [ExternalSource(s) for s in config.get("sources", ["arxiv", "github"])]
        
        # Component references (injected)
        self.learning_engine = None
        self.knowledge_base = None
        
        # State
        self.is_running = False
        self.update_task = None
        self.last_update: Dict[ExternalSource, datetime] = {}
        self.knowledge_items: List[ExternalKnowledge] = []
        
        logger.info(f"External Learning Integrator initialized with sources: {[s.value for s in self.sources]}")
    
    def set_learning_engine(self, learning_engine):
        """Inject learning engine dependency"""
        self.learning_engine = learning_engine
    
    def set_knowledge_base(self, knowledge_base):
        """Inject knowledge base dependency"""
        self.knowledge_base = knowledge_base
    
    async def start(self):
        """Start external learning integration"""
        if not self.enabled:
            logger.warning("External learning is disabled")
            return
        
        if self.is_running:
            logger.warning("External learning already running")
            return
        
        self.is_running = True
        self.update_task = asyncio.create_task(self._update_loop())
        logger.info("External learning integration started")
    
    async def stop(self):
        """Stop external learning integration"""
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        logger.info("External learning integration stopped")
    
    async def _update_loop(self):
        """Main external learning update loop"""
        while self.is_running:
            try:
                await asyncio.sleep(self.update_interval)
                
                # Fetch from all sources
                await self._fetch_from_all_sources()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in external learning loop: {str(e)}", exc_info=True)
    
    async def _fetch_from_all_sources(self):
        """Fetch knowledge from all configured sources"""
        logger.info("Fetching knowledge from external sources")
        
        tasks = []
        for source in self.sources:
            tasks.append(self._fetch_from_source(source))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_items = 0
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch from source: {str(result)}")
            else:
                total_items += len(result)
        
        logger.info(f"Fetched {total_items} knowledge items from external sources")
    
    async def _fetch_from_source(self, source: ExternalSource) -> List[ExternalKnowledge]:
        """Fetch knowledge from a specific source"""
        logger.info(f"Fetching from {source.value}")
        
        # Check if we need to update
        last_update = self.last_update.get(source)
        if last_update and (datetime.utcnow() - last_update).total_seconds() < self.update_interval:
            logger.debug(f"Skipping {source.value} - recently updated")
            return []
        
        # Dispatch to specific source handler
        if source == ExternalSource.ARXIV:
            items = await self._fetch_from_arxiv()
        elif source == ExternalSource.GITHUB:
            items = await self._fetch_from_github()
        elif source == ExternalSource.HUGGINGFACE:
            items = await self._fetch_from_huggingface()
        else:
            logger.warning(f"Handler not implemented for {source.value}")
            items = []
        
        # Store in knowledge base
        for item in items:
            if self.knowledge_base:
                await self.knowledge_base.store(
                    {
                        "title": item.title,
                        "description": item.description,
                        "url": item.url,
                        "source": item.source.value,
                        "relevance_score": item.relevance_score,
                        "metadata": item.metadata
                    },
                    category="external_knowledge",
                    tags=["external", item.source.value]
                )
        
        self.knowledge_items.extend(items)
        self.last_update[source] = datetime.utcnow()
        
        return items
    
    async def _fetch_from_arxiv(self) -> List[ExternalKnowledge]:
        """Fetch relevant papers from arXiv"""
        # In production, this would use the arXiv API
        # For now, we'll return mock data
        
        logger.info("Fetching from arXiv API")
        
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # Mock papers
        papers = [
            ExternalKnowledge(
                source=ExternalSource.ARXIV,
                title="Advances in Neural Architecture Search",
                description="A comprehensive survey of neural architecture search methods",
                url="https://arxiv.org/abs/2024.00001",
                retrieved_at=datetime.utcnow(),
                relevance_score=0.92,
                metadata={"authors": ["Smith, J.", "Doe, A."], "year": 2024}
            ),
            ExternalKnowledge(
                source=ExternalSource.ARXIV,
                title="Continuous Learning with Concept Drift Detection",
                description="Novel approaches to detecting and adapting to concept drift",
                url="https://arxiv.org/abs/2024.00002",
                retrieved_at=datetime.utcnow(),
                relevance_score=0.88,
                metadata={"authors": ["Johnson, K."], "year": 2024}
            )
        ]
        
        return papers
    
    async def _fetch_from_github(self) -> List[ExternalKnowledge]:
        """Fetch relevant repositories from GitHub"""
        logger.info("Fetching from GitHub API")
        
        await asyncio.sleep(0.1)
        
        repos = [
            ExternalKnowledge(
                source=ExternalSource.GITHUB,
                title="AutoML Framework",
                description="Production-ready AutoML framework for enterprise use",
                url="https://github.com/example/automl-framework",
                retrieved_at=datetime.utcnow(),
                relevance_score=0.85,
                metadata={"stars": 5000, "language": "Python"}
            )
        ]
        
        return repos
    
    async def _fetch_from_huggingface(self) -> List[ExternalKnowledge]:
        """Fetch relevant models from HuggingFace"""
        logger.info("Fetching from HuggingFace Hub")
        
        await asyncio.sleep(0.1)
        
        models = [
            ExternalKnowledge(
                source=ExternalSource.HUGGINGFACE,
                title="bert-large-finetuned",
                description="BERT model fine-tuned for classification tasks",
                url="https://huggingface.co/bert-large-finetuned",
                retrieved_at=datetime.utcnow(),
                relevance_score=0.90,
                metadata={"downloads": 100000, "task": "text-classification"}
            )
        ]
        
        return models
    
    async def search_external_knowledge(
        self, 
        query: str, 
        source: Optional[ExternalSource] = None,
        limit: int = 10
    ) -> List[ExternalKnowledge]:
        """Search external knowledge"""
        results = self.knowledge_items
        
        if source:
            results = [k for k in results if k.source == source]
        
        # Simple keyword search
        query_lower = query.lower()
        scored_results = []
        for item in results:
            title_lower = item.title.lower()
            desc_lower = item.description.lower()
            
            if query_lower in title_lower or query_lower in desc_lower:
                scored_results.append(item)
        
        # Sort by relevance score
        scored_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return scored_results[:limit]
    
    async def get_recent_knowledge(
        self, 
        hours: int = 24,
        source: Optional[ExternalSource] = None
    ) -> List[ExternalKnowledge]:
        """Get recently fetched knowledge"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        results = [
            k for k in self.knowledge_items
            if k.retrieved_at >= cutoff
        ]
        
        if source:
            results = [k for k in results if k.source == source]
        
        return results
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get external learning statistics"""
        source_counts = {}
        for source in self.sources:
            count = len([k for k in self.knowledge_items if k.source == source])
            source_counts[source.value] = count
        
        return {
            "enabled": self.enabled,
            "is_running": self.is_running,
            "total_knowledge_items": len(self.knowledge_items),
            "sources": [s.value for s in self.sources],
            "source_counts": source_counts,
            "last_updates": {
                source.value: last_update.isoformat()
                for source, last_update in self.last_update.items()
            }
        }
