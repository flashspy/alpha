"""
ExecutionCoordinator - Orchestrates decomposed task execution (REQ-8.1.3)

Manages task execution with dependency resolution, supports sequential/parallel
strategies, integrates with ResilienceEngine for failure handling.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from alpha.core.task_decomposition.models import (
    ExecutionPhase,
    ExecutionResult,
    ExecutionStrategy,
    ProgressSummary,
    SubTask,
    SubTaskResult,
    TaskStatus,
    TaskTree,
)
from alpha.core.task_decomposition.tracker import ProgressTracker

logger = logging.getLogger(__name__)


class ExecutionCoordinator:
    """
    Coordinates execution of decomposed task trees.

    Responsibilities:
    - Create execution plan from task dependencies
    - Execute tasks in correct order (sequential/parallel/hybrid)
    - Handle task failures with retry/skip/abort
    - Pass results from completed tasks to dependent tasks
    - Integrate with ResilienceEngine for robust execution
    """

    def __init__(
        self,
        task_tree: TaskTree,
        progress_tracker: ProgressTracker,
        tool_registry=None,
        llm_provider=None,
        resilience_engine=None
    ):
        """
        Initialize execution coordinator.

        Args:
            task_tree: TaskTree to execute
            progress_tracker: ProgressTracker instance
            tool_registry: Tool registry for task execution (optional)
            llm_provider: LLM provider for task execution (optional)
            resilience_engine: ResilienceEngine for failure handling (optional)
        """
        self.task_tree = task_tree
        self.tracker = progress_tracker
        self.tools = tool_registry
        self.llm = llm_provider
        self.resilience = resilience_engine

        # Execution state
        self.task_results: Dict[str, Any] = {}  # task_id -> result
        self.execution_context: Dict[str, Any] = {}  # Shared context
        self.cancelled = False

        logger.info(
            f"ExecutionCoordinator initialized for session {task_tree.session_id}, "
            f"strategy={task_tree.execution_strategy.value}"
        )

    async def execute(self) -> ExecutionResult:
        """
        Execute the entire task tree.

        Returns:
            ExecutionResult with overall status and results
        """
        try:
            # Start progress tracking
            self.tracker.start_tracking()

            logger.info(
                f"Starting execution of {len(self.task_tree.sub_tasks)} tasks"
            )

            # Create execution plan (dependency-aware phases)
            execution_plan = self._create_execution_plan()
            logger.info(f"Execution plan created: {len(execution_plan)} phases")

            # Execute tasks phase by phase
            for phase_idx, phase in enumerate(execution_plan):
                if self.cancelled:
                    logger.warning("Execution cancelled by user")
                    break

                logger.info(
                    f"Executing phase {phase_idx + 1}/{len(execution_plan)}: "
                    f"{len(phase.tasks)} tasks, strategy={phase.strategy.value}"
                )

                await self._execute_phase(phase)

            # Determine overall success
            failed_tasks = [
                t for t in self.task_tree.sub_tasks.values()
                if t.status == TaskStatus.FAILED
            ]

            success = len(failed_tasks) == 0 and not self.cancelled

            # Mark tracking complete
            error_msg = None
            if failed_tasks:
                error_msg = f"{len(failed_tasks)} tasks failed"
            elif self.cancelled:
                error_msg = "Execution cancelled"

            self.tracker.complete_tracking(success=success, error=error_msg)

            # Get final summary after tracking complete
            summary = self.tracker.get_progress_summary()

            return ExecutionResult(
                session_id=self.task_tree.session_id,
                success=success,
                results=self.task_results,
                summary=summary,
                error=error_msg
            )

        except Exception as e:
            logger.error(f"Execution failed with exception: {e}", exc_info=True)

            # Mark tracking as failed
            self.tracker.complete_tracking(success=False, error=str(e))

            return ExecutionResult(
                session_id=self.task_tree.session_id,
                success=False,
                error=str(e),
                partial_results=self.task_results,
                summary=self.tracker.get_progress_summary()
            )

    def _create_execution_plan(self) -> List[ExecutionPhase]:
        """
        Create execution plan with dependency-aware phases.

        Uses topological sorting to group tasks into phases where:
        - Tasks within a phase have no dependencies on each other
        - All dependencies are satisfied by previous phases

        Returns:
            List of ExecutionPhase objects
        """
        phases: List[ExecutionPhase] = []
        executed_task_ids = set()
        all_task_ids = set(self.task_tree.sub_tasks.keys())

        phase_id = 0

        while len(executed_task_ids) < len(all_task_ids):
            # Find tasks ready to execute (all dependencies satisfied)
            ready_tasks = []

            for task in self.task_tree.sub_tasks.values():
                if task.id in executed_task_ids:
                    continue

                # Check if all dependencies completed
                deps_satisfied = all(
                    dep_id in executed_task_ids
                    for dep_id in task.dependencies
                )

                if deps_satisfied:
                    ready_tasks.append(task)

            if not ready_tasks:
                # No tasks ready - circular dependency or logic error
                remaining = all_task_ids - executed_task_ids
                logger.error(
                    f"Deadlock detected: {len(remaining)} tasks remaining "
                    f"but none ready to execute. IDs: {remaining}"
                )
                break

            # Determine execution strategy for this phase
            strategy = self._determine_phase_strategy(ready_tasks)

            phase = ExecutionPhase(
                phase_id=phase_id,
                tasks=ready_tasks,
                strategy=strategy
            )

            phases.append(phase)

            # Mark these tasks as "will be executed"
            executed_task_ids.update(task.id for task in ready_tasks)

            phase_id += 1

        return phases

    def _determine_phase_strategy(
        self,
        tasks: List[SubTask]
    ) -> ExecutionStrategy:
        """
        Determine execution strategy for a phase.

        Args:
            tasks: Tasks in this phase

        Returns:
            ExecutionStrategy for this phase
        """
        # Use tree-level strategy as default
        global_strategy = self.task_tree.execution_strategy

        # Override rules:
        # - If global is SEQUENTIAL, always use sequential
        # - If global is PARALLEL and tasks are independent, use parallel
        # - If global is HYBRID, decide per phase

        if global_strategy == ExecutionStrategy.SEQUENTIAL:
            return ExecutionStrategy.SEQUENTIAL

        if global_strategy == ExecutionStrategy.PARALLEL:
            # Can run in parallel if no inter-task dependencies
            return ExecutionStrategy.PARALLEL

        # HYBRID: Use parallel for phases with 3+ tasks, sequential otherwise
        if len(tasks) >= 3:
            return ExecutionStrategy.PARALLEL
        else:
            return ExecutionStrategy.SEQUENTIAL

    async def _execute_phase(self, phase: ExecutionPhase):
        """
        Execute all tasks in a phase.

        Args:
            phase: ExecutionPhase to execute
        """
        if phase.strategy == ExecutionStrategy.SEQUENTIAL:
            # Execute tasks one by one
            for task in phase.tasks:
                if self.cancelled:
                    break
                await self._execute_task(task)

        elif phase.strategy in [ExecutionStrategy.PARALLEL, ExecutionStrategy.HYBRID]:
            # Execute tasks concurrently
            await asyncio.gather(
                *[self._execute_task(task) for task in phase.tasks],
                return_exceptions=True  # Don't fail entire phase if one task fails
            )

    async def _execute_task(self, task: SubTask) -> SubTaskResult:
        """
        Execute a single sub-task.

        Steps:
        1. Mark task as IN_PROGRESS
        2. Inject context from parent/dependent tasks
        3. Execute task (via tool, LLM, or mock)
        4. Update progress tracker with result
        5. Store result for dependent tasks

        Args:
            task: SubTask to execute

        Returns:
            SubTaskResult with execution outcome
        """
        logger.info(f"Executing task {task.id}: {task.description}")

        # Mark as in progress
        self.tracker.update_task_status(task.id, TaskStatus.IN_PROGRESS)

        try:
            # Inject context from dependencies
            context = self._build_task_context(task)

            # Execute with resilience if available
            if self.resilience:
                result = await self._execute_with_resilience(task, context)
            else:
                result = await self._execute_task_direct(task, context)

            # Update tracker with success
            self.tracker.update_task_status(
                task.id,
                TaskStatus.COMPLETED,
                result=result
            )

            # Store result for dependent tasks
            self.task_results[task.id] = result

            logger.info(f"Task {task.id} completed successfully")

            return SubTaskResult(
                task_id=task.id,
                success=True,
                result=result,
                duration=task.actual_duration or 0.0
            )

        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}", exc_info=True)

            # Update tracker with failure
            self.tracker.update_task_status(
                task.id,
                TaskStatus.FAILED,
                error=str(e)
            )

            return SubTaskResult(
                task_id=task.id,
                success=False,
                error=str(e),
                duration=task.actual_duration or 0.0
            )

    def _build_task_context(self, task: SubTask) -> Dict[str, Any]:
        """
        Build execution context for a task.

        Includes:
        - Results from dependency tasks
        - Parent task information
        - Shared execution context

        Args:
            task: Task to build context for

        Returns:
            Context dictionary
        """
        context = self.execution_context.copy()

        # Add dependency results
        if task.dependencies:
            context["dependency_results"] = {
                dep_id: self.task_results.get(dep_id)
                for dep_id in task.dependencies
            }

        # Add parent task info
        if task.parent_id:
            parent = self.task_tree.get_task(task.parent_id)
            if parent:
                context["parent_task"] = {
                    "id": parent.id,
                    "description": parent.description,
                    "result": self.task_results.get(parent.id)
                }

        # Add task metadata
        context["task_metadata"] = task.metadata

        return context

    async def _execute_task_direct(
        self,
        task: SubTask,
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute task directly (without resilience).

        Phase 2 Implementation: Mock execution for testing
        Phase 3: Real execution with tool/LLM selection

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Task execution result
        """
        # Phase 2: Mock execution
        logger.debug(f"Mock executing task {task.id}")

        # Simulate some work
        await asyncio.sleep(0.01)

        # Return mock result
        return {
            "status": "success",
            "task_id": task.id,
            "description": task.description,
            "context_keys": list(context.keys())
        }

    async def _execute_with_resilience(
        self,
        task: SubTask,
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute task with ResilienceEngine integration.

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Task execution result
        """
        # Wrap execution in resilience layer
        async def _resilient_execution():
            return await self._execute_task_direct(task, context)

        # Use resilience engine's retry policy
        result = await self.resilience.execute_with_retry(
            operation=_resilient_execution,
            operation_id=f"task_{task.id}",
            max_retries=3
        )

        return result

    def cancel(self):
        """Cancel ongoing execution."""
        self.cancelled = True
        logger.info("Execution cancellation requested")
