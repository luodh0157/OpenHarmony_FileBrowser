#!/usr/bin/env python3
"""
Simple test script for Phase 1 validation.
Run: python tests/simple_test.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_platform_detection():
    """Test platform detection."""
    from src.utils.platform_utils import get_platform, get_architecture
    
    platform = get_platform()
    arch = get_architecture()
    
    print(f"✓ Platform: {platform}")
    print(f"✓ Architecture: {arch}")
    
    assert platform in ["windows", "linux", "macos"]
    assert arch in ["x86_64", "arm64", "x86", "arm"]


def test_file_utils():
    """Test file utilities."""
    from src.utils.file_utils import (
        get_file_type,
        format_file_size,
        is_image_file,
        is_video_file,
    )
    
    assert get_file_type("test.jpg", False) == "image"
    assert get_file_type("test.mp4", False) == "video"
    assert get_file_type("test.txt", False) == "document"  # .txt is a document
    assert get_file_type("test.unknown", False) == "file"  # unknown extension
    assert get_file_type("folder", True) == "folder"
    
    print(f"✓ File type detection works")
    
    assert format_file_size(1024) == "1.00 KB"
    assert format_file_size(1024 * 1024) == "1.00 MB"
    
    print(f"✓ File size formatting works")
    
    assert is_image_file("test.jpg") == True
    assert is_image_file("test.txt") == False
    
    assert is_video_file("test.mp4") == True
    assert is_video_file("test.jpg") == False
    
    print(f"✓ File preview detection works")


def test_models():
    """Test data models."""
    from src.models.device import DeviceInfo, DeviceStatus
    from src.models.file_info import FileInfo, FileType
    from datetime import datetime
    
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
    
    print(f"✓ Device model works")
    
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
    
    print(f"✓ File info model works")


def test_config():
    """Test configuration."""
    from src.config import Config
    
    config = Config()
    
    assert config.app_name == "OpenHarmony File Browser"
    assert config.window_width == 1200
    assert config.window_height == 800
    assert config.transfer_max_workers == 3
    
    print(f"✓ Configuration works")


def test_logger():
    """Test logger."""
    from src.utils.logger import get_logger
    import logging
    
    logger = get_logger("TestLogger", level=logging.DEBUG)
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    
    print(f"✓ Logger works")


def test_hdc_wrapper_class():
    """Test HDC wrapper class (without actual HDC tool)."""
    from src.core.hdc_wrapper import HDCWrapper, HDCError
    
    print(f"✓ HDC wrapper class imported successfully")
    
    # This will fail without HDC tool, but that's expected
    try:
        from src.utils.platform_utils import get_hdc_executable
        hdc_path = get_hdc_executable()
        print(f"✓ HDC tool found at: {hdc_path}")
        
        # Try to initialize
        hdc = HDCWrapper()
        print(f"✓ HDC wrapper initialized successfully")
    except FileNotFoundError as e:
        print(f"⚠ HDC tool not found (expected): {e}")
        print(f"  Please place HDC tool in: hdc/{get_platform()}/{get_architecture()}/")
    except Exception as e:
        print(f"⚠ HDC initialization error: {e}")


def get_platform():
    """Get platform for message."""
    import platform
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    return system


def get_architecture():
    """Get architecture for message."""
    import platform
    machine = platform.machine().lower()
    
    arch_map = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }
    
    return arch_map.get(machine, machine)


def main():
    """Run all tests."""
    print("=" * 60)
    print("OpenHarmony File Browser - Phase 1 Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Platform Detection", test_platform_detection),
        ("File Utilities", test_file_utils),
        ("Data Models", test_models),
        ("Configuration", test_config),
        ("Logger", test_logger),
        ("HDC Wrapper", test_hdc_wrapper_class),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\nTesting: {name}")
        print("-" * 60)
        try:
            test_func()
            passed += 1
            print(f"✓ {name} PASSED")
        except Exception as e:
            failed += 1
            print(f"✗ {name} FAILED: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓✓✓ All Phase 1 tests passed! ✓✓✓")
        print("\nNext: Phase 2 - Device Management & GUI Framework")
        return 0
    else:
        print(f"\n✗✗✗ {failed} tests failed ✗✗✗")
        return 1


if __name__ == "__main__":
    sys.exit(main())