"""
Tests for WorkflowPatternDetector
"""

import pytest
from datetime import datetime, timedelta
from alpha.workflow.pattern_detector import (
    WorkflowPattern,
    WorkflowPatternDetector
)


class TestWorkflowPattern:
    """Tests for WorkflowPattern dataclass"""

    def test_create_pattern(self):
        """Test creating a WorkflowPattern instance"""
        now = datetime.now()
        pattern = WorkflowPattern(
            pattern_id="test_001",
            task_sequence=["task 1", "task 2"],
            frequency=5,
            confidence=0.85,
            first_seen=now - timedelta(days=10),
            last_seen=now,
            avg_interval=timedelta(days=2),
            task_ids=["id1", "id2", "id3"],
            suggested_workflow_name="Test Workflow"
        )

        assert pattern.pattern_id == "test_001"
        assert len(pattern.task_sequence) == 2
        assert pattern.frequency == 5
        assert pattern.confidence == 0.85

    def test_pattern_to_dict(self):
        """Test converting pattern to dictionary"""
        now = datetime.now()
        pattern = WorkflowPattern(
            pattern_id="test_002",
            task_sequence=["deploy", "test"],
            frequency=3,
            confidence=0.9,
            first_seen=now,
            last_seen=now,
            avg_interval=timedelta(hours=24),
            task_ids=["t1", "t2"],
            suggested_workflow_name="Deploy Workflow"
        )

        result = pattern.to_dict()
        assert result["pattern_id"] == "test_002"
        assert result["frequency"] == 3
        assert result["confidence"] == 0.9
        assert "first_seen" in result
        assert "avg_interval" in result


class TestNormalization:
    """Tests for task description normalization"""

    def test_normalize_dates(self):
        """Test date normalization"""
        detector = WorkflowPatternDetector()

        # ISO format date
        result = detector.normalize_task_description("Deploy on 2026-01-15")
        assert "DATETOKEN" in result
        assert "2026-01-15" not in result

        # Slash format date
        result = detector.normalize_task_description("Meeting on 1/15/2026")
        assert "DATETOKEN" in result
        assert "1/15/2026" not in result

    def test_normalize_times(self):
        """Test time normalization"""
        detector = WorkflowPatternDetector()

        result = detector.normalize_task_description("Backup at 23:45")
        assert "TIMETOKEN" in result
        assert "23:45" not in result

        result = detector.normalize_task_description("Call at 3:30 PM")
        assert "TIMETOKEN" in result

    def test_normalize_numbers(self):
        """Test number normalization"""
        detector = WorkflowPatternDetector()

        result = detector.normalize_task_description("Process 123 items")
        assert "NUMTOKEN" in result
        assert "123" not in result

    def test_normalize_branches(self):
        """Test git branch normalization"""
        detector = WorkflowPatternDetector()

        result = detector.normalize_task_description("Deploy feature/new-auth")
        assert "BRANCHTOKEN" in result
        assert "feature/new-auth" not in result

        result = detector.normalize_task_description("Merge bugfix/login-issue")
        assert "BRANCHTOKEN" in result

    def test_normalize_paths(self):
        """Test file path normalization"""
        detector = WorkflowPatternDetector()

        # Unix path
        result = detector.normalize_task_description("Backup /home/user/data")
        assert "PATHTOKEN" in result
        assert "/home/user/data" not in result

        # Windows path
        result = detector.normalize_task_description("Copy C:\\Users\\data")
        assert "PATHTOKEN" in result

    def test_normalize_empty(self):
        """Test normalizing empty string"""
        detector = WorkflowPatternDetector()
        result = detector.normalize_task_description("")
        assert result == ""

    def test_normalize_lowercase(self):
        """Test lowercase conversion"""
        detector = WorkflowPatternDetector()
        result = detector.normalize_task_description("Deploy to STAGING")
        assert "staging" in result
        assert "STAGING" not in result  # Should be lowercase except tokens


class TestConfidenceCalculation:
    """Tests for confidence scoring"""

    def test_high_confidence_pattern(self):
        """Test high-confidence pattern (high frequency, regular intervals)"""
        detector = WorkflowPatternDetector()

        confidence = detector.calculate_pattern_confidence(
            frequency=10,  # High frequency
            sequence_length=4,  # Good length
            avg_interval=timedelta(days=1),  # Very regular (daily)
            success_rate=1.0  # Perfect success
        )

        assert confidence >= 0.8  # Should be high confidence

    def test_low_confidence_pattern(self):
        """Test low-confidence pattern (low frequency, irregular)"""
        detector = WorkflowPatternDetector()

        confidence = detector.calculate_pattern_confidence(
            frequency=2,  # Low frequency
            sequence_length=2,  # Short sequence
            avg_interval=timedelta(days=25),  # Irregular
            success_rate=0.5  # Mediocre success
        )

        assert confidence < 0.6  # Should be low confidence

    def test_confidence_bounds(self):
        """Test confidence is between 0 and 1"""
        detector = WorkflowPatternDetector()

        # Extreme high values
        confidence = detector.calculate_pattern_confidence(
            frequency=100,
            sequence_length=10,
            avg_interval=timedelta(hours=1),
            success_rate=1.0
        )
        assert 0.0 <= confidence <= 1.0

        # Extreme low values
        confidence = detector.calculate_pattern_confidence(
            frequency=1,
            sequence_length=1,
            avg_interval=timedelta(days=100),
            success_rate=0.0
        )
        assert 0.0 <= confidence <= 1.0


class TestWorkflowNameGeneration:
    """Tests for workflow name generation"""

    def test_generate_name_from_sequence(self):
        """Test generating workflow name from task sequence"""
        detector = WorkflowPatternDetector()

        sequence = ("deploy to BRANCHTOKEN", "run tests", "check coverage")
        name = detector._generate_workflow_name(sequence)

        assert len(name) > 0
        assert "Workflow" in name

    def test_generate_name_empty_sequence(self):
        """Test generating name from empty sequence"""
        detector = WorkflowPatternDetector()

        name = detector._generate_workflow_name(())
        assert name == "Untitled Workflow"

    def test_generate_name_with_tokens(self):
        """Test name generation removes tokens"""
        detector = WorkflowPatternDetector()

        sequence = ("backup PATHTOKEN", "sync to cloud")
        name = detector._generate_workflow_name(sequence)

        assert "PATHTOKEN" not in name
        assert "DATETOKEN" not in name


class TestPatternDetection:
    """Tests for pattern detection logic"""

    def test_detect_no_patterns_empty_history(self):
        """Test detecting patterns with empty task history"""
        detector = WorkflowPatternDetector(memory_store=None)
        patterns = detector.detect_workflow_patterns()

        assert patterns == []

    def test_temporal_proximity_check_pass(self):
        """Test temporal proximity check passes for close tasks"""
        detector = WorkflowPatternDetector()

        now = datetime.now()
        window = [
            ({"created_at": now.isoformat()}, "task 1"),
            ({"created_at": (now + timedelta(hours=2)).isoformat()}, "task 2"),
        ]

        result = detector._check_temporal_proximity(window, max_interval_days=7)
        assert result is True

    def test_temporal_proximity_check_fail(self):
        """Test temporal proximity check fails for distant tasks"""
        detector = WorkflowPatternDetector()

        now = datetime.now()
        window = [
            ({"created_at": now.isoformat()}, "task 1"),
            ({"created_at": (now + timedelta(days=10)).isoformat()}, "task 2"),
        ]

        result = detector._check_temporal_proximity(window, max_interval_days=7)
        assert result is False

    def test_temporal_proximity_single_task(self):
        """Test temporal proximity with single task"""
        detector = WorkflowPatternDetector()

        window = [({"created_at": datetime.now().isoformat()}, "task 1")]
        result = detector._check_temporal_proximity(window, max_interval_days=7)

        assert result is True  # Single task always passes


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_pattern_detector_initialization(self):
        """Test initializing pattern detector with custom parameters"""
        detector = WorkflowPatternDetector(
            memory_store=None,
            min_frequency=5,
            min_confidence=0.8,
            lookback_days=60
        )

        assert detector.min_frequency == 5
        assert detector.min_confidence == 0.8
        assert detector.lookback_days == 60

    def test_normalize_special_characters(self):
        """Test normalizing tasks with special characters"""
        detector = WorkflowPatternDetector()

        result = detector.normalize_task_description("Deploy (prod) @main #urgent")
        assert len(result) > 0  # Should handle special chars without error

    def test_create_pattern_no_occurrences(self):
        """Test creating pattern with no occurrences"""
        detector = WorkflowPatternDetector()

        result = detector._create_pattern_from_sequence(
            sequence=("task1", "task2"),
            occurrences=[]
        )

        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
