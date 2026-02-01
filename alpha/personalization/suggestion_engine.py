"""
Personalized Suggestions Engine

Generates personalized task and workflow suggestions based on user behavior patterns:
- Workflow suggestions from recurring task sequences
- Tool shortcuts based on usage frequency
- Time-based suggestions aligned with user patterns
- Skill recommendations based on task types

Integrates with ProfileStorage and Proactive Intelligence system.
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Dict, Any, Optional
from collections import Counter
import logging

from .profile_storage import ProfileStorage
from .user_profile import UserProfile

logger = logging.getLogger(__name__)


@dataclass
class Suggestion:
    """
    A personalized suggestion for the user

    Attributes:
        suggestion_type: Type of suggestion (workflow, tool_shortcut, time_based, skill_recommendation)
        title: Short description of the suggestion
        description: Detailed explanation
        action: Suggested action (command or workflow)
        confidence: Confidence score (0.0-1.0)
        context: Additional context data
        created_at: When suggestion was generated
        priority: Priority level (high, medium, low)
    """
    suggestion_type: str
    title: str
    description: str
    action: str
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    priority: str = "medium"  # high, medium, low

    def to_dict(self) -> Dict[str, Any]:
        """Convert suggestion to dictionary"""
        return {
            "suggestion_type": self.suggestion_type,
            "title": self.title,
            "description": self.description,
            "action": self.action,
            "confidence": self.confidence,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "priority": self.priority,
        }


class SuggestionEngine:
    """
    Generates personalized suggestions based on user behavior patterns

    Uses ProfileStorage to access:
    - User profile preferences
    - Interaction patterns
    - Tool usage history
    - Task execution patterns

    Generates 4 types of suggestions:
    1. Workflow Suggestions - From recurring task sequences
    2. Tool Shortcuts - From frequent tool usage
    3. Time-Based Suggestions - Aligned with user's active hours
    4. Skill Recommendations - Based on task types and gaps
    """

    def __init__(
        self,
        profile_storage: ProfileStorage,
        min_confidence: float = 0.7,
        max_suggestions: int = 5
    ):
        """
        Initialize SuggestionEngine

        Args:
            profile_storage: Storage for user profile data
            min_confidence: Minimum confidence threshold for suggestions (0.0-1.0)
            max_suggestions: Maximum number of suggestions to generate per type
        """
        self.storage = profile_storage
        self.min_confidence = min_confidence
        self.max_suggestions = max_suggestions
        self.logger = logging.getLogger(__name__)

    def generate_all_suggestions(
        self,
        profile_id: str = "default",
        current_time: Optional[datetime] = None
    ) -> List[Suggestion]:
        """
        Generate all types of personalized suggestions

        Args:
            profile_id: User profile ID
            current_time: Current time for time-based suggestions (default: now)

        Returns:
            List of all generated suggestions, sorted by priority and confidence
        """
        if current_time is None:
            current_time = datetime.now()

        suggestions = []

        # Generate each type of suggestion
        suggestions.extend(self.generate_workflow_suggestions(profile_id))
        suggestions.extend(self.generate_tool_shortcuts(profile_id))
        suggestions.extend(self.generate_time_based_suggestions(profile_id, current_time))
        suggestions.extend(self.generate_skill_recommendations(profile_id))

        # Filter by confidence threshold
        filtered = [s for s in suggestions if s.confidence >= self.min_confidence]

        # Sort by priority (high > medium > low) then confidence (descending)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_suggestions = sorted(
            filtered,
            key=lambda s: (priority_order.get(s.priority, 1), -s.confidence)
        )

        self.logger.info(
            f"Generated {len(sorted_suggestions)} suggestions "
            f"(filtered from {len(suggestions)} total)"
        )

        return sorted_suggestions

    def generate_workflow_suggestions(self, profile_id: str = "default") -> List[Suggestion]:
        """
        Generate workflow suggestions based on recurring task sequences

        Analyzes interaction patterns to find:
        - Frequently repeated task sequences
        - Common command chains
        - Regular multi-step operations

        Args:
            profile_id: User profile ID

        Returns:
            List of workflow suggestions
        """
        suggestions = []

        try:
            # Get workflow patterns from interaction history
            patterns = self.storage.get_interaction_patterns(
                profile_id=profile_id,
                pattern_type="task_sequence"
            )

            # Analyze patterns for workflow candidates
            for pattern in patterns:
                if pattern.occurrence_count < 3:
                    continue  # Need at least 3 occurrences

                pattern_data = pattern.pattern_data
                task_sequence = pattern_data.get("sequence", [])

                if len(task_sequence) < 2:
                    continue  # Need at least 2 tasks for a workflow

                # Calculate confidence based on occurrence count and consistency
                confidence = min(0.5 + (pattern.occurrence_count / 20), 0.95)

                # Generate suggestion
                title = f"Create workflow for '{' → '.join(task_sequence[:3])}'"
                description = (
                    f"I notice you often perform this sequence of tasks "
                    f"({pattern.occurrence_count} times). Would you like to create "
                    f"an automated workflow?"
                )

                # Determine priority based on frequency
                if pattern.occurrence_count >= 10:
                    priority = "high"
                elif pattern.occurrence_count >= 5:
                    priority = "medium"
                else:
                    priority = "low"

                suggestion = Suggestion(
                    suggestion_type="workflow",
                    title=title,
                    description=description,
                    action=f"workflow create --from-sequence {pattern.id}",
                    confidence=confidence,
                    context={
                        "task_sequence": task_sequence,
                        "occurrence_count": pattern.occurrence_count,
                        "pattern_id": pattern.id,
                    },
                    priority=priority
                )

                suggestions.append(suggestion)

        except Exception as e:
            self.logger.error(f"Error generating workflow suggestions: {e}")

        return suggestions[:self.max_suggestions]

    def generate_tool_shortcuts(self, profile_id: str = "default") -> List[Suggestion]:
        """
        Generate tool shortcut suggestions based on usage frequency

        Identifies:
        - Frequently used tool combinations
        - Common command patterns
        - Repetitive operations that could be aliased

        Args:
            profile_id: User profile ID

        Returns:
            List of tool shortcut suggestions
        """
        suggestions = []

        try:
            # Get tool usage patterns
            patterns = self.storage.get_interaction_patterns(
                profile_id=profile_id,
                pattern_type="tool_usage"
            )

            # Analyze tool usage frequency
            tool_counts = Counter()
            for pattern in patterns:
                tool_name = pattern.pattern_data.get("tool_name")
                if tool_name:
                    tool_counts[tool_name] += pattern.occurrence_count

            # Generate suggestions for frequently used tools
            for tool_name, count in tool_counts.most_common(10):
                if count < 5:
                    continue  # Need at least 5 uses

                confidence = min(0.6 + (count / 50), 0.9)

                # Different suggestion types based on tool
                if tool_name.startswith("git"):
                    title = f"Create git alias for '{tool_name}'"
                    description = (
                        f"You use '{tool_name}' frequently ({count} times). "
                        f"Consider creating a shorter alias to save time."
                    )
                    action = f"alias create {tool_name[4:]} '{tool_name}'"
                else:
                    title = f"Add '{tool_name}' to quick access"
                    description = (
                        f"'{tool_name}' is one of your most used tools ({count} times). "
                        f"Add it to your quick access menu?"
                    )
                    action = f"quick-access add {tool_name}"

                # Priority based on usage frequency
                if count >= 20:
                    priority = "high"
                elif count >= 10:
                    priority = "medium"
                else:
                    priority = "low"

                suggestion = Suggestion(
                    suggestion_type="tool_shortcut",
                    title=title,
                    description=description,
                    action=action,
                    confidence=confidence,
                    context={
                        "tool_name": tool_name,
                        "usage_count": count,
                    },
                    priority=priority
                )

                suggestions.append(suggestion)

        except Exception as e:
            self.logger.error(f"Error generating tool shortcut suggestions: {e}")

        return suggestions[:self.max_suggestions]

    def generate_time_based_suggestions(
        self,
        profile_id: str = "default",
        current_time: Optional[datetime] = None
    ) -> List[Suggestion]:
        """
        Generate time-based suggestions aligned with user's patterns

        Provides context-appropriate suggestions:
        - Morning: Daily summary, overnight updates
        - During work hours: Task reminders, proactive assistance
        - Break times: Non-urgent suggestions
        - Evening: Daily wrap-up, preparation for tomorrow

        Args:
            profile_id: User profile ID
            current_time: Current time (default: now)

        Returns:
            List of time-based suggestions
        """
        if current_time is None:
            current_time = datetime.now()

        suggestions = []

        try:
            # Get user profile for active hours
            profile = self.storage.load_profile(profile_id)
            if not profile:
                return suggestions

            current_hour = current_time.hour

            # Morning suggestions (within first hour of active time)
            if current_hour == profile.active_hours_start:
                suggestion = Suggestion(
                    suggestion_type="time_based",
                    title="Morning Summary Available",
                    description=(
                        "Good morning! Ready to review overnight notifications "
                        "and scheduled tasks for today?"
                    ),
                    action="summary daily --overnight",
                    confidence=0.85,
                    context={
                        "time_period": "morning",
                        "hour": current_hour,
                    },
                    priority="high"
                )
                suggestions.append(suggestion)

            # Mid-day check-in (halfway through work hours)
            mid_hour = (profile.active_hours_start + profile.active_hours_end) // 2
            if current_hour == mid_hour:
                suggestion = Suggestion(
                    suggestion_type="time_based",
                    title="Mid-Day Progress Check",
                    description=(
                        "Halfway through your day. Would you like a "
                        "progress summary and priority check?"
                    ),
                    action="tasks status --priority high",
                    confidence=0.75,
                    context={
                        "time_period": "midday",
                        "hour": current_hour,
                    },
                    priority="medium"
                )
                suggestions.append(suggestion)

            # Evening wrap-up (at end of active hours)
            if current_hour == profile.active_hours_end:
                suggestion = Suggestion(
                    suggestion_type="time_based",
                    title="Daily Summary Ready",
                    description=(
                        "End of day approaching. Your daily summary is ready "
                        "when you are. Review accomplishments and plan tomorrow?"
                    ),
                    action="summary daily --wrap-up",
                    confidence=0.9,
                    context={
                        "time_period": "evening",
                        "hour": current_hour,
                    },
                    priority="high"
                )
                suggestions.append(suggestion)

            # Weekend vs weekday suggestions
            is_weekend = current_time.weekday() >= 5  # Saturday = 5, Sunday = 6

            if is_weekend and current_hour == profile.active_hours_start:
                suggestion = Suggestion(
                    suggestion_type="time_based",
                    title="Weekend Mode",
                    description=(
                        "It's the weekend! Would you like me to focus on "
                        "personal tasks and reduce work notifications?"
                    ),
                    action="mode set weekend",
                    confidence=0.7,
                    context={
                        "time_period": "weekend",
                        "day": current_time.strftime("%A"),
                    },
                    priority="medium"
                )
                suggestions.append(suggestion)

        except Exception as e:
            self.logger.error(f"Error generating time-based suggestions: {e}")

        return suggestions[:self.max_suggestions]

    def generate_skill_recommendations(self, profile_id: str = "default") -> List[Suggestion]:
        """
        Generate skill recommendations based on task types and gaps

        Analyzes:
        - Task types user performs frequently
        - Skills that could help with those tasks
        - Gaps in current skill set

        Args:
            profile_id: User profile ID

        Returns:
            List of skill recommendations
        """
        suggestions = []

        try:
            # Get user profile for frequent tasks
            profile = self.storage.load_profile(profile_id)
            if not profile or not profile.frequent_tasks:
                return suggestions

            # Task type to skill mapping
            skill_recommendations = {
                "python": {
                    "skills": ["python-debugger", "code-formatter", "test-generator"],
                    "description": "Enhanced Python development tools",
                },
                "git": {
                    "skills": ["git-workflow", "commit-analyzer"],
                    "description": "Advanced git workflow automation",
                },
                "data": {
                    "skills": ["data-analyzer", "csv-processor", "json-processor"],
                    "description": "Data processing and analysis tools",
                },
                "web": {
                    "skills": ["web-scraper", "api-tester"],
                    "description": "Web development and testing utilities",
                },
            }

            # Analyze frequent tasks to identify needs
            task_categories = Counter()
            for task in profile.frequent_tasks:
                task_lower = task.lower()
                for category in skill_recommendations.keys():
                    if category in task_lower:
                        task_categories[category] += 1

            # Generate skill suggestions for top categories
            for category, count in task_categories.most_common(3):
                if count < 3:
                    continue  # Need at least 3 related tasks

                skill_info = skill_recommendations[category]
                confidence = min(0.65 + (count / 20), 0.85)

                suggestion = Suggestion(
                    suggestion_type="skill_recommendation",
                    title=f"Skills for {category.title()} Tasks",
                    description=(
                        f"Based on your {category} tasks ({count} occurrences), "
                        f"these skills might help: {', '.join(skill_info['skills'])}. "
                        f"{skill_info['description']}."
                    ),
                    action=f"skills search {category}",
                    confidence=confidence,
                    context={
                        "category": category,
                        "recommended_skills": skill_info["skills"],
                        "task_count": count,
                    },
                    priority="medium"
                )

                suggestions.append(suggestion)

        except Exception as e:
            self.logger.error(f"Error generating skill recommendations: {e}")

        return suggestions[:self.max_suggestions]

    def get_suggestion_by_type(
        self,
        suggestion_type: str,
        profile_id: str = "default"
    ) -> List[Suggestion]:
        """
        Get suggestions of a specific type

        Args:
            suggestion_type: Type of suggestion to generate
            profile_id: User profile ID

        Returns:
            List of suggestions of the specified type
        """
        if suggestion_type == "workflow":
            return self.generate_workflow_suggestions(profile_id)
        elif suggestion_type == "tool_shortcut":
            return self.generate_tool_shortcuts(profile_id)
        elif suggestion_type == "time_based":
            return self.generate_time_based_suggestions(profile_id)
        elif suggestion_type == "skill_recommendation":
            return self.generate_skill_recommendations(profile_id)
        else:
            self.logger.warning(f"Unknown suggestion type: {suggestion_type}")
            return []
