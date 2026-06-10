import os
import subprocess
from pathlib import Path
from typing import List, Dict
from datetime import timedelta


def find_avi_files(directory: str, recursive: bool = True) -> List[str]:
    """Find all .avi files in directory."""
    path = Path(directory)
    if not path.exists() or not path.is_dir():
        return []

    pattern = "**/*.avi" if recursive else "*.avi"
    return sorted([str(f) for f in path.glob(pattern)])


def find_usb_devices() -> Dict[str, str]:
    """Find mounted USB devices."""
    usb_dirs = {}

    try:
        # Check /media and /mnt for mounted devices
        for mount_base in ["/media", "/mnt"]:
            mount_path = Path(mount_base)
            if mount_path.exists():
                for item in mount_path.iterdir():
                    if item.is_dir() and os.access(item, os.R_OK):
                        label = item.name
                        usb_dirs[f"🔌 {label}"] = str(item)
    except PermissionError:
        pass

    return usb_dirs


def find_home_directories() -> Dict[str, str]:
    """Find subdirectories in /home and user's home."""
    home_dirs = {}

    # Add user's home directory
    home = Path.home()
    home_dirs[f"🏠 Home"] = str(home)

    # Add Downloads, Documents, Desktop if they exist
    common_dirs = {
        "📥 Downloads": home / "Downloads",
        "📄 Documents": home / "Documents",
        "🖥️ Desktop": home / "Desktop",
        "🎬 Videos": home / "Videos",
    }

    for label, path in common_dirs.items():
        if path.exists() and path.is_dir():
            home_dirs[label] = str(path)

    # Add other user directories in /home
    try:
        home_base = Path("/home")
        if home_base.exists():
            for user_dir in home_base.iterdir():
                if user_dir.is_dir() and user_dir.name != home.name:
                    home_dirs[f"👤 {user_dir.name}"] = str(user_dir)
    except PermissionError:
        pass

    return home_dirs


def get_available_locations() -> Dict[str, str]:
    """Get all available media locations (USB + home directories)."""
    locations = {}

    # Add USB devices
    usb_devices = find_usb_devices()
    locations.update(usb_devices)

    # Add home directories
    if locations:  # Add separator if we have USB devices
        locations["─" * 20] = ""

    home_dirs = find_home_directories()
    locations.update(home_dirs)

    return locations


def create_output_directory(base_path: str, folder_name: str = "converted") -> str:
    """Create output directory and return path."""
    output_dir = Path(base_path) / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir)


def validate_paths(source_dir: str, target_dir: str) -> tuple[bool, str]:
    """Validate source and target directories."""
    source = Path(source_dir)
    target = Path(target_dir)

    if not source.exists():
        return False, f"Source directory does not exist: {source_dir}"

    if not source.is_dir():
        return False, f"Source is not a directory: {source_dir}"

    # Check write permissions on target parent
    try:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        return False, f"No write permission in target directory: {target_dir}"

    return True, ""


def format_time(seconds: float) -> str:
    """Format seconds to HH:MM:SS."""
    if seconds < 0:
        seconds = 0
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(int(td.total_seconds()), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_filesize(bytes_val: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}TB"


def get_output_filename(input_path: str) -> str:
    """Convert .avi filename to .mp4."""
    path = Path(input_path)
    return path.stem + ".mp4"
