"""
Build script for OpenHarmony File Browser.
Creates standalone executable with PyInstaller.
"""

import PyInstaller.__main__
import platform
import sys
from pathlib import Path


def get_platform():
    """Get current platform."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    return system


def build():
    """Build application with PyInstaller."""
    print("Building OpenHarmony File Browser...")
    
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    hdc_dir = project_root / "hdc"
    resources_dir = project_root / "resources"
    assets_dir = project_root / "assets"
    config_dir = project_root / "config"
    
    # 确保只打包 config.json，不打包 logs 等运行时目录
    config_json = config_dir / "config.json"
    if not config_json.exists():
        print(f"Warning: {config_json} not found, creating default config")
        config_json.parent.mkdir(parents=True, exist_ok=True)
        import json
        default_config = {
            "app_name": "OpenHarmony File Browser",
            "window_width": 1200,
            "window_height": 800,
            "log_level": "INFO",
            "theme": "light",
            "language": "zh",
        }
        with open(config_json, 'w') as f:
            json.dump(default_config, f, indent=2)
    
    platform_name = get_platform()
    
    params = [
        str(project_root / "main.py"),
        f"--name=OpenHarmonyFileBrowser",
        "--windowed",
        "--onedir",
        "--optimize=1",
        f"--add-data={hdc_dir}:hdc",
        f"--add-data={resources_dir}:resources",
        f"--add-data={config_json}:config",  # 只打包 config.json，不打包 logs
        "--clean",
        "--noconfirm",
        f"--distpath={project_root / 'dist'}",
        f"--workpath={project_root / 'build'}",
        f"--specpath={project_root}",
    ]
    
    icon_path = None
    if platform_name == "windows":
        icon_path = assets_dir / "icons" / "app.ico"
    elif platform_name == "macos":
        icon_path = assets_dir / "icons" / "app.icns"
    elif platform_name == "linux":
        icon_path = assets_dir / "icons" / "app.png"

    if icon_path and icon_path.exists():
        params.append(f"--icon={icon_path}")
        print(f"Using icon: {icon_path}")
    else:
        print(f"Warning: Icon not found at {icon_path}, building without icon")
        print(f"Run 'python generate_icon.py' to generate icons")
    
    print(f"Build parameters: {params}")
    
    try:
        PyInstaller.__main__.run(params)
        print("\n[OK] Build completed successfully!")
        print(f"Output directory: {project_root / 'dist' / 'OpenHarmonyFileBrowser'}")
    except Exception as e:
        print(f"\n[FAIL] Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build()