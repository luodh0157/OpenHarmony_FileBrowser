"""
主题管理器 - 管理应用的主题切换和样式加载
支持亮色/暗色主题切换，并保存用户偏好
"""

import sys
from pathlib import Path
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow

from src.utils.icon_manager import icon_manager
from src.utils.logger import get_logger
from src.config import config

_resource_cache = {}


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and PyInstaller."""
    if relative_path in _resource_cache:
        return _resource_cache[relative_path]

    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent.parent.parent

    result = base_path / relative_path
    _resource_cache[relative_path] = result
    return result


logger = get_logger(__name__)


class ThemeManager(QObject):
    """
    主题管理器

    功能：
    - 加载和切换主题
    - 管理图标主题
    - 保存用户偏好
    - 刷新UI组件
    """

    theme_changed = Signal(str)  # 主题切换信号

    def __init__(self, main_window: QMainWindow):
        """
        初始化主题管理器

        Args:
            main_window: 主窗口实例
        """
        super().__init__()

        self.main_window = main_window
        self.current_theme = config.theme

        # 样式文件路径
        self.styles_dir = get_resource_path("resources/styles")

    def set_theme(self, theme: str):
        """
        设置主题

        Args:
            theme: 'light' 或 'dark'
        """
        if theme not in ["light", "dark"]:
            logger.warning(f"Invalid theme: {theme}")
            return

        if self.current_theme == theme:
            return

        self.current_theme = theme

        # 应用样式表
        self.apply_stylesheet()

        # 更新图标主题
        icon_manager.set_theme(theme)

        # 保存到统一配置
        config.theme = theme
        config.save()

        # 发送主题切换信号
        self.theme_changed.emit(theme)

        logger.info(f"Theme changed to: {theme}")

    def toggle_theme(self):
        """
        切换主题（亮色 <-> 暗色）
        """
        if self.current_theme == "light":
            self.set_theme("dark")
        else:
            self.set_theme("light")

    def apply_stylesheet(self):
        """
        应用当前主题的样式表
        """
        try:
            qss_file = self.styles_dir / f"modern_{self.current_theme}.qss"

            if qss_file.exists():
                with open(qss_file, "r", encoding="utf-8") as f:
                    stylesheet = f.read()
                    self.main_window.setStyleSheet(stylesheet)
                    logger.info(f"Applied stylesheet: {qss_file}")
            else:
                logger.error(f"Stylesheet file not found: {qss_file}")
        except Exception as e:
            logger.error(f"Failed to apply stylesheet: {e}")

    def get_theme_icon(self) -> QAction:
        """
        获取主题切换按钮的图标

        Returns:
            当前主题对应的图标（sun或moon）
        """
        icon_name = "sun" if self.current_theme == "dark" else "moon"
        return icon_manager.get_icon(icon_name)

    def refresh_icons(self):
        """
        刷新所有图标（主题切换后）

        注意：这个方法需要在MainWindow中实现具体的刷新逻辑
        """
        # 信号已经发出，MainWindow会处理图标刷新
        pass
