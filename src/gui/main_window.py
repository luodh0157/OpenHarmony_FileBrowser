"""
Main window for OpenHarmony File Browser.
Compact layout with device selector integrated into toolbar.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QLabel, QComboBox, QPushButton, QMessageBox, QStyle, QToolBar
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QAction, QKeySequence, QStandardItemModel, QStandardItem, QColor, QIcon, QPixmap, QPainter, QPalette

from src.config import config
from src.utils.logger import get_logger
from src.utils.language_manager import language_manager


logger = get_logger(__name__)


def _create_checkmark_icon(color: str, size: int = 16) -> QIcon:
    """Create a checkmark icon with specified color."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QColor(color))
    painter.setFont(painter.font())
    # Draw checkmark character
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "✓")
    painter.end()
    return QIcon(pixmap)


def _create_blank_icon(size: int = 16) -> QIcon:
    """Create a transparent blank icon for alignment."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    """Main window with integrated toolbar."""
    
    device_selected = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        self.device_manager = None
        self.current_device_id: Optional[str] = None
        self.theme_manager = None
        self.file_browser = None
        self._loading_widget = None
        
        # Menu actions (for language update)
        self.theme_action: Optional[QAction] = None
        self.language_action: Optional[QAction] = None
        
        # Set window properties (minimal, no heavy widget creation yet)
        self.setWindowTitle(f"{language_manager.tr('app_name')} {config.app_version}")
        self.setMinimumSize(config.window_min_width, config.window_min_height)
        self.resize(config.window_width, config.window_height)
        
        # Apply stylesheet BEFORE creating widget tree (much faster)
        self._init_theme_manager()
        self.theme_manager.apply_stylesheet()
        
        # Show loading placeholder
        self._show_loading_placeholder()
        
        # Show window immediately with loading indicator
        self.show()
        
        # Defer heavy widget creation to event loop (non-blocking)
        QTimer.singleShot(50, self._init_ui_deferred)
        
        logger.info("Main window initialized and shown")
    
    def _show_loading_placeholder(self):
        """Show a clean loading placeholder while deferring heavy UI init."""
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QLabel
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self._loading_widget = QLabel(language_manager.tr('status.initializing'))
        self._loading_widget.setAlignment(Qt.AlignCenter)
        self._loading_widget.setStyleSheet(
            "color: #888; font-size: 18px; padding: 60px;"
        )
        layout.addWidget(self._loading_widget)
    
    def _init_ui_deferred(self):
        """Initialize heavy UI components after window is visible."""
        self._init_ui()
        self._create_status_bar()
        
        # Remove loading placeholder
        if self._loading_widget:
            self._loading_widget.setParent(None)
            self._loading_widget = None
        
        # Now defer device initialization
        QTimer.singleShot(100, self._init_device_manager_later)
        
        logger.info("Deferred UI initialization complete")
    
    def _init_ui(self):
        """Initialize UI with toolbar (called deferred after window is visible)."""
        from src.utils.icon_manager import icon_manager
        from src.gui.widgets.file_browser import FileBrowserWidget
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Combined toolbar: Device selector + File operations
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(26, 26))
        toolbar.setFixedHeight(37)
        
        # Set bold font for toolbar
        toolbar_font = toolbar.font()
        toolbar_font.setBold(True)
        toolbar.setFont(toolbar_font)
        
        # Device selector
        self.device_label = QLabel(language_manager.tr('device.label'))
        toolbar.addWidget(self.device_label)
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(150)
        self.device_combo.setMinimumHeight(20)
        self.device_combo.setMaximumHeight(28)
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        toolbar.addWidget(self.device_combo)
        
        refresh_devices_btn = QAction(icon_manager.get_icon('refresh_devices'), language_manager.tr('toolbar.refresh_devices'), self)
        refresh_devices_btn.setToolTip(language_manager.tr('device.refresh_tooltip'))
        refresh_devices_btn.triggered.connect(self._refresh_devices)
        toolbar.addAction(refresh_devices_btn)
        
        toolbar.addSeparator()
        
        # File operations (exposed from file_browser)
        self.file_browser = FileBrowserWidget()
        self.file_browser.status_message.connect(self.set_status_message)
        self.file_browser.setup_toolbar(toolbar)
        
        layout.addWidget(toolbar)
        layout.addWidget(self.file_browser, stretch=1)
        
        self._create_menu_bar()
    
    def _init_theme_manager(self):
        """Initialize theme manager."""
        from src.gui.styles.theme_manager import ThemeManager
        
        self.theme_manager = ThemeManager(self)
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
        
        logger.info(f"Theme manager initialized with theme: {self.theme_manager.current_theme}")
    
    def _toggle_theme(self):
        """Toggle between light and dark theme."""
        if self.theme_manager:
            self.theme_manager.toggle_theme()
    
    def _on_theme_changed(self, theme: str):
        """Handle theme change."""
        from src.utils.icon_manager import icon_manager
        
        icon_name = 'sun' if theme == 'dark' else 'moon'
        if self.theme_action:
            self.theme_action.setIcon(icon_manager.get_icon(icon_name))
        
        logger.info(f"UI updated for theme: {theme}")
    
    def _toggle_language(self):
        """Toggle between English and Chinese."""
        language_manager.toggle_language()
        self._on_language_changed(language_manager.current_language)
    
    def _on_language_changed(self, language: str):
        """Handle language change."""
        # Update window title
        self.setWindowTitle(f"{language_manager.tr('app_name')} {config.app_version}")
        
        # Update all UI texts
        self._update_ui_language()
        
        # Request file browser to update language
        if hasattr(self.file_browser, 'update_language'):
            self.file_browser.update_language()
        
        logger.info(f"UI updated for language: {language}")
    
    def _update_ui_language(self):
        """Update all UI components for language change."""
        # Update device label
        if hasattr(self, 'device_label') and self.device_label:
            self.device_label.setText(language_manager.tr('device.label'))
        
        # Update status bar
        if hasattr(self, 'device_label_status') and self.device_label_status:
            self.device_label_status.setText(language_manager.tr('status.no_device'))
        
        # Update menu bar
        self._update_menu_language()
    
    def _update_menu_language(self):
        """Update menu bar texts for language change."""
        menubar = self.menuBar()
        
        # Clear and recreate menu bar
        menubar.clear()
        
        file_menu = menubar.addMenu(language_manager.tr('menu.file'))
        
        refresh_action = QAction(language_manager.tr('menu.refresh_devices'), self)
        refresh_action.triggered.connect(self._refresh_devices)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(language_manager.tr('menu.exit'), self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu with Theme and Language
        view_menu = menubar.addMenu(language_manager.tr('menu.view'))
        
        if self.theme_action:
            self.theme_action.setText(language_manager.tr('menu.theme'))
            self.theme_action.setToolTip(language_manager.tr('menu.theme_tooltip'))
        view_menu.addAction(self.theme_action)
        
        if self.language_action:
            self.language_action.setText(language_manager.tr('menu.language'))
            self.language_action.setToolTip(language_manager.tr('menu.language_tooltip'))
        view_menu.addAction(self.language_action)
        
        help_menu = menubar.addMenu(language_manager.tr('menu.help'))
        
        about_action = QAction(language_manager.tr('menu.about'), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_menu_bar(self):
        """Create menu bar."""
        from src.utils.icon_manager import icon_manager
        
        menubar = self.menuBar()
        menu_font = menubar.font()
        menu_font.setBold(True)
        menubar.setFont(menu_font)
        
        file_menu = menubar.addMenu(language_manager.tr('menu.file'))
        
        refresh_action = QAction(language_manager.tr('menu.refresh_devices'), self)
        refresh_action.triggered.connect(self._refresh_devices)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(language_manager.tr('menu.exit'), self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        view_menu = menubar.addMenu(language_manager.tr('menu.view'))
        
        self.theme_action = QAction(icon_manager.get_icon('sun'), language_manager.tr('menu.theme'), self)
        self.theme_action.setToolTip(language_manager.tr('menu.theme_tooltip'))
        self.theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(self.theme_action)
        
        self.language_action = QAction(language_manager.tr('menu.language'), self)
        self.language_action.setToolTip(language_manager.tr('menu.language_tooltip'))
        self.language_action.triggered.connect(self._toggle_language)
        view_menu.addAction(self.language_action)
        
        help_menu = menubar.addMenu(language_manager.tr('menu.help'))
        
        about_action = QAction(language_manager.tr('menu.about'), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self):
        """Create status bar."""
        statusbar = self.statusBar()
        
        self.file_count_label = QLabel(language_manager.tr('status.items', count=0))
        statusbar.addWidget(self.file_count_label, 1)
        
        self.device_label_status = QLabel(language_manager.tr('status.no_device'))
        statusbar.addPermanentWidget(self.device_label_status)
    
    def set_status_message(self, message: str):
        """Update status bar message (file count info)."""
        # message contains count like "5 items" or path info
        # Try to extract count for translation
        try:
            parts = message.split()
            if parts and parts[0].isdigit():
                count = int(parts[0])
                translated = language_manager.tr('status.items', count=count)
                self.file_count_label.setText(translated)
                return
        except:
            pass
        
        # Check if it's a path status message
        if " - " in message:
            parts = message.split(" - ", 1)
            if len(parts) == 2 and parts[1].endswith("items"):
                try:
                    count = int(parts[1].split()[0])
                    self.file_count_label.setText(language_manager.tr('status.items', count=count))
                    return
                except:
                    pass
        
        self.file_count_label.setText(message)
    
    def update_device_status(self, device_id: str = None, device_name: str = None):
        """Update device status display."""
        if device_id and device_name:
            self.device_label_status.setText(
                f"<span style='color: #22c55e;'>{language_manager.tr('status.connected', device_name=device_name)}</span>"
            )
        else:
            self.device_label_status.setText(language_manager.tr('status.no_device'))
    
    def _init_device_manager_later(self):
        """Initialize device manager after UI is shown (delayed startup optimization)."""
        from src.core.device_manager import DeviceManager
        from src.gui.widgets.dialogs import show_warning_dialog
        
        self.file_count_label.setText(language_manager.tr('status.initializing'))
        
        try:
            self.device_manager = DeviceManager(auto_start_monitoring=False)
            
            logger.info("Device manager initialized")
            
            # Auto-refresh devices after initialization
            QTimer.singleShot(200, self._auto_refresh_devices)
        
        except Exception as e:
            logger.error(f"Failed to initialize device manager: {e}")
            self.file_count_label.setText(f"Error: {e}")
            
            show_warning_dialog(
                language_manager.tr('dialogs.hdc_not_found'),
                language_manager.tr('dialogs.hdc_not_found_text', error=str(e)),
                self
            )
    
    def _auto_refresh_devices(self):
        """Automatically refresh devices and update status bar."""
        if not self.device_manager:
            return
        
        self.file_count_label.setText(language_manager.tr('status.scanning'))
        
        try:
            devices = self.device_manager.refresh_devices()
            self._update_device_combo(devices)
            
            # Auto-connect first device if available
            if len(devices) > 0:
                device = devices[0]
                self.file_count_label.setText(
                    language_manager.tr('status.found_devices_connecting', count=len(devices))
                )
                self.device_combo.setCurrentIndex(0)
                
                logger.info(f"Auto-connected to first device: {device.device_id}")
            else:
                self.file_count_label.setText(language_manager.tr('status.no_devices_found'))
                self.update_device_status()
        
        except Exception as e:
            logger.error(f"Failed to refresh devices: {e}")
            self.file_count_label.setText(language_manager.tr('status.scan_error', e=str(e)))
            self.update_device_status()  # Clear status
    
    def _update_device_combo(self, devices: list):
        """Update device combo box."""
        self.device_combo.clear()
        self._devices_cache = devices
        
        if len(devices) == 0:
            self.device_combo.addItem(language_manager.tr('device.no_device'), None)
        else:
            for device in devices:
                display_name = device.model or device.device_id[:15]
                self.device_combo.addItem(display_name, device.device_id)
            
            self.device_combo.setCurrentIndex(0)
            self._update_device_display()
    
    def _update_device_display(self):
        """Update device combo box display to show checkmark only for selected device."""
        current_index = self.device_combo.currentIndex()
        checkmark_icon = _create_checkmark_icon('#2563eb')
        blank_icon = _create_blank_icon()
        blue_color = QColor('#2563eb')
        normal_color = self.palette().color(QPalette.WindowText)
        
        for i in range(self.device_combo.count()):
            device_id = self.device_combo.itemData(i)
            if device_id is None:
                continue
            
            display_name = self.device_combo.itemText(i)
            # Remove existing checkmark or blank space prefix, but keep arrow
            if display_name.startswith("✓ "):
                original_name = display_name[2:]
            elif display_name.startswith("  "):
                original_name = display_name[2:]
            else:
                original_name = display_name
            
            if i == current_index:
                # Selected: blue text with checkmark icon (no text checkmark)
                self.device_combo.setItemText(i, original_name)
                self.device_combo.setItemData(i, blue_color, Qt.ForegroundRole)
                self.device_combo.setItemIcon(i, checkmark_icon)
            else:
                # Unselected: blank space for alignment, normal color
                self.device_combo.setItemText(i, original_name)
                self.device_combo.setItemData(i, normal_color, Qt.ForegroundRole)
                self.device_combo.setItemIcon(i, blank_icon)
    
    def _on_device_changed(self, index: int):
        """Handle device selection change."""
        new_device_id = self.device_combo.currentData()
        
        # Clear old device if switching
        if self.current_device_id and new_device_id != self.current_device_id:
            self.file_browser.clear_device()
        
        self.current_device_id = new_device_id
        
        self._update_device_display()
        
        if new_device_id and self.device_manager:
            device = self.device_manager.get_device(new_device_id)
            if device:
                self.update_device_status(new_device_id, device.display_name)
                self.file_browser.set_device(new_device_id, self.device_manager.hdc)
                self.device_selected.emit(new_device_id)
                logger.info(f"Device changed to: {device.display_name} ({new_device_id})")
            else:
                self.update_device_status(new_device_id, new_device_id[:15])
                logger.warning(f"Device info not found for: {new_device_id}")
        else:
            self.update_device_status()
            logger.info("No device selected")
    
    def _refresh_devices(self):
        """Refresh device list."""
        if self.device_manager:
            self.file_count_label.setText(language_manager.tr('status.scanning'))
            devices = self.device_manager.refresh_devices()
            self._update_device_combo(devices)
            
            if len(devices) > 0:
                self.file_count_label.setText(language_manager.tr('status.found_devices', count=len(devices)))
            else:
                self.file_count_label.setText(language_manager.tr('status.no_devices_found_short'))
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            language_manager.tr('dialogs.about_title'),
            language_manager.tr('dialogs.about_text', app_name=config.app_name, version=config.app_version),
        )
    
    def closeEvent(self, event):
        """Handle close event."""
        if self.device_manager:
            self.device_manager.cleanup()
        
        logger.info("Application closed")
        event.accept()
