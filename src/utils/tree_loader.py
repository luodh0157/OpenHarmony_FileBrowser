"""
异步文件树加载线程 - 避免展开目录时阻塞UI
"""

from typing import List
from PySide6.QtCore import QThread, Signal

from src.core.file_operations import FileOperations
from src.models.file_info import FileInfo
from src.utils.logger import get_logger


logger = get_logger(__name__)


class TreeLoadThread(QThread):
    """
    异步加载目录子目录列表的线程
    
    只返回目录（用于文件树显示），避免阻塞主线程
    """
    
    loaded = Signal(list)
    error = Signal(str)
    
    def __init__(self, file_ops: FileOperations, path: str):
        super().__init__()
        
        self.file_ops = file_ops
        self.path = path
        self.is_cancelled = False
    
    def run(self):
        try:
            logger.debug(f"Loading tree directories asynchronously: {self.path}")
            
            files = self.file_ops.list_directory(self.path, show_hidden=False)
            
            if self.is_cancelled:
                logger.debug(f"Tree loading cancelled: {self.path}")
                return
            
            dirs = [f for f in files if f.is_dir]
            self.loaded.emit(dirs)
            
            logger.debug(f"Tree loaded successfully: {self.path}, {len(dirs)} dirs")
        
        except Exception as e:
            if not self.is_cancelled:
                logger.error(f"Failed to load tree directories {self.path}: {e}")
                self.error.emit(str(e))
        finally:
            self.deleteLater()
    
    def cancel(self):
        self.is_cancelled = True
        logger.debug(f"Tree loading marked as cancelled: {self.path}")
