"""
Path navigation bar for OpenHarmony File Browser.
Displays breadcrumb navigation for current path.
"""

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QStyle,
    QCheckBox,
)
from PySide6.QtCore import Qt, Signal, QSize

from src.utils.logger import get_logger
from src.utils.language_manager import language_manager

logger = get_logger(__name__)


class PathBarWidget(QWidget):
    """
    Path navigation bar widget.

    Features:
    - Breadcrumb buttons for path parts
    - Path input field
    - Home button
    """

    path_changed = Signal(str)
    show_hidden_changed = Signal(bool)
    select_all_changed = Signal(int)

    def __init__(self):
        """Initialize path bar widget."""
        super().__init__()

        self.current_path: str = "/"

        self._init_ui()

        logger.info("Path bar widget initialized")

    def _init_ui(self):
        """Initialize UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 4, 5, 4)
        layout.setSpacing(4)

        home_btn = QPushButton()
        home_btn.setFlat(True)
        home_btn.setToolTip(language_manager.tr("path_bar.go_home"))
        home_btn.setIcon(self.style().standardIcon(QStyle.SP_DirHomeIcon))
        home_btn.setIconSize(QSize(16, 16))
        home_btn.setMaximumWidth(30)
        home_btn.clicked.connect(self._go_home)
        layout.addWidget(home_btn)

        self.breadcrumb_container = QWidget()
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_container)
        self.breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
        self.breadcrumb_layout.setSpacing(2)
        layout.addWidget(self.breadcrumb_container)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(language_manager.tr("path_bar.enter_path"))
        self.path_input.setMaximumHeight(22)
        self.path_input.returnPressed.connect(self._on_path_input)
        self.path_input.hide()

        layout.addWidget(self.path_input)

        toggle_btn = QPushButton("✏")
        toggle_btn.setFlat(True)
        toggle_btn.setToolTip(language_manager.tr("path_bar.toggle_edit"))
        toggle_btn.setMaximumWidth(30)
        toggle_btn.clicked.connect(self._toggle_edit_mode)
        layout.addWidget(toggle_btn)

        layout.addStretch()

        self.show_hidden_checkbox = QCheckBox(
            language_manager.tr("path_bar.show_hidden")
        )
        self.show_hidden_checkbox.setChecked(True)
        self.show_hidden_checkbox.stateChanged.connect(self._on_show_hidden_changed)
        layout.addWidget(self.show_hidden_checkbox)

        self.select_all_checkbox = QCheckBox(language_manager.tr("path_bar.select_all"))
        self.select_all_checkbox.stateChanged.connect(self._on_select_all_changed)
        layout.addWidget(self.select_all_checkbox)

        self.setMaximumHeight(37)

    def update_language(self):
        """Update all UI texts when language changes."""
        # Update show hidden checkbox
        if hasattr(self, "show_hidden_checkbox"):
            self.show_hidden_checkbox.setText(
                language_manager.tr("path_bar.show_hidden")
            )

        # Update select all checkbox
        if hasattr(self, "select_all_checkbox"):
            self.select_all_checkbox.setText(language_manager.tr("path_bar.select_all"))

        # Update path input placeholder
        if hasattr(self, "path_input"):
            self.path_input.setPlaceholderText(
                language_manager.tr("path_bar.enter_path")
            )

        # Update home button tooltip
        # Find home button (first button in layout)
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QPushButton) and widget.toolTip():
                # Home button is the first button with an icon
                if widget.icon().isNull() is False:
                    widget.setToolTip(language_manager.tr("path_bar.go_home"))
                    break

        # Update toggle button tooltip (second button with text "✏")
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QPushButton) and widget.text() == "✏":
                widget.setToolTip(language_manager.tr("path_bar.toggle_edit"))
                break

    def set_path(self, path: str):
        """
        Set current path.

        Args:
            path: Current path
        """
        self.current_path = path
        self._update_breadcrumb()

        logger.debug(f"Path set: {path}")

    def _update_breadcrumb(self):
        """Update breadcrumb buttons."""
        while self.breadcrumb_layout.count():
            item = self.breadcrumb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        parts = self.current_path.split("/")
        parts = [p for p in parts if p]

        current_path = ""

        for part in parts:
            current_path = f"{current_path}/{part}"

            btn = QPushButton(part)
            btn.setToolTip(current_path)
            btn.clicked.connect(
                lambda checked, p=current_path: self._on_breadcrumb_click(p)
            )

            self.breadcrumb_layout.addWidget(btn)

    def _on_breadcrumb_click(self, path: str):
        """Handle breadcrumb button click."""
        self.path_changed.emit(path)

        logger.debug(f"Breadcrumb clicked: {path}")

    def _go_home(self):
        """Go to root directory."""
        self.path_changed.emit("/")

        logger.debug("Going to root directory")

    def _on_path_input(self):
        """Handle path input."""
        path = self.path_input.text().strip()

        if path:
            self.path_changed.emit(path)

            logger.debug(f"Path input: {path}")

    def _on_show_hidden_changed(self, state):
        """Handle show hidden checkbox state change."""
        self.show_hidden_changed.emit(state == Qt.Checked.value)

        logger.debug(f"Show hidden changed: state={state}, Qt.Checked={Qt.Checked}")

    def _on_select_all_changed(self, state):
        """Handle select all checkbox state change."""
        self.select_all_changed.emit(state)

        logger.debug(f"Select all changed: {state}")

    def _toggle_edit_mode(self):
        """Toggle between breadcrumb and input mode."""
        if self.breadcrumb_container.isVisible():
            self.breadcrumb_container.hide()
            self.path_input.show()
            self.path_input.setText(self.current_path)
            self.path_input.setFocus()
        else:
            self.breadcrumb_container.show()
            self.path_input.hide()

    def refresh(self):
        """Refresh breadcrumb display."""
        self._update_breadcrumb()

        logger.debug("Path bar refreshed")
