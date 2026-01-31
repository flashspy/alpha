"""
Tests for ImprovementExecutor - applying improvements to the system.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from datetime import datetime

from alpha.learning.improvement_executor import (
    ImprovementExecutor,
    ImprovementStatus,
    AppliedImprovement
)
from alpha.learning.log_analyzer import (
    ImprovementRecommendation,
    Priority,
    LogPattern,
    PatternType
)


@pytest.fixture
def temp_config_file():
    """Create temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config = {
            "alpha": {"name": "Test Alpha", "version": "0.1.0"},
            "llm": {
                "default_provider": "deepseek",
                "providers": {
                    "deepseek": {
                        "auto_select_model": False
                    }
                }
            },
            "code_execution": {
                "defaults": {"timeout": 30}
            },
            "tasks": {"timeouts": {}}
        }
        yaml.dump(config, f)
        yield f.name

    Path(f.name).unlink()


@pytest.fixture
def sample_pattern():
    """Create sample pattern."""
    return LogPattern(
        pattern_type=PatternType.SLOW_OPERATION,
        description="Slow operation detected",
        occurrences=5,
        impact_score=7.0,
        metadata={"operation": "test_task", "average_duration": 15.0}
    )


@pytest.fixture
def sample_recommendation(sample_pattern):
    """Create sample recommendation."""
    return ImprovementRecommendation(
        title="Increase timeout for slow task",
        description="Task is timing out frequently",
        priority=Priority.MEDIUM,
        pattern=sample_pattern,
        action_type="config_update",
        action_data={
            "task_name": "slow_task",
            "suggested_timeout": 60
        },
        confidence=0.8
    )


@pytest.mark.asyncio
async def test_executor_initialization(temp_config_file):
    """Test ImprovementExecutor initialization."""
    executor = ImprovementExecutor(config_path=temp_config_file)

    assert executor.config_path == Path(temp_config_file)
    assert executor.applied_improvements == []


@pytest.mark.asyncio
async def test_apply_recommendation_dry_run(temp_config_file, sample_recommendation):
    """Test applying recommendation in dry-run mode."""
    executor = ImprovementExecutor(config_path=temp_config_file)

    result = await executor.apply_recommendation(
        sample_recommendation,
        dry_run=True
    )

    assert isinstance(result, AppliedImprovement)
    assert result.metadata["dry_run"] is True
    assert len(executor.applied_improvements) == 0  # Not added in dry-run


@pytest.mark.asyncio
async def test_apply_recommendation_real(temp_config_file, sample_recommendation):
    """Test applying recommendation for real."""
    executor = ImprovementExecutor(config_path=temp_config_file)

    result = await executor.apply_recommendation(
        sample_recommendation,
        dry_run=False
    )

    assert isinstance(result, AppliedImprovement)
    assert result.status == ImprovementStatus.APPLIED
    assert len(executor.applied_improvements) == 1


@pytest.mark.asyncio
async def test_validation_low_confidence(temp_config_file, sample_pattern):
    """Test that low-confidence recommendations fail validation."""
    executor = ImprovementExecutor(config_path=temp_config_file)

    low_confidence_rec = ImprovementRecommendation(
        title="Test",
        description="Test recommendation",
        priority=Priority.LOW,
        pattern=sample_pattern,
        action_type="config_update",
        action_data={},
        confidence=0.3  # Low confidence
    )

    result = await executor.apply_recommendation(low_confidence_rec)

    assert result.status == ImprovementStatus.FAILED
    assert "confidence" in result.error.lower()


@pytest.mark.asyncio
async def test_config_update_timeout(temp_config_file, sample_recommendation):
    """Test config update for timeout."""
    executor = ImprovementExecutor(config_path=temp_config_file)

    result = await executor.apply_recommendation(
        sample_recommendation,
        dry_run=False
    )

    assert result.status == ImprovementStatus.APPLIED
    assert "path" in result.changes

    # Verify config was updated
    with open(temp_config_file) as f:
        config = yaml.safe_load(f)

    assert "slow_task" in config["tasks"]["timeouts"]
    assert config["tasks"]["timeouts"]["slow_task"] == 60


@pytest.mark.asyncio
async def test_model_routing_update(temp_config_file, sample_pattern):
    """Test model routing update."""
    executor = ImprovementExecutor(config_path=temp_config_file)

    recommendation = ImprovementRecommendation(
        title="Enable auto model selection",
        description="Use cheaper models for simple tasks",
        priority=Priority.HIGH,
        pattern=sample_pattern,
        action_type="model_routing",
        action_data={
            "current_model": "gpt-4",
            "suggested_action": "use_cheaper_model_for_simple_tasks"
        },
        confidence=0.9
    )

    result = await executor.apply_recommendation(recommendation, dry_run=False)

    assert result.status == ImprovementStatus.APPLIED

    # Verify config was updated
    with open(temp_config_file) as f:
        config = yaml.safe_load(f)

    assert config["llm"]["providers"]["deepseek"]["auto_select_model"] is True


@pytest.mark.asyncio
async def test_rollback_improvement(temp_config_file, sample_recommendation):
    """Test rolling back an improvement."""
    executor = ImprovementExecutor(config_path=temp_config_file)

    # Apply improvement
    result = await executor.apply_recommendation(
        sample_recommendation,
        dry_run=False
    )

    improvement_id = result.id

    # Rollback
    success = await executor.rollback_improvement(improvement_id)

    assert success is True
    assert result.status == ImprovementStatus.ROLLED_BACK


@pytest.mark.asyncio
async def test_get_applied_improvements(temp_config_file, sample_recommendation):
    """Test getting applied improvements."""
    executor = ImprovementExecutor(config_path=temp_config_file)

    # Apply some improvements
    await executor.apply_recommendation(sample_recommendation, dry_run=False)

    improvements = await executor.get_applied_improvements()

    assert len(improvements) == 1
    assert improvements[0].status == ImprovementStatus.APPLIED


@pytest.mark.asyncio
async def test_get_improvements_by_status(temp_config_file, sample_recommendation):
    """Test filtering improvements by status."""
    executor = ImprovementExecutor(config_path=temp_config_file)

    # Apply improvement
    result = await executor.apply_recommendation(
        sample_recommendation,
        dry_run=False
    )

    # Get applied improvements
    applied = await executor.get_applied_improvements(
        status=ImprovementStatus.APPLIED
    )

    assert len(applied) == 1
    assert applied[0].status == ImprovementStatus.APPLIED


@pytest.mark.asyncio
async def test_get_statistics(temp_config_file, sample_recommendation):
    """Test getting executor statistics."""
    executor = ImprovementExecutor(config_path=temp_config_file)

    # Apply some improvements
    await executor.apply_recommendation(sample_recommendation, dry_run=False)

    stats = executor.get_statistics()

    assert "total_improvements" in stats
    assert "by_status" in stats
    assert "by_action_type" in stats
    assert "success_rate" in stats
    assert stats["total_improvements"] == 1
