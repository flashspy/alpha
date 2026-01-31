"""
Level 1 Smoke Tests - Task Decomposition System (REQ-8.1)

Quick validation tests (≤2 minutes) to verify basic initialization and core functionality.
These tests run always, before all other tests.
"""

import pytest

from alpha.core.task_decomposition import (
    ComplexityLevel,
    ExecutionStrategy,
    ProgressSummary,
    SubTask,
    TaskAnalysis,
    TaskStatus,
    TaskTree,
)
from alpha.core.task_decomposition.decomposer import TaskDecomposer


class TestBasicInitialization:
    """Level 1 - Verify basic component initialization"""

    def test_decomposer_initialization_without_llm(self):
        """Decomposer can initialize without LLM service (Phase 1)"""
        decomposer = TaskDecomposer(llm_service=None)
        assert decomposer is not None
        assert decomposer.llm_service is None
        assert decomposer.max_depth > 0
        assert decomposer.max_subtasks_per_level > 0

    def test_decomposer_initialization_with_config(self):
        """Decomposer respects configuration parameters"""
        config = {
            "max_depth": 5,
            "max_subtasks_per_level": 10,
            "min_task_duration": 5.0,
        }
        decomposer = TaskDecomposer(llm_service=None, config=config)
        assert decomposer.max_depth == 5
        assert decomposer.max_subtasks_per_level == 10
        assert decomposer.min_task_duration == 5.0


class TestDataModels:
    """Level 1 - Verify data model basic operations"""

    def test_subtask_creation(self):
        """SubTask can be created with required fields"""
        task = SubTask(
            id="1",
            description="Test task",
            depth=1,
            estimated_duration=60.0,
        )
        assert task.id == "1"
        assert task.description == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.depth == 1
        assert len(task.dependencies) == 0

    def test_subtask_serialization(self):
        """SubTask can be serialized to dict and back"""
        task = SubTask(
            id="2",
            description="Serialization test",
            parent_id="1",
            depth=2,
            dependencies=["1.1"],
            estimated_duration=120.0,
        )
        task_dict = task.to_dict()
        assert isinstance(task_dict, dict)
        assert task_dict["id"] == "2"
        assert task_dict["parent_id"] == "1"

        # Deserialize
        restored_task = SubTask.from_dict(task_dict)
        assert restored_task.id == task.id
        assert restored_task.description == task.description
        assert restored_task.status == task.status

    def test_task_tree_creation(self):
        """TaskTree can be created with root task"""
        root = SubTask(id="0", description="Root task", depth=0)
        tree = TaskTree(
            session_id="test-session",
            user_request="Test request",
            root_task=root,
        )
        assert tree.session_id == "test-session"
        assert tree.root_task.id == "0"
        assert len(tree.sub_tasks) == 0
        assert tree.execution_strategy == ExecutionStrategy.HYBRID

    def test_task_tree_get_task(self):
        """TaskTree can retrieve tasks by ID"""
        root = SubTask(id="0", description="Root", depth=0)
        sub1 = SubTask(id="1", description="Sub 1", parent_id="0", depth=1)

        tree = TaskTree(
            session_id="test",
            user_request="Test",
            root_task=root,
            sub_tasks={"1": sub1},
        )

        assert tree.get_task("0") == root
        assert tree.get_task("1") == sub1
        assert tree.get_task("999") is None

    def test_task_tree_get_children(self):
        """TaskTree can retrieve child tasks"""
        root = SubTask(id="0", description="Root", depth=0)
        child1 = SubTask(id="1", description="Child 1", parent_id="0", depth=1)
        child2 = SubTask(id="2", description="Child 2", parent_id="0", depth=1)
        grandchild = SubTask(id="1.1", description="Grandchild", parent_id="1", depth=2)

        tree = TaskTree(
            session_id="test",
            user_request="Test",
            root_task=root,
            sub_tasks={"1": child1, "2": child2, "1.1": grandchild},
        )

        root_children = tree.get_children("0")
        assert len(root_children) == 2
        assert child1 in root_children
        assert child2 in root_children

        child1_children = tree.get_children("1")
        assert len(child1_children) == 1
        assert grandchild in child1_children

    def test_task_analysis_creation(self):
        """TaskAnalysis can be created"""
        analysis = TaskAnalysis(
            complexity_level=ComplexityLevel.COMPLEX,
            estimated_duration=600.0,
            decomposition_needed=True,
            required_capabilities=["http_tool", "llm"],
            reasoning="Complex task requiring multiple steps",
        )
        assert analysis.complexity_level == ComplexityLevel.COMPLEX
        assert analysis.decomposition_needed is True
        assert "http_tool" in analysis.required_capabilities

    def test_progress_summary_creation(self):
        """ProgressSummary can be created and serialized"""
        summary = ProgressSummary(
            overall_progress=0.5,
            completed_count=3,
            pending_count=2,
            in_progress_count=1,
            elapsed_time=120.0,
            estimated_remaining=120.0,
            current_phase="Phase 2: Implementation",
        )
        assert summary.overall_progress == 0.5
        assert summary.completed_count == 3

        summary_dict = summary.to_dict()
        assert summary_dict["overall_progress"] == 0.5


class TestBasicDecomposition:
    """Level 1 - Verify basic decomposition functionality"""

    @pytest.mark.asyncio
    async def test_rule_based_analysis_simple_task(self):
        """Rule-based analysis classifies simple tasks correctly"""
        decomposer = TaskDecomposer(llm_service=None)
        analysis = await decomposer.analyze_task("What is 5 + 3?")

        assert analysis is not None
        assert analysis.complexity_level == ComplexityLevel.SIMPLE
        assert analysis.decomposition_needed is False

    @pytest.mark.asyncio
    async def test_rule_based_analysis_complex_task(self):
        """Rule-based analysis classifies complex tasks correctly"""
        decomposer = TaskDecomposer(llm_service=None)
        analysis = await decomposer.analyze_task(
            "Implement a complete user authentication system with JWT tokens, "
            "refresh tokens, role-based access control, and password reset functionality"
        )

        assert analysis is not None
        assert analysis.complexity_level in [ComplexityLevel.COMPLEX, ComplexityLevel.EXPERT]
        assert analysis.decomposition_needed is True

    @pytest.mark.asyncio
    async def test_dummy_tree_creation(self):
        """Decomposer creates valid dummy tree (Phase 1)"""
        decomposer = TaskDecomposer(llm_service=None)
        tree = await decomposer.decompose_task("Build a REST API")

        assert tree is not None
        assert tree.root_task is not None
        assert tree.root_task.id == "0"
        assert len(tree.sub_tasks) > 0

        # Verify hierarchical structure
        phase_tasks = [t for t in tree.sub_tasks.values() if t.depth == 1]
        assert len(phase_tasks) > 0

        # Verify dependencies exist
        tasks_with_deps = [t for t in tree.sub_tasks.values() if len(t.dependencies) > 0]
        assert len(tasks_with_deps) > 0

    @pytest.mark.asyncio
    async def test_get_ready_tasks(self):
        """TaskTree correctly identifies ready-to-execute tasks"""
        root = SubTask(id="0", description="Root", depth=0)
        task1 = SubTask(id="1", description="Task 1", parent_id="0", depth=1,
                        status=TaskStatus.PENDING, dependencies=[])
        task2 = SubTask(id="2", description="Task 2", parent_id="0", depth=1,
                        status=TaskStatus.PENDING, dependencies=["1"])
        task3 = SubTask(id="3", description="Task 3", parent_id="0", depth=1,
                        status=TaskStatus.COMPLETED, dependencies=[])

        tree = TaskTree(
            session_id="test",
            user_request="Test",
            root_task=root,
            sub_tasks={"1": task1, "2": task2, "3": task3},
        )

        ready_tasks = tree.get_ready_tasks()

        # Task 1 should be ready (pending, no dependencies)
        # Task 2 should NOT be ready (depends on task 1 which is not completed)
        # Task 3 should NOT be ready (already completed)
        assert len(ready_tasks) == 1
        assert task1 in ready_tasks
        assert task2 not in ready_tasks


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
