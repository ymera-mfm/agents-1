"""Graceful Shutdown Handler"""

import asyncio
import signal
from typing import Optional
import structlog


class GracefulShutdown:
    """Handles graceful shutdown of the application"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self._is_shutting_down = False
        self._shutdown_event = asyncio.Event()
    
    def initiate_shutdown(self):
        """Initiate graceful shutdown"""
        if not self._is_shutting_down:
            self.logger.info("Initiating graceful shutdown...")
            self._is_shutting_down = True
            self._shutdown_event.set()
    
    async def wait_for_shutdown(self, timeout: int = 30):
        """Wait for shutdown to complete"""
        try:
            await asyncio.wait_for(self._shutdown_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"Shutdown timeout after {timeout} seconds")
    
    @property
    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress"""
        return self._is_shutting_down
