"""
图标管理器 - 使用SVG图标提供现代、高清的图标系统
支持亮色和暗色主题切换
"""

import sys
from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, QObject, Signal

_resource_cache = {}


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and PyInstaller."""
    if relative_path in _resource_cache:
        return _resource_cache[relative_path]

    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent.parent

    result = base_path / relative_path
    _resource_cache[relative_path] = result
    return result


class IconManager(QObject):
    """
    SVG图标管理器

    提供高清SVG图标，支持亮色/暗色主题自动切换
    """

    theme_changed = Signal(str)  # 主题切换信号

    def __init__(self):
        """初始化图标管理器"""
        super().__init__()

        self.current_theme = "light"
        self.icon_size = QSize(24, 24)  # 增大图标大小

        # 图标资源目录
        self.icons_dir = get_resource_path("resources/icons")

        # 图标缓存
        self.icon_cache = {}

        # 图标名称映射
        self.icon_names = {
            "folder": "folder",
            "file": "file",
            "image": "image",
            "video": "video",
            "music": "music",
            "document": "document",
            "archive": "archive",
            "code": "code",
            "refresh": "refresh",
            "refresh_devices": "refresh_devices",
            "upload": "upload",
            "download": "download",
            "delete": "delete",
            "rename": "rename",
            "new_folder": "new_folder",
            "sun": "sun",
            "moon": "moon",
            "arrow_down": "arrow_down",
        }

    def set_theme(self, theme: str):
        """
        设置主题

        Args:
            theme: 'light' 或 'dark'
        """
        if theme not in ["light", "dark"]:
            return

        if self.current_theme != theme:
            self.current_theme = theme
            self.icon_cache.clear()  # 清空缓存，重新加载图标
            self.theme_changed.emit(theme)

    def get_icon(self, name: str) -> QIcon:
        """
        获取图标

        Args:
            name: 图标名称

        Returns:
            QIcon 对象
        """
        # 检查缓存
        cache_key = f"{name}_{self.current_theme}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]

        # 获取图标文件名
        icon_file = self.icon_names.get(name, name)

        # 加载SVG图标
        icon_path = self.icons_dir / self.current_theme / f"{icon_file}.svg"

        if icon_path.exists():
            # 使用QIcon直接加载SVG，支持矢量缩放
            icon = QIcon(str(icon_path))
            # 缓存图标
            self.icon_cache[cache_key] = icon
            return icon

        # 如果图标不存在，返回空图标
        return QIcon()

    def get_file_type_icon(self, file_name: str, is_dir: bool = False) -> QIcon:
        """
        根据文件类型获取图标

        Args:
            file_name: 文件名
            is_dir: 是否是目录

        Returns:
            QIcon 对象
        """
        if is_dir:
            return self.get_icon("folder")

        # 根据文件扩展名判断类型
        extension = file_name.lower().split(".")[-1] if "." in file_name else ""

        # 图片文件
        image_extensions = ["png", "jpg", "jpeg", "gif", "bmp", "svg", "webp"]
        if extension in image_extensions:
            return self.get_icon("image")

        # 视频文件
        video_extensions = ["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm"]
        if extension in video_extensions:
            return self.get_icon("video")

        # 音乐文件
        music_extensions = ["mp3", "wav", "flac", "aac", "ogg", "m4a"]
        if extension in music_extensions:
            return self.get_icon("music")

        # 文档文件
        document_extensions = [
            "pdf",
            "doc",
            "docx",
            "xls",
            "xlsx",
            "ppt",
            "pptx",
            "txt",
            "md",
        ]
        if extension in document_extensions:
            return self.get_icon("document")

        # 压缩文件
        archive_extensions = ["zip", "rar", "tar", "gz", "7z", "bz2"]
        if extension in archive_extensions:
            return self.get_icon("archive")

        # 代码文件
        code_extensions = [
            "py",
            "js",
            "java",
            "cpp",
            "c",
            "h",
            "cs",
            "rb",
            "go",
            "rs",
            "ts",
        ]
        if extension in code_extensions:
            return self.get_icon("code")

        # 默认文件图标
        return self.get_icon("file")


# 全局图标管理器实例
icon_manager = IconManager()
