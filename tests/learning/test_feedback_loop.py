"""
Tests for FeedbackLoop - continuous learning orchestration.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from alpha.learning.feedback_loop import (
    FeedbackLoop,
    FeedbackLoopConfig,
    FeedbackLoopMode
)
from alpha.learning.log_analyzer import LogAnalyzer
from alpha.learning.improvement_executor import ImprovementExecutor
from alpha.learning.learning_store import LearningStore


@pytest.fixture
def temp_dirs():
    """Create temporary directories."""
    log_dir = tempfile.mkdtemp()
    db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)

    # Write minimal config
    import yaml
    config = {
        "alpha": {"name": "Test"},
        "llm": {"default_provider": "deepseek", "providers": {"deepseek": {}}},
        "tasks": {"timeouts": {}}
    }
    yaml.dump(config, config_file)
    config_file.close()

    yield {
        "log_dir": log_dir,
        "db_path": db_file.name,
        "config_path": config_file.name
    }

    # Cleanup
    import shutil
    shutil.rmtree(log_dir, ignore_errors=True)
    Path(db_file.name).unlink(missing_ok=True)
    Path(config_file.name).unlink(missing_ok=True)


@pytest.fixture
def feedback_loop_components(temp_dirs):
    """Create feedback loop components."""
    log_analyzer = LogAnalyzer(log_dir=temp_dirs["log_dir"])
    improvement_executor = ImprovementExecutor(config_path=temp_dirs["config_path"])
    learning_store = LearningStore(db_path=temp_dirs["db_path"])
    learning_store.initialize()

    yield {
        "log_analyzer": log_analyzer,
        "improvement_executor": improvement_executor,
        "learning_store": learning_store
    }

    learning_store.close()


@pytest.fixture
def feedback_loop(feedback_loop_components):
    """Create feedback loop instance."""
    config = FeedbackLoopConfig(
        mode=FeedbackLoopMode.MANUAL,
        analysis_frequency="daily",
        analysis_days=7,
        min_confidence=0.7
    )

    return FeedbackLoop(
        config=config,
        log_analyzer=feedback_loop_components["log_analyzer"],
        improvement_executor=feedback_loop_components["improvement_executor"],
        learning_store=feedback_loop_components["learning_store"]
    )


def test_feedback_loop_initialization(feedback_loop):
    """Test FeedbackLoop initialization."""
    assert feedback_loop.running is False
    assert feedback_loop.cycle_count == 0
    assert feedback_loop.config.mode == FeedbackLoopMode.MANUAL


@pytest.mark.asyncio
async def test_start_feedback_loop(feedback_loop):
    """Test starting feedback loop."""
    await feedback_loop.start()

    assert feedback_loop.running is True

    await feedback_loop.stop()


@pytest.mark.asyncio
async def test_stop_feedback_loop(feedback_loop):
    """Test stopping feedback loop."""
    await feedback_loop.start()
    await feedback_loop.stop()

    assert feedback_loop.running is False


@pytest.mark.asyncio
async def test_run_cycle(feedback_loop):
    """Test running a learning cycle."""
    await feedback_loop.start()

    result = await feedback_loop.run_cycle()

    assert "cycle_number" in result
    assert "started_at" in result
    assert "steps" in result
    assert result["cycle_number"] == 1

    await feedback_loop.stop()


@pytest.mark.asyncio
async def test_cycle_increments(feedback_loop):
    """Test that cycle count increments."""
    await feedback_loop.start()

    await feedback_loop.run_cycle()
    await feedback_loop.run_cycle()

    assert feedback_loop.cycle_count == 2

    await feedback_loop.stop()


@pytest.mark.asyncio
async def test_manual_trigger(feedback_loop):
    """Test manually triggering a cycle."""
    result = await feedback_loop.manual_trigger()

    assert result is not None
    assert "cycle_number" in result


def test_get_status(feedback_loop):
    """Test getting feedback loop status."""
    status = feedback_loop.get_status()

    assert "running" in status
    assert "mode" in status
    assert "cycle_count" in status
    assert status["mode"] == FeedbackLoopMode.MANUAL.value


def test_get_statistics(feedback_loop):
    """Test getting feedback loop statistics."""
    stats = feedback_loop.get_statistics()

    assert "feedback_loop" in stats
    assert "learning_store" in stats
    assert "improvements" in stats


def test_config_modes():
    """Test different feedback loop modes."""
    # Manual mode
    manual_config = FeedbackLoopConfig(mode=FeedbackLoopMode.MANUAL)
    assert manual_config.mode == FeedbackLoopMode.MANUAL

    # Semi-auto mode
    semi_config = FeedbackLoopConfig(mode=FeedbackLoopMode.SEMI_AUTO)
    assert semi_config.mode == FeedbackLoopMode.SEMI_AUTO

    # Full-auto mode
    auto_config = FeedbackLoopConfig(mode=FeedbackLoopMode.FULL_AUTO)
    assert auto_config.mode == FeedbackLoopMode.FULL_AUTO


def test_config_defaults():
    """Test default configuration values."""
    config = FeedbackLoopConfig()

    assert config.mode == FeedbackLoopMode.SEMI_AUTO
    assert config.analysis_frequency == "daily"
    assert config.analysis_days == 7
    assert config.min_confidence == 0.7
    assert config.max_daily_improvements == 5
    assert config.enable_rollback is True
    assert config.dry_run_first is True


@pytest.mark.asyncio
async def test_should_auto_apply_manual_mode(feedback_loop_components):
    """Test auto-apply decision in manual mode."""
    config = FeedbackLoopConfig(mode=FeedbackLoopMode.MANUAL)
    loop = FeedbackLoop(config=config, **feedback_loop_components)

    from alpha.learning.log_analyzer import (
        ImprovementRecommendation,
        Priority,
        LogPattern,
        PatternType
    )

    pattern = LogPattern(
        pattern_type=PatternType.SLOW_OPERATION,
        description="Test",
        occurrences=5,
        impact_score=5.0
    )

    rec = ImprovementRecommendation(
        title="Test",
        description="Test",
        priority=Priority.HIGH,
        pattern=pattern,
        action_type="config_update",
        action_data={},
        confidence=0.9
    )

    should_apply = loop._should_auto_apply(rec)
    assert should_apply is False


@pytest.mark.asyncio
async def test_should_auto_apply_full_auto_mode(feedback_loop_components):
    """Test auto-apply decision in full-auto mode."""
    config = FeedbackLoopConfig(mode=FeedbackLoopMode.FULL_AUTO)
    loop = FeedbackLoop(config=config, **feedback_loop_components)

    from alpha.learning.log_analyzer import (
        ImprovementRecommendation,
        Priority,
        LogPattern,
        PatternType
    )

    pattern = LogPattern(
        pattern_type=PatternType.SLOW_OPERATION,
        description="Test",
        occurrences=5,
        impact_score=5.0
    )

    rec = ImprovementRecommendation(
        title="Test",
        description="Test",
        priority=Priority.HIGH,
        pattern=pattern,
        action_type="config_update",
        action_data={},
        confidence=0.9
    )

    should_apply = loop._should_auto_apply(rec)
    assert should_apply is True


@pytest.mark.asyncio
async def test_should_auto_apply_semi_auto_safe(feedback_loop_components):
    """Test auto-apply decision for safe actions in semi-auto mode."""
    config = FeedbackLoopConfig(mode=FeedbackLoopMode.SEMI_AUTO)
    loop = FeedbackLoop(config=config, **feedback_loop_components)

    from alpha.learning.log_analyzer import (
        ImprovementRecommendation,
        Priority,
        LogPattern,
        PatternType
    )

    pattern = LogPattern(
        pattern_type=PatternType.SLOW_OPERATION,
        description="Test",
        occurrences=5,
        impact_score=5.0
    )

    # Safe action with high confidence
    rec = ImprovementRecommendation(
        title="Test",
        description="Test",
        priority=Priority.HIGH,
        pattern=pattern,
        action_type="config_update",  # Safe action
        action_data={},
        confidence=0.9  # High confidence
    )

    should_apply = loop._should_auto_apply(rec)
    assert should_apply is True


@pytest.mark.asyncio
async def test_should_auto_apply_semi_auto_unsafe(feedback_loop_components):
    """Test auto-apply decision for unsafe actions in semi-auto mode."""
    config = FeedbackLoopConfig(mode=FeedbackLoopMode.SEMI_AUTO)
    loop = FeedbackLoop(config=config, **feedback_loop_components)

    from alpha.learning.log_analyzer import (
        ImprovementRecommendation,
        Priority,
        LogPattern,
        PatternType
    )

    pattern = LogPattern(
        pattern_type=PatternType.SLOW_OPERATION,
        description="Test",
        occurrences=5,
        impact_score=5.0
    )

    # Unsafe action
    rec = ImprovementRecommendation(
        title="Test",
        description="Test",
        priority=Priority.HIGH,
        pattern=pattern,
        action_type="tool_strategy",  # Potentially unsafe
        action_data={},
        confidence=0.9
    )

    should_apply = loop._should_auto_apply(rec)
    assert should_apply is False
