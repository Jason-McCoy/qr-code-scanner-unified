"""
Android QR Scanner Application - Main Entry Point

Continuous camera scanning for Android (Pydroid 3) and other systems
where OpenCV can open the camera.

On Termux, OpenCV usually cannot open the phone camera; use
`python -m android.scan_latest` there instead (see README).

Run from the project folder with either:
    python -m android.qr_scanner_android
    python android/qr_scanner_android.py
"""

import sys
import logging
from pathlib import Path

if __package__ in (None, ""):
    # Started as a script (python android/qr_scanner_android.py): put the
    # project folder on the import path so "shared" can be found.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.config import Config  # noqa: E402
from shared.safety import safe_display  # noqa: E402

logger = logging.getLogger(__name__)


def main():
    """Main entry point for Android application"""
    from shared.logging_setup import setup_logging

    setup_logging("android.log")
    manager = None

    try:
        logger.info(f"Starting {Config.APP_NAME} v{Config.APP_VERSION} (Android)")

        from shared.qr_scanner import QRScanner
        from shared.data_manager import DataManager

        # Initialize components
        scanner = QRScanner(camera_index=Config.CAMERA_INDEX)
        manager = DataManager()

        logger.info("Android application initialized")
        logger.info("Scan results will be saved to: " + str(Config.DB_PATH))

        print(f"\n{'='*60}")
        print(f"  {Config.APP_NAME} v{Config.APP_VERSION}")
        print("  Android Edition")
        print(f"{'='*60}\n")

        if not scanner.start():
            print("Could not open the camera.")
            print("On Termux, use: python -m android.scan_latest")
            return 1

        print("Instructions:")
        print("1. Position your device camera over a QR code")
        print("2. Scans will be automatically saved to the database")
        print("3. Results are stored in: " + str(Config.DB_PATH))
        print(
            f"   (the same code is saved once per {Config.DUPLICATE_COOLDOWN:g} seconds)"
        )
        print("\nPress Ctrl+C to stop scanning\n")

        # Start continuous scanning
        def on_scan(results):
            for result in results:
                # QR content is untrusted: escape control characters so a
                # code cannot clear the screen or rewrite the terminal
                print(f"✓ Scanned: {safe_display(result.data, 60)}")
                scan_id = manager.save_scan(result)
                if scan_id is None:
                    print("  Not saved (see log)\n")
                else:
                    print(f"  Saved with ID: {scan_id}\n")

        scanner.scan_continuous(callback=on_scan)

        logger.info("Android application closed")
        return 0

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n\nScanning stopped.")
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nError: {e}")
        return 1

    finally:
        if manager is not None:
            manager.close()


if __name__ == "__main__":
    sys.exit(main())
