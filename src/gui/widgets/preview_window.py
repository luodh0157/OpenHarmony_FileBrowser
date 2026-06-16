"""
Preview window for OpenHarmony File Browser.
Displays image and video previews.
"""

from typing import Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QMessageBox,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QImage, QFont

from src.core.preview_handler import PreviewHandler
from src.utils.logger import get_logger
from src.utils.language_manager import language_manager
from src.gui.widgets.dialogs import show_warning_dialog

logger = get_logger(__name__)


class PreviewWindow(QDialog):
    """
    Preview window for displaying files.

    Features:
    - Image preview with QPixmap
    - Video preview placeholder with play button
    - Zoom controls
    - Open in system player for videos
    """

    def __init__(self, parent=None):
        """
        Initialize preview window.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self.preview_handler: Optional[PreviewHandler] = None

        self.local_file_path: Optional[str] = None
        self.file_name: Optional[str] = None
        self.file_size: int = 0

        self.is_video: bool = False

        self.original_pixmap: Optional[QPixmap] = None
        self.current_scale: float = 1.0

        self._init_ui()

        logger.info("Preview window initialized")

    def _init_ui(self):
        """Initialize UI."""
        self.setWindowTitle(language_manager.tr("preview.title"))
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.file_label = QLabel(language_manager.tr("preview.no_file"))
        self.file_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(self.file_label)

        self.size_label = QLabel(language_manager.tr("preview.bytes", size=0))
        header_layout.addWidget(self.size_label)

        header_layout.addStretch()

        layout.addWidget(header_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignCenter)

        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        self.preview_layout.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.preview_layout.addWidget(self.image_label)

        self.video_placeholder = QWidget()
        video_layout = QVBoxLayout(self.video_placeholder)
        video_layout.setAlignment(Qt.AlignCenter)

        self.video_icon_label = QLabel("🎬")
        self.video_icon_label.setAlignment(Qt.AlignCenter)
        self.video_icon_label.setStyleSheet("font-size: 80px;")
        video_layout.addWidget(self.video_icon_label)

        self.video_info_label = QLabel(language_manager.tr("preview.video_file"))
        self.video_info_label.setAlignment(Qt.AlignCenter)
        self.video_info_label.setStyleSheet("font-size: 14px;")
        video_layout.addWidget(self.video_info_label)

        self.play_btn = QPushButton(language_manager.tr("preview.play_video"))
        self.play_btn.setToolTip(language_manager.tr("preview.play_tooltip"))
        self.play_btn.clicked.connect(self._play_video)
        video_layout.addWidget(self.play_btn)

        self.video_placeholder.hide()
        self.preview_layout.addWidget(self.video_placeholder)

        scroll_area.setWidget(self.preview_widget)

        layout.addWidget(scroll_area)

        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        zoom_in_btn = QPushButton(language_manager.tr("preview.zoom_in"))
        zoom_in_btn.clicked.connect(self._zoom_in)
        controls_layout.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton(language_manager.tr("preview.zoom_out"))
        zoom_out_btn.clicked.connect(self._zoom_out)
        controls_layout.addWidget(zoom_out_btn)

        reset_btn = QPushButton(language_manager.tr("preview.reset"))
        reset_btn.clicked.connect(self._reset_zoom)
        controls_layout.addWidget(reset_btn)

        controls_layout.addStretch()

        fit_btn = QPushButton(language_manager.tr("preview.fit_window"))
        fit_btn.clicked.connect(self._fit_to_window)
        controls_layout.addWidget(fit_btn)

        layout.addWidget(controls_widget)

        close_btn = QPushButton(language_manager.tr("preview.close"))
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def update_language(self):
        """Update all UI texts when language changes."""
        self.setWindowTitle(language_manager.tr("preview.title"))
        if self.file_name:
            self.setWindowTitle(
                language_manager.tr("preview.preview_title", name=self.file_name)
            )

        self.file_label.setText(
            self.file_name if self.file_name else language_manager.tr("preview.no_file")
        )
        if self.file_size > 0:
            self.size_label.setText(
                language_manager.tr("preview.bytes", size=self.file_size)
            )

        self.play_btn.setText(language_manager.tr("preview.play_video"))
        self.play_btn.setToolTip(language_manager.tr("preview.play_tooltip"))

        # Update zoom buttons
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QWidget) and widget.layout():
                for j in range(widget.layout().count()):
                    child = widget.layout().itemAt(j).widget()
                    if isinstance(child, QPushButton):
                        text = child.text()
                        if "+" in text:
                            child.setText(language_manager.tr("preview.zoom_in"))
                        elif "-" in text:
                            child.setText(language_manager.tr("preview.zoom_out"))
                        elif "100%" in text:
                            child.setText(language_manager.tr("preview.reset"))
                        elif "Fit" in text or "适应" in text:
                            child.setText(language_manager.tr("preview.fit_window"))
                        elif "Close" in text or "关闭" in text:
                            child.setText(language_manager.tr("preview.close"))

    def set_preview_handler(self, handler: PreviewHandler):
        """
        Set preview handler.

        Args:
            handler: PreviewHandler instance
        """
        self.preview_handler = handler

    def preview_file(self, remote_path: str, file_name: str, file_size: int):
        """
        Preview a file from device.

        Args:
            remote_path: Remote file path
            file_name: File name
            file_size: File size
        """
        if not self.preview_handler:
            show_warning_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("preview.handler_not_init"),
                self,
            )
            return

        if not self.preview_handler.can_preview(file_name, file_size):
            show_warning_dialog(
                language_manager.tr("dialogs.cannot_preview"),
                language_manager.tr("dialogs.cannot_preview_msg", name=file_name),
                self,
            )
            return

        self.file_name = file_name
        self.file_size = file_size

        self.setWindowTitle(
            language_manager.tr("preview.preview_title", name=file_name)
        )

        self.file_label.setText(file_name)
        self.size_label.setText(language_manager.tr("preview.bytes", size=file_size))

        logger.info(f"Previewing file: {file_name}")

        self.local_file_path = self.preview_handler.download_for_preview(remote_path)

        if not self.local_file_path:
            show_warning_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("preview.download_failed"),
                self,
            )
            return

        if self.preview_handler.is_image(file_name):
            self._preview_image()
        elif self.preview_handler.is_video(file_name):
            self._preview_video()

    def _preview_image(self):
        """Preview image file."""
        try:
            image = self.preview_handler.open_image(self.local_file_path)

            if not image:
                show_warning_dialog(
                    language_manager.tr("dialogs.error_title"),
                    language_manager.tr("preview.open_image_failed"),
                    self,
                )
                return

            # Convert PIL Image to QPixmap
            if image.mode == "RGBA":
                qimage = QImage(
                    image.tobytes(),
                    image.size[0],
                    image.size[1],
                    QImage.Format_RGBA8888,
                )
            else:
                qimage = QImage(
                    image.tobytes(), image.size[0], image.size[1], QImage.Format_RGB888
                )

            self.original_pixmap = QPixmap.fromImage(qimage)

            self.image_label.setPixmap(self.original_pixmap)
            self.image_label.show()
            self.video_placeholder.hide()

            logger.info(f"Image preview loaded: {image.size}")

            self._fit_to_window()

        except Exception as e:
            logger.error(f"Failed to preview image: {e}")
            show_warning_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("preview.preview_image_error", error=str(e)),
                self,
            )

    def _preview_video(self):
        """Preview video file (placeholder with play button)."""
        self.is_video = True

        self.image_label.hide()
        self.video_placeholder.show()

        self.video_info_label.setText(
            language_manager.tr(
                "preview.video_info", name=self.file_name, size=self.file_size
            )
        )

        logger.info(f"Video preview placeholder shown: {self.file_name}")

    def _play_video(self):
        """Play video with system player."""
        if not self.local_file_path or not self.preview_handler:
            return

        success = self.preview_handler.open_video_with_system_player(
            self.local_file_path
        )

        if success:
            logger.info(f"Video opened with system player")
        else:
            show_warning_dialog(
                language_manager.tr("dialogs.error_title"),
                language_manager.tr("preview.open_video_failed"),
                self,
            )

    def _zoom_in(self):
        """Zoom in (increase scale by 10%)."""
        if not self.original_pixmap:
            return

        self.current_scale += 0.1

        self._apply_zoom()

    def _zoom_out(self):
        """Zoom out (decrease scale by 10%)."""
        if not self.original_pixmap:
            return

        self.current_scale -= 0.1

        if self.current_scale < 0.1:
            self.current_scale = 0.1

        self._apply_zoom()

    def _reset_zoom(self):
        """Reset zoom to 100%."""
        if not self.original_pixmap:
            return

        self.current_scale = 1.0

        self._apply_zoom()

    def _fit_to_window(self):
        """Fit image to window size."""
        if not self.original_pixmap:
            return

        window_size = self.size()

        pixmap_size = self.original_pixmap.size()

        width_scale = window_size.width() / pixmap_size.width()
        height_scale = window_size.height() / pixmap_size.height()

        self.current_scale = min(width_scale, height_scale) * 0.9

        self._apply_zoom()

    def _apply_zoom(self):
        """Apply current zoom scale."""
        if not self.original_pixmap:
            return

        new_size = self.original_pixmap.size() * self.current_scale

        scaled_pixmap = self.original_pixmap.scaled(
            new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        self.image_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        """Handle close event."""
        if self.preview_handler and self.local_file_path:
            self.preview_handler.cleanup_temp_file(self.local_file_path)

        logger.info("Preview window closed")

        event.accept()
