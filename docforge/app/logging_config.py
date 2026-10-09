"""Logging configuration for DocForge with log rotation."""

import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from docforge.app.paths import get_logs_dir


def setup_logging(log_filename: str = "docforge.log", level: int = logging.INFO) -> logging.Logger:
    """Configure and return the main application logger with file rotation.

    Args:
        log_filename: Filename for log storage.
        level: Minimum logging level.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger("DocForge")
    logger.setLevel(level)

    if not logger.handlers:
        log_file = get_logs_dir() / log_filename
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=2 * 1024 * 1024,  # 2 MB max file size
            backupCount=5,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
