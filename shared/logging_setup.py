"""
Logging setup shared by the desktop app, the Android app and scan_latest.

Each entry point calls setup_logging() once at start-up. The shared
modules only create loggers and never configure logging themselves.
"""

import logging
from typing import Optional

from .config import Config

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(log_file: Optional[str] = None, console_level: Optional[int] = None) -> None:
    """
    Configure the root logger.

    Args:
        log_file: File name inside Config.LOGS_DIR, such as "desktop.log".
            None means no log file.
        console_level: Level for messages printed to the terminal. Defaults
            to DEBUG in DEBUG_MODE, INFO when ENABLE_LOGGING is on, and
            WARNING otherwise.
    """
    file_level = logging.DEBUG if Config.DEBUG_MODE else logging.INFO
    if console_level is None:
        if Config.DEBUG_MODE:
            console_level = logging.DEBUG
        elif Config.ENABLE_LOGGING:
            console_level = logging.INFO
        else:
            console_level = logging.WARNING

    formatter = logging.Formatter(LOG_FORMAT)
    handlers = []

    console = logging.StreamHandler()
    console.setLevel(console_level)
    console.setFormatter(formatter)
    handlers.append(console)

    if log_file and Config.ENABLE_LOGGING:
        Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(Config.LOGS_DIR / log_file, encoding="utf-8")
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()
    root.setLevel(min(h.level for h in handlers))
    for handler in handlers:
        root.addHandler(handler)
