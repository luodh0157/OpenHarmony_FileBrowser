"""
语言管理器 - 管理应用的中英文切换
支持国际化，保存用户偏好
"""

from pathlib import Path
from typing import Dict, Any
import json
from PySide6.QtCore import QObject, Signal


from src.utils.logger import get_logger


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
        """初始化语言管理器"""
        super().__init__()
        
        self.current_language = 'en'
        self.translations: Dict[str, Any] = {}
        
        # 翻译文件路径
        self.i18n_dir = Path(__file__).parent.parent.parent / "resources" / "i18n"
        
        # 配置文件路径
        self.config_file = Path.home() / '.opencode' / 'file_browser_config.json'
        
        # 加载用户偏好
        self.load_preference()
        
        # 加载翻译文件
        self.load_translations()
    
    def load_preference(self):
        """加载用户语言偏好"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    preferred_lang = config.get('language', 'en')
                    if preferred_lang in ['en', 'zh']:
                        self.current_language = preferred_lang
                        logger.info(f"Loaded user language preference: {preferred_lang}")
        except Exception as e:
            logger.warning(f"Failed to load language preference: {e}")
    
    def save_preference(self):
        """保存用户语言偏好"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['language'] = self.current_language
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved user language preference: {self.current_language}")
        except Exception as e:
            logger.error(f"Failed to save language preference: {e}")
    
    def load_translations(self):
        """加载当前语言的翻译文件"""
        try:
            translation_file = self.i18n_dir / f"{self.current_language}.json"
            
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
        
        # 保存用户偏好
        self.save_preference()
        
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