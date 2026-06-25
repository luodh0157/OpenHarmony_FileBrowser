"""
Resource path utilities - works for both dev and PyInstaller packaged mode.
"""

import os
import platform
import sys
from pathlib import Path
from typing import Dict

_resource_cache: Dict[str, Path] = {}


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and PyInstaller."""
    if relative_path in _resource_cache:
        return _resource_cache[relative_path]

    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base_path = Path(__file__).parent.parent.parent

    result = base_path / relative_path
    _resource_cache[relative_path] = result
    return result


def get_user_data_dir() -> Path:
    """Get writable user data directory for logs and config saves.

    In dev mode, returns the project's config directory (same as current behavior).
    In packaged mode, returns a platform-specific user data directory.
    """
    if getattr(sys, "frozen", False):
        system = platform.system()
        if system == "Windows":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif system == "Darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path.home() / ".local" / "share"
        return base / "OpenHarmonyFileBrowser"
    return Path(__file__).parent.parent.parent / "config"
