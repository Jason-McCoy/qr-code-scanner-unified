# Quick Reference Guide

## Install

**Desktop (Windows/Linux):**
```bash
git clone https://github.com/Jason-McCoy/qr-code-scanner-unified.git
cd qr-code-scanner-unified
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
pyzbar also needs the zbar library (Linux: `sudo apt install libzbar0`; the Windows pyzbar wheel includes it).

**Termux (Android):** see the setup notes at the top of `requirements-termux.txt`, then:
```bash
pip install -r requirements-termux.txt
```

## Run

Run these from the project folder.

| What | Command |
|------|---------|
| Termux: scan newest camera photo | `python -m android.scan_latest` |
| Termux: scan a given image | `python -m android.scan_latest photo.jpg` |
| Termux: scan a photo again | `python -m android.scan_latest --force` |
| Desktop window | `python -m desktop.qr_scanner_desktop` |
| Live camera, no window (Pydroid 3) | `python -m android.qr_scanner_android` |
| Tests | `pytest tests/ -v` |

## Key Files

| File | Purpose |
|------|---------|
| `shared/qr_scanner.py` | Scanning engine and duplicate filter |
| `shared/data_manager.py` | SQLite database and JSON/CSV export |
| `shared/safety.py` | Safe display of untrusted QR content |
| `shared/config.py` | Settings from `.env` |
| `android/scan_latest.py` | Termux photo scanner |
| `desktop/qr_scanner_desktop.py` | Desktop GUI app |
| `android/qr_scanner_android.py` | Live camera scanner without a window |

## Common Tasks

**Scan an image file:**
```python
from shared import QRScanner, DataManager

manager = DataManager()
for result in QRScanner().scan_image_file("photo.jpg"):
    manager.save_scan(result)
manager.close()
```

**Scan from the camera for 30 seconds:**
```python
from shared import QRScanner, DataManager

scanner = QRScanner()
manager = DataManager()
results = scanner.scan_continuous(duration=30)  # opens and closes the camera
for result in results:
    manager.save_scan(result)
manager.close()
```

**Export and search:**
```python
from shared import DataManager

manager = DataManager()
manager.export_json("scans.json")
manager.export_csv("scans.csv")
for scan in manager.search_scans("github"):
    print(scan["data"])
manager.close()
```

When printing scanned content in your own code, pass it through `shared.safety.safe_display()` first, because a QR code can contain terminal control characters.

## Environment Variables

Copy `.env.example` to `.env`. The most useful settings:

```bash
CAMERA_INDEX=0           # Camera device (0 = default)
DUPLICATE_COOLDOWN=5     # Seconds before the same code is saved again
DEBUG_MODE=false         # More detail in logs
DATA_DIR=./data          # Database folder (relative to the project folder)
```

## License

GNU General Public License v3.0. See the LICENSE file.

## Author

Created by Jason McCoy
GitHub: [@Jason-McCoy](https://github.com/Jason-McCoy)
