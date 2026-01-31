"""
Tests for LogAnalyzer - pattern detection and recommendation generation.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from alpha.learning.log_analyzer import (
    LogAnalyzer,
    LogPattern,
    ImprovementRecommendation,
    PatternType,
    Priority
)


@pytest.fixture
def temp_log_dir():
    """Create temporary log directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_logs(temp_log_dir):
    """Create sample log files."""
    log_file = Path(temp_log_dir) / "test_log.json"

    # Create sample log entries
    logs = []

    # Add some error entries
    for i in range(5):
        logs.append({
            "event": "task_error",
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
            "task_id": f"task_{i}",
            "task_name": "test_task",
            "error": "Connection timeout",
            "error_type": "TimeoutError"
        })

    # Add some slow operations
    for i in range(3):
        logs.append({
            "event": "tool_execution",
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
            "tool_name": "slow_tool",
            "duration": 10.5 + i,
            "success": True
        })

    # Add some high-cost LLM operations
    for i in range(3):
        logs.append({
            "event": "llm_interaction",
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
            "provider": "openai",
            "model": "gpt-4",
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "total_tokens": 1500,
            "duration": 2.5,
            "estimated_cost": 0.15
        })

    # Add successful tasks
    for i in range(10):
        logs.append({
            "event": "task_complete",
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
            "task_id": f"success_task_{i}",
            "task_name": "successful_task",
            "duration": 1.2,
            "result": "success"
        })

    # Write logs
    with open(log_file, 'w') as f:
        for log in logs:
            f.write(json.dumps(log) + '\n')

    return temp_log_dir


@pytest.mark.asyncio
async def test_log_analyzer_initialization(temp_log_dir):
    """Test LogAnalyzer initialization."""
    analyzer = LogAnalyzer(log_dir=temp_log_dir)

    assert analyzer.log_dir == Path(temp_log_dir)
    assert analyzer.patterns == []
    assert analyzer.recommendations == []


@pytest.mark.asyncio
async def test_analyze_logs_detects_patterns(sample_logs):
    """Test that log analysis detects patterns."""
    analyzer = LogAnalyzer(log_dir=sample_logs)

    patterns = await analyzer.analyze_logs()

    assert len(patterns) > 0
    assert isinstance(patterns[0], LogPattern)


@pytest.mark.asyncio
async def test_detect_error_patterns(sample_logs):
    """Test detection of recurring error patterns."""
    analyzer = LogAnalyzer(log_dir=sample_logs)

    await analyzer.analyze_logs()

    # Should detect recurring TimeoutError
    error_patterns = [
        p for p in analyzer.patterns
        if p.pattern_type == PatternType.RECURRING_ERROR
    ]

    assert len(error_patterns) > 0
    assert error_patterns[0].occurrences >= 3


@pytest.mark.asyncio
async def test_detect_slow_operations(sample_logs):
    """Test detection of slow operations."""
    analyzer = LogAnalyzer(log_dir=sample_logs)

    await analyzer.analyze_logs()

    # Should detect slow tool executions
    slow_patterns = [
        p for p in analyzer.patterns
        if p.pattern_type == PatternType.SLOW_OPERATION
    ]

    assert len(slow_patterns) > 0


@pytest.mark.asyncio
async def test_detect_high_cost_operations(sample_logs):
    """Test detection of high-cost operations."""
    analyzer = LogAnalyzer(log_dir=sample_logs)

    await analyzer.analyze_logs()

    # Should detect high-cost LLM operations
    cost_patterns = [
        p for p in analyzer.patterns
        if p.pattern_type == PatternType.HIGH_COST_OPERATION
    ]

    assert len(cost_patterns) > 0


@pytest.mark.asyncio
async def test_detect_successful_patterns(sample_logs):
    """Test detection of successful patterns."""
    analyzer = LogAnalyzer(log_dir=sample_logs)

    await analyzer.analyze_logs()

    # Should detect successful task patterns
    success_patterns = [
        p for p in analyzer.patterns
        if p.pattern_type == PatternType.SUCCESSFUL_PATTERN
    ]

    assert len(success_patterns) > 0


@pytest.mark.asyncio
async def test_generate_recommendations(sample_logs):
    """Test generation of improvement recommendations."""
    analyzer = LogAnalyzer(log_dir=sample_logs)

    await analyzer.analyze_logs()
    recommendations = await analyzer.generate_recommendations()

    assert len(recommendations) > 0
    assert isinstance(recommendations[0], ImprovementRecommendation)
    assert hasattr(recommendations[0], 'priority')
    assert hasattr(recommendations[0], 'confidence')


@pytest.mark.asyncio
async def test_recommendations_sorted_by_priority(sample_logs):
    """Test that recommendations are sorted by priority."""
    analyzer = LogAnalyzer(log_dir=sample_logs)

    await analyzer.analyze_logs()
    recommendations = await analyzer.generate_recommendations()

    if len(recommendations) >= 2:
        # Check priority ordering (higher priority first)
        for i in range(len(recommendations) - 1):
            assert recommendations[i].priority.value >= recommendations[i+1].priority.value


@pytest.mark.asyncio
async def test_analyze_time_period(sample_logs):
    """Test analyzing specific time period."""
    analyzer = LogAnalyzer(log_dir=sample_logs)

    result = await analyzer.analyze_time_period(days=1)

    assert "time_range" in result
    assert "patterns" in result
    assert "recommendations" in result
    assert result["time_range"]["days"] == 1


@pytest.mark.asyncio
async def test_get_summary(sample_logs):
    """Test getting analysis summary."""
    analyzer = LogAnalyzer(log_dir=sample_logs)

    await analyzer.analyze_logs()
    await analyzer.generate_recommendations()

    summary = analyzer.get_summary()

    assert "patterns_detected" in summary
    assert "patterns_by_type" in summary
    assert "recommendations_generated" in summary
    assert summary["patterns_detected"] == len(analyzer.patterns)


@pytest.mark.asyncio
async def test_empty_log_directory(temp_log_dir):
    """Test handling of empty log directory."""
    analyzer = LogAnalyzer(log_dir=temp_log_dir)

    patterns = await analyzer.analyze_logs()

    assert patterns == []


@pytest.mark.asyncio
async def test_pattern_metadata(sample_logs):
    """Test that patterns contain proper metadata."""
    analyzer = LogAnalyzer(log_dir=sample_logs)

    await analyzer.analyze_logs()

    for pattern in analyzer.patterns:
        assert pattern.description is not None
        assert pattern.occurrences > 0
        assert pattern.impact_score >= 0
        assert isinstance(pattern.metadata, dict)


@pytest.mark.asyncio
async def test_recommendation_action_types(sample_logs):
    """Test that recommendations have valid action types."""
    analyzer = LogAnalyzer(log_dir=sample_logs)

    await analyzer.analyze_logs()
    recommendations = await analyzer.generate_recommendations()

    valid_action_types = [
        "config_update",
        "model_routing",
        "tool_strategy",
        "error_handling"
    ]

    for rec in recommendations:
        assert rec.action_type in valid_action_types
