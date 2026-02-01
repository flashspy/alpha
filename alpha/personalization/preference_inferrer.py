"""
Preference Inferrer - Infer implicit preferences from user behavior

Analyzes behavioral patterns to infer user preferences:
- Tool preferences from usage frequency
- Task priorities from execution patterns
- Workflow patterns from task sequences
- Time-of-day preferences
- Confidence scoring for inferred preferences
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging

from .user_profile import UserProfile, InteractionPattern
from .profile_storage import ProfileStorage


logger = logging.getLogger(__name__)


class PreferenceInferrer:
    """
    Infer user preferences from behavioral patterns

    Uses statistical analysis and heuristics to detect preferences
    from user actions without explicit feedback
    """

    def __init__(self, storage: ProfileStorage, profile_id: str = "default"):
        """
        Initialize preference inferrer

        Args:
            storage: ProfileStorage instance
            profile_id: User profile ID
        """
        self.storage = storage
        self.profile_id = profile_id
        self.profile = storage.load_profile(profile_id)

        if not self.profile:
            raise ValueError(f"Profile {profile_id} not found")

    def infer_all_preferences(self) -> Dict[str, Any]:
        """
        Run all preference inference algorithms

        Returns:
            Dictionary with inferred preferences and confidence scores
        """
        inferences = {}

        # Infer tool preferences
        tool_prefs = self.infer_tool_preferences()
        if tool_prefs:
            inferences["tool_preferences"] = tool_prefs

        # Infer task priorities
        task_priorities = self.infer_task_priorities()
        if task_priorities:
            inferences["task_priorities"] = task_priorities

        # Infer workflow patterns
        workflows = self.infer_workflow_patterns()
        if workflows:
            inferences["workflow_patterns"] = workflows

        # Infer time preferences
        time_prefs = self.infer_time_preferences()
        if time_prefs:
            inferences["time_preferences"] = time_prefs

        # Infer communication style
        comm_style = self.infer_communication_style()
        if comm_style:
            inferences["communication_style"] = comm_style

        return inferences

    def infer_tool_preferences(
        self,
        min_usage: int = 3,
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Infer tool preferences from usage frequency

        Args:
            min_usage: Minimum usage count to consider
            min_confidence: Minimum confidence threshold

        Returns:
            List of tool preferences with confidence scores
        """
        tool_patterns = self.storage.get_interaction_patterns(
            self.profile_id,
            pattern_type="tool_usage",
            min_occurrences=min_usage
        )

        if not tool_patterns:
            return []

        # Calculate total tool usage
        total_usage = sum(p.occurrence_count for p in tool_patterns)

        preferences = []
        for pattern in tool_patterns:
            tool = pattern.pattern_data.get("tool")
            usage_count = pattern.occurrence_count

            # Calculate confidence based on:
            # 1. Usage frequency
            # 2. Consistency over time
            # 3. Recency

            # Frequency score (0.0-1.0)
            frequency_score = min(1.0, usage_count / max(total_usage * 0.3, 1))

            # Consistency score (0.0-1.0)
            days_active = (pattern.last_seen - pattern.first_seen).total_seconds() / 86400
            consistency_score = min(1.0, days_active / 30.0)  # 30 days max

            # Recency score (0.0-1.0) - more weight to recent usage
            days_since_last = (datetime.now() - pattern.last_seen).total_seconds() / 86400
            recency_score = max(0.0, 1.0 - (days_since_last / 14.0))  # 14 days decay

            # Overall confidence (weighted average)
            confidence = (
                frequency_score * 0.5 +
                consistency_score * 0.3 +
                recency_score * 0.2
            )

            if confidence >= min_confidence:
                preferences.append({
                    "tool": tool,
                    "usage_count": usage_count,
                    "frequency": usage_count / total_usage,
                    "confidence": round(confidence, 2),
                    "last_used": pattern.last_seen.isoformat(),
                    "inference": f"User frequently uses {tool} ({usage_count} times)"
                })

        # Sort by confidence (descending)
        preferences.sort(key=lambda x: x["confidence"], reverse=True)

        logger.info(f"Inferred {len(preferences)} tool preferences")
        return preferences

    def infer_task_priorities(
        self,
        min_occurrences: int = 3,
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Infer task priorities from execution patterns

        Args:
            min_occurrences: Minimum task occurrences
            min_confidence: Minimum confidence threshold

        Returns:
            List of task priorities with confidence scores
        """
        task_patterns = self.storage.get_interaction_patterns(
            self.profile_id,
            pattern_type="task_type",
            min_occurrences=min_occurrences
        )

        if not task_patterns:
            return []

        total_tasks = sum(p.occurrence_count for p in task_patterns)

        priorities = []
        for pattern in task_patterns:
            task_type = pattern.pattern_data.get("type")
            count = pattern.occurrence_count

            # Calculate priority confidence
            frequency = count / total_tasks
            consistency = min(1.0, pattern.get_frequency(days=30) / 5.0)  # 5/day max

            days_since = (datetime.now() - pattern.last_seen).total_seconds() / 86400
            recency = max(0.0, 1.0 - (days_since / 7.0))

            confidence = (
                frequency * 0.4 +
                consistency * 0.4 +
                recency * 0.2
            )

            if confidence >= min_confidence:
                # Determine priority level
                if frequency >= 0.4:
                    priority_level = "high"
                elif frequency >= 0.2:
                    priority_level = "medium"
                else:
                    priority_level = "low"

                priorities.append({
                    "task_type": task_type,
                    "priority_level": priority_level,
                    "frequency": round(frequency, 2),
                    "occurrence_count": count,
                    "confidence": round(confidence, 2),
                    "inference": f"{task_type} is a {priority_level} priority task"
                })

        priorities.sort(key=lambda x: x["confidence"], reverse=True)

        logger.info(f"Inferred {len(priorities)} task priorities")
        return priorities

    def infer_workflow_patterns(
        self,
        min_sequence_length: int = 2,
        min_occurrences: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Infer workflow patterns from task/tool sequences

        Detects recurring sequences like:
        - "git status" → "git commit" → "git push"
        - "test" → "debug" → "fix" → "test"

        Args:
            min_sequence_length: Minimum sequence length
            min_occurrences: Minimum times sequence must occur

        Returns:
            List of detected workflow patterns
        """
        # Get tool usage patterns sorted by time
        tool_patterns = self.storage.get_interaction_patterns(
            self.profile_id,
            pattern_type="tool_usage"
        )

        if len(tool_patterns) < min_sequence_length:
            return []

        # Simple sequence detection (consecutive tool usage)
        # TODO: Implement more sophisticated sequence mining algorithms

        workflows = []

        # Look for common 2-step sequences
        tool_sequences = defaultdict(int)

        for i in range(len(tool_patterns) - 1):
            tool1 = tool_patterns[i].pattern_data.get("tool")
            tool2 = tool_patterns[i + 1].pattern_data.get("tool")

            if tool1 and tool2:
                sequence = (tool1, tool2)
                tool_sequences[sequence] += 1

        # Find sequences that occur frequently
        for sequence, count in tool_sequences.items():
            if count >= min_occurrences:
                confidence = min(1.0, count / 10.0)  # 10 occurrences = 100% confidence

                workflows.append({
                    "sequence": list(sequence),
                    "occurrence_count": count,
                    "confidence": round(confidence, 2),
                    "inference": f"User often runs {sequence[0]} followed by {sequence[1]}"
                })

        workflows.sort(key=lambda x: x["occurrence_count"], reverse=True)

        logger.info(f"Inferred {len(workflows)} workflow patterns")
        return workflows

    def infer_time_preferences(
        self,
        min_interactions: int = 20
    ) -> Dict[str, Any]:
        """
        Infer user's time-based preferences

        Analyzes:
        - Most active hours
        - Peak productivity times
        - Preferred work schedule

        Args:
            min_interactions: Minimum interactions needed for reliable inference

        Returns:
            Dictionary with time preferences and confidence
        """
        if self.profile.interaction_count < min_interactions:
            return {}

        time_patterns = self.storage.get_interaction_patterns(
            self.profile_id,
            pattern_type="time_of_day",
            min_occurrences=2
        )

        if not time_patterns:
            return {}

        # Analyze hour distribution
        hour_counts = defaultdict(int)
        for pattern in time_patterns:
            hour = pattern.pattern_data.get("hour")
            if hour is not None:
                hour_counts[hour] = pattern.occurrence_count

        if not hour_counts:
            return {}

        # Find peak hours
        total_interactions = sum(hour_counts.values())
        hour_frequencies = {h: count / total_interactions for h, count in hour_counts.items()}

        # Find continuous active period
        sorted_hours = sorted(hour_counts.keys())

        if not sorted_hours:
            return {}

        # Detect active window (hours with >5% of activity)
        active_threshold = 0.05
        active_hours = [h for h in sorted_hours if hour_frequencies[h] >= active_threshold]

        if not active_hours:
            return {}

        active_start = min(active_hours)
        active_end = max(active_hours)

        # Find peak hour (most activity)
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0]

        # Calculate confidence based on data quality
        confidence = min(1.0, total_interactions / 100.0)  # 100 interactions = full confidence

        # Determine work pattern
        if active_start >= 9 and active_end <= 18:
            pattern_name = "standard_workday"
        elif active_start >= 6 and active_end <= 14:
            pattern_name = "early_bird"
        elif active_start >= 12 and active_end <= 22:
            pattern_name = "afternoon_evening"
        elif active_start >= 18 or active_end <= 6:
            pattern_name = "night_owl"
        else:
            pattern_name = "flexible"

        result = {
            "active_hours_start": active_start,
            "active_hours_end": active_end,
            "peak_hour": peak_hour,
            "pattern_name": pattern_name,
            "confidence": round(confidence, 2),
            "total_interactions": total_interactions,
            "inference": f"User most active {active_start}:00-{active_end}:00, peak at {peak_hour}:00 ({pattern_name})"
        }

        logger.info(f"Inferred time preferences: {pattern_name} ({active_start}-{active_end})")
        return result

    def infer_communication_style(self) -> Dict[str, Any]:
        """
        Infer user's preferred communication style

        Analyzes:
        - Message length patterns
        - Formality level
        - Technical terminology usage

        Returns:
            Dictionary with communication style preferences
        """
        if self.profile.interaction_count < 10:
            return {}

        # Get preference history to analyze trends
        history = self.storage.get_preference_history(
            self.profile_id,
            limit=50
        )

        # Analyze current preferences
        style = {
            "verbosity_level": self.profile.verbosity_level,
            "technical_level": self.profile.technical_level,
            "language_preference": self.profile.language_preference,
            "tone_preference": self.profile.tone_preference,
            "confidence": self.profile.confidence_score
        }

        # Check for stable preferences (not changed recently)
        verbosity_changes = [h for h in history if h.preference_type == "verbosity_level"]
        if verbosity_changes:
            last_change = verbosity_changes[0]
            days_stable = (datetime.now() - last_change.learned_at).total_seconds() / 86400

            # Higher confidence if preference stable for 7+ days
            if days_stable >= 7:
                style["confidence"] = min(1.0, style["confidence"] + 0.1)
                style["stability"] = "stable"
            else:
                style["stability"] = "evolving"
        else:
            style["stability"] = "default"

        style["inference"] = (
            f"User prefers {style['verbosity_level']} responses, "
            f"{style['technical_level']} technical level, "
            f"{style['language_preference']} language"
        )

        return style

    def calculate_overall_confidence(self) -> float:
        """
        Calculate overall confidence in user profile

        Based on:
        - Number of interactions
        - Preference stability
        - Pattern consistency

        Returns:
            Overall confidence score (0.0-1.0)
        """
        # Base confidence from interaction count
        interaction_confidence = min(1.0, self.profile.interaction_count / 100.0)

        # Preference stability (how many preferences have been learned)
        learned_preferences = 0
        if self.profile.verbosity_level != "balanced":
            learned_preferences += 1
        if self.profile.technical_level != "intermediate":
            learned_preferences += 1
        if self.profile.language_preference != "en":
            learned_preferences += 1

        preference_confidence = learned_preferences / 3.0

        # Pattern detection (how many patterns detected)
        patterns = self.storage.get_interaction_patterns(self.profile_id)
        pattern_confidence = min(1.0, len(patterns) / 10.0)  # 10 patterns = full confidence

        # Weighted average
        overall = (
            interaction_confidence * 0.4 +
            preference_confidence * 0.3 +
            pattern_confidence * 0.3
        )

        return round(overall, 2)

    def get_confidence_report(self) -> Dict[str, Any]:
        """
        Get detailed confidence report for all inferences

        Returns:
            Dictionary with confidence scores for each preference type
        """
        report = {
            "overall_confidence": self.calculate_overall_confidence(),
            "interaction_count": self.profile.interaction_count,
            "profile_confidence": self.profile.confidence_score,
            "preferences": {}
        }

        # Add confidence for each preference
        if self.profile.verbosity_level != "balanced":
            history = self.storage.get_preference_history(
                self.profile_id,
                preference_type="verbosity_level",
                limit=1
            )
            if history:
                report["preferences"]["verbosity_level"] = {
                    "value": self.profile.verbosity_level,
                    "confidence": history[0].confidence,
                    "reason": history[0].reason
                }

        if self.profile.technical_level != "intermediate":
            history = self.storage.get_preference_history(
                self.profile_id,
                preference_type="technical_level",
                limit=1
            )
            if history:
                report["preferences"]["technical_level"] = {
                    "value": self.profile.technical_level,
                    "confidence": history[0].confidence,
                    "reason": history[0].reason
                }

        # Add pattern-based inferences
        tool_prefs = self.infer_tool_preferences()
        if tool_prefs:
            report["preferences"]["tool_preferences"] = {
                "count": len(tool_prefs),
                "top_tool": tool_prefs[0]["tool"] if tool_prefs else None,
                "avg_confidence": sum(p["confidence"] for p in tool_prefs) / len(tool_prefs)
            }

        return report
