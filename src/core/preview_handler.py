"""
Preview handler for OpenHarmony File Browser.
Handles file preview operations (images and videos).
"""

import os
import subprocess
import platform
from typing import Optional
from pathlib import Path

from src.core.hdc_wrapper import HDCWrapper, HDCError
from src.utils.file_utils import is_image_file, is_video_file
from src.utils.logger import get_logger
from src.config import config


logger = get_logger(__name__)


class PreviewHandler:
    """
    Preview handler for managing file previews.
    
    Features:
    - Download file to temp directory for preview
    - Image preview (using Pillow)
    - Video preview thumbnail extraction (placeholder)
    - Call system video player
    - Temp file cleanup
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
        
        self.temp_dir = config.preview_temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_preview_size = config.preview_max_size
        
        logger.info(f"Preview handler initialized (temp_dir={self.temp_dir})")
    
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
            logger.warning(f"File too large for preview: {file_size} > {self.max_preview_size}")
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
        
        Args:
            remote_path: Remote file path
        
        Returns:
            Local temp file path or None
        """
        file_name = Path(remote_path).name
        
        local_temp_path = self.temp_dir / file_name
        
        try:
            logger.info(f"Downloading file for preview: {remote_path}")
            
            self.hdc.file_recv(self.device_id, remote_path, str(local_temp_path))
            
            logger.info(f"File downloaded to: {local_temp_path}")
            
            return str(local_temp_path)
        
        except HDCError as e:
            logger.error(f"Failed to download file: {e}")
            return None
    
    def open_image(self, local_path: str) -> Optional[bytes]:
        """
        Open image file for preview.
        
        Args:
            local_path: Local image file path
        
        Returns:
            Image data or None
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
                subprocess.run(["open", local_path], check=False, creationflags=subprocess.CREATE_NO_WINDOW if system == "Windows" else 0)
            else:  # Linux
                subprocess.run(["xdg-open", local_path], check=False)
            
            logger.info(f"Video opened successfully")
            
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
            
            if file_path.exists() and file_path.parent == self.temp_dir:
                file_path.unlink()
                
                logger.debug(f"Temp file cleaned up: {local_path}")
        
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file: {e}")
    
    def cleanup_all_temp_files(self):
        """Clean up all temporary files."""
        try:
            for file in self.temp_dir.iterdir():
                if file.is_file():
                    file.unlink()
            
            logger.info("All temp files cleaned up")
        
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")
    
    def cleanup(self):
        """Cleanup resources (alias for cleanup_all_temp_files)."""
        self.cleanup_all_temp_files()