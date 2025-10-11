# -*- coding: utf-8 -*-
"""
Logger Setup using Loguru
=========================

Configures the Loguru logger for the HALO application.
"""
import sys
from pathlib import Path
from loguru import logger

def setup_logging():
    """
    Configures the application's logger using Loguru.

    This setup performs the following actions:
    1. Removes any default pre-configured handlers.
    2. Adds a new handler to stream logs to the console (stdout) with a
       custom format and INFO level.
    3. Creates a 'logs' directory in the project root if it doesn't exist.
    4. Adds a new handler to write logs to a file within the 'logs' directory.
       Log files are rotated when they reach 10 MB.
    """
    # 1. Remove default handlers to avoid duplicate logs
    logger.remove()

    # 2. Add a console logger
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True
    )

    # 3. Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file_path = log_dir / "halo_app_{time}.log"

    # 4. Add a file logger
    logger.add(
        log_file_path,
        level="INFO",
        rotation="10 MB",  # Rotate after 10 MB
        retention="7 days", # Keep logs for 7 days
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    logger.info("Logger has been initialized.")