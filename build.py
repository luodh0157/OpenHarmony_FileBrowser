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
    
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    hdc_dir = project_root / "hdc"
    resources_dir = src_dir / "resources"
    
    platform_name = get_platform()
    
    params = [
        str(src_dir / "main.py"),
        f"--name=OpenHarmonyFileBrowser",
        "--windowed",
        "--onedir",
        f"--add-data={hdc_dir}:hdc",
        f"--add-data={resources_dir}:resources",
        "--clean",
        "--noconfirm",
        f"--distpath={project_root / 'dist'}",
        f"--workpath={project_root / 'build'}",
        f"--specpath={project_root}",
    ]
    
    if platform_name == "windows":
        params.append("--icon=src/resources/icons/app.ico")
    elif platform_name == "macos":
        params.append("--icon=src/resources/icons/app.icns")
    
    print(f"Build parameters: {params}")
    
    try:
        PyInstaller.__main__.run(params)
        print("\n✓ Build completed successfully!")
        print(f"Output directory: {project_root / 'dist' / 'OpenHarmonyFileBrowser'}")
    except Exception as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build()