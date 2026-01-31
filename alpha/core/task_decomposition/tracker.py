"""
ProgressTracker - Real-time task execution progress tracking (REQ-8.1.2)

Tracks status of decomposed tasks, calculates progress metrics,
estimates time remaining, and manages progress snapshots.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from alpha.core.task_decomposition.models import (
    ProgressSummary,
    SubTask,
    TaskStatus,
    TaskTree,
)

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Tracks execution progress of decomposed task trees.

    Responsibilities:
    - Update task statuses in real-time
    - Calculate overall progress percentage
    - Estimate time remaining based on completed tasks
    - Generate progress snapshots for persistence
    - Provide current task and phase information
    """

    def __init__(self, task_tree: TaskTree, storage=None):
        """
        Initialize progress tracker.

        Args:
            task_tree: TaskTree to track
            storage: ProgressStorage instance for persistence (optional)
        """
        self.task_tree = task_tree
        self.storage = storage
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        logger.info(
            f"ProgressTracker initialized for session {task_tree.session_id}, "
            f"{len(task_tree.sub_tasks)} sub-tasks"
        )

    def start_tracking(self):
        """Initialize progress tracking session."""
        self.start_time = datetime.now()
        self.task_tree.root_task.status = TaskStatus.IN_PROGRESS
        self.task_tree.root_task.started_at = self.start_time

        logger.info(
            f"Progress tracking started for session {self.task_tree.session_id}"
        )

        # Save initial snapshot if storage available
        if self.storage:
            self.storage.save_snapshot(
                session_id=self.task_tree.session_id,
                task_tree=self.task_tree,
                summary=self.get_progress_summary()
            )

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ):
        """
        Update status of a specific sub-task.

        Args:
            task_id: ID of task to update
            status: New status
            result: Execution result (for completed tasks)
            error: Error message (for failed tasks)
        """
        task = self.task_tree.get_task(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found in tree")
            return

        old_status = task.status
        task.status = status

        # Update timestamps
        now = datetime.now()
        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = now
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED]:
            if not task.completed_at:
                task.completed_at = now
            # Calculate actual duration
            if task.started_at:
                task.actual_duration = (now - task.started_at).total_seconds()

        # Store result or error
        if result is not None:
            task.result = result
        if error:
            task.error = error

        logger.info(
            f"Task {task_id} status: {old_status.value} → {status.value} "
            f"({task.description[:50]}...)"
        )

        # Save snapshot for important state transitions
        if self.storage and status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            self.storage.save_snapshot(
                session_id=self.task_tree.session_id,
                task_tree=self.task_tree,
                summary=self.get_progress_summary()
            )

    def get_progress_summary(self) -> ProgressSummary:
        """
        Calculate current progress metrics.

        Returns:
            ProgressSummary with current progress data
        """
        # Count tasks by status
        all_tasks = list(self.task_tree.sub_tasks.values())
        if self.task_tree.root_task.id not in self.task_tree.sub_tasks:
            all_tasks.append(self.task_tree.root_task)

        completed = sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED)
        pending = sum(1 for t in all_tasks if t.status == TaskStatus.PENDING)
        in_progress = sum(1 for t in all_tasks if t.status == TaskStatus.IN_PROGRESS)
        failed = sum(1 for t in all_tasks if t.status == TaskStatus.FAILED)
        skipped = sum(1 for t in all_tasks if t.status == TaskStatus.SKIPPED)

        total_tasks = len(all_tasks)

        # Calculate overall progress (0.0 to 1.0)
        if total_tasks > 0:
            # Completed and skipped count as done
            done_count = completed + skipped
            overall_progress = done_count / total_tasks
        else:
            overall_progress = 0.0

        # Calculate elapsed time
        elapsed_time = 0.0
        if self.start_time:
            end = self.end_time or datetime.now()
            elapsed_time = (end - self.start_time).total_seconds()

        # Estimate remaining time
        estimated_remaining = self._estimate_remaining_time(
            completed, pending, in_progress, elapsed_time
        )

        # Get current task info
        current_task = self.get_current_task()
        current_task_id = current_task.id if current_task else None
        current_task_desc = current_task.description if current_task else ""

        # Determine current phase
        current_phase = self._determine_current_phase(current_task)

        return ProgressSummary(
            overall_progress=overall_progress,
            completed_count=completed,
            pending_count=pending,
            in_progress_count=in_progress,
            failed_count=failed,
            skipped_count=skipped,
            elapsed_time=elapsed_time,
            estimated_remaining=estimated_remaining,
            current_phase=current_phase,
            current_task_id=current_task_id,
            current_task_description=current_task_desc,
        )

    def _estimate_remaining_time(
        self,
        completed: int,
        pending: int,
        in_progress: int,
        elapsed_time: float
    ) -> float:
        """
        Estimate time remaining based on completed tasks.

        Uses two strategies:
        1. If we have actual durations: average actual vs estimated ratio
        2. Otherwise: use estimated durations of remaining tasks

        Args:
            completed: Number of completed tasks
            pending: Number of pending tasks
            in_progress: Number of in-progress tasks
            elapsed_time: Time elapsed so far

        Returns:
            Estimated seconds remaining
        """
        # Strategy 1: Use actual duration data if available
        completed_tasks = [
            t for t in self.task_tree.sub_tasks.values()
            if t.status == TaskStatus.COMPLETED and t.actual_duration is not None
        ]

        if len(completed_tasks) >= 2:
            # Calculate average completion rate (actual / estimated)
            total_actual = sum(t.actual_duration for t in completed_tasks)
            total_estimated = sum(t.estimated_duration for t in completed_tasks)

            if total_estimated > 0:
                completion_rate = total_actual / total_estimated
            else:
                completion_rate = 1.0

            # Apply rate to remaining tasks
            remaining_tasks = [
                t for t in self.task_tree.sub_tasks.values()
                if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
            ]

            estimated = sum(t.estimated_duration for t in remaining_tasks)
            return estimated * completion_rate

        # Strategy 2: Use estimated durations
        remaining_tasks = [
            t for t in self.task_tree.sub_tasks.values()
            if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
        ]

        return sum(t.estimated_duration for t in remaining_tasks)

    def _determine_current_phase(self, current_task: Optional[SubTask]) -> str:
        """
        Determine current execution phase description.

        Args:
            current_task: Currently executing task

        Returns:
            Human-readable phase description
        """
        if not current_task:
            return "Idle"

        # Use task metadata if available
        if "phase" in current_task.metadata:
            return current_task.metadata["phase"]

        # Use parent task description as phase
        if current_task.parent_id:
            parent = self.task_tree.get_task(current_task.parent_id)
            if parent:
                return parent.description

        # Default to task ID prefix (e.g., "1.2" → "Phase 1.2")
        if "." in current_task.id:
            phase_id = current_task.id.rsplit(".", 1)[0]
            return f"Phase {phase_id}"

        return f"Phase {current_task.id}"

    def get_current_task(self) -> Optional[SubTask]:
        """
        Get the currently executing task.

        Returns:
            SubTask that is IN_PROGRESS, or None if no task running
        """
        for task in self.task_tree.sub_tasks.values():
            if task.status == TaskStatus.IN_PROGRESS:
                return task

        # Check root task
        if self.task_tree.root_task.status == TaskStatus.IN_PROGRESS:
            return self.task_tree.root_task

        return None

    def complete_tracking(self, success: bool, error: Optional[str] = None):
        """
        Mark tracking session as complete.

        Args:
            success: Whether execution succeeded overall
            error: Error message if execution failed
        """
        self.end_time = datetime.now()

        # Update root task status
        if success:
            self.task_tree.root_task.status = TaskStatus.COMPLETED
        else:
            self.task_tree.root_task.status = TaskStatus.FAILED
            if error:
                self.task_tree.root_task.error = error

        self.task_tree.root_task.completed_at = self.end_time

        # Calculate final duration
        if self.start_time:
            self.task_tree.root_task.actual_duration = (
                self.end_time - self.start_time
            ).total_seconds()

        logger.info(
            f"Progress tracking completed for session {self.task_tree.session_id}, "
            f"success={success}, duration={self.task_tree.root_task.actual_duration:.2f}s"
        )

        # Save final snapshot
        if self.storage:
            self.storage.save_snapshot(
                session_id=self.task_tree.session_id,
                task_tree=self.task_tree,
                summary=self.get_progress_summary()
            )
            self.storage.complete_session(
                session_id=self.task_tree.session_id,
                success=success
            )

    def restore_from_snapshot(self, snapshot_id: str) -> TaskTree:
        """
        Restore progress from saved snapshot.

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            Restored TaskTree

        Raises:
            ValueError: If snapshot not found or storage not configured
        """
        if not self.storage:
            raise ValueError("Cannot restore: no storage configured")

        snapshot = self.storage.load_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        # Update internal state
        self.task_tree = snapshot["task_tree"]

        # Restore timestamps from metadata
        if "start_time" in snapshot.get("metadata", {}):
            self.start_time = datetime.fromisoformat(snapshot["metadata"]["start_time"])
        if "end_time" in snapshot.get("metadata", {}):
            self.end_time = datetime.fromisoformat(snapshot["metadata"]["end_time"])

        logger.info(f"Restored progress from snapshot {snapshot_id}")

        return self.task_tree
