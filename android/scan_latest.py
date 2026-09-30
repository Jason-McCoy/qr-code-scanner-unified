"""Scan the newest camera photo (or a given image) and save results.

Usage (from project root):
    python -m android.scan_latest            # newest photo in camera folder
    python -m android.scan_latest photo.jpg  # a specific image
"""
import glob
import os
import sys

from shared import QRScanner, DataManager

CAMERA_DIR = os.path.expanduser("~/storage/dcim/Camera")
PATTERNS = ("*.jpg", "*.jpeg", "*.png")


def newest_photo(folder):
    files = []
    for pattern in PATTERNS:
        files.extend(glob.glob(os.path.join(folder, pattern)))
    return max(files, key=os.path.getmtime) if files else None


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else newest_photo(CAMERA_DIR)
    if not path or not os.path.isfile(path):
        print("No image found. Take a photo first, or pass a file path.")
        return 1

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

    print(f"Saved {len(results)} code(s) to the database.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
