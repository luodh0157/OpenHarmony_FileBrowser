"""
Device Manager for OpenHarmony File Browser.
Manages device connections, status monitoring, and device information.
"""

from typing import List, Optional, Dict
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QApplication

from .hdc_wrapper import HDCWrapper, HDCError
from ..models.device import DeviceInfo, DeviceStatus
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DeviceMonitorThread(QThread):
    """Thread for monitoring device status."""

    devices_updated = Signal(list)
    device_connected = Signal(object)
    device_disconnected = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, hdc: HDCWrapper, interval: int = 2000):
        """
        Initialize device monitor thread.

        Args:
            hdc: HDC wrapper instance
            interval: Monitoring interval in milliseconds
        """
        super().__init__()
        self.hdc = hdc
        self.interval = interval
        self.running = False
        self.current_devices: Dict[str, DeviceInfo] = {}

    def run(self):
        """Run the monitoring loop."""
        self.running = True
        logger.info("Device monitor thread started")

        while self.running:
            try:
                devices = self.hdc.list_targets()
                device_dict = {d.device_id: d for d in devices}

                new_devices = []
                removed_devices = []

                for device_id, device in device_dict.items():
                    if device_id not in self.current_devices:
                        new_devices.append(device)
                        try:
                            full_info = self.hdc.get_device_info(device_id)
                            device_dict[device_id] = full_info
                        except HDCError as e:
                            logger.warning(f"Failed to get device info: {e}")

                for device_id in self.current_devices:
                    if device_id not in device_dict:
                        removed_devices.append(device_id)

                self.current_devices = device_dict

                updated_devices = list(device_dict.values())
                self.devices_updated.emit(updated_devices)

                for device in new_devices:
                    self.device_connected.emit(device)
                    logger.info(f"Device connected: {device.device_id}")

                for device_id in removed_devices:
                    self.device_disconnected.emit(device_id)
                    logger.info(f"Device disconnected: {device_id}")

            except HDCError as e:
                self.error_occurred.emit(str(e))
                logger.error(f"Device monitoring error: {e}")

            self.msleep(self.interval)

    def stop(self):
        """Stop the monitoring thread."""
        self.running = False
        logger.info("Device monitor thread stopped")


class DeviceManager(QObject):
    """
    Device manager for managing OpenHarmony devices.

    Provides device connection, monitoring, and management functionality.
    """

    devices_changed = Signal(list)
    device_added = Signal(object)
    device_removed = Signal(str)
    connection_failed = Signal(str)

    def __init__(
        self, hdc: Optional[HDCWrapper] = None, auto_start_monitoring: bool = False
    ):
        """
        Initialize device manager.

        Args:
            hdc: HDC wrapper instance. If None, will create automatically.
            auto_start_monitoring: Whether to auto-start monitoring (default False - manual refresh)
        """
        super().__init__()

        if hdc is None:
            try:
                self.hdc = HDCWrapper()
                logger.info("HDC wrapper created successfully")
            except HDCError as e:
                self.hdc = None
                logger.error(f"Failed to create HDC wrapper: {e}")
                self.connection_failed.emit(str(e))
        else:
            self.hdc = hdc

        self.devices: List[DeviceInfo] = []
        self.monitor_thread: Optional[DeviceMonitorThread] = None
        self.monitoring = False

        # Don't auto-start monitoring - user will manually refresh
        logger.info("Device manager initialized (manual refresh mode)")

    def start_monitoring(self, interval: int = 2000) -> bool:
        """
        Start device monitoring.

        Args:
            interval: Monitoring interval in milliseconds

        Returns:
            True if monitoring started successfully
        """
        if not self.hdc:
            logger.error("HDC wrapper not available")
            return False

        if self.monitoring:
            logger.warning("Monitoring already running")
            return True

        try:
            self.monitor_thread = DeviceMonitorThread(self.hdc, interval)

            self.monitor_thread.devices_updated.connect(self._on_devices_updated)
            self.monitor_thread.device_connected.connect(self._on_device_connected)
            self.monitor_thread.device_disconnected.connect(
                self._on_device_disconnected
            )
            self.monitor_thread.error_occurred.connect(self._on_monitor_error)

            self.monitor_thread.start()
            self.monitoring = True

            logger.info(f"Device monitoring started (interval: {interval}ms)")
            return True

        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            return False

    def stop_monitoring(self):
        """Stop device monitoring."""
        if self.monitor_thread and self.monitoring:
            self.monitor_thread.stop()
            self.monitor_thread.wait()
            self.monitor_thread = None
            self.monitoring = False

            logger.info("Device monitoring stopped")

    def refresh_devices(self) -> List[DeviceInfo]:
        """
        Manually refresh device list.

        Returns:
            List of connected devices
        """
        if not self.hdc:
            logger.error("HDC wrapper not available")
            return []

        try:
            devices = self.hdc.list_targets()

            for i in range(len(devices)):
                try:
                    full_info = self.hdc.get_device_info(devices[i].device_id)
                    devices[i] = full_info
                except HDCError as e:
                    logger.warning(
                        f"Failed to get device info for {devices[i].device_id}: {e}"
                    )

            self.devices = devices
            self.devices_changed.emit(devices)

            logger.info(f"Found {len(devices)} devices")
            return devices

        except HDCError as e:
            logger.error(f"Failed to refresh devices: {e}")
            self.connection_failed.emit(str(e))
            return []

    def connect_wireless(self, ip_port: str) -> bool:
        """
        Connect to device via TCP/IP.

        Args:
            ip_port: IP address and port (e.g., "192.168.1.100:5555")

        Returns:
            True if connection successful
        """
        if not self.hdc:
            logger.error("HDC wrapper not available")
            return False

        try:
            logger.info(f"Connecting to wireless device: {ip_port}")
            self.hdc.tconn(ip_port)

            QApplication.processEvents()

            self.refresh_devices()

            logger.info(f"Successfully connected to: {ip_port}")
            return True

        except HDCError as e:
            logger.error(f"Failed to connect wirelessly: {e}")
            self.connection_failed.emit(str(e))
            return False

    def disconnect_wireless(self, ip_port: str) -> bool:
        """
        Disconnect from wireless device.

        Args:
            ip_port: IP address and port

        Returns:
            True if disconnection successful
        """
        if not self.hdc:
            logger.error("HDC wrapper not available")
            return False

        try:
            logger.info(f"Disconnecting from wireless device: {ip_port}")
            self.hdc.tdisconn(ip_port)

            QApplication.processEvents()

            self.refresh_devices()

            logger.info(f"Successfully disconnected from: {ip_port}")
            return True

        except HDCError as e:
            logger.error(f"Failed to disconnect wirelessly: {e}")
            return False

    def get_device(self, device_id: str) -> Optional[DeviceInfo]:
        """
        Get device by ID.

        Args:
            device_id: Device ID

        Returns:
            Device info or None if not found
        """
        for device in self.devices:
            if device.device_id == device_id:
                return device
        return None

    def get_connected_devices(self) -> List[DeviceInfo]:
        """
        Get all connected devices.

        Returns:
            List of connected devices
        """
        return [d for d in self.devices if d.status == DeviceStatus.CONNECTED]

    def get_ready_devices(self) -> List[DeviceInfo]:
        """
        Get all ready devices (connected and authorized).

        Returns:
            List of ready devices
        """
        return [d for d in self.devices if d.is_ready]

    def _on_devices_updated(self, devices: List[DeviceInfo]):
        """Handle devices updated signal."""
        self.devices = devices
        self.devices_changed.emit(devices)

    def _on_device_connected(self, device: DeviceInfo):
        """Handle device connected signal."""
        self.device_added.emit(device)

    def _on_device_disconnected(self, device_id: str):
        """Handle device disconnected signal."""
        self.device_removed.emit(device_id)

    def _on_monitor_error(self, error: str):
        """Handle monitor error signal."""
        self.connection_failed.emit(error)

    def cleanup(self):
        """Cleanup resources."""
        self.stop_monitoring()
        if self.hdc:
            self.hdc.cleanup()
        logger.info("Device manager cleanup completed")
