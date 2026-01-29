"""
Alpha - Metrics Collector

Collects and stores performance metrics for monitoring and analysis.
"""

import logging
import time
import psutil
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"        # Cumulative count (tasks completed, errors)
    GAUGE = "gauge"           # Current value (memory usage, active tasks)
    TIMER = "timer"           # Duration measurements (response time)
    HISTOGRAM = "histogram"   # Distribution of values


@dataclass
class Metric:
    """Represents a single metric."""
    name: str
    value: float
    type: MetricType
    timestamp: str
    tags: Dict[str, str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'value': self.value,
            'type': self.type.value,
            'timestamp': self.timestamp,
            'tags': self.tags or {},
            'metadata': self.metadata or {}
        }


class MetricsCollector:
    """
    Collects and aggregates performance metrics.

    Features:
    - System metrics (CPU, memory, disk)
    - LLM metrics (tokens, cost, response time)
    - Tool metrics (execution time, success rate)
    - Task metrics (completion rate, duration)
    - Custom metrics
    """

    def __init__(self, storage_path: str = "data/metrics"):
        """
        Initialize metrics collector.

        Args:
            storage_path: Path to store metrics
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.metrics: List[Metric] = []
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.timers: Dict[str, List[float]] = {}

        logger.info(f"Metrics collector initialized: {self.storage_path}")

    def record_counter(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record a counter metric.

        Args:
            name: Metric name
            value: Value to add (default: 1.0)
            tags: Optional tags
        """
        self.counters[name] = self.counters.get(name, 0) + value

        metric = Metric(
            name=name,
            value=value,
            type=MetricType.COUNTER,
            timestamp=datetime.now().isoformat(),
            tags=tags
        )
        self.metrics.append(metric)
        logger.debug(f"Counter recorded: {name}={value}")

    def record_gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record a gauge metric (current value).

        Args:
            name: Metric name
            value: Current value
            tags: Optional tags
        """
        self.gauges[name] = value

        metric = Metric(
            name=name,
            value=value,
            type=MetricType.GAUGE,
            timestamp=datetime.now().isoformat(),
            tags=tags
        )
        self.metrics.append(metric)
        logger.debug(f"Gauge recorded: {name}={value}")

    def record_timer(
        self,
        name: str,
        duration: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record a timer metric (duration).

        Args:
            name: Metric name
            duration: Duration in seconds
            tags: Optional tags
        """
        if name not in self.timers:
            self.timers[name] = []
        self.timers[name].append(duration)

        metric = Metric(
            name=name,
            value=duration,
            type=MetricType.TIMER,
            timestamp=datetime.now().isoformat(),
            tags=tags
        )
        self.metrics.append(metric)
        logger.debug(f"Timer recorded: {name}={duration:.3f}s")

    def collect_system_metrics(self):
        """Collect system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.record_gauge("system.cpu_percent", cpu_percent, {"type": "system"})

            # Memory usage
            memory = psutil.virtual_memory()
            self.record_gauge("system.memory_percent", memory.percent, {"type": "system"})
            self.record_gauge("system.memory_available_mb", memory.available / 1024 / 1024, {"type": "system"})

            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_gauge("system.disk_percent", disk.percent, {"type": "system"})

            logger.debug("System metrics collected")
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """
        Get statistics for a timer metric.

        Args:
            name: Timer name

        Returns:
            Statistics dictionary
        """
        if name not in self.timers or not self.timers[name]:
            return {}

        durations = self.timers[name]
        return {
            'count': len(durations),
            'min': min(durations),
            'max': max(durations),
            'mean': sum(durations) / len(durations),
            'total': sum(durations)
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Get metrics summary.

        Returns:
            Summary dictionary
        """
        timer_summaries = {
            name: self.get_timer_stats(name)
            for name in self.timers.keys()
        }

        return {
            'timestamp': datetime.now().isoformat(),
            'total_metrics': len(self.metrics),
            'counters': self.counters.copy(),
            'gauges': self.gauges.copy(),
            'timers': timer_summaries,
            'period': {
                'start': self.metrics[0].timestamp if self.metrics else None,
                'end': self.metrics[-1].timestamp if self.metrics else None
            }
        }

    def save_metrics(self, filename: Optional[str] = None):
        """
        Save metrics to file.

        Args:
            filename: Output filename (default: metrics_<timestamp>.json)
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{timestamp}.json"

        filepath = self.storage_path / filename

        data = {
            'summary': self.get_summary(),
            'metrics': [m.to_dict() for m in self.metrics]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Metrics saved: {filepath}")

    def clear_metrics(self):
        """Clear all metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()
        self.timers.clear()
        logger.info("Metrics cleared")


class Timer:
    """Context manager for timing operations."""

    def __init__(self, collector: MetricsCollector, name: str, tags: Optional[Dict] = None):
        """
        Initialize timer.

        Args:
            collector: MetricsCollector instance
            name: Timer name
            tags: Optional tags
        """
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record metric."""
        duration = time.time() - self.start_time
        self.collector.record_timer(self.name, duration, self.tags)
