"""
Test proactive intelligence integration with AlphaEngine (REQ-6.1).
"""

import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from alpha.core.engine import AlphaEngine


def create_test_config(tmpdir, proactive_enabled=True):
    """Create a minimal test config object."""
    config = MagicMock()
    config.memory = MagicMock()
    config.memory.database = f'{tmpdir}/test.db'

    if proactive_enabled:
        config.proactive = {
            'enabled': True,
            'database': f'{tmpdir}/proactive.db',
            'pattern_learning': {
                'enabled': True,
                'min_frequency': 3,
                'min_confidence': 0.6
            },
            'task_detection': {
                'enabled': True,
                'min_confidence': 0.7,
                'check_interval': 1,  # Fast for testing
                'max_suggestions': 5
            },
            'auto_execute': {
                'enabled': False,
                'min_confidence': 0.9
            }
        }
    else:
        config.proactive = {
            'enabled': False
        }

    return config


@pytest.mark.asyncio
async def test_proactive_components_initialization():
    """Test that proactive components are initialized when enabled."""
    # Create temporary config with proactive enabled
    with tempfile.TemporaryDirectory() as tmpdir:
        config = create_test_config(tmpdir, proactive_enabled=True)

        engine = AlphaEngine(config)

        # Verify proactive components are initialized
        assert engine.pattern_learner is not None
        assert engine.task_detector is not None
        assert engine.notifier is not None
        assert engine.proactive_task is None  # Not started yet


@pytest.mark.asyncio
async def test_proactive_components_disabled():
    """Test that proactive components are not initialized when disabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = create_test_config(tmpdir, proactive_enabled=False)

        engine = AlphaEngine(config)

        # Verify proactive components are NOT initialized
        assert engine.pattern_learner is None
        assert engine.task_detector is None
        assert engine.notifier is None


@pytest.mark.asyncio
async def test_proactive_startup_and_shutdown():
    """Test that proactive loop starts on startup and stops on shutdown."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = create_test_config(tmpdir, proactive_enabled=True)

        engine = AlphaEngine(config)

        # Start engine
        await engine.startup()

        # Verify proactive loop is running
        assert engine.proactive_task is not None
        assert not engine.proactive_task.done()

        # Wait a bit to ensure loop is active
        await asyncio.sleep(0.5)

        # Shutdown
        await engine.shutdown()

        # Verify proactive loop is stopped
        assert engine.proactive_task.done() or engine.proactive_task.cancelled()


@pytest.mark.asyncio
async def test_health_check_includes_proactive_status():
    """Test that health check includes proactive intelligence status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = create_test_config(tmpdir, proactive_enabled=True)

        engine = AlphaEngine(config)
        await engine.startup()

        # Get health check
        health = await engine.health_check()

        # Verify proactive status is included
        assert "proactive" in health
        assert health["proactive"]["enabled"] is True
        assert "pattern_count" in health["proactive"]
        assert "loop_running" in health["proactive"]

        await engine.shutdown()


@pytest.mark.asyncio
async def test_get_current_context():
    """Test _get_current_context returns valid context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = create_test_config(tmpdir, proactive_enabled=True)

        engine = AlphaEngine(config)
        await engine.startup()

        # Get context
        context = await engine._get_current_context()

        # Verify context structure
        assert "current_time" in context
        assert "running_tasks" in context
        assert "total_tasks" in context
        assert "uptime_seconds" in context
        assert context["uptime_seconds"] >= 0

        await engine.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
