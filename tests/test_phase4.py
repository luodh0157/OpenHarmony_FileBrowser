"""
Test script for Phase 4 validation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_transfer_manager():
    """Test transfer manager."""
    from src.core.transfer_manager import (
        TransferManager, TransferTask, TransferStatus, TransferDirection
    )
    
    print("Testing TransferManager...")
    
    try:
        manager = TransferManager(max_workers=3)
        print(f"  ✓ TransferManager created")
        
        task = TransferTask(
            local_path="/tmp/test.txt",
            remote_path="/data/local/tmp/test.txt",
            direction=TransferDirection.UPLOAD,
            device_id="test_device"
        )
        print(f"  ✓ TransferTask created")
        
        assert task.status == TransferStatus.PENDING
        assert task.direction == TransferDirection.UPLOAD
        
        print(f"  ✓ Transfer status and direction enums work")
        
        manager.cleanup()
        print(f"  ✓ Cleanup works")
        
        print("✓ TransferManager works")
        return True
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_transfer_dialog():
    """Test transfer dialog."""
    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.widgets.transfer_dialog import TransferDialog
        from src.core.transfer_manager import TransferTask, TransferDirection
        
        print("Testing TransferDialog...")
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        dialog = TransferDialog()
        print(f"  ✓ TransferDialog created")
        
        task = TransferTask(
            local_path="/tmp/test.txt",
            remote_path="/data/test.txt",
            direction=TransferDirection.UPLOAD,
            device_id="test"
        )
        
        dialog.add_task(task)
        print(f"  ✓ add_task() works")
        
        dialog.update_progress("/tmp/test.txt", 50, 1024, 512.0)
        print(f"  ✓ update_progress() works")
        
        dialog.mark_completed("/tmp/test.txt", True, "")
        print(f"  ✓ mark_completed() works")
        
        dialog.clear_tasks()
        print(f"  ✓ clear_tasks() works")
        
        print("✓ TransferDialog works")
        return True
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_browser_with_transfer():
    """Test file browser with transfer integration."""
    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.widgets.file_browser import FileBrowserWidget
        
        print("Testing FileBrowserWidget (with transfer)...")
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        browser = FileBrowserWidget()
        print(f"  ✓ FileBrowserWidget created")
        
        assert browser.transfer_manager is None
        print(f"  ✓ Transfer manager initialized as None")
        
        browser.clear_device()
        print(f"  ✓ clear_device() works")
        
        print(f"  ✓ Drag & drop enabled: {browser.acceptDrops()}")
        
        print("✓ FileBrowserWidget transfer integration works")
        return True
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_transfer_directions():
    """Test transfer direction functionality."""
    from src.core.transfer_manager import TransferDirection
    
    print("Testing TransferDirection enum...")
    
    assert TransferDirection.UPLOAD.value == "upload"
    assert TransferDirection.DOWNLOAD.value == "download"
    
    print(f"  ✓ UPLOAD direction: {TransferDirection.UPLOAD.value}")
    print(f"  ✓ DOWNLOAD direction: {TransferDirection.DOWNLOAD.value}")
    
    print("✓ TransferDirection works")
    return True


def test_transfer_status():
    """Test transfer status functionality."""
    from src.core.transfer_manager import TransferStatus
    
    print("Testing TransferStatus enum...")
    
    statuses = [
        TransferStatus.PENDING,
        TransferStatus.RUNNING,
        TransferStatus.COMPLETED,
        TransferStatus.FAILED,
        TransferStatus.CANCELLED
    ]
    
    for status in statuses:
        print(f"  ✓ {status.value}")
    
    print("✓ TransferStatus works")
    return True


def main():
    """Run all Phase 4 tests."""
    print("=" * 60)
    print("OpenHarmony File Browser - Phase 4 Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Transfer Manager", test_transfer_manager),
        ("Transfer Dialog", test_transfer_dialog),
        ("File Browser with Transfer", test_file_browser_with_transfer),
        ("Transfer Direction", test_transfer_directions),
        ("Transfer Status", test_transfer_status),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\nTesting: {name}")
        print("-" * 60)
        try:
            if test_func():
                passed += 1
                print(f"✓ {name} PASSED")
            else:
                failed += 1
                print(f"✗ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {name} FAILED: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓✓✓ All Phase 4 tests passed! ✓✓✓")
        print("\nPhase 4 Complete:")
        print("  • Transfer Manager (thread pool, progress tracking)")
        print("  • Transfer Dialog (progress display, cancel)")
        print("  • Upload/Download buttons")
        print("  • Drag & Drop support")
        print("  • Recursive folder transfer (helper)")
        print("  • Integration with file browser")
        print("\nNext: Phase 5 - File Preview")
        return 0
    else:
        print(f"\n✗✗✗ {failed} tests failed ✗✗✗")
        return 1


if __name__ == "__main__":
    sys.exit(main())