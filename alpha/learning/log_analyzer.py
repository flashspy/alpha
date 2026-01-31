"""
Alpha - Log Analyzer

Analyzes execution logs to identify patterns, inefficiencies, and improvement opportunities.
Extracts insights from alpha/monitoring/logger.py execution data.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from enum import Enum


logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns detected in logs."""
    RECURRING_ERROR = "recurring_error"
    SLOW_OPERATION = "slow_operation"
    INEFFICIENT_CHAIN = "inefficient_tool_chain"
    SUCCESSFUL_PATTERN = "successful_pattern"
    HIGH_COST_OPERATION = "high_cost_operation"
    TIMEOUT_PATTERN = "timeout_pattern"


class Priority(Enum):
    """Priority levels for improvement recommendations."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1


@dataclass
class LogPattern:
    """
    Represents a detected pattern in execution logs.

    Attributes:
        pattern_type: Type of pattern detected
        description: Human-readable description
        occurrences: Number of times pattern occurred
        examples: Example log entries demonstrating the pattern
        impact_score: Estimated impact (1-10)
        metadata: Additional pattern-specific data
    """
    pattern_type: PatternType
    description: str
    occurrences: int
    examples: List[Dict[str, Any]] = field(default_factory=list)
    impact_score: float = 5.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


@dataclass
class ImprovementRecommendation:
    """
    Recommendation for system improvement.

    Attributes:
        title: Short title
        description: Detailed recommendation
        priority: Priority level
        pattern: Related pattern that triggered recommendation
        action_type: Type of action to take
        action_data: Data needed to execute action
        estimated_impact: Expected improvement impact
        confidence: Confidence in recommendation (0-1)
    """
    title: str
    description: str
    priority: Priority
    pattern: LogPattern
    action_type: str  # config_update, tool_strategy, model_routing, etc.
    action_data: Dict[str, Any] = field(default_factory=dict)
    estimated_impact: str = "medium"  # low, medium, high
    confidence: float = 0.7
    created_at: datetime = field(default_factory=datetime.now)


class LogAnalyzer:
    """
    Analyzes execution logs to identify patterns and generate improvement recommendations.

    Features:
    - Pattern detection (errors, slow ops, inefficiencies)
    - Temporal analysis (trends over time)
    - Tool chain analysis
    - Cost optimization insights
    - Success pattern identification
    """

    def __init__(self, log_dir: str = "logs"):
        """
        Initialize log analyzer.

        Args:
            log_dir: Directory containing execution logs
        """
        self.log_dir = Path(log_dir)
        self.patterns: List[LogPattern] = []
        self.recommendations: List[ImprovementRecommendation] = []

        # Pattern detection thresholds
        self.min_error_occurrences = 3
        self.slow_operation_threshold = 5.0  # seconds
        self.high_cost_threshold = 0.10  # USD
        self.timeout_threshold = 30.0  # seconds

        logger.info(f"Log analyzer initialized: {self.log_dir}")

    async def analyze_logs(
        self,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        log_files: Optional[List[str]] = None
    ) -> List[LogPattern]:
        """
        Analyze execution logs and detect patterns.

        Args:
            time_range: Optional (start, end) datetime tuple
            log_files: Optional specific log files to analyze

        Returns:
            List of detected patterns
        """
        logger.info("Starting log analysis...")

        # Load log entries
        log_entries = await self._load_logs(time_range, log_files)
        logger.info(f"Loaded {len(log_entries)} log entries")

        if not log_entries:
            logger.warning("No log entries found for analysis")
            return []

        # Detect patterns
        self.patterns = []

        # Error patterns
        self.patterns.extend(self._detect_error_patterns(log_entries))

        # Performance patterns
        self.patterns.extend(self._detect_slow_operations(log_entries))

        # Tool chain patterns
        self.patterns.extend(self._detect_inefficient_chains(log_entries))

        # Cost patterns
        self.patterns.extend(self._detect_high_cost_operations(log_entries))

        # Success patterns
        self.patterns.extend(self._detect_successful_patterns(log_entries))

        # Timeout patterns
        self.patterns.extend(self._detect_timeout_patterns(log_entries))

        logger.info(f"Detected {len(self.patterns)} patterns")
        return self.patterns

    async def generate_recommendations(
        self,
        patterns: Optional[List[LogPattern]] = None
    ) -> List[ImprovementRecommendation]:
        """
        Generate improvement recommendations based on detected patterns.

        Args:
            patterns: Optional patterns to analyze (uses self.patterns if None)

        Returns:
            List of improvement recommendations
        """
        if patterns is None:
            patterns = self.patterns

        logger.info(f"Generating recommendations from {len(patterns)} patterns")

        self.recommendations = []

        for pattern in patterns:
            recommendations = self._pattern_to_recommendations(pattern)
            self.recommendations.extend(recommendations)

        # Sort by priority and impact
        self.recommendations.sort(
            key=lambda r: (r.priority.value, r.confidence),
            reverse=True
        )

        logger.info(f"Generated {len(self.recommendations)} recommendations")
        return self.recommendations

    async def analyze_time_period(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Analyze logs for a specific time period.

        Args:
            days: Number of days to analyze (from now backwards)

        Returns:
            Analysis summary dictionary
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        patterns = await self.analyze_logs(time_range=(start_time, end_time))
        recommendations = await self.generate_recommendations(patterns)

        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": days
            },
            "patterns": {
                "total": len(patterns),
                "by_type": self._count_by_type(patterns)
            },
            "recommendations": {
                "total": len(recommendations),
                "by_priority": self._count_by_priority(recommendations)
            },
            "top_patterns": [
                {
                    "type": p.pattern_type.value,
                    "description": p.description,
                    "occurrences": p.occurrences,
                    "impact_score": p.impact_score
                }
                for p in sorted(patterns, key=lambda x: x.impact_score, reverse=True)[:5]
            ],
            "top_recommendations": [
                {
                    "title": r.title,
                    "priority": r.priority.value,
                    "confidence": r.confidence,
                    "impact": r.estimated_impact
                }
                for r in recommendations[:5]
            ]
        }

    async def _load_logs(
        self,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        log_files: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Load log entries from files.

        Args:
            time_range: Optional time range filter
            log_files: Optional specific files to load

        Returns:
            List of log entries
        """
        entries = []

        if not self.log_dir.exists():
            logger.warning(f"Log directory does not exist: {self.log_dir}")
            return entries

        # Determine files to read
        if log_files:
            files = [self.log_dir / f for f in log_files]
        else:
            files = sorted(self.log_dir.glob("*.json*"))

        for log_file in files:
            try:
                if log_file.suffix == '.json':
                    with open(log_file) as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                entry = json.loads(line)

                                # Apply time range filter
                                if time_range:
                                    entry_time = datetime.fromisoformat(
                                        entry.get('timestamp', entry.get('event', ''))
                                    )
                                    if not (time_range[0] <= entry_time <= time_range[1]):
                                        continue

                                entries.append(entry)
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse log line in {log_file}")
                                continue
            except Exception as e:
                logger.error(f"Error reading log file {log_file}: {e}")
                continue

        return entries

    def _detect_error_patterns(self, log_entries: List[Dict]) -> List[LogPattern]:
        """Detect recurring error patterns."""
        patterns = []

        # Group errors by error type and message
        error_groups = defaultdict(list)

        for entry in log_entries:
            if entry.get('event') == 'task_error':
                error_key = (
                    entry.get('error_type', 'Unknown'),
                    entry.get('error', '')[:100]  # First 100 chars
                )
                error_groups[error_key].append(entry)

        # Create patterns for recurring errors
        for (error_type, error_msg), occurrences in error_groups.items():
            if len(occurrences) >= self.min_error_occurrences:
                timestamps = [
                    datetime.fromisoformat(e.get('timestamp', datetime.now().isoformat()))
                    for e in occurrences
                ]

                pattern = LogPattern(
                    pattern_type=PatternType.RECURRING_ERROR,
                    description=f"Recurring {error_type}: {error_msg}",
                    occurrences=len(occurrences),
                    examples=occurrences[:3],
                    impact_score=min(10.0, len(occurrences) / 2),
                    first_seen=min(timestamps),
                    last_seen=max(timestamps),
                    metadata={
                        "error_type": error_type,
                        "error_message": error_msg
                    }
                )
                patterns.append(pattern)

        return patterns

    def _detect_slow_operations(self, log_entries: List[Dict]) -> List[LogPattern]:
        """Detect slow tool executions and operations."""
        patterns = []

        # Group slow operations by tool/operation type
        slow_ops = defaultdict(list)

        for entry in log_entries:
            if entry.get('event') == 'tool_execution':
                duration = entry.get('duration', 0)
                if duration > self.slow_operation_threshold:
                    tool_name = entry.get('tool_name', 'Unknown')
                    slow_ops[tool_name].append(entry)

            elif entry.get('event') == 'task_complete':
                duration = entry.get('duration', 0)
                if duration > self.slow_operation_threshold * 2:
                    task_name = entry.get('task_name', 'Unknown')
                    slow_ops[f"task:{task_name}"].append(entry)

        # Create patterns for consistently slow operations
        for op_name, occurrences in slow_ops.items():
            if len(occurrences) >= 2:
                avg_duration = sum(e.get('duration', 0) for e in occurrences) / len(occurrences)

                pattern = LogPattern(
                    pattern_type=PatternType.SLOW_OPERATION,
                    description=f"Slow operation: {op_name} (avg {avg_duration:.2f}s)",
                    occurrences=len(occurrences),
                    examples=occurrences[:3],
                    impact_score=min(10.0, avg_duration / 2),
                    metadata={
                        "operation": op_name,
                        "average_duration": avg_duration,
                        "max_duration": max(e.get('duration', 0) for e in occurrences)
                    }
                )
                patterns.append(pattern)

        return patterns

    def _detect_inefficient_chains(self, log_entries: List[Dict]) -> List[LogPattern]:
        """Detect inefficient tool usage chains."""
        patterns = []

        # Group tool executions by task
        task_tools = defaultdict(list)

        for entry in log_entries:
            if entry.get('event') == 'tool_execution':
                task_id = entry.get('task_id', 'unknown')
                task_tools[task_id].append(entry.get('tool_name'))

        # Analyze chains
        chain_counter = Counter()
        for task_id, tools in task_tools.items():
            if len(tools) >= 3:
                # Create chain signature
                chain = " -> ".join(tools[:5])
                chain_counter[chain] += 1

        # Identify common chains
        for chain, count in chain_counter.most_common(5):
            if count >= 2:
                pattern = LogPattern(
                    pattern_type=PatternType.INEFFICIENT_CHAIN,
                    description=f"Common tool chain: {chain}",
                    occurrences=count,
                    impact_score=min(10.0, count * 1.5),
                    metadata={"chain": chain}
                )
                patterns.append(pattern)

        return patterns

    def _detect_high_cost_operations(self, log_entries: List[Dict]) -> List[LogPattern]:
        """Detect high-cost LLM operations."""
        patterns = []

        # Group LLM interactions by model
        llm_costs = defaultdict(list)

        for entry in log_entries:
            if entry.get('event') == 'llm_interaction':
                cost = entry.get('estimated_cost', 0)
                if cost and cost > self.high_cost_threshold:
                    model = entry.get('model', 'Unknown')
                    llm_costs[model].append(entry)

        # Create patterns for high-cost models
        for model, occurrences in llm_costs.items():
            if len(occurrences) >= 2:
                total_cost = sum(e.get('estimated_cost', 0) for e in occurrences)
                avg_cost = total_cost / len(occurrences)

                pattern = LogPattern(
                    pattern_type=PatternType.HIGH_COST_OPERATION,
                    description=f"High-cost model usage: {model} (avg ${avg_cost:.4f})",
                    occurrences=len(occurrences),
                    examples=occurrences[:3],
                    impact_score=min(10.0, total_cost * 20),
                    metadata={
                        "model": model,
                        "total_cost": total_cost,
                        "average_cost": avg_cost
                    }
                )
                patterns.append(pattern)

        return patterns

    def _detect_successful_patterns(self, log_entries: List[Dict]) -> List[LogPattern]:
        """Detect successful operation patterns."""
        patterns = []

        # Find tasks with high success rates
        task_outcomes = defaultdict(lambda: {"success": 0, "failure": 0})

        for entry in log_entries:
            if entry.get('event') == 'task_complete':
                task_name = entry.get('task_name', 'Unknown')
                task_outcomes[task_name]["success"] += 1
            elif entry.get('event') == 'task_error':
                task_name = entry.get('task_name', 'Unknown')
                task_outcomes[task_name]["failure"] += 1

        # Identify successful patterns
        for task_name, outcomes in task_outcomes.items():
            total = outcomes["success"] + outcomes["failure"]
            if total >= 5 and outcomes["success"] / total >= 0.9:
                pattern = LogPattern(
                    pattern_type=PatternType.SUCCESSFUL_PATTERN,
                    description=f"High success rate: {task_name} ({outcomes['success']}/{total})",
                    occurrences=outcomes["success"],
                    impact_score=7.0,
                    metadata={
                        "task_name": task_name,
                        "success_rate": outcomes["success"] / total
                    }
                )
                patterns.append(pattern)

        return patterns

    def _detect_timeout_patterns(self, log_entries: List[Dict]) -> List[LogPattern]:
        """Detect timeout patterns."""
        patterns = []

        # Find operations that timeout
        timeouts = defaultdict(list)

        for entry in log_entries:
            if entry.get('event') == 'task_error':
                error = entry.get('error', '').lower()
                if 'timeout' in error:
                    task_name = entry.get('task_name', 'Unknown')
                    timeouts[task_name].append(entry)

        # Create patterns
        for task_name, occurrences in timeouts.items():
            if len(occurrences) >= 2:
                pattern = LogPattern(
                    pattern_type=PatternType.TIMEOUT_PATTERN,
                    description=f"Recurring timeouts: {task_name}",
                    occurrences=len(occurrences),
                    examples=occurrences[:3],
                    impact_score=8.0,
                    metadata={"task_name": task_name}
                )
                patterns.append(pattern)

        return patterns

    def _pattern_to_recommendations(
        self,
        pattern: LogPattern
    ) -> List[ImprovementRecommendation]:
        """Convert a pattern to improvement recommendations."""
        recommendations = []

        if pattern.pattern_type == PatternType.RECURRING_ERROR:
            # Recommend error handling improvement
            rec = ImprovementRecommendation(
                title=f"Improve error handling for {pattern.metadata.get('error_type')}",
                description=(
                    f"This error has occurred {pattern.occurrences} times. "
                    f"Consider adding specific error handling or fixing the root cause."
                ),
                priority=Priority.HIGH if pattern.occurrences > 10 else Priority.MEDIUM,
                pattern=pattern,
                action_type="error_handling",
                action_data={
                    "error_type": pattern.metadata.get('error_type'),
                    "suggested_action": "add_retry_logic"
                },
                estimated_impact="high",
                confidence=0.8
            )
            recommendations.append(rec)

        elif pattern.pattern_type == PatternType.SLOW_OPERATION:
            # Recommend timeout adjustment or caching
            avg_duration = pattern.metadata.get('average_duration', 0)
            rec = ImprovementRecommendation(
                title=f"Optimize slow operation: {pattern.metadata.get('operation')}",
                description=(
                    f"Operation takes {avg_duration:.2f}s on average. "
                    f"Consider caching results or increasing timeout."
                ),
                priority=Priority.MEDIUM,
                pattern=pattern,
                action_type="config_update",
                action_data={
                    "operation": pattern.metadata.get('operation'),
                    "suggested_timeout": avg_duration * 1.5
                },
                estimated_impact="medium",
                confidence=0.7
            )
            recommendations.append(rec)

        elif pattern.pattern_type == PatternType.HIGH_COST_OPERATION:
            # Recommend model routing change
            model = pattern.metadata.get('model', '')
            rec = ImprovementRecommendation(
                title=f"Optimize model usage: {model}",
                description=(
                    f"Model has high cost (avg ${pattern.metadata.get('average_cost', 0):.4f}). "
                    f"Consider using cheaper model for simpler tasks."
                ),
                priority=Priority.HIGH,
                pattern=pattern,
                action_type="model_routing",
                action_data={
                    "current_model": model,
                    "suggested_action": "use_cheaper_model_for_simple_tasks"
                },
                estimated_impact="high",
                confidence=0.9
            )
            recommendations.append(rec)

        elif pattern.pattern_type == PatternType.TIMEOUT_PATTERN:
            # Recommend timeout increase
            task_name = pattern.metadata.get('task_name', '')
            rec = ImprovementRecommendation(
                title=f"Increase timeout for {task_name}",
                description=(
                    f"Task times out frequently ({pattern.occurrences} times). "
                    f"Consider increasing timeout or optimizing task."
                ),
                priority=Priority.MEDIUM,
                pattern=pattern,
                action_type="config_update",
                action_data={
                    "task_name": task_name,
                    "suggested_action": "increase_timeout"
                },
                estimated_impact="medium",
                confidence=0.75
            )
            recommendations.append(rec)

        return recommendations

    def _count_by_type(self, patterns: List[LogPattern]) -> Dict[str, int]:
        """Count patterns by type."""
        counts = defaultdict(int)
        for pattern in patterns:
            counts[pattern.pattern_type.value] += 1
        return dict(counts)

    def _count_by_priority(self, recommendations: List[ImprovementRecommendation]) -> Dict[str, int]:
        """Count recommendations by priority."""
        counts = defaultdict(int)
        for rec in recommendations:
            counts[rec.priority.name] += 1
        return dict(counts)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of analysis results.

        Returns:
            Summary dictionary
        """
        return {
            "patterns_detected": len(self.patterns),
            "patterns_by_type": self._count_by_type(self.patterns),
            "recommendations_generated": len(self.recommendations),
            "recommendations_by_priority": self._count_by_priority(self.recommendations),
            "high_priority_recommendations": [
                {
                    "title": r.title,
                    "confidence": r.confidence,
                    "impact": r.estimated_impact
                }
                for r in self.recommendations
                if r.priority in [Priority.CRITICAL, Priority.HIGH]
            ]
        }
