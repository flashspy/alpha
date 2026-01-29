"""
Alpha - Performance Reporter

Generates performance reports and visualizations.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceReporter:
    """
    Generates performance reports from metrics and analysis results.

    Features:
    - Summary reports
    - Trend analysis
    - Comparison reports
    - Export to various formats
    """

    def __init__(self, output_dir: str = "data/reports"):
        """
        Initialize performance reporter.

        Args:
            output_dir: Directory for output reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Performance reporter initialized: {self.output_dir}")

    def generate_summary_report(
        self,
        metrics_summary: Dict,
        analysis_results: List[Dict],
        period: str = "daily"
    ) -> Dict:
        """
        Generate summary performance report.

        Args:
            metrics_summary: Metrics summary from MetricsCollector
            analysis_results: Analysis results from SelfAnalyzer
            period: Report period (daily, weekly, monthly)

        Returns:
            Report dictionary
        """
        # Extract key metrics
        counters = metrics_summary.get('counters', {})
        gauges = metrics_summary.get('gauges', {})
        timers = metrics_summary.get('timers', {})

        # Calculate task statistics
        task_count = counters.get('tasks.completed', 0) + counters.get('tasks.failed', 0)
        task_success_rate = 0
        if task_count > 0:
            task_success_rate = (counters.get('tasks.completed', 0) / task_count) * 100

        # Calculate average response time
        avg_response_time = 0
        if 'task.execution' in timers and timers['task.execution'].get('count', 0) > 0:
            avg_response_time = timers['task.execution'].get('mean', 0)

        # System health
        system_health = "good"
        cpu = gauges.get('system.cpu_percent', 0)
        memory = gauges.get('system.memory_percent', 0)

        if cpu > 80 or memory > 85:
            system_health = "warning"
        if cpu > 95 or memory > 95:
            system_health = "critical"

        # Count issues by severity
        critical_issues = sum(1 for r in analysis_results if r.get('severity') == 'error')
        warnings = sum(1 for r in analysis_results if r.get('severity') == 'warning')

        report = {
            'period': period,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'task_statistics': {
                    'total_tasks': task_count,
                    'completed': counters.get('tasks.completed', 0),
                    'failed': counters.get('tasks.failed', 0),
                    'success_rate': f"{task_success_rate:.1f}%"
                },
                'performance': {
                    'avg_response_time': f"{avg_response_time:.2f}s",
                    'total_llm_tokens': counters.get('llm.total_tokens', 0),
                    'estimated_cost': f"${counters.get('llm.estimated_cost', 0):.4f}"
                },
                'system_health': {
                    'status': system_health,
                    'cpu_usage': f"{cpu:.1f}%",
                    'memory_usage': f"{memory:.1f}%"
                },
                'issues': {
                    'critical': critical_issues,
                    'warnings': warnings,
                    'total': len(analysis_results)
                }
            },
            'detailed_metrics': {
                'counters': counters,
                'gauges': gauges,
                'timers': {
                    name: {
                        'count': stats.get('count', 0),
                        'mean': stats.get('mean', 0),
                        'min': stats.get('min', 0),
                        'max': stats.get('max', 0)
                    }
                    for name, stats in timers.items()
                }
            },
            'analysis_findings': analysis_results
        }

        return report

    def save_report(
        self,
        report: Dict,
        filename: Optional[str] = None,
        format: str = "json"
    ):
        """
        Save report to file.

        Args:
            report: Report dictionary
            filename: Output filename
            format: Output format (json, txt)
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{timestamp}.{format}"

        filepath = self.output_dir / filename

        if format == "json":
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
        elif format == "txt":
            with open(filepath, 'w') as f:
                f.write(self._format_report_text(report))

        logger.info(f"Performance report saved: {filepath}")

    def _format_report_text(self, report: Dict) -> str:
        """
        Format report as text.

        Args:
            report: Report dictionary

        Returns:
            Formatted text
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"Alpha Performance Report - {report['period']}")
        lines.append(f"Generated: {report['timestamp']}")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        summary = report['summary']
        lines.append("TASK STATISTICS")
        lines.append("-" * 80)
        for key, value in summary['task_statistics'].items():
            lines.append(f"  {key.replace('_', ' ').title()}: {value}")
        lines.append("")

        lines.append("PERFORMANCE METRICS")
        lines.append("-" * 80)
        for key, value in summary['performance'].items():
            lines.append(f"  {key.replace('_', ' ').title()}: {value}")
        lines.append("")

        lines.append("SYSTEM HEALTH")
        lines.append("-" * 80)
        for key, value in summary['system_health'].items():
            lines.append(f"  {key.replace('_', ' ').title()}: {value}")
        lines.append("")

        lines.append("ISSUES")
        lines.append("-" * 80)
        for key, value in summary['issues'].items():
            lines.append(f"  {key.replace('_', ' ').title()}: {value}")
        lines.append("")

        # Analysis findings
        if report.get('analysis_findings'):
            lines.append("ANALYSIS FINDINGS")
            lines.append("-" * 80)
            for finding in report['analysis_findings']:
                lines.append(f"[{finding['severity'].upper()}] {finding['title']}")
                lines.append(f"  Category: {finding['category']}")
                lines.append(f"  Description: {finding['description']}")
                lines.append(f"  Recommendations:")
                for rec in finding['recommendations']:
                    lines.append(f"    - {rec}")
                lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)
