#!/usr/bin/env python
"""
PYPEG Demo - Quick walkthrough of the conversion process.
This script demonstrates the key features without the TUI.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from pypeg.ffmpeg_handler import FFMPEGHandler
from pypeg.conversion_worker import ConversionWorker, ConversionStatus
from pypeg.utils import find_avi_files, create_output_directory, format_time

def demo():
    print("=" * 60)
    print("PYPEG - Demo: Batch AVI to MP4 Conversion")
    print("=" * 60)

    # Setup directories
    source_dir = "/tmp/test_avi_source"
    target_dir = "/tmp/test_avi_target"

    print(f"\n📁 Source directory: {source_dir}")
    print(f"📁 Target directory: {target_dir}")

    # Find AVI files
    avi_files = find_avi_files(source_dir, recursive=False)
    print(f"\n🎬 Found {len(avi_files)} AVI files:")
    for avi in avi_files:
        size = Path(avi).stat().st_size / 1024
        print(f"   • {Path(avi).name} ({size:.1f} KB)")

    if not avi_files:
        print("❌ No AVI files found!")
        return

    # Create output directory
    output_dir = create_output_directory(target_dir)
    print(f"\n✓ Output directory created: {output_dir}")

    # Extract metadata
    print("\n📊 Extracting video metadata...")
    ffmpeg = FFMPEGHandler()
    metadata_dict = {}

    for avi_file in avi_files:
        try:
            metadata = ffmpeg.get_video_metadata(avi_file)
            metadata_dict[avi_file] = {
                "duration": metadata.duration,
                "bitrate": metadata.bitrate,
                "width": metadata.width,
                "height": metadata.height,
                "fps": metadata.fps,
            }
            print(f"   ✓ {Path(avi_file).name}: {metadata.duration:.1f}s, {metadata.bitrate} kbps")
        except Exception as e:
            print(f"   ✗ {Path(avi_file).name}: {e}")

    # Create worker
    print("\n⚙️  Creating conversion worker...")
    worker = ConversionWorker(max_workers=2)

    # Add tasks
    for avi_file in avi_files:
        if avi_file in metadata_dict:
            output_file = str(Path(output_dir) / (Path(avi_file).stem + ".mp4"))
            worker.add_task(avi_file, output_file)
            print(f"   ✓ Queued: {Path(avi_file).name} -> {Path(output_file).name}")

    # Start conversion
    print("\n🚀 Starting conversion (2 workers)...\n")
    start_time = time.time()
    worker.start_conversion(metadata_dict)

    # Monitor progress
    last_update = 0
    while not worker.is_finished():
        time.sleep(0.5)

        # Print progress every 1 second
        if time.time() - last_update >= 1:
            stats = worker.get_stats()
            print(
                f"  {stats['completed']}/{stats['total']} completed | "
                f"Running: {stats['running']} | "
                f"ETA: {format_time(stats['total_eta'])}"
            )
            last_update = time.time()

    # Summary
    total_time = time.time() - start_time
    stats = worker.get_stats()

    print("\n" + "=" * 60)
    print("✨ CONVERSION COMPLETE!")
    print("=" * 60)
    print(f"Total time: {format_time(total_time)}")
    print(f"Videos completed: {stats['completed']}/{stats['total']}")
    print(f"Failed: {stats['failed']}")

    # List output files
    output_files = list(Path(output_dir).glob("*.mp4"))
    if output_files:
        print(f"\n📁 Output files ({len(output_files)}):")
        for mp4 in sorted(output_files):
            size = mp4.stat().st_size / 1024
            print(f"   ✓ {mp4.name} ({size:.1f} KB)")

    worker.shutdown()

    print("\n" + "=" * 60)
    print("To use the interactive TUI, run: pypeg")
    print("=" * 60)


if __name__ == "__main__":
    demo()
