
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging
from uuid import UUID, uuid4

try:
    from database import Database
except ImportError:
    Database = None

try:
    from models import Experience, KnowledgeItem
except ImportError:
    Experience = None
    KnowledgeItem = None

try:
    from ml_pipeline import MLPipeline
except ImportError:
    MLPipeline = None

try:
    from knowledge_manager import KnowledgeManager
except ImportError:
    KnowledgeManager = None

logger = logging.getLogger(__name__)

class YmeraAgent:
    def __init__(self, database: Database, settings):
        self.database = database
        self.settings = settings
        self.ml_pipeline = MLPipeline(settings)
        self.knowledge_manager = KnowledgeManager(database)
        self.is_initialized = False
        self.background_tasks = []
    
    async def initialize(self):
        """Initialize agent components"""
        try:
            await self.ml_pipeline.initialize()
            await self.knowledge_manager.initialize()
            
            # Start background tasks
            self.background_tasks.extend([
                asyncio.create_task(self._experience_processing_loop()),
                asyncio.create_task(self._knowledge_update_loop()),
                asyncio.create_task(self._metrics_collection_loop())
            ])
            
            self.is_initialized = True
            logger.info("Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}")
            raise
    
    async def process_message(self, user_id: UUID, message: str, 
                            conversation_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Process incoming message and generate response"""
        if not self.is_initialized:
            raise RuntimeError("Agent not initialized")
        
        conversation_id = conversation_id or uuid4()
        
        try:
            # Create experience record
            experience = Experience(
                user_id=user_id,
                conversation_id=conversation_id,
                input_data={"message": message, "timestamp": datetime.utcnow().isoformat()},
                metadata={"source": "chat"}
            )
            
            # Get relevant knowledge
            relevant_knowledge = await self.knowledge_manager.search_knowledge(
                message, limit=5
            )
            
            # Generate response using ML pipeline
            response_data = await self.ml_pipeline.generate_response(
                message=message,
                context=relevant_knowledge,
                conversation_history=await self._get_conversation_history(conversation_id)
            )
            
            # Update experience with response
            experience.output_data = response_data
            
            # Store experience
            await self._store_experience(experience)
            
            return {
                "response": response_data.get("response", "I understand your message."),
                "conversation_id": str(conversation_id),
                "confidence": response_data.get("confidence", 0.8),
                "suggestions": response_data.get("suggestions", []),
                "context_used": response_data.get("context_used", False)
            }
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return {
                "response": "I\"m having trouble processing your message right now. Please try again.",
                "conversation_id": str(conversation_id),
                "confidence": 0.0,
                "error": True
            }
    
    async def provide_feedback(self, experience_id: UUID, score: int, 
                              comment: Optional[str] = None) -> bool:
        """Provide feedback on agent response"""
        try:
            query = """
                UPDATE agent_experiences 
                SET feedback_score = $1, 
                    metadata = metadata || $2,
                    updated_at = NOW()
                WHERE id = $3
            """
            
            metadata_update = {"feedback_comment": comment} if comment else {}
            
            await self.database.execute_command(
                query, score, json.dumps(metadata_update), experience_id
            )
            
            # Trigger learning update
            asyncio.create_task(self._trigger_learning_update())
            
            return True
            
        except Exception as e:
            logger.error(f"Feedback storage failed: {e}")
            return False
    
    async def _store_experience(self, experience: Experience):
        """Store experience in database"""
        query = """
            INSERT INTO agent_experiences (user_id, conversation_id, input_data, 
                                         output_data, metadata)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """
        
        result = await self.database.execute_single(
            query,
            experience.user_id,
            experience.conversation_id,
            json.dumps(experience.input_data),
            json.dumps(experience.output_data) if experience.output_data else None,
            json.dumps(experience.metadata)
        )
        
        return result["id"] if result else None
    
    async def _get_conversation_history(self, conversation_id: UUID, 
                                       limit: int = None) -> List[Dict]:
        """Get conversation history"""
        limit = limit or self.settings.max_conversation_history
        
        query = """
            SELECT input_data, output_data, created_at
            FROM agent_experiences
            WHERE conversation_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        
        results = await self.database.execute_query(query, conversation_id, limit)
        return list(reversed(results))  # Return in chronological order
    
    async def get_user_conversations(self, user_id: UUID, limit: int = 20) -> List[Dict]:
        """Get distinct conversation IDs for a user"""
        query = """
            SELECT DISTINCT conversation_id, MAX(created_at) as last_message_at
            FROM agent_experiences
            WHERE user_id = $1
            GROUP BY conversation_id
            ORDER BY last_message_at DESC
            LIMIT $2
        """
        results = await self.database.execute_query(query, user_id, limit)
        return results

    async def _experience_processing_loop(self):
        """Background loop to process unprocessed experiences"""
        while True:
            try:
                # Get unprocessed experiences
                experiences = await self._get_unprocessed_experiences()
                
                if experiences:
                    await self.ml_pipeline.batch_process_experiences(experiences)
                    await self._mark_experiences_processed([exp["id"] for exp in experiences])
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Experience processing loop failed: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _get_unprocessed_experiences(self) -> List[Dict]:
        """Retrieve unprocessed experiences from the database"""
        query = """
            SELECT id, user_id, conversation_id, input_data, output_data, feedback_score, metadata
            FROM agent_experiences
            WHERE processed = FALSE
            LIMIT $1
        """
        return await self.database.execute_query(query, self.settings.learning_batch_size)

    async def _mark_experiences_processed(self, experience_ids: List[UUID]):
        """Mark experiences as processed in the database"""
        if not experience_ids:
            return
        query = """
            UPDATE agent_experiences
            SET processed = TRUE, updated_at = NOW()
            WHERE id = ANY($1)
        """
        await self.database.execute_command(query, experience_ids)

    async def _trigger_learning_update(self):
        """Trigger an immediate learning update (e.g., after feedback)"""
        logger.info("Triggering immediate learning update...")
        # In a real system, this might enqueue a task for the ML pipeline
        # For now, we'll just log it.

    async def _knowledge_update_loop(self):
        """Background loop to update knowledge base"""
        while True:
            try:
                await self.knowledge_manager.update_knowledge_scores()
                await asyncio.sleep(self.settings.model_update_interval)  # Update every hour
                
            except Exception as e:
                logger.error(f"Knowledge update loop failed: {e}")
                await asyncio.sleep(self.settings.model_update_interval / 2)  # Wait half interval on error
    
    async def _metrics_collection_loop(self):
        """Background loop to collect and store metrics"""
        while True:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(300)  # Collect every 5 minutes
                
            except Exception as e:
                logger.error(f"Metrics collection loop failed: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error
    
    async def _collect_system_metrics(self):
        """Collect and store system metrics (placeholder)"""
        # In a real system, this would collect CPU, memory, network, etc.
        # and store them in the system_metrics table.
        logger.debug("Collecting system metrics...")
        # Example: await self.database.execute_command(
        #     "INSERT INTO system_metrics (metric_name, metric_value, labels) VALUES ($1, $2, $3)",
        #     "cpu_usage", 0.5, json.dumps({"host": "agent-01"})
        # )

    async def health_check(self) -> bool:
        """Check agent health"""
        try:
            # Basic checks
            if not self.is_initialized:
                return False
            
            # Check components
            ml_healthy = await self.ml_pipeline.health_check()
            knowledge_healthy = await self.knowledge_manager.health_check()
            
            return ml_healthy and knowledge_healthy
            
        except Exception as e:
            logger.error(f"Agent health check failed: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown agent gracefully"""
        logger.info("Shutting down agent...")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Shutdown components
        await self.ml_pipeline.shutdown()
        await self.knowledge_manager.shutdown()
        
        logger.info("Agent shutdown complete")

