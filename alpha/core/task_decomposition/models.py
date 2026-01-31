"""
Data models for Task Decomposition System (REQ-8.1)

Defines core data structures for hierarchical task representation,
progress tracking, and execution orchestration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ComplexityLevel(str, Enum):
    """Task complexity classification"""
    SIMPLE = "simple"        # 1-2 steps, <1min
    MEDIUM = "medium"        # 3-5 steps, 1-10min
    COMPLEX = "complex"      # 6-15 steps, 10-60min
    EXPERT = "expert"        # 15+ steps, >60min


class ExecutionStrategy(str, Enum):
    """Task execution strategy"""
    SEQUENTIAL = "sequential"  # Execute tasks one by one
    PARALLEL = "parallel"      # Execute independent tasks in parallel
    HYBRID = "hybrid"          # Mix of sequential and parallel


@dataclass
class SubTask:
    """
    Represents a single sub-task in the decomposition tree.

    Attributes:
        id: Unique identifier (e.g., "1.2.3" for hierarchical tracking)
        description: Human-readable task description
        parent_id: ID of parent task (None for root)
        depth: Nesting depth (0=root, 1=direct child, etc.)
        status: Current execution status
        dependencies: List of task IDs that must complete first
        estimated_duration: Estimated execution time in seconds
        actual_duration: Actual execution time (None until completed)
        result: Execution result data
        error: Error message if failed
        metadata: Additional task-specific data
        created_at: Task creation timestamp
        started_at: Execution start timestamp
        completed_at: Execution completion timestamp
    """
    id: str
    description: str
    parent_id: Optional[str] = None
    depth: int = 0
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: float = 10.0  # seconds
    actual_duration: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage"""
        return {
            "id": self.id,
            "description": self.description,
            "parent_id": self.parent_id,
            "depth": self.depth,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "estimated_duration": self.estimated_duration,
            "actual_duration": self.actual_duration,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubTask":
        """Deserialize from dictionary"""
        data = data.copy()
        data["status"] = TaskStatus(data["status"])
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        return cls(**data)


@dataclass
class TaskTree:
    """
    Hierarchical representation of decomposed task.

    Attributes:
        session_id: Unique session identifier
        user_request: Original user request
        root_task: Top-level task (id="0")
        sub_tasks: Dictionary of all sub-tasks (task_id -> SubTask)
        execution_strategy: How to execute tasks (sequential/parallel/hybrid)
        total_estimated_duration: Sum of all task estimates
        metadata: Additional tree-level data
    """
    session_id: str
    user_request: str
    root_task: SubTask
    sub_tasks: Dict[str, SubTask] = field(default_factory=dict)
    execution_strategy: ExecutionStrategy = ExecutionStrategy.HYBRID
    total_estimated_duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_task(self, task_id: str) -> Optional[SubTask]:
        """Get task by ID"""
        if task_id == self.root_task.id:
            return self.root_task
        return self.sub_tasks.get(task_id)

    def get_children(self, parent_id: str) -> List[SubTask]:
        """Get all direct children of a task"""
        return [
            task for task in self.sub_tasks.values()
            if task.parent_id == parent_id
        ]

    def get_ready_tasks(self) -> List[SubTask]:
        """Get tasks ready to execute (pending + dependencies met)"""
        ready = []
        for task in self.sub_tasks.values():
            if task.status != TaskStatus.PENDING:
                continue

            # Check if all dependencies completed
            deps_met = all(
                self.get_task(dep_id) and self.get_task(dep_id).status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )

            if deps_met:
                ready.append(task)

        return ready

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "session_id": self.session_id,
            "user_request": self.user_request,
            "root_task": self.root_task.to_dict(),
            "sub_tasks": {k: v.to_dict() for k, v in self.sub_tasks.items()},
            "execution_strategy": self.execution_strategy.value,
            "total_estimated_duration": self.total_estimated_duration,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskTree":
        """Deserialize from dictionary"""
        data = data.copy()
        data["root_task"] = SubTask.from_dict(data["root_task"])
        data["sub_tasks"] = {k: SubTask.from_dict(v) for k, v in data["sub_tasks"].items()}
        data["execution_strategy"] = ExecutionStrategy(data["execution_strategy"])
        return cls(**data)


@dataclass
class TaskAnalysis:
    """
    Analysis result from TaskDecomposer.analyze_task()

    Attributes:
        complexity_level: Classified complexity (simple/medium/complex/expert)
        estimated_duration: Total estimated time in seconds
        decomposition_needed: Whether task should be decomposed
        required_capabilities: List of tools/skills needed
        reasoning: Explanation of analysis
    """
    complexity_level: ComplexityLevel
    estimated_duration: float
    decomposition_needed: bool
    required_capabilities: List[str] = field(default_factory=list)
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "complexity_level": self.complexity_level.value,
            "estimated_duration": self.estimated_duration,
            "decomposition_needed": self.decomposition_needed,
            "required_capabilities": self.required_capabilities,
            "reasoning": self.reasoning,
        }


@dataclass
class ProgressSummary:
    """
    Real-time progress summary

    Attributes:
        overall_progress: Completion percentage (0.0 to 1.0)
        completed_count: Number of completed tasks
        pending_count: Number of pending tasks
        in_progress_count: Number of running tasks
        failed_count: Number of failed tasks
        skipped_count: Number of skipped tasks
        elapsed_time: Time since execution started (seconds)
        estimated_remaining: Estimated time to completion (seconds)
        current_phase: Current execution phase description
        current_task_id: ID of currently executing task
        current_task_description: Description of current task
    """
    overall_progress: float = 0.0
    completed_count: int = 0
    pending_count: int = 0
    in_progress_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    elapsed_time: float = 0.0
    estimated_remaining: float = 0.0
    current_phase: str = ""
    current_task_id: Optional[str] = None
    current_task_description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "overall_progress": self.overall_progress,
            "completed_count": self.completed_count,
            "pending_count": self.pending_count,
            "in_progress_count": self.in_progress_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "elapsed_time": self.elapsed_time,
            "estimated_remaining": self.estimated_remaining,
            "current_phase": self.current_phase,
            "current_task_id": self.current_task_id,
            "current_task_description": self.current_task_description,
        }


@dataclass
class ExecutionPhase:
    """
    Group of tasks that can be executed together

    Attributes:
        phase_id: Numeric phase identifier
        tasks: List of tasks in this phase
        strategy: Execution strategy for this phase
    """
    phase_id: int
    tasks: List[SubTask]
    strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL


@dataclass
class SubTaskResult:
    """
    Result of executing a single sub-task

    Attributes:
        task_id: ID of executed task
        success: Whether execution succeeded
        result: Execution output data
        error: Error message if failed
        duration: Actual execution time in seconds
    """
    task_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class ExecutionResult:
    """
    Final result of executing entire task tree

    Attributes:
        session_id: Session identifier
        success: Whether overall execution succeeded
        results: Dictionary of task_id -> result
        summary: Final progress summary
        error: Error message if failed
        partial_results: Results from partially completed execution
    """
    session_id: str
    success: bool
    results: Dict[str, Any] = field(default_factory=dict)
    summary: Optional[ProgressSummary] = None
    error: Optional[str] = None
    partial_results: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "session_id": self.session_id,
            "success": self.success,
            "results": self.results,
            "summary": self.summary.to_dict() if self.summary else None,
            "error": self.error,
            "partial_results": self.partial_results,
        }
