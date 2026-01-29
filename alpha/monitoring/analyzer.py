"""
Alpha - Self Analyzer

Analyzes execution logs and metrics to identify patterns, issues, and improvement opportunities.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class AnalysisResult:
    """Represents analysis result."""

    def __init__(
        self,
        category: str,
        severity: str,
        title: str,
        description: str,
        recommendations: List[str],
        data: Optional[Dict] = None
    ):
        self.category = category
        self.severity = severity
        self.title = title
        self.description = description
        self.recommendations = recommendations
        self.data = data or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'category': self.category,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'recommendations': self.recommendations,
            'data': self.data,
            'timestamp': self.timestamp
        }


class SelfAnalyzer:
    """
    Analyzes execution logs and metrics to identify issues and improvements.

    Features:
    - Pattern detection in failures
    - Performance bottleneck identification
    - Resource usage analysis
    - Success/failure rate tracking
    - Anomaly detection
    - Recommendation generation
    """

    def __init__(self):
        """Initialize self analyzer."""
        logger.info("Self analyzer initialized")

    def analyze_task_performance(
        self,
        metrics_summary: Dict
    ) -> List[AnalysisResult]:
        """
        Analyze task performance metrics.

        Args:
            metrics_summary: Metrics summary from MetricsCollector

        Returns:
            List of analysis results
        """
        results = []

        # Analyze task completion times
        if 'timers' in metrics_summary:
            task_timers = {
                name: stats
                for name, stats in metrics_summary['timers'].items()
                if 'task.' in name
            }

            for name, stats in task_timers.items():
                # Check for slow tasks
                if stats.get('mean', 0) > 30:  # Tasks taking >30 seconds
                    results.append(AnalysisResult(
                        category='performance',
                        severity='warning',
                        title=f'Slow task detected: {name}',
                        description=f'Average execution time: {stats["mean"]:.2f}s',
                        recommendations=[
                            'Review task implementation for optimization opportunities',
                            'Consider breaking down into smaller sub-tasks',
                            'Check for blocking I/O operations'
                        ],
                        data=stats
                    ))

                # Check for high variance in execution time
                if stats.get('count', 0) > 10:
                    variance = (stats['max'] - stats['min']) / stats['mean']
                    if variance > 2:  # High variance
                        results.append(AnalysisResult(
                            category='performance',
                            severity='info',
                            title=f'Inconsistent task performance: {name}',
                            description=f'High variance in execution time (min: {stats["min"]:.2f}s, max: {stats["max"]:.2f}s)',
                            recommendations=[
                                'Investigate factors causing performance variation',
                                'Consider caching or optimization'
                            ],
                            data=stats
                        ))

        return results

    def analyze_error_patterns(
        self,
        error_logs: List[Dict]
    ) -> List[AnalysisResult]:
        """
        Analyze error patterns in execution logs.

        Args:
            error_logs: List of error log entries

        Returns:
            List of analysis results
        """
        results = []

        if not error_logs:
            return results

        # Group errors by type
        error_types = defaultdict(list)
        for error in error_logs:
            error_type = error.get('error_type', 'Unknown')
            error_types[error_type].append(error)

        # Analyze frequent errors
        for error_type, errors in error_types.items():
            count = len(errors)
            if count > 3:  # Recurring error
                results.append(AnalysisResult(
                    category='reliability',
                    severity='error' if count > 10 else 'warning',
                    title=f'Recurring error: {error_type}',
                    description=f'Error occurred {count} times',
                    recommendations=[
                        'Implement better error handling',
                        'Add retry mechanism if applicable',
                        'Investigate root cause'
                    ],
                    data={'count': count, 'error_type': error_type}
                ))

        return results

    def analyze_resource_usage(
        self,
        metrics_summary: Dict
    ) -> List[AnalysisResult]:
        """
        Analyze system resource usage.

        Args:
            metrics_summary: Metrics summary

        Returns:
            List of analysis results
        """
        results = []

        gauges = metrics_summary.get('gauges', {})

        # Check CPU usage
        cpu_percent = gauges.get('system.cpu_percent', 0)
        if cpu_percent > 80:
            results.append(AnalysisResult(
                category='resources',
                severity='warning',
                title='High CPU usage detected',
                description=f'CPU usage: {cpu_percent}%',
                recommendations=[
                    'Review CPU-intensive operations',
                    'Consider optimizing algorithms',
                    'Implement rate limiting for concurrent tasks'
                ],
                data={'cpu_percent': cpu_percent}
            ))

        # Check memory usage
        memory_percent = gauges.get('system.memory_percent', 0)
        if memory_percent > 85:
            results.append(AnalysisResult(
                category='resources',
                severity='error' if memory_percent > 95 else 'warning',
                title='High memory usage detected',
                description=f'Memory usage: {memory_percent}%',
                recommendations=[
                    'Review memory-intensive operations',
                    'Implement memory cleanup',
                    'Check for memory leaks'
                ],
                data={'memory_percent': memory_percent}
            ))

        return results

    def analyze_llm_usage(
        self,
        llm_logs: List[Dict]
    ) -> List[AnalysisResult]:
        """
        Analyze LLM usage and costs.

        Args:
            llm_logs: List of LLM interaction logs

        Returns:
            List of analysis results
        """
        results = []

        if not llm_logs:
            return results

        # Calculate total tokens and cost
        total_tokens = sum(log.get('total_tokens', 0) for log in llm_logs)
        total_cost = sum(log.get('estimated_cost', 0) for log in llm_logs)

        # Analyze token efficiency
        avg_tokens_per_request = total_tokens / len(llm_logs)
        if avg_tokens_per_request > 4000:
            results.append(AnalysisResult(
                category='cost',
                severity='warning',
                title='High token usage per request',
                description=f'Average tokens per request: {avg_tokens_per_request:.0f}',
                recommendations=[
                    'Review prompt engineering to reduce token usage',
                    'Implement context truncation',
                    'Use smaller models for simpler tasks'
                ],
                data={'avg_tokens': avg_tokens_per_request, 'total_cost': total_cost}
            ))

        return results

    def generate_report(
        self,
        analysis_results: List[AnalysisResult],
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Generate analysis report.

        Args:
            analysis_results: List of analysis results
            output_path: Optional path to save report

        Returns:
            Report dictionary
        """
        # Group results by category and severity
        by_category = defaultdict(list)
        by_severity = defaultdict(list)

        for result in analysis_results:
            by_category[result.category].append(result)
            by_severity[result.severity].append(result)

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_findings': len(analysis_results),
                'by_severity': {
                    severity: len(results)
                    for severity, results in by_severity.items()
                },
                'by_category': {
                    category: len(results)
                    for category, results in by_category.items()
                }
            },
            'findings': [r.to_dict() for r in analysis_results]
        }

        # Save report if path provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Analysis report saved: {output_path}")

        return report
