"""
Alpha AI Assistant - Core Engine

Main runtime engine for 24/7 continuous operation.
"""

import asyncio
import logging
import signal
from typing import Optional
from datetime import datetime

from alpha.events.bus import EventBus
from alpha.tasks.manager import TaskManager
from alpha.memory.manager import MemoryManager
from alpha.utils.config import Config

logger = logging.getLogger(__name__)


class AlphaEngine:
    """
    Core engine orchestrating all Alpha components.

    Responsibilities:
    - Lifecycle management (startup, running, shutdown)
    - Component coordination
    - Error recovery
    - Health monitoring
    """

    def __init__(self, config: Config):
        self.config = config
        self.running = False
        self.start_time: Optional[datetime] = None

        # Core components
        self.event_bus = EventBus()
        self.task_manager = TaskManager(self.event_bus)
        self.memory_manager = MemoryManager(config.memory.database)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)
        signal.signal(signal.SIGTERM, self._handle_shutdown_signal)

    def _handle_shutdown_signal(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received shutdown signal: {signum}")
        asyncio.create_task(self.shutdown())

    async def startup(self):
        """Initialize all components and start the engine."""
        logger.info("Starting Alpha AI Assistant...")
        self.start_time = datetime.now()

        try:
            # Initialize memory system
            await self.memory_manager.initialize()
            logger.info("Memory system initialized")

            # Initialize task manager
            await self.task_manager.initialize()
            logger.info("Task manager initialized")

            # Initialize event bus
            await self.event_bus.initialize()
            logger.info("Event bus initialized")

            self.running = True
            logger.info("Alpha started successfully")

            # Record startup in memory
            await self.memory_manager.add_system_event(
                "startup",
                {"timestamp": self.start_time.isoformat()}
            )

        except Exception as e:
            logger.error(f"Failed to start Alpha: {e}", exc_info=True)
            raise

    async def run(self):
        """Main event loop - runs continuously."""
        if not self.running:
            raise RuntimeError("Engine not started. Call startup() first.")

        logger.info("Entering main event loop...")

        try:
            while self.running:
                # Main loop iteration
                await self._process_cycle()

                # Brief sleep to prevent CPU spinning
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            # Attempt recovery
            await self._recover_from_error(e)

    async def _process_cycle(self):
        """Single processing cycle."""
        # Process pending events
        await self.event_bus.process_pending()

        # Update task statuses
        await self.task_manager.update_tasks()

        # Check for scheduled tasks
        await self.task_manager.check_scheduled()

    async def _recover_from_error(self, error: Exception):
        """Attempt to recover from errors."""
        logger.info("Attempting error recovery...")

        try:
            # Log error to memory
            await self.memory_manager.add_system_event(
                "error",
                {
                    "error": str(error),
                    "type": type(error).__name__
                }
            )

            # Reset components if needed
            await self.task_manager.reset()

            logger.info("Recovery successful")

        except Exception as recovery_error:
            logger.error(f"Recovery failed: {recovery_error}")
            # If recovery fails, initiate shutdown
            await self.shutdown()

    async def shutdown(self):
        """Graceful shutdown of all components."""
        logger.info("Shutting down Alpha...")
        self.running = False

        try:
            # Cancel all running tasks
            await self.task_manager.cancel_all()

            # Close event bus
            await self.event_bus.close()

            # Close memory system
            await self.memory_manager.close()

            # Record shutdown
            uptime = datetime.now() - self.start_time if self.start_time else None
            logger.info(f"Alpha shut down successfully. Uptime: {uptime}")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

    async def health_check(self) -> dict:
        """Return current health status."""
        uptime = datetime.now() - self.start_time if self.start_time else None

        return {
            "status": "running" if self.running else "stopped",
            "uptime": str(uptime),
            "tasks": await self.task_manager.get_stats(),
            "memory": await self.memory_manager.get_stats(),
        }
