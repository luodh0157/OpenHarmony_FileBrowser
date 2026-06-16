"""
异步目录加载线程 - 提升目录浏览性能
"""

from PySide6.QtCore import QThread, Signal

from src.core.file_operations import FileOperations
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DirectoryLoadThread(QThread):
    """
    异步加载目录内容的线程

    在后台执行目录加载，避免阻塞UI线程
    """

    loaded = Signal(list)  # 加载完成信号，传递文件列表
    error = Signal(str)  # 加载失败信号，传递错误消息

    def __init__(self, file_ops: FileOperations, path: str, show_hidden: bool = True):
        """
        初始化目录加载线程

        Args:
            file_ops: 文件操作实例
            path: 要加载的目录路径
            show_hidden: 是否显示隐藏文件
        """
        super().__init__()

        self.file_ops = file_ops
        self.path = path
        self.show_hidden = show_hidden
        self.is_cancelled = False

        logger.debug(f"DirectoryLoadThread created for path: {path}")

    def run(self):
        """
        在线程中执行目录加载

        加载完成后通过信号通知主线程
        """
        try:
            logger.info(
                f"Loading directory asynchronously: {self.path} (show_hidden={self.show_hidden})"
            )

            # 执行目录加载（可能耗时）
            files = self.file_ops.list_directory(
                self.path, show_hidden=self.show_hidden
            )

            # 检查是否被取消
            if self.is_cancelled:
                logger.info(f"Directory loading cancelled: {self.path}")
                return

            # 发射加载完成信号
            self.loaded.emit(files)

            logger.info(
                f"Directory loaded successfully: {self.path}, {len(files)} files"
            )

        except Exception as e:
            if not self.is_cancelled:
                logger.error(f"Failed to load directory {self.path}: {e}")
                self.error.emit(str(e))
        finally:
            self.deleteLater()

    def cancel(self):
        """
        取消加载

        标记线程为已取消状态，线程会在适当时机停止
        """
        self.is_cancelled = True
        logger.debug(f"Directory loading marked as cancelled: {self.path}")
