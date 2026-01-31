"""
ProgressDisplay - CLI visualization for task decomposition progress (REQ-8.1.4)

Provides real-time visual feedback of task execution progress with:
- Hierarchical task tree display
- Progress bars and percentages
- Status icons (✅ 🔄 ⏸️ ❌ ⏭️)
- Time estimates (elapsed and remaining)
- Intermediate results/insights
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta

from alpha.core.task_decomposition.models import (
    TaskStatus,
    TaskTree,
    SubTask,
    ProgressSummary
)
from alpha.core.task_decomposition.tracker import ProgressTracker

logger = logging.getLogger(__name__)


class ProgressDisplay:
    """
    Renders task decomposition progress in CLI with real-time updates.

    Features:
    - Hierarchical tree visualization with indentation
    - Progress bar with percentage
    - Status icons for each task
    - Time tracking (elapsed, estimated remaining)
    - Intermediate insights display
    - Support for both rich and simple terminal output
    """

    # Status icons mapping
    STATUS_ICONS = {
        TaskStatus.COMPLETED: "✅",
        TaskStatus.IN_PROGRESS: "🔄",
        TaskStatus.PENDING: "⏸️",
        TaskStatus.FAILED: "❌",
        TaskStatus.SKIPPED: "⏭️",
    }

    # Rich library support (optional)
    _rich_available = False
    try:
        from rich.console import Console
        from rich.live import Live
        from rich.table import Table
        from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
        from rich.tree import Tree
        from rich.panel import Panel
        _rich_available = True
    except ImportError:
        pass

    def __init__(self, tracker: ProgressTracker, use_rich: bool = True):
        """
        Initialize progress display.

        Args:
            tracker: ProgressTracker instance
            use_rich: Use rich library for enhanced formatting (if available)
        """
        self.tracker = tracker
        self.use_rich = use_rich and self._rich_available

        if self.use_rich:
            self.console = self.Console()
            self._live = None

        logger.info(
            f"ProgressDisplay initialized (rich={'enabled' if self.use_rich else 'disabled'})"
        )

    def get_status_icon(self, status: TaskStatus) -> str:
        """
        Get emoji icon for task status.

        Args:
            status: TaskStatus enum value

        Returns:
            Emoji icon string
        """
        return self.STATUS_ICONS.get(status, "❓")

    def format_duration(self, seconds: Optional[float]) -> str:
        """
        Format duration in human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string (e.g., "2m 30s", "1h 15m")
        """
        if seconds is None or seconds < 0:
            return "unknown"

        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"

    def _render_progress_bar_simple(self, progress: float, width: int = 40) -> str:
        """
        Render simple ASCII progress bar.

        Args:
            progress: Progress value (0.0 to 1.0)
            width: Bar width in characters

        Returns:
            ASCII progress bar string
        """
        filled = int(width * progress)
        empty = width - filled
        percentage = int(progress * 100)
        bar = "━" * filled + "─" * empty
        return f"{bar} {percentage}%"

    def _render_task_simple(self, task: SubTask, indent_level: int = 0) -> str:
        """
        Render single task in simple text format.

        Args:
            task: SubTask to render
            indent_level: Indentation level

        Returns:
            Formatted task string
        """
        indent = "    " * indent_level
        icon = self.get_status_icon(task.status)

        # Basic task info
        task_str = f"{indent}{icon} [{task.id}] {task.description}"

        # Add timing info if available
        if task.actual_duration is not None:
            task_str += f" ({self.format_duration(task.actual_duration)})"
        elif task.status == TaskStatus.IN_PROGRESS and task.started_at:
            elapsed = (datetime.now() - task.started_at).total_seconds()
            task_str += f" (running {self.format_duration(elapsed)}...)"

        # Add error info if failed
        if task.status == TaskStatus.FAILED and task.error:
            task_str += f"\n{indent}    ❗ Error: {task.error}"

        # Add result preview if completed
        if task.status == TaskStatus.COMPLETED and task.result:
            result_preview = str(task.result)[:80]
            if len(str(task.result)) > 80:
                result_preview += "..."
            task_str += f"\n{indent}    └─ {result_preview}"

        return task_str

    def _build_task_tree_simple(self, task_tree: TaskTree) -> List[str]:
        """
        Build hierarchical task tree display (simple format).

        Args:
            task_tree: TaskTree to render

        Returns:
            List of formatted lines
        """
        lines = []

        # Group tasks by parent
        tasks_by_parent = {}
        for task in task_tree.sub_tasks.values():
            parent_id = task.parent_id or "root"
            if parent_id not in tasks_by_parent:
                tasks_by_parent[parent_id] = []
            tasks_by_parent[parent_id].append(task)

        def render_subtree(parent_id: str, depth: int = 0):
            """Recursively render task subtree"""
            children = tasks_by_parent.get(parent_id, [])
            for task in children:
                lines.append(self._render_task_simple(task, depth))
                # Recurse for children
                render_subtree(task.id, depth + 1)

        # Start with root tasks
        render_subtree("root", 0)

        return lines

    def render_simple(self) -> str:
        """
        Render progress in simple text format (no rich library).

        Returns:
            Formatted progress display string
        """
        task_tree = self.tracker.task_tree
        summary = self.tracker.get_progress_summary()

        lines = []

        # Header
        lines.append("=" * 60)
        lines.append(f"🎯 Task: {task_tree.user_request}")
        lines.append("=" * 60)

        # Overall progress bar
        progress_bar = self._render_progress_bar_simple(summary.overall_progress)
        lines.append(f"\n{progress_bar}")
        lines.append(
            f"   ({summary.completed_count}/{len(task_tree.sub_tasks)} tasks complete)"
        )

        # Task tree
        lines.append("\n📋 Task Breakdown:\n")
        lines.extend(self._build_task_tree_simple(task_tree))

        # Time summary
        lines.append("\n" + "─" * 60)
        elapsed_str = self.format_duration(summary.elapsed_time)
        remaining_str = self.format_duration(summary.estimated_remaining)
        lines.append(f"⏱️  Elapsed: {elapsed_str} | Estimated remaining: {remaining_str}")

        # Current task/phase
        if summary.current_task_description:
            lines.append(f"\n💡 Current: {summary.current_task_description}")

        # Status counts
        if summary.failed_count > 0:
            lines.append(f"\n⚠️  {summary.failed_count} task(s) failed")
        if summary.skipped_count > 0:
            lines.append(f"⏭️  {summary.skipped_count} task(s) skipped")

        lines.append("=" * 60)

        return "\n".join(lines)

    def _build_task_tree_rich(self, task_tree: TaskTree):
        """
        Build hierarchical task tree using rich Tree widget.

        Args:
            task_tree: TaskTree to render

        Returns:
            Rich Tree object
        """
        if not self.use_rich:
            raise RuntimeError("Rich library not available")

        # Create root tree node
        tree = self.Tree(f"🎯 [bold]{task_tree.user_request}[/bold]")

        # Group tasks by parent
        tasks_by_parent = {}
        for task in task_tree.sub_tasks.values():
            parent_id = task.parent_id or "root"
            if parent_id not in tasks_by_parent:
                tasks_by_parent[parent_id] = []
            tasks_by_parent[parent_id].append(task)

        # Recursive tree building
        def add_subtree(parent_node, parent_id: str):
            children = tasks_by_parent.get(parent_id, [])
            for task in children:
                # Format task label
                icon = self.get_status_icon(task.status)
                label = f"{icon} [{task.id}] {task.description}"

                # Add timing
                if task.actual_duration is not None:
                    label += f" [dim]({self.format_duration(task.actual_duration)})[/dim]"
                elif task.status == TaskStatus.IN_PROGRESS and task.started_at:
                    elapsed = (datetime.now() - task.started_at).total_seconds()
                    label += f" [yellow](running {self.format_duration(elapsed)}...)[/yellow]"

                # Add error
                if task.status == TaskStatus.FAILED and task.error:
                    label += f"\n    [red]❗ Error: {task.error}[/red]"

                # Create node
                node = parent_node.add(label)

                # Recurse for children
                add_subtree(node, task.id)

        add_subtree(tree, "root")

        return tree

    def render_rich(self):
        """
        Render progress using rich library (enhanced format).

        Returns:
            Rich renderable object
        """
        if not self.use_rich:
            raise RuntimeError("Rich library not available")

        task_tree = self.tracker.task_tree
        summary = self.tracker.get_progress_summary()

        # Create main table
        table = self.Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Content", no_wrap=False)

        # Progress bar
        progress_pct = int(summary.overall_progress * 100)
        progress_text = (
            f"[bold]Progress:[/bold] {summary.completed_count}/{len(task_tree.sub_tasks)} "
            f"tasks complete ({progress_pct}%)"
        )
        table.add_row(progress_text)

        # Progress bar widget
        from rich.progress import Progress as RichProgress, BarColumn, TextColumn
        progress_bar = RichProgress(
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            BarColumn(bar_width=40),
        )
        task_id = progress_bar.add_task("", total=100, completed=progress_pct)
        table.add_row(progress_bar)

        # Task tree
        table.add_row("")  # Spacer
        table.add_row("[bold]📋 Task Breakdown:[/bold]")
        task_tree_widget = self._build_task_tree_rich(task_tree)
        table.add_row(task_tree_widget)

        # Time summary
        table.add_row("")  # Spacer
        elapsed_str = self.format_duration(summary.elapsed_time)
        remaining_str = self.format_duration(summary.estimated_remaining)
        time_info = f"⏱️  Elapsed: {elapsed_str} | Estimated remaining: {remaining_str}"
        table.add_row(time_info)

        # Current task
        if summary.current_task_description:
            table.add_row(f"\n💡 [yellow]Current: {summary.current_task_description}[/yellow]")

        # Status warnings
        if summary.failed_count > 0:
            table.add_row(f"[red]⚠️  {summary.failed_count} task(s) failed[/red]")
        if summary.skipped_count > 0:
            table.add_row(f"[dim]⏭️  {summary.skipped_count} task(s) skipped[/dim]")

        # Wrap in panel
        panel = self.Panel(
            table,
            title=f"[bold cyan]{task_tree.user_request}[/bold cyan]",
            border_style="cyan"
        )

        return panel

    def render(self) -> str:
        """
        Render current progress (auto-detect format).

        Returns:
            Formatted progress display (string for simple, rich object for rich)
        """
        if self.use_rich:
            return self.render_rich()
        else:
            return self.render_simple()

    def print_progress(self):
        """Print current progress to console."""
        output = self.render()

        if self.use_rich:
            self.console.print(output)
        else:
            print(output)

    def start_live_display(self):
        """
        Start live updating display (uses rich.live).

        Only available when rich library is enabled.
        """
        if not self.use_rich:
            logger.warning("Live display requires rich library - falling back to static display")
            self.print_progress()
            return

        if self._live is not None:
            logger.warning("Live display already running")
            return

        self._live = self.Live(
            self.render_rich(),
            console=self.console,
            refresh_per_second=2,
            transient=False
        )
        self._live.start()
        logger.info("Live progress display started")

    def update_live_display(self):
        """Update live display with current progress."""
        if self._live is not None:
            self._live.update(self.render_rich())

    def stop_live_display(self):
        """
        Stop live display and show final summary.
        """
        if self._live is not None:
            self._live.stop()
            self._live = None
            logger.info("Live progress display stopped")

            # Print final summary
            self.print_final_summary()

    def print_final_summary(self):
        """Print final execution summary."""
        summary = self.tracker.get_progress_summary()
        task_tree = self.tracker.task_tree

        if self.use_rich:
            # Rich format
            from rich.panel import Panel
            from rich.table import Table

            table = Table(show_header=False, box=None)
            table.add_column("Label", style="bold")
            table.add_column("Value")

            table.add_row("Total Tasks", str(len(task_tree.sub_tasks)))
            table.add_row("Completed", f"[green]{summary.completed_count}[/green]")
            table.add_row("Failed", f"[red]{summary.failed_count}[/red]")
            table.add_row("Skipped", f"[yellow]{summary.skipped_count}[/yellow]")
            table.add_row("Total Time", self.format_duration(summary.elapsed_time))

            panel = Panel(
                table,
                title="[bold green]✅ Execution Complete[/bold green]",
                border_style="green"
            )
            self.console.print(panel)
        else:
            # Simple format
            print("\n" + "=" * 60)
            print("✅ EXECUTION COMPLETE")
            print("=" * 60)
            print(f"Total Tasks:  {len(task_tree.sub_tasks)}")
            print(f"Completed:    {summary.completed_count}")
            print(f"Failed:       {summary.failed_count}")
            print(f"Skipped:      {summary.skipped_count}")
            print(f"Total Time:   {self.format_duration(summary.elapsed_time)}")
            print("=" * 60)
