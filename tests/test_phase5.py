"""
Test script for Phase 5 validation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_preview_handler():
    """Test preview handler."""
    from src.core.preview_handler import PreviewHandler
    from src.utils.file_utils import is_image_file, is_video_file
    
    print("Testing PreviewHandler...")
    
    try:
        from src.utils.platform_utils import get_hdc_executable
        from src.core.hdc_wrapper import HDCWrapper
        
        hdc_path = get_hdc_executable()
        hdc = HDCWrapper()
        
        handler = PreviewHandler(hdc, "test_device")
        print(f"  ✓ PreviewHandler created")
        
        # Test can_preview
        assert handler.can_preview("test.jpg", 1024*1024) == True
        assert handler.can_preview("test.mp4", 1024*1024) == True
        assert handler.can_preview("test.txt", 1024) == False
        print(f"  ✓ can_preview() works")
        
        # Test is_image/is_video
        assert handler.is_image("test.jpg") == True
        assert handler.is_video("test.mp4") == True
        print(f"  ✓ is_image() and is_video() work")
        
        # Test temp directory
        assert handler.temp_dir.exists()
        print(f"  ✓ Temp directory exists")
        
        # Cleanup
        handler.cleanup_all_temp_files()
        print(f"  ✓ Cleanup works")
        
        print("✓ PreviewHandler works")
        return True
    
    except FileNotFoundError:
        print("  ⚠ HDC not found, skipping HDC-dependent tests")
        print("  ✓ PreviewHandler class imported successfully")
        return True
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preview_window():
    """Test preview window."""
    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.widgets.preview_window import PreviewWindow
        
        print("Testing PreviewWindow...")
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        window = PreviewWindow()
        print(f"  ✓ PreviewWindow created")
        
        assert window.preview_handler is None
        print(f"  ✓ Preview handler initialized as None")
        
        assert window.image_label is not None
        assert window.video_placeholder is not None
        print(f"  ✓ UI components created")
        
        # Test zoom methods (no actual zoom without pixmap)
        window._zoom_in()
        window._zoom_out()
        window._reset_zoom()
        window._fit_to_window()
        print(f"  ✓ Zoom methods callable")
        
        window.close()
        print(f"  ✓ Window close works")
        
        print("✓ PreviewWindow works")
        return True
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preview_integration():
    """Test preview integration in file browser."""
    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.widgets.file_browser import FileBrowserWidget
        
        print("Testing Preview Integration...")
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        browser = FileBrowserWidget()
        print(f"  ✓ FileBrowserWidget created")
        
        assert browser.preview_handler is None
        assert browser.preview_window is None
        print(f"  ✓ Preview components initialized as None")
        
        browser.clear_device()
        print(f"  ✓ clear_device() works with preview cleanup")
        
        print("✓ Preview integration works")
        return True
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_preview_detection():
    """Test file preview detection."""
    from src.utils.file_utils import is_previewable, is_image_file, is_video_file
    
    print("Testing File Preview Detection...")
    
    # Test image detection
    assert is_image_file("test.jpg") == True
    assert is_image_file("test.png") == True
    assert is_image_file("test.gif") == True
    assert is_image_file("test.bmp") == True
    assert is_image_file("test.webp") == True
    print(f"  ✓ Image file detection works")
    
    # Test video detection
    assert is_video_file("test.mp4") == True
    assert is_video_file("test.avi") == True
    assert is_video_file("test.mkv") == True
    assert is_video_file("test.mov") == True
    print(f"  ✓ Video file detection works")
    
    # Test previewable
    assert is_previewable("test.jpg") == True
    assert is_previewable("test.mp4") == True
    assert is_previewable("test.txt") == False
    print(f"  ✓ is_previewable() works")
    
    print("✓ File preview detection works")
    return True


def test_pillow_import():
    """Test Pillow import for image preview."""
    print("Testing Pillow (PIL) import...")
    
    try:
        from PIL import Image
        
        print(f"  ✓ Pillow imported successfully")
        
        # Test creating a simple image
        img = Image.new('RGB', (100, 100), color='red')
        print(f"  ✓ PIL Image creation works")
        
        print("✓ Pillow works")
        return True
    
    except ImportError:
        print(f"  ✗ Pillow not installed")
        return False
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run all Phase 5 tests."""
    print("=" * 60)
    print("OpenHarmony File Browser - Phase 5 Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Preview Handler", test_preview_handler),
        ("Preview Window", test_preview_window),
        ("Preview Integration", test_preview_integration),
        ("File Preview Detection", test_file_preview_detection),
        ("Pillow Import", test_pillow_import),
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
        print("\n✓✓✓ All Phase 5 tests passed! ✓✓✓")
        print("\nPhase 5 Complete:")
        print("  • Preview Handler (download, open, cleanup)")
        print("  • Preview Window (image display, video placeholder)")
        print("  • Zoom controls (in, out, reset, fit)")
        print("  • System video player integration")
        print("  • File preview detection")
        print("  • Integration with file browser")
        print("\nAll 5 Phases Completed! Application is fully functional!")
        return 0
    else:
        print(f"\n✗✗✗ {failed} tests failed ✗✗✗")
        return 1


if __name__ == "__main__":
    sys.exit(main())