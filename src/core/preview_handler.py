"""
Preview handler for OpenHarmony File Browser.
Handles file preview operations (images and videos).
"""

import os
import subprocess
import platform
import tempfile
from typing import Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from PIL import Image

from src.core.hdc_wrapper import HDCWrapper, HDCError
from src.utils.file_utils import is_image_file, is_video_file
from src.utils.logger import get_logger
from src.config import config

logger = get_logger(__name__)


class PreviewHandler:
    """
    Preview handler for managing file previews.

    Features:
    - Download file to system temp directory for preview
    - Image preview (using Pillow)
    - Video preview thumbnail extraction (placeholder)
    - Call system video player
    - Temp file cleanup (auto-managed by OS)
    """

    def __init__(self, hdc: HDCWrapper, device_id: str):
        """
        Initialize preview handler.

        Args:
            hdc: HDC wrapper instance
            device_id: Device ID
        """
        self.hdc = hdc
        self.device_id = device_id

        self.max_preview_size = config.preview_max_size

        logger.info("Preview handler initialized (using system temp directory)")

    def can_preview(self, file_name: str, file_size: int) -> bool:
        """
        Check if file can be previewed.

        Args:
            file_name: File name
            file_size: File size in bytes

        Returns:
            True if previewable
        """
        if not is_image_file(file_name) and not is_video_file(file_name):
            return False

        if file_size > self.max_preview_size:
            logger.warning(
                f"File too large for preview: {file_size} > {self.max_preview_size}"
            )
            return False

        return True

    def is_image(self, file_name: str) -> bool:
        """
        Check if file is an image.

        Args:
            file_name: File name

        Returns:
            True if image
        """
        return is_image_file(file_name)

    def is_video(self, file_name: str) -> bool:
        """
        Check if file is a video.

        Args:
            file_name: File name

        Returns:
            True if video
        """
        return is_video_file(file_name)

    def download_for_preview(self, remote_path: str) -> Optional[str]:
        """
        Download file from device for preview.
        Uses system temp directory (auto-managed by OS).

        Args:
            remote_path: Remote file path

        Returns:
            Local temp file path or None
        """
        file_name = Path(remote_path).name

        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file_name).suffix, prefix="preview_"
        )
        temp_file.close()

        try:
            logger.info(f"Downloading file for preview: {remote_path}")

            self.hdc.file_recv(self.device_id, remote_path, temp_file.name)

            logger.info(f"File downloaded to temp: {temp_file.name}")

            return temp_file.name

        except HDCError as e:
            logger.error(f"Failed to download file: {e}")
            Path(temp_file.name).unlink(missing_ok=True)
            return None

    def open_image(self, local_path: str) -> Optional["Image.Image"]:
        """
        Open image file for preview.

        Args:
            local_path: Local image file path

        Returns:
            PIL Image object or None
        """
        try:
            from PIL import Image

            logger.debug(f"Opening image: {local_path}")

            image = Image.open(local_path)

            logger.debug(f"Image opened: {image.size}")

            return image

        except Exception as e:
            logger.error(f"Failed to open image: {e}")
            return None

    def open_video_with_system_player(self, local_path: str) -> bool:
        """
        Open video file with system default player.

        Args:
            local_path: Local video file path

        Returns:
            True if successful
        """
        try:
            system = platform.system()

            logger.info(f"Opening video with system player: {local_path}")

            if system == "Windows":
                os.startfile(local_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", local_path], check=False)
            else:  # Linux
                subprocess.run(["xdg-open", local_path], check=False)

            logger.info("Video opened successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to open video: {e}")
            return False

    def cleanup_temp_file(self, local_path: str):
        """
        Clean up temporary file.

        Args:
            local_path: Local temp file path
        """
        try:
            file_path = Path(local_path)

            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Temp file cleaned up: {local_path}")

        except Exception as e:
            logger.warning(f"Failed to cleanup temp file: {e}")

    def cleanup(self):
        """Cleanup resources."""
        logger.info("Preview handler cleanup completed")
