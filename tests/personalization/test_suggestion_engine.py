"""
Tests for Personalized Suggestions Engine

Tests all suggestion generation functionality:
- Suggestion data class
- Workflow suggestions
- Tool shortcut suggestions
- Time-based suggestions
- Skill recommendations
- Priority and confidence sorting
"""

import pytest
from datetime import datetime, time
from unittest.mock import Mock
import tempfile
import os

from alpha.personalization.suggestion_engine import (
    Suggestion,
    SuggestionEngine
)
from alpha.personalization.profile_storage import ProfileStorage
from alpha.personalization.user_profile import UserProfile, InteractionPattern


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def storage(temp_db):
    """Create ProfileStorage instance for testing"""
    # ProfileStorage automatically creates tables in __init__
    return ProfileStorage(temp_db)


@pytest.fixture
def engine(storage):
    """Create SuggestionEngine instance for testing"""
    return SuggestionEngine(
        profile_storage=storage,
        min_confidence=0.7,
        max_suggestions=5
    )


# ==================== Suggestion Data Class Tests ====================


class TestSuggestion:
    """Test Suggestion data class"""

    def test_suggestion_creation(self):
        """Test creating a basic suggestion"""
        suggestion = Suggestion(
            suggestion_type="workflow",
            title="Test Workflow",
            description="A test workflow suggestion",
            action="workflow create test",
            confidence=0.85
        )

        assert suggestion.suggestion_type == "workflow"
        assert suggestion.title == "Test Workflow"
        assert suggestion.description == "A test workflow suggestion"
        assert suggestion.action == "workflow create test"
        assert suggestion.confidence == 0.85
        assert suggestion.priority == "medium"  # default
        assert isinstance(suggestion.context, dict)
        assert isinstance(suggestion.created_at, datetime)

    def test_suggestion_to_dict(self):
        """Test converting suggestion to dictionary"""
        suggestion = Suggestion(
            suggestion_type="tool_shortcut",
            title="Git Alias",
            description="Create git shortcut",
            action="alias create status 'git status'",
            confidence=0.9,
            context={"tool": "git", "count": 20},
            priority="high"
        )

        data = suggestion.to_dict()

        assert data["suggestion_type"] == "tool_shortcut"
        assert data["title"] == "Git Alias"
        assert data["description"] == "Create git shortcut"
        assert data["action"] == "alias create status 'git status'"
        assert data["confidence"] == 0.9
        assert data["context"]["tool"] == "git"
        assert data["context"]["count"] == 20
        assert data["priority"] == "high"
        assert "created_at" in data

    def test_suggestion_with_custom_context(self):
        """Test suggestion with custom context data"""
        context = {
            "task_sequence": ["task1", "task2", "task3"],
            "occurrence_count": 15,
            "pattern_id": 123
        }

        suggestion = Suggestion(
            suggestion_type="workflow",
            title="Multi-task Workflow",
            description="Frequent task sequence",
            action="workflow create --from-pattern 123",
            confidence=0.88,
            context=context
        )

        assert suggestion.context["task_sequence"] == ["task1", "task2", "task3"]
        assert suggestion.context["occurrence_count"] == 15
        assert suggestion.context["pattern_id"] == 123


# ==================== SuggestionEngine Core Tests ====================


class TestSuggestionEngine:
    """Test SuggestionEngine initialization and core functionality"""

    def test_engine_initialization(self, storage):
        """Test creating SuggestionEngine"""
        engine = SuggestionEngine(
            profile_storage=storage,
            min_confidence=0.75,
            max_suggestions=10
        )

        assert engine.storage == storage
        assert engine.min_confidence == 0.75
        assert engine.max_suggestions == 10

    def test_engine_default_parameters(self, storage):
        """Test default engine parameters"""
        engine = SuggestionEngine(profile_storage=storage)

        assert engine.min_confidence == 0.7
        assert engine.max_suggestions == 5


# ==================== Workflow Suggestions Tests ====================


class TestWorkflowSuggestions:
    """Test workflow suggestion generation"""

    def test_workflow_suggestions_no_patterns(self, engine, storage):
        """Test workflow suggestions with no interaction patterns"""
        # No patterns saved yet
        suggestions = engine.generate_workflow_suggestions("default")

        assert len(suggestions) == 0

    def test_workflow_suggestions_below_threshold(self, engine, storage):
        """Test workflow patterns below occurrence threshold"""
        # Create profile
        profile = UserProfile(id="default")
        storage.save_profile(profile)

        # Save pattern with only 2 occurrences (threshold is 3)
        pattern = InteractionPattern(
            profile_id="default",
            pattern_type="task_sequence",
            pattern_data={
                "sequence": ["git status", "git add", "git commit"]
            },
            occurrence_count=2
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_workflow_suggestions("default")

        assert len(suggestions) == 0  # Below threshold

    def test_workflow_suggestions_frequent_pattern(self, engine, storage):
        """Test workflow suggestions for frequent patterns"""
        # Create profile
        profile = UserProfile(id="default")
        storage.save_profile(profile)

        # Save pattern with 5 occurrences
        pattern = InteractionPattern(
            profile_id="default",
            pattern_type="task_sequence",
            pattern_data={
                "sequence": ["email check", "email summarize", "email reply"]
            },
            occurrence_count=5
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_workflow_suggestions("default")

        assert len(suggestions) == 1
        suggestion = suggestions[0]

        assert suggestion.suggestion_type == "workflow"
        assert "email check" in suggestion.title
        assert suggestion.confidence >= 0.7
        assert suggestion.priority == "medium"  # 5-9 occurrences
        assert suggestion.context["occurrence_count"] == 5
        assert len(suggestion.context["task_sequence"]) == 3

    def test_workflow_suggestions_high_priority(self, engine, storage):
        """Test high priority workflow suggestions"""
        # Create profile
        profile = UserProfile(id="default")
        storage.save_profile(profile)

        # Save pattern with 12 occurrences (>= 10 → high priority)
        pattern = InteractionPattern(
            profile_id="default",
            pattern_type="task_sequence",
            pattern_data={
                "sequence": ["deploy start", "test run", "monitor check"]
            },
            occurrence_count=12
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_workflow_suggestions("default")

        assert len(suggestions) == 1
        assert suggestions[0].priority == "high"
        assert suggestions[0].confidence >= 0.7

    def test_workflow_suggestions_confidence_calculation(self, engine, storage):
        """Test confidence score calculation based on occurrence"""
        profile = UserProfile(id="default")
        storage.save_profile(profile)

        # Pattern with 3 occurrences
        pattern1 = InteractionPattern(
            profile_id="default",
            pattern_type="task_sequence",
            pattern_data={"sequence": ["task1", "task2"]},
            occurrence_count=3
        )
        storage.save_interaction_pattern(pattern1)

        # Pattern with 20 occurrences (should have higher confidence)
        pattern2 = InteractionPattern(
            profile_id="default",
            pattern_type="task_sequence",
            pattern_data={"sequence": ["task3", "task4"]},
            occurrence_count=20
        )
        storage.save_interaction_pattern(pattern2)

        suggestions = engine.generate_workflow_suggestions("default")

        assert len(suggestions) == 2
        # Pattern with more occurrences should have higher confidence
        # (but limited by max suggestions if more than 5)


# ==================== Tool Shortcut Suggestions Tests ====================


class TestToolShortcutSuggestions:
    """Test tool shortcut suggestion generation"""

    def test_tool_shortcuts_no_patterns(self, engine, storage):
        """Test tool shortcuts with no usage patterns"""
        suggestions = engine.generate_tool_shortcuts("default")

        assert len(suggestions) == 0

    def test_tool_shortcuts_below_threshold(self, engine, storage):
        """Test tool usage below threshold"""
        profile = UserProfile(id="default")
        storage.save_profile(profile)

        # Tool used only 3 times (threshold is 5)
        pattern = InteractionPattern(
            profile_id="default",
            pattern_type="tool_usage",
            pattern_data={"tool_name": "shell"},
            occurrence_count=3
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_tool_shortcuts("default")

        assert len(suggestions) == 0

    def test_tool_shortcuts_git_tools(self, engine, storage):
        """Test git tool shortcut suggestions"""
        profile = UserProfile(id="default")
        storage.save_profile(profile)

        # Frequent git usage
        pattern = InteractionPattern(
            profile_id="default",
            pattern_type="tool_usage",
            pattern_data={"tool_name": "git status"},
            occurrence_count=15
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_tool_shortcuts("default")

        assert len(suggestions) == 1
        suggestion = suggestions[0]

        assert suggestion.suggestion_type == "tool_shortcut"
        assert "git alias" in suggestion.title.lower()
        assert "git status" in suggestion.description
        assert suggestion.context["tool_name"] == "git status"
        assert suggestion.context["usage_count"] == 15
        assert suggestion.priority == "medium"  # 10-19 uses

    def test_tool_shortcuts_high_usage(self, engine, storage):
        """Test high usage tools get high priority"""
        profile = UserProfile(id="default")
        storage.save_profile(profile)

        # Very frequent usage (>= 20 → high priority)
        pattern = InteractionPattern(
            profile_id="default",
            pattern_type="tool_usage",
            pattern_data={"tool_name": "search"},
            occurrence_count=25
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_tool_shortcuts("default")

        assert len(suggestions) == 1
        assert suggestions[0].priority == "high"
        assert suggestions[0].confidence >= 0.7

    def test_tool_shortcuts_multiple_tools(self, engine, storage):
        """Test suggestions for multiple frequently used tools"""
        profile = UserProfile(id="default")
        storage.save_profile(profile)

        # Multiple tools
        tools = [
            ("git status", 20),
            ("search", 15),
            ("file", 10),
            ("http", 8),
            ("calculator", 5)
        ]

        for tool_name, count in tools:
            pattern = InteractionPattern(
                profile_id="default",
                pattern_type="tool_usage",
                pattern_data={"tool_name": tool_name},
                occurrence_count=count
            )
            storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_tool_shortcuts("default")

        # Should get all 5 (max_suggestions default is 5)
        assert len(suggestions) <= 5
        # Should be ordered by usage count
        assert suggestions[0].context["usage_count"] >= suggestions[-1].context["usage_count"]


# ==================== Time-Based Suggestions Tests ====================


class TestTimeBasedSuggestions:
    """Test time-based suggestion generation"""

    def test_time_based_suggestions_no_profile(self, engine, storage):
        """Test time-based suggestions without profile"""
        suggestions = engine.generate_time_based_suggestions("default")

        assert len(suggestions) == 0  # No profile

    def test_time_based_morning_suggestion(self, engine, storage):
        """Test morning suggestion at start of work day"""
        profile = UserProfile(
            id="default",
            active_hours_start=9,
            active_hours_end=18
        )
        storage.save_profile(profile)

        # Simulate morning time (9am)
        morning_time = datetime(2026, 2, 2, 9, 0, 0)

        suggestions = engine.generate_time_based_suggestions("default", morning_time)

        assert len(suggestions) >= 1
        morning_sugg = next((s for s in suggestions if "morning" in s.title.lower()), None)
        assert morning_sugg is not None
        assert morning_sugg.suggestion_type == "time_based"
        assert morning_sugg.priority == "high"
        assert morning_sugg.context["time_period"] == "morning"

    def test_time_based_midday_suggestion(self, engine, storage):
        """Test mid-day suggestion"""
        profile = UserProfile(
            id="default",
            active_hours_start=9,
            active_hours_end=17
        )
        storage.save_profile(profile)

        # Mid-day: (9 + 17) // 2 = 13 (1pm)
        midday_time = datetime(2026, 2, 2, 13, 0, 0)

        suggestions = engine.generate_time_based_suggestions("default", midday_time)

        assert len(suggestions) >= 1
        midday_sugg = next((s for s in suggestions if "mid" in s.title.lower()), None)
        assert midday_sugg is not None
        assert midday_sugg.context["time_period"] == "midday"
        assert midday_sugg.priority == "medium"

    def test_time_based_evening_suggestion(self, engine, storage):
        """Test evening wrap-up suggestion"""
        profile = UserProfile(
            id="default",
            active_hours_start=9,
            active_hours_end=18
        )
        storage.save_profile(profile)

        # Evening: 18:00 (6pm)
        evening_time = datetime(2026, 2, 2, 18, 0, 0)

        suggestions = engine.generate_time_based_suggestions("default", evening_time)

        assert len(suggestions) >= 1
        evening_sugg = next((s for s in suggestions if "summary" in s.title.lower()), None)
        assert evening_sugg is not None
        assert evening_sugg.context["time_period"] == "evening"
        assert evening_sugg.priority == "high"

    def test_time_based_weekend_suggestion(self, engine, storage):
        """Test weekend-specific suggestion"""
        profile = UserProfile(
            id="default",
            active_hours_start=10,
            active_hours_end=17
        )
        storage.save_profile(profile)

        # Saturday morning (weekday = 5)
        saturday_morning = datetime(2026, 2, 7, 10, 0, 0)  # Feb 7, 2026 is Saturday

        suggestions = engine.generate_time_based_suggestions("default", saturday_morning)

        # Should have both weekend and morning suggestions
        weekend_sugg = next((s for s in suggestions if "weekend" in s.title.lower()), None)
        assert weekend_sugg is not None
        assert weekend_sugg.context["time_period"] == "weekend"


# ==================== Skill Recommendation Tests ====================


class TestSkillRecommendations:
    """Test skill recommendation generation"""

    def test_skill_recommendations_no_profile(self, engine, storage):
        """Test skill recommendations without profile"""
        suggestions = engine.generate_skill_recommendations("default")

        assert len(suggestions) == 0

    def test_skill_recommendations_no_frequent_tasks(self, engine, storage):
        """Test skill recommendations without frequent tasks"""
        profile = UserProfile(id="default", frequent_tasks=[])
        storage.save_profile(profile)

        suggestions = engine.generate_skill_recommendations("default")

        assert len(suggestions) == 0

    def test_skill_recommendations_python_tasks(self, engine, storage):
        """Test skill recommendations for Python tasks"""
        profile = UserProfile(
            id="default",
            frequent_tasks=[
                "python script execution",
                "python debug session",
                "python test run",
                "python code review"
            ]
        )
        storage.save_profile(profile)

        suggestions = engine.generate_skill_recommendations("default")

        assert len(suggestions) >= 1
        python_sugg = next((s for s in suggestions if "python" in s.title.lower()), None)
        assert python_sugg is not None
        assert python_sugg.suggestion_type == "skill_recommendation"
        assert "python" in python_sugg.context["category"]
        assert len(python_sugg.context["recommended_skills"]) > 0
        assert python_sugg.priority == "medium"

    def test_skill_recommendations_git_tasks(self, engine, storage):
        """Test skill recommendations for git tasks"""
        profile = UserProfile(
            id="default",
            frequent_tasks=[
                "git commit",
                "git push",
                "git merge",
                "git rebase"
            ]
        )
        storage.save_profile(profile)

        suggestions = engine.generate_skill_recommendations("default")

        assert len(suggestions) >= 1
        git_sugg = next((s for s in suggestions if "git" in s.title.lower()), None)
        assert git_sugg is not None
        assert "git" in git_sugg.context["category"]
        assert git_sugg.context["task_count"] >= 3

    def test_skill_recommendations_data_tasks(self, engine, storage):
        """Test skill recommendations for data tasks"""
        profile = UserProfile(
            id="default",
            frequent_tasks=[
                "data analysis",
                "data transformation",
                "data export"
            ]
        )
        storage.save_profile(profile)

        suggestions = engine.generate_skill_recommendations("default")

        assert len(suggestions) >= 1
        data_sugg = next((s for s in suggestions if "data" in s.title.lower()), None)
        assert data_sugg is not None
        assert "data" in data_sugg.context["category"]

    def test_skill_recommendations_below_threshold(self, engine, storage):
        """Test no recommendations when task count below threshold"""
        profile = UserProfile(
            id="default",
            frequent_tasks=[
                "python script",
                "python test"  # Only 2 python tasks (threshold is 3)
            ]
        )
        storage.save_profile(profile)

        suggestions = engine.generate_skill_recommendations("default")

        # Should not suggest python skills (only 2 occurrences)
        python_sugg = next((s for s in suggestions if "python" in s.title.lower()), None)
        assert python_sugg is None


# ==================== Integration Tests ====================


class TestSuggestionEngineIntegration:
    """Test integrated suggestion generation"""

    def test_generate_all_suggestions_empty(self, engine, storage):
        """Test generating all suggestions with no data"""
        suggestions = engine.generate_all_suggestions("default")

        assert len(suggestions) == 0

    def test_generate_all_suggestions_with_data(self, engine, storage):
        """Test generating all types of suggestions"""
        # Create comprehensive profile
        profile = UserProfile(
            id="default",
            active_hours_start=9,
            active_hours_end=18,
            frequent_tasks=["python debug", "python test", "python script"]
        )
        storage.save_profile(profile)

        # Add workflow pattern
        workflow_pattern = InteractionPattern(
            profile_id="default",
            pattern_type="task_sequence",
            pattern_data={"sequence": ["test", "deploy", "monitor"]},
            occurrence_count=8
        )
        storage.save_interaction_pattern(workflow_pattern)

        # Add tool usage pattern
        tool_pattern = InteractionPattern(
            profile_id="default",
            pattern_type="tool_usage",
            pattern_data={"tool_name": "git status"},
            occurrence_count=15
        )
        storage.save_interaction_pattern(tool_pattern)

        # Generate at morning time
        morning_time = datetime(2026, 2, 2, 9, 0, 0)
        suggestions = engine.generate_all_suggestions("default", morning_time)

        # Should get suggestions from multiple types
        assert len(suggestions) > 0

        # Check that suggestions are from different types
        types = set(s.suggestion_type for s in suggestions)
        assert len(types) >= 2  # At least 2 different types

    def test_generate_all_suggestions_filtering_by_confidence(self, engine, storage):
        """Test that low-confidence suggestions are filtered out"""
        # Create engine with high confidence threshold
        high_conf_engine = SuggestionEngine(
            profile_storage=storage,
            min_confidence=0.9,
            max_suggestions=10
        )

        profile = UserProfile(id="default")
        storage.save_profile(profile)

        # Add pattern with low confidence (3 occurrences → confidence ~0.65)
        pattern = InteractionPattern(
            profile_id="default",
            pattern_type="task_sequence",
            pattern_data={"sequence": ["task1", "task2"]},
            occurrence_count=3
        )
        storage.save_interaction_pattern(pattern)

        suggestions = high_conf_engine.generate_all_suggestions("default")

        # Should be filtered out due to low confidence
        assert len(suggestions) == 0

    def test_generate_all_suggestions_priority_sorting(self, engine, storage):
        """Test that suggestions are sorted by priority then confidence"""
        profile = UserProfile(id="default")
        storage.save_profile(profile)

        # Create patterns with different priorities
        # High priority workflow (12 occurrences)
        high_priority_pattern = InteractionPattern(
            profile_id="default",
            pattern_type="task_sequence",
            pattern_data={"sequence": ["high", "priority", "workflow"]},
            occurrence_count=12
        )
        storage.save_interaction_pattern(high_priority_pattern)

        # Medium priority workflow (6 occurrences)
        medium_priority_pattern = InteractionPattern(
            profile_id="default",
            pattern_type="task_sequence",
            pattern_data={"sequence": ["medium", "priority", "workflow"]},
            occurrence_count=6
        )
        storage.save_interaction_pattern(medium_priority_pattern)

        suggestions = engine.generate_all_suggestions("default")

        # High priority should come first
        assert suggestions[0].priority == "high"
        assert suggestions[-1].priority in ["medium", "low"]

    def test_get_suggestion_by_type(self, engine, storage):
        """Test getting suggestions by specific type"""
        profile = UserProfile(
            id="default",
            active_hours_start=9,
            active_hours_end=18
        )
        storage.save_profile(profile)

        # Test each suggestion type
        workflow_suggs = engine.get_suggestion_by_type("workflow", "default")
        assert isinstance(workflow_suggs, list)

        tool_suggs = engine.get_suggestion_by_type("tool_shortcut", "default")
        assert isinstance(tool_suggs, list)

        time_suggs = engine.get_suggestion_by_type("time_based", "default")
        assert isinstance(time_suggs, list)

        skill_suggs = engine.get_suggestion_by_type("skill_recommendation", "default")
        assert isinstance(skill_suggs, list)

    def test_get_suggestion_by_unknown_type(self, engine, storage):
        """Test getting suggestions with unknown type"""
        suggestions = engine.get_suggestion_by_type("unknown_type", "default")

        assert suggestions == []

    def test_max_suggestions_limit(self, engine, storage):
        """Test that max_suggestions limit is respected"""
        profile = UserProfile(id="default")
        storage.save_profile(profile)

        # Create 10 tool usage patterns (more than max_suggestions=5)
        for i in range(10):
            pattern = InteractionPattern(
                profile_id="default",
                pattern_type="tool_usage",
                pattern_data={"tool_name": f"tool_{i}"},
                occurrence_count=10 + i
            )
            storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_tool_shortcuts("default")

        # Should respect max_suggestions limit
        assert len(suggestions) <= engine.max_suggestions
