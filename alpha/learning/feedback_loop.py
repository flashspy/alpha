"""
Alpha - Feedback Loop

Orchestrates the continuous learning cycle:
analyze logs -> generate recommendations -> apply improvements -> track results
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from alpha.learning.log_analyzer import LogAnalyzer
from alpha.learning.improvement_executor import ImprovementExecutor, ImprovementStatus
from alpha.learning.learning_store import LearningStore
from alpha.scheduler.scheduler import TaskScheduler, TaskSpec, ScheduleConfig, ScheduleType


logger = logging.getLogger(__name__)


class FeedbackLoopMode(Enum):
    """Feedback loop operation mode."""
    MANUAL = "manual"  # Manual approval required
    SEMI_AUTO = "semi_auto"  # Auto-apply safe improvements
    FULL_AUTO = "full_auto"  # Fully automatic


@dataclass
class FeedbackLoopConfig:
    """
    Configuration for feedback loop.

    Attributes:
        mode: Operation mode
        analysis_frequency: How often to analyze logs
        min_confidence: Minimum confidence for auto-apply
        max_daily_improvements: Max improvements per day
        enable_rollback: Whether rollback is enabled
        dry_run_first: Always dry-run before applying
    """
    mode: FeedbackLoopMode = FeedbackLoopMode.SEMI_AUTO
    analysis_frequency: str = "daily"  # daily, weekly, custom_cron
    analysis_cron: Optional[str] = None  # Custom cron expression
    analysis_days: int = 7  # Days of history to analyze
    min_confidence: float = 0.7
    max_daily_improvements: int = 5
    enable_rollback: bool = True
    dry_run_first: bool = True
    store_patterns: bool = True
    store_metrics: bool = True


class FeedbackLoop:
    """
    Orchestrates continuous system improvement through learning.

    Features:
    - Scheduled log analysis
    - Automatic improvement application
    - Success tracking
    - Rollback on failure
    - Metrics collection
    """

    def __init__(
        self,
        config: FeedbackLoopConfig,
        log_analyzer: LogAnalyzer,
        improvement_executor: ImprovementExecutor,
        learning_store: LearningStore,
        scheduler: Optional[TaskScheduler] = None
    ):
        """
        Initialize feedback loop.

        Args:
            config: Feedback loop configuration
            log_analyzer: Log analyzer instance
            improvement_executor: Improvement executor instance
            learning_store: Learning store instance
            scheduler: Optional task scheduler for automation
        """
        self.config = config
        self.log_analyzer = log_analyzer
        self.improvement_executor = improvement_executor
        self.learning_store = learning_store
        self.scheduler = scheduler

        self.running = False
        self.schedule_id: Optional[str] = None
        self.cycle_count = 0
        self.last_cycle_time: Optional[datetime] = None

        logger.info(f"Feedback loop initialized: mode={config.mode.value}")

    async def start(self):
        """Start the feedback loop."""
        logger.info("Starting feedback loop...")

        # Initialize learning store
        self.learning_store.initialize()

        # Schedule periodic analysis if scheduler available
        if self.scheduler and not self.schedule_id:
            await self._schedule_analysis()

        self.running = True
        logger.info("Feedback loop started")

    async def stop(self):
        """Stop the feedback loop."""
        logger.info("Stopping feedback loop...")

        # Cancel scheduled analysis
        if self.scheduler and self.schedule_id:
            await self.scheduler.cancel_schedule(self.schedule_id)
            self.schedule_id = None

        self.running = False
        logger.info("Feedback loop stopped")

    async def run_cycle(self) -> Dict[str, Any]:
        """
        Run a single learning cycle.

        Returns:
            Cycle results dictionary
        """
        cycle_start = datetime.now()
        self.cycle_count += 1

        logger.info(f"Starting learning cycle #{self.cycle_count}")

        results = {
            "cycle_number": self.cycle_count,
            "started_at": cycle_start.isoformat(),
            "steps": {}
        }

        try:
            # Step 1: Analyze logs
            logger.info("Step 1: Analyzing logs...")
            analysis_result = await self.log_analyzer.analyze_time_period(
                days=self.config.analysis_days
            )

            results["steps"]["analysis"] = {
                "patterns_found": analysis_result["patterns"]["total"],
                "patterns_by_type": analysis_result["patterns"]["by_type"]
            }

            # Store patterns if enabled
            if self.config.store_patterns:
                for pattern in self.log_analyzer.patterns:
                    await self.learning_store.store_pattern(pattern)

            # Step 2: Generate recommendations
            logger.info("Step 2: Generating recommendations...")
            recommendations = await self.log_analyzer.generate_recommendations()

            results["steps"]["recommendations"] = {
                "total": len(recommendations),
                "by_priority": analysis_result["recommendations"]["by_priority"]
            }

            # Step 3: Apply improvements
            logger.info("Step 3: Applying improvements...")
            improvements_applied = await self._apply_improvements(recommendations)

            results["steps"]["improvements"] = {
                "applied": len([i for i in improvements_applied if i.status == ImprovementStatus.APPLIED]),
                "failed": len([i for i in improvements_applied if i.status == ImprovementStatus.FAILED]),
                "dry_run": len([i for i in improvements_applied if i.metadata.get("dry_run")])
            }

            # Step 4: Track metrics
            logger.info("Step 4: Tracking metrics...")
            if self.config.store_metrics:
                await self._track_metrics(cycle_start, datetime.now())

            results["steps"]["metrics"] = {"stored": True}

            # Mark success
            results["status"] = "completed"
            results["completed_at"] = datetime.now().isoformat()
            results["duration"] = (datetime.now() - cycle_start).total_seconds()

            logger.info(
                f"Learning cycle #{self.cycle_count} completed: "
                f"{results['steps']['improvements']['applied']} improvements applied"
            )

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"Learning cycle failed: {e}", exc_info=True)

        self.last_cycle_time = datetime.now()
        return results

    async def _apply_improvements(
        self,
        recommendations: List[Any]
    ) -> List[Any]:
        """
        Apply improvement recommendations based on configuration.

        Args:
            recommendations: List of ImprovementRecommendation instances

        Returns:
            List of AppliedImprovement instances
        """
        applied_improvements = []

        # Filter recommendations based on confidence
        filtered_recs = [
            r for r in recommendations
            if r.confidence >= self.config.min_confidence
        ]

        logger.info(
            f"Filtered {len(filtered_recs)} recommendations "
            f"(out of {len(recommendations)}) with confidence >= {self.config.min_confidence}"
        )

        # Limit daily improvements
        improvements_today = len([
            imp for imp in self.improvement_executor.applied_improvements
            if imp.applied_at and
            imp.applied_at.date() == datetime.now().date()
        ])

        remaining_quota = self.config.max_daily_improvements - improvements_today
        if remaining_quota <= 0:
            logger.warning("Daily improvement quota reached")
            return applied_improvements

        # Apply improvements
        for i, recommendation in enumerate(filtered_recs[:remaining_quota]):
            try:
                # Determine if should auto-apply
                should_apply = self._should_auto_apply(recommendation)
                dry_run = not should_apply or self.config.dry_run_first

                logger.info(
                    f"Processing recommendation {i+1}/{len(filtered_recs)}: "
                    f"{recommendation.title} (dry_run={dry_run})"
                )

                # Apply improvement
                improvement = await self.improvement_executor.apply_recommendation(
                    recommendation,
                    validate=True,
                    dry_run=dry_run
                )

                applied_improvements.append(improvement)

                # If dry run succeeded and full auto mode, apply for real
                if (dry_run and
                    improvement.status != ImprovementStatus.FAILED and
                    self.config.mode == FeedbackLoopMode.FULL_AUTO):

                    logger.info("Dry run successful, applying for real...")
                    improvement = await self.improvement_executor.apply_recommendation(
                        recommendation,
                        validate=False,
                        dry_run=False
                    )
                    applied_improvements[-1] = improvement

            except Exception as e:
                logger.error(f"Failed to apply recommendation: {e}", exc_info=True)
                continue

        return applied_improvements

    def _should_auto_apply(self, recommendation: Any) -> bool:
        """
        Determine if recommendation should be auto-applied.

        Args:
            recommendation: ImprovementRecommendation instance

        Returns:
            True if should auto-apply
        """
        if self.config.mode == FeedbackLoopMode.MANUAL:
            return False

        if self.config.mode == FeedbackLoopMode.FULL_AUTO:
            return True

        # Semi-auto mode: apply only safe improvements with high confidence
        safe_actions = ["config_update", "model_routing"]
        return (
            recommendation.action_type in safe_actions and
            recommendation.confidence >= 0.8
        )

    async def _track_metrics(
        self,
        period_start: datetime,
        period_end: datetime
    ):
        """
        Track success metrics for the period.

        Args:
            period_start: Start of period
            period_end: End of period
        """
        # Get improvement statistics
        stats = self.improvement_executor.get_statistics()

        # Store success rate metric
        await self.learning_store.store_metric(
            metric_type="success_rate",
            metric_name="improvement_application",
            value=stats["success_rate"],
            period_start=period_start,
            period_end=period_end,
            metadata=stats
        )

        # Store cycle count metric
        await self.learning_store.store_metric(
            metric_type="cycle_count",
            metric_name="feedback_loop",
            value=self.cycle_count,
            period_start=period_start,
            period_end=period_end
        )

    async def _schedule_analysis(self):
        """Schedule periodic log analysis."""
        if not self.scheduler:
            logger.warning("No scheduler available for periodic analysis")
            return

        # Determine schedule configuration
        if self.config.analysis_frequency == "daily":
            schedule_config = ScheduleConfig(
                type=ScheduleType.DAILY,
                time="02:00"  # 2 AM daily
            )
        elif self.config.analysis_frequency == "weekly":
            schedule_config = ScheduleConfig(
                type=ScheduleType.WEEKLY,
                weekday=1,  # Monday
                time="02:00"
            )
        elif self.config.analysis_cron:
            schedule_config = ScheduleConfig(
                type=ScheduleType.CRON,
                cron=self.config.analysis_cron
            )
        else:
            logger.error("Invalid analysis frequency configuration")
            return

        # Create task spec
        task_spec = TaskSpec(
            name="feedback_loop_analysis",
            description="Automated learning cycle execution",
            executor="feedback_loop_executor",
            params={"config": self.config.__dict__}
        )

        # Schedule the task
        self.schedule_id = await self.scheduler.schedule_task(
            task_spec,
            schedule_config
        )

        logger.info(f"Scheduled periodic analysis: {self.config.analysis_frequency}")

    async def manual_trigger(self) -> Dict[str, Any]:
        """
        Manually trigger a learning cycle.

        Returns:
            Cycle results
        """
        logger.info("Manually triggered learning cycle")
        return await self.run_cycle()

    async def rollback_last_improvement(self) -> bool:
        """
        Rollback the last applied improvement.

        Returns:
            True if rollback successful
        """
        if not self.config.enable_rollback:
            logger.error("Rollback is disabled in configuration")
            return False

        applied = await self.improvement_executor.get_applied_improvements(
            status=ImprovementStatus.APPLIED
        )

        if not applied:
            logger.warning("No applied improvements to rollback")
            return False

        # Get most recent
        last_improvement = max(applied, key=lambda x: x.applied_at)

        logger.info(f"Rolling back improvement: {last_improvement.id}")
        return await self.improvement_executor.rollback_improvement(last_improvement.id)

    def get_status(self) -> Dict[str, Any]:
        """
        Get feedback loop status.

        Returns:
            Status dictionary
        """
        return {
            "running": self.running,
            "mode": self.config.mode.value,
            "cycle_count": self.cycle_count,
            "last_cycle": self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            "scheduled": self.schedule_id is not None,
            "schedule_id": self.schedule_id,
            "configuration": {
                "analysis_frequency": self.config.analysis_frequency,
                "analysis_days": self.config.analysis_days,
                "min_confidence": self.config.min_confidence,
                "max_daily_improvements": self.config.max_daily_improvements
            }
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get feedback loop statistics.

        Returns:
            Statistics dictionary
        """
        learning_stats = self.learning_store.get_statistics()
        executor_stats = self.improvement_executor.get_statistics()

        return {
            "feedback_loop": {
                "total_cycles": self.cycle_count,
                "last_cycle": self.last_cycle_time.isoformat() if self.last_cycle_time else None
            },
            "learning_store": learning_stats,
            "improvements": executor_stats
        }
