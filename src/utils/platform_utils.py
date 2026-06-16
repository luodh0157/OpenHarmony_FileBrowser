"""
Platform utilities for OpenHarmony File Browser.
Provides platform and architecture detection functionality.
"""

import platform
import sys
from pathlib import Path
from typing import Optional


def get_platform() -> str:
    """
    Get the current platform name.

    Returns:
        Platform name: 'Windows', 'Linux', or 'Darwin'
    """
    system = platform.system()
    # macOS returns 'Darwin'
    return system


def get_architecture() -> str:
    """
    Get the current CPU architecture.

    Returns:
        Architecture name: 'x64' or 'arm64'
    """
    machine = platform.machine().lower()

    # New HDC directory structure uses simplified arch names
    arch_map = {
        "x86_64": "x64",
        "amd64": "x64",
        "x64": "x64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }

    return arch_map.get(machine, "x64")  # Default to x64 if unknown


def get_hdc_executable(hdc_dir: Optional[Path] = None) -> Path:
    """
    Get the path to the HDC executable for the current platform.

    Args:
        hdc_dir: Base HDC directory. If None, uses default location.

    Returns:
        Path to HDC executable

    Raises:
        FileNotFoundError: If HDC executable not found
    """
    if hdc_dir is None:
        hdc_dir = Path(__file__).parent.parent.parent / "hdc"

    current_platform = get_platform()
    current_arch = get_architecture()

    executable_name = "hdc.exe" if current_platform == "Windows" else "hdc"

    hdc_path = hdc_dir / current_platform / current_arch / executable_name

    if not hdc_path.exists():
        raise FileNotFoundError(
            f"HDC tool not found at {hdc_path}\n"
            f"Platform: {current_platform}, Architecture: {current_arch}\n"
            f"Please ensure HDC tool is placed in: {hdc_dir}/{current_platform}/{current_arch}/"
        )

    return hdc_path


def get_platform_info() -> dict:
    """
    Get comprehensive platform information.

    Returns:
        Dictionary containing platform information
    """
    return {
        "system": platform.system(),
        "node": platform.node(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "platform": get_platform(),
        "architecture": get_architecture(),
    }
