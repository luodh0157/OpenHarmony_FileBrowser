"""
Configuration module for OpenHarmony File Browser.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json

from src.utils.resource_utils import get_resource_path, get_user_data_dir


@dataclass
class Config:
    """Application configuration."""

    app_name: str = "OpenHarmony File Browser"
    app_version: str = "1.0.0"

    window_width: int = 1200
    window_height: int = 800
    window_min_width: int = 800
    window_min_height: int = 600

    log_level: str = "INFO"
    log_dir: Optional[Path] = None

    hdc_timeout: int = 30
    hdc_max_retries: int = 3

    transfer_max_workers: int = 3
    transfer_chunk_size: int = 1024 * 1024

    preview_max_size: int = 10 * 1024 * 1024

    default_remote_path: str = "/"

    show_upload_hint: bool = True

    theme: str = "light"
    language: str = "zh"

    def __post_init__(self):
        """Initialize default paths."""
        if self.log_dir is None:
            self.log_dir = get_user_data_dir() / "logs"

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """
        Load configuration from file.

        Args:
            config_path: Path to config file

        Returns:
            Config instance
        """
        if config_path is None:
            config_path = get_user_data_dir() / "config.json"
            if not config_path.exists():
                config_path = get_resource_path("config") / "config.json"

        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            known_fields = {f.name for f in cls.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in known_fields}
            return cls(**filtered)

        return cls()

    def save(self, config_path: Optional[Path] = None) -> None:
        """
        Save configuration to file.

        Args:
            config_path: Path to config file
        """
        if config_path is None:
            config_path = get_user_data_dir() / "config.json"

        data = {
            "window_width": self.window_width,
            "window_height": self.window_height,
            "log_level": self.log_level,
            "transfer_max_workers": self.transfer_max_workers,
            "preview_max_size": self.preview_max_size,
            "theme": self.theme,
            "language": self.language,
        }

        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


config = Config.load()
