# PYPEG - Usage Guide

## Quick Start

### 1. Install PYPEG

First, make sure FFmpeg is installed on your system:

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

Then install PYPEG:
```bash
git clone https://github.com/yourusername/pypeg2mp4.git
cd pypeg2mp4
pip install -e .
```

### 2. Run PYPEG

Simply type:
```bash
pypeg
```

## User Interface

### Screen 1: Directory Selection

When you start PYPEG, you'll see the directory selection screen:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ PYPEG - Batch AVI to MP4 Converter                ┃
┃                                                     ┃
┃ Source Directory (AVI files):                      ┃
┃ /home/user/videos/source                           ┃
┃                                                     ┃
┃ Target Directory (for MP4 files):                  ┃
┃ /home/user/videos/output                           ┃
┃                                                     ┃
┃ [Start Conversion]  [Quit]                         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

**Actions:**
- Click on **Source Directory** field and enter the path to your AVI files
- Click on **Target Directory** field and enter where you want the MP4 files saved
- Click **Start Conversion** to proceed
- Click **Quit** to exit

### Screen 2: Conversion Progress

Once you click "Start Conversion", you'll see the progress screen:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ CONVERSION IN PROGRESS                             ┃
┃                                                     ┃
┃ CPU Load: ████████░░░░░░░░░░░░░░░░░░░░░░  45.2%   ┃
┃                                                     ┃
┃ Videos: 5/20 | Failed: 0 | Running: 2             ┃
┃ Elapsed: 00:05:23 | ETA: 00:12:45                 ┃
┃                                                     ┃
┃ video1.avi                                          ┃
┃ ████████████████░░░░░░░░░░░░░░░░ 60% | ETA: 00:02 ┃
┃                                                     ┃
┃ video2.avi                                          ┃
┃ ████████████████░░░░░░░░░░░░░░░░ 50% | ETA: 00:03 ┃
┃                                                     ┃
┃ Converting: video5.avi...                          ┃
┃                                                     ┃
┃ [Pause All]  [Cancel]                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

**What You See:**
- **CPU Load**: Real-time CPU usage as a visual bar
- **Video Count**: How many videos have been completed (e.g., "5/20")
- **Video Progress**: Individual progress bar for currently processing videos
- **Time Info**: Total elapsed time and estimated time remaining
- **Status**: Current video being processed

**Actions:**
- Press **P** to pause all conversions (or resume if already paused)
- Press **Q** to cancel all conversions and return to directory selection
- Click **Pause All** to pause conversions
- Click **Cancel** to stop all conversions

### Screen 3: Conversion Summary

After all conversions are complete, you'll see the summary screen:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ === CONVERSION SUMMARY ===                          ┃
┃                                                     ┃
┃ Total Videos: 20                                    ┃
┃ Successful: 20                                      ┃
┃ Failed: 0                                           ┃
┃ Total Time: 00:45:30                               ┃
┃                                                     ┃
┃ [New Conversion]  [Quit]                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

**Actions:**
- Click **New Conversion** to convert more videos
- Press **Enter** for New Conversion (keyboard shortcut)
- Click **Quit** to exit
- Press **Q** to quit (keyboard shortcut)

## Keyboard Shortcuts

| Key | Action | Screen |
|-----|--------|--------|
| **P** | Pause/Resume all conversions | Conversion |
| **Q** | Quit application | Any |
| **Enter** | Start new conversion | Summary |

## Advanced Features

### Auto-Detection

PYPEG automatically:
- Detects video duration and bitrate from each AVI file
- Calculates optimal number of parallel workers (CPU count / 2)
- Estimates total conversion time based on video duration
- Updates ETA in real-time as conversions progress

### Parallel Processing

By default, PYPEG uses **CPU count / 2** workers:
- 2-core CPU: 1 worker
- 4-core CPU: 2 workers
- 8-core CPU: 4 workers
- 16-core CPU: 8 workers

This ensures smooth operation while keeping your system responsive.

### Output Structure

Files are saved in:
```
<target_directory>/converted/
├── video1.mp4
├── video2.mp4
└── ...
```

A new `converted/` folder is automatically created in your target directory.

## Examples

### Example 1: Convert Videos in Home Directory

```
Source: /home/user/Videos
Target: /home/user/Videos
```

Output: `/home/user/Videos/converted/`

### Example 2: Convert to External Drive

```
Source: /media/disk1/raw_videos
Target: /media/disk2/
```

Output: `/media/disk2/converted/`

### Example 3: Network Drive (if mounted)

```
Source: /mnt/network_share/videos
Target: /backup/conversions
```

Output: `/backup/conversions/converted/`

## Performance Tips

1. **Pause Other Applications**: Close memory-intensive apps for faster conversion
2. **Disk Speed Matters**: Faster SSDs = faster conversions
3. **Network Drives**: Converting to local drives is much faster than network drives
4. **CPU Temp**: Monitor your CPU temperature, especially with high core counts
5. **Background Tasks**: Disable background scans/updates during conversion

## Troubleshooting

### "No .avi files found"
- Make sure AVI files have lowercase `.avi` extension
- Verify the source directory path is correct
- Use absolute paths (e.g., `/full/path/to/videos` not `./videos`)

### Slow conversions
- Check CPU load in the conversion screen
- Close other applications
- Try converting to a local SSD instead of network drive

### "FFmpeg not found"
- Install FFmpeg: `sudo apt-get install ffmpeg` (Linux) or `brew install ffmpeg` (macOS)
- Verify: `ffmpeg -version`

### Application crashes
- Update Textual: `pip install --upgrade textual`
- Check your terminal supports 256 colors: `echo $TERM`
- Try a different terminal application

## Demo Mode

To see PYPEG in action without the interactive TUI:

```bash
python demo.py
```

This runs a demonstration with test files.

## Support

For issues or feature requests, visit the repository or contact the developers.

---

**Enjoy batch converting your videos! 🎬**
