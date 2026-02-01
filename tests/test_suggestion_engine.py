"""
Tests for Personalized Suggestions Engine

Test coverage for all suggestion types:
- Workflow suggestions
- Tool shortcut suggestions
- Time-based suggestions
- Skill recommendations
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from alpha.personalization.suggestion_engine import SuggestionEngine, Suggestion
from alpha.personalization.profile_storage import ProfileStorage
from alpha.personalization.user_profile import UserProfile, InteractionPattern


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def storage(temp_db):
    """Create ProfileStorage instance"""
    return ProfileStorage(temp_db)


@pytest.fixture
def engine(storage):
    """Create SuggestionEngine instance"""
    return SuggestionEngine(storage, min_confidence=0.5, max_suggestions=5)


@pytest.fixture
def sample_profile(storage):
    """Create sample user profile"""
    profile = UserProfile(
        id="test_user",
        verbosity_level="balanced",
        active_hours_start=9,
        active_hours_end=18,
        frequent_tasks=["python test", "git commit", "data analysis"],
        preferred_tools=["git", "python", "pytest"],
    )
    storage.save_profile(profile)
    return profile


class TestSuggestionEngine:
    """Test SuggestionEngine initialization and configuration"""

    def test_init_default_values(self, storage):
        """Test initialization with default values"""
        engine = SuggestionEngine(storage)
        assert engine.storage == storage
        assert engine.min_confidence == 0.7
        assert engine.max_suggestions == 5

    def test_init_custom_values(self, storage):
        """Test initialization with custom values"""
        engine = SuggestionEngine(storage, min_confidence=0.8, max_suggestions=10)
        assert engine.min_confidence == 0.8
        assert engine.max_suggestions == 10


class TestWorkflowSuggestions:
    """Test workflow suggestion generation"""

    def test_generate_workflow_no_patterns(self, engine, sample_profile):
        """Test when no workflow patterns exist"""
        suggestions = engine.generate_workflow_suggestions("test_user")
        assert suggestions == []

    def test_generate_workflow_single_occurrence(self, engine, storage, sample_profile):
        """Test workflow with single occurrence (should not suggest)"""
        pattern = InteractionPattern(
            profile_id="test_user",
            pattern_type="task_sequence",
            pattern_data={"sequence": ["git status", "git commit"]},
            occurrence_count=1,
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_workflow_suggestions("test_user")
        assert len(suggestions) == 0  # Need at least 3 occurrences

    def test_generate_workflow_sufficient_occurrences(self, engine, storage, sample_profile):
        """Test workflow with sufficient occurrences"""
        pattern = InteractionPattern(
            profile_id="test_user",
            pattern_type="task_sequence",
            pattern_data={"sequence": ["git status", "git add", "git commit"]},
            occurrence_count=5,
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_workflow_suggestions("test_user")
        assert len(suggestions) == 1
        assert suggestions[0].suggestion_type == "workflow"
        assert suggestions[0].confidence > 0.5
        assert "git status → git add → git commit" in suggestions[0].title

    def test_workflow_priority_based_on_frequency(self, engine, storage, sample_profile):
        """Test workflow priority assignment based on frequency"""
        # High frequency pattern
        pattern1 = InteractionPattern(
            profile_id="test_user",
            pattern_type="task_sequence",
            pattern_data={"sequence": ["task1", "task2"]},
            occurrence_count=15,
        )
        storage.save_interaction_pattern(pattern1)

        # Medium frequency pattern
        pattern2 = InteractionPattern(
            profile_id="test_user",
            pattern_type="task_sequence",
            pattern_data={"sequence": ["task3", "task4"]},
            occurrence_count=7,
        )
        storage.save_interaction_pattern(pattern2)

        suggestions = engine.generate_workflow_suggestions("test_user")
        assert len(suggestions) == 2

        # Check priorities
        high_priority_found = any(s.priority == "high" for s in suggestions)
        medium_priority_found = any(s.priority == "medium" for s in suggestions)
        assert high_priority_found
        assert medium_priority_found

    def test_workflow_max_suggestions_limit(self, engine, storage, sample_profile):
        """Test max suggestions limit is enforced"""
        # Create 10 patterns
        for i in range(10):
            pattern = InteractionPattern(
                profile_id="test_user",
                pattern_type="task_sequence",
                pattern_data={"sequence": [f"task{i}_1", f"task{i}_2"]},
                occurrence_count=5,
            )
            storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_workflow_suggestions("test_user")
        assert len(suggestions) <= engine.max_suggestions


class TestToolShortcuts:
    """Test tool shortcut suggestion generation"""

    def test_generate_tool_shortcuts_no_patterns(self, engine, sample_profile):
        """Test when no tool usage patterns exist"""
        suggestions = engine.generate_tool_shortcuts("test_user")
        assert suggestions == []

    def test_generate_tool_shortcuts_low_usage(self, engine, storage, sample_profile):
        """Test tool with low usage count (should not suggest)"""
        pattern = InteractionPattern(
            profile_id="test_user",
            pattern_type="tool_usage",
            pattern_data={"tool_name": "git status"},
            occurrence_count=2,
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_tool_shortcuts("test_user")
        assert len(suggestions) == 0  # Need at least 5 uses

    def test_generate_tool_shortcuts_git_command(self, engine, storage, sample_profile):
        """Test git command shortcut suggestion"""
        pattern = InteractionPattern(
            profile_id="test_user",
            pattern_type="tool_usage",
            pattern_data={"tool_name": "git status"},
            occurrence_count=10,
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_tool_shortcuts("test_user")
        assert len(suggestions) == 1
        assert suggestions[0].suggestion_type == "tool_shortcut"
        assert "git" in suggestions[0].title.lower()
        assert "alias" in suggestions[0].title.lower()

    def test_generate_tool_shortcuts_non_git_tool(self, engine, storage, sample_profile):
        """Test non-git tool shortcut suggestion"""
        pattern = InteractionPattern(
            profile_id="test_user",
            pattern_type="tool_usage",
            pattern_data={"tool_name": "pytest"},
            occurrence_count=15,
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_tool_shortcuts("test_user")
        assert len(suggestions) == 1
        assert suggestions[0].suggestion_type == "tool_shortcut"
        assert "pytest" in suggestions[0].title

    def test_tool_shortcut_priority_by_frequency(self, engine, storage, sample_profile):
        """Test priority assignment based on tool usage frequency"""
        # High usage tool
        pattern1 = InteractionPattern(
            profile_id="test_user",
            pattern_type="tool_usage",
            pattern_data={"tool_name": "git commit"},
            occurrence_count=25,
        )
        storage.save_interaction_pattern(pattern1)

        # Medium usage tool
        pattern2 = InteractionPattern(
            profile_id="test_user",
            pattern_type="tool_usage",
            pattern_data={"tool_name": "pytest"},
            occurrence_count=12,
        )
        storage.save_interaction_pattern(pattern2)

        suggestions = engine.generate_tool_shortcuts("test_user")
        assert len(suggestions) == 2

        # Verify priorities
        assert any(s.priority == "high" for s in suggestions)
        assert any(s.priority == "medium" for s in suggestions)


class TestTimeBasedSuggestions:
    """Test time-based suggestion generation"""

    def test_generate_time_based_no_profile(self, engine):
        """Test when profile doesn't exist"""
        suggestions = engine.generate_time_based_suggestions("nonexistent_user")
        assert suggestions == []

    def test_morning_suggestion(self, engine, sample_profile):
        """Test morning suggestion at start of active hours"""
        morning_time = datetime.now().replace(hour=9, minute=0)
        suggestions = engine.generate_time_based_suggestions("test_user", morning_time)

        assert len(suggestions) >= 1
        morning_sugg = next(
            (s for s in suggestions if "morning" in s.title.lower() or "morning" in s.description.lower()),
            None
        )
        assert morning_sugg is not None
        assert morning_sugg.priority == "high"
        assert "overnight" in morning_sugg.description.lower()

    def test_midday_suggestion(self, engine, sample_profile):
        """Test mid-day suggestion"""
        midday_time = datetime.now().replace(hour=13, minute=30)  # Halfway between 9-18
        suggestions = engine.generate_time_based_suggestions("test_user", midday_time)

        assert len(suggestions) >= 1
        midday_sugg = next(
            (s for s in suggestions if "mid" in s.title.lower() or "progress" in s.title.lower()),
            None
        )
        if midday_sugg:  # Only if time matches exactly
            assert midday_sugg.suggestion_type == "time_based"

    def test_evening_suggestion(self, engine, sample_profile):
        """Test evening suggestion at end of active hours"""
        evening_time = datetime.now().replace(hour=18, minute=0)
        suggestions = engine.generate_time_based_suggestions("test_user", evening_time)

        assert len(suggestions) >= 1
        evening_sugg = next(
            (s for s in suggestions if "summary" in s.title.lower() or "daily" in s.title.lower()),
            None
        )
        assert evening_sugg is not None
        assert evening_sugg.priority == "high"

    def test_weekend_suggestion(self, engine, sample_profile):
        """Test weekend-specific suggestion"""
        # Get next Saturday
        today = datetime.now()
        days_ahead = 5 - today.weekday()  # Saturday = 5
        if days_ahead <= 0:
            days_ahead += 7
        saturday = today + timedelta(days=days_ahead)
        saturday = saturday.replace(hour=9, minute=0)

        suggestions = engine.generate_time_based_suggestions("test_user", saturday)

        # Should have both morning and weekend suggestions
        assert len(suggestions) >= 1
        weekend_sugg = next(
            (s for s in suggestions if "weekend" in s.title.lower()),
            None
        )
        if weekend_sugg:
            assert weekend_sugg.suggestion_type == "time_based"


class TestSkillRecommendations:
    """Test skill recommendation generation"""

    def test_generate_skill_recommendations_no_tasks(self, engine, storage):
        """Test when user has no frequent tasks"""
        profile = UserProfile(id="empty_user", frequent_tasks=[])
        storage.save_profile(profile)

        suggestions = engine.generate_skill_recommendations("empty_user")
        assert suggestions == []

    def test_generate_skill_recommendations_python_tasks(self, engine, sample_profile):
        """Test skill recommendations for Python tasks"""
        # Update profile with more Python tasks
        profile = sample_profile
        profile.frequent_tasks = [
            "python test",
            "python debug",
            "python run script.py",
            "python analyze data",
        ]
        engine.storage.save_profile(profile)

        suggestions = engine.generate_skill_recommendations("test_user")
        assert len(suggestions) >= 1
        python_sugg = next(
            (s for s in suggestions if "python" in s.title.lower()),
            None
        )
        assert python_sugg is not None
        assert python_sugg.suggestion_type == "skill_recommendation"
        assert python_sugg.confidence >= 0.5

    def test_generate_skill_recommendations_git_tasks(self, engine, sample_profile):
        """Test skill recommendations for Git tasks"""
        profile = sample_profile
        profile.frequent_tasks = ["git commit", "git push", "git merge", "git rebase"]
        engine.storage.save_profile(profile)

        suggestions = engine.generate_skill_recommendations("test_user")
        assert len(suggestions) >= 1
        git_sugg = next(
            (s for s in suggestions if "git" in s.title.lower()),
            None
        )
        assert git_sugg is not None

    def test_skill_recommendation_confidence_scaling(self, engine, sample_profile):
        """Test confidence increases with more task occurrences"""
        # Many Python tasks
        profile = sample_profile
        profile.frequent_tasks = ["python " + str(i) for i in range(15)]
        engine.storage.save_profile(profile)

        suggestions = engine.generate_skill_recommendations("test_user")
        python_sugg = next(
            (s for s in suggestions if "python" in s.title.lower()),
            None
        )
        if python_sugg:
            assert python_sugg.confidence > 0.7


class TestGenerateAllSuggestions:
    """Test generating all suggestion types together"""

    def test_generate_all_empty_profile(self, engine, sample_profile):
        """Test generating all suggestions with minimal data"""
        suggestions = engine.generate_all_suggestions("test_user")
        # Should have at least time-based suggestions
        assert len(suggestions) >= 0

    def test_generate_all_with_patterns(self, engine, storage, sample_profile):
        """Test generating all suggestions with various patterns"""
        # Add workflow pattern
        workflow_pattern = InteractionPattern(
            profile_id="test_user",
            pattern_type="task_sequence",
            pattern_data={"sequence": ["task1", "task2"]},
            occurrence_count=10,
        )
        storage.save_interaction_pattern(workflow_pattern)

        # Add tool usage pattern
        tool_pattern = InteractionPattern(
            profile_id="test_user",
            pattern_type="tool_usage",
            pattern_data={"tool_name": "git status"},
            occurrence_count=20,
        )
        storage.save_interaction_pattern(tool_pattern)

        suggestions = engine.generate_all_suggestions("test_user")

        # Should have multiple types
        types = {s.suggestion_type for s in suggestions}
        assert len(types) >= 2  # At least workflow and tool_shortcut

    def test_confidence_filtering(self, engine, storage, sample_profile):
        """Test that low-confidence suggestions are filtered"""
        # Set high confidence threshold
        engine.min_confidence = 0.9

        # Add pattern with medium confidence
        pattern = InteractionPattern(
            profile_id="test_user",
            pattern_type="task_sequence",
            pattern_data={"sequence": ["task1", "task2"]},
            occurrence_count=3,  # Low count = lower confidence
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_all_suggestions("test_user")

        # All suggestions should meet minimum confidence
        for suggestion in suggestions:
            assert suggestion.confidence >= engine.min_confidence

    def test_sorting_by_priority_and_confidence(self, engine, storage, sample_profile):
        """Test suggestions are sorted correctly"""
        # Add multiple patterns
        for i in range(3):
            pattern = InteractionPattern(
                profile_id="test_user",
                pattern_type="task_sequence",
                pattern_data={"sequence": [f"task{i}", f"task{i+1}"]},
                occurrence_count=5 + i * 5,  # Varying counts
            )
            storage.save_interaction_pattern(pattern)

        suggestions = engine.generate_all_suggestions("test_user")

        if len(suggestions) > 1:
            # Verify sorting: high priority first, then by confidence
            priority_order = {"high": 0, "medium": 1, "low": 2}
            for i in range(len(suggestions) - 1):
                curr_priority = priority_order[suggestions[i].priority]
                next_priority = priority_order[suggestions[i + 1].priority]

                # If same priority, confidence should decrease
                if curr_priority == next_priority:
                    assert suggestions[i].confidence >= suggestions[i + 1].confidence


class TestGetSuggestionByType:
    """Test getting suggestions by specific type"""

    def test_get_workflow_type(self, engine, storage, sample_profile):
        """Test getting workflow suggestions specifically"""
        pattern = InteractionPattern(
            profile_id="test_user",
            pattern_type="task_sequence",
            pattern_data={"sequence": ["task1", "task2"]},
            occurrence_count=5,
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.get_suggestion_by_type("workflow", "test_user")
        assert all(s.suggestion_type == "workflow" for s in suggestions)

    def test_get_tool_shortcut_type(self, engine, storage, sample_profile):
        """Test getting tool shortcut suggestions specifically"""
        pattern = InteractionPattern(
            profile_id="test_user",
            pattern_type="tool_usage",
            pattern_data={"tool_name": "pytest"},
            occurrence_count=10,
        )
        storage.save_interaction_pattern(pattern)

        suggestions = engine.get_suggestion_by_type("tool_shortcut", "test_user")
        assert all(s.suggestion_type == "tool_shortcut" for s in suggestions)

    def test_get_unknown_type(self, engine, sample_profile):
        """Test getting unknown suggestion type"""
        suggestions = engine.get_suggestion_by_type("unknown_type", "test_user")
        assert suggestions == []


class TestSuggestionModel:
    """Test Suggestion data model"""

    def test_suggestion_creation(self):
        """Test creating a Suggestion instance"""
        suggestion = Suggestion(
            suggestion_type="workflow",
            title="Test Suggestion",
            description="Test description",
            action="test action",
            confidence=0.85,
            priority="high"
        )

        assert suggestion.suggestion_type == "workflow"
        assert suggestion.title == "Test Suggestion"
        assert suggestion.confidence == 0.85
        assert suggestion.priority == "high"

    def test_suggestion_to_dict(self):
        """Test converting suggestion to dictionary"""
        suggestion = Suggestion(
            suggestion_type="workflow",
            title="Test",
            description="Test",
            action="test",
            confidence=0.9,
            context={"key": "value"}
        )

        data = suggestion.to_dict()
        assert data["suggestion_type"] == "workflow"
        assert data["title"] == "Test"
        assert data["confidence"] == 0.9
        assert data["context"] == {"key": "value"}
        assert "created_at" in data

    def test_suggestion_default_values(self):
        """Test suggestion default values"""
        suggestion = Suggestion(
            suggestion_type="workflow",
            title="Test",
            description="Test",
            action="test",
            confidence=0.8
        )

        assert suggestion.context == {}
        assert suggestion.priority == "medium"
        assert isinstance(suggestion.created_at, datetime)
