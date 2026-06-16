"""
File utilities for OpenHarmony File Browser.
Provides file type detection and formatting functions.
"""

from typing import Dict
from pathlib import Path

FILE_TYPE_ICONS: Dict[str, str] = {
    "image": "image",
    "video": "video",
    "audio": "audio",
    "document": "document",
    "archive": "archive",
    "code": "code",
    "folder": "folder",
    "file": "file",
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".svg",
    ".ico",
    ".tiff",
    ".tif",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".3gp",
    ".ogv",
}

AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".flac",
    ".aac",
    ".ogg",
    ".wma",
    ".m4a",
    ".opus",
    ".aiff",
}

DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
    ".rtf",
    ".odt",
    ".ods",
    ".odp",
    ".pages",
    ".numbers",
    ".keynote",
}

ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"}

ARCHIVE_COMPOUND_EXTENSIONS = {".tar.gz", ".tar.bz2", ".tar.xz"}

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".ts",
    ".jsx",
    ".tsx",
    ".vue",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".html",
    ".xml",
    ".json",
    ".yaml",
    ".yml",
    ".sh",
    ".bash",
    ".zsh",
    ".bat",
    ".ps1",
    ".sql",
    ".md",
}


def get_file_type(file_name: str, is_dir: bool = False) -> str:
    """
    Determine file type based on extension.

    Args:
        file_name: File name
        is_dir: Whether it's a directory

    Returns:
        File type string
    """
    if is_dir:
        return "folder"

    path_obj = Path(file_name)
    suffixes = [s.lower() for s in path_obj.suffixes]
    ext = suffixes[-1] if suffixes else ""
    compound_ext = "".join(suffixes[-2:]) if len(suffixes) >= 2 else ""

    if ext in IMAGE_EXTENSIONS:
        return "image"
    elif ext in VIDEO_EXTENSIONS:
        return "video"
    elif ext in AUDIO_EXTENSIONS:
        return "audio"
    elif ext in DOCUMENT_EXTENSIONS:
        return "document"
    elif compound_ext in ARCHIVE_COMPOUND_EXTENSIONS or ext in ARCHIVE_EXTENSIONS:
        return "archive"
    elif ext in CODE_EXTENSIONS:
        return "code"
    else:
        return "file"


def get_file_icon(file_name: str, is_dir: bool = False) -> str:
    """
    Get icon name for a file.

    Args:
        file_name: File name
        is_dir: Whether it's a directory

    Returns:
        Icon name
    """
    file_type = get_file_type(file_name, is_dir)
    return FILE_TYPE_ICONS.get(file_type, "file")


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return (
                f"{size_bytes:.2f} {unit}"
                if unit != "B"
                else f"{int(size_bytes)} {unit}"
            )
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_permissions(permissions: str) -> str:
    """
    Format file permissions for display.

    Args:
        permissions: Permission string (e.g., 'drwxr-xr-x')

    Returns:
        Formatted permission string with spaced groups (e.g., 'd rwx r-x r-x')
    """
    if not permissions or len(permissions) < 10:
        return permissions

    file_type = permissions[0]
    perms = permissions[1:]

    # fmt: off
    chunks = [perms[i:i + 3] for i in range(0, 9, 3)]
    # fmt: on

    return f"{file_type} {chunks[0]} {chunks[1]} {chunks[2]}"


def is_image_file(file_name: str) -> bool:
    """
    Check if file is an image.

    Args:
        file_name: File name

    Returns:
        True if file is an image
    """
    ext = Path(file_name).suffix.lower()
    return ext in IMAGE_EXTENSIONS


def is_video_file(file_name: str) -> bool:
    """
    Check if file is a video.

    Args:
        file_name: File name

    Returns:
        True if file is a video
    """
    ext = Path(file_name).suffix.lower()
    return ext in VIDEO_EXTENSIONS


def is_previewable(file_name: str) -> bool:
    """
    Check if file can be previewed.

    Args:
        file_name: File name

    Returns:
        True if file can be previewed
    """
    return is_image_file(file_name) or is_video_file(file_name)
