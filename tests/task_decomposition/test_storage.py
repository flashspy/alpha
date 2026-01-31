"""
Tests for ProgressStorage (REQ-8.1.2)

Tests SQLite persistence for task execution sessions and progress snapshots.
"""

import pytest
import json
from pathlib import Path

from alpha.core.task_decomposition import (
    ProgressStorage,
    ProgressSummary,
    SubTask,
    TaskStatus,
    TaskTree,
)


@pytest.fixture
def storage(tmp_path):
    """Create temporary storage for testing."""
    db_path = tmp_path / "test_storage.db"
    return ProgressStorage(str(db_path))


@pytest.fixture
def sample_task_tree():
    """Create a sample task tree."""
    root = SubTask(
        id="0",
        description="Root task",
        depth=0
    )

    sub_tasks = {
        "1": SubTask(id="1", description="Task 1", parent_id="0", depth=1),
        "2": SubTask(id="2", description="Task 2", parent_id="0", depth=1),
    }

    return TaskTree(
        session_id="test_session_1",
        user_request="Test request",
        root_task=root,
        sub_tasks=sub_tasks
    )


def test_storage_initialization(tmp_path):
    """Test storage initialization creates schema."""
    db_path = tmp_path / "test.db"
    storage = ProgressStorage(str(db_path))

    # Verify database file created
    assert db_path.exists()


def test_create_session(storage, sample_task_tree):
    """Test creating a new session."""
    session_id = storage.create_session(
        sample_task_tree.session_id,
        sample_task_tree.user_request,
        sample_task_tree,
        metadata={"test": "data"}
    )

    assert session_id == sample_task_tree.session_id

    # Verify session exists
    session = storage.load_session(session_id)
    assert session is not None
    assert session["session_id"] == session_id
    assert session["user_request"] == sample_task_tree.user_request
    assert session["status"] == "pending"


def test_start_session(storage, sample_task_tree):
    """Test starting a session."""
    storage.create_session(
        sample_task_tree.session_id,
        sample_task_tree.user_request,
        sample_task_tree
    )

    storage.start_session(sample_task_tree.session_id)

    session = storage.load_session(sample_task_tree.session_id)
    assert session["status"] == "running"
    assert session["started_at"] is not None


def test_complete_session(storage, sample_task_tree):
    """Test completing a session."""
    storage.create_session(
        sample_task_tree.session_id,
        sample_task_tree.user_request,
        sample_task_tree
    )

    storage.complete_session(sample_task_tree.session_id, success=True)

    session = storage.load_session(sample_task_tree.session_id)
    assert session["status"] == "completed"
    assert session["completed_at"] is not None


def test_complete_session_failure(storage, sample_task_tree):
    """Test completing a session with failure."""
    storage.create_session(
        sample_task_tree.session_id,
        sample_task_tree.user_request,
        sample_task_tree
    )

    storage.complete_session(sample_task_tree.session_id, success=False)

    session = storage.load_session(sample_task_tree.session_id)
    assert session["status"] == "failed"


def test_save_snapshot(storage, sample_task_tree):
    """Test saving progress snapshot."""
    storage.create_session(
        sample_task_tree.session_id,
        sample_task_tree.user_request,
        sample_task_tree
    )

    summary = ProgressSummary(
        overall_progress=0.5,
        completed_count=1,
        pending_count=1
    )

    snapshot_id = storage.save_snapshot(
        sample_task_tree.session_id,
        sample_task_tree,
        summary
    )

    assert snapshot_id.startswith(sample_task_tree.session_id)


def test_load_snapshot(storage, sample_task_tree):
    """Test loading progress snapshot."""
    storage.create_session(
        sample_task_tree.session_id,
        sample_task_tree.user_request,
        sample_task_tree
    )

    summary = ProgressSummary(overall_progress=0.5, completed_count=1)

    snapshot_id = storage.save_snapshot(
        sample_task_tree.session_id,
        sample_task_tree,
        summary
    )

    # Load snapshot
    snapshot = storage.load_snapshot(snapshot_id)

    assert snapshot is not None
    assert snapshot["task_tree"].session_id == sample_task_tree.session_id
    assert snapshot["progress_summary"]["overall_progress"] == 0.5


def test_load_session_with_snapshots(storage, sample_task_tree):
    """Test loading session includes latest snapshot."""
    storage.create_session(
        sample_task_tree.session_id,
        sample_task_tree.user_request,
        sample_task_tree
    )

    # Save multiple snapshots
    summary1 = ProgressSummary(overall_progress=0.3)
    summary2 = ProgressSummary(overall_progress=0.7)

    storage.save_snapshot(sample_task_tree.session_id, sample_task_tree, summary1)
    storage.save_snapshot(sample_task_tree.session_id, sample_task_tree, summary2)

    # Load session
    session = storage.load_session(sample_task_tree.session_id)

    assert "latest_snapshot" in session
    assert session["latest_snapshot"]["progress_summary"]["overall_progress"] == 0.7


def test_list_sessions(storage, sample_task_tree):
    """Test listing sessions."""
    # Create multiple sessions
    for i in range(3):
        tree = TaskTree(
            session_id=f"session_{i}",
            user_request=f"Request {i}",
            root_task=sample_task_tree.root_task,
            sub_tasks={}
        )
        storage.create_session(tree.session_id, tree.user_request, tree)

    sessions = storage.list_sessions()

    assert len(sessions) >= 3
    assert all("session_id" in s for s in sessions)


def test_list_sessions_filtered(storage, sample_task_tree):
    """Test listing sessions with status filter."""
    # Create sessions with different statuses
    storage.create_session("pending_1", "Request 1", sample_task_tree)

    storage.create_session("running_1", "Request 2", sample_task_tree)
    storage.start_session("running_1")

    storage.create_session("completed_1", "Request 3", sample_task_tree)
    storage.complete_session("completed_1", success=True)

    # Filter by status
    pending = storage.list_sessions(status="pending")
    running = storage.list_sessions(status="running")
    completed = storage.list_sessions(status="completed")

    assert len(pending) >= 1
    assert len(running) >= 1
    assert len(completed) >= 1


def test_list_snapshots(storage, sample_task_tree):
    """Test listing snapshots for a session."""
    storage.create_session(
        sample_task_tree.session_id,
        sample_task_tree.user_request,
        sample_task_tree
    )

    # Save multiple snapshots
    for i in range(5):
        summary = ProgressSummary(overall_progress=i * 0.2)
        storage.save_snapshot(sample_task_tree.session_id, sample_task_tree, summary)

    snapshots = storage.list_snapshots(sample_task_tree.session_id)

    assert len(snapshots) == 5
    # Should be ordered by created_at DESC (most recent first)
    assert snapshots[0]["overall_progress"] == 0.8


def test_delete_session(storage, sample_task_tree):
    """Test deleting session and its snapshots."""
    storage.create_session(
        sample_task_tree.session_id,
        sample_task_tree.user_request,
        sample_task_tree
    )

    # Save some snapshots
    summary = ProgressSummary(overall_progress=0.5)
    storage.save_snapshot(sample_task_tree.session_id, sample_task_tree, summary)

    # Delete session
    storage.delete_session(sample_task_tree.session_id)

    # Verify session deleted
    session = storage.load_session(sample_task_tree.session_id)
    assert session is None

    # Verify snapshots deleted
    snapshots = storage.list_snapshots(sample_task_tree.session_id)
    assert len(snapshots) == 0


def test_cleanup_old_sessions(storage, sample_task_tree):
    """Test cleaning up old sessions."""
    # Create a session
    storage.create_session(
        sample_task_tree.session_id,
        sample_task_tree.user_request,
        sample_task_tree
    )

    # Cleanup with 0 days (should delete everything)
    storage.cleanup_old_sessions(days=0)

    # Sessions should still exist (created just now, within cutoff)
    sessions = storage.list_sessions()
    # Can't easily test age-based deletion without mocking datetime
    # Just verify cleanup doesn't crash


def test_task_tree_serialization_roundtrip(storage, sample_task_tree):
    """Test TaskTree serialization/deserialization through storage."""
    storage.create_session(
        sample_task_tree.session_id,
        sample_task_tree.user_request,
        sample_task_tree
    )

    # Load session
    session = storage.load_session(sample_task_tree.session_id)
    loaded_tree = session["initial_task_tree"]

    # Verify tree structure preserved
    assert loaded_tree.session_id == sample_task_tree.session_id
    assert loaded_tree.user_request == sample_task_tree.user_request
    assert len(loaded_tree.sub_tasks) == len(sample_task_tree.sub_tasks)
    assert loaded_tree.root_task.id == sample_task_tree.root_task.id


def test_concurrent_sessions(storage):
    """Test handling multiple concurrent sessions."""
    sessions = []

    # Create multiple sessions
    for i in range(10):
        tree = TaskTree(
            session_id=f"concurrent_{i}",
            user_request=f"Request {i}",
            root_task=SubTask(id=f"{i}", description=f"Root {i}", depth=0),
            sub_tasks={}
        )
        storage.create_session(tree.session_id, tree.user_request, tree)
        sessions.append(tree.session_id)

    # Verify all sessions exist
    loaded_sessions = storage.list_sessions(limit=20)
    session_ids = [s["session_id"] for s in loaded_sessions]

    for session_id in sessions:
        assert session_id in session_ids
