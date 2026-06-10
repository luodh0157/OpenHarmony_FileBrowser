"""
Main entry point for OpenHarmony File Browser.
"""

import sys
import argparse
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from .config import config
from .utils.logger import get_logger, set_log_level
from .utils.platform_utils import get_platform_info


logger = get_logger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="OpenHarmony File Browser - A cross-platform file browser for OpenHarmony/HarmonyOS devices"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"OpenHarmony File Browser {config.app_version}",
    )
    
    return parser.parse_args()


def check_dependencies():
    """Check if all dependencies are available."""
    try:
        from PySide6.QtWidgets import QApplication
        logger.debug("PySide6 is available")
    except ImportError as e:
        print(f"Error: PySide6 is not installed: {e}")
        print("Please install it with: pip install PySide6")
        return False
    
    try:
        from PIL import Image
        logger.debug("Pillow is available")
    except ImportError as e:
        print(f"Error: Pillow is not installed: {e}")
        print("Please install it with: pip install Pillow")
        return False
    
    return True


def check_hdc():
    """Check if HDC tool is available."""
    try:
        from .utils.platform_utils import get_hdc_executable
        hdc_path = get_hdc_executable()
        logger.info(f"HDC tool found: {hdc_path}")
        return True
    except FileNotFoundError as e:
        logger.warning(f"HDC tool not found: {e}")
        return False


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.debug:
        import logging
        set_log_level(logger, logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    logger.info(f"Starting {config.app_name} v{config.app_version}")
    logger.debug(f"Platform info: {get_platform_info()}")
    
    if not check_dependencies():
        sys.exit(1)
    
    hdc_available = check_hdc()
    if not hdc_available:
        logger.warning(
            "HDC tool not found. Please ensure HDC tool is placed in the correct directory."
        )
    
    try:
        app = QApplication(sys.argv)
        app.setApplicationName(config.app_name)
        app.setApplicationVersion(config.app_version)
        app.setOrganizationName("OpenHarmony")
        
        from .gui.main_window import MainWindow
        
        window = MainWindow()
        window.show()
        
        logger.info("Application started successfully")
        logger.info(f"Phase 2 GUI initialized")
        
        if hdc_available:
            logger.info("HDC tool available, device monitoring active")
        else:
            logger.warning("HDC tool not available, device features limited")
        
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()