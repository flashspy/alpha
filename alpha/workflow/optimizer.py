"""
Workflow Optimizer

Analyzes workflow execution history to find optimization opportunities.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from statistics import mean, stdev
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class WorkflowOptimization:
    """Optimization recommendation for a workflow."""
    workflow_id: str
    optimization_type: str  # "remove_redundancy", "parallel_execution", "parameter_tuning", "add_caching", "improve_error_handling"
    description: str
    potential_improvement: str  # e.g., "30% faster", "reduce errors"
    suggested_changes: Dict[str, Any]
    confidence: float
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "optimization_type": self.optimization_type,
            "description": self.description,
            "potential_improvement": self.potential_improvement,
            "suggested_changes": self.suggested_changes,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata
        }


class WorkflowOptimizer:
    """
    Analyzes workflow execution data to find optimization opportunities.

    Optimization Types:
    1. Remove redundant steps
    2. Enable parallel execution
    3. Tune parameters
    4. Improve error handling
    5. Add caching
    """

    def __init__(
        self,
        execution_store: Optional[Any] = None,
        min_executions: int = 5
    ):
        """
        Initialize workflow optimizer.

        Args:
            execution_store: Storage for workflow execution history
            min_executions: Minimum executions required for analysis
        """
        self.execution_store = execution_store
        self.min_executions = min_executions

    def analyze_workflow(
        self,
        workflow_id: str,
        min_executions: Optional[int] = None
    ) -> List[WorkflowOptimization]:
        """
        Analyze workflow execution history.

        Analysis includes:
        - Execution times per step
        - Error rates per step
        - Parameter value distribution
        - Step dependencies

        Args:
            workflow_id: Workflow ID to analyze
            min_executions: Minimum executions required (default: self.min_executions)

        Returns:
            List of optimization recommendations
        """
        min_executions = min_executions or self.min_executions

        logger.info(f"Analyzing workflow {workflow_id} (min_executions={min_executions})")

        # Fetch execution history
        execution_history = self._fetch_execution_history(workflow_id)

        if len(execution_history) < min_executions:
            logger.info(f"Insufficient execution history ({len(execution_history)} < {min_executions})")
            return []

        logger.info(f"Analyzing {len(execution_history)} executions")

        optimizations = []

        # Analyze for different optimization types
        try:
            # 1. Check for parallel execution opportunities
            parallel_opts = self._analyze_parallel_execution(workflow_id, execution_history)
            optimizations.extend(parallel_opts)

            # 2. Identify bottlenecks
            bottleneck_opts = self._analyze_bottlenecks(workflow_id, execution_history)
            optimizations.extend(bottleneck_opts)

            # 3. Check for redundant steps
            redundancy_opts = self._analyze_redundancy(workflow_id, execution_history)
            optimizations.extend(redundancy_opts)

            # 4. Analyze error patterns
            error_opts = self._analyze_error_patterns(workflow_id, execution_history)
            optimizations.extend(error_opts)

            # 5. Check caching opportunities
            caching_opts = self._analyze_caching_opportunities(workflow_id, execution_history)
            optimizations.extend(caching_opts)

        except Exception as e:
            logger.error(f"Error during workflow analysis: {e}")

        logger.info(f"Generated {len(optimizations)} optimization recommendations")
        return optimizations

    def _fetch_execution_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        Fetch workflow execution history from store.

        Returns list of execution dicts with keys: id, workflow_id, steps, duration, status, etc.
        """
        if not self.execution_store:
            # Return empty list if no execution store
            return []

        try:
            # Fetch executions (implementation depends on execution_store interface)
            # Placeholder: executions = self.execution_store.get_executions(workflow_id)
            executions = []

            return executions

        except Exception as e:
            logger.error(f"Error fetching execution history: {e}")
            return []

    def identify_bottlenecks(
        self,
        execution_history: List[Dict[str, Any]]
    ) -> List[Tuple[int, str, float]]:
        """
        Find slow steps in workflow.

        Args:
            execution_history: List of execution dicts

        Returns:
            List of tuples: [(step_index, step_name, avg_duration_ms), ...]
            Sorted by duration (slowest first)
        """
        if not execution_history:
            return []

        # Collect step durations
        step_durations = defaultdict(list)

        for execution in execution_history:
            steps = execution.get("steps", [])
            for i, step in enumerate(steps):
                step_name = step.get("name", f"step_{i}")
                duration = step.get("duration_ms", 0)
                if duration > 0:
                    step_durations[(i, step_name)].append(duration)

        # Calculate average durations
        avg_durations = []
        for (step_index, step_name), durations in step_durations.items():
            avg_duration = mean(durations)
            avg_durations.append((step_index, step_name, avg_duration))

        # Sort by duration (slowest first)
        avg_durations.sort(key=lambda x: x[2], reverse=True)

        return avg_durations

    def recommend_improvements(
        self,
        workflow: Dict[str, Any],
        execution_history: List[Dict[str, Any]]
    ) -> List[WorkflowOptimization]:
        """
        Generate optimization recommendations.

        Examples:
        - "Step 2 and 3 can run in parallel (30% faster)"
        - "Remove step 5: redundant with step 3"
        - "Add retry to step 4: fails 20% of the time"

        Args:
            workflow: Workflow definition dict
            execution_history: List of execution dicts

        Returns:
            List of optimization recommendations
        """
        workflow_id = workflow.get("id", "unknown")
        recommendations = []

        # Analyze all optimization types
        recommendations.extend(self._analyze_parallel_execution(workflow_id, execution_history))
        recommendations.extend(self._analyze_bottlenecks(workflow_id, execution_history))
        recommendations.extend(self._analyze_redundancy(workflow_id, execution_history))
        recommendations.extend(self._analyze_error_patterns(workflow_id, execution_history))
        recommendations.extend(self._analyze_caching_opportunities(workflow_id, execution_history))

        return recommendations

    def _analyze_parallel_execution(
        self,
        workflow_id: str,
        execution_history: List[Dict[str, Any]]
    ) -> List[WorkflowOptimization]:
        """
        Analyze opportunities for parallel execution.

        Identifies steps that:
        - Have no dependencies on each other
        - Take significant time individually
        - Can be safely parallelized

        Args:
            workflow_id: Workflow ID
            execution_history: Execution history

        Returns:
            List of parallel execution optimization recommendations
        """
        optimizations = []

        if not execution_history:
            return optimizations

        try:
            # Analyze step dependencies (simplified heuristic)
            # In real implementation, would analyze actual step dependencies from workflow definition

            # Get average step durations
            bottlenecks = self.identify_bottlenecks(execution_history)

            # Look for consecutive slow steps that could potentially be parallelized
            for i in range(len(bottlenecks) - 1):
                step1_idx, step1_name, step1_duration = bottlenecks[i]
                step2_idx, step2_name, step2_duration = bottlenecks[i + 1]

                # Check if steps are consecutive
                if step2_idx == step1_idx + 1:
                    # Estimate potential improvement
                    total_sequential = step1_duration + step2_duration
                    total_parallel = max(step1_duration, step2_duration)
                    improvement_ms = total_sequential - total_parallel
                    improvement_pct = (improvement_ms / total_sequential) * 100

                    if improvement_pct >= 20:  # At least 20% improvement
                        opt = WorkflowOptimization(
                            workflow_id=workflow_id,
                            optimization_type="parallel_execution",
                            description=f"Steps {step1_idx} and {step2_idx} can run in parallel",
                            potential_improvement=f"{improvement_pct:.0f}% faster",
                            suggested_changes={
                                "steps": [step1_idx, step2_idx],
                                "action": "enable_parallel_execution",
                                "estimated_savings_ms": improvement_ms
                            },
                            confidence=0.7,
                            created_at=datetime.now(),
                            metadata={
                                "step1": step1_name,
                                "step2": step2_name,
                                "step1_duration_ms": step1_duration,
                                "step2_duration_ms": step2_duration
                            }
                        )
                        optimizations.append(opt)

        except Exception as e:
            logger.error(f"Error analyzing parallel execution: {e}")

        return optimizations

    def _analyze_bottlenecks(
        self,
        workflow_id: str,
        execution_history: List[Dict[str, Any]]
    ) -> List[WorkflowOptimization]:
        """
        Analyze bottlenecks and recommend improvements.

        Args:
            workflow_id: Workflow ID
            execution_history: Execution history

        Returns:
            List of bottleneck optimization recommendations
        """
        optimizations = []

        if not execution_history:
            return optimizations

        try:
            bottlenecks = self.identify_bottlenecks(execution_history)

            # Report top 3 slowest steps
            for step_index, step_name, avg_duration in bottlenecks[:3]:
                # Calculate what percentage of total workflow time this step takes
                total_workflow_times = [
                    sum(step.get("duration_ms", 0) for step in exec_data.get("steps", []))
                    for exec_data in execution_history
                ]
                avg_total_time = mean(total_workflow_times) if total_workflow_times else 0

                if avg_total_time > 0:
                    pct_of_total = (avg_duration / avg_total_time) * 100

                    if pct_of_total >= 30:  # Step takes ≥30% of total time
                        opt = WorkflowOptimization(
                            workflow_id=workflow_id,
                            optimization_type="parameter_tuning",
                            description=f"Step {step_index} ({step_name}) is a bottleneck",
                            potential_improvement=f"Optimize to reduce {pct_of_total:.0f}% of workflow time",
                            suggested_changes={
                                "step_index": step_index,
                                "step_name": step_name,
                                "action": "optimize_step",
                                "suggestions": [
                                    "Review step logic for inefficiencies",
                                    "Consider caching intermediate results",
                                    "Optimize database queries or API calls"
                                ]
                            },
                            confidence=0.8,
                            created_at=datetime.now(),
                            metadata={
                                "avg_duration_ms": avg_duration,
                                "pct_of_total_time": pct_of_total
                            }
                        )
                        optimizations.append(opt)

        except Exception as e:
            logger.error(f"Error analyzing bottlenecks: {e}")

        return optimizations

    def _analyze_redundancy(
        self,
        workflow_id: str,
        execution_history: List[Dict[str, Any]]
    ) -> List[WorkflowOptimization]:
        """
        Analyze for redundant steps.

        Looks for:
        - Steps that produce identical outputs
        - Steps that are always skipped
        - Duplicate operations

        Args:
            workflow_id: Workflow ID
            execution_history: Execution history

        Returns:
            List of redundancy optimization recommendations
        """
        optimizations = []

        # Placeholder - in real implementation would:
        # 1. Track step outputs to find duplicates
        # 2. Identify steps that are always skipped
        # 3. Look for repeated operations

        # For now, return empty list
        return optimizations

    def _analyze_error_patterns(
        self,
        workflow_id: str,
        execution_history: List[Dict[str, Any]]
    ) -> List[WorkflowOptimization]:
        """
        Analyze error patterns and recommend improvements.

        Looks for:
        - Steps with high failure rates
        - Common error types
        - Missing retry logic

        Args:
            workflow_id: Workflow ID
            execution_history: Execution history

        Returns:
            List of error handling optimization recommendations
        """
        optimizations = []

        if not execution_history:
            return optimizations

        try:
            # Calculate error rates per step
            step_stats = defaultdict(lambda: {"total": 0, "errors": 0, "error_types": []})

            for execution in execution_history:
                steps = execution.get("steps", [])
                for i, step in enumerate(steps):
                    step_name = step.get("name", f"step_{i}")
                    step_stats[(i, step_name)]["total"] += 1

                    if step.get("status") == "failed":
                        step_stats[(i, step_name)]["errors"] += 1
                        error_type = step.get("error_type", "unknown")
                        step_stats[(i, step_name)]["error_types"].append(error_type)

            # Identify steps with high error rates
            for (step_index, step_name), stats in step_stats.items():
                if stats["total"] >= 3:  # At least 3 executions
                    error_rate = stats["errors"] / stats["total"]

                    if error_rate >= 0.2:  # ≥20% error rate
                        opt = WorkflowOptimization(
                            workflow_id=workflow_id,
                            optimization_type="improve_error_handling",
                            description=f"Step {step_index} ({step_name}) has high error rate",
                            potential_improvement=f"Reduce {error_rate:.0%} error rate",
                            suggested_changes={
                                "step_index": step_index,
                                "step_name": step_name,
                                "action": "add_retry_logic",
                                "suggestions": [
                                    "Add retry mechanism with exponential backoff",
                                    "Implement better error handling",
                                    "Add validation before step execution"
                                ]
                            },
                            confidence=0.9,
                            created_at=datetime.now(),
                            metadata={
                                "error_rate": error_rate,
                                "total_executions": stats["total"],
                                "errors": stats["errors"],
                                "common_error_types": list(set(stats["error_types"]))
                            }
                        )
                        optimizations.append(opt)

        except Exception as e:
            logger.error(f"Error analyzing error patterns: {e}")

        return optimizations

    def _analyze_caching_opportunities(
        self,
        workflow_id: str,
        execution_history: List[Dict[str, Any]]
    ) -> List[WorkflowOptimization]:
        """
        Analyze opportunities for caching.

        Looks for:
        - Steps that produce same output for same input
        - Expensive operations that could be cached
        - Repeated API calls

        Args:
            workflow_id: Workflow ID
            execution_history: Execution history

        Returns:
            List of caching optimization recommendations
        """
        optimizations = []

        if not execution_history:
            return optimizations

        try:
            # Analyze step inputs/outputs for caching opportunities
            # Simplified heuristic: Look for slow steps that execute frequently

            bottlenecks = self.identify_bottlenecks(execution_history)

            # Check if slow steps execute with similar parameters
            for step_index, step_name, avg_duration in bottlenecks[:3]:
                # If step is slow (>1 second average) and executed multiple times
                if avg_duration > 1000 and len(execution_history) >= 5:
                    # Estimate potential improvement from caching
                    # Assume 80% cache hit rate after first execution
                    cache_hit_rate = 0.8
                    cached_duration = avg_duration * 0.1  # Cached calls are 10x faster
                    improved_avg = (cache_hit_rate * cached_duration) + ((1 - cache_hit_rate) * avg_duration)
                    improvement_pct = ((avg_duration - improved_avg) / avg_duration) * 100

                    if improvement_pct >= 30:  # At least 30% improvement
                        opt = WorkflowOptimization(
                            workflow_id=workflow_id,
                            optimization_type="add_caching",
                            description=f"Step {step_index} ({step_name}) could benefit from caching",
                            potential_improvement=f"{improvement_pct:.0f}% faster with caching",
                            suggested_changes={
                                "step_index": step_index,
                                "step_name": step_name,
                                "action": "add_result_caching",
                                "cache_ttl_seconds": 3600,  # 1 hour default
                                "estimated_savings_ms": avg_duration - improved_avg
                            },
                            confidence=0.7,
                            created_at=datetime.now(),
                            metadata={
                                "avg_duration_ms": avg_duration,
                                "assumed_cache_hit_rate": cache_hit_rate,
                                "executions_analyzed": len(execution_history)
                            }
                        )
                        optimizations.append(opt)

        except Exception as e:
            logger.error(f"Error analyzing caching opportunities: {e}")

        return optimizations
