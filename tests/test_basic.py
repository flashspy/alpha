"""
Test basic functionality of Alpha components.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import os

from alpha.events.bus import EventBus, EventType, Event
from alpha.tasks.manager import TaskManager, TaskPriority
from alpha.memory.manager import MemoryManager
from alpha.tools.registry import create_default_registry


@pytest.mark.asyncio
async def test_event_bus():
    """Test event bus functionality."""
    bus = EventBus()
    await bus.initialize()

    # Track events
    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    # Subscribe handler
    bus.subscribe(EventType.USER_INPUT, handler)

    # Publish event
    await bus.publish_event(
        EventType.USER_INPUT,
        {"message": "test"}
    )

    # Give time for processing
    await asyncio.sleep(0.1)

    # Verify
    assert len(received_events) == 1
    assert received_events[0].data["message"] == "test"

    await bus.close()


@pytest.mark.asyncio
async def test_task_manager():
    """Test task manager functionality."""
    bus = EventBus()
    await bus.initialize()

    manager = TaskManager(bus)
    await manager.initialize()

    # Create task
    task = await manager.create_task(
        name="Test Task",
        description="A test task",
        priority=TaskPriority.NORMAL
    )

    assert task.id is not None
    assert task.name == "Test Task"

    # Execute task
    async def executor(task):
        await asyncio.sleep(0.1)
        return "completed"

    await manager.execute_task(task.id, executor)

    # Wait for completion
    await asyncio.sleep(0.2)

    # Verify
    completed_task = await manager.get_task(task.id)
    assert completed_task.result == "completed"

    await bus.close()


@pytest.mark.asyncio
async def test_memory_manager():
    """Test memory manager functionality."""
    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    try:
        manager = MemoryManager(db_path)
        await manager.initialize()

        # Add conversation
        await manager.add_conversation(
            role="user",
            content="Hello"
        )

        await manager.add_conversation(
            role="assistant",
            content="Hi there!"
        )

        # Get history
        history = await manager.get_conversation_history(limit=10)
        assert len(history) == 2

        # Add knowledge
        await manager.set_knowledge("test_key", "test_value")

        # Retrieve knowledge
        value = await manager.get_knowledge("test_key")
        assert value == "test_value"

        # Get stats
        stats = await manager.get_stats()
        assert stats['conversations'] == 2
        assert stats['knowledge'] == 1

        await manager.close()

    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.asyncio
async def test_tool_registry():
    """Test tool registry functionality."""
    registry = create_default_registry()

    # List tools
    tools = registry.list_tools()
    assert len(tools) >= 3  # shell, file, search

    # Test shell tool
    result = await registry.execute_tool(
        "shell",
        command="echo 'Hello World'"
    )
    assert result.success
    assert "Hello World" in result.output

    # Test file tool
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"

        # Write file
        result = await registry.execute_tool(
            "file",
            operation="write",
            path=str(test_file),
            content="Test content"
        )
        assert result.success

        # Read file
        result = await registry.execute_tool(
            "file",
            operation="read",
            path=str(test_file)
        )
        assert result.success
        assert result.output == "Test content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
