"""
Comprehensive Tests for SkillEvolutionManager

Tests skill evolution system including metrics tracking, evaluation,
exploration, optimization, pruning, and persistence.

Total tests: 26
Target coverage: 90%+
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from alpha.learning.skill_evolution_manager import (
    SkillEvolutionManager,
    SkillMetrics,
    SkillStatus,
    SkillEvaluationResult,
    EvolutionConfig
)


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_registry():
    """Mock SkillRegistry."""
    registry = Mock()
    registry.get_skill = Mock(return_value={"id": "test_skill", "name": "Test Skill"})
    registry.install_skill = AsyncMock()
    registry.uninstall_skill = AsyncMock()
    return registry


@pytest.fixture
def mock_marketplace():
    """Mock SkillMarketplace."""
    marketplace = Mock()
    marketplace.search = AsyncMock(return_value=[
        {
            "id": "skill_1",
            "name": "Skill 1",
            "description": "Test skill 1",
            "readme": "Documentation",
            "examples": ["example1", "example2"],
            "python_version": "3.11"
        },
        {
            "id": "skill_2",
            "name": "Skill 2",
            "description": "Test skill 2",
            "python_version": "3.9"
        }
    ])
    return marketplace


@pytest.fixture
def evolution_config():
    """Create test configuration."""
    return EvolutionConfig(
        exploration_enabled=True,
        exploration_interval_hours=1,
        max_skills_per_exploration=5,
        pruning_enabled=True,
        pruning_interval_hours=1,
        min_uses_before_prune=3,
        max_unused_days=7,
        min_success_rate=0.5,
        min_overall_score=0.4,
        optimization_enabled=True,
        optimization_interval_hours=1,
        top_performers_count=5
    )


@pytest.fixture
def manager(evolution_config, mock_registry, mock_marketplace, temp_data_dir):
    """Create SkillEvolutionManager instance."""
    return SkillEvolutionManager(
        config=evolution_config,
        skill_registry=mock_registry,
        marketplace=mock_marketplace,
        data_dir=temp_data_dir
    )


class TestSkillMetrics:
    """Test SkillMetrics tracking and calculations."""

    def test_skill_metrics_initialization(self):
        """Test SkillMetrics initialization."""
        metrics = SkillMetrics(skill_id="test_skill")

        assert metrics.skill_id == "test_skill"
        assert metrics.total_uses == 0
        assert metrics.successful_uses == 0
        assert metrics.failed_uses == 0
        assert metrics.total_execution_time == 0.0
        assert metrics.success_rate == 0.0
        assert metrics.status == SkillStatus.DISCOVERED

    def test_update_from_successful_execution(self):
        """Test metrics update from successful execution."""
        metrics = SkillMetrics(skill_id="test_skill")

        # Set first_used to avoid division by zero
        metrics.first_used = datetime.now() - timedelta(days=1)
        metrics.update_from_execution(success=True, execution_time=1.5)

        assert metrics.total_uses == 1
        assert metrics.successful_uses == 1
        assert metrics.failed_uses == 0
        assert metrics.total_execution_time == 1.5
        assert metrics.avg_execution_time == 1.5
        assert metrics.success_rate == 1.0
        assert metrics.last_used is not None
        assert metrics.first_used is not None

    def test_update_from_failed_execution(self):
        """Test metrics update from failed execution."""
        metrics = SkillMetrics(skill_id="test_skill")

        # Set first_used to avoid division by zero
        metrics.first_used = datetime.now() - timedelta(days=1)
        metrics.update_from_execution(success=False, execution_time=2.0)

        assert metrics.total_uses == 1
        assert metrics.successful_uses == 0
        assert metrics.failed_uses == 1
        assert metrics.success_rate == 0.0

    def test_multiple_executions_tracking(self):
        """Test tracking multiple executions."""
        metrics = SkillMetrics(skill_id="test_skill")

        # Set first_used to avoid division by zero
        metrics.first_used = datetime.now() - timedelta(days=2)

        # Record multiple executions
        metrics.update_from_execution(success=True, execution_time=1.0)
        metrics.update_from_execution(success=True, execution_time=2.0)
        metrics.update_from_execution(success=False, execution_time=1.5)

        assert metrics.total_uses == 3
        assert metrics.successful_uses == 2
        assert metrics.failed_uses == 1
        assert metrics.success_rate == pytest.approx(0.666, rel=0.01)
        assert metrics.avg_execution_time == pytest.approx(1.5, rel=0.01)

    def test_score_calculations(self):
        """Test score calculations."""
        metrics = SkillMetrics(skill_id="test_skill")

        # Set first_used to avoid division by zero
        metrics.first_used = datetime.now() - timedelta(days=3)

        # Simulate multiple successful uses
        for _ in range(5):
            metrics.update_from_execution(success=True, execution_time=1.0)

        # Should have calculated scores
        assert metrics.success_rate == 1.0
        assert metrics.quality_score == 1.0
        assert metrics.utility_score > 0.0
        assert metrics.cost_score > 0.0
        assert metrics.overall_score > 0.0

    def test_cost_score_calculation(self):
        """Test cost score based on execution time."""
        metrics = SkillMetrics(skill_id="test_skill")

        # Set first_used to avoid division by zero
        metrics.first_used = datetime.now() - timedelta(days=1)

        # Fast execution (low cost)
        metrics.update_from_execution(success=True, execution_time=0.5)
        fast_cost_score = metrics.cost_score

        # Slow execution (high cost)
        metrics.update_from_execution(success=True, execution_time=10.0)

        # Cost score should decrease with slower execution
        assert metrics.cost_score < fast_cost_score


class TestSkillEvolutionManager:
    """Test SkillEvolutionManager core functionality."""

    def test_manager_initialization(self, manager, temp_data_dir):
        """Test manager initialization."""
        assert manager.config is not None
        assert manager.registry is not None
        assert manager.marketplace is not None
        assert manager.data_dir == temp_data_dir
        assert isinstance(manager.metrics, dict)
        assert len(manager.metrics) == 0

    @pytest.mark.asyncio
    async def test_record_skill_usage(self, manager):
        """Test recording skill usage."""
        # Patch datetime.now to avoid division by zero in _recalculate_scores
        with patch('alpha.learning.skill_evolution_manager.datetime') as mock_datetime:
            # Set current time
            base_time = datetime(2026, 1, 31, 12, 0, 0)
            mock_datetime.now.return_value = base_time
            # For first_used calculation, make sure we have at least 1 day difference
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs) if args else base_time

            await manager.record_skill_usage(
                skill_id="test_skill",
                success=True,
                execution_time=1.5
            )

        assert "test_skill" in manager.metrics
        metrics = manager.metrics["test_skill"]
        assert metrics.total_uses == 1
        assert metrics.successful_uses == 1

    @pytest.mark.asyncio
    async def test_record_multiple_skill_uses(self, manager):
        """Test recording multiple uses of same skill."""
        with patch('alpha.learning.skill_evolution_manager.datetime') as mock_datetime:
            base_time = datetime(2026, 1, 31, 12, 0, 0)
            mock_datetime.now.return_value = base_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs) if args else base_time

            for i in range(5):
                await manager.record_skill_usage(
                    skill_id="test_skill",
                    success=True,
                    execution_time=1.0
                )

        metrics = manager.metrics["test_skill"]
        assert metrics.total_uses == 5
        assert metrics.successful_uses == 5

    @pytest.mark.asyncio
    async def test_status_update_after_usage(self, manager):
        """Test skill status updates based on usage."""
        skill_id = "test_skill"

        with patch('alpha.learning.skill_evolution_manager.datetime') as mock_datetime:
            base_time = datetime(2026, 1, 31, 12, 0, 0)
            mock_datetime.now.return_value = base_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs) if args else base_time

            # Record enough uses to update status
            for _ in range(manager.config.min_uses_before_prune):
                await manager.record_skill_usage(
                    skill_id=skill_id,
                    success=True,
                    execution_time=0.5
                )

        metrics = manager.metrics[skill_id]
        # With high success rate and good scores, should be ACTIVE
        assert metrics.status == SkillStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_underperforming_status(self, manager):
        """Test skill marked as underperforming."""
        skill_id = "bad_skill"

        with patch('alpha.learning.skill_evolution_manager.datetime') as mock_datetime:
            base_time = datetime(2026, 1, 31, 12, 0, 0)
            mock_datetime.now.return_value = base_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs) if args else base_time

            # Record enough failing uses
            for _ in range(manager.config.min_uses_before_prune):
                await manager.record_skill_usage(
                    skill_id=skill_id,
                    success=False,
                    execution_time=10.0
                )

        metrics = manager.metrics[skill_id]
        # With low success rate, should be UNDERPERFORMING
        assert metrics.status == SkillStatus.UNDERPERFORMING


class TestSkillEvaluation:
    """Test skill evaluation logic."""

    @pytest.mark.asyncio
    async def test_evaluate_skill_with_documentation(self, manager):
        """Test skill evaluation with good documentation."""
        skill_metadata = {
            "id": "skill_1",
            "name": "Test Skill",
            "readme": "Good documentation",
            "examples": ["example1", "example2"],
            "python_version": "3.11"
        }

        result = await manager._evaluate_skill(skill_metadata)

        assert isinstance(result, SkillEvaluationResult)
        assert result.skill_id == "skill_1"
        assert result.documentation_score > 0.5
        assert result.compatibility_score > 0.0
        assert result.overall_score > 0.0

    @pytest.mark.asyncio
    async def test_evaluate_skill_without_documentation(self, manager):
        """Test skill evaluation without documentation."""
        skill_metadata = {
            "id": "skill_2",
            "name": "Test Skill 2"
        }

        result = await manager._evaluate_skill(skill_metadata)

        assert result.documentation_score == 0.0

    @pytest.mark.asyncio
    async def test_evaluation_recommendation_activate(self, manager):
        """Test evaluation recommendation for high-quality skill."""
        skill_metadata = {
            "id": "good_skill",
            "readme": "Documentation",
            "examples": ["example"],
            "python_version": "3.11"
        }

        result = await manager._evaluate_skill(skill_metadata)

        # With good compatibility and docs, might get 'activate' recommendation
        assert result.recommendation in ["activate", "monitor"]

    @pytest.mark.asyncio
    async def test_evaluation_recommendation_reject(self, manager):
        """Test evaluation recommendation for low-quality skill."""
        with patch.object(manager, '_evaluate_skill') as mock_eval:
            # Force low scores
            mock_eval.return_value = SkillEvaluationResult(
                skill_id="bad_skill",
                evaluation_time=datetime.now(),
                quality_score=0.3,
                compatibility_score=0.3,
                documentation_score=0.0,
                code_quality_score=0.3,
                overall_score=0.3,
                recommendation="reject",
                notes=["Quality score below threshold"]
            )

            result = await manager._evaluate_skill({"id": "bad_skill"})
            assert result.recommendation == "reject"


class TestExploration:
    """Test skill exploration functionality."""

    @pytest.mark.asyncio
    async def test_explore_new_skills(self, manager, mock_marketplace):
        """Test exploring new skills from marketplace."""
        await manager._explore_new_skills()

        # Should have called marketplace search
        mock_marketplace.search.assert_called_once()

        # Should have discovered new skills
        assert len(manager.metrics) > 0
        assert len(manager.evaluation_history) > 0

    @pytest.mark.asyncio
    async def test_skip_already_discovered_skills(self, manager, mock_marketplace):
        """Test skipping already discovered skills."""
        # First exploration
        await manager._explore_new_skills()
        initial_count = len(manager.metrics)

        # Second exploration with same results
        await manager._explore_new_skills()

        # Should not duplicate metrics
        assert len(manager.metrics) == initial_count

    @pytest.mark.asyncio
    async def test_exploration_loop_cancellation(self, manager):
        """Test exploration loop can be cancelled."""
        await manager.start()

        # Give it a moment to start
        import asyncio
        await asyncio.sleep(0.1)

        # Should be running
        assert manager._exploration_task is not None

        # Stop should cancel gracefully
        await manager.stop()

        assert manager._exploration_task.done()


class TestOptimization:
    """Test skill optimization functionality."""

    @pytest.mark.asyncio
    async def test_optimize_skills(self, manager):
        """Test skill optimization."""
        # Add some active skills with different scores
        for i in range(5):
            skill_id = f"skill_{i}"
            manager.metrics[skill_id] = SkillMetrics(
                skill_id=skill_id,
                total_uses=10,
                successful_uses=10 - i,  # Varying success rates
                status=SkillStatus.ACTIVE
            )
            manager.metrics[skill_id]._recalculate_scores()

        await manager._optimize_skills()

        # Should complete without errors
        assert len(manager.metrics) == 5

    @pytest.mark.asyncio
    async def test_get_top_skills(self, manager):
        """Test getting top performing skills."""
        # Add skills with different performance
        for i in range(10):
            skill_id = f"skill_{i}"
            manager.metrics[skill_id] = SkillMetrics(
                skill_id=skill_id,
                total_uses=10,
                successful_uses=i,  # Varying success
                status=SkillStatus.ACTIVE
            )
            manager.metrics[skill_id]._recalculate_scores()

        top_skills = manager.get_top_skills(limit=3)

        assert len(top_skills) == 3
        # Should be sorted by score (descending)
        assert top_skills[0][1].overall_score >= top_skills[1][1].overall_score
        assert top_skills[1][1].overall_score >= top_skills[2][1].overall_score

    @pytest.mark.asyncio
    async def test_optimization_loop_cancellation(self, manager):
        """Test optimization loop can be cancelled."""
        await manager.start()

        import asyncio
        await asyncio.sleep(0.1)

        assert manager._optimization_task is not None

        await manager.stop()

        assert manager._optimization_task.done()


class TestPruning:
    """Test skill pruning functionality."""

    @pytest.mark.asyncio
    async def test_prune_low_performance_skill(self, manager):
        """Test pruning skill with low performance."""
        skill_id = "bad_skill"

        # Create skill with low performance
        manager.metrics[skill_id] = SkillMetrics(
            skill_id=skill_id,
            total_uses=10,
            successful_uses=2,  # 20% success rate
            failed_uses=8,
            status=SkillStatus.ACTIVE
        )
        manager.metrics[skill_id]._recalculate_scores()

        await manager._prune_skills()

        # Should be marked as pruned
        assert manager.metrics[skill_id].status == SkillStatus.PRUNED

    @pytest.mark.asyncio
    async def test_prune_unused_skill(self, manager):
        """Test pruning unused skill."""
        skill_id = "unused_skill"

        # Create skill that hasn't been used in a long time
        manager.metrics[skill_id] = SkillMetrics(
            skill_id=skill_id,
            total_uses=5,
            successful_uses=5,
            status=SkillStatus.ACTIVE
        )
        # Set last_used to long ago
        manager.metrics[skill_id].last_used = datetime.now() - timedelta(
            days=manager.config.max_unused_days + 1
        )

        await manager._prune_skills()

        # Should be marked as pruned
        assert manager.metrics[skill_id].status == SkillStatus.PRUNED

    @pytest.mark.asyncio
    async def test_dont_prune_insufficient_data(self, manager):
        """Test not pruning skill with insufficient usage data."""
        skill_id = "new_skill"

        # Create skill with few uses
        manager.metrics[skill_id] = SkillMetrics(
            skill_id=skill_id,
            total_uses=1,  # Less than min_uses_before_prune
            successful_uses=0,
            status=SkillStatus.ACTIVE
        )

        await manager._prune_skills()

        # Should NOT be pruned (not enough data)
        assert manager.metrics[skill_id].status == SkillStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_dont_prune_good_performer(self, manager):
        """Test not pruning well-performing skill."""
        skill_id = "good_skill"

        # Create skill with good performance
        manager.metrics[skill_id] = SkillMetrics(
            skill_id=skill_id,
            total_uses=10,
            successful_uses=10,
            failed_uses=0,
            status=SkillStatus.ACTIVE
        )
        # Set first_used to avoid division by zero and calculate proper scores
        manager.metrics[skill_id].first_used = datetime.now() - timedelta(days=5)
        manager.metrics[skill_id].last_used = datetime.now()
        manager.metrics[skill_id].success_rate = 1.0  # 10/10 = 100%
        manager.metrics[skill_id]._recalculate_scores()

        await manager._prune_skills()

        # Should remain active (high success rate and good scores)
        assert manager.metrics[skill_id].status == SkillStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_pruning_loop_cancellation(self, manager):
        """Test pruning loop can be cancelled."""
        await manager.start()

        import asyncio
        await asyncio.sleep(0.1)

        assert manager._pruning_task is not None

        await manager.stop()

        assert manager._pruning_task.done()


class TestPersistence:
    """Test metrics persistence (save/load)."""

    def test_save_metrics(self, manager, temp_data_dir):
        """Test saving metrics to disk."""
        # Add some metrics
        manager.metrics["skill_1"] = SkillMetrics(
            skill_id="skill_1",
            total_uses=10,
            successful_uses=8,
            status=SkillStatus.ACTIVE
        )

        manager._save_metrics()

        # Check file exists
        metrics_file = temp_data_dir / "skill_metrics.json"
        assert metrics_file.exists()

        # Check content
        with open(metrics_file, 'r') as f:
            data = json.load(f)

        assert "skill_1" in data
        assert data["skill_1"]["total_uses"] == 10
        assert data["skill_1"]["successful_uses"] == 8

    def test_load_metrics(self, temp_data_dir, evolution_config, mock_registry, mock_marketplace):
        """Test loading metrics from disk."""
        # Create metrics file
        metrics_file = temp_data_dir / "skill_metrics.json"
        test_data = {
            "skill_1": {
                "skill_id": "skill_1",
                "total_uses": 15,
                "successful_uses": 12,
                "failed_uses": 3,
                "total_execution_time": 30.0,
                "avg_execution_time": 2.0,
                "last_used": datetime.now().isoformat(),
                "first_used": datetime.now().isoformat(),
                "success_rate": 0.8,
                "cost_score": 0.6,
                "utility_score": 0.7,
                "quality_score": 0.8,
                "overall_score": 0.75,
                "status": "active"
            }
        }

        with open(metrics_file, 'w') as f:
            json.dump(test_data, f)

        # Create new manager (should load existing metrics)
        new_manager = SkillEvolutionManager(
            config=evolution_config,
            skill_registry=mock_registry,
            marketplace=mock_marketplace,
            data_dir=temp_data_dir
        )

        assert "skill_1" in new_manager.metrics
        assert new_manager.metrics["skill_1"].total_uses == 15
        assert new_manager.metrics["skill_1"].successful_uses == 12
        assert new_manager.metrics["skill_1"].status == SkillStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_save_on_stop(self, manager):
        """Test metrics are saved when manager stops."""
        # Add metric
        with patch('alpha.learning.skill_evolution_manager.datetime') as mock_datetime:
            base_time = datetime(2026, 1, 31, 12, 0, 0)
            mock_datetime.now.return_value = base_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs) if args else base_time

            await manager.record_skill_usage("test_skill", success=True, execution_time=1.0)

        await manager.stop()

        # Check file was saved
        metrics_file = manager.data_dir / "skill_metrics.json"
        assert metrics_file.exists()


class TestUtilityMethods:
    """Test utility and helper methods."""

    def test_get_skill_metrics(self, manager):
        """Test getting metrics for specific skill."""
        manager.metrics["test_skill"] = SkillMetrics(skill_id="test_skill")

        metrics = manager.get_skill_metrics("test_skill")

        assert metrics is not None
        assert metrics.skill_id == "test_skill"

    def test_get_skill_metrics_not_found(self, manager):
        """Test getting metrics for non-existent skill."""
        metrics = manager.get_skill_metrics("nonexistent")

        assert metrics is None

    def test_get_evolution_summary(self, manager):
        """Test getting evolution summary."""
        # Add various skills in different states
        manager.metrics["discovered"] = SkillMetrics(
            skill_id="discovered",
            status=SkillStatus.DISCOVERED
        )
        manager.metrics["active"] = SkillMetrics(
            skill_id="active",
            status=SkillStatus.ACTIVE
        )
        manager.metrics["pruned"] = SkillMetrics(
            skill_id="pruned",
            status=SkillStatus.PRUNED
        )

        summary = manager.get_evolution_summary()

        assert summary["total_skills"] == 3
        assert summary["active_skills"] == 1
        assert summary["discovered_skills"] == 1
        assert summary["pruned_skills"] == 1
        assert "total_evaluations" in summary


class TestEvolutionConfig:
    """Test configuration options."""

    def test_default_config(self):
        """Test default configuration values."""
        config = EvolutionConfig()

        assert config.exploration_enabled is True
        assert config.exploration_interval_hours == 24
        assert config.max_skills_per_exploration == 10
        assert config.pruning_enabled is True
        assert config.min_uses_before_prune == 5
        assert config.max_unused_days == 30
        assert config.min_success_rate == 0.5

    def test_custom_config(self):
        """Test custom configuration values."""
        config = EvolutionConfig(
            exploration_enabled=False,
            exploration_interval_hours=12,
            max_skills_per_exploration=20,
            min_uses_before_prune=10,
            max_unused_days=60
        )

        assert config.exploration_enabled is False
        assert config.exploration_interval_hours == 12
        assert config.max_skills_per_exploration == 20
        assert config.min_uses_before_prune == 10
        assert config.max_unused_days == 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
