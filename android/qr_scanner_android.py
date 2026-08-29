"""
Android QR Scanner Application - Main Entry Point

Pydroid 3 compatible implementation for Android devices.
Provides touch-optimized UI for mobile scanning.
"""

import sys
import logging
from pathlib import Path

from shared.config import Config

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if Config.DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOGS_DIR / 'android.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for Android application"""
    try:
        logger.info(f"Starting {Config.APP_NAME} v{Config.APP_VERSION} (Android)")
        
        from shared.qr_scanner import QRScanner
        from shared.data_manager import DataManager
        
        # Initialize components
        scanner = QRScanner(camera_index=0)
        manager = DataManager()
        
        logger.info("Android application initialized")
        logger.info("Scan results will be saved to: " + str(Config.DB_PATH))
        
        print(f"\n{'='*60}")
        print(f"  {Config.APP_NAME} v{Config.APP_VERSION}")
        print(f"  Android (Pydroid 3) Edition")
        print(f"{'='*60}\n")
        
        print("Instructions:")
        print("1. Position your device camera over a QR code")
        print("2. Scans will be automatically saved to the database")
        print("3. Results are stored in: " + str(Config.DB_PATH))
        print("\nPress Ctrl+C to stop scanning\n")
        
        # Start continuous scanning
        def on_scan(results):
            for result in results:
                print(f"✓ Scanned: {result.data[:60]}...")
                scan_id = manager.save_scan(result)
                print(f"  Saved with ID: {scan_id}\n")
        
        scanner.scan_continuous(callback=on_scan)
        
        manager.close()
        logger.info("Android application closed")
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n\nScanning stopped.")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
