"""Scan the newest camera photo (or a given image) and save results.

Usage (from project root):
    python -m android.scan_latest            # newest photo in camera folder
    python -m android.scan_latest photo.jpg  # a specific image
    python -m android.scan_latest --force    # rescan even if already scanned
"""
import argparse
import glob
import os
import sys
from pathlib import Path

from shared import QRScanner, DataManager

CAMERA_DIR = os.path.expanduser("~/storage/dcim/Camera")
PATTERNS = ("*.jpg", "*.jpeg", "*.png")
SEEN_FILE = Path(__file__).resolve().parent.parent / "data" / "scanned_photos.txt"


def newest_photo(folder):
    files = []
    for pattern in PATTERNS:
        files.extend(glob.glob(os.path.join(folder, pattern)))
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
    args = parser.parse_args()

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
    try:
        for i, result in enumerate(results, 1):
            manager.save_scan(result)
            print(f"  {i}. [{result.format}] {result.data}")
    finally:
        manager.close()

    mark_seen(path)
    print(f"Saved {len(results)} code(s) to the database.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
