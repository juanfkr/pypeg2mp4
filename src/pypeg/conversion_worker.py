import time
import os
from dataclasses import dataclass, field
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Optional, Dict, List
from enum import Enum

from pypeg.ffmpeg_handler import FFMPEGHandler
from pypeg.utils import get_output_filename, format_time


class ConversionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ConversionTask:
    input_path: str
    output_path: str
    status: ConversionStatus = ConversionStatus.PENDING
    progress: float = 0.0
    start_time: float = field(default_factory=time.time)
    elapsed: float = 0.0
    eta: float = 0.0
    error: Optional[str] = None
    paused: bool = False

    def get_elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.status == ConversionStatus.RUNNING and not self.paused:
            return time.time() - self.start_time
        return self.elapsed

    def update_eta(self, duration: float):
        """Update ETA based on progress and duration."""
        if self.progress > 0.01:
            elapsed = self.get_elapsed()
            remaining = (elapsed / self.progress) - elapsed
            self.eta = max(0, remaining)


class ConversionWorker:
    def __init__(
        self,
        max_workers: Optional[int] = None,
        on_progress: Optional[Callable[[str, float], None]] = None,
    ):
        if max_workers is None:
            max_workers = max(1, os.cpu_count() // 2)

        self.max_workers = max_workers
        self.on_progress = on_progress
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.ffmpeg = FFMPEGHandler()
        self.tasks: Dict[str, ConversionTask] = {}
        self.futures: Dict[str, Future] = {}
        self.paused_tasks: set = set()

    def add_task(self, input_path: str, output_path: str):
        """Add a conversion task to queue."""
        task = ConversionTask(input_path=input_path, output_path=output_path)
        self.tasks[input_path] = task

    def start_conversion(self, metadata_dict: Dict[str, dict]):
        """
        Start all queued conversions.
        metadata_dict: {input_path: {"duration": float, "bitrate": int, ...}}
        """
        for input_path, task in self.tasks.items():
            if task.status == ConversionStatus.PENDING:
                future = self.executor.submit(self._convert_task, input_path, metadata_dict)
                self.futures[input_path] = future

    def _convert_task(self, input_path: str, metadata_dict: Dict):
        """Internal task execution."""
        task = self.tasks[input_path]
        task.status = ConversionStatus.RUNNING
        task.start_time = time.time()

        try:
            metadata = metadata_dict.get(input_path, {})
            duration = metadata.get("duration", 0)

            def progress_callback(progress: float):
                task.progress = progress
                task.update_eta(duration)
                if self.on_progress:
                    self.on_progress(input_path, progress)

            success = self.ffmpeg.convert_video(
                input_path, task.output_path, progress_callback=progress_callback
            )

            if success:
                task.status = ConversionStatus.COMPLETED
                task.progress = 1.0
            else:
                task.status = ConversionStatus.FAILED
                task.error = "Conversion process returned non-zero exit code"

        except Exception as e:
            task.status = ConversionStatus.FAILED
            task.error = str(e)

        task.elapsed = time.time() - task.start_time

    def pause_task(self, input_path: str):
        """Pause a specific task."""
        if input_path in self.tasks:
            self.tasks[input_path].paused = True
            self.paused_tasks.add(input_path)

    def resume_task(self, input_path: str):
        """Resume a paused task."""
        if input_path in self.tasks:
            self.tasks[input_path].paused = False
            self.paused_tasks.discard(input_path)

    def pause_all(self):
        """Pause all running tasks."""
        for task in self.tasks.values():
            if task.status == ConversionStatus.RUNNING:
                task.paused = True
                self.paused_tasks.add(task.input_path)

    def resume_all(self):
        """Resume all paused tasks."""
        for task in self.tasks.values():
            if task.status == ConversionStatus.RUNNING and task.paused:
                task.paused = False
                self.paused_tasks.discard(task.input_path)

    def cancel_task(self, input_path: str):
        """Cancel a specific task."""
        if input_path in self.futures:
            self.futures[input_path].cancel()
        if input_path in self.tasks:
            self.tasks[input_path].status = ConversionStatus.FAILED
            self.tasks[input_path].error = "Cancelled by user"

    def get_stats(self) -> dict:
        """Get overall conversion statistics."""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == ConversionStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == ConversionStatus.FAILED)
        running = sum(1 for t in self.tasks.values() if t.status == ConversionStatus.RUNNING)
        paused = len(self.paused_tasks)

        total_elapsed = sum(t.get_elapsed() for t in self.tasks.values())
        total_eta = sum(
            t.eta
            for t in self.tasks.values()
            if t.status in (ConversionStatus.RUNNING, ConversionStatus.PENDING)
        )

        avg_speed = 0
        if total_elapsed > 0:
            completed_tasks = [t for t in self.tasks.values() if t.status == ConversionStatus.COMPLETED]
            if completed_tasks:
                avg_speed = completed_tasks[0].elapsed / (completed_tasks[0].progress or 1)

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "paused": paused,
            "total_elapsed": total_elapsed,
            "total_eta": total_eta,
            "avg_speed": avg_speed,
        }

    def is_finished(self) -> bool:
        """Check if all tasks are finished."""
        return all(
            t.status
            in (ConversionStatus.COMPLETED, ConversionStatus.FAILED)
            for t in self.tasks.values()
        )

    def shutdown(self):
        """Cleanup worker threads."""
        self.executor.shutdown(wait=True)
