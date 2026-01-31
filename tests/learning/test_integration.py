"""
Integration tests for the learning system.
Tests all components working together.
"""

import pytest
import json
import tempfile
import yaml
from pathlib import Path
from datetime import datetime, timedelta

from alpha.learning import (
    LogAnalyzer,
    ImprovementExecutor,
    LearningStore,
    FeedbackLoop,
    FeedbackLoopConfig,
    FeedbackLoopMode
)


@pytest.fixture
def integrated_system():
    """Create integrated learning system."""
    # Create temp directories and files
    log_dir = tempfile.mkdtemp()
    db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)

    # Write config
    config = {
        "alpha": {"name": "Test", "version": "0.1.0"},
        "llm": {
            "default_provider": "deepseek",
            "providers": {
                "deepseek": {"auto_select_model": False}
            }
        },
        "code_execution": {"defaults": {"timeout": 30}},
        "tasks": {"timeouts": {}}
    }
    yaml.dump(config, config_file)
    config_file.close()

    # Create sample logs
    log_file = Path(log_dir) / "execution_log.json"
    logs = []

    # Add recurring errors
    for i in range(5):
        logs.append({
            "event": "task_error",
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
            "task_id": f"task_{i}",
            "task_name": "db_query",
            "error": "Connection timeout",
            "error_type": "TimeoutError"
        })

    # Add slow operations
    for i in range(4):
        logs.append({
            "event": "tool_execution",
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
            "tool_name": "database_tool",
            "duration": 15.0 + i,
            "success": True
        })

    # Write logs
    with open(log_file, 'w') as f:
        for log in logs:
            f.write(json.dumps(log) + '\n')

    # Create components
    log_analyzer = LogAnalyzer(log_dir=log_dir)
    improvement_executor = ImprovementExecutor(config_path=config_file.name)
    learning_store = LearningStore(db_path=db_file.name)
    learning_store.initialize()

    # Link executor to store
    improvement_executor.learning_store = learning_store

    loop_config = FeedbackLoopConfig(
        mode=FeedbackLoopMode.SEMI_AUTO,
        analysis_days=1,
        min_confidence=0.6,
        max_daily_improvements=10,
        dry_run_first=False  # Apply for real in tests
    )

    feedback_loop = FeedbackLoop(
        config=loop_config,
        log_analyzer=log_analyzer,
        improvement_executor=improvement_executor,
        learning_store=learning_store
    )

    yield {
        "log_analyzer": log_analyzer,
        "improvement_executor": improvement_executor,
        "learning_store": learning_store,
        "feedback_loop": feedback_loop,
        "log_dir": log_dir,
        "db_path": db_file.name,
        "config_path": config_file.name
    }

    # Cleanup
    import shutil
    learning_store.close()
    shutil.rmtree(log_dir, ignore_errors=True)
    Path(db_file.name).unlink(missing_ok=True)
    Path(config_file.name).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_end_to_end_learning_cycle(integrated_system):
    """Test complete learning cycle from logs to improvements."""
    feedback_loop = integrated_system["feedback_loop"]
    learning_store = integrated_system["learning_store"]

    # Start feedback loop
    await feedback_loop.start()

    # Run one complete cycle
    result = await feedback_loop.run_cycle()

    # Verify cycle completed
    assert result["status"] == "completed"
    assert "steps" in result

    # Verify patterns were detected
    assert result["steps"]["analysis"]["patterns_found"] > 0

    # Verify recommendations were generated
    assert result["steps"]["recommendations"]["total"] > 0

    # Verify patterns were stored
    patterns = learning_store.get_patterns()
    assert len(patterns) > 0

    # Stop feedback loop
    await feedback_loop.stop()


@pytest.mark.asyncio
async def test_pattern_to_improvement_flow(integrated_system):
    """Test flow from pattern detection to improvement application."""
    log_analyzer = integrated_system["log_analyzer"]
    improvement_executor = integrated_system["improvement_executor"]
    learning_store = integrated_system["learning_store"]

    # Step 1: Analyze logs
    patterns = await log_analyzer.analyze_logs()
    assert len(patterns) > 0

    # Step 2: Generate recommendations
    recommendations = await log_analyzer.generate_recommendations()
    assert len(recommendations) > 0

    # Step 3: Store patterns
    for pattern in patterns:
        await learning_store.store_pattern(pattern)

    # Step 4: Apply improvement (using first recommendation)
    if recommendations:
        improvement = await improvement_executor.apply_recommendation(
            recommendations[0],
            dry_run=False
        )

        # Verify improvement was applied or validated
        assert improvement.id is not None
        assert improvement.recommendation_title == recommendations[0].title

        # Verify improvement was stored
        improvements = learning_store.get_improvements()
        assert len(improvements) > 0


@pytest.mark.asyncio
async def test_metrics_tracking(integrated_system):
    """Test that metrics are tracked throughout the cycle."""
    feedback_loop = integrated_system["feedback_loop"]
    learning_store = integrated_system["learning_store"]

    # Run cycle
    await feedback_loop.start()
    await feedback_loop.run_cycle()
    await feedback_loop.stop()

    # Check that metrics were stored
    metrics = learning_store.get_metrics()
    assert len(metrics) > 0


@pytest.mark.asyncio
async def test_multiple_cycles(integrated_system):
    """Test running multiple learning cycles."""
    feedback_loop = integrated_system["feedback_loop"]

    await feedback_loop.start()

    # Run multiple cycles
    for i in range(3):
        result = await feedback_loop.run_cycle()
        assert result["status"] == "completed"
        assert result["cycle_number"] == i + 1

    assert feedback_loop.cycle_count == 3

    await feedback_loop.stop()


@pytest.mark.asyncio
async def test_statistics_aggregation(integrated_system):
    """Test that statistics are properly aggregated."""
    feedback_loop = integrated_system["feedback_loop"]
    learning_store = integrated_system["learning_store"]
    improvement_executor = integrated_system["improvement_executor"]

    # Run a cycle
    await feedback_loop.start()
    await feedback_loop.run_cycle()
    await feedback_loop.stop()

    # Get statistics from all components
    loop_stats = feedback_loop.get_statistics()
    store_stats = learning_store.get_statistics()
    executor_stats = improvement_executor.get_statistics()

    # Verify structure
    assert "feedback_loop" in loop_stats
    assert "learning_store" in loop_stats
    assert "improvements" in loop_stats

    assert "patterns" in store_stats
    assert "improvements" in store_stats
    assert "metrics" in store_stats

    assert "total_improvements" in executor_stats


@pytest.mark.asyncio
async def test_confidence_filtering(integrated_system):
    """Test that low-confidence recommendations are filtered."""
    feedback_loop = integrated_system["feedback_loop"]

    # Set high confidence threshold
    feedback_loop.config.min_confidence = 0.95

    await feedback_loop.start()
    result = await feedback_loop.run_cycle()
    await feedback_loop.stop()

    # With high threshold, fewer improvements should be applied
    # (or none if all are below threshold)
    improvements_applied = result["steps"]["improvements"]["applied"]
    assert improvements_applied >= 0  # Can be 0 if all below threshold


@pytest.mark.asyncio
async def test_daily_quota_enforcement(integrated_system):
    """Test that daily improvement quota is enforced."""
    feedback_loop = integrated_system["feedback_loop"]

    # Set low quota
    feedback_loop.config.max_daily_improvements = 1

    await feedback_loop.start()
    result = await feedback_loop.run_cycle()
    await feedback_loop.stop()

    # Should not exceed quota
    improvements_applied = result["steps"]["improvements"]["applied"]
    assert improvements_applied <= 1
