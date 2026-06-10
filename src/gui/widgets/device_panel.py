"""
Device panel widget for OpenHarmony File Browser.
Compact device selector with refresh button.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, QPushButton, QStyle
)
from PySide6.QtCore import Qt, Signal

from src.models.device import DeviceInfo, DeviceStatus
from src.utils.logger import get_logger
from src.utils.language_manager import language_manager


logger = get_logger(__name__)


class DevicePanel(QWidget):
    """
    Compact device panel widget.
    
    Displays:
    - Device dropdown selector
    - Refresh button
    """
    
    device_selected = Signal(str)
    
    def __init__(self):
        """Initialize device panel."""
        super().__init__()
        
        self.devices: List[DeviceInfo] = []
        self.current_device: Optional[str] = None
        
        self._init_ui()
        
        logger.info("Device panel initialized")
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        self.device_label = QLabel(language_manager.tr('device.label'))
        layout.addWidget(self.device_label)
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        layout.addWidget(self.device_combo, stretch=1)
        
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.refresh_btn.setToolTip(language_manager.tr('device.refresh_tooltip'))
        self.refresh_btn.setMaximumWidth(40)
        layout.addWidget(self.refresh_btn)
        
        layout.addStretch()
    
    def update_language(self):
        """Update all UI texts when language changes."""
        if hasattr(self, 'device_label'):
            self.device_label.setText(language_manager.tr('device.label'))
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setToolTip(language_manager.tr('device.refresh_tooltip'))
    
    def update_devices(self, devices: List[DeviceInfo]):
        """
        Update device list.
        
        Args:
            devices: List of device information
        """
        self.devices = devices
        self.device_combo.clear()
        
        no_device_text = f"{language_manager.tr('device.no_device')}  ▾"
        self.device_combo.addItem(no_device_text, None)
        
        for device in devices:
            display_text = device.display_name or device.device_id
            if device.model:
                display_text = f"{device.model}"
            
            status_icon = self._get_status_icon(device.status)
            display_text = f"{status_icon} {display_text}  ▾"
            
            self.device_combo.addItem(display_text, device.device_id)
        
        if len(devices) > 0:
            self.device_combo.setCurrentIndex(1)
        else:
            self.device_combo.setCurrentIndex(0)
    
    def _get_status_icon(self, status: DeviceStatus) -> str:
        """Get status icon for device."""
        icons = {
            DeviceStatus.CONNECTED: "✓",
            DeviceStatus.DISCONNECTED: "✗",
            DeviceStatus.UNAUTHORIZED: "?",
            DeviceStatus.OFFLINE: "○",
            DeviceStatus.UNKNOWN: "?",
        }
        return icons.get(status, "?")
    
    def _on_device_changed(self, index: int):
        """Handle device selection change."""
        device_id = self.device_combo.currentData()
        self.current_device = device_id
        
        if device_id:
            self.device_selected.emit(device_id)
            logger.info(f"Device selected: {device_id}")
