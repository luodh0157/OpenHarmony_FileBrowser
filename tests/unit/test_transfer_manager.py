"""
Unit tests for transfer manager (src/core/transfer_manager.py).
"""

from src.core.transfer_manager import (
    TransferDirection,
    TransferStatus,
    TransferTask,
    TransferManager,
)


class TestTransferDirection:
    """Tests for TransferDirection enum."""

    def test_upload_value(self):
        assert TransferDirection.UPLOAD.value == "upload"

    def test_download_value(self):
        assert TransferDirection.DOWNLOAD.value == "download"

    def test_direction_count(self):
        assert len(TransferDirection) == 2


class TestTransferStatus:
    """Tests for TransferStatus enum."""

    def test_pending_value(self):
        assert TransferStatus.PENDING.value == "pending"

    def test_running_value(self):
        assert TransferStatus.RUNNING.value == "running"

    def test_completed_value(self):
        assert TransferStatus.COMPLETED.value == "completed"

    def test_failed_value(self):
        assert TransferStatus.FAILED.value == "failed"

    def test_cancelled_value(self):
        assert TransferStatus.CANCELLED.value == "cancelled"

    def test_status_count(self):
        assert len(TransferStatus) == 5


class TestTransferTask:
    """Tests for TransferTask dataclass."""

    def test_create_upload_task(self):
        task = TransferTask(
            local_path="/tmp/test.txt",
            remote_path="/data/local/tmp/test.txt",
            direction=TransferDirection.UPLOAD,
            device_id="test_device",
        )
        assert task.local_path == "/tmp/test.txt"
        assert task.remote_path == "/data/local/tmp/test.txt"
        assert task.direction == TransferDirection.UPLOAD
        assert task.device_id == "test_device"
        assert task.status == TransferStatus.PENDING
        assert task.progress == 0
        assert task.total_size == 0
        assert task.transferred_size == 0
        assert task.speed == 0.0
        assert task.error is None
        assert task.start_time is None
        assert task.end_time is None
        assert task.preserve_timestamp is True

    def test_create_download_task(self):
        task = TransferTask(
            local_path="/tmp/test.txt",
            remote_path="/data/local/tmp/test.txt",
            direction=TransferDirection.DOWNLOAD,
            device_id="test_device",
        )
        assert task.direction == TransferDirection.DOWNLOAD

    def test_task_with_size(self):
        task = TransferTask(
            local_path="/tmp/test.txt",
            remote_path="/data/local/tmp/test.txt",
            direction=TransferDirection.UPLOAD,
            device_id="test_device",
            total_size=1024,
        )
        assert task.total_size == 1024

    def test_task_with_error(self):
        task = TransferTask(
            local_path="/tmp/test.txt",
            remote_path="/data/local/tmp/test.txt",
            direction=TransferDirection.UPLOAD,
            device_id="test_device",
            status=TransferStatus.FAILED,
            error="Connection lost",
        )
        assert task.status == TransferStatus.FAILED
        assert task.error == "Connection lost"

    def test_task_timestamp_preservation(self):
        task = TransferTask(
            local_path="/tmp/test.txt",
            remote_path="/data/local/tmp/test.txt",
            direction=TransferDirection.UPLOAD,
            device_id="test_device",
            original_mtime=1700000000.0,
            preserve_timestamp=True,
        )
        assert task.original_mtime == 1700000000.0
        assert task.preserve_timestamp is True


class TestTransferManager:
    """Tests for TransferManager class."""

    def test_create_manager_default_workers(self):
        manager = TransferManager()
        assert manager.max_workers == 3
        assert len(manager.tasks) == 0

    def test_create_manager_custom_workers(self):
        manager = TransferManager(max_workers=5)
        assert manager.max_workers == 5

    def test_add_upload_task(self):
        manager = TransferManager()
        manager.add_upload_task(
            device_id="test_device",
            local_path="/tmp/test.txt",
            remote_path="/data/local/tmp/test.txt",
        )
        assert len(manager.tasks) == 1
        assert manager.tasks[0].direction == TransferDirection.UPLOAD

    def test_add_download_task(self):
        manager = TransferManager()
        manager.add_download_task(
            device_id="test_device",
            remote_path="/data/local/tmp/test.txt",
            local_path="/tmp/test.txt",
        )
        assert len(manager.tasks) == 1
        assert manager.tasks[0].direction == TransferDirection.DOWNLOAD

    def test_add_task_with_preserve_timestamp(self):
        manager = TransferManager()
        manager.add_upload_task(
            device_id="test_device",
            local_path="/tmp/test.txt",
            remote_path="/data/local/tmp/test.txt",
            preserve_timestamp=True,
        )
        assert len(manager.tasks) == 1
        assert manager.tasks[0].preserve_timestamp is True

    def test_get_task_status_by_path(self):
        manager = TransferManager()
        manager.add_upload_task(
            device_id="test_device",
            local_path="/tmp/test.txt",
            remote_path="/data/local/tmp/test.txt",
        )
        task = manager.get_task_status("/tmp/test.txt")
        assert task is not None
        assert task.local_path == "/tmp/test.txt"

    def test_get_nonexistent_task_status(self):
        manager = TransferManager()
        task = manager.get_task_status("/nonexistent/path")
        assert task is None

    def test_clear_completed_tasks(self):
        manager = TransferManager()
        manager.add_upload_task(
            device_id="test_device",
            local_path="/tmp/test1.txt",
            remote_path="/data/local/tmp/test1.txt",
        )
        manager.tasks[0].status = TransferStatus.COMPLETED
        manager.add_upload_task(
            device_id="test_device",
            local_path="/tmp/test2.txt",
            remote_path="/data/local/tmp/test2.txt",
        )
        assert len(manager.tasks) == 2

        manager.clear_completed_tasks()
        assert len(manager.tasks) == 1

    def test_cancel_all(self):
        manager = TransferManager()
        manager.add_upload_task(
            device_id="test_device",
            local_path="/tmp/test.txt",
            remote_path="/data/local/tmp/test.txt",
        )
        manager.cancel_all()
        assert len(manager.tasks) == 1
