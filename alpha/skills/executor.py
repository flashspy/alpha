"""
Agent Skill Executor

Execute skills with sandboxing and security controls.
"""

import logging
import asyncio
from typing import Optional
from pathlib import Path

from rich.console import Console

from alpha.skills.base import AgentSkill, SkillResult
from alpha.skills.registry import SkillRegistry
from alpha.skills.marketplace import SkillMarketplace
from alpha.skills.installer import SkillInstaller

logger = logging.getLogger(__name__)
console = Console()


class SkillExecutor:
    """
    Skill executor with dynamic discovery and installation.

    Features:
    - Execute skills with sandboxing (TODO: implement proper sandboxing)
    - Auto-discover and install skills on-demand
    - Resource management and timeout handling
    - Security controls
    """

    def __init__(
        self,
        registry: SkillRegistry,
        marketplace: SkillMarketplace,
        installer: SkillInstaller,
        auto_install: bool = True
    ):
        self.registry = registry
        self.marketplace = marketplace
        self.installer = installer
        self.auto_install = auto_install

    async def execute(
        self,
        skill_name: str,
        timeout: Optional[int] = None,
        sandbox: bool = False,
        **kwargs
    ) -> SkillResult:
        """
        Execute a skill.

        If skill is not installed, will attempt to discover and install it
        automatically (if auto_install is enabled).

        Args:
            skill_name: Skill name
            timeout: Execution timeout in seconds
            sandbox: Whether to execute in sandbox (not yet implemented)
            **kwargs: Skill parameters

        Returns:
            Skill execution result
        """
        logger.info(f"Executing skill: {skill_name}")

        # Check if skill is installed
        skill = self.registry.get_skill(skill_name)

        if not skill and self.auto_install:
            # Skill not installed, try to discover and install
            logger.info(f"Skill {skill_name} not found, attempting auto-install...")
            success = await self._auto_install_skill(skill_name)

            if success:
                skill = self.registry.get_skill(skill_name)
            else:
                return SkillResult(
                    success=False,
                    output=None,
                    error=f"Failed to auto-install skill: {skill_name}"
                )

        if not skill:
            return SkillResult(
                success=False,
                output=None,
                error=f"Skill not found and auto-install disabled: {skill_name}"
            )

        # Execute with timeout
        try:
            if timeout:
                result = await asyncio.wait_for(
                    self.registry.execute_skill(skill_name, **kwargs),
                    timeout=timeout
                )
            else:
                result = await self.registry.execute_skill(skill_name, **kwargs)

            return result

        except asyncio.TimeoutError:
            logger.error(f"Skill execution timed out: {skill_name}")
            return SkillResult(
                success=False,
                output=None,
                error=f"Execution timed out after {timeout} seconds"
            )
        except Exception as e:
            logger.error(f"Error executing skill {skill_name}: {e}", exc_info=True)
            return SkillResult(
                success=False,
                output=None,
                error=str(e)
            )

    async def _auto_install_skill(self, skill_name: str) -> bool:
        """
        Automatically discover and install a skill.

        Args:
            skill_name: Skill name

        Returns:
            True if successful
        """
        logger.info(f"Auto-installing skill: {skill_name}")

        try:
            # Search for skill
            console.print(f"[yellow]Searching for skill: {skill_name}...[/yellow]")
            results = await self.marketplace.search(skill_name, limit=1)

            if not results:
                logger.warning(f"Skill not found in marketplace: {skill_name}")
                console.print(f"[red]Skill not found: {skill_name}[/red]")
                return False

            skill_meta = results[0]

            # Download skill
            console.print(f"[yellow]Downloading skill: {skill_name}...[/yellow]")
            skill_dir = await self.marketplace.download_skill(
                skill_name,
                self.registry.skills_dir
            )

            if not skill_dir:
                logger.error(f"Failed to download skill: {skill_name}")
                console.print(f"[red]Failed to download skill: {skill_name}[/red]")
                return False

            # Install skill
            console.print(f"[yellow]Installing skill: {skill_name}...[/yellow]")
            skill_instance = await self.installer.install(skill_dir)

            if not skill_instance:
                logger.error(f"Failed to install skill: {skill_name}")
                console.print(f"[red]Failed to install skill: {skill_name}[/red]")
                return False

            # Register skill
            console.print(f"[yellow]Registering skill: {skill_name}...[/yellow]")
            success = await self.registry.register(skill_instance)

            if success:
                logger.info(f"Successfully auto-installed skill: {skill_name}")
                console.print(f"[green]✓ Skill installed: {skill_name}[/green]")
                return True
            else:
                logger.error(f"Failed to register skill: {skill_name}")
                console.print(f"[red]Failed to register skill: {skill_name}[/red]")
                return False

        except Exception as e:
            logger.error(f"Error auto-installing skill {skill_name}: {e}", exc_info=True)
            console.print(f"[red]Error installing skill: {e}[/red]")
            return False

    async def discover_skills(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[list] = None
    ) -> list:
        """
        Discover available skills.

        Args:
            query: Search query
            category: Filter by category
            tags: Filter by tags

        Returns:
            List of skill metadata
        """
        return await self.marketplace.search(
            query=query,
            category=category,
            tags=tags
        )

    def list_installed_skills(self) -> list:
        """
        List installed skills.

        Returns:
            List of skill metadata dicts
        """
        return self.registry.list_skills()

    # TODO: Implement proper sandboxing
    # Options:
    # 1. Use separate process with restricted permissions
    # 2. Use Docker containers
    # 3. Use Python sandboxing libraries (RestrictedPython, etc.)
    # 4. Use cgroups/namespaces on Linux
    async def _execute_sandboxed(
        self,
        skill: AgentSkill,
        **kwargs
    ) -> SkillResult:
        """
        Execute skill in sandbox (not yet implemented).

        Args:
            skill: Skill instance
            **kwargs: Skill parameters

        Returns:
            Skill execution result
        """
        # For now, just execute normally
        # In production, implement proper sandboxing
        logger.warning("Sandboxed execution not yet implemented, executing normally")
        return await skill.execute(**kwargs)
