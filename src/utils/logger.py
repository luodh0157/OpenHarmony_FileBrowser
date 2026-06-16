"""
Logger module for OpenHarmony File Browser.
Provides logging functionality with both file and console output.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

_logger_names: set[str] = set()


def get_logger(
    name: str = "OpenHarmonyFileBrowser",
    log_file: Optional[str] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name
        log_file: Path to log file. If None, uses default path.
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    _logger_names.add(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if log_file is None:
        from src.config import config

        log_dir = config.log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def set_log_level(logger: logging.Logger, level: int) -> None:
    """
    Set logging level for logger and all its handlers.

    Args:
        logger: Logger instance
        level: Logging level
    """
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


def set_global_log_level(level: int) -> None:
    """
    Set global log level affecting all module loggers.

    Args:
        level: Logging level
    """
    for name in _logger_names:
        lg = logging.getLogger(name)
        lg.setLevel(level)
        for handler in lg.handlers:
            handler.setLevel(level)
