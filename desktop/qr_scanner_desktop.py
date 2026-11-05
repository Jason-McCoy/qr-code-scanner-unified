"""
Desktop QR Scanner Application - Main Entry Point

PyQt5-based GUI for Windows and Linux platforms.
Provides real-time QR code scanning with persistent storage and export capabilities.

Run from the project folder with either:
    python -m desktop.qr_scanner_desktop
    python desktop/qr_scanner_desktop.py
"""

import sys
import logging
from pathlib import Path

if __package__ in (None, ""):
    # Started as a script (python desktop/qr_scanner_desktop.py): put the
    # project folder on the import path so "shared" and "desktop" can be
    # found. Without this the README command failed with
    # "ModuleNotFoundError: No module named 'shared'".
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.config import Config  # noqa: E402

logger = logging.getLogger(__name__)


def main():
    """Main entry point for desktop application"""
    from shared.logging_setup import setup_logging

    setup_logging("desktop.log")

    try:
        # Imported here so that importing this module (for example from
        # desktop/__init__.py) does not need a display or start Qt
        from PyQt5.QtWidgets import QApplication
        from desktop.ui.main_window import MainWindow

        logger.info(f"Starting {Config.APP_NAME} v{Config.APP_VERSION}")

        # Create Qt application
        app = QApplication(sys.argv)

        # Set application metadata
        app.setApplicationName(Config.APP_NAME)
        app.setApplicationVersion(Config.APP_VERSION)

        # Create and show main window
        window = MainWindow()
        window.show()

        logger.info("Application window displayed")

        # Run event loop
        return app.exec_()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
