"""
Tests for TaskDecompositionManager (REQ-8.1 Phase 4)

Integration tests for the high-level manager that coordinates
task decomposition workflow in CLI.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from alpha.core.task_decomposition.manager import TaskDecompositionManager
from alpha.core.task_decomposition.models import (
    TaskAnalysis, ComplexityLevel, TaskTree, SubTask, TaskStatus, ExecutionStrategy
)


class TestManagerInitialization:
    """Test TaskDecompositionManager initialization."""

    def test_manager_initialization_with_defaults(self):
        """Test manager initializes with default configuration."""
        llm_service = Mock()
        tool_registry = Mock()

        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry
        )

        assert manager.enabled is True
        assert manager.auto_detect is True
        assert manager.approval_required is True
        assert manager.max_depth == 3

    def test_manager_initialization_with_custom_config(self):
        """Test manager initializes with custom configuration."""
        llm_service = Mock()
        tool_registry = Mock()
        config = {
            'enabled': False,
            'auto_detect': False,
            'approval_required': False,
            'max_depth': 5
        }

        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry,
            config=config
        )

        assert manager.enabled is False
        assert manager.auto_detect is False
        assert manager.approval_required is False
        assert manager.max_depth == 5

    @pytest.mark.asyncio
    async def test_manager_initialize_and_close(self, tmp_path):
        """Test manager lifecycle (initialize and close)."""
        llm_service = Mock()
        tool_registry = Mock()
        storage_path = str(tmp_path / "test_manager.db")

        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry,
            storage_path=storage_path
        )

        # Initialize
        await manager.initialize()

        # Check storage is ready (no _initialized attribute, just verify it works)
        # Storage should be initialized automatically

        await manager.close()
        # Storage connection should be closed


class TestShouldDecompose:
    """Test task decomposition detection logic."""

    def test_should_decompose_disabled(self):
        """Test should_decompose returns False when disabled."""
        llm_service = Mock()
        tool_registry = Mock()
        config = {'enabled': False}

        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry,
            config=config
        )

        result = manager.should_decompose("Implement a complex feature")
        assert result is False

    def test_should_decompose_auto_detect_off(self):
        """Test should_decompose returns False when auto-detect disabled."""
        llm_service = Mock()
        tool_registry = Mock()
        config = {'auto_detect': False}

        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry,
            config=config
        )

        result = manager.should_decompose("Implement a complex feature")
        assert result is False

    def test_should_decompose_simple_query(self):
        """Test should_decompose returns False for simple queries."""
        llm_service = Mock()
        tool_registry = Mock()

        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry
        )

        # Short query, no complexity indicators
        result = manager.should_decompose("What is Python?")
        assert result is False

    def test_should_decompose_complex_query_by_length(self):
        """Test should_decompose returns True for long queries."""
        llm_service = Mock()
        tool_registry = Mock()

        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry
        )

        # Long query with complexity keyword
        query = "Implement a comprehensive user authentication system with JWT tokens and refresh token rotation"
        result = manager.should_decompose(query)
        assert result is True

    def test_should_decompose_complex_query_by_keywords(self):
        """Test should_decompose returns True for queries with complexity keywords."""
        llm_service = Mock()
        tool_registry = Mock()

        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry
        )

        # Contains "implement" and "then" keywords
        query = "Implement authentication, then add authorization, and finally deploy"
        result = manager.should_decompose(query)
        assert result is True


class TestAnalyzeAndDecompose:
    """Test task analysis and decomposition flow."""

    @pytest.mark.asyncio
    async def test_analyze_simple_task_no_decomposition(self, tmp_path):
        """Test simple task analysis returns None (no decomposition needed)."""
        llm_service = Mock()
        tool_registry = Mock()

        # Mock simple task analysis
        simple_analysis = TaskAnalysis(
            complexity_level=ComplexityLevel.SIMPLE,
            estimated_duration=10.0,
            decomposition_needed=False,
            reasoning="Task is straightforward"
        )

        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry,
            storage_path=str(tmp_path / "test.db")
        )
        manager.decomposer.analyze_task = AsyncMock(return_value=simple_analysis)

        result = await manager.analyze_and_decompose("What is Python?")
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_complex_task_with_decomposition(self, tmp_path):
        """Test complex task analysis returns TaskTree."""
        llm_service = Mock()
        tool_registry = Mock()

        # Mock complex task analysis
        complex_analysis = TaskAnalysis(
            complexity_level=ComplexityLevel.COMPLEX,
            estimated_duration=600.0,
            decomposition_needed=True,
            reasoning="Multi-step implementation required"
        )

        # Mock task tree
        root_task = SubTask(
            id="root",
            description="Implement authentication system",
            depth=0,
            status=TaskStatus.PENDING,
            dependencies=[],
            estimated_duration=600.0
        )
        task_tree = TaskTree(
            session_id="test_session",
            user_request="Implement authentication system",
            root_task=root_task,
            sub_tasks={
                "task_1": SubTask(
                    id="task_1",
                    description="Design architecture",
                    depth=1,
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    estimated_duration=120.0
                ),
                "task_2": SubTask(
                    id="task_2",
                    description="Implement JWT tokens",
                    depth=1,
                    status=TaskStatus.PENDING,
                    dependencies=["task_1"],
                    estimated_duration=300.0
                ),
            },
            execution_strategy=ExecutionStrategy.SEQUENTIAL,
            total_estimated_duration=600.0
        )

        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry,
            storage_path=str(tmp_path / "test.db")
        )
        manager.decomposer.analyze_task = AsyncMock(return_value=complex_analysis)
        manager.decomposer.decompose_task = AsyncMock(return_value=task_tree)

        result = await manager.analyze_and_decompose("Implement authentication system")
        assert result is not None
        assert isinstance(result, TaskTree)
        assert len(result.sub_tasks) == 2

    @pytest.mark.asyncio
    async def test_analyze_handles_exceptions(self, tmp_path):
        """Test analyze_and_decompose handles exceptions gracefully."""
        llm_service = Mock()
        tool_registry = Mock()

        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry,
            storage_path=str(tmp_path / "test.db")
        )

        # Mock exception during analysis
        manager.decomposer.analyze_task = AsyncMock(side_effect=Exception("LLM error"))

        result = await manager.analyze_and_decompose("Implement feature")
        assert result is None  # Should return None on error


class TestFormatDecompositionPreview:
    """Test decomposition preview formatting."""

    def test_format_preview_basic(self):
        """Test basic decomposition preview formatting."""
        llm_service = Mock()
        tool_registry = Mock()
        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry
        )

        # Create simple task tree
        root_task = SubTask(
            id="root",
            description="Test Task",
            depth=0,
            status=TaskStatus.PENDING,
            dependencies=[],
            estimated_duration=100.0
        )
        task_tree = TaskTree(
            session_id="test_session",
            user_request="Test request",
            root_task=root_task,
            sub_tasks={
                "task_1": SubTask(
                    id="task_1",
                    description="Step 1",
                    depth=1,
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    estimated_duration=50.0
                ),
                "task_2": SubTask(
                    id="task_2",
                    description="Step 2",
                    depth=1,
                    status=TaskStatus.PENDING,
                    dependencies=["task_1"],
                    estimated_duration=50.0
                ),
            },
            execution_strategy=ExecutionStrategy.SEQUENTIAL,
            total_estimated_duration=100.0
        )

        preview = manager.format_decomposition_preview(task_tree)

        assert "Task Decomposition Preview" in preview
        assert "Test Task" in preview
        assert "Total Sub-tasks: 2" in preview
        assert "Estimated Duration: 100s" in preview
        assert "Step 1" in preview
        assert "Step 2" in preview

    def test_format_preview_with_hierarchy(self):
        """Test preview formatting with hierarchical tasks."""
        llm_service = Mock()
        tool_registry = Mock()
        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry
        )

        # Create hierarchical task tree
        root_task = SubTask(
            id="root",
            description="Parent Task",
            depth=0,
            status=TaskStatus.PENDING,
            dependencies=[],
            estimated_duration=300.0
        )
        task_tree = TaskTree(
            session_id="test_session",
            user_request="Parent Task",
            root_task=root_task,
            sub_tasks={
                "task_1": SubTask(
                    id="task_1",
                    description="Phase 1",
                    depth=1,
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    estimated_duration=100.0,
                    parent_id=None
                ),
                "task_1_1": SubTask(
                    id="task_1_1",
                    description="Phase 1 - Step 1",
                    depth=2,
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    estimated_duration=50.0,
                    parent_id="task_1"
                ),
                "task_1_2": SubTask(
                    id="task_1_2",
                    description="Phase 1 - Step 2",
                    depth=2,
                    status=TaskStatus.PENDING,
                    dependencies=["task_1_1"],
                    estimated_duration=50.0,
                    parent_id="task_1"
                ),
                "task_2": SubTask(
                    id="task_2",
                    description="Phase 2",
                    depth=1,
                    status=TaskStatus.PENDING,
                    dependencies=["task_1"],
                    estimated_duration=200.0,
                    parent_id=None
                ),
            },
            execution_strategy=ExecutionStrategy.SEQUENTIAL,
            total_estimated_duration=300.0
        )

        preview = manager.format_decomposition_preview(task_tree)

        assert "Phase 1" in preview
        assert "Phase 2" in preview
        # Should show children indented
        assert "Phase 1 - Step 1" in preview


class TestSessionManagement:
    """Test session status and history management."""

    @pytest.mark.asyncio
    async def test_get_session_status(self, tmp_path):
        """Test retrieving session status."""
        llm_service = Mock()
        tool_registry = Mock()
        storage_path = str(tmp_path / "test.db")

        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry,
            storage_path=storage_path
        )
        await manager.initialize()

        # Create a session
        root_task = SubTask(
            id="root",
            description="Test",
            depth=0,
            status=TaskStatus.PENDING,
            dependencies=[],
            estimated_duration=10.0
        )
        task_tree = TaskTree(
            session_id="test_session",
            user_request="Test request",
            root_task=root_task,
            sub_tasks={},
            execution_strategy=ExecutionStrategy.SEQUENTIAL,
            total_estimated_duration=10.0
        )

        session_id = manager.storage.create_session(
            session_id="test_session_001",
            user_request="Test request",
            task_tree=task_tree
        )

        # Get session status
        session = await manager.get_session_status(session_id)
        assert session is not None
        assert session["session_id"] == session_id
        assert session["user_request"] == "Test request"

        await manager.close()

    @pytest.mark.asyncio
    async def test_list_recent_sessions(self, tmp_path):
        """Test listing recent sessions."""
        llm_service = Mock()
        tool_registry = Mock()

        manager = TaskDecompositionManager(
            llm_service=llm_service,
            tool_registry=tool_registry,
            storage_path=str(tmp_path / "test.db")
        )

        # Currently returns empty list (placeholder)
        sessions = await manager.list_recent_sessions(limit=10)
        assert isinstance(sessions, list)
