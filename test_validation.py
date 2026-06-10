#!/usr/bin/env python
"""
Quick validation script for pypeg components.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    try:
        from pypeg.ffmpeg_handler import FFMPEGHandler
        print("  ✓ ffmpeg_handler")

        from pypeg.utils import find_avi_files, create_output_directory, validate_paths
        print("  ✓ utils")

        from pypeg.conversion_worker import ConversionWorker
        print("  ✓ conversion_worker")

        from pypeg.ui_components import CPULoadWidget, MetricsWidget, VideoProgressWidget
        print("  ✓ ui_components")

        from pypeg.app import PypegApp, DirectorySelectionScreen, ConversionScreen, SummaryScreen
        print("  ✓ app")

        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_ffmpeg_detection():
    """Test FFMPEG detection."""
    print("\nTesting FFmpeg detection...")
    try:
        from pypeg.ffmpeg_handler import FFMPEGHandler
        handler = FFMPEGHandler()
        print("  ✓ FFmpeg is installed and accessible")
        return True
    except Exception as e:
        print(f"  ✗ FFmpeg not found: {e}")
        return False


def test_utils():
    """Test utility functions."""
    print("\nTesting utility functions...")
    try:
        from pypeg.utils import format_time, format_filesize, get_output_filename

        # Test format_time
        assert format_time(3661) == "01:01:01"
        print("  ✓ format_time()")

        # Test format_filesize
        assert "MB" in format_filesize(5242880)
        print("  ✓ format_filesize()")

        # Test get_output_filename
        assert get_output_filename("/path/to/video.avi") == "video.mp4"
        print("  ✓ get_output_filename()")

        return True
    except Exception as e:
        print(f"  ✗ Utility test failed: {e}")
        return False


def test_worker_init():
    """Test conversion worker initialization."""
    print("\nTesting conversion worker...")
    try:
        from pypeg.conversion_worker import ConversionWorker
        worker = ConversionWorker(max_workers=2)
        print(f"  ✓ ConversionWorker initialized with 2 workers")

        stats = worker.get_stats()
        assert stats["total"] == 0
        print("  ✓ Stats calculation works")

        worker.shutdown()
        return True
    except Exception as e:
        print(f"  ✗ Worker test failed: {e}")
        return False


def main():
    print("=" * 50)
    print("PYPEG - Component Validation Tests")
    print("=" * 50)

    results = {
        "Imports": test_imports(),
        "FFmpeg": test_ffmpeg_detection(),
        "Utils": test_utils(),
        "Worker": test_worker_init(),
    }

    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:.<30} {status}")

    print(f"\nTotal: {passed}/{total} passed")
    print("=" * 50)

    if passed == total:
        print("\n✨ All validations passed! You're ready to use pypeg.")
        print("\nRun: pypeg")
        return 0
    else:
        print("\n⚠️  Some validations failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
