"""
Skill Management CLI Commands (REQ-9.1)

Provides CLI commands for skill evolution management:
- skill status - View skill performance and health metrics
- skill explore - Manual marketplace exploration trigger
- skill prune - Prune underperforming skills (with dry-run)
- skill rank - View skill performance rankings
- skill gaps - View detected skill gaps
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

logger = logging.getLogger(__name__)


class SkillCommands:
    """
    CLI command handlers for skill evolution system.

    Provides interactive commands for:
    - Viewing skill performance metrics
    - Manual skill exploration
    - Skill pruning (manual and dry-run)
    - Performance rankings
    - Skill gap analysis
    """

    def __init__(
        self,
        performance_tracker,
        optimizer,
        console: Optional[Console] = None
    ):
        """
        Initialize skill commands handler.

        Args:
            performance_tracker: PerformanceTracker instance
            optimizer: SkillOptimizer instance
            console: Rich console for output (creates new if not provided)
        """
        self.performance_tracker = performance_tracker
        self.optimizer = optimizer
        self.console = console or Console()

        logger.info("SkillCommands initialized")

    async def cmd_skill_status(self, skill_id: Optional[str] = None) -> bool:
        """
        Display skill performance status.

        Args:
            skill_id: Optional specific skill to show (shows all if None)

        Returns:
            True if successful
        """
        try:
            self.console.print("\n[bold cyan]Skill Performance Status[/bold cyan]\n")

            if skill_id:
                # Show specific skill
                stats = self.performance_tracker.get_skill_stats(skill_id)
                if not stats:
                    self.console.print(f"[yellow]No data found for skill: {skill_id}[/yellow]")
                    return False

                self._display_skill_details(stats)
            else:
                # Show all skills
                all_stats = self.performance_tracker.get_all_stats()
                if not all_stats:
                    self.console.print("[yellow]No skill performance data available[/yellow]")
                    return True

                self._display_skill_table(all_stats)

            return True

        except Exception as e:
            self.console.print(f"[red]Error displaying skill status: {e}[/red]")
            logger.error(f"Error in cmd_skill_status: {e}", exc_info=True)
            return False

    def _display_skill_details(self, stats):
        """Display detailed stats for a single skill."""
        table = Table(title=f"Skill: {stats.skill_id}", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Total Executions", str(stats.total_executions))
        table.add_row("Success Rate", f"{stats.success_rate:.1%}")
        table.add_row("Recent Success Rate", f"{stats.recent_success_rate:.1%}")
        table.add_row("Avg Execution Time", f"{stats.avg_execution_time:.2f}s")
        table.add_row("Total Cost", f"${stats.total_cost:.4f}")
        table.add_row("ROI Score", f"{stats.roi_score:.2f}")
        table.add_row("Value Score", f"{stats.value_score:.2f}")
        table.add_row("Usage Frequency", f"{stats.usage_frequency:.2f}/day")

        if stats.last_used:
            days_ago = (datetime.now() - stats.last_used).days
            table.add_row("Last Used", f"{days_ago} days ago")

        if stats.last_error:
            table.add_row("Last Error", stats.last_error)

        self.console.print(table)

    def _display_skill_table(self, all_stats):
        """Display overview table of all skills."""
        table = Table(title="Skill Performance Overview")
        table.add_column("Skill ID", style="cyan")
        table.add_column("Uses", justify="right")
        table.add_column("Success", justify="right")
        table.add_column("ROI", justify="right")
        table.add_column("Avg Time", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("Last Used", justify="right")

        # Sort by ROI descending
        sorted_stats = sorted(
            all_stats.values(),
            key=lambda s: s.roi_score,
            reverse=True
        )

        for stats in sorted_stats[:20]:  # Top 20
            days_ago = (
                (datetime.now() - stats.last_used).days
                if stats.last_used else 999
            )

            # Color code success rate
            success_color = (
                "green" if stats.success_rate >= 0.8
                else "yellow" if stats.success_rate >= 0.5
                else "red"
            )

            table.add_row(
                stats.skill_id[:30],
                str(stats.total_executions),
                f"[{success_color}]{stats.success_rate:.0%}[/{success_color}]",
                f"{stats.roi_score:.2f}",
                f"{stats.avg_execution_time:.2f}s",
                f"${stats.total_cost:.3f}",
                f"{days_ago}d"
            )

        self.console.print(table)

    async def cmd_skill_explore(self, auto_approve: bool = False) -> bool:
        """
        Manually trigger marketplace exploration.

        Args:
            auto_approve: Auto-approve skill installations

        Returns:
            True if successful
        """
        try:
            self.console.print("\n[bold cyan]Exploring Skill Marketplace[/bold cyan]\n")

            if not auto_approve:
                proceed = Confirm.ask("Explore marketplace for new skills?")
                if not proceed:
                    self.console.print("[yellow]Exploration cancelled[/yellow]")
                    return False

            result = await self.optimizer.explore_marketplace()

            self.console.print(f"\n[green]✓ Exploration Complete[/green]")
            self.console.print(f"  Skills Discovered: {result.skills_discovered}")
            self.console.print(f"  Skills Evaluated: {result.skills_evaluated}")
            self.console.print(f"  Recommendations: {len(result.recommendations)}")

            if result.recommendations:
                self.console.print("\n[bold]Recommendations:[/bold]")
                for rec in result.recommendations[:5]:  # Top 5
                    self.console.print(
                        f"  • {rec.skill_id}: {rec.reason} "
                        f"(priority: {rec.priority:.2f})"
                    )

            if result.errors:
                self.console.print(f"\n[yellow]Errors: {len(result.errors)}[/yellow]")

            return True

        except Exception as e:
            self.console.print(f"[red]Error during exploration: {e}[/red]")
            logger.error(f"Error in cmd_skill_explore: {e}", exc_info=True)
            return False

    async def cmd_skill_prune(self, dry_run: bool = True) -> bool:
        """
        Prune underperforming skills.

        Args:
            dry_run: If True, only simulate pruning

        Returns:
            True if successful
        """
        try:
            mode = "DRY RUN" if dry_run else "LIVE"
            self.console.print(f"\n[bold cyan]Skill Pruning ({mode})[/bold cyan]\n")

            if not dry_run:
                proceed = Confirm.ask(
                    "[bold red]WARNING:[/bold red] This will DELETE skill files. Continue?"
                )
                if not proceed:
                    self.console.print("[yellow]Pruning cancelled[/yellow]")
                    return False

            result = await self.optimizer.prune_skills(dry_run=dry_run)

            self.console.print(f"\n[green]✓ Pruning Complete[/green]")
            self.console.print(f"  Skills Evaluated: {result.skills_evaluated}")
            self.console.print(f"  Skills Pruned: {result.skills_pruned}")

            if result.pruned_skills:
                self.console.print("\n[bold]Pruned Skills:[/bold]")
                for skill_id in result.pruned_skills:
                    self.console.print(f"  • {skill_id}")

            return True

        except Exception as e:
            self.console.print(f"[red]Error during pruning: {e}[/red]")
            logger.error(f"Error in cmd_skill_prune: {e}", exc_info=True)
            return False

    async def cmd_skill_rank(self, top_n: int = 10) -> bool:
        """
        Display skill performance rankings.

        Args:
            top_n: Number of top skills to show

        Returns:
            True if successful
        """
        try:
            self.console.print("\n[bold cyan]Skill Performance Rankings[/bold cyan]\n")

            top_performers = self.performance_tracker.get_top_performers(
                limit=top_n
            )

            if not top_performers:
                self.console.print("[yellow]No performance data available[/yellow]")
                return True

            table = Table(title=f"Top {top_n} Performing Skills")
            table.add_column("Rank", justify="right", style="cyan")
            table.add_column("Skill ID")
            table.add_column("ROI Score", justify="right")
            table.add_column("Success Rate", justify="right")
            table.add_column("Uses", justify="right")
            table.add_column("Avg Time", justify="right")

            for i, stats in enumerate(top_performers, 1):
                table.add_row(
                    str(i),
                    stats.skill_id[:40],
                    f"{stats.roi_score:.2f}",
                    f"{stats.success_rate:.0%}",
                    str(stats.total_executions),
                    f"{stats.avg_execution_time:.2f}s"
                )

            self.console.print(table)
            return True

        except Exception as e:
            self.console.print(f"[red]Error displaying rankings: {e}[/red]")
            logger.error(f"Error in cmd_skill_rank: {e}", exc_info=True)
            return False

    async def cmd_skill_gaps(self, min_priority: float = 0.3) -> bool:
        """
        Display detected skill gaps.

        Args:
            min_priority: Minimum priority score for gaps to show

        Returns:
            True if successful
        """
        try:
            self.console.print("\n[bold cyan]Detected Skill Gaps[/bold cyan]\n")

            gaps = self.performance_tracker.get_skill_gaps(
                min_priority=min_priority
            )

            if not gaps:
                self.console.print("[green]No significant skill gaps detected[/green]")
                return True

            table = Table(title="Skill Gap Analysis")
            table.add_column("Priority", justify="right", style="yellow")
            table.add_column("Missing Capability")
            table.add_column("Task Description")
            table.add_column("Failures", justify="right")

            for gap in gaps[:10]:  # Top 10
                table.add_row(
                    f"{gap.priority_score:.2f}",
                    gap.missing_capability[:40],
                    gap.task_description[:50],
                    str(gap.failure_count)
                )

            self.console.print(table)

            # Suggestions
            self.console.print(
                "\n[dim]Tip: Use 'skill explore' to find skills "
                "that might fill these gaps[/dim]"
            )

            return True

        except Exception as e:
            self.console.print(f"[red]Error displaying gaps: {e}[/red]")
            logger.error(f"Error in cmd_skill_gaps: {e}", exc_info=True)
            return False
