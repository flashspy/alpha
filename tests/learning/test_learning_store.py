"""
Tests for LearningStore - persistent storage for learning data.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from alpha.learning.learning_store import LearningStore
from alpha.learning.log_analyzer import LogPattern, PatternType
from alpha.learning.improvement_executor import (
    AppliedImprovement,
    ImprovementStatus
)


@pytest.fixture
def temp_db():
    """Create temporary database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def learning_store(temp_db):
    """Create learning store instance."""
    store = LearningStore(db_path=temp_db)
    store.initialize()
    yield store
    store.close()


@pytest.fixture
def sample_pattern():
    """Create sample pattern."""
    return LogPattern(
        pattern_type=PatternType.RECURRING_ERROR,
        description="Test error pattern",
        occurrences=10,
        impact_score=8.5,
        examples=[{"error": "test"}],
        metadata={"error_type": "TestError"},
        first_seen=datetime.now() - timedelta(days=7),
        last_seen=datetime.now()
    )


@pytest.fixture
def sample_improvement():
    """Create sample improvement."""
    return AppliedImprovement(
        id="test_imp_001",
        recommendation_title="Test Improvement",
        action_type="config_update",
        changes={"path": "test.timeout", "value": 60},
        status=ImprovementStatus.APPLIED,
        applied_at=datetime.now()
    )


def test_learning_store_initialization(temp_db):
    """Test LearningStore initialization."""
    store = LearningStore(db_path=temp_db)
    store.initialize()

    assert store.conn is not None
    assert Path(temp_db).exists()

    store.close()


@pytest.mark.asyncio
async def test_store_pattern(learning_store, sample_pattern):
    """Test storing a pattern."""
    pattern_id = await learning_store.store_pattern(sample_pattern)

    assert pattern_id is not None
    assert pattern_id.startswith("pat_")


@pytest.mark.asyncio
async def test_get_patterns(learning_store, sample_pattern):
    """Test retrieving patterns."""
    await learning_store.store_pattern(sample_pattern)

    patterns = learning_store.get_patterns()

    assert len(patterns) == 1
    assert patterns[0]["pattern_type"] == PatternType.RECURRING_ERROR.value
    assert patterns[0]["occurrences"] == 10


@pytest.mark.asyncio
async def test_get_patterns_by_type(learning_store, sample_pattern):
    """Test filtering patterns by type."""
    await learning_store.store_pattern(sample_pattern)

    # Get by specific type
    error_patterns = learning_store.get_patterns(
        pattern_type=PatternType.RECURRING_ERROR.value
    )

    assert len(error_patterns) == 1

    # Get by different type (should be empty)
    slow_patterns = learning_store.get_patterns(
        pattern_type=PatternType.SLOW_OPERATION.value
    )

    assert len(slow_patterns) == 0


@pytest.mark.asyncio
async def test_get_patterns_by_impact(learning_store, sample_pattern):
    """Test filtering patterns by impact score."""
    await learning_store.store_pattern(sample_pattern)

    # Get patterns with high impact
    high_impact = learning_store.get_patterns(min_impact=8.0)

    assert len(high_impact) == 1

    # Get patterns with very high impact (should be empty)
    very_high = learning_store.get_patterns(min_impact=10.0)

    assert len(very_high) == 0


@pytest.mark.asyncio
async def test_store_improvement(learning_store, sample_improvement):
    """Test storing an improvement."""
    improvement_id = await learning_store.store_improvement(sample_improvement)

    assert improvement_id == sample_improvement.id


@pytest.mark.asyncio
async def test_get_improvements(learning_store, sample_improvement):
    """Test retrieving improvements."""
    await learning_store.store_improvement(sample_improvement)

    improvements = learning_store.get_improvements()

    assert len(improvements) == 1
    assert improvements[0]["improvement_id"] == sample_improvement.id
    assert improvements[0]["status"] == ImprovementStatus.APPLIED.value


@pytest.mark.asyncio
async def test_get_improvements_by_status(learning_store, sample_improvement):
    """Test filtering improvements by status."""
    await learning_store.store_improvement(sample_improvement)

    applied = learning_store.get_improvements(
        status=ImprovementStatus.APPLIED.value
    )

    assert len(applied) == 1

    failed = learning_store.get_improvements(
        status=ImprovementStatus.FAILED.value
    )

    assert len(failed) == 0


@pytest.mark.asyncio
async def test_update_improvement_status(learning_store, sample_improvement):
    """Test updating improvement status."""
    await learning_store.store_improvement(sample_improvement)

    # Update status
    await learning_store.update_improvement_status(
        sample_improvement.id,
        ImprovementStatus.ROLLED_BACK
    )

    # Verify update
    improvements = learning_store.get_improvements()
    assert improvements[0]["status"] == ImprovementStatus.ROLLED_BACK.value


@pytest.mark.asyncio
async def test_store_metric(learning_store):
    """Test storing a metric."""
    now = datetime.now()
    period_start = now - timedelta(hours=1)

    metric_id = await learning_store.store_metric(
        metric_type="success_rate",
        metric_name="task_completion",
        value=0.85,
        period_start=period_start,
        period_end=now,
        metadata={"tasks": 100}
    )

    assert metric_id is not None
    assert metric_id > 0


@pytest.mark.asyncio
async def test_get_metrics(learning_store):
    """Test retrieving metrics."""
    now = datetime.now()
    period_start = now - timedelta(hours=1)

    await learning_store.store_metric(
        metric_type="success_rate",
        metric_name="task_completion",
        value=0.85,
        period_start=period_start,
        period_end=now
    )

    metrics = learning_store.get_metrics()

    assert len(metrics) == 1
    assert metrics[0]["metric_type"] == "success_rate"
    assert metrics[0]["value"] == 0.85


@pytest.mark.asyncio
async def test_get_metrics_by_type(learning_store):
    """Test filtering metrics by type."""
    now = datetime.now()
    period_start = now - timedelta(hours=1)

    await learning_store.store_metric(
        metric_type="success_rate",
        metric_name="test",
        value=0.85,
        period_start=period_start,
        period_end=now
    )

    # Get by type
    success_metrics = learning_store.get_metrics(metric_type="success_rate")
    assert len(success_metrics) == 1

    # Get different type (should be empty)
    duration_metrics = learning_store.get_metrics(metric_type="duration")
    assert len(duration_metrics) == 0


@pytest.mark.asyncio
async def test_store_correlation(learning_store):
    """Test storing a correlation."""
    correlation_id = await learning_store.store_correlation(
        correlation_type="error_improvement",
        entity_a="timeout_error",
        entity_b="timeout_increase",
        correlation_score=0.85,
        sample_size=50,
        metadata={"context": "test"}
    )

    assert correlation_id is not None
    assert correlation_id > 0


@pytest.mark.asyncio
async def test_get_correlations(learning_store):
    """Test retrieving correlations."""
    await learning_store.store_correlation(
        correlation_type="error_improvement",
        entity_a="timeout_error",
        entity_b="timeout_increase",
        correlation_score=0.85,
        sample_size=50
    )

    correlations = learning_store.get_correlations()

    assert len(correlations) == 1
    assert correlations[0]["correlation_score"] == 0.85


@pytest.mark.asyncio
async def test_get_correlations_by_score(learning_store):
    """Test filtering correlations by score."""
    await learning_store.store_correlation(
        correlation_type="test",
        entity_a="a",
        entity_b="b",
        correlation_score=0.85,
        sample_size=50
    )

    # Get high correlations
    high_corr = learning_store.get_correlations(min_score=0.8)
    assert len(high_corr) == 1

    # Get very high correlations (should be empty)
    very_high = learning_store.get_correlations(min_score=0.9)
    assert len(very_high) == 0


def test_get_statistics(learning_store, sample_pattern, sample_improvement):
    """Test getting store statistics."""
    import asyncio

    # Add some data
    asyncio.run(learning_store.store_pattern(sample_pattern))
    asyncio.run(learning_store.store_improvement(sample_improvement))

    stats = learning_store.get_statistics()

    assert "patterns" in stats
    assert "improvements" in stats
    assert "metrics" in stats
    assert "correlations" in stats
    assert stats["patterns"]["total"] == 1
    assert stats["improvements"]["total"] == 1


def test_context_manager(temp_db):
    """Test using LearningStore as context manager."""
    with LearningStore(db_path=temp_db) as store:
        assert store.conn is not None

    # Connection should be closed
    assert store.conn is None or not store.conn
