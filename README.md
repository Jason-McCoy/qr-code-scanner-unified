# QR Code Scanner Unified

**QR Code and Barcode Scanner** - Android (Termux, Pydroid 3) & Desktop (Windows/Linux)

A cross-platform QR code and barcode scanner written in Python. The same core code runs on an Android phone (in Termux, by scanning camera photos) and on a desktop computer (a PyQt5 window with a live camera view).

## Current status

This project is a free, open-source Python codebase. It is not a standalone APK.

| Platform | How it scans | Tested |
|----------|--------------|--------|
| Android, Termux | Scans the newest camera photo (`android.scan_latest`) | Used by the author on his phone |
| Desktop, Linux | Live camera window (PyQt5) | Window starts; live camera not tested in review |
| Desktop, Windows | Live camera window (PyQt5) | Not tested |
| Android, Pydroid 3 | Live camera (`android.qr_scanner_android`) | Not tested |

## Features

- **QR codes and barcodes** - decoded with pyzbar (zbar) from camera frames or photos
- **Saved history** - every scan is stored in a local SQLite database
- **No duplicate floods** - during live scanning, the same code is saved once per cooldown (5 seconds by default, `DUPLICATE_COOLDOWN`)
- **Safe display** - control characters in scanned content are shown as visible escapes (such as `\x1b`), so a QR code cannot clear or rewrite your terminal
- **Export** - JSON and CSV (CSV cells that would run as spreadsheet formulas are neutralised)
- **Search** - find past scans by content

## Quick Start

### Prerequisites
- Python 3.8+
- pip (package manager)
- Camera access (for scanning)

### Installation

```bash
# Clone the repository
git clone https://github.com/Jason-McCoy/qr-code-scanner-unified.git
cd qr-code-scanner-unified

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

Run these from the project folder.

**Android (Termux):** take a photo of the code with the camera app, then:
```bash
python -m android.scan_latest            # newest photo in ~/storage/dcim/Camera
python -m android.scan_latest photo.jpg  # a specific image
python -m android.scan_latest --force    # scan a photo again
```
Termux setup is in [requirements-termux.txt](requirements-termux.txt). Photos already scanned are remembered in `data/scanned_photos.txt`.

**Desktop (Windows/Linux):**
```bash
python -m desktop.qr_scanner_desktop
# or: python desktop/qr_scanner_desktop.py
```

**Android (Pydroid 3), live camera:**
```bash
python -m android.qr_scanner_android
# or: python android/qr_scanner_android.py
```
OpenCV usually cannot open the phone camera from Termux; use `android.scan_latest` there.

Settings can be changed in a `.env` file (copy [.env.example](.env.example)).

## Project Structure

```
qr-code-scanner-unified/
├── shared/          # Shared code (scanning, database, settings, safe display)
├── desktop/         # Desktop application (PyQt5)
├── android/         # Android: scan_latest (Termux) and live camera (Pydroid 3)
├── tests/           # Test suite (fixtures/ holds sample QR images)
├── docs/            # Documentation
└── scripts/         # Utility scripts
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Technical design and decisions
- [Setup Guide](docs/SETUP.md) - Detailed installation instructions
- [Contributing](docs/CONTRIBUTING.md) - How to contribute
- [API Reference](docs/API.md) - Core API documentation

## Testing

```bash
pytest tests/ -v --cov=shared
```

The desktop tests need PyQt5 and are skipped without it (for example on Termux). Without a screen, set `QT_QPA_PLATFORM=offscreen`.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## License

GNU General Public License, version 3 only (SPDX: `GPL-3.0-only`). Later versions of the GPL do not apply. The full text is in [LICENSE](LICENSE).

## Support

For issues, questions, or suggestions, please open an [Issue](https://github.com/Jason-McCoy/qr-code-scanner-unified/issues) on GitHub.

---

**Status**: Active development. A record of the November 2026 review, with what was found, changed, tested and left open, is in [docs/REVIEW-RECORD-2026-11-05.md](docs/REVIEW-RECORD-2026-11-05.md).
