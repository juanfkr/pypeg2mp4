from textual.app import App, ComposeResult, on
from textual.widgets import Header, Footer, Static, Button, Input, Label
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.binding import Binding
from pathlib import Path
import time
import psutil
from typing import Dict

from pypeg.ffmpeg_handler import FFMPEGHandler
from pypeg.conversion_worker import ConversionWorker
from pypeg.ui_components import (
    CPULoadWidget,
    MetricsWidget,
    VideoProgressWidget,
    StatusMessageWidget,
    ConversionSummaryWidget,
)
from pypeg.utils import (
    find_avi_files,
    create_output_directory,
    validate_paths,
    get_output_filename,
    format_time,
)


class DirectorySelectionScreen(Screen):
    """Screen for selecting source and target directories."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.source_dir = ""
        self.target_dir = ""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("PYPEG - Batch AVI to MP4 Converter", id="title"),
            Static("\n"),
            Label("Source Directory (AVI files):"),
            Input(id="source_input", placeholder="/path/to/avi/files"),
            Label("Target Directory (for MP4 files):"),
            Input(id="target_input", placeholder="/path/to/output"),
            Static("\n"),
            Horizontal(
                Button("Start Conversion", id="start_btn", variant="primary"),
                Button("Quit", id="quit_btn", variant="error"),
            ),
            id="main_container",
        )
        yield Footer()

    def on_mount(self):
        self.query_one("#source_input", Input).focus()

    @on(Button.Pressed, "#start_btn")
    async def on_start(self):
        """Start conversion with selected directories."""
        source_input = self.query_one("#source_input", Input)
        target_input = self.query_one("#target_input", Input)

        self.source_dir = source_input.value.strip()
        self.target_dir = target_input.value.strip()

        # Validate paths
        if not self.source_dir or not self.target_dir:
            self.app.notify("Please enter both source and target directories", severity="error")
            return

        valid, error = validate_paths(self.source_dir, self.target_dir)
        if not valid:
            self.app.notify(error, severity="error")
            return

        # Find AVI files
        avi_files = find_avi_files(self.source_dir)
        if not avi_files:
            self.app.notify("No .avi files found in source directory", severity="error")
            return

        # Proceed to conversion screen
        self.app.source_dir = self.source_dir
        self.app.target_dir = self.target_dir
        self.app.avi_files = avi_files
        self.app.switch_screen("conversion")

    @on(Button.Pressed, "#quit_btn")
    def on_quit(self):
        """Quit application."""
        self.app.exit()


class ConversionScreen(Screen):
    """Main conversion progress screen."""

    BINDINGS = [
        Binding("p", "toggle_pause", "Pause/Resume"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.worker = None
        self.video_widgets: Dict[str, VideoProgressWidget] = {}
        self.start_time = 0
        self.ffmpeg = FFMPEGHandler()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("CONVERSION IN PROGRESS", id="title"),
            CPULoadWidget(id="cpu_widget"),
            Static("\n", size=(1, 1)),
            MetricsWidget({}),
            Static("\n", size=(1, 1)),
            Container(
                Static(id="video_list_container"),
                id="videos_container",
            ),
            Static("\n", size=(1, 1)),
            StatusMessageWidget(id="status_msg"),
            Horizontal(
                Button("Pause All", id="pause_btn", variant="warning"),
                Button("Cancel", id="cancel_btn", variant="error"),
            ),
            id="main_container",
        )
        yield Footer()

    def on_mount(self):
        """Initialize conversion when screen mounts."""
        self.start_time = time.time()

        # Get paths and files
        source_dir = self.app.source_dir
        target_dir = self.app.target_dir
        avi_files = self.app.avi_files

        # Create output directory
        output_dir = create_output_directory(target_dir)

        # Extract metadata
        status = self.query_one("#status_msg", StatusMessageWidget)
        status.set_message("Analyzing videos...")

        metadata_dict = {}
        for avi_file in avi_files:
            try:
                metadata = self.ffmpeg.get_video_metadata(avi_file)
                metadata_dict[avi_file] = {
                    "duration": metadata.duration,
                    "bitrate": metadata.bitrate,
                    "width": metadata.width,
                    "height": metadata.height,
                    "fps": metadata.fps,
                }
            except Exception as e:
                self.app.notify(f"Error analyzing {Path(avi_file).name}: {e}", severity="warning")

        # Create worker and add tasks
        self.worker = ConversionWorker(on_progress=self._on_progress_update)

        for avi_file in avi_files:
            if avi_file in metadata_dict:
                output_file = str(Path(output_dir) / get_output_filename(avi_file))
                self.worker.add_task(avi_file, output_file)

        # Start conversion
        status.set_message("Starting conversion...")
        self.worker.start_conversion(metadata_dict)

        # Setup update loop
        self.set_interval(0.5, self._update_ui)

    def _on_progress_update(self, input_path: str, progress: float):
        """Called when a video's progress updates."""
        task = self.worker.tasks.get(input_path)
        if task and input_path in self.video_widgets:
            widget = self.video_widgets[input_path]
            widget.update_progress(progress, task.eta)

    def _update_ui(self):
        """Update UI elements periodically."""
        if not self.worker:
            return

        # Update CPU load
        cpu_widget = self.query_one("#cpu_widget", CPULoadWidget)
        cpu_widget.update_cpu()

        # Update metrics
        stats = self.worker.get_stats()
        metrics_widget = self.query_one(MetricsWidget)
        metrics_widget.metrics_dict = stats
        metrics_widget.update()

        # Update video list and create new widgets if needed
        video_list = self.query_one("#video_list_container", Static)
        videos_html = []

        for avi_file, task in self.worker.tasks.items():
            filename = Path(avi_file).name
            if avi_file not in self.video_widgets:
                widget = VideoProgressWidget(filename)
                self.video_widgets[avi_file] = widget

            widget = self.video_widgets[avi_file]
            widget.update_progress(task.progress, task.eta)
            videos_html.append(f"  {widget.render()}")

        video_list.update("\n".join(videos_html))

        # Check if finished
        if self.worker.is_finished():
            self._show_summary()

    def _show_summary(self):
        """Show summary when conversion is complete."""
        total_time = time.time() - self.start_time
        stats = self.worker.get_stats()

        errors = [
            f"{Path(task.input_path).name}: {task.error}"
            for task in self.worker.tasks.values()
            if task.error
        ]

        summary_data = {
            "total": stats["total"],
            "completed": stats["completed"],
            "failed": stats["failed"],
            "total_time": total_time,
            "errors": errors,
        }

        self.app.summary_data = summary_data
        self.worker.shutdown()
        self.app.switch_screen("summary")

    @on(Button.Pressed, "#pause_btn")
    def toggle_pause(self):
        """Toggle pause/resume all conversions."""
        if self.worker:
            if any(t.paused for t in self.worker.tasks.values()):
                self.worker.resume_all()
            else:
                self.worker.pause_all()

    @on(Button.Pressed, "#cancel_btn")
    def on_cancel(self):
        """Cancel all conversions."""
        if self.worker:
            for avi_file in list(self.worker.tasks.keys()):
                self.worker.cancel_task(avi_file)
            self.worker.shutdown()
        self.app.switch_screen("directory_selection")


class SummaryScreen(Screen):
    """Summary screen after conversion completes."""

    BINDINGS = [
        Binding("enter", "new_conversion", "New Conversion"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            ConversionSummaryWidget(id="summary_widget"),
            Static("\n"),
            Horizontal(
                Button("New Conversion", id="new_btn", variant="primary"),
                Button("Quit", id="quit_btn", variant="error"),
            ),
            id="main_container",
        )
        yield Footer()

    def on_mount(self):
        """Display summary."""
        summary_widget = self.query_one("#summary_widget", ConversionSummaryWidget)
        summary_data = getattr(self.app, "summary_data", {})
        summary_widget.update(summary_widget.render_summary(summary_data))

    @on(Button.Pressed, "#new_btn")
    def on_new(self):
        """Start new conversion."""
        self.app.switch_screen("directory_selection")

    @on(Button.Pressed, "#quit_btn")
    def on_quit(self):
        """Quit application."""
        self.app.exit()


class PypegApp(App):
    """Main application."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    CSS = """
    Screen {
        layout: vertical;
    }

    #main_container {
        width: 100%;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    #title {
        dock: top;
        width: 100%;
        height: 1;
        background: $boost;
        color: $text;
        text-align: center;
        text-style: bold;
    }

    Input {
        margin: 0 2;
        width: 80%;
    }

    Label {
        width: 80%;
        margin: 1 2;
    }

    Button {
        margin: 0 1;
    }

    #videos_container {
        width: 100%;
        height: auto;
        border: solid $primary;
        overflow-y: auto;
    }

    #video_list_container {
        width: 100%;
        height: auto;
        padding: 1;
    }

    #status_msg {
        width: 100%;
        height: auto;
        margin: 1 0;
    }

    #cpu_widget {
        width: 100%;
        height: 1;
        margin: 0 1;
    }
    """

    TITLE = "PYPEG - Batch AVI to MP4 Converter"

    def on_mount(self):
        """Setup initial screen."""
        self.install_screen(DirectorySelectionScreen(), name="directory_selection")
        self.install_screen(ConversionScreen(), name="conversion")
        self.install_screen(SummaryScreen(), name="summary")
        self.switch_screen("directory_selection")
