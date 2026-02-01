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
from alpha.workflow import (
    WorkflowPatternDetector,
    WorkflowSuggestionGenerator,
    WorkflowOptimizer,
    WorkflowLibrary
)
from alpha.learning import (
    FeedbackLoop,
    FeedbackLoopConfig,
    FeedbackLoopMode,
    LogAnalyzer,
    ImprovementExecutor,
    LearningStore
)

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

            # Workflow Intelligence components (REQ-6.2.5)
            workflow_config = proactive_config.get('workflow_detection', {})
            if workflow_config.get('enabled', True):
                self.workflow_pattern_detector = WorkflowPatternDetector(
                    memory_store=self.memory_manager,
                    min_frequency=workflow_config.get('min_pattern_frequency', 3),
                    min_confidence=workflow_config.get('min_confidence', 0.7),
                    lookback_days=workflow_config.get('lookback_days', 30)
                )
                self.workflow_suggestion_generator = WorkflowSuggestionGenerator(
                    pattern_detector=self.workflow_pattern_detector,
                    memory_store=self.memory_manager
                )

                # Initialize workflow library with default path
                workflow_db = proactive_config.get('workflow_database', 'data/alpha_workflows.db')
                self.workflow_library = WorkflowLibrary(database_path=workflow_db)

                self.workflow_optimizer = WorkflowOptimizer()
                logger.info("Workflow intelligence components initialized")
            else:
                self.workflow_pattern_detector = None
                self.workflow_suggestion_generator = None
                self.workflow_library = None
                self.workflow_optimizer = None
                logger.info("Workflow intelligence disabled in config")
        else:
            self.pattern_learner = None
            self.task_detector = None
            self.notifier = None
            self.workflow_pattern_detector = None
            self.workflow_suggestion_generator = None
            self.workflow_library = None
            self.workflow_optimizer = None
            logger.info("Proactive intelligence disabled in config")

        # Self-Improvement Loop components (REQ-5.1.5)
        self.improvement_task: Optional[asyncio.Task] = None
        improvement_enabled = getattr(config, 'improvement_loop', {}).get('enabled', False)
        if improvement_enabled:
            improvement_db = getattr(config, 'improvement_loop', {}).get('database', 'data/alpha_learning.db')
            loop_config_dict = getattr(config, 'improvement_loop', {}).get('config', {})

            # Parse feedback loop mode
            mode_str = loop_config_dict.get('mode', 'semi_auto')
            mode = FeedbackLoopMode(mode_str)

            # Create FeedbackLoopConfig
            loop_config = FeedbackLoopConfig(
                mode=mode,
                analysis_frequency=loop_config_dict.get('analysis_frequency', 'daily'),
                analysis_days=loop_config_dict.get('analysis_days', 7),
                min_confidence=loop_config_dict.get('min_confidence', 0.7),
                max_daily_improvements=loop_config_dict.get('max_daily_improvements', 5),
                enable_rollback=loop_config_dict.get('enable_rollback', True),
                dry_run_first=loop_config_dict.get('dry_run_first', True)
            )

            # Initialize feedback loop components
            self.learning_store = LearningStore(database_path=improvement_db)
            self.log_analyzer = LogAnalyzer(learning_store=self.learning_store)
            self.improvement_executor = ImprovementExecutor(
                config_path=getattr(config, 'config_file', 'config.yaml'),
                learning_store=self.learning_store
            )
            self.feedback_loop = FeedbackLoop(
                config=loop_config,
                log_analyzer=self.log_analyzer,
                improvement_executor=self.improvement_executor,
                learning_store=self.learning_store,
                scheduler=None  # Will use background loop instead
            )
            logger.info("Self-improvement loop components initialized")
        else:
            self.feedback_loop = None
            self.learning_store = None
            self.log_analyzer = None
            self.improvement_executor = None
            logger.info("Self-improvement loop disabled in config")

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

            # Initialize self-improvement loop (REQ-5.1.5)
            if self.feedback_loop:
                await self.feedback_loop.start()
                logger.info("Self-improvement feedback loop initialized")

                # Start background improvement loop
                self.improvement_task = asyncio.create_task(self._improvement_loop())
                logger.info("Self-improvement loop started")

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

            # Cancel improvement loop (REQ-5.1.5)
            if self.improvement_task and not self.improvement_task.done():
                self.improvement_task.cancel()
                try:
                    await self.improvement_task
                except asyncio.CancelledError:
                    logger.info("Improvement loop cancelled")

            # Close self-improvement components
            if self.feedback_loop:
                await self.feedback_loop.stop()
                logger.info("Self-improvement feedback loop stopped")

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

        # Add self-improvement status
        if self.feedback_loop:
            health["self_improvement"] = {
                "enabled": True,
                "loop_running": self.improvement_task and not self.improvement_task.done(),
                "cycle_count": getattr(self.feedback_loop, 'cycle_count', 0),
                "last_cycle": getattr(self.feedback_loop, 'last_cycle_time', None)
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

        # Workflow detection settings (REQ-6.2.5)
        workflow_detection_interval = proactive_config.get('workflow_detection', {}).get('analysis_interval', 3600)
        last_workflow_detection = datetime.now()
        workflow_optimization_interval = proactive_config.get('workflow_optimization', {}).get('analysis_interval', 86400)
        last_workflow_optimization = datetime.now()

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

                # Workflow pattern detection (REQ-6.2.5)
                if self.workflow_pattern_detector:
                    time_since_workflow_detection = (datetime.now() - last_workflow_detection).total_seconds()
                    if time_since_workflow_detection >= workflow_detection_interval:
                        await self._detect_workflow_patterns()
                        last_workflow_detection = datetime.now()

                # Workflow optimization analysis (REQ-6.2.5)
                if self.workflow_optimizer and self.workflow_library:
                    time_since_optimization = (datetime.now() - last_workflow_optimization).total_seconds()
                    if time_since_optimization >= workflow_optimization_interval:
                        await self._analyze_workflow_optimizations()
                        last_workflow_optimization = datetime.now()

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

    async def _improvement_loop(self):
        """
        Background loop for continuous self-improvement (REQ-5.1.5).

        This loop periodically runs the feedback cycle:
        1. Analyze execution logs for patterns
        2. Generate improvement recommendations
        3. Apply safe improvements automatically
        4. Track results and metrics
        """
        logger.info("Self-improvement loop started")

        improvement_config = getattr(self.config, 'improvement_loop', {})
        check_interval = improvement_config.get('check_interval', 86400)  # Default: daily (24 hours)
        min_uptime = improvement_config.get('min_uptime_for_analysis', 3600)  # 1 hour minimum uptime

        # Track last analysis time
        last_analysis = datetime.now()

        while self.running:
            try:
                # Calculate time since last analysis
                time_since_analysis = (datetime.now() - last_analysis).total_seconds()

                # Check if it's time for next analysis cycle
                if time_since_analysis >= check_interval:
                    # Ensure minimum uptime before analyzing
                    uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
                    if uptime < min_uptime:
                        logger.info(f"Skipping improvement cycle - uptime too short ({uptime:.0f}s < {min_uptime}s)")
                    else:
                        # Run feedback loop cycle
                        logger.info("Starting self-improvement cycle...")
                        cycle_result = await self.feedback_loop.run_cycle()

                        # Log cycle completion
                        logger.info(f"Self-improvement cycle complete: {cycle_result.get('summary', {})}")

                        # Record cycle in memory for tracking
                        await self.memory_manager.add_system_event(
                            "improvement_cycle",
                            {
                                "cycle_number": cycle_result.get('cycle_number'),
                                "patterns_found": cycle_result.get('steps', {}).get('analysis', {}).get('pattern_count', 0),
                                "improvements_applied": cycle_result.get('steps', {}).get('apply', {}).get('applied_count', 0),
                                "timestamp": datetime.now().isoformat()
                            }
        )

                        last_analysis = datetime.now()

            except asyncio.CancelledError:
                logger.info("Self-improvement loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in self-improvement loop: {e}", exc_info=True)

            # Sleep until next check
            await asyncio.sleep(min(check_interval, 3600))  # Check at least every hour

    async def _detect_workflow_patterns(self):
        """
        Detect workflow patterns from task execution history (REQ-6.2.5).
        
        Analyzes recent task sequences and generates workflow suggestions.
        """
        try:
            logger.info("Detecting workflow patterns...")
            
            # Detect patterns
            patterns = await self.workflow_pattern_detector.detect_workflow_patterns()
            
            if not patterns:
                logger.info("No workflow patterns detected")
                return
            
            logger.info(f"Detected {len(patterns)} workflow patterns")
            
            # Generate suggestions from patterns
            suggestions = await self.workflow_suggestion_generator.generate_workflow_suggestions(
                patterns=patterns,
                max_suggestions=5
            )
            
            if not suggestions:
                logger.info("No workflow suggestions generated")
                return
            
            logger.info(f"Generated {len(suggestions)} workflow suggestions")
            
            # Process suggestions
            proactive_config = getattr(self.config, 'proactive', {})
            workflow_config = proactive_config.get('workflow_detection', {})
            auto_create = workflow_config.get('auto_create_workflows', False)
            auto_create_threshold = workflow_config.get('min_confidence', 0.9)
            
            for suggestion in suggestions:
                # Auto-create high-confidence workflows if enabled
                if auto_create and suggestion.confidence >= auto_create_threshold:
                    try:
                        # Create workflow from suggestion
                        workflow_def = await self.workflow_suggestion_generator.create_workflow_from_pattern(
                            pattern=None,  # Pattern already in suggestion
                            suggestion=suggestion
                        )
                        
                        # Save to library
                        workflow_id = await self.workflow_library.save_workflow(workflow_def)
                        
                        logger.info(f"Auto-created workflow: {workflow_def.get('name')} (ID: {workflow_id})")
                        
                        # Log creation
                        await self.memory_manager.add_system_event(
                            "workflow_auto_created",
                            {
                                "workflow_id": workflow_id,
                                "pattern_id": suggestion.pattern_id,
                                "confidence": suggestion.confidence,
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to auto-create workflow: {e}", exc_info=True)
                
                # Notify user about high-confidence suggestions
                elif suggestion.confidence >= 0.7:
                    if self.notifier:
                        await self.notifier.notify(
                            title="Workflow Suggestion",
                            message=f"{suggestion.suggested_name}: {suggestion.description}",
                            priority="normal",
                            notification_type="workflow_suggestion",
                            metadata={
                                "suggestion_id": suggestion.suggestion_id,
                                "confidence": suggestion.confidence,
                                "pattern_id": suggestion.pattern_id
                            }
                        )
                    
                    # Log suggestion
                    await self.memory_manager.add_system_event(
                        "workflow_suggested",
                        {
                            "suggestion_id": suggestion.suggestion_id,
                            "pattern_id": suggestion.pattern_id,
                            "suggested_name": suggestion.suggested_name,
                            "confidence": suggestion.confidence,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
        
        except Exception as e:
            logger.error(f"Workflow pattern detection failed: {e}", exc_info=True)

    async def _analyze_workflow_optimizations(self):
        """
        Analyze existing workflows for optimization opportunities (REQ-6.2.5).
        
        Examines workflow execution history and recommends improvements.
        """
        try:
            logger.info("Analyzing workflow optimizations...")
            
            # Get all workflows
            workflows = await self.workflow_library.list_workflows()
            
            if not workflows:
                logger.info("No workflows to optimize")
                return
            
            optimization_count = 0
            
            # Analyze each workflow
            for workflow in workflows:
                try:
                    # Get execution history
                    history = await self.workflow_library.get_execution_history(
                        workflow_id=workflow.get('id'),
                        limit=10
                    )
                    
                    if not history or len(history) < 5:
                        continue  # Need at least 5 executions for meaningful analysis
                    
                    # Analyze for optimizations
                    optimizations = await self.workflow_optimizer.analyze_workflow(
                        workflow_id=workflow.get('id'),
                        min_executions=5
                    )
                    
                    if optimizations:
                        optimization_count += len(optimizations)
                        logger.info(f"Found {len(optimizations)} optimizations for workflow: {workflow.get('name')}")
                        
                        # Notify user about optimization opportunities
                        if self.notifier:
                            for opt in optimizations:
                                await self.notifier.notify(
                                    title="Workflow Optimization",
                                    message=f"{workflow.get('name')}: {opt.description} ({opt.potential_improvement})",
                                    priority="low",
                                    notification_type="workflow_optimization",
                                    metadata={
                                        "workflow_id": workflow.get('id'),
                                        "optimization_type": opt.optimization_type,
                                        "confidence": opt.confidence
                                    }
                                )
                        
                        # Log optimizations
                        await self.memory_manager.add_system_event(
                            "workflow_optimization_detected",
                            {
                                "workflow_id": workflow.get('id'),
                                "workflow_name": workflow.get('name'),
                                "optimization_count": len(optimizations),
                                "optimizations": [
                                    {
                                        "type": opt.optimization_type,
                                        "description": opt.description,
                                        "improvement": opt.potential_improvement
                                    }
                                    for opt in optimizations
                                ],
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                
                except Exception as e:
                    logger.error(f"Failed to optimize workflow {workflow.get('name')}: {e}")
                    continue
            
            logger.info(f"Workflow optimization analysis complete: {optimization_count} optimizations found")
        
        except Exception as e:
            logger.error(f"Workflow optimization analysis failed: {e}", exc_info=True)
