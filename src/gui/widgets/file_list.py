"""
File list widget with proper multi-selection synchronization.
"""

from typing import Optional, List
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout,
    QHeaderView, QAbstractItemView, QLabel, QCheckBox, QStyle, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor

from src.core.file_operations import FileOperations
from src.core.hdc_wrapper import HDCWrapper
from src.models.file_info import FileInfo
from src.utils.file_utils import get_file_type
from src.utils.logger import get_logger
from src.utils.async_loader import DirectoryLoadThread
from src.utils.icon_manager import icon_manager
from src.utils.language_manager import language_manager


logger = get_logger(__name__)


class CustomCheckBox(QCheckBox):
    """Custom checkbox that distinguishes single-click from double-click."""
    
    double_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        
        self._click_count = 0
        self._click_timer = QTimer()
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._on_single_click_timeout)
    
    def mousePressEvent(self, event):
        """Handle mouse press - start click counting."""
        if event.button() == Qt.LeftButton:
            self._click_count += 1
            
            if self._click_count == 1:
                # Start timer to distinguish single vs double click
                self._click_timer.start(200)  # 200ms threshold
            elif self._click_count == 2:
                # Double click detected
                self._click_timer.stop()
                self._click_count = 0
                self.double_clicked.emit()
                # Don't toggle checkbox on double click
                return
        
        super().mousePressEvent(event)
    
    def _on_single_click_timeout(self):
        """Handle single click timeout - allow normal toggle."""
        if self._click_count == 1:
            pass
        
        self._click_count = 0


class FileListWidget(QWidget):
    """File list with synchronized checkbox + Ctrl+click multi-selection."""
    
    file_selected = Signal(str)
    file_double_clicked = Signal(str)
    directory_entered = Signal(str)
    selection_changed = Signal()
    status_message = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        self.file_ops: Optional[FileOperations] = None
        self.hdc: Optional[HDCWrapper] = None
        self.device_id: Optional[str] = None
        self.current_path: str = "/"
        self.files: List[FileInfo] = []
        
        self.load_thread: Optional[DirectoryLoadThread] = None
        
        self._init_ui()
        
        logger.info("File list widget initialized")
    
    def _init_ui(self):
        """Initialize UI with synchronized selection."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.content_container = QWidget()
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self._update_table_headers()
        
        self.table.setStyleSheet("""
            QTableCornerButton::section {
                background-color: transparent;
            }
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.setSectionsClickable(True)
        header.setSectionsMovable(False)
        header.resizeSection(0, 17)
        header.resizeSection(1, 250)
        header.resizeSection(2, 80)
        header.resizeSection(3, 150)
        header.resizeSection(4, 80)
        header.setMinimumSectionSize(50)
        
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        
        self.setFocusPolicy(Qt.StrongFocus)
        self.table.setFocusPolicy(Qt.StrongFocus)
        
        self.table.installEventFilter(self)
        
        self.table.itemClicked.connect(self._on_item_clicked)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        content_layout.addWidget(self.table, stretch=1)
        
        self.loading_label = QLabel(language_manager.tr('file_list.loading'))
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setProperty("loading", "true")  # Set dynamic property for QSS styling
        self.loading_label.hide()
        
        self.empty_label = QLabel(language_manager.tr('file_list.empty_text'))
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: gray; font-size: 12px; padding: 20px;")
        self.empty_label.hide()
        content_layout.addWidget(self.empty_label, stretch=1)
        
        layout.addWidget(self.content_container, stretch=1)
        
        self.loading_label.setParent(self.content_container)
    
    def update_language(self):
        """Update all UI texts when language changes."""
        self._update_table_headers()
        self.loading_label.setText(language_manager.tr('file_list.loading'))
        self.empty_label.setText(language_manager.tr('file_list.empty_text'))
        # Re-display files to update type column
        if self.files:
            self._display_files()
    
    def _update_table_headers(self):
        """Update table header labels for current language."""
        self.table.setHorizontalHeaderLabels([
            "",
            language_manager.tr('file_list.name'),
            language_manager.tr('file_list.size'),
            language_manager.tr('file_list.modified'),
            language_manager.tr('file_list.type')
        ])
    
    def _translate_file_type(self, file_type: str) -> str:
        """Translate file type string."""
        type_map = {
            'folder': language_manager.tr('file_types.folder'),
            'file': language_manager.tr('file_types.file'),
            'image': language_manager.tr('file_types.image'),
            'video': language_manager.tr('file_types.video'),
            'music': language_manager.tr('file_types.music'),
            'audio': language_manager.tr('file_types.music'),
            'document': language_manager.tr('file_types.document'),
            'archive': language_manager.tr('file_types.archive'),
            'code': language_manager.tr('file_types.code'),
            'unknown': language_manager.tr('file_types.unknown'),
        }
        return type_map.get(file_type, file_type)
    
    def eventFilter(self, watched, event):
        """Event filter to intercept keyboard events from table widget."""
        from PySide6.QtCore import QEvent
        
        if watched == self.table:
            if event.type() == QEvent.KeyPress:
                logger.debug(f"Key pressed in table: key={event.key()}, modifiers={event.modifiers()}")
                
                if event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
                    logger.info("Ctrl+A detected via event filter")
                    self._handle_select_all_shortcut()
                    event.accept()
                    return True
                
                if event.key() == Qt.Key_D and event.modifiers() == Qt.ControlModifier:
                    logger.info("Ctrl+D detected via event filter")
                    self._handle_deselect_all_shortcut()
                    event.accept()
                    return True
        
        return super().eventFilter(watched, event)
    
    def _handle_select_all_shortcut(self):
        """Handle Ctrl+A shortcut - select all rows and sync checkboxes."""
        self.table.blockSignals(True)
        self.table.selectAll()
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
        self.table.blockSignals(False)
        self.selection_changed.emit()
        logger.info(f"Ctrl+A: selected all {self.table.rowCount()} items")
    
    def _handle_deselect_all_shortcut(self):
        """Handle Ctrl+D shortcut - deselect all rows and sync checkboxes."""
        self.table.blockSignals(True)
        self.table.clearSelection()
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
        self.table.blockSignals(False)
        self.selection_changed.emit()
        logger.info(f"Ctrl+D: deselected all {self.table.rowCount()} items")
    
    def set_device(self, device_id: str, hdc: HDCWrapper):
        """Set device."""
        self.device_id = device_id
        self.hdc = hdc
        self.file_ops = FileOperations(hdc, device_id)
        logger.info(f"Device set for file list: {device_id}")
    
    def clear_device(self):
        """Clear current device."""
        if self.load_thread:
            try:
                if self.load_thread.isRunning():
                    self.load_thread.cancel()
                    self.load_thread.wait(2000)
                    if self.load_thread.isRunning():
                        logger.warning("Load thread did not finish in 2 seconds, forcing termination")
                        self.load_thread.terminate()
                        self.load_thread.wait()
            except RuntimeError as e:
                logger.debug(f"Thread object already deleted: {e}")
            self.load_thread = None
        
        self.device_id = None
        self.hdc = None
        self.file_ops = None
        self.current_path = "/"
        self.files = []
        
        self.table.setRowCount(0)
        self._hide_loading()
        logger.info("Device cleared from file list")
    
    def load_directory(self, path: str):
        """Load and display files asynchronously."""
        if not self.file_ops:
            return
        
        if self.load_thread:
            try:
                if self.load_thread.isRunning():
                    logger.info(f"Cancelling previous load for: {self.current_path}")
                    self.load_thread.cancel()
                    if not self.load_thread.wait(500):
                        logger.warning("Previous load thread did not finish in 2 seconds, forcing termination")
                        self.load_thread.terminate()
                        self.load_thread.wait()
            except RuntimeError as e:
                logger.debug(f"Previous thread object already deleted: {e}")
            self.load_thread = None
        
        self.current_path = path
        self._show_loading()
        logger.info(f"Loading directory asynchronously: {path}")
        
        self.load_thread = DirectoryLoadThread(self.file_ops, path)
        self.load_thread.loaded.connect(self._on_directory_loaded)
        self.load_thread.error.connect(self._on_load_error)
        self.load_thread.start()
    
    def resizeEvent(self, event):
        """Handle resize to update loading label geometry."""
        super().resizeEvent(event)
        self._update_loading_geometry()
    
    def _update_loading_geometry(self):
        """Update loading label geometry to fill container."""
        if self.loading_label.isVisible() and self.content_container:
            parent_size = self.content_container.size()
            if parent_size.width() > 0 and parent_size.height() > 0:
                self.loading_label.setGeometry(0, 0, parent_size.width(), parent_size.height())
    
    def _show_loading(self):
        """Show loading indicator."""
        if self.content_container:
            parent_size = self.content_container.size()
            if parent_size.width() > 0 and parent_size.height() > 0:
                self.loading_label.setGeometry(0, 0, parent_size.width(), parent_size.height())
        
        self.loading_label.ensurePolished()
        
        self.table.hide()
        self.empty_label.hide()
        self.loading_label.show()
        self.loading_label.raise_()
    
    def _hide_loading(self):
        """Hide loading indicator and restore table."""
        self.loading_label.hide()
        
        if len(self.files) == 0:
            self.table.hide()
            self.empty_label.setText(language_manager.tr('file_list.empty_text'))
            self.empty_label.show()
        else:
            self.empty_label.hide()
            self.table.show()
    
    def _on_directory_loaded(self, files: List[FileInfo]):
        """Handle directory loaded event (async callback)."""
        self.files = files
        self._display_files()
        self._hide_loading()
        self.status_message.emit(f"{self.current_path} - {len(files)} items")
        logger.info(f"Directory loaded and displayed: {len(files)} files")
    
    def _on_load_error(self, error_msg: str):
        """Handle directory load error (async callback)."""
        self.files = []
        self._hide_loading()
        self.empty_label.setText(language_manager.tr('file_list.error', message=error_msg))
        self.empty_label.show()
        self.table.hide()
        logger.error(f"Directory load error: {error_msg}")
    
    def _display_files(self):
        """Display files in table."""
        if len(self.files) == 0:
            self.table.hide()
            self.empty_label.setText(language_manager.tr('file_list.empty_text'))
            self.empty_label.show()
            return
        
        self.empty_label.hide()
        self.table.show()
        self.table.setRowCount(len(self.files))
        
        for row, file_info in enumerate(self.files):
            # Checkbox column (column 0)
            checkbox_widget = CustomCheckBox()
            checkbox_widget.setChecked(False)
            checkbox_widget.setProperty("row", row)
            checkbox_widget.setProperty("path", file_info.path)
            checkbox_widget.setProperty("is_dir", file_info.is_dir)
            checkbox_widget.stateChanged.connect(self._on_checkbox_changed)
            checkbox_widget.double_clicked.connect(self._on_checkbox_double_clicked)
            self.table.setCellWidget(row, 0, checkbox_widget)
            
            # Name column (column 1)
            name_item = QTableWidgetItem(file_info.name)
            if file_info.is_dir:
                name_item.setForeground(QColor("#1976d2"))
                name_item.setIcon(icon_manager.get_icon('folder'))
            else:
                name_item.setIcon(icon_manager.get_file_type_icon(file_info.name, False))
            self.table.setItem(row, 1, name_item)
            
            # Size column (column 2)
            if file_info.is_dir:
                size_item = QTableWidgetItem(language_manager.tr('file_list.dir_placeholder'))
                size_item.setForeground(QColor("#757575"))
            else:
                size_item = QTableWidgetItem(file_info.display_size)
            self.table.setItem(row, 2, size_item)
            
            # Modified column (column 3)
            time_item = QTableWidgetItem(file_info.display_time)
            self.table.setItem(row, 3, time_item)
            
            # Type column (column 4) - translated
            if file_info.is_dir:
                type_text = self._translate_file_type('folder')
            else:
                raw_type = get_file_type(file_info.name, False)
                type_text = self._translate_file_type(raw_type)
            type_item = QTableWidgetItem(type_text.capitalize())
            self.table.setItem(row, 4, type_item)
        
    def _on_checkbox_changed(self, state):
        """Handle checkbox state change (single-click only)."""
        checkbox = self.sender()
        if not checkbox:
            return
        
        row = checkbox.property("row")
        is_checked = state == 2
        
        self.table.blockSignals(True)
        if is_checked:
            self.table.selectRow(row)
        else:
            from PySide6.QtCore import QItemSelectionModel
            self.table.selectionModel().select(
                self.table.model().index(row, 0),
                QItemSelectionModel.Deselect | QItemSelectionModel.Rows
            )
        self.table.blockSignals(False)
        logger.debug(f"Checkbox toggled (single-click): row={row}, checked={is_checked}")
    
    def _on_checkbox_double_clicked(self):
        """Handle checkbox double-click - enter directory or open file."""
        checkbox = self.sender()
        if not checkbox:
            return
        
        path = checkbox.property("path")
        is_dir = checkbox.property("is_dir")
        
        if is_dir:
            self.directory_entered.emit(path)
            logger.info(f"Double-clicked checkbox to enter directory: {path}")
        else:
            self.file_double_clicked.emit(path)
            logger.debug(f"Double-clicked checkbox to open file: {path}")
    
    def _on_item_clicked(self, item: QTableWidgetItem):
        """Handle item click on non-checkbox columns."""
        row = item.row()
        col = item.column()
        
        if col == 0:
            return
        
        checkbox = self.table.cellWidget(row, 0)
        if not checkbox:
            return
        
        is_currently_selected = checkbox.isChecked()
        
        from PySide6.QtGui import QGuiApplication
        modifiers = QGuiApplication.keyboardModifiers()
        has_ctrl = modifiers & Qt.ControlModifier
        has_shift = modifiers & Qt.ShiftModifier
        
        self.table.blockSignals(True)
        
        if has_ctrl or has_shift:
            selected_rows = set()
            for sel_item in self.table.selectedItems():
                selected_rows.add(sel_item.row())
            for r in range(self.table.rowCount()):
                cb = self.table.cellWidget(r, 0)
                if cb:
                    cb.setChecked(r in selected_rows)
        else:
            if is_currently_selected:
                checkbox.setChecked(False)
                self.table.clearSelection()
            else:
                for r in range(self.table.rowCount()):
                    cb = self.table.cellWidget(r, 0)
                    if cb:
                        cb.setChecked(False)
                checkbox.setChecked(True)
                self.table.selectRow(row)
        
        self.table.blockSignals(False)
        self.selection_changed.emit()
        logger.debug(f"Item clicked: row={row}, col={col}, previously_selected={is_currently_selected}, ctrl={has_ctrl}, shift={has_shift}")
    
    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """Handle item double-click."""
        row = item.row()
        checkbox = self.table.cellWidget(row, 0)
        
        if not checkbox:
            return
        
        path = checkbox.property("path")
        is_dir = checkbox.property("is_dir")
        
        if is_dir:
            self.directory_entered.emit(path)
            logger.info(f"Entering directory: {path}")
        else:
            self.file_double_clicked.emit(path)
            logger.debug(f"File double-clicked: {path}")
    
    def get_selected_file(self) -> Optional[FileInfo]:
        """Get first selected file (backward compatibility)."""
        selected_files = self.get_selected_files()
        return selected_files[0] if selected_files else None
    
    def get_selected_files(self) -> List[FileInfo]:
        """Get all selected files (from checkboxes)."""
        selected_files = []
        
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                path = checkbox.property("path")
                for file_info in self.files:
                    if file_info.path == path:
                        selected_files.append(file_info)
                        break
        
        logger.info(f"Selected {len(selected_files)} files via checkboxes")
        return selected_files
    
    def refresh(self):
        """Refresh current directory."""
        self.load_directory(self.current_path)
        logger.info("File list refreshed")
