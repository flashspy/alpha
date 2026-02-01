"""
Tests for FeedbackLoop integration with AlphaEngine (REQ-5.1.5) - Fixed Version.

This test suite validates that the self-improvement loop is correctly integrated
into AlphaEngine and operates as expected.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta

from alpha.core.engine import AlphaEngine
from alpha.utils.config import Config
from alpha.learning import (
    FeedbackLoop,
    FeedbackLoopConfig,
    FeedbackLoopMode,
    LogAnalyzer,
    ImprovementExecutor,
    LearningStore
)


class TestFeedbackLoopIntegrationInitialization:
    """Test initialization of feedback loop in AlphaEngine."""

    def test_feedback_loop_disabled_by_default(self):
        """Test that feedback loop is disabled when not in config."""
        config = Mock(spec=Config)
        config.memory = Mock(database="test.db")
        config.proactive = {}
        # No improvement_loop config
        del config.improvement_loop

        engine = AlphaEngine(config)

        assert engine.feedback_loop is None
        assert engine.learning_store is None
        assert engine.log_analyzer is None
        assert engine.improvement_executor is None

    def test_feedback_loop_enabled_in_config(self):
        """Test that feedback loop is initialized when enabled in config."""
        config = Mock(spec=Config)
        config.memory = Mock(database="test.db")
        config.config_file = "test_config.yaml"
        config.proactive = {}

        # Enable improvement_loop
        config.improvement_loop = {
            'enabled': True,
            'database': 'test_learning.db',
            'check_interval': 86400,
            'min_uptime_for_analysis': 3600,
            'config': {
                'mode': 'semi_auto',
                'analysis_days': 7,
                'min_confidence': 0.7,
                'max_daily_improvements': 5,
                'enable_rollback': True,
                'dry_run_first': True
            }
        }

        with patch('alpha.core.engine.LearningStore'):
            with patch('alpha.core.engine.LogAnalyzer'):
                with patch('alpha.core.engine.ImprovementExecutor'):
                    with patch('alpha.core.engine.FeedbackLoop'):
                        engine = AlphaEngine(config)

        assert engine.feedback_loop is not None
        assert engine.learning_store is not None
        assert engine.log_analyzer is not None
        assert engine.improvement_executor is not None

    def test_feedback_loop_mode_parsing(self):
        """Test that FeedbackLoopMode is correctly parsed from config."""
        config = Mock(spec=Config)
        config.memory = Mock(database="test.db")
        config.config_file = "test_config.yaml"
        config.proactive = {}

        for mode_str in ['manual', 'semi_auto', 'full_auto']:
            config.improvement_loop = {
                'enabled': True,
                'database': 'test_learning.db',
                'config': {
                    'mode': mode_str,
                    'analysis_days': 7
                }
            }

            with patch('alpha.core.engine.LearningStore'):
                with patch('alpha.core.engine.LogAnalyzer'):
                    with patch('alpha.core.engine.ImprovementExecutor'):
                        with patch('alpha.core.engine.FeedbackLoop') as mock_fl:
                            engine = AlphaEngine(config)

                            # Verify FeedbackLoop was called with correct mode
                            call_args = mock_fl.call_args
                            loop_config = call_args[1]['config']
                            assert loop_config.mode == FeedbackLoopMode(mode_str)


class TestFeedbackLoopLifecycle:
    """Test feedback loop lifecycle (startup/shutdown)."""

    @pytest.mark.asyncio
    async def test_feedback_loop_starts_on_engine_startup(self):
        """Test that feedback loop starts when engine starts."""
        config = Mock(spec=Config)
        config.memory = Mock(database=":memory:")
        config.config_file = "test_config.yaml"
        config.proactive = {}

        config.improvement_loop = {
            'enabled': True,
            'database': ':memory:',
            'config': {'mode': 'semi_auto', 'analysis_days': 7}
        }

        with patch('alpha.core.engine.LearningStore'):
            with patch('alpha.core.engine.LogAnalyzer'):
                with patch('alpha.core.engine.ImprovementExecutor'):
                    mock_feedback_loop = AsyncMock(spec=FeedbackLoop)
                    mock_feedback_loop.start = AsyncMock()

                    with patch('alpha.core.engine.FeedbackLoop', return_value=mock_feedback_loop):
                        engine = AlphaEngine(config)
                        engine.memory_manager = AsyncMock()
                        engine.task_manager = AsyncMock()
                        engine.event_bus = AsyncMock()

                        await engine.startup()

                        # Verify feedback loop was started
                        mock_feedback_loop.start.assert_called_once()
                        assert engine.improvement_task is not None

    @pytest.mark.asyncio
    async def test_feedback_loop_stops_on_engine_shutdown(self):
        """Test that feedback loop stops when engine shuts down."""
        config = Mock(spec=Config)
        config.memory = Mock(database=":memory:")
        config.config_file = "test_config.yaml"
        config.proactive = {}

        config.improvement_loop = {
            'enabled': True,
            'database': ':memory:',
            'config': {'mode': 'semi_auto', 'analysis_days': 7}
        }

        with patch('alpha.core.engine.LearningStore'):
            with patch('alpha.core.engine.LogAnalyzer'):
                with patch('alpha.core.engine.ImprovementExecutor'):
                    mock_feedback_loop = AsyncMock(spec=FeedbackLoop)
                    mock_feedback_loop.start = AsyncMock()
                    mock_feedback_loop.stop = AsyncMock()

                    with patch('alpha.core.engine.FeedbackLoop', return_value=mock_feedback_loop):
                        engine = AlphaEngine(config)
                        engine.memory_manager = AsyncMock()
                        engine.task_manager = AsyncMock()
                        engine.event_bus = AsyncMock()

                        # Start engine
                        await engine.startup()

                        # Create proper async task for improvement_task
                        async def dummy_loop():
                            await asyncio.sleep(100)

                        engine.improvement_task = asyncio.create_task(dummy_loop())

                        # Shutdown engine
                        await engine.shutdown()

                        # Verify feedback loop was stopped
                        mock_feedback_loop.stop.assert_called_once()


class TestImprovementLoop:
    """Test the _improvement_loop background task."""

    @pytest.mark.asyncio
    async def test_improvement_loop_runs_periodically(self):
        """Test that improvement loop runs on schedule."""
        config = Mock(spec=Config)
        config.memory = Mock(database=":memory:")
        config.config_file = "test_config.yaml"
        config.proactive = {}

        config.improvement_loop = {
            'enabled': True,
            'database': ':memory:',
            'check_interval': 1,  # 1 second for testing
            'min_uptime_for_analysis': 0,  # No minimum uptime
            'config': {'mode': 'semi_auto', 'analysis_days': 7}
        }

        with patch('alpha.core.engine.LearningStore'):
            with patch('alpha.core.engine.LogAnalyzer'):
                with patch('alpha.core.engine.ImprovementExecutor'):
                    mock_feedback_loop = AsyncMock(spec=FeedbackLoop)
                    mock_feedback_loop.run_cycle = AsyncMock(return_value={
                        'cycle_number': 1,
                        'summary': {},
                        'steps': {'analysis': {'pattern_count': 0}, 'apply': {'applied_count': 0}}
                    })

                    with patch('alpha.core.engine.FeedbackLoop', return_value=mock_feedback_loop):
                        engine = AlphaEngine(config)
                        engine.memory_manager = AsyncMock()
                        engine.start_time = datetime.now()
                        engine.running = True

                        # Run loop for short time
                        loop_task = asyncio.create_task(engine._improvement_loop())
                        await asyncio.sleep(2.5)  # Let it run 2+ cycles
                        loop_task.cancel()

                        try:
                            await loop_task
                        except asyncio.CancelledError:
                            pass

                        # Verify run_cycle was called at least twice
                        assert mock_feedback_loop.run_cycle.call_count >= 2

    @pytest.mark.asyncio
    async def test_improvement_loop_respects_min_uptime(self):
        """Test that improvement loop waits for minimum uptime."""
        config = Mock(spec=Config)
        config.memory = Mock(database=":memory:")
        config.config_file = "test_config.yaml"
        config.proactive = {}

        config.improvement_loop = {
            'enabled': True,
            'database': ':memory:',
            'check_interval': 1,  # 1 second for testing
            'min_uptime_for_analysis': 10,  # 10 seconds minimum uptime
            'config': {'mode': 'semi_auto', 'analysis_days': 7}
        }

        with patch('alpha.core.engine.LearningStore'):
            with patch('alpha.core.engine.LogAnalyzer'):
                with patch('alpha.core.engine.ImprovementExecutor'):
                    mock_feedback_loop = AsyncMock(spec=FeedbackLoop)
                    mock_feedback_loop.run_cycle = AsyncMock(return_value={})

                    with patch('alpha.core.engine.FeedbackLoop', return_value=mock_feedback_loop):
                        engine = AlphaEngine(config)
                        engine.memory_manager = AsyncMock()
                        engine.start_time = datetime.now()  # Just started
                        engine.running = True

                        # Run loop for short time
                        loop_task = asyncio.create_task(engine._improvement_loop())
                        await asyncio.sleep(2.5)
                        loop_task.cancel()

                        try:
                            await loop_task
                        except asyncio.CancelledError:
                            pass

                        # run_cycle should NOT have been called (uptime too short)
                        mock_feedback_loop.run_cycle.assert_not_called()

    @pytest.mark.asyncio
    async def test_improvement_loop_handles_exceptions(self):
        """Test that improvement loop recovers from exceptions."""
        config = Mock(spec=Config)
        config.memory = Mock(database=":memory:")
        config.config_file = "test_config.yaml"
        config.proactive = {}

        config.improvement_loop = {
            'enabled': True,
            'database': ':memory:',
            'check_interval': 1,
            'min_uptime_for_analysis': 0,
            'config': {'mode': 'semi_auto', 'analysis_days': 7}
        }

        with patch('alpha.core.engine.LearningStore'):
            with patch('alpha.core.engine.LogAnalyzer'):
                with patch('alpha.core.engine.ImprovementExecutor'):
                    mock_feedback_loop = AsyncMock(spec=FeedbackLoop)
                    # First call raises exception, second call succeeds
                    mock_feedback_loop.run_cycle = AsyncMock(
                        side_effect=[
                            Exception("Test error"),
                            {'cycle_number': 2, 'summary': {}, 'steps': {'analysis': {}, 'apply': {}}}
                        ]
                    )

                    with patch('alpha.core.engine.FeedbackLoop', return_value=mock_feedback_loop):
                        engine = AlphaEngine(config)
                        engine.memory_manager = AsyncMock()
                        engine.start_time = datetime.now()
                        engine.running = True

                        # Run loop
                        loop_task = asyncio.create_task(engine._improvement_loop())
                        await asyncio.sleep(2.5)
                        loop_task.cancel()

                        try:
                            await loop_task
                        except asyncio.CancelledError:
                            pass

                        # Verify run_cycle was called at least twice (recovered from error)
                        assert mock_feedback_loop.run_cycle.call_count >= 2


class TestHealthCheck:
    """Test health check integration."""

    @pytest.mark.asyncio
    async def test_health_check_includes_improvement_status(self):
        """Test that health check includes improvement loop status."""
        config = Mock(spec=Config)
        config.memory = Mock(database=":memory:")
        config.config_file = "test_config.yaml"
        config.proactive = {}

        config.improvement_loop = {
            'enabled': True,
            'database': ':memory:',
            'config': {'mode': 'semi_auto', 'analysis_days': 7}
        }

        with patch('alpha.core.engine.LearningStore'):
            with patch('alpha.core.engine.LogAnalyzer'):
                with patch('alpha.core.engine.ImprovementExecutor'):
                    mock_feedback_loop = AsyncMock(spec=FeedbackLoop)
                    mock_feedback_loop.cycle_count = 5
                    mock_feedback_loop.last_cycle_time = datetime.now()

                    with patch('alpha.core.engine.FeedbackLoop', return_value=mock_feedback_loop):
                        engine = AlphaEngine(config)
                        engine.memory_manager = AsyncMock()
                        engine.memory_manager.get_stats = AsyncMock(return_value={})
                        engine.task_manager = AsyncMock()
                        engine.task_manager.get_stats = AsyncMock(return_value={})
                        engine.start_time = datetime.now()
                        engine.running = True

                        # Create mock improvement task
                        engine.improvement_task = Mock()
                        engine.improvement_task.done = Mock(return_value=False)

                        health = await engine.health_check()

                        # Verify health includes self_improvement section
                        assert 'self_improvement' in health
                        assert health['self_improvement']['enabled'] is True
                        assert health['self_improvement']['loop_running'] is True
                        assert health['self_improvement']['cycle_count'] == 5
                        assert health['self_improvement']['last_cycle'] is not None

    @pytest.mark.asyncio
    async def test_health_check_without_improvement_loop(self):
        """Test that health check works without improvement loop."""
        config = Mock(spec=Config)
        config.memory = Mock(database=":memory:")
        config.proactive = {}
        del config.improvement_loop

        engine = AlphaEngine(config)
        engine.memory_manager = AsyncMock()
        engine.memory_manager.get_stats = AsyncMock(return_value={})
        engine.task_manager = AsyncMock()
        engine.task_manager.get_stats = AsyncMock(return_value={})
        engine.start_time = datetime.now()
        engine.running = True

        health = await engine.health_check()

        # Verify health does NOT include self_improvement section
        assert 'self_improvement' not in health
