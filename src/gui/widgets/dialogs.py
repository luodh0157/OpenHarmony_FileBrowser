"""
File operation dialogs for OpenHarmony File Browser.
Provides dialogs for rename, create folder, delete, etc.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
    QFormLayout,
)
from PySide6.QtCore import Qt

from src.utils.logger import get_logger
from src.utils.language_manager import language_manager

logger = get_logger(__name__)


def _translate_message_box_buttons(msg_box):
    """Translate all buttons in a QMessageBox."""
    for button in msg_box.buttons():
        sb = msg_box.standardButton(button)
        if sb == QMessageBox.Ok:
            button.setText(language_manager.tr("buttons.ok"))
        elif sb == QMessageBox.Cancel:
            button.setText(language_manager.tr("buttons.cancel"))
        elif sb == QMessageBox.Yes:
            button.setText(language_manager.tr("buttons.yes"))
        elif sb == QMessageBox.No:
            button.setText(language_manager.tr("buttons.no"))
        elif sb == QMessageBox.Close:
            button.setText(language_manager.tr("buttons.close"))


def show_error_dialog(title: str, message: str, parent=None):
    """Show error dialog with translated OK button."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.addButton(language_manager.tr("buttons.ok"), QMessageBox.AcceptRole)
    msg_box.exec()
    logger.error(f"Error dialog shown: {title} - {message}")


def show_success_dialog(title: str, message: str, parent=None):
    """Show success dialog with translated OK button."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.addButton(language_manager.tr("buttons.ok"), QMessageBox.AcceptRole)
    msg_box.exec()
    logger.info(f"Success dialog shown: {title} - {message}")


def show_warning_dialog(title: str, message: str, parent=None):
    """Show warning dialog with translated OK button."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.addButton(language_manager.tr("buttons.ok"), QMessageBox.AcceptRole)
    msg_box.exec()
    logger.warning(f"Warning dialog shown: {title} - {message}")


def _create_translated_button_box(standard_buttons, parent=None):
    """Create a QDialogButtonBox with translated button text."""
    button_box = QDialogButtonBox(standard_buttons, parent=parent)

    for button in button_box.buttons():
        if button == button_box.button(QDialogButtonBox.Ok):
            button.setText(language_manager.tr("buttons.ok"))
        elif button == button_box.button(QDialogButtonBox.Cancel):
            button.setText(language_manager.tr("buttons.cancel"))
        elif button == button_box.button(QDialogButtonBox.Yes):
            button.setText(language_manager.tr("buttons.yes"))
        elif button == button_box.button(QDialogButtonBox.No):
            button.setText(language_manager.tr("buttons.no"))

    return button_box


class RenameDialog(QDialog):
    """Dialog for renaming file or directory."""

    def __init__(self, current_name: str, parent=None):
        super().__init__(parent)

        self.setWindowTitle(language_manager.tr("dialogs.rename_title"))
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        self.info_label = QLabel(
            language_manager.tr("dialogs.rename_text", name=current_name)
        )
        layout.addWidget(self.info_label)

        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setText(current_name)
        self.name_edit.selectAll()
        form_layout.addRow(
            language_manager.tr("dialogs.rename_new_name"), self.name_edit
        )

        layout.addLayout(form_layout)

        buttons = _create_translated_button_box(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def update_language(self, current_name: str = None):
        """Update dialog texts for language change."""
        self.setWindowTitle(language_manager.tr("dialogs.rename_title"))
        if current_name and hasattr(self, "info_label"):
            self.info_label.setText(
                language_manager.tr("dialogs.rename_text", name=current_name)
            )
        for child in self.findChildren(QDialogButtonBox):
            for button in child.buttons():
                if child.buttonRole(button) == QDialogButtonBox.AcceptRole:
                    button.setText(language_manager.tr("buttons.ok"))
                elif child.buttonRole(button) == QDialogButtonBox.RejectRole:
                    button.setText(language_manager.tr("buttons.cancel"))

    def get_new_name(self) -> str:
        return self.name_edit.text().strip()


class CreateFolderDialog(QDialog):
    """Dialog for creating a new folder."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(language_manager.tr("dialogs.create_folder_title"))
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        self.info_label = QLabel(language_manager.tr("dialogs.create_folder_text"))
        layout.addWidget(self.info_label)

        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(
            language_manager.tr("dialogs.folder_name_placeholder")
        )
        form_layout.addRow(
            language_manager.tr("dialogs.create_folder_name"), self.name_edit
        )

        layout.addLayout(form_layout)

        buttons = _create_translated_button_box(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def update_language(self):
        """Update dialog texts for language change."""
        self.setWindowTitle(language_manager.tr("dialogs.create_folder_title"))
        if hasattr(self, "info_label"):
            self.info_label.setText(language_manager.tr("dialogs.create_folder_text"))
        if hasattr(self, "name_edit"):
            self.name_edit.setPlaceholderText(
                language_manager.tr("dialogs.folder_name_placeholder")
            )
        for child in self.findChildren(QDialogButtonBox):
            for button in child.buttons():
                if child.buttonRole(button) == QDialogButtonBox.AcceptRole:
                    button.setText(language_manager.tr("buttons.ok"))
                elif child.buttonRole(button) == QDialogButtonBox.RejectRole:
                    button.setText(language_manager.tr("buttons.cancel"))

    def get_folder_name(self) -> str:
        return self.name_edit.text().strip()


class DeleteConfirmDialog(QDialog):
    """Dialog for confirming delete operation."""

    def __init__(self, name: str, is_dir: bool = False, parent=None):
        super().__init__(parent)

        self.setWindowTitle(language_manager.tr("dialogs.delete_title"))
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        self.info_label = QLabel(
            language_manager.tr(
                "dialogs.delete_folder" if is_dir else "dialogs.delete_file"
            )
        )
        layout.addWidget(self.info_label)

        name_label = QLabel(f"<b>{name}</b>")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        if is_dir:
            self.warning_label = QLabel(
                "<font color='#F85149'>"
                + language_manager.tr("dialogs.delete_warning")
                + "</font>"
            )
            self.warning_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.warning_label)

        buttons = _create_translated_button_box(
            QDialogButtonBox.Yes | QDialogButtonBox.No, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def update_language(self, is_dir: bool = False):
        """Update dialog texts for language change."""
        self.setWindowTitle(language_manager.tr("dialogs.delete_title"))
        if hasattr(self, "info_label"):
            self.info_label.setText(
                language_manager.tr(
                    "dialogs.delete_folder" if is_dir else "dialogs.delete_file"
                )
            )
        if hasattr(self, "warning_label") and is_dir:
            self.warning_label.setText(
                "<font color='#F85149'>"
                + language_manager.tr("dialogs.delete_warning")
                + "</font>"
            )
        for child in self.findChildren(QDialogButtonBox):
            for button in child.buttons():
                if child.buttonRole(button) == QDialogButtonBox.AcceptRole:
                    button.setText(language_manager.tr("buttons.yes"))
                elif child.buttonRole(button) == QDialogButtonBox.RejectRole:
                    button.setText(language_manager.tr("buttons.no"))
