"""
Unit tests for preview handler (src/core/preview_handler.py).
"""

import pytest
from src.core.preview_handler import PreviewHandler
from src.config import config


class TestPreviewHandlerCanPreview:
    """Tests for PreviewHandler.can_preview method."""

    @pytest.fixture
    def mock_hdc(self):
        class MockHdc:
            def file_recv(self, device_id, remote_path, local_path):
                pass
        return MockHdc()

    def test_image_can_preview(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.can_preview("test.jpg", 1024) is True

    def test_video_can_preview(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.can_preview("test.mp4", 1024) is True

    def test_txt_cannot_preview(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.can_preview("test.txt", 1024) is False

    def test_pdf_cannot_preview(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.can_preview("test.pdf", 1024) is False

    def test_large_image_cannot_preview(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        max_size = config.preview_max_size
        assert handler.can_preview("test.jpg", max_size + 1) is False

    def test_small_image_can_preview(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.can_preview("test.jpg", 1024) is True


class TestPreviewHandlerIsImageVideo:
    """Tests for PreviewHandler.is_image and is_video methods."""

    @pytest.fixture
    def mock_hdc(self):
        class MockHdc:
            def file_recv(self, device_id, remote_path, local_path):
                pass
        return MockHdc()

    def test_is_image_jpg(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.is_image("test.jpg") is True

    def test_is_image_png(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.is_image("test.png") is True

    def test_is_image_txt(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.is_image("test.txt") is False

    def test_is_video_mp4(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.is_video("test.mp4") is True

    def test_is_video_avi(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.is_video("test.avi") is True

    def test_is_video_txt(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.is_video("test.txt") is False


class TestPreviewHandlerInit:
    """Tests for PreviewHandler initialization."""

    @pytest.fixture
    def mock_hdc(self):
        class MockHdc:
            def file_recv(self, device_id, remote_path, local_path):
                pass
        return MockHdc()

    def test_device_id_set(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.device_id == "test_device"

    def test_max_preview_size_set(self, mock_hdc):
        handler = PreviewHandler(mock_hdc, "test_device")
        assert handler.max_preview_size == config.preview_max_size

    def test_uses_tempfile_not_temp_dir(self, mock_hdc):
        """测试使用 tempfile 而不是自定义 temp_dir"""
        handler = PreviewHandler(mock_hdc, "test_device")
        # 验证不再有 temp_dir 属性
        assert not hasattr(handler, 'temp_dir')
        # 验证其他属性正常
        assert handler.device_id == "test_device"
        assert handler.max_preview_size > 0
