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
from alpha.proactive import PatternLearner, TaskDetector, Notifier

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
        self.proactive_task: Optional[asyncio.Task] = None

        # Core components
        self.event_bus = EventBus()
        self.task_manager = TaskManager(self.event_bus)
        self.memory_manager = MemoryManager(config.memory.database)

        # Proactive Intelligence components (REQ-6.1.1)
        proactive_enabled = getattr(config, 'proactive', {}).get('enabled', False)
        if proactive_enabled:
            proactive_db = getattr(config, 'proactive', {}).get('database', 'data/alpha_proactive.db')
            pattern_config = getattr(config, 'proactive', {}).get('pattern_learning', {})
            task_config = getattr(config, 'proactive', {}).get('task_detection', {})

            self.pattern_learner = PatternLearner(
                database_path=proactive_db,
                min_pattern_frequency=pattern_config.get('min_frequency', 3),
                min_confidence=pattern_config.get('min_confidence', 0.6)
            )
            self.task_detector = TaskDetector(
                pattern_learner=self.pattern_learner,
                min_confidence=task_config.get('min_confidence', 0.7),
                max_suggestions_per_run=task_config.get('max_suggestions', 5)
            )
            self.notifier = Notifier()
            logger.info("Proactive intelligence components initialized")
        else:
            self.pattern_learner = None
            self.task_detector = None
            self.notifier = None
            logger.info("Proactive intelligence disabled in config")

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

            # Initialize proactive intelligence (REQ-6.1.1)
            if self.pattern_learner:
                await self.pattern_learner.initialize()
                logger.info("Pattern learner initialized")

                # Start background proactive loop
                self.proactive_task = asyncio.create_task(self._proactive_loop())
                logger.info("Proactive intelligence loop started")

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
            # Cancel proactive loop (REQ-6.1.1)
            if self.proactive_task and not self.proactive_task.done():
                self.proactive_task.cancel()
                try:
                    await self.proactive_task
                except asyncio.CancelledError:
                    logger.info("Proactive loop cancelled")

            # Close proactive components
            if self.pattern_learner:
                await self.pattern_learner.close()
                logger.info("Pattern learner closed")

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

        health = {
            "status": "running" if self.running else "stopped",
            "uptime": str(uptime),
            "tasks": await self.task_manager.get_stats(),
            "memory": await self.memory_manager.get_stats(),
        }

        # Add proactive intelligence status
        if self.pattern_learner:
            health["proactive"] = {
                "enabled": True,
                "pattern_count": len(await self.pattern_learner.get_patterns()),
                "loop_running": self.proactive_task and not self.proactive_task.done()
            }

        return health

    async def _proactive_loop(self):
        """Background loop for proactive task detection (REQ-6.1.3)."""
        logger.info("Proactive loop started")

        proactive_config = getattr(self.config, 'proactive', {})
        check_interval = proactive_config.get('task_detection', {}).get('check_interval', 60)
        auto_execute_enabled = proactive_config.get('auto_execute', {}).get('enabled', False)
        auto_execute_threshold = proactive_config.get('auto_execute', {}).get('min_confidence', 0.9)

        # Pattern learning settings
        pattern_learning_interval = 3600  # Learn patterns every hour
        last_pattern_learning = datetime.now()

        while self.running:
            try:
                # Periodic pattern learning from conversation history (REQ-6.1.2)
                time_since_learning = (datetime.now() - last_pattern_learning).total_seconds()
                if time_since_learning >= pattern_learning_interval:
                    await self._learn_patterns_from_history()
                    last_pattern_learning = datetime.now()

                # Detect task opportunities
                context = await self._get_current_context()
                suggestions = await self.task_detector.detect_proactive_tasks(context=context)

                # Process suggestions
                for suggestion in suggestions:
                    logger.info(f"Proactive suggestion: {suggestion.task_name} (confidence: {suggestion.confidence:.2f})")

                    # Auto-execute if enabled and meets threshold
                    if auto_execute_enabled and suggestion.confidence >= auto_execute_threshold:
                        await self._execute_safe_proactive_task(suggestion)
                    # Otherwise, queue for user notification
                    elif suggestion.confidence >= 0.7:
                        await self._notify_proactive_suggestion(suggestion)

            except asyncio.CancelledError:
                logger.info("Proactive loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in proactive loop: {e}", exc_info=True)

            # Sleep until next check
            await asyncio.sleep(check_interval)

    async def _learn_patterns_from_history(self):
        """Learn patterns from conversation history (REQ-6.1.2)."""
        try:
            logger.info("Learning patterns from conversation history...")

            # Get recent conversation history
            conversations = await self.memory_manager.get_conversation_history(limit=500)

            if len(conversations) < 5:
                logger.info("Not enough conversation history for pattern learning")
                return

            # Analyze and learn patterns
            patterns = await self.pattern_learner.analyze_conversation_history(
                conversations=conversations,
                lookback_days=30
            )

            # Log learned patterns
            pattern_count = sum(len(p) for p in patterns.values())
            logger.info(f"Pattern learning complete: {pattern_count} patterns detected")

            if pattern_count > 0:
                # Store patterns summary in memory for tracking
                await self.memory_manager.add_system_event(
                    "pattern_learning",
                    {
                        "patterns_detected": pattern_count,
                        "pattern_types": {k: len(v) for k, v in patterns.items()},
                        "timestamp": datetime.now().isoformat()
                    }
                )

        except Exception as e:
            logger.error(f"Pattern learning failed: {e}", exc_info=True)

    async def _get_current_context(self) -> dict:
        """Get current context for proactive task detection."""
        stats = await self.task_manager.get_stats()
        return {
            "current_time": datetime.now(),
            "running_tasks": stats.get("running", 0),
            "total_tasks": stats.get("total", 0),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }

    async def _execute_safe_proactive_task(self, suggestion):
        """Auto-execute a safe proactive task (REQ-6.1.4)."""
        logger.info(f"Auto-executing proactive task: {suggestion.task_name}")

        try:
            # Create task through task manager
            task = await self.task_manager.create_task(
                name=suggestion.task_name,
                description=suggestion.description,
                metadata=suggestion.task_params
            )

            # Log auto-execution
            await self.memory_manager.add_system_event(
                "proactive_execution",
                {
                    "suggestion_id": suggestion.suggestion_id,
                    "task_id": task.id,
                    "confidence": suggestion.confidence,
                    "auto_executed": True
                }
            )

        except Exception as e:
            logger.error(f"Failed to auto-execute proactive task: {e}", exc_info=True)

    async def _notify_proactive_suggestion(self, suggestion):
        """Notify user about proactive task suggestion."""
        try:
            await self.notifier.notify(
                title="Proactive Task Suggestion",
                message=f"{suggestion.task_name}: {suggestion.justification}",
                priority="normal",
                notification_type="suggestion",
                metadata={
                    "suggestion_id": suggestion.suggestion_id,
                    "confidence": suggestion.confidence
                }
            )

            # Log notification
            await self.memory_manager.add_system_event(
                "proactive_suggestion",
                {
                    "suggestion_id": suggestion.suggestion_id,
                    "task_name": suggestion.task_name,
                    "confidence": suggestion.confidence
                }
            )

        except Exception as e:
            logger.error(f"Failed to send proactive notification: {e}", exc_info=True)
