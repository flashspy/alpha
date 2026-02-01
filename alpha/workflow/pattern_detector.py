"""
Workflow Pattern Detector

Analyzes task execution history to detect recurring patterns worthy of workflow automation.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


@dataclass
class WorkflowPattern:
    """Detected workflow pattern from task history."""
    pattern_id: str
    task_sequence: List[str]  # Normalized task descriptions
    frequency: int  # Number of times this sequence occurred
    confidence: float  # 0.0 to 1.0
    first_seen: datetime
    last_seen: datetime
    avg_interval: timedelta  # Average time between occurrences
    task_ids: List[str]  # Original task IDs
    suggested_workflow_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "task_sequence": self.task_sequence,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "avg_interval": self.avg_interval.total_seconds() if self.avg_interval else None,
            "task_ids": self.task_ids,
            "suggested_workflow_name": self.suggested_workflow_name,
            "metadata": self.metadata
        }


class WorkflowPatternDetector:
    """
    Analyzes task execution history to detect workflow-worthy patterns.

    Detection Algorithm:
    1. Fetch recent task executions (last N days)
    2. Normalize task descriptions (remove dates, specific values)
    3. Find recurring sequences (using sliding window + LCS)
    4. Filter by frequency threshold (≥3 occurrences)
    5. Filter by temporal proximity (within 7 days)
    6. Calculate confidence score
    7. Generate suggested workflow name
    """

    def __init__(
        self,
        memory_store: Optional[Any] = None,
        min_frequency: int = 3,
        min_confidence: float = 0.7,
        lookback_days: int = 30
    ):
        """
        Initialize pattern detector.

        Args:
            memory_store: Memory store instance for fetching task history
            min_frequency: Minimum pattern frequency to consider
            min_confidence: Minimum confidence threshold
            lookback_days: Days of history to analyze
        """
        self.memory_store = memory_store
        self.min_frequency = min_frequency
        self.min_confidence = min_confidence
        self.lookback_days = lookback_days

        # Normalization patterns
        self.date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}')
        self.time_pattern = re.compile(r'\d{1,2}:\d{2}(:\d{2})?(\s*[AP]M)?', re.IGNORECASE)
        self.number_pattern = re.compile(r'\b\d+\b')
        self.branch_pattern = re.compile(r'feature/\S+|bugfix/\S+|hotfix/\S+')
        self.path_pattern = re.compile(r'/[^\s]+|[A-Za-z]:\\[^\s]+')

    def normalize_task_description(self, description: str) -> str:
        """
        Normalize task description for pattern matching.

        Removes:
        - Dates (2026-01-15 → DATETOKEN)
        - Times (23:45 → TIMETOKEN)
        - Numbers (123 → NUMTOKEN)
        - File paths (/path/to/file → PATHTOKEN)
        - Git branches (feature/auth → BRANCHTOKEN)

        Examples:
            "Deploy to staging on 2026-01-15" → "Deploy to staging on DATETOKEN"
            "Backup files at 23:45" → "Backup files at TIMETOKEN"
            "Pull branch feature/auth" → "Pull branch BRANCHTOKEN"
        """
        if not description:
            return ""

        # Normalize to lowercase
        normalized = description.lower().strip()

        # Replace specific patterns with tokens
        normalized = self.date_pattern.sub("DATETOKEN", normalized)
        normalized = self.time_pattern.sub("TIMETOKEN", normalized)
        normalized = self.branch_pattern.sub("BRANCHTOKEN", normalized)
        normalized = self.path_pattern.sub("PATHTOKEN", normalized)
        normalized = self.number_pattern.sub("NUMTOKEN", normalized)

        # Remove extra whitespace
        normalized = " ".join(normalized.split())

        return normalized

    def detect_workflow_patterns(
        self,
        lookback_days: Optional[int] = None,
        min_frequency: Optional[int] = None,
        min_sequence_length: int = 2,
        max_interval_days: int = 7
    ) -> List[WorkflowPattern]:
        """
        Detect workflow patterns from task history.

        Args:
            lookback_days: Days of history to analyze (default: self.lookback_days)
            min_frequency: Minimum occurrences (default: self.min_frequency)
            min_sequence_length: Minimum tasks in sequence (default: 2)
            max_interval_days: Max days between pattern occurrences

        Returns:
            List of detected patterns, sorted by (confidence DESC, frequency DESC)
        """
        lookback_days = lookback_days or self.lookback_days
        min_frequency = min_frequency or self.min_frequency

        logger.info(f"Detecting workflow patterns (lookback={lookback_days}d, min_freq={min_frequency})")

        # Fetch task history
        tasks = self._fetch_task_history(lookback_days)
        if not tasks:
            logger.info("No task history found")
            return []

        logger.info(f"Analyzing {len(tasks)} tasks")

        # Normalize task descriptions
        normalized_tasks = [
            (task, self.normalize_task_description(task.get("description", "")))
            for task in tasks
        ]

        # Find recurring sequences
        sequences = self._find_recurring_sequences(
            normalized_tasks,
            min_frequency=min_frequency,
            min_length=min_sequence_length,
            max_interval_days=max_interval_days
        )

        if not sequences:
            logger.info("No recurring sequences found")
            return []

        # Convert sequences to WorkflowPattern objects
        patterns = []
        for sequence, occurrences in sequences.items():
            if len(occurrences) >= min_frequency:
                pattern = self._create_pattern_from_sequence(sequence, occurrences)
                if pattern and pattern.confidence >= self.min_confidence:
                    patterns.append(pattern)

        # Sort by confidence (DESC), then frequency (DESC)
        patterns.sort(key=lambda p: (p.confidence, p.frequency), reverse=True)

        logger.info(f"Detected {len(patterns)} workflow patterns")
        return patterns

    def _fetch_task_history(self, lookback_days: int) -> List[Dict[str, Any]]:
        """
        Fetch task execution history from memory store.

        Returns list of task dicts with keys: id, description, created_at, status, etc.
        """
        if not self.memory_store:
            # Return empty list if no memory store
            return []

        try:
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=lookback_days)

            # Fetch tasks (implementation depends on memory store interface)
            # This is a placeholder - actual implementation will use memory_store API
            tasks = []

            # Placeholder: return empty for now
            # In real implementation: tasks = self.memory_store.get_tasks_since(cutoff_date)

            return tasks

        except Exception as e:
            logger.error(f"Error fetching task history: {e}")
            return []

    def _find_recurring_sequences(
        self,
        normalized_tasks: List[Tuple[Dict[str, Any], str]],
        min_frequency: int,
        min_length: int,
        max_interval_days: int
    ) -> Dict[Tuple[str, ...], List[List[Dict[str, Any]]]]:
        """
        Find recurring task sequences using sliding window.

        Args:
            normalized_tasks: List of (original_task, normalized_description) tuples
            min_frequency: Minimum occurrences
            min_length: Minimum sequence length
            max_interval_days: Maximum days between consecutive tasks in sequence

        Returns:
            Dict mapping sequence tuples to lists of occurrence lists
        """
        sequences = defaultdict(list)

        # Try different sequence lengths
        for seq_len in range(min_length, min(6, len(normalized_tasks) + 1)):  # Max length 5
            # Sliding window
            for i in range(len(normalized_tasks) - seq_len + 1):
                window = normalized_tasks[i:i + seq_len]

                # Check temporal proximity
                if not self._check_temporal_proximity(window, max_interval_days):
                    continue

                # Create sequence tuple from normalized descriptions
                sequence = tuple(norm_desc for _, norm_desc in window)

                # Get original tasks
                original_tasks = [task for task, _ in window]

                # Add to sequences
                sequences[sequence].append(original_tasks)

        # Filter by frequency
        filtered = {
            seq: occurrences
            for seq, occurrences in sequences.items()
            if len(occurrences) >= min_frequency
        }

        return filtered

    def _check_temporal_proximity(
        self,
        window: List[Tuple[Dict[str, Any], str]],
        max_interval_days: int
    ) -> bool:
        """
        Check if tasks in window occurred within max_interval_days of each other.

        Args:
            window: List of (task, normalized_description) tuples
            max_interval_days: Maximum allowed days between consecutive tasks

        Returns:
            True if all tasks are within proximity, False otherwise
        """
        if len(window) < 2:
            return True

        max_interval = timedelta(days=max_interval_days)

        for i in range(len(window) - 1):
            task1, _ = window[i]
            task2, _ = window[i + 1]

            # Get timestamps
            time1 = task1.get("created_at") or task1.get("timestamp")
            time2 = task2.get("created_at") or task2.get("timestamp")

            if not time1 or not time2:
                continue

            # Convert to datetime if needed
            if isinstance(time1, str):
                time1 = datetime.fromisoformat(time1.replace('Z', '+00:00'))
            if isinstance(time2, str):
                time2 = datetime.fromisoformat(time2.replace('Z', '+00:00'))

            # Check interval
            if abs(time2 - time1) > max_interval:
                return False

        return True

    def _create_pattern_from_sequence(
        self,
        sequence: Tuple[str, ...],
        occurrences: List[List[Dict[str, Any]]]
    ) -> Optional[WorkflowPattern]:
        """
        Create WorkflowPattern from detected sequence.

        Args:
            sequence: Tuple of normalized task descriptions
            occurrences: List of occurrence lists (each occurrence is a list of tasks)

        Returns:
            WorkflowPattern instance or None if invalid
        """
        if not occurrences:
            return None

        try:
            # Generate pattern ID
            pattern_id = f"pattern_{hash(sequence) % 1000000:06d}"

            # Extract task IDs
            all_task_ids = []
            timestamps = []

            for occurrence in occurrences:
                for task in occurrence:
                    task_id = task.get("id") or task.get("task_id", "")
                    if task_id:
                        all_task_ids.append(task_id)

                    # Collect timestamps
                    ts = task.get("created_at") or task.get("timestamp")
                    if ts:
                        if isinstance(ts, str):
                            ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        timestamps.append(ts)

            # Calculate temporal statistics
            if timestamps:
                first_seen = min(timestamps)
                last_seen = max(timestamps)

                # Calculate average interval between occurrences
                if len(occurrences) > 1:
                    occurrence_times = [
                        min(task.get("created_at") or task.get("timestamp", datetime.now())
                            for task in occurrence)
                        for occurrence in occurrences
                    ]
                    occurrence_times = [
                        datetime.fromisoformat(t.replace('Z', '+00:00')) if isinstance(t, str) else t
                        for t in occurrence_times
                    ]
                    occurrence_times.sort()

                    intervals = [
                        occurrence_times[i + 1] - occurrence_times[i]
                        for i in range(len(occurrence_times) - 1)
                    ]
                    avg_interval = sum(intervals, timedelta()) / len(intervals) if intervals else timedelta(0)
                else:
                    avg_interval = timedelta(0)
            else:
                first_seen = datetime.now()
                last_seen = datetime.now()
                avg_interval = timedelta(0)

            # Calculate confidence
            frequency = len(occurrences)
            confidence = self.calculate_pattern_confidence(
                frequency=frequency,
                sequence_length=len(sequence),
                avg_interval=avg_interval,
                success_rate=1.0  # Placeholder - would calculate from task statuses
            )

            # Generate suggested workflow name
            suggested_name = self._generate_workflow_name(sequence)

            return WorkflowPattern(
                pattern_id=pattern_id,
                task_sequence=list(sequence),
                frequency=frequency,
                confidence=confidence,
                first_seen=first_seen,
                last_seen=last_seen,
                avg_interval=avg_interval,
                task_ids=all_task_ids,
                suggested_workflow_name=suggested_name,
                metadata={
                    "sequence_length": len(sequence),
                    "total_tasks": len(all_task_ids),
                    "occurrences": len(occurrences)
                }
            )

        except Exception as e:
            logger.error(f"Error creating pattern: {e}")
            return None

    def calculate_pattern_confidence(
        self,
        frequency: int,
        sequence_length: int,
        avg_interval: timedelta,
        success_rate: float
    ) -> float:
        """
        Calculate confidence score for a pattern.

        Factors:
        - Frequency: Higher = better (40% weight)
        - Regularity: Consistent intervals = better (30% weight)
        - Sequence length: Longer = more specific = better (20% weight)
        - Success rate: Higher = better (10% weight)

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Frequency score (normalize by expected max ~10 occurrences/month)
        freq_score = min(1.0, frequency / 10.0)

        # Regularity score (lower variation = higher score)
        # For now, use a simple heuristic based on avg_interval
        # More regular patterns have shorter average intervals
        interval_days = avg_interval.total_seconds() / 86400 if avg_interval else 0
        if interval_days > 0:
            regularity_score = max(0.0, 1.0 - (interval_days / 30.0))  # Normalize by month
        else:
            regularity_score = 0.5  # Neutral if no interval data

        # Sequence length score (normalize by expected max ~5 tasks)
        length_score = min(1.0, sequence_length / 5.0)

        # Success rate (already 0.0-1.0)
        success_score = success_rate

        # Weighted average
        confidence = (
            0.4 * freq_score +
            0.3 * regularity_score +
            0.2 * length_score +
            0.1 * success_score
        )

        return round(confidence, 2)

    def _generate_workflow_name(self, sequence: Tuple[str, ...]) -> str:
        """
        Generate a suggested workflow name from sequence.

        Strategy:
        1. Extract key verbs/actions from each task
        2. Find common theme (e.g., "deploy", "backup", "test")
        3. Generate descriptive name

        Examples:
            ("deploy to BRANCHTOKEN", "run tests", "check coverage")
            → "Deployment Testing Workflow"

            ("backup PATHTOKEN", "sync to cloud", "verify integrity")
            → "Backup and Sync Workflow"
        """
        if not sequence:
            return "Untitled Workflow"

        # Extract first meaningful words from each task (verbs/actions)
        actions = []
        for task in sequence:
            # Remove tokens
            task_clean = task.replace("DATETOKEN", "").replace("TIMETOKEN", "")
            task_clean = task_clean.replace("NUMTOKEN", "").replace("BRANCHTOKEN", "")
            task_clean = task_clean.replace("PATHTOKEN", "").strip()

            # Get first 2-3 words
            words = task_clean.split()[:3]
            if words:
                actions.append(" ".join(words).title())

        if not actions:
            return "Detected Workflow"

        # Find common theme (most frequent word across actions)
        all_words = " ".join(actions).lower().split()
        word_counts = Counter(all_words)

        # Filter out common stop words
        stop_words = {"the", "a", "an", "to", "of", "in", "on", "at", "from", "and", "or"}
        meaningful_words = [w for w, count in word_counts.most_common(5)
                            if w not in stop_words and len(w) > 2]

        if meaningful_words:
            theme = meaningful_words[0].title()
            return f"{theme} Workflow"
        else:
            # Fallback: use first action
            return f"{actions[0]} Workflow"
