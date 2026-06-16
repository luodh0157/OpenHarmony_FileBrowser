"""
Integration tests for OpenHarmony File Browser.

These tests verify that components work together correctly.
"""

import pytest
from PySide6.QtWidgets import QApplication
import sys


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication instance for the test module."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestModelIntegration:
    """Tests for model integration."""

    def test_device_info_with_file_info(self):
        from src.models.device import DeviceInfo, DeviceStatus
        from src.models.file_info import FileInfo

        device = DeviceInfo(
            device_id="test_device",
            status=DeviceStatus.CONNECTED,
            model="Test Device",
        )
        assert device.is_ready is True

        file_info = FileInfo(
            name="test.txt",
            path="/data/test.txt",
            size=1024,
        )
        assert file_info.display_size == "1.00 KB"

    def test_file_info_uses_file_utils(self):
        from src.models.file_info import FileInfo

        file_info = FileInfo(
            name="photo.jpg",
            path="/data/photo.jpg",
        )
        assert file_info.icon_type == "image"
        assert file_info.extension == ".jpg"


class TestCoreIntegration:
    """Tests for core module integration."""

    @pytest.fixture
    def mock_hdc(self):
        class MockHdc:
            def shell_ls(self, device_id, path, show_hidden=False):
                from src.models.file_info import FileInfo, FileType

                return [
                    FileInfo(
                        name="file1.txt",
                        path=f"{path}/file1.txt",
                        is_dir=False,
                        size=100,
                        file_type=FileType.FILE,
                    ),
                    FileInfo(
                        name="folder1",
                        path=f"{path}/folder1",
                        is_dir=True,
                        file_type=FileType.DIRECTORY,
                    ),
                ]

            def shell_stat(self, device_id, path):
                from src.models.file_info import FileInfo, FileType

                return FileInfo(
                    name="test", path=path, is_dir=True, file_type=FileType.DIRECTORY
                )

            def shell_mkdir(self, device_id, path):
                pass

            def shell_rm(self, device_id, path, recursive=False):
                pass

            def shell_mv(self, device_id, old_path, new_path):
                pass

            def file_send(self, device_id, local_path, remote_path):
                pass

            def file_recv(self, device_id, remote_path, local_path):
                pass

        return MockHdc()

    def test_file_operations_with_mock_hdc(self, mock_hdc):
        from src.core.file_operations import FileOperations

        ops = FileOperations(mock_hdc, "test_device")
        files = ops.list_directory("/data/local/tmp")
        assert len(files) == 2
        assert files[0].name == "file1.txt"
        assert files[1].name == "folder1"

    def test_preview_handler_with_mock_hdc(self, mock_hdc):
        from src.core.preview_handler import PreviewHandler

        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.can_preview("test.jpg", 1024) is True
        assert handler.can_preview("test.mp4", 1024) is True
        assert handler.can_preview("test.txt", 1024) is False

    def test_transfer_manager_standalone(self):
        from src.core.transfer_manager import (
            TransferManager,
            TransferDirection,
        )

        manager = TransferManager(max_workers=2)
        manager.add_upload_task(
            device_id="test_device",
            local_path="/tmp/test.txt",
            remote_path="/data/test.txt",
        )
        manager.add_download_task(
            device_id="test_device",
            remote_path="/data/test.txt",
            local_path="/tmp/downloaded.txt",
        )
        assert len(manager.tasks) == 2
        assert manager.tasks[0].direction == TransferDirection.UPLOAD
        assert manager.tasks[1].direction == TransferDirection.DOWNLOAD

        manager.cancel_all()
        manager.clear_completed_tasks()


class TestGuiIntegration:
    """Tests for GUI component integration."""

    def test_main_window_contains_file_browser(self, qapp):
        from PySide6.QtWidgets import QApplication
        from src.gui.main_window import MainWindow

        window = MainWindow()
        # Process events to allow deferred UI initialization
        QApplication.processEvents()
        import time

        time.sleep(0.1)
        QApplication.processEvents()
        assert window.file_browser is not None

    def test_file_browser_contains_sub_widgets(self, qapp):
        from src.gui.widgets.file_browser import FileBrowserWidget

        browser = FileBrowserWidget()
        assert browser.file_tree is not None
        assert browser.file_list is not None
        assert browser.path_bar is not None

    def test_file_browser_transfer_manager_init(self, qapp):
        from src.gui.widgets.file_browser import FileBrowserWidget

        browser = FileBrowserWidget()
        assert browser.transfer_manager is None

    def test_file_browser_preview_handler_init(self, qapp):
        from src.gui.widgets.file_browser import FileBrowserWidget

        browser = FileBrowserWidget()
        assert browser.preview_handler is None
        assert browser.preview_window is None

    def test_transfer_dialog_integration(self, qapp):
        from src.gui.widgets.transfer_dialog import TransferDialog
        from src.core.transfer_manager import TransferTask, TransferDirection

        dialog = TransferDialog()
        task = TransferTask(
            local_path="/tmp/test.txt",
            remote_path="/data/test.txt",
            direction=TransferDirection.UPLOAD,
            device_id="test",
            total_size=2048,
        )
        dialog.add_task(task)
        dialog.update_progress("/tmp/test.txt", 75, 2048, 1024.0)
        dialog.mark_completed("/tmp/test.txt", True, "")
        dialog.clear_tasks()

    def test_preview_window_integration(self, qapp):
        from src.gui.widgets.preview_window import PreviewWindow

        window = PreviewWindow()
        assert window.preview_handler is None
        window._zoom_in()
        window._zoom_out()
        window._reset_zoom()
        window.close()


class TestUtilityIntegration:
    """Tests for utility module integration."""

    def test_language_manager_with_real_translations(self):
        from src.utils.language_manager import LanguageManager

        lm = LanguageManager()
        en_text = lm.tr("toolbar.refresh")
        assert isinstance(en_text, str)
        assert len(en_text) > 0

    def test_icon_manager_theme_switching(self, qapp):
        from src.utils.icon_manager import IconManager

        im = IconManager()
        im.set_theme("light")
        assert im.current_theme == "light"
        im.set_theme("dark")
        assert im.current_theme == "dark"

    def test_config_singleton(self):
        from src.config import config

        assert config.app_name == "OpenHarmony File Browser"
        assert config.window_width == 1200

    def test_logger_singleton(self):
        from src.utils.logger import get_logger

        logger = get_logger("test_integration")
        assert logger is not None
        logger.info("Integration test log")


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_import_chain(self):
        """Test that all major modules can be imported without error."""
        from src.models.device import DeviceStatus
        from src.models.file_info import FileType
        from src.config import config
        from src.utils.file_utils import get_file_type, format_file_size
        from src.utils.platform_utils import get_platform, get_architecture

        assert DeviceStatus.CONNECTED.value == "connected"
        assert FileType.FILE.value == "file"
        assert config.app_name == "OpenHarmony File Browser"
        assert get_file_type("test.jpg", False) == "image"
        assert format_file_size(1024) == "1.00 KB"
        assert get_platform() in ["Windows", "Linux", "Darwin"]
        assert get_architecture() in ["x64", "arm64"]

    def test_gui_import_chain(self, qapp):
        """Test that all GUI modules can be imported and instantiated."""
        from src.gui.main_window import MainWindow

        window = MainWindow()
        window.close()
