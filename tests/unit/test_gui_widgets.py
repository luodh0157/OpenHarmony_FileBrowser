"""
Unit tests for GUI widgets (src/gui/widgets/).

These tests require PySide6 and a display (or xvfb).
Run with: pytest tests/unit/test_gui_widgets.py -v
"""

import pytest
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication instance for the test module."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestFileListWidget:
    """Tests for FileListWidget."""

    def test_create_widget(self, qapp):
        from src.gui.widgets.file_list import FileListWidget

        widget = FileListWidget()
        assert widget is not None

    def test_clear_device(self, qapp):
        from src.gui.widgets.file_list import FileListWidget

        widget = FileListWidget()
        widget.clear_device()
        assert widget.table.rowCount() == 0

    def test_select_all_shortcut(self, qapp):
        from src.gui.widgets.file_list import FileListWidget, CustomCheckBox

        widget = FileListWidget()
        widget.table.setRowCount(3)
        for row in range(3):
            cb = CustomCheckBox()
            cb.setChecked(False)
            widget.table.setCellWidget(row, 0, cb)

        widget._handle_select_all_shortcut()

        for row in range(3):
            cb = widget.table.cellWidget(row, 0)
            assert cb.isChecked()

    def test_deselect_all_shortcut(self, qapp):
        from src.gui.widgets.file_list import FileListWidget, CustomCheckBox

        widget = FileListWidget()
        widget.table.setRowCount(3)
        for row in range(3):
            cb = CustomCheckBox()
            cb.setChecked(True)
            widget.table.setCellWidget(row, 0, cb)

        widget._handle_deselect_all_shortcut()

        for row in range(3):
            cb = widget.table.cellWidget(row, 0)
            assert not cb.isChecked()

    def test_ctrl_a_event_filter(self, qapp):
        from src.gui.widgets.file_list import FileListWidget, CustomCheckBox

        widget = FileListWidget()
        widget.table.setRowCount(2)
        for row in range(2):
            cb = CustomCheckBox()
            cb.setChecked(False)
            widget.table.setCellWidget(row, 0, cb)

        event = QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.ControlModifier)
        result = widget.eventFilter(widget.table, event)

        assert result is True
        for row in range(2):
            cb = widget.table.cellWidget(row, 0)
            assert cb.isChecked()

    def test_ctrl_d_event_filter(self, qapp):
        from src.gui.widgets.file_list import FileListWidget, CustomCheckBox

        widget = FileListWidget()
        widget.table.setRowCount(2)
        for row in range(2):
            cb = CustomCheckBox()
            cb.setChecked(True)
            widget.table.setCellWidget(row, 0, cb)

        event = QKeyEvent(QEvent.KeyPress, Qt.Key_D, Qt.ControlModifier)
        result = widget.eventFilter(widget.table, event)

        assert result is True
        for row in range(2):
            cb = widget.table.cellWidget(row, 0)
            assert not cb.isChecked()

    def test_get_selected_files(self, qapp):
        from src.gui.widgets.file_list import FileListWidget, CustomCheckBox
        from src.models.file_info import FileInfo, FileType

        widget = FileListWidget()
        test_files = [
            FileInfo(
                name=f"file_{i}.txt",
                path=f"/test/file_{i}.txt",
                is_dir=False,
                size=100,
                file_type=FileType.FILE,
            )
            for i in range(3)
        ]
        widget.files = test_files
        widget.table.setRowCount(3)
        for row, fi in enumerate(test_files):
            cb = CustomCheckBox()
            cb.setChecked(True)
            cb.setProperty("path", fi.path)
            cb.setProperty("is_dir", fi.is_dir)
            widget.table.setCellWidget(row, 0, cb)

        selected = widget.get_selected_files()
        assert len(selected) == 3


class TestFileTreeWidget:
    """Tests for FileTreeWidget."""

    def test_create_widget(self, qapp):
        from src.gui.widgets.file_tree import FileTreeWidget

        widget = FileTreeWidget()
        assert widget is not None

    def test_clear_device(self, qapp):
        from src.gui.widgets.file_tree import FileTreeWidget

        widget = FileTreeWidget()
        widget.clear_device()
        assert widget.tree.topLevelItemCount() == 0


class TestPathBarWidget:
    """Tests for PathBarWidget."""

    def test_create_widget(self, qapp):
        from src.gui.widgets.path_bar import PathBarWidget

        widget = PathBarWidget()
        assert widget is not None

    def test_set_path(self, qapp):
        from src.gui.widgets.path_bar import PathBarWidget

        widget = PathBarWidget()
        widget.set_path("/data/local/tmp")
        assert widget.current_path == "/data/local/tmp"

    def test_set_path_root(self, qapp):
        from src.gui.widgets.path_bar import PathBarWidget

        widget = PathBarWidget()
        widget.set_path("/")
        assert widget.current_path == "/"


class TestDialogs:
    """Tests for dialog classes."""

    def test_rename_dialog_import(self, qapp):
        from src.gui.widgets.dialogs import RenameDialog

        assert RenameDialog is not None

    def test_create_folder_dialog_import(self, qapp):
        from src.gui.widgets.dialogs import CreateFolderDialog

        assert CreateFolderDialog is not None

    def test_delete_confirm_dialog_import(self, qapp):
        from src.gui.widgets.dialogs import DeleteConfirmDialog

        assert DeleteConfirmDialog is not None

    def test_show_error_dialog_import(self, qapp):
        from src.gui.widgets.dialogs import show_error_dialog

        assert show_error_dialog is not None

    def test_show_success_dialog_import(self, qapp):
        from src.gui.widgets.dialogs import show_success_dialog

        assert show_success_dialog is not None

    def test_show_warning_dialog_import(self, qapp):
        from src.gui.widgets.dialogs import show_warning_dialog

        assert show_warning_dialog is not None


class TestTransferDialog:
    """Tests for TransferDialog."""

    def test_create_dialog(self, qapp):
        from src.gui.widgets.transfer_dialog import TransferDialog

        dialog = TransferDialog()
        assert dialog is not None

    def test_add_task(self, qapp):
        from src.gui.widgets.transfer_dialog import TransferDialog
        from src.core.transfer_manager import TransferTask, TransferDirection

        dialog = TransferDialog()
        task = TransferTask(
            local_path="/tmp/test.txt",
            remote_path="/data/test.txt",
            direction=TransferDirection.UPLOAD,
            device_id="test",
        )
        dialog.add_task(task)
        assert dialog.table.rowCount() == 1

    def test_update_progress(self, qapp):
        from src.gui.widgets.transfer_dialog import TransferDialog
        from src.core.transfer_manager import TransferTask, TransferDirection

        dialog = TransferDialog()
        task = TransferTask(
            local_path="/tmp/test.txt",
            remote_path="/data/test.txt",
            direction=TransferDirection.UPLOAD,
            device_id="test",
        )
        dialog.add_task(task)
        dialog.update_progress("/tmp/test.txt", 50, 1024, 512.0)

    def test_mark_completed(self, qapp):
        from src.gui.widgets.transfer_dialog import TransferDialog
        from src.core.transfer_manager import TransferTask, TransferDirection

        dialog = TransferDialog()
        task = TransferTask(
            local_path="/tmp/test.txt",
            remote_path="/data/test.txt",
            direction=TransferDirection.UPLOAD,
            device_id="test",
        )
        dialog.add_task(task)
        dialog.mark_completed("/tmp/test.txt", True, "")

    def test_clear_tasks(self, qapp):
        from src.gui.widgets.transfer_dialog import TransferDialog
        from src.core.transfer_manager import TransferTask, TransferDirection

        dialog = TransferDialog()
        task = TransferTask(
            local_path="/tmp/test.txt",
            remote_path="/data/test.txt",
            direction=TransferDirection.UPLOAD,
            device_id="test",
        )
        dialog.add_task(task)
        dialog.clear_tasks()
        assert dialog.table.rowCount() == 0


class TestPreviewWindow:
    """Tests for PreviewWindow."""

    def test_create_window(self, qapp):
        from src.gui.widgets.preview_window import PreviewWindow

        window = PreviewWindow()
        assert window is not None

    def test_ui_components_exist(self, qapp):
        from src.gui.widgets.preview_window import PreviewWindow

        window = PreviewWindow()
        assert window.image_label is not None
        assert window.video_placeholder is not None

    def test_zoom_methods_callable(self, qapp):
        from src.gui.widgets.preview_window import PreviewWindow

        window = PreviewWindow()
        window._zoom_in()
        window._zoom_out()
        window._reset_zoom()
        window._fit_to_window()

    def test_close_window(self, qapp):
        from src.gui.widgets.preview_window import PreviewWindow

        window = PreviewWindow()
        window.close()


class TestMainWindow:
    """Tests for MainWindow."""

    def test_create_window(self, qapp):
        from src.gui.main_window import MainWindow

        window = MainWindow()
        assert window is not None

    def test_window_title(self, qapp):
        from src.gui.main_window import MainWindow

        window = MainWindow()
        assert "OpenHarmony" in window.windowTitle()

    def test_close_window(self, qapp):
        from src.gui.main_window import MainWindow

        window = MainWindow()
        window.close()


class TestFileBrowserWidget:
    """Tests for FileBrowserWidget."""

    def test_create_widget(self, qapp):
        from src.gui.widgets.file_browser import FileBrowserWidget

        widget = FileBrowserWidget()
        assert widget is not None

    def test_clear_device(self, qapp):
        from src.gui.widgets.file_browser import FileBrowserWidget

        widget = FileBrowserWidget()
        widget.clear_device()

    def test_drag_drop_enabled(self, qapp):
        from src.gui.widgets.file_browser import FileBrowserWidget

        widget = FileBrowserWidget()
        assert widget.acceptDrops() is True
