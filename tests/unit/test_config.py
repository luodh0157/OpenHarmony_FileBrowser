"""
Unit tests for configuration (src/config.py).
"""

import pytest
import json
from pathlib import Path
from src.config import Config


class TestConfigDefaults:
    """Tests for Config default values."""

    def test_app_name(self):
        config = Config()
        assert config.app_name == "OpenHarmony File Browser"

    def test_app_version(self):
        config = Config()
        assert config.app_version == "1.0.0"

    def test_window_dimensions(self):
        config = Config()
        assert config.window_width == 1200
        assert config.window_height == 800

    def test_window_min_dimensions(self):
        config = Config()
        assert config.window_min_width == 800
        assert config.window_min_height == 600

    def test_log_level(self):
        config = Config()
        assert config.log_level == "INFO"

    def test_hdc_timeout(self):
        config = Config()
        assert config.hdc_timeout == 30

    def test_hdc_max_retries(self):
        config = Config()
        assert config.hdc_max_retries == 3

    def test_transfer_max_workers(self):
        config = Config()
        assert config.transfer_max_workers == 3

    def test_transfer_chunk_size(self):
        config = Config()
        assert config.transfer_chunk_size == 1024 * 1024

    def test_preview_max_size(self):
        config = Config()
        assert config.preview_max_size == 10 * 1024 * 1024

    def test_default_remote_path(self):
        config = Config()
        assert config.default_remote_path == "/"

    def test_show_upload_hint(self):
        config = Config()
        assert config.show_upload_hint is True

    def test_log_dir_initialized(self):
        config = Config()
        assert config.log_dir is not None
    
    def test_theme_and_language_initialized(self):
        config = Config()
        assert config.theme in ["light", "dark"]
        assert config.language in ["en", "zh"]


class TestConfigSaveLoad:
    """Tests for Config save and load functionality."""

    def test_save_and_load(self, tmp_path):
        config_path = tmp_path / "config.json"

        original = Config(
            window_width=1400,
            window_height=900,
            log_level="DEBUG",
            transfer_max_workers=5,
            preview_max_size=20 * 1024 * 1024,
            theme="dark",
            language="en",
        )
        original.save(config_path)

        loaded = Config.load(config_path)

        assert loaded.window_width == 1400
        assert loaded.window_height == 900
        assert loaded.log_level == "DEBUG"
        assert loaded.transfer_max_workers == 5
        assert loaded.preview_max_size == 20 * 1024 * 1024
        assert loaded.theme == "dark"
        assert loaded.language == "en"

    def test_load_nonexistent_file(self):
        config = Config.load(Path("/nonexistent/path/config.json"))
        assert isinstance(config, Config)
        assert config.app_name == "OpenHarmony File Browser"

    def test_save_creates_parent_directory(self, tmp_path):
        config_path = tmp_path / "subdir" / "config.json"
        config = Config()
        config.save(config_path)
        assert config_path.exists()

    def test_save_format_is_valid_json(self, tmp_path):
        config_path = tmp_path / "config.json"
        config = Config()
        config.save(config_path)

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "window_width" in data
        assert "window_height" in data
        assert "log_level" in data

    def test_load_partial_config(self, tmp_path):
        config_path = tmp_path / "config.json"
        partial_data = {"window_width": 1600}

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(partial_data, f)

        loaded = Config.load(config_path)
        assert loaded.window_width == 1600
