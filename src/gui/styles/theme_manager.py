"""
主题管理器 - 管理应用的主题切换和样式加载
支持亮色/暗色主题切换，并保存用户偏好
"""

from pathlib import Path
from typing import Optional
import json
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow

from src.utils.icon_manager import icon_manager
from src.utils.logger import get_logger


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
        self.current_theme = 'light'
        
        # 样式文件路径 - 修正路径错误
        self.styles_dir = Path(__file__).parent.parent.parent / "gui" / "styles"
        
        # 配置文件路径
        self.config_file = Path.home() / '.opencode' / 'file_browser_config.json'
        
        # 加载用户偏好
        self.load_preference()
    
    def load_preference(self):
        """
        加载用户主题偏好
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    preferred_theme = config.get('theme', 'light')
                    if preferred_theme in ['light', 'dark']:
                        self.current_theme = preferred_theme
                        logger.info(f"Loaded user theme preference: {preferred_theme}")
        except Exception as e:
            logger.warning(f"Failed to load theme preference: {e}")
    
    def save_preference(self):
        """
        保存用户主题偏好
        """
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['theme'] = self.current_theme
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved user theme preference: {self.current_theme}")
        except Exception as e:
            logger.error(f"Failed to save theme preference: {e}")
    
    def set_theme(self, theme: str):
        """
        设置主题
        
        Args:
            theme: 'light' 或 'dark'
        """
        if theme not in ['light', 'dark']:
            logger.warning(f"Invalid theme: {theme}")
            return
        
        if self.current_theme == theme:
            return
        
        self.current_theme = theme
        
        # 应用样式表
        self.apply_stylesheet()
        
        # 更新图标主题
        icon_manager.set_theme(theme)
        
        # 保存用户偏好
        self.save_preference()
        
        # 发送主题切换信号
        self.theme_changed.emit(theme)
        
        logger.info(f"Theme changed to: {theme}")
    
    def toggle_theme(self):
        """
        切换主题（亮色 <-> 暗色）
        """
        if self.current_theme == 'light':
            self.set_theme('dark')
        else:
            self.set_theme('light')
    
    def apply_stylesheet(self):
        """
        应用当前主题的样式表
        """
        try:
            qss_file = self.styles_dir / f"modern_{self.current_theme}.qss"
            
            if qss_file.exists():
                with open(qss_file, 'r', encoding='utf-8') as f:
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
        icon_name = 'sun' if self.current_theme == 'dark' else 'moon'
        return icon_manager.get_icon(icon_name)
    
    def refresh_icons(self):
        """
        刷新所有图标（主题切换后）
        
        注意：这个方法需要在MainWindow中实现具体的刷新逻辑
        """
        # 信号已经发出，MainWindow会处理图标刷新
        pass