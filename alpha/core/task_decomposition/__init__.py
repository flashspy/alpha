"""
Task Decomposition System (REQ-8.1)

Intelligent task decomposition and progress tracking for complex multi-step tasks.

Core Components:
- TaskDecomposer: LLM-powered task analysis and decomposition
- ProgressTracker: Real-time progress tracking with persistence
- ExecutionCoordinator: Sub-task orchestration and execution
- ProgressDisplay: CLI visualization with rich formatting

Features:
- Hierarchical task breakdown (root → sub-tasks → atomic steps)
- Dependency resolution and parallel execution
- Real-time progress updates with ETA
- Adaptive re-decomposition based on results
- SQLite persistence for cross-restart recovery
"""

from alpha.core.task_decomposition.coordinator import ExecutionCoordinator
from alpha.core.task_decomposition.decomposer import TaskDecomposer
from alpha.core.task_decomposition.models import (
    ComplexityLevel,
    ExecutionPhase,
    ExecutionResult,
    ExecutionStrategy,
    ProgressSummary,
    SubTask,
    SubTaskResult,
    TaskAnalysis,
    TaskStatus,
    TaskTree,
)
from alpha.core.task_decomposition.storage import ProgressStorage
from alpha.core.task_decomposition.tracker import ProgressTracker

__all__ = [
    # Core Components
    "TaskDecomposer",
    "ProgressTracker",
    "ExecutionCoordinator",
    "ProgressStorage",
    # Data Models
    "ComplexityLevel",
    "ExecutionStrategy",
    "ExecutionPhase",
    "ExecutionResult",
    "ProgressSummary",
    "SubTask",
    "SubTaskResult",
    "TaskAnalysis",
    "TaskStatus",
    "TaskTree",
]
