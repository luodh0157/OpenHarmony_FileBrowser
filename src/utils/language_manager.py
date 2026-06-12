"""
语言管理器 - 管理应用的中英文切换
支持国际化，保存用户偏好
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
from PySide6.QtCore import QObject, Signal


from src.utils.logger import get_logger
from src.config import config


_resource_cache = {}

def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and PyInstaller."""
    if relative_path in _resource_cache:
        return _resource_cache[relative_path]
    
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent.parent
    
    result = base_path / relative_path
    _resource_cache[relative_path] = result
    return result


logger = get_logger(__name__)


class LanguageManager(QObject):
    """
    语言管理器
    
    功能：
    - 加载翻译文件
    - 切换语言
    - 提供翻译API
    - 保存用户偏好
    """
    
    language_changed = Signal(str)  # 语言切换信号
    
    def __init__(self):
        """初始化语言管理器（延迟加载翻译文件）"""
        super().__init__()
        
        self.current_language = config.language
        self.translations: Dict[str, Any] = {}
        self._loaded = False
        
        # 翻译文件路径（延迟解析）
        self._i18n_dir: Optional[Path] = None
    
    def _ensure_loaded(self):
        """确保翻译文件已加载（懒加载）"""
        if self._loaded:
            return
        self.load_translations()
        self._loaded = True
    
    def load_translations(self):
        """加载当前语言的翻译文件"""
        if self._i18n_dir is None:
            self._i18n_dir = get_resource_path("resources/i18n")
        
        try:
            translation_file = self._i18n_dir / f"{self.current_language}.json"
            
            if translation_file.exists():
                with open(translation_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                    logger.info(f"Loaded translations from: {translation_file}")
            else:
                logger.error(f"Translation file not found: {translation_file}")
                self.translations = {}
        except Exception as e:
            logger.error(f"Failed to load translations: {e}")
            self.translations = {}
        
        self._loaded = True
    
    def set_language(self, language: str):
        """
        设置语言
        
        Args:
            language: 'en' 或 'zh'
        """
        if language not in ['en', 'zh']:
            logger.warning(f"Invalid language: {language}")
            return
        
        if self.current_language == language:
            return
        
        self.current_language = language
        
        # 重新加载翻译
        self.load_translations()
        
        # 保存到统一配置
        config.language = language
        config.save()
        
        # 发送语言切换信号
        self.language_changed.emit(language)
        
        logger.info(f"Language changed to: {language}")
    
    def toggle_language(self):
        """切换语言（英文 <-> 中文）"""
        if self.current_language == 'en':
            self.set_language('zh')
        else:
            self.set_language('en')
    
    def tr(self, key: str, **kwargs) -> str:
        """
        翻译文本
        
        Args:
            key: 翻译键（支持嵌套，如 'toolbar.refresh'）
            **kwargs: 模板变量（用于替换 {var}）
        
        Returns:
            翻译后的文本
        """
        self._ensure_loaded()
        
        # 解析嵌套键
        keys = key.split('.')
        value = self.translations
        
        try:
            for k in keys:
                value = value[k]
            
            # 如果是字符串，替换模板变量
            if isinstance(value, str) and kwargs:
                for var_name, var_value in kwargs.items():
                    value = value.replace(f"{{{var_name}}}", str(var_value))
            
            return str(value) if value else key
        except (KeyError, TypeError) as e:
            logger.warning(f"Translation key not found: {key} ({e})")
            return key  # 如果找不到翻译，返回原始键
    
    def get_language_name(self) -> str:
        """获取当前语言的显示名称"""
        return '中文' if self.current_language == 'zh' else 'English'


# 全局语言管理器实例
language_manager = LanguageManager()