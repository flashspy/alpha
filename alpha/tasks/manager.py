"""
Alpha - Task Manager

Manages task lifecycle, scheduling, and execution.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from alpha.events.bus import EventBus, EventType

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class Task:
    """Task representation."""
    id: str
    name: str
    description: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskManager:
    """
    Manages task lifecycle and execution.

    Features:
    - Priority-based scheduling
    - Async task execution
    - Status tracking
    - Task cancellation
    """

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

    async def initialize(self):
        """Initialize task manager."""
        # Subscribe to relevant events
        self.event_bus.subscribe(EventType.TASK_CREATED, self._on_task_created)
        logger.info("Task manager initialized")

    async def _on_task_created(self, event):
        """Handle task created event."""
        task_id = event.data.get("task_id")
        logger.info(f"Task created event received: {task_id}")

    async def create_task(
        self,
        name: str,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Optional[Dict] = None
    ) -> Task:
        """
        Create a new task.

        Args:
            name: Task name
            description: Task description
            priority: Task priority
            metadata: Additional metadata

        Returns:
            Created task
        """
        task = Task(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            priority=priority,
            metadata=metadata or {}
        )

        self.tasks[task.id] = task
        logger.info(f"Created task: {task.id} - {task.name}")

        # Publish task created event
        await self.event_bus.publish_event(
            EventType.TASK_CREATED,
            {"task_id": task.id, "name": task.name}
        )

        return task

    async def execute_task(self, task_id: str, executor_func):
        """
        Execute a task asynchronously.

        Args:
            task_id: Task ID
            executor_func: Async function to execute the task
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if task.status != TaskStatus.PENDING:
            raise ValueError(f"Task not in pending state: {task_id}")

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        logger.info(f"Executing task: {task_id}")

        # Create async task
        async_task = asyncio.create_task(self._run_task(task, executor_func))
        self.running_tasks[task_id] = async_task

    async def _run_task(self, task: Task, executor_func):
        """Internal task runner with error handling."""
        try:
            result = await executor_func(task)
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()

            logger.info(f"Task completed: {task.id}")

            # Publish completion event
            await self.event_bus.publish_event(
                EventType.TASK_COMPLETED,
                {"task_id": task.id, "result": result}
            )

        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()

            logger.error(f"Task failed: {task.id} - {e}", exc_info=True)

            # Publish failure event
            await self.event_bus.publish_event(
                EventType.TASK_FAILED,
                {"task_id": task.id, "error": str(e)}
            )

        finally:
            # Remove from running tasks
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]

    async def cancel_task(self, task_id: str):
        """Cancel a running task."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            logger.info(f"Task cancelled: {task_id}")

    async def cancel_all(self):
        """Cancel all running tasks."""
        task_ids = list(self.running_tasks.keys())
        for task_id in task_ids:
            await self.cancel_task(task_id)

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.tasks.get(task_id)

    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[Task]:
        """
        List tasks with optional filtering.

        Args:
            status: Filter by status
            limit: Maximum number of tasks to return

        Returns:
            List of tasks
        """
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        # Sort by priority and creation time
        tasks.sort(
            key=lambda t: (t.priority.value, t.created_at),
            reverse=True
        )

        return tasks[:limit]

    async def update_tasks(self):
        """Update task statuses (called from main loop)."""
        # Check for completed async tasks
        for task_id in list(self.running_tasks.keys()):
            async_task = self.running_tasks[task_id]
            if async_task.done():
                del self.running_tasks[task_id]

    async def check_scheduled(self):
        """Check for scheduled tasks to execute."""
        # TODO: Implement scheduled task checking
        pass

    async def reset(self):
        """Reset task manager state."""
        await self.cancel_all()
        logger.info("Task manager reset")

    async def get_stats(self) -> Dict:
        """Get task statistics."""
        total = len(self.tasks)
        by_status = {}

        for status in TaskStatus:
            count = len([t for t in self.tasks.values() if t.status == status])
            by_status[status.value] = count

        return {
            "total": total,
            "running": len(self.running_tasks),
            "by_status": by_status
        }
