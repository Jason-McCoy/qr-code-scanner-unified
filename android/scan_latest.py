"""Scan the newest camera photo (or a given image) and save results.

Usage (from project root):
    python -m android.scan_latest            # newest photo in camera folder
    python -m android.scan_latest photo.jpg  # a specific image
    python -m android.scan_latest --force    # rescan even if already scanned
    python -m android.scan_latest --verbose  # also show log messages

Photos are read from ~/storage/dcim/Camera unless CAMERA_DIR is set.
"""
import argparse
import glob
import logging
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    # Started as a script (python android/scan_latest.py): put the project
    # folder on the import path so "shared" can be found.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import QRScanner, DataManager, Config  # noqa: E402
from shared.logging_setup import setup_logging  # noqa: E402
from shared.safety import safe_display  # noqa: E402

CAMERA_DIR = os.path.expanduser(os.getenv("CAMERA_DIR", "~/storage/dcim/Camera"))
# Upper- and lower-case, since some phones save IMG_0001.JPG
PATTERNS = ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG")
# Same place as before by default (<project>/data), but follows DATA_DIR
SEEN_FILE = Config.DATA_DIR / "scanned_photos.txt"


def newest_photo(folder):
    files = set()
    for pattern in PATTERNS:
        files.update(glob.glob(os.path.join(folder, pattern)))
    return max(files, key=os.path.getmtime) if files else None


def load_seen():
    if not SEEN_FILE.exists():
        return set()
    return set(SEEN_FILE.read_text().splitlines())


def mark_seen(path):
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SEEN_FILE.open("a") as f:
        f.write(path + "\n")


def main():
    parser = argparse.ArgumentParser(description="Scan QR codes and barcodes in a photo.")
    parser.add_argument("image", nargs="?", help="image to scan (default: newest camera photo)")
    parser.add_argument("--force", action="store_true", help="rescan even if already scanned")
    parser.add_argument("--verbose", action="store_true", help="show log messages")
    args = parser.parse_args()

    # Quiet by default: only warnings on screen, details in logs/scan_latest.log
    setup_logging(
        "scan_latest.log",
        console_level=logging.INFO if args.verbose else logging.WARNING,
    )

    path = args.image or newest_photo(CAMERA_DIR)
    if not path or not os.path.isfile(path):
        print("No image found. Take a photo first, or pass a file path.")
        return 1
    path = os.path.abspath(path)

    if not args.force and path in load_seen():
        print(f"Already scanned {os.path.basename(path)}. Use --force to scan it again.")
        return 0

    print(f"Scanning: {os.path.basename(path)}")
    results = QRScanner().scan_image_file(path)
    if not results:
        print("No codes found. Try a closer, sharper, well-lit photo.")
        return 1

    manager = DataManager()
    saved = 0
    try:
        for i, result in enumerate(results, 1):
            scan_id = manager.save_scan(result)
            if scan_id is not None:
                saved += 1
            # QR content is untrusted: escape control characters so a code
            # cannot clear the screen, change the title or hide text
            status = "" if scan_id is not None else "  (not saved, see logs/scan_latest.log)"
            print(f"  {i}. [{result.format}] {safe_display(result.data)}{status}")
    finally:
        manager.close()

    if saved < len(results):
        # Not marked as scanned, so the next run tries this photo again
        print(f"Saved {saved} of {len(results)} code(s). Run again to retry.")
        return 1

    mark_seen(path)
    print(f"Saved {saved} code(s) to the database.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
