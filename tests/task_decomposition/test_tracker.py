"""
Tests for ProgressTracker (REQ-8.1.2)

Tests progress tracking, time estimation, status updates, and snapshot management.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from alpha.core.task_decomposition import (
    ProgressTracker,
    ProgressStorage,
    SubTask,
    TaskStatus,
    TaskTree,
)


@pytest.fixture
def sample_task_tree():
    """Create a sample task tree for testing."""
    root = SubTask(
        id="0",
        description="Complete user authentication system",
        depth=0,
        estimated_duration=1200.0
    )

    sub_tasks = {
        "1": SubTask(
            id="1",
            description="Analyze codebase",
            parent_id="0",
            depth=1,
            estimated_duration=300.0,
            status=TaskStatus.PENDING
        ),
        "2": SubTask(
            id="2",
            description="Design architecture",
            parent_id="0",
            depth=1,
            dependencies=["1"],
            estimated_duration=400.0,
            status=TaskStatus.PENDING
        ),
        "3": SubTask(
            id="3",
            description="Implement JWT generation",
            parent_id="0",
            depth=1,
            dependencies=["2"],
            estimated_duration=500.0,
            status=TaskStatus.PENDING
        ),
    }

    tree = TaskTree(
        session_id="test_session_1",
        user_request="Implement user authentication",
        root_task=root,
        sub_tasks=sub_tasks,
        total_estimated_duration=1200.0
    )

    return tree


def test_tracker_initialization(sample_task_tree):
    """Test ProgressTracker initialization."""
    tracker = ProgressTracker(sample_task_tree)

    assert tracker.task_tree == sample_task_tree
    assert tracker.start_time is None
    assert tracker.end_time is None


def test_start_tracking(sample_task_tree):
    """Test starting progress tracking."""
    tracker = ProgressTracker(sample_task_tree)
    tracker.start_tracking()

    assert tracker.start_time is not None
    assert sample_task_tree.root_task.status == TaskStatus.IN_PROGRESS
    assert sample_task_tree.root_task.started_at is not None


def test_update_task_status(sample_task_tree):
    """Test updating task status."""
    tracker = ProgressTracker(sample_task_tree)
    tracker.start_tracking()

    # Update first task to in_progress
    tracker.update_task_status("1", TaskStatus.IN_PROGRESS)
    task = sample_task_tree.get_task("1")

    assert task.status == TaskStatus.IN_PROGRESS
    assert task.started_at is not None

    # Complete the task
    tracker.update_task_status("1", TaskStatus.COMPLETED, result={"analysis": "done"})

    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None
    assert task.actual_duration is not None
    assert task.result == {"analysis": "done"}


def test_update_task_with_error(sample_task_tree):
    """Test updating task status with error."""
    tracker = ProgressTracker(sample_task_tree)
    tracker.start_tracking()

    tracker.update_task_status("1", TaskStatus.IN_PROGRESS)
    tracker.update_task_status(
        "1",
        TaskStatus.FAILED,
        error="Database connection failed"
    )

    task = sample_task_tree.get_task("1")

    assert task.status == TaskStatus.FAILED
    assert task.error == "Database connection failed"
    assert task.completed_at is not None


def test_get_progress_summary(sample_task_tree):
    """Test progress summary calculation."""
    tracker = ProgressTracker(sample_task_tree)
    tracker.start_tracking()

    # Initial summary
    summary = tracker.get_progress_summary()

    assert summary.overall_progress == 0.0  # No tasks completed
    assert summary.pending_count == 3
    assert summary.completed_count == 0
    assert summary.in_progress_count == 1  # Root task

    # Complete one task
    tracker.update_task_status("1", TaskStatus.IN_PROGRESS)
    tracker.update_task_status("1", TaskStatus.COMPLETED)

    summary = tracker.get_progress_summary()

    assert summary.completed_count == 1
    assert summary.pending_count == 2
    assert summary.overall_progress == 0.25  # 1 out of 4 tasks (including root)


def test_get_current_task(sample_task_tree):
    """Test getting currently executing task."""
    tracker = ProgressTracker(sample_task_tree)
    tracker.start_tracking()

    # Initially, root task is in progress
    current = tracker.get_current_task()
    assert current.id == "0"

    # Start a sub-task
    tracker.update_task_status("1", TaskStatus.IN_PROGRESS)
    current = tracker.get_current_task()
    assert current.id == "1"


def test_estimate_remaining_time(sample_task_tree):
    """Test remaining time estimation."""
    tracker = ProgressTracker(sample_task_tree)
    tracker.start_tracking()

    # Initial estimate (all tasks pending)
    summary = tracker.get_progress_summary()
    # Should estimate based on sum of estimated durations
    assert summary.estimated_remaining > 0

    # Complete one task faster than estimated
    task1 = sample_task_tree.get_task("1")
    task1.status = TaskStatus.COMPLETED
    task1.estimated_duration = 300.0
    task1.actual_duration = 150.0  # 50% of estimate

    summary = tracker.get_progress_summary()

    # Estimate should be adjusted based on completion rate
    assert summary.estimated_remaining > 0


def test_complete_tracking_success(sample_task_tree):
    """Test completing tracking session successfully."""
    tracker = ProgressTracker(sample_task_tree)
    tracker.start_tracking()

    # Complete all tasks
    for task_id in ["1", "2", "3"]:
        tracker.update_task_status(task_id, TaskStatus.IN_PROGRESS)
        tracker.update_task_status(task_id, TaskStatus.COMPLETED)

    tracker.complete_tracking(success=True)

    assert tracker.end_time is not None
    assert sample_task_tree.root_task.status == TaskStatus.COMPLETED
    assert sample_task_tree.root_task.completed_at is not None
    assert sample_task_tree.root_task.actual_duration is not None


def test_complete_tracking_failure(sample_task_tree):
    """Test completing tracking session with failure."""
    tracker = ProgressTracker(sample_task_tree)
    tracker.start_tracking()

    tracker.update_task_status("1", TaskStatus.IN_PROGRESS)
    tracker.update_task_status("1", TaskStatus.FAILED, error="Test error")

    tracker.complete_tracking(success=False, error="Task 1 failed")

    assert tracker.end_time is not None
    assert sample_task_tree.root_task.status == TaskStatus.FAILED
    assert sample_task_tree.root_task.error == "Task 1 failed"


def test_tracker_with_storage(sample_task_tree, tmp_path):
    """Test tracker integration with storage."""
    storage = ProgressStorage(str(tmp_path / "test.db"))
    tracker = ProgressTracker(sample_task_tree, storage=storage)

    # Create session in storage
    storage.create_session(
        sample_task_tree.session_id,
        sample_task_tree.user_request,
        sample_task_tree
    )

    # Start tracking (should save snapshot)
    tracker.start_tracking()

    # Update tasks (should save snapshots)
    tracker.update_task_status("1", TaskStatus.IN_PROGRESS)
    tracker.update_task_status("1", TaskStatus.COMPLETED)

    # Verify snapshots were saved
    snapshots = storage.list_snapshots(sample_task_tree.session_id)
    assert len(snapshots) >= 2  # Start + completion


def test_progress_summary_serialization(sample_task_tree):
    """Test ProgressSummary serialization."""
    tracker = ProgressTracker(sample_task_tree)
    tracker.start_tracking()

    summary = tracker.get_progress_summary()
    summary_dict = summary.to_dict()

    assert "overall_progress" in summary_dict
    assert "completed_count" in summary_dict
    assert "elapsed_time" in summary_dict
    assert "estimated_remaining" in summary_dict
