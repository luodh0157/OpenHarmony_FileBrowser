"""
Transfer manager for OpenHarmony File Browser.
Manages file transfer operations with progress tracking.
"""

import time
from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QObject, Signal, QThread

from src.core.hdc_wrapper import HDCWrapper, HDCError
from src.utils.logger import get_logger
from src.config import config

logger = get_logger(__name__)


class TransferDirection(Enum):
    """Transfer direction enum."""

    UPLOAD = "upload"
    DOWNLOAD = "download"


class TransferStatus(Enum):
    """Transfer status enum."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TransferTask:
    """Transfer task data class."""

    local_path: str
    remote_path: str
    direction: TransferDirection
    device_id: str
    status: TransferStatus = TransferStatus.PENDING
    progress: int = 0
    total_size: int = 0
    transferred_size: int = 0
    speed: float = 0.0
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    # Original file timestamp
    original_mtime: Optional[float] = (
        None  # Original modification time (Unix timestamp)
    )
    preserve_timestamp: bool = True  # Whether to preserve timestamp


class TransferWorker(QThread):
    """Worker thread for file transfer."""

    progress_updated = Signal(str, int, int, float)
    transfer_completed = Signal(str, bool, str)

    def __init__(self, hdc: HDCWrapper, task: TransferTask):
        """
        Initialize transfer worker.

        Args:
            hdc: HDC wrapper instance
            task: Transfer task
        """
        super().__init__()

        self.hdc = hdc
        self.task = task
        self.running = True

        logger.info(f"Transfer worker created: {task.local_path} -> {task.remote_path}")

    def run(self):
        """Execute transfer."""
        self.task.status = TransferStatus.RUNNING
        self.task.start_time = time.time()

        logger.info(f"Transfer started: {self.task.direction.value}")

        try:
            if self.task.direction == TransferDirection.UPLOAD:
                self._upload_file()
            else:
                self._download_file()

            self.task.status = TransferStatus.COMPLETED
            self.task.end_time = time.time()

            elapsed = self.task.end_time - self.task.start_time
            speed = self.task.total_size / elapsed if elapsed > 0 else 0

            self.progress_updated.emit(
                self.task.local_path, 100, self.task.total_size, speed
            )

            self.transfer_completed.emit(self.task.local_path, True, "")

            logger.info(f"Transfer completed: {self.task.local_path}")

        except HDCError as e:
            self.task.status = TransferStatus.FAILED
            self.task.error = str(e)

            self.transfer_completed.emit(self.task.local_path, False, str(e))

            logger.error(f"Transfer failed: {e}")

        except Exception as e:
            self.task.status = TransferStatus.FAILED
            self.task.error = str(e)

            self.transfer_completed.emit(self.task.local_path, False, str(e))

            logger.error(f"Transfer error: {e}")

    def _upload_file(self):
        """Upload file or directory to device."""
        try:
            from pathlib import Path
            import os

            local_path = Path(self.task.local_path)

            if not local_path.exists():
                raise HDCError(f"Local path not found: {self.task.local_path}")

            if self.task.preserve_timestamp:
                if local_path.is_file():
                    self.task.original_mtime = local_path.stat().st_mtime
                    logger.debug(f"Local file mtime: {self.task.original_mtime}")
                elif local_path.is_dir():
                    self.task.original_mtime = None

            if local_path.is_file():
                self.task.total_size = local_path.stat().st_size
            else:
                self.task.total_size = sum(
                    f.stat().st_size for f in local_path.rglob("*") if f.is_file()
                )

            logger.debug(f"Uploading: {self.task.local_path}")

            self.hdc.file_send(
                self.task.device_id,
                self.task.local_path,
                self.task.remote_path,
                preserve_timestamp=self.task.preserve_timestamp,
            )

            self.task.transferred_size = self.task.total_size

            self.progress_updated.emit(
                self.task.local_path, 100, self.task.total_size, 0
            )

        except HDCError:
            raise
        except Exception as e:
            raise HDCError(f"Upload failed: {e}")

    def _download_file(self):
        """Download file or directory from device with timestamp preservation."""
        try:
            from pathlib import Path
            import os

            local_path = Path(self.task.local_path)

            if self.task.preserve_timestamp:
                try:
                    stat_info = self.hdc.shell_stat(
                        self.task.device_id, self.task.remote_path
                    )
                    if stat_info.modified_time:
                        from datetime import datetime

                        self.task.original_mtime = stat_info.modified_time.timestamp()
                        logger.debug(f"Original mtime: {stat_info.modified_time}")
                except Exception as e:
                    logger.warning(f"Failed to get remote file timestamp: {e}")
                    self.task.original_mtime = None

            if local_path.is_dir() or self.task.remote_path.endswith("/"):
                local_path.mkdir(parents=True, exist_ok=True)
            else:
                local_path.parent.mkdir(parents=True, exist_ok=True)

            self.hdc.file_recv(
                self.task.device_id,
                self.task.remote_path,
                self.task.local_path,
                preserve_timestamp=self.task.preserve_timestamp,
            )

            if self.task.preserve_timestamp and self.task.original_mtime:
                try:
                    if local_path.is_file():
                        os.utime(
                            self.task.local_path,
                            (self.task.original_mtime, self.task.original_mtime),
                        )
                        logger.info(f"Restored file timestamp: {self.task.local_path}")
                    elif local_path.is_dir():
                        self._restore_directory_timestamps(local_path)
                except Exception as e:
                    logger.warning(f"Failed to restore timestamp: {e}")

            if local_path.is_file():
                self.task.total_size = local_path.stat().st_size
                self.task.transferred_size = self.task.total_size
            else:
                self.task.total_size = 0
                self.task.transferred_size = 0

            self.progress_updated.emit(
                self.task.local_path, 100, self.task.total_size, 0
            )

        except HDCError:
            raise
        except Exception as e:
            raise HDCError(f"Download failed: {e}")

    def _restore_directory_timestamps(self, dir_path):
        """Recursively restore timestamps for all files in directory."""
        import os
        from pathlib import Path

        for item in dir_path.rglob("*"):
            if item.is_file():
                try:
                    # Try to get remote file's timestamp
                    relative_path = item.relative_to(dir_path)
                    remote_item_path = (
                        f"{self.task.remote_path.rstrip('/')}/{relative_path}"
                    )

                    try:
                        stat_info = self.hdc.shell_stat(
                            self.task.device_id, remote_item_path
                        )
                        if stat_info.modified_time:
                            mtime = stat_info.modified_time.timestamp()
                            os.utime(str(item), (mtime, mtime))
                    except:
                        # If can't get remote timestamp, use original directory timestamp
                        if self.task.original_mtime:
                            os.utime(
                                str(item),
                                (self.task.original_mtime, self.task.original_mtime),
                            )
                except Exception as e:
                    logger.warning(f"Failed to set timestamp for {item}: {e}")

    def cancel(self):
        """Cancel transfer."""
        self.running = False
        self.task.status = TransferStatus.CANCELLED

        logger.info(f"Transfer cancelled: {self.task.local_path}")


class TransferManager(QObject):
    """
    Transfer manager for managing file transfers.

    Features:
    - Transfer queue management
    - Thread pool control (3-5 workers)
    - Progress tracking
    - Speed calculation
    - Concurrent transfers
    """

    transfer_started = Signal(object)
    transfer_progress = Signal(str, int, int, float)
    transfer_completed = Signal(str, bool, str)
    all_transfers_completed = Signal()

    def __init__(self, hdc: Optional[HDCWrapper] = None, max_workers: int = 3):
        """
        Initialize transfer manager.

        Args:
            hdc: HDC wrapper instance
            max_workers: Maximum concurrent workers
        """
        super().__init__()

        self.hdc = hdc
        self.max_workers = max_workers

        self.tasks: List[TransferTask] = []
        self.workers: Dict[str, TransferWorker] = {}
        self.executor: Optional[ThreadPoolExecutor] = None

        logger.info(f"Transfer manager initialized (max_workers={max_workers})")

    def set_hdc(self, hdc: HDCWrapper):
        """
        Set HDC wrapper.

        Args:
            hdc: HDC wrapper instance
        """
        self.hdc = hdc

        logger.info("HDC wrapper set for transfer manager")

    def add_upload_task(
        self,
        device_id: str,
        local_path: str,
        remote_path: str,
        preserve_timestamp: bool = True,
    ):
        """
        Add upload task.

        Args:
            device_id: Device ID
            local_path: Local file path
            remote_path: Remote file path
            preserve_timestamp: Whether to preserve file timestamp (default True)
        """
        task = TransferTask(
            local_path=local_path,
            remote_path=remote_path,
            direction=TransferDirection.UPLOAD,
            device_id=device_id,
            preserve_timestamp=preserve_timestamp,
        )

        self.tasks.append(task)

        logger.info(
            f"Upload task added: {local_path} -> {remote_path} (preserve_ts={preserve_timestamp})"
        )

    def add_download_task(
        self,
        device_id: str,
        remote_path: str,
        local_path: str,
        preserve_timestamp: bool = True,
    ):
        """
        Add download task.

        Args:
            device_id: Device ID
            remote_path: Remote file path
            local_path: Local file path
            preserve_timestamp: Whether to preserve file timestamp (default True)
        """
        task = TransferTask(
            local_path=local_path,
            remote_path=remote_path,
            direction=TransferDirection.DOWNLOAD,
            device_id=device_id,
            preserve_timestamp=preserve_timestamp,
        )

        self.tasks.append(task)

        logger.info(
            f"Download task added: {remote_path} -> {local_path} (preserve_ts={preserve_timestamp})"
        )

    def start_transfers(self):
        """Start all pending transfers."""
        if not self.hdc:
            logger.error("HDC wrapper not set")
            return

        pending_tasks = [t for t in self.tasks if t.status == TransferStatus.PENDING]

        if not pending_tasks:
            logger.info("No pending tasks")
            return

        logger.info(f"Starting {len(pending_tasks)} transfers")

        for task in pending_tasks:
            worker = TransferWorker(self.hdc, task)

            worker.progress_updated.connect(self._on_progress_updated)
            worker.transfer_completed.connect(self._on_transfer_completed)

            self.workers[task.local_path] = worker

            worker.start()

            self.transfer_started.emit(task)

        logger.info("All transfers started")

    def _on_progress_updated(self, path: str, progress: int, size: int, speed: float):
        """Handle progress update."""
        self.transfer_progress.emit(path, progress, size, speed)

        logger.debug(f"Progress: {path} - {progress}%")

    def _on_transfer_completed(self, path: str, success: bool, error: str):
        """Handle transfer completion."""
        if path in self.workers:
            worker = self.workers[path]
            worker.deleteLater()
            del self.workers[path]

        self.transfer_completed.emit(path, success, error)

        running = [t for t in self.tasks if t.status == TransferStatus.RUNNING]

        if not running:
            self.all_transfers_completed.emit()
            logger.info("All transfers completed")

    def cancel_all(self):
        """Cancel all transfers."""
        for worker in self.workers.values():
            worker.cancel()

        logger.info("All transfers cancelled")

    def get_task_status(self, path: str) -> Optional[TransferTask]:
        """
        Get task status by path.

        Args:
            path: File path

        Returns:
            TransferTask or None
        """
        for task in self.tasks:
            if task.local_path == path:
                return task

        return None

    def clear_completed_tasks(self):
        """Clear completed tasks from list."""
        completed = [
            t
            for t in self.tasks
            if t.status
            in [
                TransferStatus.COMPLETED,
                TransferStatus.FAILED,
                TransferStatus.CANCELLED,
            ]
        ]

        for task in completed:
            self.tasks.remove(task)

        logger.info(f"Cleared {len(completed)} completed tasks")

    def cleanup(self):
        """Cleanup resources."""
        self.cancel_all()

        for worker in self.workers.values():
            worker.wait()
            worker.deleteLater()

        self.workers.clear()

        logger.info("Transfer manager cleanup completed")
