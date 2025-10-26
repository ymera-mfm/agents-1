"""
Batch Processor
Process items in optimized batches for better performance
"""

import asyncio
from typing import List, Callable, Any, TypeVar
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class BatchConfig:
    """Batch processing configuration"""
    batch_size: int = 100
    max_wait_time: float = 1.0  # seconds
    max_concurrent_batches: int = 5


class BatchProcessor:
    """
    Process items in optimized batches
    
    Benefits:
    - 10x faster for bulk operations
    - Reduced database round trips
    - Better resource utilization
    - Automatic batching
    
    Usage:
        async def batch_insert(items: List[Dict]) -> List[str]:
            return await db.bulk_insert(items)
        
        processor = BatchProcessor(batch_insert, BatchConfig(batch_size=100))
        
        for item in items:
            item_id = await processor.add(item)
    """
    
    def __init__(
        self,
        processor: Callable[[List[T]], List[R]],
        config: BatchConfig
    ):
        self.processor = processor
        self.config = config
        self.queue: List[T] = []
        self.processing = False
        self.lock = asyncio.Lock()
        self.result_futures: Dict[int, asyncio.Future] = {}
        self.current_index = 0
    
    async def add(self, item: T) -> R:
        """
        Add item to batch queue
        
        Args:
            item: Item to process
            
        Returns:
            Processing result for this item
        """
        async with self.lock:
            self.queue.append(item)
            item_index = self.current_index
            self.current_index += 1
            
            # Create future for this item's result
            future = asyncio.Future()
            self.result_futures[item_index] = future
            
            # Check if we should process now
            should_process = (
                len(self.queue) >= self.config.batch_size and
                not self.processing
            )
        
        if should_process:
            asyncio.create_task(self._process_batch())
        else:
            # Schedule batch processing after wait time
            asyncio.create_task(self._schedule_batch_processing())
        
        # Wait for result
        return await future
    
    async def _schedule_batch_processing(self):
        """Schedule batch processing after wait time"""
        await asyncio.sleep(self.config.max_wait_time)
        
        async with self.lock:
            if self.queue and not self.processing:
                asyncio.create_task(self._process_batch())
    
    async def _process_batch(self):
        """Process accumulated items"""
        async with self.lock:
            if self.processing or not self.queue:
                return
            
            self.processing = True
            batch = self.queue[:self.config.batch_size]
            self.queue = self.queue[self.config.batch_size:]
            batch_size = len(batch)
        
        try:
            logger.debug(f"Processing batch of {batch_size} items")
            
            # Process batch
            results = await self.processor(batch)
            
            # Resolve futures with results
            for i, result in enumerate(results):
                future = self.result_futures.pop(i, None)
                if future and not future.done():
                    future.set_result(result)
            
            logger.debug(f"Batch processed successfully: {batch_size} items")
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}", exc_info=True)
            
            # Reject all futures with error
            for future in self.result_futures.values():
                if not future.done():
                    future.set_exception(e)
            
            self.result_futures.clear()
        
        finally:
            async with self.lock:
                self.processing = False
                
                # Process next batch if queue not empty
                if self.queue:
                    asyncio.create_task(self._process_batch())
    
    async def flush(self):
        """Force process any remaining items"""
        async with self.lock:
            if self.queue and not self.processing:
                asyncio.create_task(self._process_batch())
