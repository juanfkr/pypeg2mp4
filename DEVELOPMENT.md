# PYPEG - Development Guide

## Project Structure

```
pypeg2mp4/
├── src/pypeg/                 # Main package
│   ├── __init__.py           # Package init
│   ├── main.py               # CLI entry point
│   ├── app.py                # TUI application (Textual)
│   ├── ffmpeg_handler.py     # FFmpeg integration
│   ├── conversion_worker.py  # Parallel processing
│   ├── ui_components.py      # Textual widgets
│   └── utils.py              # Utilities
├── README.md                 # Project overview
├── USAGE_GUIDE.md           # User guide
├── DEVELOPMENT.md           # This file
├── pyproject.toml           # Project config
├── test_validation.py       # Component tests
├── demo.py                  # Demo script
└── .venv/                   # Virtual environment
```

## Setup Development Environment

### Clone Repository
```bash
git clone <repo-url>
cd pypeg2mp4
```

### Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -e .
```

### Verify Installation
```bash
python test_validation.py
```

## Module Overview

### `ffmpeg_handler.py` - FFmpeg Integration
**Purpose**: Handle all FFmpeg operations

**Classes**:
- `FFMPEGHandler`: Main class for video conversion
  - `get_video_metadata()`: Extract video info (duration, bitrate, resolution, fps)
  - `convert_video()`: Convert AVI to MP4 with progress callback

**Key Features**:
- Auto-detects FFmpeg installation
- Parses FFmpeg output for real-time progress
- Handles conversion errors gracefully

### `conversion_worker.py` - Parallelization
**Purpose**: Manage parallel video conversion queue

**Classes**:
- `ConversionStatus`: Enum for task states (PENDING, RUNNING, PAUSED, COMPLETED, FAILED)
- `ConversionTask`: Dataclass tracking individual video conversion
- `ConversionWorker`: Manages thread pool and task queue
  - `add_task()`: Queue a video for conversion
  - `start_conversion()`: Begin all queued conversions
  - `pause_task()` / `resume_task()`: Control individual tasks
  - `get_stats()`: Retrieve conversion statistics
  - `is_finished()`: Check if all tasks complete

**Key Features**:
- ThreadPoolExecutor for parallel processing
- Real-time ETA calculation
- Pause/resume support
- Statistics tracking (completed, failed, running, etc.)

### `ui_components.py` - Textual Widgets
**Purpose**: Custom widgets for the TUI

**Classes**:
- `CPULoadWidget`: Display real-time CPU load
- `MetricsWidget`: Show conversion statistics
- `VideoProgressWidget`: Individual video progress display
- `StatusMessageWidget`: Status and error messages
- `ConversionSummaryWidget`: Final summary display

**Key Features**:
- Uses Textual's reactive system for updates
- psutil integration for CPU monitoring
- Formatted time and size displays

### `utils.py` - Utilities
**Purpose**: Helper functions

**Functions**:
- `find_avi_files()`: Discover AVI files in directory
- `create_output_directory()`: Create output folder structure
- `validate_paths()`: Verify source/target directories
- `format_time()`: Convert seconds to HH:MM:SS
- `format_filesize()`: Convert bytes to human-readable size
- `get_output_filename()`: Convert .avi name to .mp4

### `app.py` - Main TUI Application
**Purpose**: Textual app with 3 screens

**Screens**:
1. `DirectorySelectionScreen`: Input source and target paths
2. `ConversionScreen`: Real-time conversion progress
3. `SummaryScreen`: Conversion results and statistics

**Key Features**:
- Multi-screen navigation
- Background worker thread for conversions
- UI updates every 500ms
- Keyboard shortcuts

## Architecture Decisions

### Why ThreadPoolExecutor?
- Simpler than asyncio for subprocess management
- Works well with FFmpeg subprocess calls
- Scales efficiently up to ~8 workers

### Why parse FFmpeg output?
- ffmpeg-python library limitation: no real-time progress
- Manual output parsing gives fine-grained progress updates
- Allows accurate ETA calculation

### Why reactive widgets?
- Textual's reactive system ensures UI consistency
- Automatic re-rendering on state changes
- Reduces manual refresh logic

### Why CPU count / 2?
- Keeps system responsive for other tasks
- Balances speed with usability
- Prevents thermal throttling on sustained loads

## Testing

### Run All Tests
```bash
python test_validation.py
```

### Run Demo
```bash
python demo.py
```

### Manual Testing
```bash
# Test FFmpeg integration
python -c "from pypeg.ffmpeg_handler import FFMPEGHandler; FFMPEGHandler().get_video_metadata('video.avi')"

# Test utilities
python -c "from pypeg.utils import format_time; print(format_time(3661))"

# Test worker
python -c "from pypeg.conversion_worker import ConversionWorker; ConversionWorker(max_workers=2)"
```

## Code Style

- Python 3.8+ compatible
- Type hints on function signatures
- Docstrings on classes and complex functions
- Minimal comments (code should be self-explanatory)
- No external config files (all defaults in code)

## Common Tasks

### Add New Conversion Option
1. Update `ffmpeg_handler.py` - modify `convert_video()` parameters
2. Add UI control in `ui_components.py`
3. Update `app.py` to pass option to worker

### Add New Widget
1. Create class in `ui_components.py` inheriting from Textual's `Static`
2. Implement `render()` method or use reactive properties
3. Use in `app.py` screens

### Improve Progress Calculation
1. Modify `conversion_worker.py` - `_convert_task()` method
2. Update ETA calculation in `ConversionTask.update_eta()`
3. Test with various video durations

### Add Logging
1. Use Python's standard `logging` module
2. Add to `ffmpeg_handler.py` for conversion events
3. Display errors in `ui_components.py` StatusMessageWidget

## Potential Enhancements

- [ ] Video quality presets (Fast/Medium/Slow)
- [ ] Custom bitrate input
- [ ] Drag-and-drop file selection
- [ ] Resume interrupted conversions
- [ ] Conversion history
- [ ] Schedule batch conversions
- [ ] Multi-format output (WebM, ProRes, etc.)
- [ ] Subtitle handling
- [ ] Audio codec options
- [ ] Timestamp overlays

## Performance Profiling

### Monitor Resource Usage
```bash
# During conversion, in another terminal:
watch -n 1 'ps aux | grep ffmpeg'
htop  # Real-time monitoring
```

### Benchmark Conversion Speed
```bash
# See how long a single video takes
time ffmpeg -i input.avi -c:v libx264 -crf 23 -preset medium -c:a aac output.mp4
```

## Troubleshooting Development

### Module import errors
```bash
pip install -e .  # Reinstall in editable mode
```

### FFmpeg not in PATH
```bash
which ffmpeg  # Check if installed
# If not: sudo apt-get install ffmpeg
```

### Textual display issues
```bash
export TERM=xterm-256color  # Try different terminal settings
export COLORTERM=truecolor
```

### Test failures
```bash
python test_validation.py -v  # Verbose output
python -m pytest test_validation.py  # If using pytest
```

## Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update `README.md` with new features
- [ ] Run `test_validation.py` - all pass
- [ ] Run `demo.py` - converts successfully
- [ ] Test on Linux, macOS, Windows
- [ ] Create git tag: `git tag v0.2.0`
- [ ] Push to repository: `git push origin main --tags`

---

Happy coding! 🚀
