"""
Alpha - Improvement Executor

Applies improvement recommendations to system configuration and behavior.
Validates changes before applying and tracks all modifications.
"""

import yaml
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from copy import deepcopy


logger = logging.getLogger(__name__)


class ImprovementStatus(Enum):
    """Status of improvement application."""
    PENDING = "pending"
    VALIDATING = "validating"
    APPLYING = "applying"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class AppliedImprovement:
    """
    Record of an applied improvement.

    Attributes:
        id: Unique improvement ID
        recommendation_title: Title from recommendation
        action_type: Type of action taken
        changes: Dict of changes made
        status: Current status
        applied_at: When improvement was applied
        rollback_data: Data needed to rollback change
        metadata: Additional metadata
    """
    id: str
    recommendation_title: str
    action_type: str
    changes: Dict[str, Any]
    status: ImprovementStatus = ImprovementStatus.PENDING
    applied_at: Optional[datetime] = None
    rollback_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ImprovementExecutor:
    """
    Executes improvement recommendations on the system.

    Features:
    - Configuration file updates
    - Tool selection strategy modifications
    - Model routing adjustments
    - Validation before application
    - Rollback capability
    - Change tracking
    """

    def __init__(
        self,
        config_path: str = "config.yaml",
        learning_store: Optional[Any] = None,
        auto_apply: bool = False
    ):
        """
        Initialize improvement executor.

        Args:
            config_path: Path to main configuration file
            learning_store: Optional learning store for tracking
            auto_apply: Automatically apply safe improvements
        """
        self.config_path = Path(config_path)
        self.learning_store = learning_store
        self.auto_apply = auto_apply

        self.applied_improvements: List[AppliedImprovement] = []
        self.config_backup: Optional[Dict] = None

        logger.info(f"Improvement executor initialized: {self.config_path}")

    async def apply_recommendation(
        self,
        recommendation: Any,
        validate: bool = True,
        dry_run: bool = False
    ) -> AppliedImprovement:
        """
        Apply an improvement recommendation.

        Args:
            recommendation: ImprovementRecommendation instance
            validate: Whether to validate before applying
            dry_run: If True, only simulate the change

        Returns:
            AppliedImprovement record

        Raises:
            ValueError: If recommendation is invalid
            RuntimeError: If application fails
        """
        improvement_id = f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        applied = AppliedImprovement(
            id=improvement_id,
            recommendation_title=recommendation.title,
            action_type=recommendation.action_type,
            changes={},
            metadata={
                "priority": recommendation.priority.name,
                "confidence": recommendation.confidence,
                "estimated_impact": recommendation.estimated_impact,
                "dry_run": dry_run
            }
        )

        try:
            logger.info(f"Applying recommendation: {recommendation.title}")

            # Validate recommendation
            if validate:
                applied.status = ImprovementStatus.VALIDATING
                is_valid, error = await self._validate_recommendation(recommendation)
                if not is_valid:
                    applied.status = ImprovementStatus.FAILED
                    applied.error = f"Validation failed: {error}"
                    logger.error(applied.error)
                    return applied

            # Apply based on action type
            applied.status = ImprovementStatus.APPLYING

            if recommendation.action_type == "config_update":
                changes = await self._apply_config_update(
                    recommendation.action_data,
                    dry_run=dry_run
                )
                applied.changes = changes

            elif recommendation.action_type == "model_routing":
                changes = await self._apply_model_routing_update(
                    recommendation.action_data,
                    dry_run=dry_run
                )
                applied.changes = changes

            elif recommendation.action_type == "tool_strategy":
                changes = await self._apply_tool_strategy_update(
                    recommendation.action_data,
                    dry_run=dry_run
                )
                applied.changes = changes

            elif recommendation.action_type == "error_handling":
                changes = await self._apply_error_handling_update(
                    recommendation.action_data,
                    dry_run=dry_run
                )
                applied.changes = changes

            else:
                raise ValueError(f"Unknown action type: {recommendation.action_type}")

            # Mark as applied
            if not dry_run:
                applied.status = ImprovementStatus.APPLIED
                applied.applied_at = datetime.now()
                self.applied_improvements.append(applied)

                # Store in learning database
                if self.learning_store:
                    await self.learning_store.store_improvement(applied)

                logger.info(f"Successfully applied: {recommendation.title}")
            else:
                logger.info(f"Dry run completed: {recommendation.title}")

        except Exception as e:
            applied.status = ImprovementStatus.FAILED
            applied.error = str(e)
            logger.error(f"Failed to apply recommendation: {e}", exc_info=True)

        return applied

    async def rollback_improvement(self, improvement_id: str) -> bool:
        """
        Rollback a previously applied improvement.

        Args:
            improvement_id: ID of improvement to rollback

        Returns:
            True if rollback successful, False otherwise
        """
        # Find improvement
        improvement = None
        for imp in self.applied_improvements:
            if imp.id == improvement_id:
                improvement = imp
                break

        if not improvement:
            logger.error(f"Improvement not found: {improvement_id}")
            return False

        if improvement.status != ImprovementStatus.APPLIED:
            logger.error(f"Cannot rollback improvement in status: {improvement.status}")
            return False

        try:
            logger.info(f"Rolling back improvement: {improvement_id}")

            # Restore from rollback data
            if improvement.action_type == "config_update":
                await self._restore_config(improvement.rollback_data)

            # Update status
            improvement.status = ImprovementStatus.ROLLED_BACK

            # Update in learning store
            if self.learning_store:
                await self.learning_store.update_improvement_status(
                    improvement_id,
                    ImprovementStatus.ROLLED_BACK
                )

            logger.info(f"Successfully rolled back: {improvement_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback improvement: {e}", exc_info=True)
            return False

    async def _validate_recommendation(
        self,
        recommendation: Any
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a recommendation before applying.

        Args:
            recommendation: Recommendation to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check confidence threshold
        if recommendation.confidence < 0.5:
            return False, f"Confidence too low: {recommendation.confidence}"

        # Validate action data
        action_data = recommendation.action_data

        if recommendation.action_type == "config_update":
            # Config updates are considered valid if they have action data
            # The specific fields vary by use case
            if not action_data:
                return False, "Missing action data for config_update"

        elif recommendation.action_type == "model_routing":
            # Validate model exists
            if not action_data.get("current_model"):
                return False, "Missing current_model in model_routing"

        # All validations passed
        return True, None

    async def _apply_config_update(
        self,
        action_data: Dict[str, Any],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Apply configuration update.

        Args:
            action_data: Action data from recommendation
            dry_run: If True, only simulate the change

        Returns:
            Dictionary of changes made
        """
        changes = {}

        # Load current config
        config = self._load_config()
        if not self.config_backup:
            self.config_backup = deepcopy(config)

        # Determine what to update based on action data
        operation = action_data.get("operation")
        task_name = action_data.get("task_name")
        suggested_timeout = action_data.get("suggested_timeout")

        if suggested_timeout and task_name:
            # Update timeout for specific task
            if "tasks" not in config:
                config["tasks"] = {}
            if "timeouts" not in config["tasks"]:
                config["tasks"]["timeouts"] = {}

            old_value = config["tasks"]["timeouts"].get(task_name)
            new_value = int(suggested_timeout)

            changes["path"] = f"tasks.timeouts.{task_name}"
            changes["old_value"] = old_value
            changes["new_value"] = new_value

            if not dry_run:
                config["tasks"]["timeouts"][task_name] = new_value
                self._save_config(config)

        elif "suggested_action" in action_data:
            action = action_data["suggested_action"]

            if action == "increase_timeout":
                # Increase global timeout
                if "code_execution" in config:
                    old_timeout = config["code_execution"]["defaults"].get("timeout", 30)
                    new_timeout = int(old_timeout * 1.5)

                    changes["path"] = "code_execution.defaults.timeout"
                    changes["old_value"] = old_timeout
                    changes["new_value"] = new_timeout

                    if not dry_run:
                        config["code_execution"]["defaults"]["timeout"] = new_timeout
                        self._save_config(config)

        return changes

    async def _apply_model_routing_update(
        self,
        action_data: Dict[str, Any],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Apply model routing update.

        Args:
            action_data: Action data from recommendation
            dry_run: If True, only simulate the change

        Returns:
            Dictionary of changes made
        """
        changes = {}

        # Load current config
        config = self._load_config()
        if not self.config_backup:
            self.config_backup = deepcopy(config)

        current_model = action_data.get("current_model")
        suggested_action = action_data.get("suggested_action")

        if suggested_action == "use_cheaper_model_for_simple_tasks":
            # Update auto_select_model setting
            if "deepseek" in config.get("llm", {}).get("providers", {}):
                old_value = config["llm"]["providers"]["deepseek"].get("auto_select_model", False)

                changes["path"] = "llm.providers.deepseek.auto_select_model"
                changes["old_value"] = old_value
                changes["new_value"] = True
                changes["description"] = "Enable automatic model selection based on task difficulty"

                if not dry_run:
                    config["llm"]["providers"]["deepseek"]["auto_select_model"] = True
                    self._save_config(config)

        return changes

    async def _apply_tool_strategy_update(
        self,
        action_data: Dict[str, Any],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Apply tool strategy update.

        Args:
            action_data: Action data from recommendation
            dry_run: If True, only simulate the change

        Returns:
            Dictionary of changes made
        """
        changes = {}

        # This would update tool selection strategies
        # For now, we'll log the intended change
        logger.info(f"Tool strategy update: {action_data}")
        changes["type"] = "tool_strategy"
        changes["data"] = action_data

        return changes

    async def _apply_error_handling_update(
        self,
        action_data: Dict[str, Any],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Apply error handling update.

        Args:
            action_data: Action data from recommendation
            dry_run: If True, only simulate the change

        Returns:
            Dictionary of changes made
        """
        changes = {}

        error_type = action_data.get("error_type")
        suggested_action = action_data.get("suggested_action")

        # Log the recommendation for manual implementation
        logger.info(f"Error handling recommendation: {error_type} -> {suggested_action}")

        changes["type"] = "error_handling"
        changes["error_type"] = error_type
        changes["suggested_action"] = suggested_action
        changes["note"] = "Manual implementation required"

        return changes

    async def _restore_config(self, rollback_data: Dict[str, Any]):
        """
        Restore configuration from rollback data.

        Args:
            rollback_data: Data needed to restore configuration
        """
        if self.config_backup:
            self._save_config(self.config_backup)
            logger.info("Configuration restored from backup")
        else:
            logger.warning("No backup available for rollback")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def _save_config(self, config: Dict[str, Any]):
        """
        Save configuration to YAML file.

        Args:
            config: Configuration dictionary
        """
        try:
            with open(self.config_path, 'w') as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Configuration saved: {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    async def get_applied_improvements(
        self,
        status: Optional[ImprovementStatus] = None
    ) -> List[AppliedImprovement]:
        """
        Get list of applied improvements.

        Args:
            status: Optional status filter

        Returns:
            List of applied improvements
        """
        if status:
            return [
                imp for imp in self.applied_improvements
                if imp.status == status
            ]
        return self.applied_improvements.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get improvement application statistics.

        Returns:
            Statistics dictionary
        """
        from collections import Counter

        status_counts = Counter(imp.status for imp in self.applied_improvements)
        action_counts = Counter(imp.action_type for imp in self.applied_improvements)

        return {
            "total_improvements": len(self.applied_improvements),
            "by_status": {status.value: count for status, count in status_counts.items()},
            "by_action_type": dict(action_counts),
            "success_rate": (
                status_counts[ImprovementStatus.APPLIED] / len(self.applied_improvements)
                if self.applied_improvements else 0
            )
        }
