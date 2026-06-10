import ffmpeg
import subprocess
import re
from pathlib import Path
from typing import Optional, Dict, Callable
from dataclasses import dataclass


@dataclass
class VideoMetadata:
    duration: float  # seconds
    bitrate: int  # kbps
    width: int
    height: int
    fps: float


class FFMPEGHandler:
    def __init__(self):
        self._verify_ffmpeg_installed()

    @staticmethod
    def _verify_ffmpeg_installed():
        """Verify ffmpeg and ffprobe are available."""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg: "
                "sudo apt-get install ffmpeg (Linux) or brew install ffmpeg (macOS)"
            )

    def get_video_metadata(self, video_path: str) -> VideoMetadata:
        """Extract video metadata using ffprobe."""
        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next(
                (s for s in probe["streams"] if s["codec_type"] == "video"), None
            )

            if not video_stream:
                raise ValueError(f"No video stream found in {video_path}")

            duration = float(probe["format"].get("duration", 0))
            bitrate = int(probe["format"].get("bit_rate", 0)) // 1000  # to kbps
            width = video_stream.get("width", 0)
            height = video_stream.get("height", 0)
            fps = eval(video_stream.get("r_frame_rate", "0/1"))

            return VideoMetadata(
                duration=duration,
                bitrate=bitrate if bitrate > 0 else 5000,  # fallback to 5Mbps
                width=width,
                height=height,
                fps=fps,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to extract metadata from {video_path}: {e}")

    def convert_video(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> bool:
        """
        Convert AVI to MP4 with auto-detected bitrate.
        progress_callback: called with progress 0.0-1.0
        Returns: True if successful
        """
        try:
            metadata = self.get_video_metadata(input_path)

            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                vcodec="libx264",
                crf=23,  # quality (0=best, 51=worst)
                preset="medium",  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
                acodec="aac",
                audio_bitrate="128k",
            )

            process = ffmpeg.run_async(stream, pipe_stdout=True, pipe_stderr=True)

            # Parse output for progress
            while True:
                line = process.stderr.readline()
                if not line:
                    break

                line_str = line.decode("utf-8").strip()

                # Look for frame= output to calculate progress
                if "frame=" in line_str:
                    match = re.search(r"frame=\s*(\d+)", line_str)
                    if match:
                        frame = int(match.group(1))
                        total_frames = int(metadata.fps * metadata.duration)
                        if total_frames > 0:
                            progress = min(frame / total_frames, 1.0)
                            if progress_callback:
                                progress_callback(progress)

            process.wait()
            return process.returncode == 0

        except Exception as e:
            raise RuntimeError(f"Conversion failed for {input_path}: {e}")
