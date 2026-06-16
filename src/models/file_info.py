"""
File information model for OpenHarmony File Browser.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class FileType(Enum):
    """File type enumeration."""

    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    UNKNOWN = "unknown"


@dataclass
class FileInfo:
    """
    File information data class.

    Attributes:
        name: File name
        path: Full file path
        is_dir: Whether it's a directory
        size: File size in bytes
        permissions: File permissions (e.g., 'drwxr-xr-x')
        modified_time: Last modified time
        file_type: File type
        owner: File owner
        group: File group
        links: Number of hard links
    """

    name: str
    path: str
    is_dir: bool = False
    size: int = 0
    permissions: str = ""
    modified_time: Optional[datetime] = None
    file_type: FileType = FileType.FILE
    owner: Optional[str] = None
    group: Optional[str] = None
    links: int = 1

    def __str__(self) -> str:
        """String representation."""
        type_str = "DIR" if self.is_dir else "FILE"
        return f"[{type_str}] {self.name} ({self.size} bytes)"

    def __repr__(self) -> str:
        """Repr representation."""
        return (
            f"FileInfo(name='{self.name}', path='{self.path}', "
            f"is_dir={self.is_dir}, size={self.size})"
        )

    @property
    def extension(self) -> str:
        """Get file extension."""
        if self.is_dir:
            return ""
        return Path(self.name).suffix.lower()

    @property
    def display_size(self) -> str:
        """Get human-readable size."""
        from ..utils.file_utils import format_file_size

        return format_file_size(self.size)

    @property
    def display_time(self) -> str:
        """Get formatted modified time."""
        if self.modified_time:
            return self.modified_time.strftime("%Y-%m-%d %H:%M:%S")
        return ""

    @property
    def icon_type(self) -> str:
        """Get icon type for this file."""
        from ..utils.file_utils import get_file_type

        if self.is_dir:
            return "folder"
        return get_file_type(self.name, False)
