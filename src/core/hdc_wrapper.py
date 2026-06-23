"""
HDC (HarmonyOS Device Connector) wrapper for OpenHarmony File Browser.
Provides interface to communicate with OpenHarmony/HarmonyOS devices.
"""

import os
import shutil
import subprocess
import tempfile
import time
import uuid
import platform
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from ..models.device import DeviceInfo, DeviceStatus
from ..models.file_info import FileInfo, FileType
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Cache subprocess creation flags
_IS_WINDOWS = platform.system() == "Windows"
_SUBPROCESS_KWARGS = (
    {"creationflags": subprocess.CREATE_NO_WINDOW} if _IS_WINDOWS else {}
)
_UTF8_ENV = {**os.environ, "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}


def _has_non_ascii(path: str) -> bool:
    """Check if path contains non-ASCII characters."""
    try:
        path.encode("ascii")
        return False
    except UnicodeEncodeError:
        return True


def _copy_dir_robust(src: str, dst: str) -> None:
    """Copy directory robustly on Windows using robocopy, falling back to shutil.copytree."""
    if _IS_WINDOWS:
        result = subprocess.run(
            [
                "robocopy",
                src,
                dst,
                "/E",
                "/NFL",
                "/NDL",
                "/NJH",
                "/NJS",
                "/NC",
                "/NS",
                "/NP",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        # robocopy exit codes: 0-3 = success, 4-7 = some files not copied, 8+ = error
        if result.returncode >= 8:
            raise OSError(f"robocopy failed: {result.stderr}")
    else:
        shutil.copytree(src, dst)


def _ensure_ascii_path(path: str, is_dir: bool = False) -> tuple:
    """Ensure path is ASCII-only for HDC on Windows.

    If path contains non-ASCII characters, copy/create a temporary ASCII path.

    Args:
        path: Original file/directory path
        is_dir: Whether this is a directory (True) or file (False)

    Returns:
        Tuple of (ascii_path, cleanup_func)
        - ascii_path: ASCII-only path to use with HDC
        - cleanup_func: Function to call after HDC operation to clean up temp files
    """
    if not _IS_WINDOWS or not _has_non_ascii(path):
        return path, lambda: None

    if is_dir:
        tmp_dir = tempfile.mkdtemp(prefix="hdc_")
        _copy_dir_robust(path, tmp_dir)
        logger.debug(f"Created temp ASCII dir: {tmp_dir}")
        return tmp_dir, lambda: shutil.rmtree(tmp_dir, ignore_errors=True)
    else:
        ext = Path(path).suffix
        tmp_file = tempfile.NamedTemporaryFile(suffix=ext, prefix="hdc_", delete=False)
        tmp_file.close()
        shutil.copy2(path, tmp_file.name)
        logger.debug(f"Created temp ASCII file: {tmp_file.name}")
        return tmp_file.name, lambda: os.unlink(tmp_file.name)


def _ensure_ascii_remote_path(remote_path: str, is_dir: bool = False) -> tuple:
    """Generate an ASCII temporary remote path for HDC transfer.

    If remote_path contains non-ASCII characters, return an ASCII temp path
    and the original path for post-transfer rename.

    Returns:
        Tuple of (transfer_path, original_path, rename_needed)
    """
    if not _IS_WINDOWS or not _has_non_ascii(remote_path):
        return remote_path, remote_path, False

    if is_dir:
        ascii_name = f"hdc_{uuid.uuid4().hex[:8]}"
        parent = remote_path.rstrip("/").rsplit("/", 1)[0] or "/"
        transfer_path = f"{parent}/{ascii_name}"
    else:
        parent = remote_path.rsplit("/", 1)[0] or "/"
        ext = Path(remote_path).suffix
        ascii_name = f"hdc_{uuid.uuid4().hex[:8]}{ext}"
        transfer_path = f"{parent}/{ascii_name}"

    logger.debug(f"Using temp remote path: {transfer_path}")
    return transfer_path, remote_path, True


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

        # Persistent shell sessions per device: device_id -> subprocess.Popen
        self._shell_sessions: Dict[str, subprocess.Popen] = {}

        logger.info(f"HDC wrapper initialized: {self.hdc_path}")

    def _verify_hdc(self) -> None:
        """Verify HDC tool is accessible."""
        hdc_file = Path(self.hdc_path)
        if not hdc_file.exists():
            raise HDCError(f"HDC tool not found: {self.hdc_path}")

        if not hdc_file.is_file():
            raise HDCError(f"HDC path is not a file: {self.hdc_path}")

        try:
            result = subprocess.run(
                [self.hdc_path, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=5,
                **_SUBPROCESS_KWARGS,
            )
            logger.debug(f"HDC version: {result.stdout.strip()}")
        except Exception as e:
            raise HDCError(f"Failed to execute HDC: {e}")

    def _get_or_create_shell_session(self, device_id: str) -> subprocess.Popen:
        """
        Get or create a persistent shell session for a device.

        Args:
            device_id: Device ID

        Returns:
            Popen object for the shell session
        """
        if device_id in self._shell_sessions:
            proc = self._shell_sessions[device_id]
            if proc.poll() is None:
                return proc
            else:
                del self._shell_sessions[device_id]

        cmd = [self.hdc_path, "-t", device_id, "shell"]
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=_UTF8_ENV,
            **_SUBPROCESS_KWARGS,
        )
        self._shell_sessions[device_id] = proc
        logger.debug(f"Created persistent shell session for device: {device_id}")
        return proc

    def shell_batch(
        self, device_id: str, commands: List[str], timeout: Optional[int] = None
    ) -> List[str]:
        """
        Execute multiple shell commands in a single session.

        Args:
            device_id: Device ID
            commands: List of shell commands to execute
            timeout: Command timeout in seconds

        Returns:
            List of command outputs (one per command)
        """
        proc = self._get_or_create_shell_session(device_id)

        try:
            delimiter = "---HDC_BATCH_DELIM---"
            batch_input = ""
            for cmd in commands:
                batch_input += f"{cmd}\necho {delimiter}\n"

            proc.stdin.write(batch_input)
            proc.stdin.flush()

            timeout = timeout or self.timeout
            outputs = []
            current_lines = []
            start_time = time.time()

            while True:
                if time.time() - start_time > timeout:
                    raise HDCError(f"Shell batch command timeout after {timeout}s")

                line = proc.stdout.readline()
                if line:
                    if delimiter in line:
                        outputs.append("".join(current_lines).strip())
                        current_lines = []
                        if len(outputs) == len(commands):
                            break
                    else:
                        current_lines.append(line)
                else:
                    time.sleep(0.01)

            return outputs

        except HDCError:
            raise
        except Exception as e:
            if device_id in self._shell_sessions:
                try:
                    self._shell_sessions[device_id].kill()
                except Exception:
                    pass
                del self._shell_sessions[device_id]
            raise HDCError(f"Shell batch command failed: {e}")

    def close_shell_sessions(self) -> None:
        """Close all persistent shell sessions."""
        for device_id, proc in self._shell_sessions.items():
            try:
                proc.stdin.close()
                proc.kill()
                proc.wait(timeout=2)
            except Exception:
                pass
        self._shell_sessions.clear()
        logger.debug("All shell sessions closed")

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
                encoding="utf-8",
                env=_UTF8_ENV,
                timeout=timeout or self.timeout,
                **_SUBPROCESS_KWARGS,
            )

            combined_output = result.stderr.strip() + result.stdout.strip()
            if check and (result.returncode != 0 or "[Fail]" in combined_output):
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
            batch_cmd = (
                "echo MODEL:$(param get const.product.model); "
                "echo BRAND:$(param get const.product.brand); "
                "echo PRODUCT:$(param get const.product.name)"
            )
            output = self._execute(
                ["shell", batch_cmd], device_id=device_id, check=False
            )

            for line in output.split("\n"):
                line = line.strip()
                if line.startswith("MODEL:"):
                    val = line[6:].strip()
                    if val:
                        device.model = val
                elif line.startswith("BRAND:"):
                    val = line[6:].strip()
                    if val:
                        device.brand = val
                elif line.startswith("PRODUCT:"):
                    val = line[8:].strip()
                    if val:
                        device.product = val

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
        logger.debug(f"Listing files: {device_id}:{path} (show_hidden={show_hidden})")

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
            if " -> " in name:
                name, _, target = name.partition(" -> ")
                is_dir = target.endswith("/")
            else:
                is_dir = False

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

        output = self._execute(["shell", "stat", path], device_id=device_id)

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
                    time_str = line.split("Modify: ")[1].strip()
                    time_str = time_str.split(".")[0]
                    modified_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
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

        self._execute(["shell", "mkdir", "-p", path], device_id=device_id)

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

        self._execute(["shell", "mv", src, dst], device_id=device_id)

        logger.info(f"Moved: {src} -> {dst}")

    def file_send(
        self,
        device_id: str,
        local_path: str,
        remote_path: str,
        preserve_timestamp: bool = True,
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

        def _noop_cleanup():
            pass

        cleanup_local = _noop_cleanup

        try:
            if platform.system() == "Windows":
                local_path = os.path.normpath(local_path)
                is_dir_upload = Path(local_path).is_dir()
                if _has_non_ascii(local_path):
                    local_path, cleanup_local = _ensure_ascii_path(
                        local_path, is_dir=is_dir_upload
                    )
                    logger.debug(
                        f"Using temp ASCII local path for upload: {local_path}"
                    )

                if _has_non_ascii(remote_path):
                    remote_path, original_remote, rename_needed = (
                        _ensure_ascii_remote_path(remote_path, is_dir=is_dir_upload)
                    )
                else:
                    original_remote = remote_path
                    rename_needed = False
            else:
                original_remote = remote_path
                rename_needed = False

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

            self._execute(cmd, device_id=device_id, check=True)

            # Rename on device if we used a temp remote path
            if rename_needed:
                try:
                    self._execute(
                        ["shell", "mv", remote_path, original_remote],
                        device_id=device_id,
                        check=True,
                    )
                    logger.debug(
                        f"Renamed on device: {remote_path} -> {original_remote}"
                    )
                except HDCError as e:
                    raise HDCError(f"Failed to rename file on device: {e}")

            self._execute(
                ["shell", "test", "-e", original_remote],
                device_id=device_id,
                check=True,
            )
            logger.info(f"Path sent and verified: {original_remote}")

        finally:
            cleanup_local()

    def file_recv(
        self,
        device_id: str,
        remote_path: str,
        local_path: str,
        preserve_timestamp: bool = True,
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

        original_local_path = local_path

        def _noop_cleanup():
            pass

        cleanup_local_temp = _noop_cleanup
        remote_rename_needed = False
        remote_rename_done = False
        ascii_remote = remote_path
        is_dir_download = remote_path.endswith("/")
        recv_succeeded = False
        used_temp_local = False

        try:
            if platform.system() == "Windows":
                local_path = os.path.normpath(local_path)
                if _has_non_ascii(local_path):
                    used_temp_local = True
                    if is_dir_download:
                        tmp_dir = tempfile.mkdtemp(prefix="hdc_")
                        tmp_dir_path = tmp_dir

                        def _cleanup_dir():
                            shutil.rmtree(tmp_dir_path, ignore_errors=True)

                        cleanup_local_temp = _cleanup_dir
                        local_path = tmp_dir
                    else:
                        ext = Path(local_path).suffix
                        tmp_file = tempfile.NamedTemporaryFile(
                            suffix=ext, prefix="hdc_", delete=False
                        )
                        tmp_file.close()
                        tmp_file_name = tmp_file.name

                        def _cleanup_file():
                            os.unlink(tmp_file_name)

                        cleanup_local_temp = _cleanup_file
                        local_path = tmp_file.name
                    logger.debug(
                        f"Using temp ASCII local path for download: {local_path}"
                    )

                if _has_non_ascii(remote_path):
                    ascii_remote, original_remote, remote_rename_needed = (
                        _ensure_ascii_remote_path(remote_path, is_dir=is_dir_download)
                    )
                    try:
                        self._execute(
                            ["shell", "mv", remote_path, ascii_remote],
                            device_id=device_id,
                            check=True,
                        )
                        remote_rename_done = True
                        logger.debug(
                            f"Renamed on device for download: {remote_path} -> {ascii_remote}"
                        )
                    except HDCError as e:
                        raise HDCError(
                            f"Failed to rename remote file for download: {e}"
                        )
                else:
                    original_remote = remote_path
            else:
                original_remote = remote_path

            local_path_obj = Path(local_path)

            if is_dir_download:
                local_path_obj.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created local directory: {local_path}")
            else:
                local_path_obj.parent.mkdir(parents=True, exist_ok=True)

            cmd = ["file", "recv"]
            if preserve_timestamp:
                cmd.append("-a")
                logger.info("Using HDC -a option to preserve timestamp")
            cmd.extend([ascii_remote, local_path])

            self._execute(cmd, device_id=device_id, check=True)
            recv_succeeded = True

            # Rename remote file back to original name
            if remote_rename_needed:
                try:
                    self._execute(
                        ["shell", "mv", ascii_remote, original_remote],
                        device_id=device_id,
                        check=True,
                    )
                    logger.debug(
                        f"Renamed back on device: {ascii_remote} -> {original_remote}"
                    )
                except HDCError as e:
                    logger.warning(f"Failed to rename remote file back: {e}")

            # If we used a temp local path, copy to original target
            if used_temp_local:
                target_path = Path(original_local_path)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                if is_dir_download:
                    shutil.copytree(local_path, original_local_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(local_path, original_local_path)
                logger.debug(f"Copied from temp path to: {original_local_path}")

            target_obj = Path(original_local_path)
            if target_obj.is_file():
                file_size = target_obj.stat().st_size
                if file_size == 0:
                    logger.warning(
                        f"Downloaded file has 0 bytes: {original_local_path}"
                    )
                logger.info(
                    f"File received and verified: {original_local_path} ({file_size} bytes)"
                )
            elif target_obj.is_dir():
                logger.info(f"Directory received and verified: {original_local_path}")
            else:
                logger.warning(
                    f"Download completed, but path type unknown: {original_local_path}"
                )

        finally:
            # Rollback remote rename if recv failed
            if remote_rename_needed and remote_rename_done and not recv_succeeded:
                try:
                    self._execute(
                        ["shell", "mv", ascii_remote, original_remote],
                        device_id=device_id,
                        check=True,
                    )
                    logger.debug(
                        f"Rolled back remote rename: {ascii_remote} -> {original_remote}"
                    )
                except Exception:
                    logger.warning(
                        f"Failed to rollback remote rename: {ascii_remote} -> {original_remote}"
                    )
            cleanup_local_temp()

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

        return self._execute(["shell", command], device_id=device_id)

    def cleanup(self) -> None:
        """Cleanup resources, close persistent shell sessions."""
        self.close_shell_sessions()
