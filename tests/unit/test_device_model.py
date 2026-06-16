"""
Unit tests for device model (src/models/device.py).
"""

from src.models.device import DeviceInfo, DeviceStatus


class TestDeviceStatus:
    """Tests for DeviceStatus enum."""

    def test_status_values(self):
        assert DeviceStatus.DISCONNECTED.value == "disconnected"
        assert DeviceStatus.CONNECTED.value == "connected"
        assert DeviceStatus.UNAUTHORIZED.value == "unauthorized"
        assert DeviceStatus.OFFLINE.value == "offline"
        assert DeviceStatus.UNKNOWN.value == "unknown"

    def test_status_count(self):
        assert len(DeviceStatus) == 5


class TestDeviceInfo:
    """Tests for DeviceInfo dataclass."""

    def test_create_device_with_minimal_info(self):
        device = DeviceInfo(device_id="test_device")
        assert device.device_id == "test_device"
        assert device.status == DeviceStatus.UNKNOWN
        assert device.model is None
        assert device.brand is None
        assert device.is_wireless is False

    def test_create_device_with_full_info(self):
        device = DeviceInfo(
            device_id="192.168.1.100:5555",
            status=DeviceStatus.CONNECTED,
            model="HUAWEI Mate 60",
            brand="HUAWEI",
            product="OHB-AN00",
            device="OHB-AN00",
            transport_id="1",
            is_wireless=True,
        )
        assert device.device_id == "192.168.1.100:5555"
        assert device.status == DeviceStatus.CONNECTED
        assert device.model == "HUAWEI Mate 60"
        assert device.brand == "HUAWEI"
        assert device.product == "OHB-AN00"
        assert device.device == "OHB-AN00"
        assert device.transport_id == "1"
        assert device.is_wireless is True

    def test_str_representation_with_model(self):
        device = DeviceInfo(
            device_id="test_device",
            status=DeviceStatus.CONNECTED,
            model="HUAWEI Mate 60",
        )
        result = str(device)
        assert "test_device" in result
        assert "HUAWEI Mate 60" in result
        assert "connected" in result

    def test_str_representation_without_model(self):
        device = DeviceInfo(
            device_id="test_device",
            status=DeviceStatus.DISCONNECTED,
        )
        result = str(device)
        assert "test_device" in result
        assert "disconnected" in result

    def test_repr_representation(self):
        device = DeviceInfo(
            device_id="test_device",
            status=DeviceStatus.CONNECTED,
            model="Test Model",
            is_wireless=True,
        )
        result = repr(device)
        assert "DeviceInfo" in result
        assert "test_device" in result
        assert "Test Model" in result

    def test_display_name_with_model(self):
        device = DeviceInfo(
            device_id="test_device",
            model="HUAWEI Mate 60",
            brand="HUAWEI",
            device="OHB-AN00",
        )
        assert device.display_name == "HUAWEI Mate 60"

    def test_display_name_with_brand_and_device(self):
        device = DeviceInfo(
            device_id="test_device",
            brand="HUAWEI",
            device="OHB-AN00",
        )
        assert device.display_name == "HUAWEI OHB-AN00"

    def test_display_name_with_brand_only(self):
        device = DeviceInfo(
            device_id="test_device",
            brand="HUAWEI",
        )
        assert device.display_name == "HUAWEI"

    def test_display_name_fallback_to_device_id(self):
        device = DeviceInfo(device_id="test_device")
        assert device.display_name == "test_device"

    def test_is_ready_when_connected(self):
        device = DeviceInfo(
            device_id="test_device",
            status=DeviceStatus.CONNECTED,
        )
        assert device.is_ready is True

    def test_is_ready_when_disconnected(self):
        device = DeviceInfo(
            device_id="test_device",
            status=DeviceStatus.DISCONNECTED,
        )
        assert device.is_ready is False

    def test_is_ready_when_unauthorized(self):
        device = DeviceInfo(
            device_id="test_device",
            status=DeviceStatus.UNAUTHORIZED,
        )
        assert device.is_ready is False

    def test_is_ready_when_offline(self):
        device = DeviceInfo(
            device_id="test_device",
            status=DeviceStatus.OFFLINE,
        )
        assert device.is_ready is False

    def test_is_ready_when_unknown(self):
        device = DeviceInfo(
            device_id="test_device",
            status=DeviceStatus.UNKNOWN,
        )
        assert device.is_ready is False

    def test_wireless_device_detection(self):
        device = DeviceInfo(
            device_id="192.168.1.100:5555",
            is_wireless=True,
        )
        assert device.is_wireless is True

    def test_usb_device_detection(self):
        device = DeviceInfo(
            device_id="ABC123DEF456",
            is_wireless=False,
        )
        assert device.is_wireless is False
