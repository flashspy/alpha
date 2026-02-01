"""
Tests for WorkflowOptimizer
"""

import pytest
from datetime import datetime, timedelta
from statistics import mean
from alpha.workflow.optimizer import (
    WorkflowOptimization,
    WorkflowOptimizer
)


class TestWorkflowOptimization:
    """Tests for WorkflowOptimization dataclass"""

    def test_create_optimization(self):
        """Test creating a WorkflowOptimization instance"""
        now = datetime.now()
        opt = WorkflowOptimization(
            workflow_id="wf_001",
            optimization_type="parallel_execution",
            description="Steps can run in parallel",
            potential_improvement="30% faster",
            suggested_changes={"steps": [1, 2]},
            confidence=0.8,
            created_at=now
        )

        assert opt.workflow_id == "wf_001"
        assert opt.optimization_type == "parallel_execution"
        assert opt.confidence == 0.8

    def test_optimization_to_dict(self):
        """Test converting optimization to dictionary"""
        now = datetime.now()
        opt = WorkflowOptimization(
            workflow_id="wf_002",
            optimization_type="add_caching",
            description="Add caching",
            potential_improvement="50% faster",
            suggested_changes={"cache_ttl": 3600},
            confidence=0.9,
            created_at=now
        )

        result = opt.to_dict()
        assert result["workflow_id"] == "wf_002"
        assert result["optimization_type"] == "add_caching"
        assert "created_at" in result


class TestBottleneckIdentification:
    """Tests for bottleneck identification"""

    def test_identify_bottlenecks_basic(self):
        """Test identifying bottlenecks from execution history"""
        optimizer = WorkflowOptimizer()

        execution_history = [
            {
                "id": "exec1",
                "steps": [
                    {"name": "step1", "duration_ms": 100},
                    {"name": "step2", "duration_ms": 500},
                    {"name": "step3", "duration_ms": 200}
                ]
            },
            {
                "id": "exec2",
                "steps": [
                    {"name": "step1", "duration_ms": 120},
                    {"name": "step2", "duration_ms": 480},
                    {"name": "step3", "duration_ms": 180}
                ]
            }
        ]

        bottlenecks = optimizer.identify_bottlenecks(execution_history)

        assert len(bottlenecks) == 3
        # step2 should be slowest
        assert bottlenecks[0][1] == "step2"
        assert bottlenecks[0][2] > 450  # Average ~490ms

    def test_identify_bottlenecks_empty_history(self):
        """Test identifying bottlenecks with empty history"""
        optimizer = WorkflowOptimizer()

        bottlenecks = optimizer.identify_bottlenecks([])

        assert bottlenecks == []

    def test_identify_bottlenecks_sorted(self):
        """Test bottlenecks are sorted by duration"""
        optimizer = WorkflowOptimizer()

        execution_history = [
            {
                "id": "exec1",
                "steps": [
                    {"name": "fast", "duration_ms": 50},
                    {"name": "slow", "duration_ms": 1000},
                    {"name": "medium", "duration_ms": 300}
                ]
            }
        ]

        bottlenecks = optimizer.identify_bottlenecks(execution_history)

        # Should be sorted slowest first
        assert bottlenecks[0][1] == "slow"
        assert bottlenecks[1][1] == "medium"
        assert bottlenecks[2][1] == "fast"


class TestParallelExecutionAnalysis:
    """Tests for parallel execution analysis"""

    def test_analyze_parallel_execution(self):
        """Test analyzing parallel execution opportunities"""
        optimizer = WorkflowOptimizer()

        execution_history = [
            {
                "id": "exec1",
                "steps": [
                    {"name": "step1", "duration_ms": 500},
                    {"name": "step2", "duration_ms": 600},  # Consecutive slow steps
                    {"name": "step3", "duration_ms": 100}
                ]
            },
            {
                "id": "exec2",
                "steps": [
                    {"name": "step1", "duration_ms": 480},
                    {"name": "step2", "duration_ms": 620},
                    {"name": "step3", "duration_ms": 90}
                ]
            }
        ]

        optimizations = optimizer._analyze_parallel_execution("wf_001", execution_history)

        # Should detect that step1 and step2 can be parallelized
        assert len(optimizations) > 0
        assert optimizations[0].optimization_type == "parallel_execution"

    def test_no_parallel_opportunities(self):
        """Test when no parallel execution opportunities exist"""
        optimizer = WorkflowOptimizer()

        execution_history = [
            {
                "id": "exec1",
                "steps": [
                    {"name": "step1", "duration_ms": 100},  # All fast
                    {"name": "step2", "duration_ms": 110},
                    {"name": "step3", "duration_ms": 90}
                ]
            }
        ]

        optimizations = optimizer._analyze_parallel_execution("wf_001", execution_history)

        assert len(optimizations) == 0  # No significant improvement possible


class TestErrorPatternAnalysis:
    """Tests for error pattern analysis"""

    def test_analyze_high_error_rate(self):
        """Test detecting steps with high error rates"""
        optimizer = WorkflowOptimizer()

        execution_history = [
            {
                "id": "exec1",
                "steps": [
                    {"name": "step1", "status": "success"},
                    {"name": "step2", "status": "failed", "error_type": "timeout"}
                ]
            },
            {
                "id": "exec2",
                "steps": [
                    {"name": "step1", "status": "success"},
                    {"name": "step2", "status": "failed", "error_type": "timeout"}
                ]
            },
            {
                "id": "exec3",
                "steps": [
                    {"name": "step1", "status": "success"},
                    {"name": "step2", "status": "failed", "error_type": "network_error"}
                ]
            },
            {
                "id": "exec4",
                "steps": [
                    {"name": "step1", "status": "success"},
                    {"name": "step2", "status": "success"}
                ]
            }
        ]

        optimizations = optimizer._analyze_error_patterns("wf_001", execution_history)

        # Should detect step2 has 75% error rate
        assert len(optimizations) > 0
        assert optimizations[0].optimization_type == "improve_error_handling"
        assert "step2" in optimizations[0].description or optimizations[0].suggested_changes["step_name"] == "step2"

    def test_no_error_patterns(self):
        """Test when no error patterns exist"""
        optimizer = WorkflowOptimizer()

        execution_history = [
            {
                "id": "exec1",
                "steps": [
                    {"name": "step1", "status": "success"},
                    {"name": "step2", "status": "success"}
                ]
            }
        ]

        optimizations = optimizer._analyze_error_patterns("wf_001", execution_history)

        assert len(optimizations) == 0


class TestCachingOpportunities:
    """Tests for caching opportunity analysis"""

    def test_analyze_caching_for_slow_steps(self):
        """Test detecting caching opportunities for slow steps"""
        optimizer = WorkflowOptimizer()

        execution_history = [
            {
                "id": f"exec{i}",
                "steps": [
                    {"name": "api_call", "duration_ms": 2000}  # Slow repeated step
                ]
            }
            for i in range(10)  # Many executions
        ]

        optimizations = optimizer._analyze_caching_opportunities("wf_001", execution_history)

        # Should suggest caching for slow repeated step
        assert len(optimizations) > 0
        assert optimizations[0].optimization_type == "add_caching"

    def test_no_caching_for_fast_steps(self):
        """Test no caching suggestions for fast steps"""
        optimizer = WorkflowOptimizer()

        execution_history = [
            {
                "id": "exec1",
                "steps": [
                    {"name": "fast_step", "duration_ms": 50}  # Fast step
                ]
            }
        ]

        optimizations = optimizer._analyze_caching_opportunities("wf_001", execution_history)

        assert len(optimizations) == 0  # Too fast to benefit from caching


class TestWorkflowAnalysis:
    """Tests for complete workflow analysis"""

    def test_analyze_workflow_insufficient_history(self):
        """Test analyzing workflow with insufficient history"""
        optimizer = WorkflowOptimizer(min_executions=5)

        # Only 2 executions (less than min_executions=5)
        optimizer._fetch_execution_history = lambda wf_id: [
            {"id": "exec1", "steps": []},
            {"id": "exec2", "steps": []}
        ]

        optimizations = optimizer.analyze_workflow("wf_001")

        assert len(optimizations) == 0

    def test_analyze_workflow_complete(self):
        """Test complete workflow analysis"""
        optimizer = WorkflowOptimizer(min_executions=3)

        # Mock execution history with various issues
        execution_history = [
            {
                "id": "exec1",
                "steps": [
                    {"name": "step1", "duration_ms": 800, "status": "success"},
                    {"name": "step2", "duration_ms": 900, "status": "success"}
                ]
            },
            {
                "id": "exec2",
                "steps": [
                    {"name": "step1", "duration_ms": 820, "status": "success"},
                    {"name": "step2", "duration_ms": 880, "status": "failed", "error_type": "timeout"}
                ]
            },
            {
                "id": "exec3",
                "steps": [
                    {"name": "step1", "duration_ms": 810, "status": "success"},
                    {"name": "step2", "duration_ms": 890, "status": "success"}
                ]
            }
        ]

        optimizer._fetch_execution_history = lambda wf_id: execution_history

        optimizations = optimizer.analyze_workflow("wf_001")

        # Should detect multiple optimization opportunities
        assert len(optimizations) > 0


class TestRecommendations:
    """Tests for recommendation generation"""

    def test_recommend_improvements_basic(self):
        """Test generating improvement recommendations"""
        optimizer = WorkflowOptimizer()

        workflow = {"id": "wf_001", "name": "Test Workflow"}
        execution_history = [
            {
                "id": "exec1",
                "steps": [
                    {"name": "step1", "duration_ms": 600, "status": "success"},
                    {"name": "step2", "duration_ms": 700, "status": "success"}
                ]
            },
            {
                "id": "exec2",
                "steps": [
                    {"name": "step1", "duration_ms": 580, "status": "success"},
                    {"name": "step2", "duration_ms": 720, "status": "success"}
                ]
            }
        ]

        recommendations = optimizer.recommend_improvements(workflow, execution_history)

        # Should generate some recommendations
        assert isinstance(recommendations, list)


class TestEdgeCases:
    """Tests for edge cases"""

    def test_optimizer_initialization(self):
        """Test initializing optimizer with custom parameters"""
        optimizer = WorkflowOptimizer(
            execution_store=None,
            min_executions=10
        )

        assert optimizer.execution_store is None
        assert optimizer.min_executions == 10

    def test_analyze_empty_steps(self):
        """Test analyzing execution with empty steps"""
        optimizer = WorkflowOptimizer()

        execution_history = [
            {"id": "exec1", "steps": []},
            {"id": "exec2", "steps": []}
        ]

        bottlenecks = optimizer.identify_bottlenecks(execution_history)

        assert len(bottlenecks) == 0

    def test_analyze_missing_duration(self):
        """Test analyzing steps with missing duration"""
        optimizer = WorkflowOptimizer()

        execution_history = [
            {
                "id": "exec1",
                "steps": [
                    {"name": "step1"},  # No duration_ms
                    {"name": "step2", "duration_ms": 500}
                ]
            }
        ]

        bottlenecks = optimizer.identify_bottlenecks(execution_history)

        # Should only include step with duration
        assert len(bottlenecks) == 1
        assert bottlenecks[0][1] == "step2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
