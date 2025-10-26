"""
Knowledge Flow Manager
Manages the flow of knowledge between agents and the learning system
"""

import uuid
import structlog
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from collections import defaultdict
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.utils.message_broker import MessageBroker
try:
    from models import KnowledgeItem
    KnowledgeSubscriptionModel = None
    KnowledgeCategory = None
except ImportError:
    KnowledgeSubscriptionModel = None
    KnowledgeCategory = None


logger = structlog.get_logger(__name__)


class KnowledgeFlowManager:
    """
    Manages bidirectional knowledge flow between agents and learning system
    """
    
    def __init__(self, db_session: AsyncSession, message_broker: MessageBroker, learning_agent):
        self.db = db_session
        self.broker = message_broker
        self.learning_agent = learning_agent
        self.active_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self.flow_metrics = {
            'knowledge_shared': 0,
            'requests_fulfilled': 0,
            'subscriptions_active': 0
        }
    
    async def start(self):
        """Start the knowledge flow manager"""
        try:
            # Load existing subscriptions
            await self._load_subscriptions()
            
            # Subscribe to knowledge flow channels
            await self._setup_channels()
            
            logger.info("Knowledge Flow Manager started")
            
        except Exception as e:
            logger.error("Failed to start Knowledge Flow Manager", error=str(e))
            raise
    
    async def stop(self):
        """Stop the knowledge flow manager"""
        try:
            logger.info("Knowledge Flow Manager stopped")
            
        except Exception as e:
            logger.error("Error stopping Knowledge Flow Manager", error=str(e))
    
    async def create_subscription(
        self,
        agent_id: str,
        categories: List[KnowledgeCategory],
        tags: List[str],
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a knowledge subscription for an agent
        
        Args:
            agent_id: Agent creating subscription
            categories: Categories to subscribe to
            tags: Tags to filter by
            filters: Additional filters
            
        Returns:
            Subscription ID
        """
        try:
            subscription_id = str(uuid.uuid4())
            
            subscription = KnowledgeSubscriptionModel(
                subscription_id=subscription_id,
                agent_id=agent_id,
                categories=categories,
                tags=tags,
                filters=filters or {},
                delivery_method="push",
                frequency="immediate",
                active=True,
                created_at=datetime.utcnow()
            )
            
            self.db.add(subscription)
            await self.db.commit()
            
            # Track active subscription
            for category in categories:
                self.active_subscriptions[category].add(agent_id)
            
            self.flow_metrics['subscriptions_active'] += 1
            
            logger.info("Knowledge subscription created",
                       subscription_id=subscription_id,
                       agent_id=agent_id,
                       categories=categories)
            
            return subscription_id
            
        except Exception as e:
            logger.error("Failed to create subscription", error=str(e))
            raise
    
    async def update_subscription(
        self,
        subscription_id: str,
        categories: Optional[List[KnowledgeCategory]] = None,
        tags: Optional[List[str]] = None,
        active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update an existing subscription"""
        try:
            stmt = select(KnowledgeSubscriptionModel).where(
                KnowledgeSubscriptionModel.subscription_id == subscription_id
            )
            result = await self.db.execute(stmt)
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")
            
            # Update fields
            if categories is not None:
                # Remove from old categories
                for cat in subscription.categories:
                    self.active_subscriptions[cat].discard(subscription.agent_id)
                
                subscription.categories = categories
                
                # Add to new categories
                for cat in categories:
                    self.active_subscriptions[cat].add(subscription.agent_id)
            
            if tags is not None:
                subscription.tags = tags
            
            if active is not None:
                subscription.active = active
                if not active:
                    for cat in subscription.categories:
                        self.active_subscriptions[cat].discard(subscription.agent_id)
                    self.flow_metrics['subscriptions_active'] -= 1
            
            await self.db.commit()
            
            logger.info("Subscription updated", subscription_id=subscription_id)
            
            return {
                "status": "updated",
                "subscription_id": subscription_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to update subscription", error=str(e))
            raise
    
    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a knowledge subscription"""
        try:
            return await self.update_subscription(subscription_id, active=False)
            
        except Exception as e:
            logger.error("Failed to cancel subscription", error=str(e))
            raise
    
    async def get_agent_subscriptions(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all subscriptions for an agent"""
        try:
            stmt = select(KnowledgeSubscriptionModel).where(
                and_(
                    KnowledgeSubscriptionModel.agent_id == agent_id,
                    KnowledgeSubscriptionModel.active == True
                )
            )
            result = await self.db.execute(stmt)
            subscriptions = result.scalars().all()
            
            return [
                {
                    "subscription_id": s.subscription_id,
                    "categories": s.categories,
                    "tags": s.tags,
                    "delivery_method": s.delivery_method,
                    "frequency": s.frequency,
                    "created_at": s.created_at.isoformat()
                }
                for s in subscriptions
            ]
            
        except Exception as e:
            logger.error("Failed to get subscriptions", error=str(e))
            return []
    
    async def notify_subscribers(
        self,
        category: KnowledgeCategory,
        knowledge_id: str,
        knowledge_data: Dict[str, Any]
    ):
        """Notify subscribed agents about new knowledge"""
        try:
            subscribers = self.active_subscriptions.get(category, set())
            
            if not subscribers:
                return
            
            # Get subscription details for filtering
            stmt = select(KnowledgeSubscriptionModel).where(
                and_(
                    KnowledgeSubscriptionModel.agent_id.in_(subscribers),
                    KnowledgeSubscriptionModel.active == True
                )
            )
            result = await self.db.execute(stmt)
            subscriptions = result.scalars().all()
            
            # Send notifications
            for subscription in subscriptions:
                # Check if knowledge matches subscription filters
                if self._matches_subscription(knowledge_data, subscription):
                    await self._send_knowledge_notification(
                        subscription.agent_id,
                        knowledge_id,
                        knowledge_data,
                        subscription.delivery_method
                    )
            
            self.flow_metrics['knowledge_shared'] += len(subscriptions)
            
            logger.info(f"Notified {len(subscriptions)} subscribers",
                       category=category,
                       knowledge_id=knowledge_id)
            
        except Exception as e:
            logger.error("Failed to notify subscribers", error=str(e))
    
    async def request_knowledge_flow(
        self,
        source_agent_id: str,
        target_agent_ids: List[str],
        knowledge_query: str,
        urgency: str = "normal"
    ) -> Dict[str, Any]:
        """Request knowledge flow between agents"""
        try:
            flow_id = str(uuid.uuid4())
            
            # Get relevant knowledge
            knowledge = await self.learning_agent.retrieve_knowledge(
                query=knowledge_query,
                limit=10
            )
            
            if not knowledge:
                return {
                    "status": "no_knowledge_found",
                    "flow_id": flow_id,
                    "query": knowledge_query
                }
            
            # Send to target agents
            for target_id in target_agent_ids:
                await self.broker.publish(
                    f"agent.{target_id}.knowledge_delivery",
                    {
                        "flow_id": flow_id,
                        "source_agent": source_agent_id,
                        "knowledge": knowledge,
                        "query": knowledge_query,
                        "urgency": urgency,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            self.flow_metrics['requests_fulfilled'] += 1
            
            logger.info("Knowledge flow initiated",
                       flow_id=flow_id,
                       targets=len(target_agent_ids))
            
            return {
                "status": "delivered",
                "flow_id": flow_id,
                "knowledge_count": len(knowledge),
                "target_agents": len(target_agent_ids),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to request knowledge flow", error=str(e))
            raise
    
    async def broadcast_knowledge(
        self,
        knowledge_id: str,
        knowledge_data: Dict[str, Any],
        target_categories: List[str],
        exclude_agents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Broadcast knowledge to all relevant agents"""
        try:
            # Get all active agents (would integrate with agent manager)
            # For now, broadcast to all subscribed agents
            
            notified = 0
            for category in target_categories:
                subscribers = self.active_subscriptions.get(category, set())
                
                if exclude_agents:
                    subscribers = subscribers - set(exclude_agents)
                
                for agent_id in subscribers:
                    await self._send_knowledge_notification(
                        agent_id,
                        knowledge_id,
                        knowledge_data,
                        "broadcast"
                    )
                    notified += 1
            
            logger.info(f"Knowledge broadcast to {notified} agents",
                       knowledge_id=knowledge_id)
            
            return {
                "status": "broadcast",
                "knowledge_id": knowledge_id,
                "agents_notified": notified,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to broadcast knowledge", error=str(e))
            raise
    
    async def get_flow_metrics(self) -> Dict[str, Any]:
        """Get knowledge flow metrics"""
        return {
            **self.flow_metrics,
            "active_subscriptions_count": sum(
                len(agents) for agents in self.active_subscriptions.values()
            ),
            "categories_with_subscribers": len(self.active_subscriptions),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Helper Methods
    
    async def _load_subscriptions(self):
        """Load existing subscriptions from database"""
        try:
            stmt = select(KnowledgeSubscriptionModel).where(
                KnowledgeSubscriptionModel.active == True
            )
            result = await self.db.execute(stmt)
            subscriptions = result.scalars().all()
            
            for subscription in subscriptions:
                for category in subscription.categories:
                    self.active_subscriptions[category].add(subscription.agent_id)
            
            self.flow_metrics['subscriptions_active'] = len(subscriptions)
            
            logger.info(f"Loaded {len(subscriptions)} active subscriptions")
            
        except Exception as e:
            logger.error("Failed to load subscriptions", error=str(e))
    
    async def _setup_channels(self):
        """Setup message broker channels for knowledge flow"""
        try:
            # Subscribe to knowledge request channel
            await self.broker.subscribe(
                "knowledge.request",
                self._handle_knowledge_request
            )
            
            # Subscribe to knowledge sharing channel
            await self.broker.subscribe(
                "knowledge.share",
                self._handle_knowledge_share
            )
            
            logger.info("Knowledge flow channels setup complete")
            
        except Exception as e:
            logger.error("Failed to setup channels", error=str(e))
    
    async def _handle_knowledge_request(self, message: Dict[str, Any]):
        """Handle incoming knowledge request"""
        try:
            agent_id = message.get('agent_id')
            query = message.get('query')
            urgency = message.get('urgency', 'normal')
            
            # Process through learning agent
            await self.learning_agent.request_knowledge(agent_id, query, urgency)
            
        except Exception as e:
            logger.error("Failed to handle knowledge request", error=str(e))
    
    async def _handle_knowledge_share(self, message: Dict[str, Any]):
        """Handle knowledge sharing between agents"""
        try:
            source_agent = message.get('source_agent_id')
            target_agents = message.get('target_agent_ids', [])
            knowledge_ids = message.get('knowledge_ids', [])
            
            await self.learning_agent.share_knowledge(
                source_agent,
                target_agents,
                knowledge_ids
            )
            
        except Exception as e:
            logger.error("Failed to handle knowledge share", error=str(e))
    
    def _matches_subscription(
        self,
        knowledge_data: Dict[str, Any],
        subscription: KnowledgeSubscriptionModel
    ) -> bool:
        """Check if knowledge matches subscription criteria"""
        # Check tags
        if subscription.tags:
            knowledge_tags = knowledge_data.get('tags', [])
            if not any(tag in knowledge_tags for tag in subscription.tags):
                return False
        
        # Check additional filters
        if subscription.filters:
            for key, value in subscription.filters.items():
                if knowledge_data.get(key) != value:
                    return False
        
        return True
    
    async def _send_knowledge_notification(
        self,
        agent_id: str,
        knowledge_id: str,
        knowledge_data: Dict[str, Any],
        delivery_method: str
    ):
        """Send knowledge notification to an agent"""
        try:
            # Prepare notification payload
            payload = {
                "notification_type": "new_knowledge",
                "knowledge_id": knowledge_id,
                "title": knowledge_data.get('title', 'New Knowledge Available'),
                "category": knowledge_data.get('category'),
                "summary": knowledge_data.get('summary', ''),
                "delivery_method": delivery_method,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send via message broker
            await self.broker.publish(
                f"agent.{agent_id}.notifications",
                payload
            )
            
        except Exception as e:
            logger.error("Failed to send notification", 
                        agent_id=agent_id,
                        error=str(e))
