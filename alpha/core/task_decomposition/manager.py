"""
Task Decomposition Manager - CLI Integration Layer

Provides high-level API for integrating task decomposition into CLI workflow.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

from alpha.core.task_decomposition.decomposer import TaskDecomposer
from alpha.core.task_decomposition.coordinator import ExecutionCoordinator
from alpha.core.task_decomposition.tracker import ProgressTracker
from alpha.core.task_decomposition.storage import ProgressStorage
from alpha.core.task_decomposition.models import TaskTree, TaskAnalysis, TaskStatus
from alpha.tools.registry import ToolRegistry
from alpha.llm.service import LLMService


logger = logging.getLogger(__name__)


class TaskDecompositionManager:
    """
    High-level manager for task decomposition in CLI.

    Responsibilities:
    - Detect if task should be decomposed
    - Get user approval for decomposition
    - Execute decomposed tasks with progress tracking
    - Provide real-time progress updates
    """

    def __init__(
        self,
        llm_service: LLMService,
        tool_registry: ToolRegistry,
        config: Optional[Dict[str, Any]] = None,
        storage_path: str = "data/task_decomposition.db"
    ):
        """
        Initialize TaskDecompositionManager.

        Args:
            llm_service: LLM service for decomposition and execution
            tool_registry: Tool registry for task execution
            config: Configuration dict for task decomposition settings
            storage_path: Path to SQLite database for progress storage
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.auto_detect = self.config.get('auto_detect', True)
        self.approval_required = self.config.get('approval_required', True)
        self.max_depth = self.config.get('max_depth', 3)

        # Core components
        self.decomposer = TaskDecomposer(
            llm_service=llm_service,
            config=self.config.get('decomposer', {})
        )
        self.storage = ProgressStorage(storage_path)

        # Will be set when needed
        self.tool_registry = tool_registry
        self.llm_service = llm_service

        logger.info(f"TaskDecompositionManager initialized (enabled={self.enabled}, "
                   f"auto_detect={self.auto_detect}, approval_required={self.approval_required})")

    async def initialize(self):
        """Initialize storage and components."""
        # Storage is initialized in __init__, nothing to do here
        logger.info("TaskDecompositionManager storage initialized")

    async def close(self):
        """Close storage and cleanup."""
        # Close database connection if needed
        if hasattr(self.storage, 'close'):
            self.storage.close()
        logger.info("TaskDecompositionManager closed")

    def should_decompose(self, user_request: str, context: Optional[Dict] = None) -> bool:
        """
        Determine if a user request should trigger task decomposition.

        Args:
            user_request: User's input query
            context: Additional context (conversation history, etc.)

        Returns:
            True if task should be decomposed
        """
        if not self.enabled or not self.auto_detect:
            return False

        # Quick heuristics for complex tasks
        # These are simple rules - LLM will do deeper analysis if triggered
        indicators = [
            len(user_request.split()) > 15,  # Long request
            any(kw in user_request.lower() for kw in [
                'implement', 'create', 'build', 'develop', 'refactor',
                'migrate', 'setup', 'configure', 'deploy', 'integrate'
            ]),
            any(kw in user_request.lower() for kw in [
                'step by step', 'then', 'after that', 'first', 'second'
            ]),
        ]

        # If 2+ indicators present, likely complex
        return sum(indicators) >= 2

    async def analyze_and_decompose(
        self,
        user_request: str,
        context: Optional[Dict] = None
    ) -> Optional[TaskTree]:
        """
        Analyze task and decompose if complex.

        Args:
            user_request: User's request
            context: Additional context

        Returns:
            TaskTree if decomposition successful, None if task is simple
        """
        try:
            # Analyze task complexity
            logger.info(f"Analyzing task complexity: {user_request[:50]}...")
            analysis = await self.decomposer.analyze_task(
                user_request=user_request,
                context=context or {}
            )

            logger.info(f"Task analysis: complexity={analysis.complexity_level}, "
                       f"decomposable={analysis.decomposition_needed}")

            # If simple task, no decomposition needed
            if analysis.complexity_level == "simple" or not analysis.decomposition_needed:
                logger.info("Task is simple, no decomposition needed")
                return None

            # Decompose complex task
            logger.info("Decomposing complex task...")
            task_tree = await self.decomposer.decompose_task(
                user_request=user_request,
                context=context or {},
                max_depth=self.max_depth
            )

            logger.info(f"Task decomposed into {len(task_tree.sub_tasks)} sub-tasks")
            return task_tree

        except Exception as e:
            logger.error(f"Decomposition failed: {e}", exc_info=True)
            return None

    async def execute_with_progress(
        self,
        task_tree: TaskTree,
        progress_callback: Optional[Callable[[Dict], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute decomposed task tree with progress tracking.

        Args:
            task_tree: TaskTree to execute
            progress_callback: Optional callback for progress updates
                               Called with progress summary dict

        Returns:
            Execution result dict with success status and results
        """
        try:
            # Create session and tracker
            import uuid
            session_id = str(uuid.uuid4())[:8]  # Short session ID

            self.storage.create_session(
                session_id=session_id,
                user_request=task_tree.root_task.description,
                task_tree=task_tree
            )
            logger.info(f"Created execution session: {session_id}")

            tracker = ProgressTracker(task_tree=task_tree, storage=self.storage)
            await tracker.start_tracking(session_id)

            # Create coordinator
            coordinator = ExecutionCoordinator(
                task_tree=task_tree,
                progress_tracker=tracker,
                tool_registry=self.tool_registry,
                llm_provider=self.llm_service
            )

            # Execute with progress monitoring
            execution_task = asyncio.create_task(coordinator.execute())

            # Monitor progress and call callback
            while not execution_task.done():
                await asyncio.sleep(0.5)

                if progress_callback:
                    summary = tracker.get_progress_summary()
                    progress_callback(summary.to_dict())

            # Get final result
            result = await execution_task

            # Update session status
            if result.success:
                self.storage.complete_session(
                    session_id=session_id,
                    success=True
                )
            else:
                self.storage.complete_session(
                    session_id=session_id,
                    success=False
                )

            logger.info(f"Execution completed: success={result.success}")

            return {
                "success": result.success,
                "session_id": session_id,
                "results": result.results,
                "error": result.error if not result.success else None,
                "summary": result.summary.to_dict() if result.summary else None
            }

        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "results": []
            }

    def format_decomposition_preview(self, task_tree: TaskTree) -> str:
        """
        Format task tree for user preview.

        Args:
            task_tree: TaskTree to format

        Returns:
            Formatted string for display
        """
        lines = []
        lines.append(f"\n📋 Task Decomposition Preview:\n")
        lines.append(f"Original Task: {task_tree.root_task.description}\n")
        lines.append(f"Total Sub-tasks: {len(task_tree.sub_tasks)}")
        lines.append(f"Estimated Duration: {task_tree.total_estimated_duration:.0f}s "
                    f"({task_tree.total_estimated_duration/60:.1f} minutes)\n")

        # Group tasks by depth for hierarchical display
        depth_groups = {}
        for task in task_tree.sub_tasks.values():
            if task.depth not in depth_groups:
                depth_groups[task.depth] = []
            depth_groups[task.depth].append(task)

        # Display top-level tasks (depth 1)
        if 1 in depth_groups:
            for i, task in enumerate(depth_groups[1], 1):
                indent = "  " * (task.depth - 1)
                lines.append(f"{indent}[{i}/{len(depth_groups[1])}] {task.description}")

                # Show immediate children if any
                children = [t for t in task_tree.sub_tasks.values() if t.parent_id == task.id]
                if children:
                    for child in children[:2]:  # Show first 2 children
                        lines.append(f"    └─ {child.description}")
                    if len(children) > 2:
                        lines.append(f"    └─ ... and {len(children) - 2} more steps")

        return "\n".join(lines)

    async def get_session_status(self, session_id: str) -> Optional[Dict]:
        """
        Get status of an execution session.

        Args:
            session_id: Session ID

        Returns:
            Session info dict or None if not found
        """
        session = self.storage.load_session(session_id)
        return session

    async def list_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """
        List recent execution sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session info dicts
        """
        # This would require adding a method to ProgressStorage
        # For now, return empty list
        return []
