from textual.widgets import Static, ProgressBar
from textual.reactive import reactive
import psutil

from pypeg.utils import format_time


class CPULoadWidget(Static):
    """Display real-time CPU load."""

    cpu_load = reactive(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_cpu()

    def render(self) -> str:
        bar_length = 30
        filled = int(bar_length * (self.cpu_load / 100))
        bar = "█" * filled + "░" * (bar_length - filled)
        return f"CPU Load: {bar} {self.cpu_load:.1f}%"

    def update_cpu(self):
        """Update CPU load."""
        self.cpu_load = psutil.cpu_percent(interval=0.1)


class MetricsWidget(Static):
    """Display conversion metrics."""

    def __init__(self, metrics_dict: dict, **kwargs):
        super().__init__(**kwargs)
        self.metrics_dict = metrics_dict

    def render(self) -> str:
        m = self.metrics_dict

        lines = [
            f"[cyan]Videos:[/cyan] {m.get('completed', 0)}/{m.get('total', 0)} | "
            f"[yellow]Failed:[/yellow] {m.get('failed', 0)} | "
            f"[green]Running:[/green] {m.get('running', 0)}",
            f"[cyan]Elapsed:[/cyan] {format_time(m.get('total_elapsed', 0))} | "
            f"[yellow]ETA:[/yellow] {format_time(m.get('total_eta', 0))}",
        ]

        return "\n".join(lines)


class VideoProgressWidget(Static):
    """Display individual video progress."""

    progress = reactive(0.0)

    def __init__(self, filename: str, eta: float = 0, **kwargs):
        super().__init__(**kwargs)
        self.filename = filename
        self.eta = eta

    def update_progress(self, progress: float, eta: float = 0):
        """Update progress and ETA."""
        self.progress = progress
        self.eta = eta

    def render(self) -> str:
        bar_length = 40
        filled = int(bar_length * self.progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        percentage = int(self.progress * 100)
        eta_str = format_time(self.eta)

        return (
            f"{self.filename}\n"
            f"{bar} {percentage:3d}% | ETA: {eta_str}"
        )


class StatusMessageWidget(Static):
    """Display status messages."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message = ""

    def set_message(self, message: str):
        """Update status message."""
        self.message = message
        self.update(message)

    def render(self) -> str:
        return self.message


class ConversionSummaryWidget(Static):
    """Display final conversion summary."""

    def render_summary(self, summary_data: dict) -> str:
        """Render summary table."""
        lines = [
            "[bold cyan]=== CONVERSION SUMMARY ===[/bold cyan]",
            f"Total Videos: {summary_data.get('total', 0)}",
            f"[green]Successful:[/green] {summary_data.get('completed', 0)}",
            f"[red]Failed:[/red] {summary_data.get('failed', 0)}",
            f"Total Time: {format_time(summary_data.get('total_time', 0))}",
        ]

        if summary_data.get('errors'):
            lines.append("\n[red]Errors:[/red]")
            for err in summary_data['errors'][:5]:  # Show first 5 errors
                lines.append(f"  • {err}")

        return "\n".join(lines)
