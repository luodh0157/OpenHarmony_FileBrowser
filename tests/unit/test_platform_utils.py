"""
Unit tests for platform utilities (src/utils/platform_utils.py).
"""

import pytest
import platform
from src.utils.platform_utils import (
    get_platform,
    get_architecture,
    get_hdc_executable,
    get_platform_info,
)


class TestGetPlatform:
    """Tests for get_platform function."""

    def test_returns_valid_platform(self):
        result = get_platform()
        assert result in ["Windows", "Linux", "Darwin"]

    def test_matches_system_call(self):
        result = get_platform()
        assert result == platform.system()


class TestGetArchitecture:
    """Tests for get_architecture function."""

    def test_returns_valid_architecture(self):
        result = get_architecture()
        assert result in ["x64", "arm64"]

    def test_x86_64_maps_to_x64(self, monkeypatch):
        monkeypatch.setattr(platform, "machine", lambda: "x86_64")
        assert get_architecture() == "x64"

    def test_amd64_maps_to_x64(self, monkeypatch):
        monkeypatch.setattr(platform, "machine", lambda: "amd64")
        assert get_architecture() == "x64"

    def test_arm64_maps_to_arm64(self, monkeypatch):
        monkeypatch.setattr(platform, "machine", lambda: "arm64")
        assert get_architecture() == "arm64"

    def test_aarch64_maps_to_arm64(self, monkeypatch):
        monkeypatch.setattr(platform, "machine", lambda: "aarch64")
        assert get_architecture() == "arm64"

    def test_unknown_maps_to_x64(self, monkeypatch):
        monkeypatch.setattr(platform, "machine", lambda: "unknown")
        assert get_architecture() == "x64"


class TestGetHdcExecutable:
    """Tests for get_hdc_executable function."""

    def test_raises_error_when_hdc_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError) as exc_info:
            get_hdc_executable(hdc_dir=tmp_path)
        assert "HDC tool not found" in str(exc_info.value)

    def test_includes_platform_in_error_message(self, tmp_path):
        with pytest.raises(FileNotFoundError) as exc_info:
            get_hdc_executable(hdc_dir=tmp_path)
        assert get_platform() in str(exc_info.value)

    def test_includes_architecture_in_error_message(self, tmp_path):
        with pytest.raises(FileNotFoundError) as exc_info:
            get_hdc_executable(hdc_dir=tmp_path)
        assert get_architecture() in str(exc_info.value)

    def test_finds_hdc_when_present(self, tmp_path, monkeypatch):
        plat = get_platform()
        arch = get_architecture()
        hdc_dir = tmp_path / plat / arch
        hdc_dir.mkdir(parents=True)

        if plat == "Windows":
            hdc_file = hdc_dir / "hdc.exe"
        else:
            hdc_file = hdc_dir / "hdc"
        hdc_file.touch()

        result = get_hdc_executable(hdc_dir=tmp_path)
        assert result == hdc_file


class TestGetPlatformInfo:
    """Tests for get_platform_info function."""

    def test_returns_dict(self):
        result = get_platform_info()
        assert isinstance(result, dict)

    def test_contains_required_keys(self):
        result = get_platform_info()
        required_keys = [
            "system", "node", "release", "version",
            "machine", "processor", "python_version",
            "platform", "architecture",
        ]
        for key in required_keys:
            assert key in result

    def test_platform_matches_get_platform(self):
        result = get_platform_info()
        assert result["platform"] == get_platform()

    def test_architecture_matches_get_architecture(self):
        result = get_platform_info()
        assert result["architecture"] == get_architecture()
