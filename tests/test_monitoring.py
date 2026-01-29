"""
Tests for Self-Monitoring System

Covers metrics collection, execution logging, self-analysis, and reporting.
"""

import pytest
import tempfile
import shutil
import time
from pathlib import Path

from alpha.monitoring import (
    MetricsCollector,
    ExecutionLogger,
    SelfAnalyzer,
    PerformanceReporter,
    Timer,
    MetricType
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


class TestMetricsCollector:
    """Test metrics collection functionality."""

    def test_record_counter(self, temp_dir):
        """Test counter metrics."""
        collector = MetricsCollector(storage_path=temp_dir)

        collector.record_counter("test.counter", 5.0)
        collector.record_counter("test.counter", 3.0)

        assert collector.counters["test.counter"] == 8.0
        assert len(collector.metrics) == 2

    def test_record_gauge(self, temp_dir):
        """Test gauge metrics."""
        collector = MetricsCollector(storage_path=temp_dir)

        collector.record_gauge("test.gauge", 42.5)
        collector.record_gauge("test.gauge", 50.0)

        assert collector.gauges["test.gauge"] == 50.0  # Latest value
        assert len(collector.metrics) == 2

    def test_record_timer(self, temp_dir):
        """Test timer metrics."""
        collector = MetricsCollector(storage_path=temp_dir)

        collector.record_timer("test.timer", 1.5)
        collector.record_timer("test.timer", 2.5)
        collector.record_timer("test.timer", 2.0)

        assert len(collector.timers["test.timer"]) == 3
        stats = collector.get_timer_stats("test.timer")
        assert stats['count'] == 3
        assert stats['mean'] == 2.0
        assert stats['min'] == 1.5
        assert stats['max'] == 2.5

    def test_timer_context_manager(self, temp_dir):
        """Test Timer context manager."""
        collector = MetricsCollector(storage_path=temp_dir)

        with Timer(collector, "test.operation"):
            time.sleep(0.1)

        stats = collector.get_timer_stats("test.operation")
        assert stats['count'] == 1
        assert stats['mean'] >= 0.1

    def test_collect_system_metrics(self, temp_dir):
        """Test system metrics collection."""
        collector = MetricsCollector(storage_path=temp_dir)

        collector.collect_system_metrics()

        assert "system.cpu_percent" in collector.gauges
        assert "system.memory_percent" in collector.gauges
        assert "system.disk_percent" in collector.gauges

    def test_get_summary(self, temp_dir):
        """Test metrics summary."""
        collector = MetricsCollector(storage_path=temp_dir)

        collector.record_counter("test.count", 10)
        collector.record_gauge("test.gauge", 42)
        collector.record_timer("test.timer", 1.5)

        summary = collector.get_summary()

        assert summary['total_metrics'] == 3
        assert summary['counters']['test.count'] == 10
        assert summary['gauges']['test.gauge'] == 42
        assert 'test.timer' in summary['timers']

    def test_save_metrics(self, temp_dir):
        """Test metrics saving."""
        collector = MetricsCollector(storage_path=temp_dir)

        collector.record_counter("test.count", 5)
        collector.save_metrics("test_metrics.json")

        filepath = Path(temp_dir) / "test_metrics.json"
        assert filepath.exists()


class TestExecutionLogger:
    """Test execution logging functionality."""

    def test_log_task_events(self, temp_dir):
        """Test task event logging."""
        logger = ExecutionLogger(log_dir=temp_dir)

        logger.log_task_start("task-123", "Test Task", "Testing")
        logger.log_task_complete("task-123", "Test Task", 2.5, "Success")
        logger.log_task_error("task-456", "Error Task", "Test error", "ValueError")

    def test_log_tool_execution(self, temp_dir):
        """Test tool execution logging."""
        logger = ExecutionLogger(log_dir=temp_dir)

        logger.log_tool_execution(
            tool_name="shell",
            parameters={"command": "ls"},
            duration=0.5,
            success=True,
            result="file1.txt file2.txt"
        )

    def test_log_llm_interaction(self, temp_dir):
        """Test LLM interaction logging."""
        logger = ExecutionLogger(log_dir=temp_dir)

        logger.log_llm_interaction(
            provider="openai",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            duration=2.0,
            estimated_cost=0.003
        )


class TestSelfAnalyzer:
    """Test self-analysis functionality."""

    def test_analyze_task_performance_slow_tasks(self):
        """Test detection of slow tasks."""
        analyzer = SelfAnalyzer()

        metrics_summary = {
            'timers': {
                'task.slow_operation': {
                    'count': 10,
                    'mean': 45.0,
                    'min': 30.0,
                    'max': 60.0
                }
            }
        }

        results = analyzer.analyze_task_performance(metrics_summary)

        assert len(results) > 0
        assert results[0].category == 'performance'
        assert results[0].severity == 'warning'

    def test_analyze_task_performance_variance(self):
        """Test detection of high variance in task performance."""
        analyzer = SelfAnalyzer()

        metrics_summary = {
            'timers': {
                'task.inconsistent': {
                    'count': 20,
                    'mean': 10.0,
                    'min': 1.0,
                    'max': 30.0
                }
            }
        }

        results = analyzer.analyze_task_performance(metrics_summary)

        assert len(results) > 0
        assert any(r.title.startswith('Inconsistent') for r in results)

    def test_analyze_error_patterns(self):
        """Test error pattern analysis."""
        analyzer = SelfAnalyzer()

        error_logs = [
            {'error_type': 'ValueError', 'error': 'Test error 1'},
            {'error_type': 'ValueError', 'error': 'Test error 2'},
            {'error_type': 'ValueError', 'error': 'Test error 3'},
            {'error_type': 'ValueError', 'error': 'Test error 4'},
        ]

        results = analyzer.analyze_error_patterns(error_logs)

        assert len(results) > 0
        assert results[0].category == 'reliability'

    def test_analyze_resource_usage_cpu(self):
        """Test CPU usage analysis."""
        analyzer = SelfAnalyzer()

        metrics_summary = {
            'gauges': {
                'system.cpu_percent': 85.0,
                'system.memory_percent': 50.0
            }
        }

        results = analyzer.analyze_resource_usage(metrics_summary)

        assert len(results) > 0
        assert any(r.title == 'High CPU usage detected' for r in results)

    def test_analyze_resource_usage_memory(self):
        """Test memory usage analysis."""
        analyzer = SelfAnalyzer()

        metrics_summary = {
            'gauges': {
                'system.cpu_percent': 50.0,
                'system.memory_percent': 90.0
            }
        }

        results = analyzer.analyze_resource_usage(metrics_summary)

        assert len(results) > 0
        assert any(r.title == 'High memory usage detected' for r in results)

    def test_analyze_llm_usage(self):
        """Test LLM usage analysis."""
        analyzer = SelfAnalyzer()

        llm_logs = [
            {'total_tokens': 5000, 'estimated_cost': 0.01},
            {'total_tokens': 4500, 'estimated_cost': 0.009},
            {'total_tokens': 4800, 'estimated_cost': 0.0096},
        ]

        results = analyzer.analyze_llm_usage(llm_logs)

        assert len(results) > 0
        assert results[0].category == 'cost'

    def test_generate_report(self, temp_dir):
        """Test report generation."""
        analyzer = SelfAnalyzer()

        from alpha.monitoring.analyzer import AnalysisResult

        results = [
            AnalysisResult(
                category='performance',
                severity='warning',
                title='Test finding',
                description='Test description',
                recommendations=['Fix it']
            )
        ]

        output_path = Path(temp_dir) / "analysis_report.json"
        report = analyzer.generate_report(results, str(output_path))

        assert report['summary']['total_findings'] == 1
        assert output_path.exists()


class TestPerformanceReporter:
    """Test performance reporting functionality."""

    def test_generate_summary_report(self, temp_dir):
        """Test summary report generation."""
        reporter = PerformanceReporter(output_dir=temp_dir)

        metrics_summary = {
            'counters': {
                'tasks.completed': 100,
                'tasks.failed': 5,
                'llm.total_tokens': 50000,
                'llm.estimated_cost': 0.5
            },
            'gauges': {
                'system.cpu_percent': 45.0,
                'system.memory_percent': 60.0
            },
            'timers': {
                'task.execution': {
                    'count': 105,
                    'mean': 2.5,
                    'min': 0.5,
                    'max': 10.0
                }
            }
        }

        analysis_results = [
            {
                'severity': 'warning',
                'category': 'performance',
                'title': 'Test warning'
            },
            {
                'severity': 'error',
                'category': 'reliability',
                'title': 'Test error'
            }
        ]

        report = reporter.generate_summary_report(
            metrics_summary,
            analysis_results,
            period="daily"
        )

        assert report['period'] == "daily"
        assert report['summary']['task_statistics']['total_tasks'] == 105
        assert report['summary']['issues']['warnings'] == 1
        assert report['summary']['issues']['critical'] == 1

    def test_save_report_json(self, temp_dir):
        """Test saving report as JSON."""
        reporter = PerformanceReporter(output_dir=temp_dir)

        report = {
            'period': 'daily',
            'summary': {'test': 'data'}
        }

        reporter.save_report(report, "test_report.json", format="json")

        filepath = Path(temp_dir) / "test_report.json"
        assert filepath.exists()

    def test_save_report_text(self, temp_dir):
        """Test saving report as text."""
        reporter = PerformanceReporter(output_dir=temp_dir)

        report = {
            'period': 'daily',
            'timestamp': '2024-01-01T00:00:00',
            'summary': {
                'task_statistics': {
                    'total_tasks': 100,
                    'completed': 95,
                    'failed': 5,
                    'success_rate': '95.0%'
                },
                'performance': {
                    'avg_response_time': '2.50s'
                },
                'system_health': {
                    'status': 'good'
                },
                'issues': {
                    'critical': 0,
                    'warnings': 2
                }
            },
            'analysis_findings': []
        }

        reporter.save_report(report, "test_report.txt", format="txt")

        filepath = Path(temp_dir) / "test_report.txt"
        assert filepath.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
