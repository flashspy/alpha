"""
Alpha - Skill Evolution Manager

Implements self-evolving skill library with proactive exploration, evaluation,
and optimization. Continuously improves skill selection and usage.

Core Functions:
- Proactive skill exploration
- Smart quality evaluation
- Usage tracking and analytics
- Performance-based optimization
- Automatic skill pruning
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import json


logger = logging.getLogger(__name__)


class SkillStatus(Enum):
    """Skill lifecycle status."""
    DISCOVERED = "discovered"
    EVALUATING = "evaluating"
    ACTIVE = "active"
    UNDERPERFORMING = "underperforming"
    PRUNED = "pruned"


@dataclass
class SkillMetrics:
    """Tracks performance metrics for a skill."""
    skill_id: str
    total_uses: int = 0
    successful_uses: int = 0
    failed_uses: int = 0
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    last_used: Optional[datetime] = None
    first_used: Optional[datetime] = None
    success_rate: float = 0.0
    cost_score: float = 0.0  # Normalized 0-1, lower is better
    utility_score: float = 0.0  # 0-1, higher is better
    quality_score: float = 0.0  # 0-1, higher is better
    overall_score: float = 0.0  # Combined weighted score
    status: SkillStatus = SkillStatus.DISCOVERED

    def update_from_execution(self, success: bool, execution_time: float):
        """Update metrics after skill execution."""
        self.total_uses += 1
        if success:
            self.successful_uses += 1
        else:
            self.failed_uses += 1
        
        self.total_execution_time += execution_time
        self.avg_execution_time = self.total_execution_time / self.total_uses
        self.success_rate = self.successful_uses / self.total_uses if self.total_uses > 0 else 0.0
        self.last_used = datetime.now()
        if not self.first_used:
            self.first_used = datetime.now()
        
        # Recalculate scores
        self._recalculate_scores()
    
    def _recalculate_scores(self):
        """Recalculate composite scores."""
        # Utility: based on usage frequency (normalized to 0-1)
        days_since_first_use = max(1, (datetime.now() - self.first_used).days if self.first_used else 1)
        self.utility_score = min(1.0, self.total_uses / (days_since_first_use * 2))  # Expect ~2 uses/day for highly useful
        
        # Quality: based on success rate
        self.quality_score = self.success_rate
        
        # Cost: based on execution time (normalized, assuming 5s is expensive)
        self.cost_score = max(0.0, 1.0 - (self.avg_execution_time / 5.0))
        
        # Overall: weighted combination
        self.overall_score = (
            0.4 * self.success_rate +
            0.3 * self.utility_score +
            0.2 * self.quality_score +
            0.1 * self.cost_score
        )


@dataclass
class SkillEvaluationResult:
    """Result of skill quality evaluation."""
    skill_id: str
    evaluation_time: datetime
    quality_score: float  # 0-1
    compatibility_score: float  # 0-1
    documentation_score: float  # 0-1
    code_quality_score: float  # 0-1
    overall_score: float  # 0-1
    recommendation: str  # "activate", "monitor", "reject"
    notes: List[str] = field(default_factory=list)


@dataclass
class EvolutionConfig:
    """Configuration for skill evolution system."""
    # Exploration
    exploration_enabled: bool = True
    exploration_interval_hours: int = 24
    max_skills_per_exploration: int = 10
    
    # Evaluation
    min_quality_score: float = 0.6
    min_compatibility_score: float = 0.7
    
    # Pruning
    pruning_enabled: bool = True
    pruning_interval_hours: int = 168  # Weekly
    min_uses_before_prune: int = 5
    max_unused_days: int = 30
    min_success_rate: float = 0.5
    min_overall_score: float = 0.4
    
    # Optimization
    optimization_enabled: bool = True
    optimization_interval_hours: int = 24
    top_performers_count: int = 10


class SkillEvolutionManager:
    """
    Manages self-evolving skill library with continuous improvement.
    
    Capabilities:
    - Proactive skill discovery from marketplace
    - Quality evaluation of new skills
    - Usage tracking and performance analytics
    - Automatic skill optimization
    - Intelligent skill pruning
    """
    
    def __init__(
        self,
        config: EvolutionConfig,
        skill_registry: Any,  # alpha.skills.registry.SkillRegistry
        marketplace: Any,  # alpha.skills.marketplace.SkillMarketplace
        data_dir: Path = Path("data/skill_evolution")
    ):
        self.config = config
        self.registry = skill_registry
        self.marketplace = marketplace
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Metrics storage
        self.metrics: Dict[str, SkillMetrics] = {}
        self.evaluation_history: List[SkillEvaluationResult] = []
        
        # Evolution tasks
        self._exploration_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None
        self._pruning_task: Optional[asyncio.Task] = None
        
        # Load existing metrics
        self._load_metrics()
        
        logger.info("SkillEvolutionManager initialized")
    
    async def start(self):
        """Start evolution processes."""
        logger.info("Starting skill evolution processes...")
        
        if self.config.exploration_enabled:
            self._exploration_task = asyncio.create_task(self._exploration_loop())
        
        if self.config.optimization_enabled:
            self._optimization_task = asyncio.create_task(self._optimization_loop())
        
        if self.config.pruning_enabled:
            self._pruning_task = asyncio.create_task(self._pruning_loop())
        
        logger.info("Skill evolution processes started")
    
    async def stop(self):
        """Stop evolution processes."""
        logger.info("Stopping skill evolution processes...")
        
        tasks = [self._exploration_task, self._optimization_task, self._pruning_task]
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self._save_metrics()
        logger.info("Skill evolution processes stopped")
    
    async def record_skill_usage(
        self,
        skill_id: str,
        success: bool,
        execution_time: float
    ):
        """Record skill usage for tracking and optimization."""
        if skill_id not in self.metrics:
            self.metrics[skill_id] = SkillMetrics(skill_id=skill_id)
        
        self.metrics[skill_id].update_from_execution(success, execution_time)
        
        # Update status based on performance
        metrics = self.metrics[skill_id]
        if metrics.total_uses >= self.config.min_uses_before_prune:
            if metrics.overall_score >= 0.7:
                metrics.status = SkillStatus.ACTIVE
            elif metrics.overall_score < self.config.min_overall_score:
                metrics.status = SkillStatus.UNDERPERFORMING
        
        logger.debug(f"Recorded usage for skill {skill_id}: success={success}, time={execution_time:.2f}s")
    
    async def _exploration_loop(self):
        """Continuously explore and discover new skills."""
        logger.info("Starting skill exploration loop")
        
        while True:
            try:
                await self._explore_new_skills()
                await asyncio.sleep(self.config.exploration_interval_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in exploration loop: {e}", exc_info=True)
                await asyncio.sleep(3600)  # Retry after 1 hour on error
    
    async def _explore_new_skills(self):
        """Discover and evaluate new skills from marketplace."""
        logger.info("Exploring marketplace for new skills...")
        
        try:
            # Search marketplace for trending/popular skills
            results = await self.marketplace.search(
                query="",  # All skills
                limit=self.config.max_skills_per_exploration
            )
            
            new_skills_found = 0
            for skill_metadata in results:
                skill_id = skill_metadata.get("id", skill_metadata.get("name"))
                
                # Skip if already have metrics (already discovered)
                if skill_id in self.metrics:
                    continue
                
                # Evaluate the skill
                evaluation = await self._evaluate_skill(skill_metadata)
                self.evaluation_history.append(evaluation)
                
                # Initialize metrics
                self.metrics[skill_id] = SkillMetrics(
                    skill_id=skill_id,
                    status=SkillStatus.DISCOVERED,
                    quality_score=evaluation.quality_score
                )
                
                # Auto-activate if meets criteria
                if evaluation.recommendation == "activate":
                    logger.info(f"Auto-activating high-quality skill: {skill_id}")
                    self.metrics[skill_id].status = SkillStatus.EVALUATING
                    # TODO: Install skill
                
                new_skills_found += 1
            
            logger.info(f"Exploration complete: {new_skills_found} new skills discovered")
            self._save_metrics()
            
        except Exception as e:
            logger.error(f"Error exploring skills: {e}", exc_info=True)
    
    async def _evaluate_skill(self, skill_metadata: Dict[str, Any]) -> SkillEvaluationResult:
        """Evaluate a skill's quality and compatibility."""
        skill_id = skill_metadata.get("id", skill_metadata.get("name"))
        
        # Quality scoring (0-1)
        quality_score = 0.5  # Default
        
        # Check for documentation
        has_readme = "readme" in skill_metadata or "description" in skill_metadata
        has_examples = "examples" in skill_metadata
        documentation_score = (0.5 if has_readme else 0.0) + (0.5 if has_examples else 0.0)
        
        # Compatibility (check dependencies, Python version, etc.)
        compatibility_score = 0.8  # Assume mostly compatible unless proven otherwise
        notes = []
        
        # Check version compatibility
        if "python_version" in skill_metadata:
            required_version = skill_metadata["python_version"]
            # Simplified check
            if "3.8" in required_version or "3.9" in required_version or "3.10" in required_version or "3.11" in required_version or "3.12" in required_version:
                compatibility_score = 1.0
            else:
                compatibility_score = 0.5
                notes.append("Python version compatibility uncertain")
        
        # Code quality (simplified - based on metadata)
        code_quality_score = 0.7  # Default assumption
        
        # Overall score (weighted)
        overall_score = (
            0.3 * quality_score +
            0.3 * compatibility_score +
            0.2 * documentation_score +
            0.2 * code_quality_score
        )
        
        # Recommendation
        if overall_score >= 0.7 and compatibility_score >= self.config.min_compatibility_score:
            recommendation = "activate"
        elif overall_score >= 0.5:
            recommendation = "monitor"
        else:
            recommendation = "reject"
            notes.append("Quality score below threshold")
        
        return SkillEvaluationResult(
            skill_id=skill_id,
            evaluation_time=datetime.now(),
            quality_score=quality_score,
            compatibility_score=compatibility_score,
            documentation_score=documentation_score,
            code_quality_score=code_quality_score,
            overall_score=overall_score,
            recommendation=recommendation,
            notes=notes
        )
    
    async def _optimization_loop(self):
        """Continuously optimize skill selection and prioritization."""
        logger.info("Starting skill optimization loop")
        
        while True:
            try:
                await self._optimize_skills()
                await asyncio.sleep(self.config.optimization_interval_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}", exc_info=True)
                await asyncio.sleep(3600)
    
    async def _optimize_skills(self):
        """Analyze and optimize skill performance."""
        logger.info("Optimizing skill library...")
        
        # Identify top performers
        active_skills = {
            skill_id: metrics
            for skill_id, metrics in self.metrics.items()
            if metrics.status == SkillStatus.ACTIVE and metrics.total_uses >= self.config.min_uses_before_prune
        }
        
        if not active_skills:
            logger.info("No active skills to optimize yet")
            return
        
        # Sort by overall score
        sorted_skills = sorted(
            active_skills.items(),
            key=lambda x: x[1].overall_score,
            reverse=True
        )
        
        top_performers = sorted_skills[:self.config.top_performers_count]
        
        logger.info(f"Top {len(top_performers)} performing skills:")
        for skill_id, metrics in top_performers:
            logger.info(
                f"  {skill_id}: "
                f"score={metrics.overall_score:.2f}, "
                f"uses={metrics.total_uses}, "
                f"success_rate={metrics.success_rate:.1%}"
            )
        
        # TODO: Implement skill combination experiments
        # TODO: Adjust skill priorities based on performance
        
        self._save_metrics()
    
    async def _pruning_loop(self):
        """Continuously prune underperforming/unused skills."""
        logger.info("Starting skill pruning loop")
        
        while True:
            try:
                await self._prune_skills()
                await asyncio.sleep(self.config.pruning_interval_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in pruning loop: {e}", exc_info=True)
                await asyncio.sleep(3600)
    
    async def _prune_skills(self):
        """Remove underperforming or unused skills."""
        logger.info("Pruning skill library...")
        
        pruned_count = 0
        now = datetime.now()
        
        for skill_id, metrics in list(self.metrics.items()):
            should_prune = False
            reason = ""
            
            # Skip if not enough data
            if metrics.total_uses < self.config.min_uses_before_prune:
                continue
            
            # Check for low performance
            if metrics.overall_score < self.config.min_overall_score:
                should_prune = True
                reason = f"Low overall score: {metrics.overall_score:.2f}"
            
            # Check for low success rate
            elif metrics.success_rate < self.config.min_success_rate:
                should_prune = True
                reason = f"Low success rate: {metrics.success_rate:.1%}"
            
            # Check for inactivity
            elif metrics.last_used:
                days_unused = (now - metrics.last_used).days
                if days_unused > self.config.max_unused_days:
                    should_prune = True
                    reason = f"Unused for {days_unused} days"
            
            if should_prune:
                logger.info(f"Pruning skill {skill_id}: {reason}")
                metrics.status = SkillStatus.PRUNED
                pruned_count += 1
                # TODO: Actually uninstall/disable the skill
        
        logger.info(f"Pruning complete: {pruned_count} skills pruned")
        self._save_metrics()
    
    def get_skill_metrics(self, skill_id: str) -> Optional[SkillMetrics]:
        """Get metrics for a specific skill."""
        return self.metrics.get(skill_id)
    
    def get_top_skills(self, limit: int = 10) -> List[Tuple[str, SkillMetrics]]:
        """Get top performing skills."""
        active_skills = [
            (skill_id, metrics)
            for skill_id, metrics in self.metrics.items()
            if metrics.status == SkillStatus.ACTIVE
        ]
        
        return sorted(
            active_skills,
            key=lambda x: x[1].overall_score,
            reverse=True
        )[:limit]
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get summary of skill evolution status."""
        status_counts = {status: 0 for status in SkillStatus}
        for metrics in self.metrics.values():
            status_counts[metrics.status] += 1
        
        total_skills = len(self.metrics)
        active_skills = status_counts[SkillStatus.ACTIVE]
        
        return {
            "total_skills": total_skills,
            "active_skills": active_skills,
            "discovered_skills": status_counts[SkillStatus.DISCOVERED],
            "evaluating_skills": status_counts[SkillStatus.EVALUATING],
            "underperforming_skills": status_counts[SkillStatus.UNDERPERFORMING],
            "pruned_skills": status_counts[SkillStatus.PRUNED],
            "total_evaluations": len(self.evaluation_history),
            "last_exploration": self._get_last_exploration_time(),
            "last_optimization": self._get_last_optimization_time(),
            "last_pruning": self._get_last_pruning_time(),
        }
    
    def _get_last_exploration_time(self) -> Optional[str]:
        """Get timestamp of last exploration."""
        if self.evaluation_history:
            return self.evaluation_history[-1].evaluation_time.isoformat()
        return None
    
    def _get_last_optimization_time(self) -> Optional[str]:
        """Get timestamp of last optimization."""
        # TODO: Track optimization timestamps
        return None
    
    def _get_last_pruning_time(self) -> Optional[str]:
        """Get timestamp of last pruning."""
        # TODO: Track pruning timestamps
        return None
    
    def _save_metrics(self):
        """Save metrics to persistent storage."""
        try:
            metrics_file = self.data_dir / "skill_metrics.json"
            
            # Convert to serializable format
            data = {
                skill_id: {
                    "skill_id": m.skill_id,
                    "total_uses": m.total_uses,
                    "successful_uses": m.successful_uses,
                    "failed_uses": m.failed_uses,
                    "total_execution_time": m.total_execution_time,
                    "avg_execution_time": m.avg_execution_time,
                    "last_used": m.last_used.isoformat() if m.last_used else None,
                    "first_used": m.first_used.isoformat() if m.first_used else None,
                    "success_rate": m.success_rate,
                    "cost_score": m.cost_score,
                    "utility_score": m.utility_score,
                    "quality_score": m.quality_score,
                    "overall_score": m.overall_score,
                    "status": m.status.value,
                }
                for skill_id, m in self.metrics.items()
            }
            
            with open(metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(data)} skill metrics to {metrics_file}")
            
        except Exception as e:
            logger.error(f"Error saving metrics: {e}", exc_info=True)
    
    def _load_metrics(self):
        """Load metrics from persistent storage."""
        try:
            metrics_file = self.data_dir / "skill_metrics.json"
            
            if not metrics_file.exists():
                logger.info("No existing metrics file found, starting fresh")
                return
            
            with open(metrics_file, 'r') as f:
                data = json.load(f)
            
            for skill_id, m_dict in data.items():
                self.metrics[skill_id] = SkillMetrics(
                    skill_id=m_dict["skill_id"],
                    total_uses=m_dict["total_uses"],
                    successful_uses=m_dict["successful_uses"],
                    failed_uses=m_dict["failed_uses"],
                    total_execution_time=m_dict["total_execution_time"],
                    avg_execution_time=m_dict["avg_execution_time"],
                    last_used=datetime.fromisoformat(m_dict["last_used"]) if m_dict["last_used"] else None,
                    first_used=datetime.fromisoformat(m_dict["first_used"]) if m_dict["first_used"] else None,
                    success_rate=m_dict["success_rate"],
                    cost_score=m_dict["cost_score"],
                    utility_score=m_dict["utility_score"],
                    quality_score=m_dict["quality_score"],
                    overall_score=m_dict["overall_score"],
                    status=SkillStatus(m_dict["status"]),
                )
            
            logger.info(f"Loaded {len(self.metrics)} skill metrics from {metrics_file}")
            
        except Exception as e:
            logger.error(f"Error loading metrics: {e}", exc_info=True)
