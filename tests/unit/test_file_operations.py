"""
Unit tests for file operations (src/core/file_operations.py).
"""

import pytest
from src.core.file_operations import FileOperations


class TestFileOperationsPathMethods:
    """Tests for FileOperations path manipulation methods."""

    def test_join_path_root_base(self):
        result = FileOperations.join_path(None, "/", "test")
        assert result == "/test"

    def test_join_path_subdirectory(self):
        result = FileOperations.join_path(None, "/data", "test")
        assert result == "/data/test"

    def test_join_path_trailing_slash(self):
        result = FileOperations.join_path(None, "/data/", "test")
        assert result == "/data/test"

    def test_get_parent_directory_root(self):
        result = FileOperations.get_parent_directory(None, "/")
        assert result == "/"

    def test_get_parent_directory_empty(self):
        result = FileOperations.get_parent_directory(None, "")
        assert result == "/"

    def test_get_parent_directory_single_level(self):
        result = FileOperations.get_parent_directory(None, "/file.txt")
        assert result == "/"

    def test_get_parent_directory_nested(self):
        result = FileOperations.get_parent_directory(None, "/data/local/tmp")
        assert result == "/data/local"

    def test_get_parent_directory_deep(self):
        result = FileOperations.get_parent_directory(
            None, "/storage/media/100/local/files/Photo/16/LICENSE"
        )
        assert result == "/storage/media/100/local/files/Photo/16"

    def test_normalize_path_empty(self):
        result = FileOperations.normalize_path(None, "")
        assert result == "/"

    def test_normalize_path_no_leading_slash(self):
        result = FileOperations.normalize_path(None, "data/local/tmp")
        assert result == "/data/local/tmp"

    def test_normalize_path_with_dot(self):
        result = FileOperations.normalize_path(None, "/storage/./test.txt")
        assert result == "/storage/test.txt"

    def test_normalize_path_with_dotdot(self):
        result = FileOperations.normalize_path(None, "/storage/media/../test.txt")
        assert result == "/storage/test.txt"

    def test_normalize_path_backslash_to_slash(self):
        result = FileOperations.normalize_path(None, "\\storage\\media\\100\\LICENSE")
        assert result == "/storage/media/100/LICENSE"
        assert "\\" not in result

    def test_normalize_path_complex(self):
        result = FileOperations.normalize_path(None, "/data/../tmp/./test.txt")
        assert result == "/tmp/test.txt"

    def test_validate_path_valid(self):
        result = FileOperations.validate_path(None, "/data/local/tmp")
        assert result is True

    def test_validate_path_no_leading_slash(self):
        result = FileOperations.validate_path(None, "data/local/tmp")
        assert result is False

    def test_validate_path_empty(self):
        result = FileOperations.validate_path(None, "")
        assert result is False

    def test_validate_path_none(self):
        result = FileOperations.validate_path(None, None)
        assert result is False


class TestFileOperationsWithMockHdc:
    """Tests for FileOperations with a mock HDC wrapper."""

    @pytest.fixture
    def mock_hdc(self):
        """Create a mock HDC wrapper."""
        class MockHdc:
            def shell_ls(self, device_id, path, show_hidden=False):
                return []

            def shell_stat(self, device_id, path):
                from src.models.file_info import FileInfo, FileType
                return FileInfo(
                    name="test",
                    path=path,
                    is_dir=True,
                    file_type=FileType.DIRECTORY,
                )

            def shell_mkdir(self, device_id, path):
                pass

            def shell_rm(self, device_id, path, recursive=False):
                pass

            def shell_mv(self, device_id, old_path, new_path):
                pass

        return MockHdc()

    def test_init(self, mock_hdc):
        ops = FileOperations(mock_hdc, "test_device")
        assert ops.device_id == "test_device"
        assert ops.hdc == mock_hdc

    def test_list_directory(self, mock_hdc):
        ops = FileOperations(mock_hdc, "test_device")
        result = ops.list_directory("/data/local/tmp")
        assert isinstance(result, list)

    def test_get_file_info(self, mock_hdc):
        ops = FileOperations(mock_hdc, "test_device")
        result = ops.get_file_info("/data/local/tmp")
        assert result.path == "/data/local/tmp"

    def test_create_directory(self, mock_hdc):
        ops = FileOperations(mock_hdc, "test_device")
        result = ops.create_directory("/data/local/tmp/new_folder")
        assert result is True

    def test_delete_file(self, mock_hdc):
        ops = FileOperations(mock_hdc, "test_device")
        result = ops.delete_file("/data/local/tmp/test.txt")
        assert result is True

    def test_rename_file(self, mock_hdc):
        ops = FileOperations(mock_hdc, "test_device")
        result = ops.rename_file("/data/local/tmp/old.txt", "/data/local/tmp/new.txt")
        assert result is True

    def test_exists_true(self, mock_hdc):
        ops = FileOperations(mock_hdc, "test_device")
        result = ops.exists("/data/local/tmp")
        assert result is True

    def test_is_directory_true(self, mock_hdc):
        ops = FileOperations(mock_hdc, "test_device")
        result = ops.is_directory("/data/local/tmp")
        assert result is True
