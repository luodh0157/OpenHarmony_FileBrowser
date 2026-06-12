"""
Unit tests for file utilities (src/utils/file_utils.py).
"""

import pytest
from src.utils.file_utils import (
    get_file_type,
    get_file_icon,
    format_file_size,
    format_permissions,
    is_image_file,
    is_video_file,
    is_previewable,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    AUDIO_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    ARCHIVE_EXTENSIONS,
    CODE_EXTENSIONS,
)


class TestGetFileType:
    """Tests for get_file_type function."""

    def test_directory_returns_folder(self):
        assert get_file_type("documents", is_dir=True) == "folder"

    def test_image_extensions(self):
        for ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"]:
            assert get_file_type(f"test{ext}", is_dir=False) == "image"

    def test_video_extensions(self):
        for ext in [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"]:
            assert get_file_type(f"test{ext}", is_dir=False) == "video"

    def test_audio_extensions(self):
        for ext in [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"]:
            assert get_file_type(f"test{ext}", is_dir=False) == "audio"

    def test_document_extensions(self):
        for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".rtf"]:
            assert get_file_type(f"test{ext}", is_dir=False) == "document"

    def test_archive_extensions(self):
        for ext in [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"]:
            assert get_file_type(f"test{ext}", is_dir=False) == "archive"

    def test_code_extensions(self):
        for ext in [".py", ".js", ".java", ".c", ".cpp", ".go", ".rs", ".html"]:
            assert get_file_type(f"test{ext}", is_dir=False) == "code"

    def test_unknown_extension_returns_file(self):
        assert get_file_type("test.unknown", is_dir=False) == "file"

    def test_case_insensitive(self):
        assert get_file_type("test.JPG", is_dir=False) == "image"
        assert get_file_type("test.MP4", is_dir=False) == "video"
        assert get_file_type("test.PY", is_dir=False) == "code"


class TestGetFileIcon:
    """Tests for get_file_icon function."""

    def test_directory_icon(self):
        assert get_file_icon("documents", is_dir=True) == "folder"

    def test_image_icon(self):
        assert get_file_icon("test.jpg", is_dir=False) == "image"

    def test_video_icon(self):
        assert get_file_icon("test.mp4", is_dir=False) == "video"

    def test_unknown_icon(self):
        assert get_file_icon("test.xyz", is_dir=False) == "file"


class TestFormatFileSize:
    """Tests for format_file_size function."""

    def test_zero_bytes(self):
        assert format_file_size(0) == "0 B"

    def test_bytes(self):
        assert format_file_size(512) == "512 B"

    def test_kilobytes(self):
        assert format_file_size(1024) == "1.00 KB"

    def test_megabytes(self):
        assert format_file_size(1024 * 1024) == "1.00 MB"

    def test_gigabytes(self):
        assert format_file_size(1024 * 1024 * 1024) == "1.00 GB"

    def test_terabytes(self):
        assert format_file_size(1024 * 1024 * 1024 * 1024) == "1.00 TB"

    def test_fractional_kb(self):
        result = format_file_size(1536)
        assert "1.50 KB" in result

    def test_fractional_mb(self):
        result = format_file_size(1572864)
        assert "1.50 MB" in result


class TestFormatPermissions:
    """Tests for format_permissions function."""

    def test_valid_permissions(self):
        perms = "drwxr-xr-x"
        result = format_permissions(perms)
        assert len(result) == 10

    def test_short_permissions(self):
        perms = "rwx"
        result = format_permissions(perms)
        assert result == perms

    def test_empty_permissions(self):
        result = format_permissions("")
        assert result == ""

    def test_none_permissions(self):
        result = format_permissions(None)
        assert result is None


class TestIsImageFile:
    """Tests for is_image_file function."""

    def test_jpg_is_image(self):
        assert is_image_file("test.jpg") is True

    def test_png_is_image(self):
        assert is_image_file("test.png") is True

    def test_txt_not_image(self):
        assert is_image_file("test.txt") is False

    def test_case_insensitive(self):
        assert is_image_file("test.JPG") is True


class TestIsVideoFile:
    """Tests for is_video_file function."""

    def test_mp4_is_video(self):
        assert is_video_file("test.mp4") is True

    def test_avi_is_video(self):
        assert is_video_file("test.avi") is True

    def test_txt_not_video(self):
        assert is_video_file("test.txt") is False

    def test_case_insensitive(self):
        assert is_video_file("test.MP4") is True


class TestIsPreviewable:
    """Tests for is_previewable function."""

    def test_image_is_previewable(self):
        assert is_previewable("test.jpg") is True

    def test_video_is_previewable(self):
        assert is_previewable("test.mp4") is True

    def test_txt_not_previewable(self):
        assert is_previewable("test.txt") is False

    def test_pdf_not_previewable(self):
        assert is_previewable("test.pdf") is False
