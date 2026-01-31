"""
Tests for ExecutionCoordinator (REQ-8.1.3)

Tests task execution orchestration, dependency resolution, and coordination logic.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from alpha.core.task_decomposition import (
    ExecutionCoordinator,
    ExecutionStrategy,
    ProgressTracker,
    SubTask,
    TaskStatus,
    TaskTree,
)


@pytest.fixture
def simple_task_tree():
    """Create a simple sequential task tree."""
    root = SubTask(id="0", description="Root task", depth=0)

    sub_tasks = {
        "1": SubTask(
            id="1",
            description="Task 1",
            parent_id="0",
            depth=1,
            estimated_duration=10.0
        ),
        "2": SubTask(
            id="2",
            description="Task 2",
            parent_id="0",
            depth=1,
            dependencies=["1"],  # Depends on task 1
            estimated_duration=15.0
        ),
        "3": SubTask(
            id="3",
            description="Task 3",
            parent_id="0",
            depth=1,
            dependencies=["2"],  # Depends on task 2
            estimated_duration=20.0
        ),
    }

    return TaskTree(
        session_id="simple_test",
        user_request="Simple sequential test",
        root_task=root,
        sub_tasks=sub_tasks,
        execution_strategy=ExecutionStrategy.SEQUENTIAL
    )


@pytest.fixture
def parallel_task_tree():
    """Create a task tree with parallel execution."""
    root = SubTask(id="0", description="Root task", depth=0)

    sub_tasks = {
        "1": SubTask(id="1", description="Independent task 1", parent_id="0", depth=1),
        "2": SubTask(id="2", description="Independent task 2", parent_id="0", depth=1),
        "3": SubTask(id="3", description="Independent task 3", parent_id="0", depth=1),
        "4": SubTask(
            id="4",
            description="Dependent task",
            parent_id="0",
            depth=1,
            dependencies=["1", "2", "3"]  # Depends on all three
        ),
    }

    return TaskTree(
        session_id="parallel_test",
        user_request="Parallel execution test",
        root_task=root,
        sub_tasks=sub_tasks,
        execution_strategy=ExecutionStrategy.PARALLEL
    )


@pytest.mark.asyncio
async def test_coordinator_initialization(simple_task_tree):
    """Test ExecutionCoordinator initialization."""
    tracker = ProgressTracker(simple_task_tree)
    coordinator = ExecutionCoordinator(simple_task_tree, tracker)

    assert coordinator.task_tree == simple_task_tree
    assert coordinator.tracker == tracker
    assert coordinator.cancelled == False
    assert len(coordinator.task_results) == 0


@pytest.mark.asyncio
async def test_simple_sequential_execution(simple_task_tree):
    """Test simple sequential task execution."""
    tracker = ProgressTracker(simple_task_tree)
    coordinator = ExecutionCoordinator(simple_task_tree, tracker)

    result = await coordinator.execute()

    # Verify execution succeeded
    assert result.success == True
    assert result.session_id == simple_task_tree.session_id

    # Verify all tasks completed
    for task_id in ["1", "2", "3"]:
        task = simple_task_tree.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_parallel_execution(parallel_task_tree):
    """Test parallel task execution."""
    tracker = ProgressTracker(parallel_task_tree)
    coordinator = ExecutionCoordinator(parallel_task_tree, tracker)

    result = await coordinator.execute()

    # Verify execution succeeded
    assert result.success == True

    # Verify independent tasks all completed
    for task_id in ["1", "2", "3"]:
        task = parallel_task_tree.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED

    # Verify dependent task completed
    task4 = parallel_task_tree.get_task("4")
    assert task4.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_create_execution_plan_sequential(simple_task_tree):
    """Test execution plan creation for sequential tasks."""
    tracker = ProgressTracker(simple_task_tree)
    coordinator = ExecutionCoordinator(simple_task_tree, tracker)

    plan = coordinator._create_execution_plan()

    # Should have 3 phases (one task per phase due to dependencies)
    assert len(plan) == 3

    # Verify phase order
    assert plan[0].tasks[0].id == "1"  # No dependencies
    assert plan[1].tasks[0].id == "2"  # Depends on 1
    assert plan[2].tasks[0].id == "3"  # Depends on 2


@pytest.mark.asyncio
async def test_create_execution_plan_parallel(parallel_task_tree):
    """Test execution plan creation for parallel tasks."""
    tracker = ProgressTracker(parallel_task_tree)
    coordinator = ExecutionCoordinator(parallel_task_tree, tracker)

    plan = coordinator._create_execution_plan()

    # Should have 2 phases:
    # Phase 1: Tasks 1, 2, 3 (no dependencies, can run in parallel)
    # Phase 2: Task 4 (depends on 1, 2, 3)
    assert len(plan) == 2

    # Verify phase 1 has all independent tasks
    phase1_ids = {t.id for t in plan[0].tasks}
    assert phase1_ids == {"1", "2", "3"}

    # Verify phase 2 has dependent task
    assert plan[1].tasks[0].id == "4"


@pytest.mark.asyncio
async def test_task_context_building(simple_task_tree):
    """Test building execution context for tasks."""
    tracker = ProgressTracker(simple_task_tree)
    coordinator = ExecutionCoordinator(simple_task_tree, tracker)

    # Execute first task to get a result
    task1 = simple_task_tree.get_task("1")
    coordinator.task_results["1"] = {"data": "test_result"}

    # Build context for task 2 (depends on task 1)
    task2 = simple_task_tree.get_task("2")
    context = coordinator._build_task_context(task2)

    # Verify dependency results included
    assert "dependency_results" in context
    assert "1" in context["dependency_results"]
    assert context["dependency_results"]["1"] == {"data": "test_result"}


@pytest.mark.asyncio
async def test_task_execution_with_result(simple_task_tree):
    """Test individual task execution stores result."""
    tracker = ProgressTracker(simple_task_tree)
    coordinator = ExecutionCoordinator(simple_task_tree, tracker)

    tracker.start_tracking()

    task1 = simple_task_tree.get_task("1")
    result = await coordinator._execute_task(task1)

    # Verify result stored
    assert result.success == True
    assert task1.id in coordinator.task_results


@pytest.mark.asyncio
async def test_execution_with_task_failure(simple_task_tree):
    """Test handling task execution failure."""
    tracker = ProgressTracker(simple_task_tree)
    coordinator = ExecutionCoordinator(simple_task_tree, tracker)

    # Mock task execution to fail
    async def failing_execution(task, context):
        raise Exception("Task failed deliberately")

    coordinator._execute_task_direct = failing_execution

    result = await coordinator.execute()

    # Execution should complete but with failure
    assert result.success == False
    assert result.error is not None


@pytest.mark.asyncio
async def test_cancel_execution(simple_task_tree):
    """Test canceling ongoing execution."""
    tracker = ProgressTracker(simple_task_tree)
    coordinator = ExecutionCoordinator(simple_task_tree, tracker)

    # Start execution and cancel immediately
    async def execute_and_cancel():
        coordinator.cancel()
        return await coordinator.execute()

    result = await execute_and_cancel()

    # Should indicate cancellation
    assert result.success == False
    assert "cancel" in result.error.lower()


@pytest.mark.asyncio
async def test_determine_phase_strategy(simple_task_tree):
    """Test phase strategy determination."""
    tracker = ProgressTracker(simple_task_tree)
    coordinator = ExecutionCoordinator(simple_task_tree, tracker)

    # Sequential tree should use sequential strategy
    task1 = simple_task_tree.get_task("1")
    strategy = coordinator._determine_phase_strategy([task1])

    assert strategy == ExecutionStrategy.SEQUENTIAL


@pytest.mark.asyncio
async def test_determine_phase_strategy_parallel(parallel_task_tree):
    """Test phase strategy for parallel execution."""
    tracker = ProgressTracker(parallel_task_tree)
    coordinator = ExecutionCoordinator(parallel_task_tree, tracker)

    # Get first phase tasks (should be parallel)
    tasks = [
        parallel_task_tree.get_task("1"),
        parallel_task_tree.get_task("2"),
        parallel_task_tree.get_task("3"),
    ]

    strategy = coordinator._determine_phase_strategy(tasks)

    assert strategy == ExecutionStrategy.PARALLEL


@pytest.mark.asyncio
async def test_execution_with_resilience(simple_task_tree):
    """Test execution with resilience engine integration."""
    tracker = ProgressTracker(simple_task_tree)

    # Mock resilience engine
    resilience = Mock()
    resilience.execute_with_retry = AsyncMock(return_value={"status": "success"})

    coordinator = ExecutionCoordinator(
        simple_task_tree,
        tracker,
        resilience_engine=resilience
    )

    tracker.start_tracking()

    task1 = simple_task_tree.get_task("1")
    result = await coordinator._execute_task(task1)

    # Verify resilience was used
    assert resilience.execute_with_retry.called


@pytest.mark.asyncio
async def test_progress_updates_during_execution(simple_task_tree):
    """Test progress tracker updates during execution."""
    tracker = ProgressTracker(simple_task_tree)
    coordinator = ExecutionCoordinator(simple_task_tree, tracker)

    result = await coordinator.execute()

    # Verify all tasks have timestamps
    for task_id in ["1", "2", "3"]:
        task = simple_task_tree.get_task(task_id)
        assert task.started_at is not None
        assert task.completed_at is not None
        assert task.actual_duration is not None


@pytest.mark.asyncio
async def test_execution_result_includes_summary(simple_task_tree):
    """Test execution result includes progress summary."""
    tracker = ProgressTracker(simple_task_tree)
    coordinator = ExecutionCoordinator(simple_task_tree, tracker)

    result = await coordinator.execute()

    # Verify summary included
    assert result.summary is not None
    assert result.summary.overall_progress == 1.0  # All completed
    assert result.summary.completed_count == 4  # 3 sub-tasks + 1 root task


@pytest.mark.asyncio
async def test_complex_dependency_graph():
    """Test execution with complex dependency graph."""
    root = SubTask(id="0", description="Root", depth=0)

    #     1
    #    / \
    #   2   3
    #    \ /
    #     4

    sub_tasks = {
        "1": SubTask(id="1", description="Task 1", parent_id="0", depth=1),
        "2": SubTask(
            id="2",
            description="Task 2",
            parent_id="0",
            depth=1,
            dependencies=["1"]
        ),
        "3": SubTask(
            id="3",
            description="Task 3",
            parent_id="0",
            depth=1,
            dependencies=["1"]
        ),
        "4": SubTask(
            id="4",
            description="Task 4",
            parent_id="0",
            depth=1,
            dependencies=["2", "3"]
        ),
    }

    tree = TaskTree(
        session_id="complex_test",
        user_request="Complex dependency test",
        root_task=root,
        sub_tasks=sub_tasks,
        execution_strategy=ExecutionStrategy.HYBRID
    )

    tracker = ProgressTracker(tree)
    coordinator = ExecutionCoordinator(tree, tracker)

    plan = coordinator._create_execution_plan()

    # Should have 3 phases:
    # Phase 1: Task 1
    # Phase 2: Tasks 2 and 3 (parallel)
    # Phase 3: Task 4
    assert len(plan) == 3

    result = await coordinator.execute()
    assert result.success == True
