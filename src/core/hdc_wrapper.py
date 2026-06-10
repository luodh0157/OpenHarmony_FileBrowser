"""
HDC (HarmonyOS Device Connector) wrapper for OpenHarmony File Browser.
Provides interface to communicate with OpenHarmony/HarmonyOS devices.
"""

import subprocess
import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

from ..models.device import DeviceInfo, DeviceStatus
from ..models.file_info import FileInfo, FileType
from ..utils.logger import get_logger


logger = get_logger(__name__)


class HDCError(Exception):
    """HDC command execution error."""
    pass


class HDCWrapper:
    """
    Wrapper for HDC (HarmonyOS Device Connector) commands.
    
    This class provides a Python interface to interact with OpenHarmony/HarmonyOS
    devices using the HDC command-line tool.
    """
    
    def __init__(self, hdc_path: Optional[str] = None, timeout: int = 30):
        """
        Initialize HDC wrapper.
        
        Args:
            hdc_path: Path to HDC executable. If None, will auto-detect.
            timeout: Default command timeout in seconds.
        """
        if hdc_path is None:
            from ..utils.platform_utils import get_hdc_executable
            hdc_path = str(get_hdc_executable())
        
        self.hdc_path = hdc_path
        self.timeout = timeout
        self._verify_hdc()
        
        logger.info(f"HDC wrapper initialized: {self.hdc_path}")
    
    def _verify_hdc(self) -> None:
        """Verify HDC tool is accessible."""
        hdc_file = Path(self.hdc_path)
        if not hdc_file.exists():
            raise HDCError(f"HDC tool not found: {self.hdc_path}")
        
        if not hdc_file.is_file():
            raise HDCError(f"HDC path is not a file: {self.hdc_path}")
        
        try:
            result = self._execute(["--version"], check=False)
            logger.debug(f"HDC version: {result}")
        except Exception as e:
            raise HDCError(f"Failed to execute HDC: {e}")
    
    def _execute(
        self,
        args: List[str],
        device_id: Optional[str] = None,
        timeout: Optional[int] = None,
        check: bool = True,
    ) -> str:
        """
        Execute HDC command.
        
        Args:
            args: Command arguments
            device_id: Device ID (serial number or IP:PORT)
            timeout: Command timeout in seconds
            check: Whether to check return code
        
        Returns:
            Command stdout
        
        Raises:
            HDCError: If command fails
        """
        cmd = [self.hdc_path]
        
        if device_id:
            cmd.extend(["-t", device_id])
        
        cmd.extend(args)
        
        logger.debug(f"Executing HDC command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
            )
            
            if check and result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                raise HDCError(f"HDC command failed: {error_msg}")
            
            return result.stdout.strip()
        
        except subprocess.TimeoutExpired:
            raise HDCError(f"HDC command timeout after {timeout or self.timeout}s")
        except Exception as e:
            if isinstance(e, HDCError):
                raise
            raise HDCError(f"Failed to execute HDC command: {e}")
    
    def list_targets(self) -> List[DeviceInfo]:
        """
        List all connected devices.
        
        Returns:
            List of device information
        """
        logger.info("Listing connected devices")
        
        output = self._execute(["list", "targets"])
        
        devices = []
        
        for line in output.split("\n"):
            line = line.strip()
            if not line or line.startswith("[Empty]"):
                continue
            
            device_id = line
            is_wireless = ":" in device_id
            
            device = DeviceInfo(
                device_id=device_id,
                status=DeviceStatus.CONNECTED,
                is_wireless=is_wireless,
            )
            
            devices.append(device)
        
        logger.info(f"Found {len(devices)} devices")
        return devices
    
    def get_device_info(self, device_id: str) -> DeviceInfo:
        """
        Get detailed device information.
        
        Args:
            device_id: Device ID
        
        Returns:
            Device information
        """
        logger.info(f"Getting device info: {device_id}")
        
        is_wireless = ":" in device_id
        device = DeviceInfo(
            device_id=device_id,
            status=DeviceStatus.CONNECTED,
            is_wireless=is_wireless,
        )
        
        try:
            model = self._execute(
                ["shell", "param", "get", "const.product.model"],
                device_id=device_id,
                check=False
            )
            if model:
                device.model = model.strip()
            
            brand = self._execute(
                ["shell", "param", "get", "const.product.brand"],
                device_id=device_id,
                check=False
            )
            if brand:
                device.brand = brand.strip()
            
            product = self._execute(
                ["shell", "param", "get", "const.product.name"],
                device_id=device_id,
                check=False
            )
            if product:
                device.product = product.strip()
            
        except Exception as e:
            logger.warning(f"Failed to get device details: {e}")
        
        return device
    
    def shell_ls(
        self, device_id: str, path: str, show_hidden: bool = False
    ) -> List[FileInfo]:
        """
        List files in a directory.
        
        Args:
            device_id: Device ID
            path: Directory path
            show_hidden: Whether to show hidden files
        
        Returns:
            List of file information
        """
        logger.debug(f"Listing files: {device_id}:{path}")
        
        args = ["shell", "ls", "-l"]
        if show_hidden:
            args.append("-a")
        args.append(path)
        
        output = self._execute(args, device_id=device_id)
        
        files = []
        
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue
            
            file_info = self._parse_ls_line(line, path)
            if file_info:
                files.append(file_info)
        
        logger.debug(f"Found {len(files)} items in {path}")
        return files
    
    def _parse_ls_line(self, line: str, parent_path: str) -> Optional[FileInfo]:
        """
        Parse ls -l output line.
        
        Format: drwxr-xr-x 2 root root 4096 2024-01-01 12:00 folder_name
        or: -rw-r--r-- 1 root root 1234 2024-01-01 12:00 file_name
        
        Args:
            line: ls -l output line
            parent_path: Parent directory path
        
        Returns:
            FileInfo or None
        """
        parts = line.split(None, 7)
        
        if len(parts) < 8:
            return None
        
        permissions = parts[0]
        links = int(parts[1])
        owner = parts[2]
        group = parts[3]
        
        size_str = parts[4]
        try:
            size = int(size_str)
        except ValueError:
            size = 0
        
        date_str = f"{parts[5]} {parts[6]}"
        try:
            modified_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            modified_time = None
        
        name = parts[7]
        
        is_dir = permissions.startswith("d")
        file_type = FileType.DIRECTORY if is_dir else FileType.FILE
        
        if permissions.startswith("l"):
            file_type = FileType.SYMLINK
        
        full_path = f"{parent_path.rstrip('/')}/{name}"
        
        return FileInfo(
            name=name,
            path=full_path,
            is_dir=is_dir,
            size=size,
            permissions=permissions,
            modified_time=modified_time,
            file_type=file_type,
            owner=owner,
            group=group,
            links=links,
        )
    
    def shell_stat(self, device_id: str, path: str) -> FileInfo:
        """
        Get file/directory information.
        
        Args:
            device_id: Device ID
            path: File path
        
        Returns:
            File information
        
        Note:
            This method parses stat output. The actual HDC stat output format
            may vary, so this implementation may need adjustment based on
            real device testing.
        """
        logger.debug(f"Getting file info: {device_id}:{path}")
        
        output = self._execute(
            ["shell", "stat", path],
            device_id=device_id
        )
        
        return self._parse_stat_output(output, path)
    
    def _parse_stat_output(self, output: str, path: str) -> FileInfo:
        """
        Parse stat command output.
        
        Args:
            output: stat command output
            path: File path
        
        Returns:
            FileInfo object
        """
        import os
        
        name = os.path.basename(path)
        
        size = 0
        permissions = ""
        modified_time = None
        is_dir = False
        owner = None
        group = None
        links = 1
        
        for line in output.split("\n"):
            line = line.strip()
            
            if line.startswith("Size:"):
                try:
                    size = int(line.split(":")[1].split()[0])
                except (IndexError, ValueError):
                    pass
            
            elif line.startswith("Access:") and "(" in line:
                parts = line.split("(")
                if len(parts) >= 2:
                    perm_part = parts[1].split("/")
                    if len(perm_part) >= 2:
                        permissions = perm_part[1].rstrip(")")
                        is_dir = permissions.startswith("d")
            
            elif "directory" in line.lower():
                is_dir = True
                if not permissions:
                    permissions = "drwxr-xr-x"
            
            elif "regular file" in line.lower():
                is_dir = False
                if not permissions:
                    permissions = "-rw-r--r--"
            
            elif line.startswith("Uid:"):
                try:
                    uid_parts = line.split("(")
                    if len(uid_parts) >= 2:
                        owner = uid_parts[1].split("/")[1].rstrip(")")
                except IndexError:
                    pass
            
            elif line.startswith("Gid:"):
                try:
                    gid_parts = line.split("(")
                    if len(gid_parts) >= 2:
                        group = gid_parts[1].split("/")[1].rstrip(")")
                except IndexError:
                    pass
            
            elif line.startswith("Links:"):
                try:
                    links = int(line.split(":")[1].strip())
                except (IndexError, ValueError):
                    pass
            
            elif line.startswith("Modify:"):
                try:
                    time_str = line.split(":")[1].strip()
                    modified_time = datetime.strptime(
                        time_str, "%Y-%m-%d %H:%M:%S"
                    )
                except (IndexError, ValueError):
                    pass
        
        file_type = FileType.DIRECTORY if is_dir else FileType.FILE
        
        return FileInfo(
            name=name,
            path=path,
            is_dir=is_dir,
            size=size,
            permissions=permissions,
            modified_time=modified_time,
            file_type=file_type,
            owner=owner,
            group=group,
            links=links,
        )
    
    def shell_mkdir(self, device_id: str, path: str) -> None:
        """
        Create directory.
        
        Args:
            device_id: Device ID
            path: Directory path to create
        """
        logger.info(f"Creating directory: {device_id}:{path}")
        
        self._execute(
            ["shell", "mkdir", "-p", path],
            device_id=device_id
        )
        
        logger.info(f"Directory created: {path}")
    
    def shell_rm(
        self, device_id: str, path: str, recursive: bool = False, force: bool = False
    ) -> None:
        """
        Remove file or directory.
        
        Args:
            device_id: Device ID
            path: Path to remove
            recursive: Remove recursively (for directories)
            force: Force removal
        """
        logger.info(f"Removing: {device_id}:{path}")
        
        args = ["shell", "rm"]
        
        if recursive:
            args.append("-r")
        if force:
            args.append("-f")
        
        args.append(path)
        
        self._execute(args, device_id=device_id)
        
        logger.info(f"Removed: {path}")
    
    def shell_mv(self, device_id: str, src: str, dst: str) -> None:
        """
        Move or rename file/directory.
        
        Args:
            device_id: Device ID
            src: Source path
            dst: Destination path
        """
        logger.info(f"Moving: {device_id}:{src} -> {dst}")
        
        self._execute(
            ["shell", "mv", src, dst],
            device_id=device_id
        )
        
        logger.info(f"Moved: {src} -> {dst}")
    
    def file_send(
        self, device_id: str, local_path: str, remote_path: str,
        preserve_timestamp: bool = True
    ) -> None:
        """
        Send file or directory to device.
        
        Args:
            device_id: Device ID
            local_path: Local file path
            remote_path: Remote file path
            preserve_timestamp: Whether to preserve file timestamp (default True)
        """
        logger.info(f"Sending: {local_path} -> {device_id}:{remote_path}")
        
        import os
        import platform
        
        if platform.system() == "Windows":
            local_path = os.path.normpath(local_path)
            logger.debug(f"Normalized Windows path: {local_path}")
        
        from pathlib import Path
        local_path_obj = Path(local_path)
        if not local_path_obj.exists():
            raise HDCError(f"Local path not found: {local_path}")
        
        if local_path_obj.is_file():
            logger.debug(f"Local file size: {local_path_obj.stat().st_size} bytes")
        
        cmd = ["file", "send"]
        if preserve_timestamp:
            cmd.append("-a")
            logger.info("Using HDC -a option to preserve timestamp")
        cmd.extend([local_path, remote_path])
        
        output = self._execute(
            cmd,
            device_id=device_id,
            check=True
        )
        
        logger.debug(f"HDC output: {output}")
        
        try:
            verify_output = self.shell(device_id, f"ls {remote_path}")
            if remote_path not in verify_output:
                logger.error(f"Path not found on device: {remote_path}")
                raise HDCError(f"Path not found on device after upload: {remote_path}")
            logger.info(f"Path sent and verified: {remote_path}")
        except Exception as e:
            logger.warning(f"Could not verify path on device: {e}")
            logger.info(f"Path sent: {remote_path}")

    def file_recv(
        self, device_id: str, remote_path: str, local_path: str,
        preserve_timestamp: bool = True
    ) -> None:
        """
        Receive file or directory from device.
        
        Args:
            device_id: Device ID
            remote_path: Remote file path
            local_path: Local file path
            preserve_timestamp: Whether to preserve file timestamp (default True)
        """
        logger.info(f"Receiving: {device_id}:{remote_path} -> {local_path}")
        
        import os
        import platform
        
        from pathlib import Path
        local_path_obj = Path(local_path)
        
        if local_path_obj.is_dir() or remote_path.endswith('/'):
            local_path_obj.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created local directory: {local_path}")
        else:
            local_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        if platform.system() == "Windows":
            local_path = os.path.normpath(local_path)
            logger.debug(f"Normalized Windows path: {local_path}")
        
        cmd = ["file", "recv"]
        if preserve_timestamp:
            cmd.append("-a")
            logger.info("Using HDC -a option to preserve timestamp")
        cmd.extend([remote_path, local_path])
        
        output = self._execute(
            cmd,
            device_id=device_id,
            check=True
        )
        
        logger.debug(f"HDC output: {output}")
        
        if local_path_obj.is_file():
            file_size = local_path_obj.stat().st_size
            if file_size == 0:
                logger.warning(f"Downloaded file has 0 bytes: {local_path}")
            logger.info(f"File received and verified: {local_path} ({file_size} bytes)")
        elif local_path_obj.is_dir():
            logger.info(f"Directory received and verified: {local_path}")
        else:
            logger.warning(f"Download completed, but path type unknown: {local_path}")
    
    def tconn(self, ip_port: str) -> None:
        """
        Connect to device via TCP/IP.
        
        Args:
            ip_port: IP address and port (e.g., "192.168.1.100:5555")
        """
        logger.info(f"Connecting to device: {ip_port}")
        
        self._execute(["tconn", ip_port])
        
        logger.info(f"Connected to: {ip_port}")
    
    def tdisconn(self, ip_port: str) -> None:
        """
        Disconnect from device via TCP/IP.
        
        Args:
            ip_port: IP address and port
        """
        logger.info(f"Disconnecting from device: {ip_port}")
        
        self._execute(["tdisconn", ip_port])
        
        logger.info(f"Disconnected from: {ip_port}")
    
    def shell(self, device_id: str, command: str) -> str:
        """
        Execute shell command on device.
        
        Args:
            device_id: Device ID
            command: Shell command
        
        Returns:
            Command output
        """
        logger.debug(f"Executing shell command: {command}")
        
        return self._execute(
            ["shell", command],
            device_id=device_id
        )