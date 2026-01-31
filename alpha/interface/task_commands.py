"""
Task Decomposition CLI Commands (REQ-8.1.5)

Provides CLI commands for task decomposition management:
- task decompose <query> - Manual decomposition trigger
- task status - View current task execution status
- task cancel - Cancel ongoing decomposed task
- task history - View recent task decomposition history
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from alpha.core.task_decomposition.decomposer import TaskDecomposer
from alpha.core.task_decomposition.tracker import ProgressTracker
from alpha.core.task_decomposition.coordinator import ExecutionCoordinator
from alpha.core.task_decomposition.storage import ProgressStorage
from alpha.interface.progress_display import ProgressDisplay
from alpha.core.task_decomposition.models import TaskStatus

logger = logging.getLogger(__name__)


class TaskCommands:
    """
    CLI command handlers for task decomposition system.

    Provides interactive commands for:
    - Manual task decomposition and execution
    - Status checking of running tasks
    - Task cancellation
    - Execution history browsing
    """

    def __init__(
        self,
        decomposer: TaskDecomposer,
        storage: ProgressStorage,
        tool_registry,
        llm_provider,
        resilience_engine=None,
        console: Optional[Console] = None
    ):
        """
        Initialize task commands handler.

        Args:
            decomposer: TaskDecomposer instance
            storage: ProgressStorage for persistence
            tool_registry: Tool registry for execution
            llm_provider: LLM provider for task execution
            resilience_engine: Optional resilience engine for failure handling
            console: Rich console for output (creates new if not provided)
        """
        self.decomposer = decomposer
        self.storage = storage
        self.tool_registry = tool_registry
        self.llm_provider = llm_provider
        self.resilience_engine = resilience_engine
        self.console = console or Console()

        # Track current execution
        self.current_coordinator: Optional[ExecutionCoordinator] = None
        self.current_tracker: Optional[ProgressTracker] = None
        self.current_display: Optional[ProgressDisplay] = None

        logger.info("TaskCommands initialized")

    async def cmd_task_decompose(self, query: str, auto_approve: bool = False) -> bool:
        """
        Decompose and execute a task.

        Args:
            query: User request to decompose
            auto_approve: Skip user approval (for testing)

        Returns:
            True if execution successful, False otherwise
        """
        try:
            self.console.print(f"\n[bold cyan]🤖 Analyzing task:[/bold cyan] {query}")

            # Step 1: Analyze complexity
            with self.console.status("[bold yellow]Analyzing complexity...[/bold yellow]"):
                analysis = self.decomposer.analyze_task(query, {})

            self.console.print(
                f"[dim]Complexity: {analysis.complexity_level.value} | "
                f"Estimated: {analysis.estimated_duration:.0f}s[/dim]"
            )

            # Check if decomposition needed
            if not analysis.decomposition_needed:
                self.console.print(
                    "[yellow]ℹ️  Task is simple enough to execute directly (no decomposition needed)[/yellow]"
                )
                return False

            # Step 2: Decompose into task tree
            with self.console.status("[bold yellow]Breaking down into sub-tasks...[/bold yellow]"):
                task_tree = self.decomposer.decompose_task(query, {})

            # Step 3: Show preview
            self._show_decomposition_preview(task_tree)

            # Step 4: Get user approval
            if not auto_approve:
                approved = Confirm.ask(
                    "\n[bold]Proceed with this decomposition?[/bold]",
                    default=True
                )
                if not approved:
                    self.console.print("[yellow]Task decomposition cancelled by user[/yellow]")
                    return False

            # Step 5: Execute
            self.console.print("\n[bold green]🚀 Starting execution...[/bold green]\n")

            # Initialize tracker and display
            self.current_tracker = ProgressTracker(task_tree, self.storage)
            self.current_display = ProgressDisplay(self.current_tracker, use_rich=True)

            # Initialize coordinator
            self.current_coordinator = ExecutionCoordinator(
                task_tree=task_tree,
                progress_tracker=self.current_tracker,
                tool_registry=self.tool_registry,
                llm_provider=self.llm_provider,
                resilience_engine=self.resilience_engine
            )

            # Start live display
            self.current_display.start_live_display()

            try:
                # Execute task tree
                result = await self.current_coordinator.execute()

                # Stop live display
                self.current_display.stop_live_display()

                # Show final result
                if result.success:
                    self.console.print("\n[bold green]✅ Task completed successfully![/bold green]")
                    return True
                else:
                    self.console.print(
                        f"\n[bold red]❌ Task failed:[/bold red] {result.error}"
                    )
                    return False

            finally:
                # Cleanup
                self.current_coordinator = None
                self.current_tracker = None
                self.current_display = None

        except Exception as e:
            logger.error(f"Task decomposition failed: {e}", exc_info=True)
            self.console.print(f"[bold red]Error during task execution:[/bold red] {e}")
            return False

    def _show_decomposition_preview(self, task_tree):
        """Show task decomposition preview."""
        # Create preview table
        table = Table(
            title="📋 Task Decomposition Preview",
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("#", style="dim", width=6)
        table.add_column("Task Description", style="")
        table.add_column("Est. Time", justify="right", style="dim", width=12)

        # Add all sub-tasks
        total_est = 0
        for task in task_tree.sub_tasks.values():
            indent = "  " * task.depth
            desc = f"{indent}{task.description}"
            est_time = f"{task.estimated_duration:.0f}s"
            total_est += task.estimated_duration

            table.add_row(task.id, desc, est_time)

        # Add footer with total
        table.add_row(
            "",
            "[bold]Total estimated time:[/bold]",
            f"[bold]{total_est:.0f}s[/bold]"
        )

        self.console.print(table)

        # Show execution strategy
        strategy_text = f"[dim]Execution strategy: {task_tree.execution_strategy.value}[/dim]"
        self.console.print(strategy_text)

    def cmd_task_status(self):
        """
        Display status of currently executing task.
        """
        if self.current_tracker is None:
            self.console.print("[yellow]No task currently executing[/yellow]")

            # Show recent sessions from storage
            recent_sessions = self.storage.list_sessions(limit=5)
            if recent_sessions:
                self.console.print("\n[bold]Recent task executions:[/bold]")
                table = Table(show_header=True)
                table.add_column("Session ID", style="dim", no_wrap=True)
                table.add_column("Request")
                table.add_column("Status")
                table.add_column("Started At")

                for session in recent_sessions:
                    status_color = {
                        "completed": "green",
                        "running": "yellow",
                        "failed": "red",
                        "pending": "dim"
                    }.get(session["status"], "white")

                    table.add_row(
                        session["session_id"][:12],
                        session["user_request"][:50],
                        f"[{status_color}]{session['status']}[/{status_color}]",
                        session.get("started_at", "N/A")
                    )

                self.console.print(table)
            else:
                self.console.print("[dim]No recent task executions found[/dim]")

            return

        # Show current progress
        if self.current_display:
            self.current_display.print_progress()
        else:
            # Fallback: show summary
            summary = self.current_tracker.get_progress_summary()
            self.console.print(
                f"[bold]Progress:[/bold] {summary.overall_progress * 100:.1f}% "
                f"({summary.completed_count}/{summary.completed_count + summary.pending_count} tasks)"
            )
            self.console.print(
                f"[dim]Elapsed: {summary.elapsed_time:.0f}s | "
                f"Remaining: ~{summary.estimated_remaining:.0f}s[/dim]"
            )
            if summary.current_task_description:
                self.console.print(f"[yellow]Current: {summary.current_task_description}[/yellow]")

    def cmd_task_cancel(self) -> bool:
        """
        Cancel currently executing task.

        Returns:
            True if task was cancelled, False if no task running
        """
        if self.current_coordinator is None:
            self.console.print("[yellow]No task currently executing[/yellow]")
            return False

        # Confirm cancellation
        confirmed = Confirm.ask(
            "[bold red]Are you sure you want to cancel the current task?[/bold red]",
            default=False
        )

        if not confirmed:
            self.console.print("[dim]Cancellation aborted[/dim]")
            return False

        # Cancel execution
        try:
            self.current_coordinator.cancel()
            self.console.print("[yellow]⚠️  Task cancellation requested[/yellow]")

            # Stop live display
            if self.current_display:
                self.current_display.stop_live_display()

            # Cleanup
            self.current_coordinator = None
            self.current_tracker = None
            self.current_display = None

            self.console.print("[green]✓ Task cancelled successfully[/green]")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel task: {e}", exc_info=True)
            self.console.print(f"[red]Error cancelling task: {e}[/red]")
            return False

    def cmd_task_history(self, limit: int = 10):
        """
        Show task execution history.

        Args:
            limit: Maximum number of sessions to show
        """
        sessions = self.storage.list_sessions(limit=limit)

        if not sessions:
            self.console.print("[dim]No task execution history found[/dim]")
            return

        # Create history table
        table = Table(
            title=f"📜 Task Execution History (Last {min(len(sessions), limit)})",
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("Session ID", style="dim", no_wrap=True, width=14)
        table.add_column("Request", style="", width=40)
        table.add_column("Status", width=12)
        table.add_column("Tasks", justify="right", width=8)
        table.add_column("Duration", justify="right", width=10)
        table.add_column("Started At", style="dim", width=20)

        for session in sessions:
            # Status with color
            status = session["status"]
            status_color = {
                "completed": "green",
                "running": "yellow",
                "failed": "red",
                "pending": "dim"
            }.get(status, "white")
            status_text = f"[{status_color}]{status}[/{status_color}]"

            # Calculate duration
            started = session.get("started_at")
            completed = session.get("completed_at")
            if started and completed:
                try:
                    start_dt = datetime.fromisoformat(started)
                    end_dt = datetime.fromisoformat(completed)
                    duration = (end_dt - start_dt).total_seconds()
                    duration_text = f"{duration:.0f}s"
                except:
                    duration_text = "N/A"
            else:
                duration_text = "N/A"

            # Task count (from task_tree JSON if available)
            task_count = "N/A"
            if "task_tree" in session and session["task_tree"]:
                try:
                    import json
                    tree = json.loads(session["task_tree"]) if isinstance(session["task_tree"], str) else session["task_tree"]
                    task_count = str(len(tree.get("sub_tasks", [])))
                except:
                    pass

            table.add_row(
                session["session_id"][:12] + "...",
                session["user_request"][:40],
                status_text,
                task_count,
                duration_text,
                started or "N/A"
            )

        self.console.print(table)


def integrate_task_commands_to_cli(cli_instance, task_commands: TaskCommands):
    """
    Integrate task commands into existing CLI instance.

    Adds command handlers to CLI for:
    - /task decompose <query>
    - /task status
    - /task cancel
    - /task history

    Args:
        cli_instance: Alpha CLI instance
        task_commands: TaskCommands handler instance
    """
    # Store reference
    cli_instance.task_commands = task_commands

    # Add to CLI's command handlers (if it has one)
    # This would integrate with the existing command dispatch system
    logger.info("Task decomposition commands integrated into CLI")
