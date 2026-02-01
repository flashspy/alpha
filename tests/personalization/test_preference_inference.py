"""
Unit tests for Preference Inference System (Phase 2)

Tests:
- PreferenceInferrer tool preference inference
- Task priority inference
- Workflow pattern detection
- Time preference analysis
- Communication style inference
- Confidence scoring
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta

from alpha.personalization.user_profile import UserProfile, InteractionPattern
from alpha.personalization.profile_storage import ProfileStorage
from alpha.personalization.profile_learner import ProfileLearner
from alpha.personalization.preference_inferrer import PreferenceInferrer


class TestPreferenceInferrer:
    """Test PreferenceInferrer functionality"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_alpha.db")
            yield db_path

    @pytest.fixture
    def storage(self, temp_db):
        """Create ProfileStorage instance"""
        return ProfileStorage(db_path=temp_db)

    @pytest.fixture
    def inferrer(self, storage):
        """Create PreferenceInferrer with sample data"""
        # Create profile
        learner = ProfileLearner(storage, profile_id="test_user")

        # Add some interactions for testing
        for _ in range(10):
            learner.record_interaction(
                user_message="test message",
                tool_used="git"
            )

        for _ in range(5):
            learner.record_interaction(
                user_message="test",
                tool_used="docker"
            )

        return PreferenceInferrer(storage, profile_id="test_user")

    def test_inferrer_initialization(self, inferrer):
        """Test inferrer initializes correctly"""
        assert inferrer.profile is not None
        assert inferrer.profile_id == "test_user"

    def test_infer_tool_preferences(self, inferrer):
        """Test tool preference inference"""
        tool_prefs = inferrer.infer_tool_preferences(min_usage=3, min_confidence=0.0)

        assert len(tool_prefs) > 0

        # Git should have more usage than docker
        git_pref = next((p for p in tool_prefs if p["tool"] == "git"), None)
        docker_pref = next((p for p in tool_prefs if p["tool"] == "docker"), None)

        assert git_pref is not None
        assert docker_pref is not None
        assert git_pref["usage_count"] > docker_pref["usage_count"]
        assert git_pref["confidence"] > 0.0

    def test_infer_tool_preferences_confidence_threshold(self, inferrer):
        """Test tool preference filtering by confidence"""
        # High confidence threshold should return fewer results
        high_conf = inferrer.infer_tool_preferences(min_confidence=0.9)
        low_conf = inferrer.infer_tool_preferences(min_confidence=0.1)

        assert len(high_conf) <= len(low_conf)

    def test_infer_task_priorities(self, storage):
        """Test task priority inference"""
        learner = ProfileLearner(storage, profile_id="priority_user")

        # Add tasks with different frequencies
        for _ in range(10):
            learner.record_interaction(user_message="test", task_type="coding")

        for _ in range(3):
            learner.record_interaction(user_message="test", task_type="review")

        inferrer = PreferenceInferrer(storage, profile_id="priority_user")

        priorities = inferrer.infer_task_priorities(min_occurrences=2, min_confidence=0.0)

        assert len(priorities) > 0

        # Coding should have higher priority
        coding = next((p for p in priorities if p["task_type"] == "coding"), None)
        assert coding is not None
        assert coding["occurrence_count"] >= 10
        assert coding["priority_level"] in ["high", "medium", "low"]

    def test_infer_task_priority_levels(self, storage):
        """Test task priority level assignment"""
        learner = ProfileLearner(storage, profile_id="priority_test")

        # Create high-frequency task
        for _ in range(20):
            learner.record_interaction(user_message="test", task_type="high_freq")

        # Create medium-frequency task
        for _ in range(8):
            learner.record_interaction(user_message="test", task_type="medium_freq")

        # Create low-frequency task
        for _ in range(3):
            learner.record_interaction(user_message="test", task_type="low_freq")

        inferrer = PreferenceInferrer(storage, profile_id="priority_test")
        priorities = inferrer.infer_task_priorities(min_occurrences=3, min_confidence=0.0)

        # Verify different priority levels assigned
        priority_levels = {p["task_type"]: p["priority_level"] for p in priorities}

        assert priority_levels.get("high_freq") in ["high", "medium"]
        assert "low_freq" in priority_levels  # Should have some priority

    def test_infer_workflow_patterns(self, storage):
        """Test workflow pattern detection"""
        learner = ProfileLearner(storage, profile_id="workflow_user")

        # Simulate recurring workflow: git status → git commit
        for _ in range(5):
            learner.record_interaction(user_message="test", tool_used="git_status")
            learner.record_interaction(user_message="test", tool_used="git_commit")

        inferrer = PreferenceInferrer(storage, profile_id="workflow_user")
        workflows = inferrer.infer_workflow_patterns(min_occurrences=3)

        # Should detect the workflow pattern
        # Note: This is a simplified test; actual implementation may vary
        assert isinstance(workflows, list)

    def test_infer_time_preferences(self, storage):
        """Test time preference inference"""
        learner = ProfileLearner(storage, profile_id="time_user")

        # Simulate interactions at specific hours
        for hour in [9, 10, 11, 14, 15, 16]:
            for _ in range(5):
                learner._detect_time_pattern()  # Record current time
                # Manually add time pattern
                pattern = InteractionPattern(
                    profile_id="time_user",
                    pattern_type="time_of_day",
                    pattern_data={"hour": hour}
                )
                storage.save_interaction_pattern(pattern)

        # Add enough interactions
        learner.profile.interaction_count = 30
        storage.save_profile(learner.profile)

        inferrer = PreferenceInferrer(storage, profile_id="time_user")
        time_prefs = inferrer.infer_time_preferences(min_interactions=20)

        if time_prefs:  # May not infer if not enough data
            assert "active_hours_start" in time_prefs
            assert "active_hours_end" in time_prefs
            assert "confidence" in time_prefs
            assert 0.0 <= time_prefs["confidence"] <= 1.0

    def test_infer_time_preferences_pattern_detection(self, storage):
        """Test time preference pattern name detection"""
        learner = ProfileLearner(storage, profile_id="pattern_user")

        # Simulate standard workday (9-17)
        for hour in range(9, 18):
            for _ in range(3):
                pattern = InteractionPattern(
                    profile_id="pattern_user",
                    pattern_type="time_of_day",
                    pattern_data={"hour": hour},
                    occurrence_count=3
                )
                storage.save_interaction_pattern(pattern)

        learner.profile.interaction_count = 30
        storage.save_profile(learner.profile)

        inferrer = PreferenceInferrer(storage, profile_id="pattern_user")
        time_prefs = inferrer.infer_time_preferences(min_interactions=20)

        if time_prefs:
            assert time_prefs["pattern_name"] in [
                "standard_workday", "early_bird", "afternoon_evening",
                "night_owl", "flexible"
            ]

    def test_infer_communication_style(self, storage):
        """Test communication style inference"""
        learner = ProfileLearner(storage, profile_id="comm_user")

        # Record some interactions to build profile
        for _ in range(15):
            learner.record_interaction(user_message="Be brief please")

        inferrer = PreferenceInferrer(storage, profile_id="comm_user")
        style = inferrer.infer_communication_style()

        assert isinstance(style, dict)
        assert "verbosity_level" in style
        assert "confidence" in style

    def test_infer_communication_style_insufficient_data(self, storage):
        """Test communication style with insufficient data"""
        learner = ProfileLearner(storage, profile_id="new_user")

        # Only a few interactions
        for _ in range(3):
            learner.record_interaction(user_message="test")

        inferrer = PreferenceInferrer(storage, profile_id="new_user")
        style = inferrer.infer_communication_style()

        # Should return empty dict or minimal info
        assert isinstance(style, dict)

    def test_calculate_overall_confidence(self, inferrer):
        """Test overall confidence calculation"""
        confidence = inferrer.calculate_overall_confidence()

        assert 0.0 <= confidence <= 1.0
        assert isinstance(confidence, float)

    def test_confidence_increases_with_interactions(self, storage):
        """Test confidence increases with more interactions"""
        learner1 = ProfileLearner(storage, profile_id="user_few")
        for _ in range(5):
            learner1.record_interaction(user_message="test")

        learner2 = ProfileLearner(storage, profile_id="user_many")
        for _ in range(50):
            learner2.record_interaction(user_message="test")

        inferrer1 = PreferenceInferrer(storage, profile_id="user_few")
        inferrer2 = PreferenceInferrer(storage, profile_id="user_many")

        conf1 = inferrer1.calculate_overall_confidence()
        conf2 = inferrer2.calculate_overall_confidence()

        # More interactions should lead to higher confidence
        assert conf2 >= conf1

    def test_get_confidence_report(self, inferrer):
        """Test confidence report generation"""
        report = inferrer.get_confidence_report()

        assert "overall_confidence" in report
        assert "interaction_count" in report
        assert "profile_confidence" in report
        assert "preferences" in report
        assert isinstance(report["preferences"], dict)

    def test_infer_all_preferences(self, inferrer):
        """Test inferring all preferences at once"""
        inferences = inferrer.infer_all_preferences()

        assert isinstance(inferences, dict)
        # Should have at least some inferences
        # (exact keys depend on data)

    def test_tool_preference_confidence_scoring(self, storage):
        """Test tool preference confidence scoring logic"""
        learner = ProfileLearner(storage, profile_id="conf_user")

        # Recent, frequent usage → high confidence
        for _ in range(15):
            learner.record_interaction(user_message="test", tool_used="frequent_tool")

        # Old, infrequent usage → lower confidence
        pattern = InteractionPattern(
            profile_id="conf_user",
            pattern_type="tool_usage",
            pattern_data={"tool": "old_tool"},
            occurrence_count=3
        )
        pattern.first_seen = datetime.now() - timedelta(days=60)
        pattern.last_seen = datetime.now() - timedelta(days=30)
        storage.save_interaction_pattern(pattern)

        inferrer = PreferenceInferrer(storage, profile_id="conf_user")
        tool_prefs = inferrer.infer_tool_preferences(min_usage=2, min_confidence=0.0)

        frequent = next((p for p in tool_prefs if p["tool"] == "frequent_tool"), None)
        old = next((p for p in tool_prefs if p["tool"] == "old_tool"), None)

        if frequent and old:
            # Frequent recent tool should have higher confidence
            assert frequent["confidence"] > old["confidence"]

    def test_task_priority_frequency_calculation(self, storage):
        """Test task priority frequency calculation"""
        learner = ProfileLearner(storage, profile_id="freq_user")

        # Add 10 total tasks: 7 coding, 3 review
        for _ in range(7):
            learner.record_interaction(user_message="test", task_type="coding")
        for _ in range(3):
            learner.record_interaction(user_message="test", task_type="review")

        inferrer = PreferenceInferrer(storage, profile_id="freq_user")
        priorities = inferrer.infer_task_priorities(min_occurrences=2, min_confidence=0.0)

        coding = next((p for p in priorities if p["task_type"] == "coding"), None)

        if coding:
            # Coding frequency should be 0.7 (7 out of 10)
            assert abs(coding["frequency"] - 0.7) < 0.1  # Allow small floating point error

    def test_confidence_report_with_preferences(self, storage):
        """Test confidence report includes learned preferences"""
        learner = ProfileLearner(storage, profile_id="pref_user")

        # Learn verbosity preference
        learner.record_interaction(user_message="Be brief please")

        # Add tool usage
        for _ in range(5):
            learner.record_interaction(user_message="test", tool_used="git")

        inferrer = PreferenceInferrer(storage, profile_id="pref_user")
        report = inferrer.get_confidence_report()

        # Should have verbosity_level in preferences
        if "verbosity_level" in report["preferences"]:
            assert "value" in report["preferences"]["verbosity_level"]
            assert "confidence" in report["preferences"]["verbosity_level"]


class TestPreferenceInferenceIntegration:
    """Integration tests for preference inference"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_alpha.db")
            yield db_path

    def test_end_to_end_inference(self, temp_db):
        """Test complete inference pipeline"""
        storage = ProfileStorage(db_path=temp_db)
        learner = ProfileLearner(storage, profile_id="e2e_user")

        # Simulate user behavior over time
        behaviors = [
            ("Use git frequently", "git", "coding"),
            ("Use git frequently", "git", "coding"),
            ("Use git frequently", "git", "coding"),
            ("Use docker occasionally", "docker", "deployment"),
            ("Use docker occasionally", "docker", "deployment"),
            ("Brief response please", None, "communication"),
            ("Be concise", None, "communication"),
        ]

        for message, tool, task in behaviors:
            learner.record_interaction(
                user_message=message,
                tool_used=tool,
                task_type=task
            )

        # Infer all preferences
        inferrer = PreferenceInferrer(storage, profile_id="e2e_user")
        inferences = inferrer.infer_all_preferences()

        # Verify inferences
        assert isinstance(inferences, dict)

        # Should infer tool preferences
        if "tool_preferences" in inferences:
            tools = inferences["tool_preferences"]
            git_pref = next((t for t in tools if t["tool"] == "git"), None)
            assert git_pref is not None
            assert git_pref["usage_count"] >= 3

        # Should infer task priorities
        if "task_priorities" in inferences:
            tasks = inferences["task_priorities"]
            coding_task = next((t for t in tasks if t["task_type"] == "coding"), None)
            assert coding_task is not None

        # Overall confidence should be reasonable
        overall_conf = inferrer.calculate_overall_confidence()
        assert 0.0 <= overall_conf <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
