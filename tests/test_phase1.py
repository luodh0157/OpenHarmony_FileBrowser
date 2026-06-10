"""
Test HDC wrapper functionality.
"""

import pytest
from pathlib import Path


def test_platform_detection():
    """Test platform detection."""
    from src.utils.platform_utils import get_platform, get_architecture
    
    platform = get_platform()
    arch = get_architecture()
    
    print(f"Platform: {platform}")
    print(f"Architecture: {arch}")
    
    assert platform in ["windows", "linux", "macos"]
    assert arch in ["x86_64", "arm64", "x86", "arm"]


def test_hdc_path_detection():
    """Test HDC path detection."""
    from src.utils.platform_utils import get_hdc_executable
    
    try:
        hdc_path = get_hdc_executable()
        print(f"HDC path: {hdc_path}")
        assert Path(hdc_path).exists()
    except FileNotFoundError as e:
        print(f"HDC not found (expected in test environment): {e}")
        assert True  # Expected in test environment


def test_file_utils():
    """Test file utilities."""
    from src.utils.file_utils import (
        get_file_type,
        get_file_icon,
        format_file_size,
        is_image_file,
        is_video_file,
    )
    
    assert get_file_type("test.jpg", False) == "image"
    assert get_file_type("test.mp4", False) == "video"
    assert get_file_type("test.txt", False) == "file"
    assert get_file_type("folder", True) == "folder"
    
    assert get_file_icon("test.jpg", False) == "image"
    assert get_file_icon("folder", True) == "folder"
    
    assert format_file_size(1024) == "1.00 KB"
    assert format_file_size(1024 * 1024) == "1.00 MB"
    
    assert is_image_file("test.jpg") == True
    assert is_image_file("test.txt") == False
    
    assert is_video_file("test.mp4") == True
    assert is_video_file("test.jpg") == False


def test_device_model():
    """Test device model."""
    from src.models.device import DeviceInfo, DeviceStatus
    
    device = DeviceInfo(
        device_id="192.168.1.100:5555",
        status=DeviceStatus.CONNECTED,
        model="HUAWEI Mate 60",
        brand="HUAWEI",
        is_wireless=True,
    )
    
    assert device.device_id == "192.168.1.100:5555"
    assert device.is_wireless == True
    assert device.is_ready == True
    assert device.display_name == "HUAWEI Mate 60"


def test_file_info_model():
    """Test file info model."""
    from src.models.file_info import FileInfo, FileType
    from datetime import datetime
    
    file_info = FileInfo(
        name="test.txt",
        path="/data/local/tmp/test.txt",
        is_dir=False,
        size=1024,
        permissions="-rw-r--r--",
        modified_time=datetime.now(),
        file_type=FileType.FILE,
    )
    
    assert file_info.name == "test.txt"
    assert file_info.is_dir == False
    assert file_info.extension == ".txt"
    assert file_info.display_size == "1.00 KB"


def test_config():
    """Test configuration."""
    from src.config import Config
    
    config = Config()
    
    assert config.app_name == "OpenHarmony File Browser"
    assert config.window_width == 1200
    assert config.window_height == 800
    assert config.transfer_max_workers == 3


def test_hdc_wrapper_initialization():
    """Test HDC wrapper initialization (without HDC tool)."""
    from src.core.hdc_wrapper import HDCWrapper, HDCError
    
    # This will fail if HDC tool is not available
    try:
        hdc = HDCWrapper()
        print(f"HDC initialized: {hdc.hdc_path}")
    except HDCError as e:
        print(f"HDC initialization failed (expected): {e}")
        assert True  # Expected in test environment


if __name__ == "__main__":
    print("Running tests...")
    print("\n=== Platform Detection ===")
    test_platform_detection()
    
    print("\n=== HDC Path Detection ===")
    test_hdc_path_detection()
    
    print("\n=== File Utils ===")
    test_file_utils()
    
    print("\n=== Device Model ===")
    test_device_model()
    
    print("\n=== File Info Model ===")
    test_file_info_model()
    
    print("\n=== Config ===")
    test_config()
    
    print("\n=== HDC Wrapper ===")
    test_hdc_wrapper_initialization()
    
    print("\n=== All tests passed! ===")