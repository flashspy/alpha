"""
Alpha - Agent Skill System

Dynamic skill discovery, installation, and execution system.
"""

from alpha.skills.base import AgentSkill, SkillMetadata, SkillResult
from alpha.skills.registry import SkillRegistry
from alpha.skills.marketplace import SkillMarketplace
from alpha.skills.installer import SkillInstaller
from alpha.skills.executor import SkillExecutor

# Auto-skill system
from alpha.skills.matcher import SkillMatcher
from alpha.skills.downloader import SkillDownloader
from alpha.skills.loader import SkillLoader
from alpha.skills.auto_manager import AutoSkillManager

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def preinstall_builtin_skills(
    registry: SkillRegistry,
    installer: SkillInstaller
) -> int:
    """
    Preinstall all builtin skills.

    Args:
        registry: Skill registry
        installer: Skill installer

    Returns:
        Number of skills successfully installed
    """
    builtin_dir = Path(__file__).parent / "builtin"

    if not builtin_dir.exists():
        logger.warning("Builtin skills directory not found")
        return 0

    skill_dirs = [d for d in builtin_dir.iterdir() if d.is_dir() and (d / "skill.yaml").exists()]

    installed_count = 0

    for skill_dir in skill_dirs:
        try:
            # Install skill without dependencies (builtin skills have no deps)
            skill = await installer.install(skill_dir, install_deps=False)

            if skill:
                # Register skill
                success = await registry.register(skill)
                if success:
                    logger.info(f"Preinstalled builtin skill: {skill.metadata.name}")
                    installed_count += 1
                else:
                    logger.warning(f"Failed to register builtin skill: {skill_dir.name}")
            else:
                logger.warning(f"Failed to install builtin skill: {skill_dir.name}")

        except Exception as e:
            logger.error(f"Error preinstalling skill {skill_dir.name}: {e}", exc_info=True)

    logger.info(f"Preinstalled {installed_count} builtin skills")
    return installed_count


__all__ = [
    "AgentSkill",
    "SkillMetadata",
    "SkillResult",
    "SkillRegistry",
    "SkillMarketplace",
    "SkillInstaller",
    "SkillExecutor",
    "preinstall_builtin_skills",
    # Auto-skill system
    "SkillMatcher",
    "SkillDownloader",
    "SkillLoader",
    "AutoSkillManager",
]
