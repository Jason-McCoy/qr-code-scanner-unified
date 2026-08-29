"""
Desktop QR Scanner Application - Main Entry Point

PyQt5-based GUI for Windows and Linux platforms.
Provides real-time QR code scanning with persistent storage and export capabilities.
"""

import sys
import logging
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from shared.config import Config

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if Config.DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOGS_DIR / 'desktop.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import UI after logging setup
from ui.main_window import MainWindow


def main():
    """Main entry point for desktop application"""
    try:
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
        sys.exit(app.exec_())
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
