"""
Transfer dialog for OpenHarmony File Browser.
Displays transfer progress and status.
"""

from typing import Dict
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from src.core.transfer_manager import TransferTask, TransferStatus, TransferDirection
from src.utils.file_utils import format_file_size
from src.utils.logger import get_logger
from src.utils.language_manager import language_manager

logger = get_logger(__name__)


class TransferDialog(QDialog):
    """
    Transfer progress dialog.

    Features:
    - Transfer list table
    - Progress bars
    - Transfer speed display
    - Cancel button
    - Close when complete
    """

    transfer_cancelled = Signal()

    def __init__(self, parent=None):
        """
        Initialize transfer dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self.setWindowTitle(language_manager.tr("transfer.title"))
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.tasks: Dict[str, TransferTask] = {}
        self.completed_count = 0
        self.total_count = 0

        self._init_ui()

        logger.info("Transfer dialog initialized")

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(language_manager.tr("transfer.transferring"))
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.title_label)

        self.status_label = QLabel(
            language_manager.tr("transfer.status", completed=0, total=0)
        )
        header_layout.addWidget(self.status_label)

        header_layout.addStretch()

        layout.addWidget(header_widget)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            [
                language_manager.tr("transfer.file"),
                language_manager.tr("transfer.direction"),
                language_manager.tr("transfer.progress"),
                language_manager.tr("transfer.size"),
                language_manager.tr("transfer.speed_col"),
            ]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        layout.addWidget(self.table)

        summary_widget = QWidget()
        summary_layout = QHBoxLayout(summary_widget)
        summary_layout.setContentsMargins(0, 0, 0, 0)

        self.total_size_label = QLabel(
            language_manager.tr("transfer.total", size="0 bytes")
        )
        summary_layout.addWidget(self.total_size_label)

        summary_layout.addStretch()

        self.avg_speed_label = QLabel(
            language_manager.tr("transfer.speed", speed="0 B")
        )
        layout.addWidget(summary_widget)

        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)

        button_layout.addStretch()

        self.cancel_btn = QPushButton(language_manager.tr("transfer.cancel_all"))
        self.cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_btn)

        self.close_btn = QPushButton(language_manager.tr("transfer.close"))
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setEnabled(False)
        button_layout.addWidget(self.close_btn)

        layout.addWidget(button_widget)

    def update_language(self):
        """Update all UI texts when language changes."""
        self.setWindowTitle(language_manager.tr("transfer.title"))

        # Update table headers
        self.table.setHorizontalHeaderLabels(
            [
                language_manager.tr("transfer.file"),
                language_manager.tr("transfer.direction"),
                language_manager.tr("transfer.progress"),
                language_manager.tr("transfer.size"),
                language_manager.tr("transfer.speed_col"),
            ]
        )

        # Update buttons
        self.cancel_btn.setText(language_manager.tr("transfer.cancel_all"))
        self.close_btn.setText(language_manager.tr("transfer.close"))

        # Update status label
        self.status_label.setText(
            language_manager.tr(
                "transfer.status",
                completed=self.completed_count,
                total=self.total_count,
            )
        )

        # Update title based on completion state
        if self.completed_count >= self.total_count and self.total_count > 0:
            self.title_label.setText(language_manager.tr("transfer.completed_title"))
        else:
            self.title_label.setText(language_manager.tr("transfer.transferring"))

        # Update table row texts
        self._update_table_language()

    def _update_table_language(self):
        """Update direction and status texts in table rows."""
        for row in range(self.table.rowCount()):
            direction_item = self.table.item(row, 1)
            progress_item = self.table.item(row, 2)

            if direction_item:
                path = (
                    self.table.item(row, 0).data(Qt.UserRole)
                    if self.table.item(row, 0)
                    else None
                )
                if path and path in self.tasks:
                    task = self.tasks[path]
                    direction_text = (
                        language_manager.tr("transfer.upload")
                        if task.direction == TransferDirection.UPLOAD
                        else language_manager.tr("transfer.download")
                    )
                    direction_item.setText(direction_text)

            if progress_item:
                path = (
                    self.table.item(row, 0).data(Qt.UserRole)
                    if self.table.item(row, 0)
                    else None
                )
                if path and path in self.tasks:
                    task = self.tasks[path]
                    if task.status == TransferStatus.COMPLETED:
                        progress_item.setText(language_manager.tr("transfer.complete"))
                    elif task.status == TransferStatus.FAILED:
                        progress_item.setText(
                            language_manager.tr(
                                "transfer.failed", error=task.error or "Unknown error"
                            )
                        )
                    elif task.status == TransferStatus.RUNNING:
                        progress_item.setText(f"{task.progress}%")
                    else:
                        progress_item.setText(language_manager.tr("transfer.pending"))

    def add_task(self, task: TransferTask):
        """
        Add a transfer task to the dialog.

        Args:
            task: Transfer task
        """
        self.tasks[task.local_path] = task
        self.total_count = len(self.tasks)

        self._update_table()

        logger.debug(f"Task added to dialog: {task.local_path}")

    def update_progress(self, path: str, progress: int, size: int, speed: float):
        """
        Update progress for a task.

        Args:
            path: File path
            progress: Progress percentage
            size: Total size
            speed: Transfer speed
        """
        if path not in self.tasks:
            return

        self.tasks[path].progress = progress
        self.tasks[path].total_size = size
        self.tasks[path].speed = speed

        self._update_table_row(path)

        logger.debug(f"Progress updated: {path} - {progress}%")

    def task_completed(self, path: str, success: bool, error: str):
        """
        Mark a task as completed (alias for mark_completed).

        Args:
            path: File path
            success: Whether transfer succeeded
            error: Error message if failed
        """
        self.mark_completed(path, success, error)

    def mark_completed(self, path: str, success: bool, error: str):
        """
        Mark a task as completed.

        Args:
            path: File path
            success: Whether transfer succeeded
            error: Error message if failed
        """
        if path not in self.tasks:
            return

        task = self.tasks[path]

        if success:
            task.status = TransferStatus.COMPLETED
            task.progress = 100
        else:
            task.status = TransferStatus.FAILED
            task.error = error

        self.completed_count += 1

        self._update_table_row(path)
        self._update_summary()

        logger.info(f"Task completed: {path} - {'success' if success else 'failed'}")

        if self.completed_count >= self.total_count:
            self._all_completed()

    def all_completed(self):
        """Mark all transfers as completed (external call)."""
        self._all_completed()

    def _update_table(self):
        """Update entire table."""
        self.table.setRowCount(len(self.tasks))

        for row, (path, task) in enumerate(self.tasks.items()):
            self._set_table_row(row, task)

    def _update_table_row(self, path: str):
        """Update specific row in table."""
        for row in range(self.table.rowCount()):
            file_item = self.table.item(row, 0)

            if file_item and file_item.data(Qt.UserRole) == path:
                task = self.tasks[path]
                self._set_table_row(row, task)
                break

    def _set_table_row(self, row: int, task: TransferTask):
        """
        Set data for a table row.

        Args:
            row: Row index
            task: Transfer task
        """
        from pathlib import Path

        file_name = Path(task.local_path).name
        file_item = QTableWidgetItem(file_name)
        file_item.setData(Qt.UserRole, task.local_path)
        self.table.setItem(row, 0, file_item)

        direction_text = (
            language_manager.tr("transfer.upload")
            if task.direction == TransferDirection.UPLOAD
            else language_manager.tr("transfer.download")
        )
        direction_item = QTableWidgetItem(direction_text)
        self.table.setItem(row, 1, direction_item)

        progress_item = QTableWidgetItem()

        if task.status == TransferStatus.COMPLETED:
            progress_item.setText(language_manager.tr("transfer.complete"))
            progress_item.setForeground(QColor("#3FB950"))
        elif task.status == TransferStatus.FAILED:
            progress_item.setText(
                language_manager.tr(
                    "transfer.failed", error=task.error or "Unknown error"
                )
            )
            progress_item.setForeground(QColor("#F85149"))
        elif task.status == TransferStatus.RUNNING:
            progress_item.setText(f"{task.progress}%")
        else:
            progress_item.setText(language_manager.tr("transfer.pending"))

        self.table.setItem(row, 2, progress_item)

        size_text = (
            format_file_size(task.total_size)
            if task.total_size > 0
            else language_manager.tr("transfer.unknown_size")
        )
        size_item = QTableWidgetItem(size_text)
        self.table.setItem(row, 3, size_item)

        speed_text = (
            f"{format_file_size(int(task.speed))}/s" if task.speed > 0 else "0 B/s"
        )
        speed_item = QTableWidgetItem(speed_text)
        self.table.setItem(row, 4, speed_item)

    def _update_summary(self):
        """Update summary labels."""
        total_size = sum(t.total_size for t in self.tasks.values())
        self.total_size_label.setText(
            language_manager.tr("transfer.total", size=format_file_size(total_size))
        )

        if self.completed_count > 0:
            completed_tasks = [
                t
                for t in self.tasks.values()
                if t.status in (TransferStatus.COMPLETED, TransferStatus.FAILED)
            ]
            if completed_tasks:
                avg_speed = sum(t.speed for t in completed_tasks) / len(completed_tasks)
            else:
                avg_speed = 0
        else:
            avg_speed = 0

        self.avg_speed_label.setText(
            language_manager.tr(
                "transfer.speed", speed=format_file_size(int(avg_speed))
            )
        )

        self.status_label.setText(
            language_manager.tr(
                "transfer.status",
                completed=self.completed_count,
                total=self.total_count,
            )
        )

    def _all_completed(self):
        """Mark all transfers as completed."""
        self.title_label.setText(language_manager.tr("transfer.completed_title"))

        # Disable cancel button when all transfers completed
        self.cancel_btn.setEnabled(False)

        # Enable close button when all transfers completed
        self.close_btn.setEnabled(True)

        self._update_summary()

        logger.info("All transfers completed")

    def _on_cancel(self):
        """Handle cancel button."""
        self.transfer_cancelled.emit()

        logger.info("Transfer cancelled by user")

    def clear_tasks(self):
        """Clear all tasks."""
        self.tasks.clear()
        self.completed_count = 0
        self.total_count = 0

        self.table.setRowCount(0)

        logger.debug("Tasks cleared from dialog")

    def closeEvent(self, event):
        """Handle close event."""
        running = [t for t in self.tasks.values() if t.status == TransferStatus.RUNNING]

        if running:
            self.transfer_cancelled.emit()

        event.accept()
