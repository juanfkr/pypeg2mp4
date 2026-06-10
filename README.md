# PYPEG - Batch AVI to MP4 Converter

A fast, parallel TUI (Text User Interface) application for converting multiple AVI videos to MP4 format using FFMPEG.

## Features

✨ **Fast & Parallel**: Converts multiple videos simultaneously using thread pooling (default: CPU count / 2 workers)
🎯 **Easy to Use**: Simple TUI with just a `pypeg` command
📊 **Progress Tracking**: Real-time progress bars for each video with ETA calculations
📈 **System Monitoring**: Live CPU load display
⏸️ **Pause/Resume**: Pause all conversions or individual videos anytime
🎬 **Auto-Detection**: Automatically detects video bitrate and duration
✅ **Batch Processing**: Convert entire directories of AVI files at once

## Requirements

- Python 3.8+
- FFmpeg (must be installed on your system)
- Linux, macOS, or Windows

## Installation

### Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### Install PYPEG

```bash
pip install -e .
```

Or with your venv activated:
```bash
source .venv/bin/activate
pip install -e .
```

## Usage

Simply run:
```bash
pypeg
```

### Navigation

1. **Directory Selection Screen**
   - Enter source directory (where your .avi files are)
   - Enter target directory (where MP4 files will be saved)
   - Click "Start Conversion"

2. **Conversion Screen**
   - See real-time progress for each video
   - Watch CPU load and overall statistics
   - Use **P** to pause/resume all conversions
   - Use **Q** to quit (cancels ongoing conversions)

3. **Summary Screen**
   - View conversion results and statistics
   - See any errors that occurred
   - Start a new batch or quit

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **P** | Pause/Resume all conversions |
| **Q** | Quit application |
| **Enter** | Start new conversion (on summary) |

## Architecture

The application is built with:

- **Textual**: Modern TUI framework for Python
- **FFmpeg-Python**: Clean API for FFmpeg integration
- **psutil**: System monitoring (CPU, memory)
- **concurrent.futures**: Thread pooling for parallel conversion

### Module Structure

```
src/pypeg/
├── app.py                  # Main TUI application (3 screens)
├── ffmpeg_handler.py       # FFmpeg integration & metadata extraction
├── conversion_worker.py    # Parallel conversion queue & worker pool
├── ui_components.py        # Custom Textual widgets
├── utils.py               # Helper utilities
└── main.py                # Entry point
```

## Configuration

### Auto-Detected Settings

- **Workers**: Automatically set to `CPU count / 2` (keeps system responsive)
- **Bitrate**: Auto-detected from source AVI file
- **Codec**: H.264 video (libx264) + AAC audio
- **Quality**: CRF 23 (good balance between quality and speed)
- **Preset**: Medium (default encoding speed)

## Performance

- Typical conversion speed: 15-100x real-time (depending on CPU and video quality)
- Each worker converts one video at a time
- Total time scales roughly as: `longest_video_duration / number_of_workers`

Example: 10 videos × 2 hours each, 4 workers
- Sequential: ~20 hours
- PYPEG: ~5 hours

## Error Handling

- Invalid paths are detected early
- Missing AVI files are skipped with warning
- FFmpeg installation is verified on startup
- Conversion errors are logged and don't stop other videos
- All errors are shown in the summary screen

## Development

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```

## Troubleshooting

### "FFmpeg not found"
Make sure FFmpeg is installed and in your PATH:
```bash
ffmpeg -version
```

### Slow conversions
- Check CPU usage in the conversion screen
- Reduce max workers (currently auto-calculated)
- Close other applications

### Videos not found
- Ensure .avi files have lowercase extensions (.avi not .AVI)
- Check that source directory path is correct

## License

MIT License - Feel free to use and modify!

## Contributing

Found a bug or want a feature? Create an issue or PR!

---

Made with ❤️ for batch video conversion
