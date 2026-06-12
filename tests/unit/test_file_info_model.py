"""
Unit tests for file info model (src/models/file_info.py).
"""

import pytest
from datetime import datetime
from src.models.file_info import FileInfo, FileType


class TestFileType:
    """Tests for FileType enum."""

    def test_type_values(self):
        assert FileType.FILE.value == "file"
        assert FileType.DIRECTORY.value == "directory"
        assert FileType.SYMLINK.value == "symlink"
        assert FileType.UNKNOWN.value == "unknown"

    def test_type_count(self):
        assert len(FileType) == 4


class TestFileInfo:
    """Tests for FileInfo dataclass."""

    def test_create_file_with_minimal_info(self):
        file_info = FileInfo(name="test.txt", path="/tmp/test.txt")
        assert file_info.name == "test.txt"
        assert file_info.path == "/tmp/test.txt"
        assert file_info.is_dir is False
        assert file_info.size == 0
        assert file_info.file_type == FileType.FILE

    def test_create_file_with_full_info(self):
        now = datetime.now()
        file_info = FileInfo(
            name="test.txt",
            path="/data/local/tmp/test.txt",
            is_dir=False,
            size=1024,
            permissions="-rw-r--r--",
            modified_time=now,
            file_type=FileType.FILE,
            owner="root",
            group="root",
            links=1,
        )
        assert file_info.name == "test.txt"
        assert file_info.path == "/data/local/tmp/test.txt"
        assert file_info.is_dir is False
        assert file_info.size == 1024
        assert file_info.permissions == "-rw-r--r--"
        assert file_info.modified_time == now
        assert file_info.owner == "root"
        assert file_info.group == "root"
        assert file_info.links == 1

    def test_create_directory_info(self):
        dir_info = FileInfo(
            name="documents",
            path="/data/local/tmp/documents",
            is_dir=True,
            file_type=FileType.DIRECTORY,
        )
        assert dir_info.is_dir is True
        assert dir_info.file_type == FileType.DIRECTORY

    def test_str_representation_for_file(self):
        file_info = FileInfo(
            name="test.txt",
            path="/tmp/test.txt",
            size=1024,
        )
        result = str(file_info)
        assert "FILE" in result
        assert "test.txt" in result
        assert "1024" in result

    def test_str_representation_for_directory(self):
        dir_info = FileInfo(
            name="documents",
            path="/tmp/documents",
            is_dir=True,
        )
        result = str(dir_info)
        assert "DIR" in result
        assert "documents" in result

    def test_repr_representation(self):
        file_info = FileInfo(
            name="test.txt",
            path="/tmp/test.txt",
            size=1024,
        )
        result = repr(file_info)
        assert "FileInfo" in result
        assert "test.txt" in result
        assert "1024" in result

    def test_extension_for_file(self):
        file_info = FileInfo(name="test.txt", path="/tmp/test.txt")
        assert file_info.extension == ".txt"

    def test_extension_for_image(self):
        file_info = FileInfo(name="photo.jpg", path="/tmp/photo.jpg")
        assert file_info.extension == ".jpg"

    def test_extension_for_directory(self):
        dir_info = FileInfo(
            name="documents",
            path="/tmp/documents",
            is_dir=True,
        )
        assert dir_info.extension == ""

    def test_extension_for_file_without_extension(self):
        file_info = FileInfo(name="Makefile", path="/tmp/Makefile")
        assert file_info.extension == ""

    def test_display_size_bytes(self):
        file_info = FileInfo(name="small.txt", path="/tmp/small.txt", size=512)
        assert "512" in file_info.display_size

    def test_display_size_kb(self):
        file_info = FileInfo(name="medium.txt", path="/tmp/medium.txt", size=1024)
        assert "1.00 KB" in file_info.display_size

    def test_display_size_mb(self):
        file_info = FileInfo(name="large.txt", path="/tmp/large.txt", size=1024 * 1024)
        assert "1.00 MB" in file_info.display_size

    def test_display_time_with_valid_time(self):
        now = datetime(2024, 1, 15, 10, 30, 45)
        file_info = FileInfo(
            name="test.txt",
            path="/tmp/test.txt",
            modified_time=now,
        )
        assert file_info.display_time == "2024-01-15 10:30:45"

    def test_display_time_without_time(self):
        file_info = FileInfo(name="test.txt", path="/tmp/test.txt")
        assert file_info.display_time == ""

    def test_icon_type_for_directory(self):
        dir_info = FileInfo(
            name="documents",
            path="/tmp/documents",
            is_dir=True,
        )
        assert dir_info.icon_type == "folder"

    def test_icon_type_for_image(self):
        file_info = FileInfo(name="photo.jpg", path="/tmp/photo.jpg")
        assert file_info.icon_type == "image"

    def test_icon_type_for_video(self):
        file_info = FileInfo(name="video.mp4", path="/tmp/video.mp4")
        assert file_info.icon_type == "video"

    def test_icon_type_for_unknown_file(self):
        file_info = FileInfo(name="unknown.xyz", path="/tmp/unknown.xyz")
        assert file_info.icon_type == "file"
