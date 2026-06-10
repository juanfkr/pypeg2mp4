from textual.app import App, ComposeResult, on
from textual.widgets import Header, Footer, Static, Button, Label, OptionList
from textual.widgets.option_list import Option
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.screen import Screen
from textual.binding import Binding
from pathlib import Path
import time
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
    get_available_locations,
)


class DirectorySelectionScreen(Screen):
    """Screen for selecting source and target directories."""

    BINDINGS = [
        Binding("ctrl+q", "app.quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.source_dir = ""
        self.target_dir = ""
        self.selecting_source = True

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("[bold]PYPEG - Batch AVI to MP4 Converter[/bold]"),
            Static(""),
            Label(id="selection_title"),
            OptionList(id="location_list"),
            Static(""),
            Label(id="selected_path"),
            Static(""),
            Horizontal(
                Button("Confirm", id="confirm_btn", variant="primary"),
                Button("Cancel", id="cancel_btn", variant="error"),
            ),
        )
        yield Footer()

    def on_mount(self):
        self._update_location_list()

    def _update_location_list(self):
        """Update the location list based on current selection mode."""
        title = self.query_one("#selection_title", Label)
        option_list = self.query_one("#location_list", OptionList)
        selected_path = self.query_one("#selected_path", Label)

        if self.selecting_source:
            title.update("[cyan]Select Source Directory (AVI files):[/cyan]")
        else:
            title.update("[cyan]Select Target Directory (MP4 output):[/cyan]")

        # Get available locations
        locations = get_available_locations()

        # Populate option list
        option_list.clear_options()
        for label, path in locations.items():
            if label.startswith("─"):  # Separator
                option_list.add_option(Option(label, id=""))
            else:
                option_list.add_option(Option(label, id=path))

        # Show current selection
        if self.selecting_source and self.source_dir:
            selected_path.update(f"[green]Selected:[/green] {self.source_dir}")
        elif not self.selecting_source and self.target_dir:
            selected_path.update(f"[green]Selected:[/green] {self.target_dir}")
        else:
            selected_path.update("[yellow]No selection yet[/yellow]")

    @on(OptionList.OptionSelected)
    def on_option_selected(self, event: OptionList.OptionSelected):
        """Handle directory selection."""
        if not event.option.id:  # Skip separators
            return

        selected_path = self.query_one("#selected_path", Label)

        if self.selecting_source:
            self.source_dir = event.option.id
            selected_path.update(f"[green]Source selected:[/green] {self.source_dir}")
        else:
            self.target_dir = event.option.id
            selected_path.update(f"[green]Target selected:[/green] {self.target_dir}")

    @on(Button.Pressed, "#confirm_btn")
    async def on_confirm(self):
        """Confirm selection and move to next step."""
        if self.selecting_source:
            if not self.source_dir:
                self.app.notify("Please select a source directory", severity="error")
                return

            # Check if directory has AVI files
            avi_files = find_avi_files(self.source_dir)
            if not avi_files:
                self.app.notify("No .avi files found in selected directory", severity="error")
                return

            # Move to target directory selection
            self.selecting_source = False
            self._update_location_list()
        else:
            if not self.target_dir:
                self.app.notify("Please select a target directory", severity="error")
                return

            # Validate paths
            valid, error = validate_paths(self.source_dir, self.target_dir)
            if not valid:
                self.app.notify(error, severity="error")
                return

            # Get AVI files and proceed
            avi_files = find_avi_files(self.source_dir)
            self.app.source_dir = self.source_dir
            self.app.target_dir = self.target_dir
            self.app.avi_files = avi_files
            self.app.push_screen("conversion")

    @on(Button.Pressed, "#cancel_btn")
    def on_cancel(self):
        """Cancel and reset selection."""
        if self.selecting_source:
            self.app.exit()
        else:
            self.selecting_source = True
            self.source_dir = ""
            self._update_location_list()


class ConversionScreen(Screen):
    """Main conversion progress screen."""

    BINDINGS = [
        Binding("p", "toggle_pause", "Pause/Resume"),
        Binding("ctrl+q", "app.quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.worker = None
        self.video_widgets = {}
        self.start_time = 0
        self.ffmpeg = FFMPEGHandler()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("[bold]CONVERSION IN PROGRESS[/bold]"),
            CPULoadWidget(id="cpu_widget"),
            MetricsWidget({}, id="metrics"),
            ScrollableContainer(Static(id="video_list")),
            StatusMessageWidget(id="status"),
            Horizontal(
                Button("Pause All", id="pause_btn", variant="warning"),
                Button("Cancel", id="cancel_btn", variant="error"),
            ),
        )
        yield Footer()

    def on_mount(self):
        """Initialize conversion."""
        self.start_time = time.time()
        source_dir = self.app.source_dir
        target_dir = self.app.target_dir
        avi_files = self.app.avi_files

        output_dir = create_output_directory(target_dir)
        status = self.query_one("#status", StatusMessageWidget)
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
                pass

        self.worker = ConversionWorker(on_progress=self._on_progress_update)
        for avi_file in avi_files:
            if avi_file in metadata_dict:
                output_file = str(Path(output_dir) / get_output_filename(avi_file))
                self.worker.add_task(avi_file, output_file)

        status.set_message("Starting conversion...")
        self.worker.start_conversion(metadata_dict)
        self.set_interval(0.5, self._update_ui)

    def _on_progress_update(self, input_path: str, progress: float):
        task = self.worker.tasks.get(input_path)
        if task and input_path in self.video_widgets:
            self.video_widgets[input_path].update_progress(progress, task.eta)

    def _update_ui(self):
        if not self.worker:
            return

        cpu = self.query_one("#cpu_widget", CPULoadWidget)
        cpu.update_cpu()

        stats = self.worker.get_stats()
        metrics = self.query_one("#metrics", MetricsWidget)
        metrics.metrics_dict = stats
        metrics.update()

        video_list = self.query_one("#video_list", Static)
        videos = []

        for avi_file, task in self.worker.tasks.items():
            filename = Path(avi_file).name
            if avi_file not in self.video_widgets:
                self.video_widgets[avi_file] = VideoProgressWidget(filename)

            widget = self.video_widgets[avi_file]
            widget.update_progress(task.progress, task.eta)
            videos.append(widget.render())

        video_list.update("\n".join(videos))

        if self.worker.is_finished():
            self._show_summary()

    def _show_summary(self):
        total_time = time.time() - self.start_time
        stats = self.worker.get_stats()
        errors = [
            f"{Path(t.input_path).name}: {t.error}"
            for t in self.worker.tasks.values()
            if t.error
        ]
        self.app.summary_data = {
            "total": stats["total"],
            "completed": stats["completed"],
            "failed": stats["failed"],
            "total_time": total_time,
            "errors": errors,
        }
        self.worker.shutdown()
        self.app.push_screen("summary")

    @on(Button.Pressed, "#pause_btn")
    def toggle_pause(self):
        if self.worker:
            if any(t.paused for t in self.worker.tasks.values()):
                self.worker.resume_all()
            else:
                self.worker.pause_all()

    @on(Button.Pressed, "#cancel_btn")
    def on_cancel(self):
        if self.worker:
            for avi_file in list(self.worker.tasks.keys()):
                self.worker.cancel_task(avi_file)
            self.worker.shutdown()
        self.app.push_screen("directory_selection")


class SummaryScreen(Screen):
    """Summary screen after conversion."""

    BINDINGS = [
        Binding("enter", "new_conversion", "New Conversion"),
        Binding("ctrl+q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            ConversionSummaryWidget(id="summary_widget"),
            Static(""),
            Horizontal(
                Button("New Conversion", id="new_btn", variant="primary"),
                Button("Quit", id="quit_btn", variant="error"),
            ),
        )
        yield Footer()

    def on_mount(self):
        summary_widget = self.query_one("#summary_widget", ConversionSummaryWidget)
        summary_data = getattr(self.app, "summary_data", {})
        summary_widget.update(summary_widget.render_summary(summary_data))

    @on(Button.Pressed, "#new_btn")
    def on_new(self):
        self.app.push_screen("directory_selection")

    @on(Button.Pressed, "#quit_btn")
    def on_quit(self):
        self.app.exit()


class PypegApp(App):
    """Main application."""

    BINDINGS = [
        Binding("ctrl+q", "action_quit", "Quit"),
    ]

    CSS = """
    Screen {
        background: $background;
    }

    Label {
        margin: 1;
    }

    Button {
        margin: 1;
    }

    OptionList {
        margin: 0 1;
        width: 70;
        height: auto;
    }

    #video_list {
        height: 10;
        border: solid $accent;
        margin: 1;
    }
    """

    TITLE = "PYPEG - Batch AVI to MP4 Converter"

    def on_mount(self):
        """Install all screens."""
        self.install_screen(DirectorySelectionScreen(), name="directory_selection")
        self.install_screen(ConversionScreen(), name="conversion")
        self.install_screen(SummaryScreen(), name="summary")
        self.push_screen("directory_selection")
