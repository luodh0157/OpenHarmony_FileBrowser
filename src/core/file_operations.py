"""
File operations core for OpenHarmony File Browser.
Provides file browsing and basic file operations.
"""

from typing import List

from .hdc_wrapper import HDCWrapper, HDCError
from ..models.file_info import FileInfo
from ..utils.logger import get_logger
from ..utils.directory_cache import DirectoryCache

logger = get_logger(__name__)

# Shared directory cache per device (class-level)
_device_caches: dict = {}


def _get_device_cache(device_id: str) -> DirectoryCache:
    """Get or create directory cache for a device."""
    if device_id not in _device_caches:
        _device_caches[device_id] = DirectoryCache(ttl_seconds=30)
    return _device_caches[device_id]


def clear_device_cache(device_id: str) -> None:
    """Clear directory cache for a device."""
    if device_id in _device_caches:
        _device_caches[device_id].clear()
        del _device_caches[device_id]


class FileOperations:
    """
    File operations handler for OpenHarmony devices.

    Provides file browsing and basic operations like:
    - List files and directories
    - Create directory
    - Delete files/folders
    - Rename files/folders
    """

    def __init__(self, hdc: HDCWrapper, device_id: str):
        """
        Initialize file operations.

        Args:
            hdc: HDC wrapper instance
            device_id: Device ID to operate on
        """
        self.hdc = hdc
        self.device_id = device_id
        self.cache = _get_device_cache(device_id)

        logger.info(f"FileOperations initialized for device: {device_id}")

    def list_directory(
        self, path: str, show_hidden: bool = False, use_cache: bool = True
    ) -> List[FileInfo]:
        """
        List files in a directory.

        Args:
            path: Directory path
            show_hidden: Whether to show hidden files
            use_cache: Whether to use cached results (default True)

        Returns:
            List of FileInfo objects

        Raises:
            HDCError: If operation fails
        """
        logger.debug(f"Listing directory: {path}")

        # Try cache first
        if use_cache and not show_hidden:
            cached = self.cache.get(path)
            if cached is not None:
                return cached

        try:
            files = self.hdc.shell_ls(self.device_id, path, show_hidden)

            # Cache the result
            if not show_hidden:
                self.cache.put(path, files)

            logger.info(f"Found {len(files)} items in {path}")
            return files

        except HDCError as e:
            logger.error(f"Failed to list directory {path}: {e}")
            raise

    def get_file_info(self, path: str) -> FileInfo:
        """
        Get detailed file information.

        Args:
            path: File path

        Returns:
            FileInfo object

        Raises:
            HDCError: If operation fails
        """
        logger.debug(f"Getting file info: {path}")

        try:
            info = self.hdc.shell_stat(self.device_id, path)

            logger.debug(f"File info retrieved: {path}")
            return info

        except HDCError as e:
            logger.error(f"Failed to get file info {path}: {e}")
            raise

    def create_directory(self, path: str) -> bool:
        """
        Create a directory.

        Args:
            path: Directory path to create

        Returns:
            True if successful

        Raises:
            HDCError: If operation fails
        """
        logger.info(f"Creating directory: {path}")

        try:
            self.hdc.shell_mkdir(self.device_id, path)

            # Invalidate parent directory cache
            self.cache.invalidate_parent(path)

            logger.info(f"Directory created: {path}")
            return True

        except HDCError as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise

    def delete_file(self, path: str, recursive: bool = False) -> bool:
        """
        Delete a file or directory.

        Args:
            path: Path to delete
            recursive: Delete recursively (for directories)

        Returns:
            True if successful

        Raises:
            HDCError: If operation fails
        """
        logger.info(f"Deleting: {path} (recursive={recursive})")

        try:
            self.hdc.shell_rm(self.device_id, path, recursive=recursive)

            # Invalidate the deleted path and parent directory cache
            self.cache.invalidate(path)
            self.cache.invalidate_parent(path)
            if recursive:
                self.cache.clear()  # Conservative: clear all on recursive delete

            logger.info(f"Deleted: {path}")
            return True

        except HDCError as e:
            logger.error(f"Failed to delete {path}: {e}")
            raise

    def rename_file(self, old_path: str, new_path: str) -> bool:
        """
        Rename or move a file/directory.

        Args:
            old_path: Original path
            new_path: New path

        Returns:
            True if successful

        Raises:
            HDCError: If operation fails
        """
        logger.info(f"Renaming: {old_path} -> {new_path}")

        try:
            self.hdc.shell_mv(self.device_id, old_path, new_path)

            # Invalidate both old and new parent directory caches
            self.cache.invalidate(old_path)
            self.cache.invalidate(new_path)
            self.cache.invalidate_parent(old_path)
            self.cache.invalidate_parent(new_path)

            logger.info(f"Renamed: {old_path} -> {new_path}")
            return True

        except HDCError as e:
            logger.error(f"Failed to rename {old_path}: {e}")
            raise

    def exists(self, path: str) -> bool:
        """
        Check if a file/directory exists.

        Args:
            path: Path to check

        Returns:
            True if exists
        """
        logger.debug(f"Checking if exists: {path}")

        try:
            self.hdc.shell_stat(self.device_id, path)
            return True

        except HDCError:
            return False

    def is_directory(self, path: str) -> bool:
        """
        Check if path is a directory.

        Args:
            path: Path to check

        Returns:
            True if is directory
        """
        logger.debug(f"Checking if directory: {path}")

        try:
            info = self.hdc.shell_stat(self.device_id, path)
            return info.is_dir

        except HDCError:
            return False

    def get_parent_directory(self, path: str) -> str:
        """
        Get parent directory of a path.

        Args:
            path: File/directory path

        Returns:
            Parent directory path
        """
        if path == "/" or path == "":
            return "/"

        # Don't use pathlib.Path - it may convert to Windows path style on Windows
        # Use string operations to ensure Unix-style path (with forward slashes)
        path = path.rstrip("/")

        if "/" not in path:
            return "/"

        last_slash = path.rfind("/")

        if last_slash == 0:
            return "/"

        parent = path[:last_slash]

        if parent == "":
            parent = "/"

        return parent

    def join_path(self, base: str, name: str) -> str:
        """
        Join path components.

        Args:
            base: Base directory
            name: File/directory name

        Returns:
            Combined path
        """
        if base == "/":
            return f"/{name}"

        return f"{base.rstrip('/')}/{name}"

    def validate_path(self, path: str) -> bool:
        """
        Validate a path string.

        Args:
            path: Path to validate

        Returns:
            True if valid
        """
        if not path:
            return False

        if not path.startswith("/"):
            return False

        return True

    def normalize_path(self, path: str) -> str:
        """
        Normalize a path string.

        Args:
            path: Path to normalize

        Returns:
            Normalized path (Unix-style with forward slashes)
        """
        if not path:
            return "/"

        # Ensure path starts with /
        if not path.startswith("/"):
            path = f"/{path}"

        # Replace backslashes with forward slashes (for cross-platform compatibility)
        path = path.replace("\\", "/")

        # Split and normalize
        parts = path.split("/")
        normalized = []

        for part in parts:
            if part == "" or part == ".":
                continue
            elif part == "..":
                if normalized:
                    normalized.pop()
            else:
                normalized.append(part)

        result = "/" + "/".join(normalized)

        return result if result else "/"

    def clear_cache(self) -> None:
        """Clear the directory cache for this device."""
        self.cache.clear()
