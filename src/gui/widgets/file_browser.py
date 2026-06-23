"""
File browser widget with batch download support.
"""

from typing import Optional, List
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSplitter,
    QToolBar,
    QFileDialog,
    QDialog,
    QStyle,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QKeySequence

from src.core.hdc_wrapper import HDCWrapper
from src.core.file_operations import FileOperations
from src.core.transfer_manager import TransferManager, TransferDirection
from src.core.preview_handler import PreviewHandler
from src.gui.widgets.file_tree import FileTreeWidget
from src.gui.widgets.file_list import FileListWidget
from src.gui.widgets.path_bar import PathBarWidget
from src.gui.widgets.dialogs import (
    RenameDialog,
    CreateFolderDialog,
    show_error_dialog,
    show_success_dialog,
)
from src.gui.widgets.transfer_dialog import TransferDialog
from src.gui.widgets.preview_window import PreviewWindow
from src.utils.logger import get_logger
from src.utils.icon_manager import icon_manager
from src.utils.language_manager import language_manager
from src.config import config

logger = get_logger(__name__)


class FileBrowserWidget(QWidget):
    """File browser with batch operations."""

    file_operation_completed = Signal()
    status_message = Signal(str)

    def __init__(self):
        super().__init__()

        self.hdc: Optional[HDCWrapper] = None
        self.device_id: Optional[str] = None
        self.file_ops: Optional[FileOperations] = None
        self.current_path: str = "/"

        self.transfer_manager: Optional[TransferManager] = None
        self.transfer_dialog: Optional[TransferDialog] = None

        self.preview_handler: Optional[PreviewHandler] = None
        self.preview_window: Optional[PreviewWindow] = None

        self._show_hidden: bool = False
        self._pending_path: Optional[str] = None

        self._init_ui()

        self.setAcceptDrops(True)

        logger.info("File browser widget initialized")

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.path_bar = PathBarWidget()
        self.path_bar.path_changed.connect(self._on_path_changed)
        self.path_bar.show_hidden_changed.connect(self._on_show_hidden_changed)
        self.path_bar.select_all_changed.connect(self._toggle_select_all)
        layout.addWidget(self.path_bar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setContentsMargins(0, 0, 0, 0)
        splitter.setHandleWidth(3)

        self.file_tree = FileTreeWidget()
        self.file_list = FileListWidget()

        splitter.addWidget(self.file_tree)
        splitter.addWidget(self.file_list)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([200, 600])

        layout.addWidget(splitter)

        self.file_tree.directory_selected.connect(self._on_directory_selected)
        self.file_list.directory_entered.connect(self._on_directory_entered)
        self.file_list.file_double_clicked.connect(self._on_file_double_clicked)
        self.file_list.status_message.connect(self._on_file_list_status_message)
        self.file_list.selection_changed.connect(self._sync_select_all_checkbox)

    def setup_toolbar(self, toolbar: QToolBar):
        """Setup file operation toolbar in main window."""
        refresh_action = QAction(
            icon_manager.get_icon("refresh"),
            language_manager.tr("toolbar.refresh"),
            self,
        )
        refresh_action.setToolTip(language_manager.tr("toolbar.refresh_tooltip"))
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self._refresh)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        new_folder_action = QAction(
            icon_manager.get_icon("new_folder"),
            language_manager.tr("toolbar.new_folder"),
            self,
        )
        new_folder_action.setToolTip(language_manager.tr("toolbar.new_folder_tooltip"))
        new_folder_action.triggered.connect(self._create_folder)
        toolbar.addAction(new_folder_action)

        rename_action = QAction(
            icon_manager.get_icon("rename"), language_manager.tr("toolbar.rename"), self
        )
        rename_action.setToolTip(language_manager.tr("toolbar.rename_tooltip"))
        rename_action.triggered.connect(self._rename)
        toolbar.addAction(rename_action)

        delete_action = QAction(
            icon_manager.get_icon("delete"), language_manager.tr("toolbar.delete"), self
        )
        delete_action.setToolTip(language_manager.tr("toolbar.delete_tooltip"))
        delete_action.triggered.connect(self._delete)
        toolbar.addAction(delete_action)

        toolbar.addSeparator()

        upload_action = QAction(
            icon_manager.get_icon("upload"), language_manager.tr("toolbar.upload"), self
        )
        upload_action.setToolTip(language_manager.tr("toolbar.upload_tooltip"))
        upload_action.triggered.connect(self._upload_file)
        toolbar.addAction(upload_action)

        download_action = QAction(
            icon_manager.get_icon("download"),
            language_manager.tr("toolbar.download"),
            self,
        )
        download_action.setToolTip(language_manager.tr("toolbar.download_tooltip"))
        download_action.triggered.connect(self._download_files)
        toolbar.addAction(download_action)

    def update_language(self):
        """Update all UI texts when language changes."""
        if hasattr(self.file_tree, "update_language"):
            self.file_tree.update_language()
        if hasattr(self.file_list, "update_language"):
            self.file_list.update_language()
        if hasattr(self.path_bar, "update_language"):
            self.path_bar.update_language()
        if hasattr(self.transfer_dialog, "update_language"):
            self.transfer_dialog.update_language()
        if hasattr(self.preview_window, "update_language"):
            self.preview_window.update_language()

    def _toggle_select_all(self, state):
        """Toggle select all checkboxes in file list."""
        check_state = state != Qt.CheckState.Unchecked.value
        logger.info(
            f"_toggle_select_all called: state={state}, check_state={check_state}"
        )

        self.file_list._bulk_operation = True
        self.file_list.table.blockSignals(True)

        total = self.file_list.table.rowCount()
        for row in range(total):
            checkbox = self.file_list.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(check_state)

        logger.info(f"_toggle_select_all: set {total} checkboxes to {check_state}")

        if check_state:
            self.file_list.table.selectAll()
        else:
            self.file_list.table.clearSelection()

        self.file_list.table.blockSignals(False)
        self.file_list._bulk_operation = False

        self.file_list.selection_changed.emit()
        logger.info(f"_toggle_select_all completed, selection_changed emitted")

    def _sync_select_all_checkbox(self):
        """Sync select all checkbox with current file selection state."""
        selected = 0
        total = self.file_list.table.rowCount()
        for row in range(total):
            checkbox = self.file_list.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected += 1
        logger.info(f"_sync_select_all_checkbox: selected={selected}, total={total}")
        self.path_bar.update_select_all_state(selected, total)

    def _on_file_list_status_message(self, message: str):
        """Forward file list status message to main window."""
        self.status_message.emit(message)

    def _on_show_hidden_changed(self, show: bool):
        """Handle show hidden files checkbox change."""
        self._show_hidden = show
        if self.file_ops:
            self.file_ops.cache.invalidate(self.current_path)
        self.file_list.load_directory(self.current_path, show_hidden=show)

        logger.debug(f"Show hidden files: {show}")

    def set_device(self, device_id: str, hdc: HDCWrapper):
        """Set device."""
        self.device_id = device_id
        self.hdc = hdc
        self.file_ops = FileOperations(hdc, device_id)

        # Delayed initialization of transfer_manager and preview_handler (improve startup speed)
        self.transfer_manager = None
        self.preview_handler = None

        self.file_tree.set_device(device_id, hdc)
        self.file_list.set_device(device_id, hdc)

        self._load_root_directory()

        logger.info(f"Device set for file browser: {device_id}")

    def clear_device(self):
        """Clear current device."""
        self.device_id = None
        self.hdc = None
        self.file_ops = None

        if self.transfer_manager:
            try:
                self.transfer_manager.transfer_progress.disconnect(
                    self._on_transfer_progress
                )
                self.transfer_manager.transfer_completed.disconnect(
                    self._on_transfer_completed
                )
                self.transfer_manager.all_transfers_completed.disconnect(
                    self._on_all_transfers_completed
                )
            except (TypeError, RuntimeError):
                pass
            self.transfer_manager.cleanup()
        self.transfer_manager = None

        if self.preview_handler:
            self.preview_handler.cleanup()
        self.preview_handler = None

        self.file_tree.clear_device()
        self.file_list.clear_device()

        self.current_path = "/"
        self._pending_path = None

        logger.info("Device cleared from file browser")

    def _load_root_directory(self):
        """Load root directory."""
        self.current_path = "/"
        self.path_bar.set_path("/")

        # file_tree.set_device() already called in set_device(), don't call again
        self.file_list.load_directory("/", show_hidden=self._show_hidden)

    def _on_directory_selected(self, path: str):
        """Handle directory selection from tree."""
        if self._pending_path:
            if path != self._pending_path:
                return
            self._pending_path = None

        if self.current_path == path:
            return
        self.current_path = path
        self.path_bar.set_path(path)
        self.file_list.load_directory(path, show_hidden=self._show_hidden)

        # 发射状态更新信号
        self.status_message.emit(language_manager.tr("status.current_path", path=path))

        logger.debug(f"Directory selected from tree: {path}")

    def _on_directory_entered(self, path: str):
        """Handle directory entry from file list."""
        if self.current_path == path:
            return

        self.current_path = path
        self._pending_path = path

        self.file_tree.expand_to_path(path)

        self.path_bar.blockSignals(True)
        self.path_bar.set_path(path)
        self.path_bar.blockSignals(False)

        self.file_list.load_directory(path, show_hidden=self._show_hidden)

        # 发射状态更新信号
        self.status_message.emit(language_manager.tr("status.current_path", path=path))

        logger.info(f"Directory entered: {path}")

    def _on_path_changed(self, path: str):
        """Handle path change from navigation bar."""
        if not self.file_ops:
            return

        try:
            normalized = self.file_ops.normalize_path(path)

            if self.current_path == normalized:
                return

            self.current_path = normalized
            self._pending_path = normalized

            self.path_bar.blockSignals(True)
            self.path_bar.set_path(normalized)
            self.path_bar.blockSignals(False)

            self.file_tree.expand_to_path(normalized)
            self.file_list.load_directory(normalized, show_hidden=self._show_hidden)

            # 发射状态更新信号
            self.status_message.emit(
                language_manager.tr("status.current_path", path=normalized)
            )

            logger.info(f"Path changed: {normalized}")

        except Exception as e:
            show_error_dialog(
                language_manager.tr("dialogs.invalid_path"),
                language_manager.tr("dialogs.invalid_path_msg", path=path),
                self,
            )
            logger.error(f"Invalid path: {path} - {e}")

    def _on_file_double_clicked(self, path: str):
        """Handle file double-click (preview)."""
        if not self.preview_handler and self.hdc and self.device_id:
            self.preview_handler = PreviewHandler(self.hdc, self.device_id)

        if not self.preview_handler:
            logger.warning("Preview handler not available")
            return

        selected_file = self.file_list.get_selected_file()

        if not selected_file:
            return

        if not self.preview_handler.can_preview(selected_file.name, selected_file.size):
            show_error_dialog(
                language_manager.tr("dialogs.cannot_preview"),
                language_manager.tr(
                    "dialogs.cannot_preview_msg", name=selected_file.name
                ),
                self,
            )
            return

        logger.info(f"Previewing file: {selected_file.name}")

        if not self.preview_window:
            self.preview_window = PreviewWindow(self)
        self.preview_window.set_preview_handler(self.preview_handler)

        self.preview_window.preview_file(
            selected_file.path, selected_file.name, selected_file.size
        )

        self.preview_window.show()

    def _refresh(self):
        """Refresh current directory (invalidate cache first)."""
        if self.file_ops:
            self.file_ops.cache.invalidate(self.current_path)

        self.file_list.refresh(show_hidden=self._show_hidden)

        # 发射状态更新信号
        self.status_message.emit(
            language_manager.tr("status.refreshed", path=self.current_path)
        )
        self.file_tree.refresh_directory(self.current_path)

        logger.info(f"Refreshed: {self.current_path}")

    def _create_folder(self):
        """Create new folder."""
        if not self.file_ops:
            show_error_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("dialogs.no_device"),
                self,
            )
            return

        dialog = CreateFolderDialog(self)

        if dialog.exec() == QDialog.Accepted:
            folder_name = dialog.get_folder_name()

            if not folder_name:
                show_error_dialog(
                    language_manager.tr("dialogs.error_title"),
                    language_manager.tr("dialogs.folder_name_empty"),
                    self,
                )
                return

            try:
                new_path = self.file_ops.join_path(self.current_path, folder_name)

                self.file_ops.create_directory(new_path)

                self._refresh()

                show_success_dialog(
                    language_manager.tr("dialogs.success_title"),
                    language_manager.tr("dialogs.folder_created", name=folder_name),
                    self,
                )

                self.file_operation_completed.emit()

                logger.info(f"Folder created: {new_path}")

            except Exception as e:
                show_error_dialog(
                    language_manager.tr("dialogs.error_title"),
                    language_manager.tr("dialogs.create_folder_failed", error=str(e)),
                    self,
                )
                logger.error(f"Failed to create folder: {e}")

    def _rename(self):
        """Rename selected file/folder."""
        if not self.file_ops:
            show_error_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("dialogs.no_device"),
                self,
            )
            return

        selected_file = self.file_list.get_selected_file()

        if not selected_file:
            show_error_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("dialogs.no_files_selected"),
                self,
            )
            return

        dialog = RenameDialog(selected_file.name, self)

        if dialog.exec() == QDialog.Accepted:
            new_name = dialog.get_new_name()

            if not new_name:
                show_error_dialog(
                    language_manager.tr("dialogs.error_title"),
                    language_manager.tr("dialogs.name_empty"),
                    self,
                )
                return

            try:
                parent_path = self.file_ops.get_parent_directory(selected_file.path)
                new_path = self.file_ops.join_path(parent_path, new_name)

                self.file_ops.rename_file(selected_file.path, new_path)

                self._refresh()

                show_success_dialog(
                    language_manager.tr("dialogs.success_title"),
                    language_manager.tr("dialogs.renamed_to", name=new_name),
                    self,
                )

                self.file_operation_completed.emit()

                logger.info(f"File renamed: {selected_file.path} -> {new_path}")

            except Exception as e:
                show_error_dialog(
                    language_manager.tr("dialogs.error_title"),
                    language_manager.tr("dialogs.rename_failed", error=str(e)),
                    self,
                )
                logger.error(f"Failed to rename: {e}")

    def _delete(self):
        """Delete selected items (batch)."""
        if not self.file_ops:
            show_error_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("dialogs.no_device"),
                self,
            )
            return

        selected_files = self.file_list.get_selected_files()

        if not selected_files:
            show_error_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("dialogs.no_files_selected"),
                self,
            )
            return

        # Show confirmation for batch delete
        count = len(selected_files)
        message = language_manager.tr("dialogs.delete_confirm", count=count) + "\n\n"

        if count <= 5:
            names = [f.name for f in selected_files]
            message += (
                language_manager.tr("dialogs.delete_items_list")
                + "\n"
                + "\n".join(names)
            )
        else:
            message += (
                language_manager.tr("dialogs.delete_items_list")
                + "\n"
                + "\n".join([f.name for f in selected_files[:5]])
                + "\n"
                + language_manager.tr("dialogs.delete_more_items", count=count - 5)
            )

        # Create message box with translated buttons
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle(language_manager.tr("dialogs.delete_title"))
        msg_box.setText(message)
        btn_yes = msg_box.addButton(
            language_manager.tr("buttons.yes"), QMessageBox.YesRole
        )
        btn_no = msg_box.addButton(
            language_manager.tr("buttons.no"), QMessageBox.NoRole
        )
        msg_box.setDefaultButton(btn_no)
        msg_box.exec()

        if msg_box.clickedButton() != btn_yes:
            return

        try:
            deleted_count = 0

            for file_info in selected_files:
                self.file_ops.delete_file(file_info.path, recursive=file_info.is_dir)
                deleted_count += 1

            self._refresh()

            show_success_dialog(
                language_manager.tr("dialogs.success_title"),
                language_manager.tr("dialogs.deleted_items", count=deleted_count),
                self,
            )

            self.file_operation_completed.emit()

            logger.info(f"Deleted {deleted_count} items")

        except Exception as e:
            show_error_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("dialogs.delete_failed", error=str(e)),
                self,
            )
            logger.error(f"Failed to delete: {e}")

    def _upload_file(self):
        """Upload files or folder to device."""
        transfer_manager = self._ensure_transfer_manager()

        if not transfer_manager or not self.file_ops:
            show_error_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("dialogs.no_device"),
                self,
            )
            return

        msg = QMessageBox(self)
        msg.setWindowTitle(language_manager.tr("dialogs.upload_title"))
        msg.setIconPixmap(self.style().standardIcon(QStyle.SP_ArrowUp).pixmap(64, 64))
        msg.setText("<h3>" + language_manager.tr("dialogs.upload_text") + "</h3>")
        msg.setInformativeText(
            "<p style='line-height: 1.6;'>"
            "📁 <b>" + language_manager.tr("dialogs.select_files") + "</b><br>"
            "📂 <b>" + language_manager.tr("dialogs.select_folder") + "</b><br>"
            "<br>"
            "💡 <i>" + language_manager.tr("dialogs.upload_tip") + "</i>"
            "</p>"
        )

        msg.setMinimumWidth(400)

        btn_files = msg.addButton(
            "📁 " + language_manager.tr("dialogs.select_files"), QMessageBox.ActionRole
        )
        btn_folder = msg.addButton(
            "📂 " + language_manager.tr("dialogs.select_folder"), QMessageBox.ActionRole
        )
        msg.addButton(language_manager.tr("buttons.cancel"), QMessageBox.RejectRole)

        msg.exec()

        clicked = msg.clickedButton()

        if clicked != btn_files and clicked != btn_folder:
            return

        upload_mode = "files" if clicked == btn_files else "folder"

        local_paths = []

        if upload_mode == "files":
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                language_manager.tr("dialogs.select_files_title"),
                "",
                language_manager.tr("dialogs.all_files"),
            )
            if file_paths:
                local_paths = file_paths

        elif upload_mode == "folder":
            folder_path = QFileDialog.getExistingDirectory(
                self,
                language_manager.tr("dialogs.select_folder_title"),
                "",
                QFileDialog.ShowDirsOnly,
            )
            if folder_path:
                local_paths = [folder_path]

        if not local_paths:
            return

        try:
            remote_paths = []
            for local_path in local_paths:
                file_name = Path(local_path).name
                remote_path = self.file_ops.join_path(self.current_path, file_name)
                remote_paths.append(remote_path)

            self._start_transfer(local_paths, remote_paths, TransferDirection.UPLOAD)

            item_count = len(local_paths)
            item_type = "folder" if upload_mode == "folder" else "files"
            logger.info(f"Upload started: {item_count} {item_type}")
        except Exception as e:
            show_error_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("dialogs.upload_failed", error=str(e)),
                self,
            )
            logger.error(f"Failed to start upload: {e}")

    def _download_files(self):
        """Download selected files and directories (batch)."""
        transfer_manager = self._ensure_transfer_manager()

        if not transfer_manager or not self.file_ops:
            show_error_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("dialogs.no_device"),
                self,
            )
            return

        selected_files = self.file_list.get_selected_files()

        if not selected_files:
            show_error_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("dialogs.no_files_selected"),
                self,
            )
            return

        # Select save directory for batch download
        save_dir = QFileDialog.getExistingDirectory(
            self,
            language_manager.tr("dialogs.select_save_dir"),
            "",
            QFileDialog.ShowDirsOnly,
        )

        if not save_dir:
            return

        try:
            local_paths = []
            remote_paths = []

            for file_info in selected_files:
                local_path = str(Path(save_dir) / file_info.name)
                local_paths.append(local_path)
                remote_paths.append(file_info.path)

            self._start_transfer(local_paths, remote_paths, TransferDirection.DOWNLOAD)

            logger.info(f"Download started: {len(selected_files)} items to {save_dir}")

        except Exception as e:
            show_error_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("dialogs.download_failed", error=str(e)),
                self,
            )
            logger.error(f"Failed to start download: {e}")

    def _ensure_transfer_manager(self):
        """Ensure transfer manager is initialized with signals connected (only once)."""
        if self.transfer_manager is None and self.hdc:
            self.transfer_manager = TransferManager(
                self.hdc, max_workers=config.transfer_max_workers
            )
            self.transfer_manager.transfer_progress.connect(self._on_transfer_progress)
            self.transfer_manager.transfer_completed.connect(
                self._on_transfer_completed
            )
            self.transfer_manager.all_transfers_completed.connect(
                self._on_all_transfers_completed
            )
        return self.transfer_manager

    def _start_transfer(
        self,
        local_paths: List[str],
        remote_paths: List[str],
        direction: TransferDirection,
    ):
        """Start batch transfer."""
        transfer_manager = self._ensure_transfer_manager()

        if not transfer_manager:
            return

        for local_path, remote_path in zip(local_paths, remote_paths):
            if direction == TransferDirection.UPLOAD:
                transfer_manager.add_upload_task(
                    self.device_id, local_path, remote_path
                )
            else:
                transfer_manager.add_download_task(
                    self.device_id, remote_path, local_path
                )

        if not self.transfer_dialog:
            self.transfer_dialog = TransferDialog(self)
            self.transfer_dialog.transfer_cancelled.connect(self._on_transfer_cancelled)

        self.transfer_dialog.clear_tasks()

        for task in self.transfer_manager.tasks:
            self.transfer_dialog.add_task(task)

        transfer_manager.start_transfers()

        self.transfer_dialog.show()

    def _on_transfer_progress(self, path: str, progress: int, size: int, speed: float):
        """Handle transfer progress."""
        if self.transfer_dialog:
            self.transfer_dialog.update_progress(path, progress, size, speed)

    def _on_transfer_completed(self, path: str, success: bool, error: str):
        """Handle single transfer completed."""
        if self.transfer_dialog:
            self.transfer_dialog.task_completed(path, success, error)

        logger.info(f"Transfer completed: {path} - success={success}")

    def _on_all_transfers_completed(self):
        """Handle all transfers completed."""
        if self.transfer_dialog:
            self.transfer_dialog.all_completed()

        self._refresh()

        logger.info("All transfers completed")

    def _on_transfer_cancelled(self):
        """Handle transfer cancelled."""
        if self.transfer_manager:
            self.transfer_manager.cancel_all()

        logger.info("Transfer cancelled")

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop."""
        transfer_manager = self._ensure_transfer_manager()

        if not transfer_manager or not self.file_ops:
            return

        urls = event.mimeData().urls()

        local_paths = []
        remote_paths = []

        for url in urls:
            local_path = url.toLocalFile()

            if Path(local_path).exists():
                file_name = Path(local_path).name
                remote_path = self.file_ops.join_path(self.current_path, file_name)

                local_paths.append(local_path)
                remote_paths.append(remote_path)

        if local_paths:
            self._start_transfer(local_paths, remote_paths, TransferDirection.UPLOAD)

            logger.info(f"Drag-drop upload: {len(local_paths)} files")

    def get_current_path(self) -> str:
        """Get current path."""
        return self.current_path
