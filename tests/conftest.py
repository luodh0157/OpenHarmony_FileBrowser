"""
Pytest configuration and shared fixtures for OpenHarmony File Browser tests.
"""

import sys
import os
from pathlib import Path

import pytest

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def src_dir():
    """Return the src directory."""
    return PROJECT_ROOT / "src"


@pytest.fixture(scope="session")
def resources_dir():
    """Return the resources directory."""
    return PROJECT_ROOT / "src" / "resources"


@pytest.fixture
def sample_device_info():
    """Return sample device info data."""
    return {
        "device_id": "192.168.1.100:5555",
        "model": "HUAWEI Mate 60",
        "brand": "HUAWEI",
        "product": "OHB-AN00",
        "is_wireless": True,
    }


@pytest.fixture
def sample_file_info():
    """Return sample file info data."""
    return {
        "name": "test.txt",
        "path": "/data/local/tmp/test.txt",
        "is_dir": False,
        "size": 1024,
        "permissions": "-rw-r--r--",
        "owner": "root",
        "group": "root",
    }


@pytest.fixture
def sample_directory_info():
    """Return sample directory info data."""
    return {
        "name": "documents",
        "path": "/data/local/tmp/documents",
        "is_dir": True,
        "size": 0,
        "permissions": "drwxr-xr-x",
        "owner": "root",
        "group": "root",
    }


@pytest.fixture
def mock_hdc_path(tmp_path):
    """Create a mock HDC executable for testing."""
    hdc_file = tmp_path / "hdc"
    hdc_file.touch()
    os.chmod(hdc_file, 0o755)
    return str(hdc_file)


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_i18n_dir(tmp_path):
    """Create a mock i18n directory with translation files."""
    i18n_dir = tmp_path / "i18n"
    i18n_dir.mkdir()

    en_translations = {
        "toolbar": {
            "refresh": "Refresh",
            "refresh_devices": "Refresh Devices",
            "upload": "Upload",
            "download": "Download",
            "new_folder": "New Folder",
            "delete": "Delete",
            "rename": "Rename",
        },
        "menu": {
            "file": "File",
            "view": "View",
            "help": "Help",
            "theme": "Theme",
            "language": "Language",
        },
        "dialogs": {
            "create_folder": "Create Folder",
            "rename": "Rename",
            "delete_confirm": "Are you sure you want to delete {count} item(s)?",
            "folder_name": "Folder name",
            "new_name": "New name",
        },
        "status": {
            "ready": "Ready",
            "loading": "Loading...",
            "transferring": "Transferring {current}/{total}",
        },
    }

    zh_translations = {
        "toolbar": {
            "refresh": "刷新",
            "refresh_devices": "刷新设备",
            "upload": "上传",
            "download": "下载",
            "new_folder": "新建文件夹",
            "delete": "删除",
            "rename": "重命名",
        },
        "menu": {
            "file": "文件",
            "view": "视图",
            "help": "帮助",
            "theme": "主题",
            "language": "语言",
        },
        "dialogs": {
            "create_folder": "新建文件夹",
            "rename": "重命名",
            "delete_confirm": "确定要删除 {count} 个项目吗？",
            "folder_name": "文件夹名称",
            "new_name": "新名称",
        },
        "status": {
            "ready": "就绪",
            "loading": "加载中...",
            "transferring": "传输中 {current}/{total}",
        },
    }

    import json

    with open(i18n_dir / "en.json", "w", encoding="utf-8") as f:
        json.dump(en_translations, f, indent=2, ensure_ascii=False)

    with open(i18n_dir / "zh.json", "w", encoding="utf-8") as f:
        json.dump(zh_translations, f, indent=2, ensure_ascii=False)

    return i18n_dir


@pytest.fixture
def mock_icons_dir(tmp_path):
    """Create a mock icons directory with SVG files."""
    icons_dir = tmp_path / "icons"
    light_dir = icons_dir / "light"
    dark_dir = icons_dir / "dark"
    light_dir.mkdir(parents=True)
    dark_dir.mkdir(parents=True)

    icon_names = [
        "folder",
        "file",
        "image",
        "video",
        "music",
        "document",
        "archive",
        "code",
        "refresh",
        "refresh_devices",
        "upload",
        "download",
        "delete",
        "rename",
        "new_folder",
        "sun",
        "moon",
        "arrow_down",
    ]

    for name in icon_names:
        svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M0 0h24v24H0z"/></svg>'
        (light_dir / f"{name}.svg").write_text(svg_content)
        (dark_dir / f"{name}.svg").write_text(svg_content)

    return icons_dir
