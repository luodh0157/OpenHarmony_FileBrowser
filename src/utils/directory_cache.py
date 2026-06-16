"""
目录缓存 - 缓存远程目录内容，避免重复 HDC 查询
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta

from src.models.file_info import FileInfo
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DirectoryCache:
    """
    目录内容缓存

    功能:
    - 缓存每个目录的 FileInfo 列表
    - 支持 TTL 过期
    - 支持手动失效化（文件操作后清除相关缓存）
    """

    def __init__(self, ttl_seconds: int = 30):
        """
        初始化目录缓存

        Args:
            ttl_seconds: 缓存有效期（秒）
        """
        self._cache: Dict[str, tuple] = {}  # path -> (files, timestamp)
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self, path: str) -> Optional[List[FileInfo]]:
        """
        获取缓存的目录内容

        Args:
            path: 目录路径

        Returns:
            缓存的 FileInfo 列表，如果不存在或已过期则返回 None
        """
        if path not in self._cache:
            return None

        files, timestamp = self._cache[path]
        if datetime.now() - timestamp > self._ttl:
            del self._cache[path]
            logger.debug(f"Cache expired for: {path}")
            return None

        logger.debug(f"Cache hit for: {path} ({len(files)} items)")
        return files

    def put(self, path: str, files: List[FileInfo]) -> None:
        """
        缓存目录内容

        Args:
            path: 目录路径
            files: FileInfo 列表
        """
        self._cache[path] = (files, datetime.now())
        logger.debug(f"Cached directory: {path} ({len(files)} items)")

    def invalidate(self, path: str) -> None:
        """
        使指定目录缓存失效

        Args:
            path: 目录路径
        """
        if path in self._cache:
            del self._cache[path]
            logger.debug(f"Invalidated cache for: {path}")

    def invalidate_parent(self, path: str) -> None:
        """
        使指定路径的父目录缓存失效

        Args:
            path: 文件或目录路径
        """
        if path == "/":
            return
        parent = path.rstrip("/").rsplit("/", 1)[0] or "/"
        self.invalidate(parent)

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        logger.debug("Directory cache cleared")

    def get_child_dirs(self, path: str) -> List[FileInfo]:
        """
        从缓存中获取指定目录下的子目录（不查询远程）

        Args:
            path: 目录路径

        Returns:
            子目录的 FileInfo 列表，如果缓存不存在则返回空列表
        """
        cached = self.get(path)
        if cached is None:
            return []
        return [f for f in cached if f.is_dir]
