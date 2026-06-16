"""
Device model for OpenHarmony File Browser.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DeviceStatus(Enum):
    """Device connection status."""

    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    UNAUTHORIZED = "unauthorized"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class DeviceInfo:
    """
    Device information data class.

    Attributes:
        device_id: Device serial number or IP:PORT
        status: Device connection status
        model: Device model (e.g., 'HUAWEI Mate 60')
        brand: Device brand (e.g., 'HUAWEI')
        product: Product name
        device: Device name
        transport_id: Transport ID for wireless connection
        is_wireless: Whether connected via wireless
    """

    device_id: str
    status: DeviceStatus = DeviceStatus.UNKNOWN
    model: Optional[str] = None
    brand: Optional[str] = None
    product: Optional[str] = None
    device: Optional[str] = None
    transport_id: Optional[str] = None
    is_wireless: bool = False

    def __str__(self) -> str:
        """String representation of device."""
        parts = [self.device_id]
        if self.model:
            parts.append(f"({self.model})")
        parts.append(f"[{self.status.value}]")
        return " ".join(parts)

    def __repr__(self) -> str:
        """Repr representation."""
        return (
            f"DeviceInfo(device_id='{self.device_id}', "
            f"status={self.status}, model='{self.model}', "
            f"is_wireless={self.is_wireless})"
        )

    @property
    def display_name(self) -> str:
        """Get display name for the device."""
        if self.model:
            return self.model
        elif self.brand and self.device:
            return f"{self.brand} {self.device}"
        elif self.brand:
            return self.brand
        else:
            return self.device_id

    @property
    def compact_display_name(self) -> str:
        """Get compact display name with truncated device_id and model."""
        if len(self.device_id) > 16:
            short_id = f"{self.device_id[:6]}...{self.device_id[-6:]}"
        else:
            short_id = self.device_id
        if self.model:
            return f"{short_id} ({self.model})"
        return short_id

    @property
    def is_ready(self) -> bool:
        """Check if device is ready for operations."""
        return self.status == DeviceStatus.CONNECTED
