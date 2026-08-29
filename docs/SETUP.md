# Setup and Installation Guide

## Prerequisites

- **Python**: 3.8 or higher
- **pip**: Python package manager
- **Git**: For cloning the repository
- **Camera**: Device with working camera
- **OS**: Windows, Linux, macOS (Desktop) or Android with Pydroid 3

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/Jason-McCoy/qr-code-scanner-unified.git
cd qr-code-scanner-unified
```

### 2. Create Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -c "from shared import QRScanner; print('✓ Installation successful')"
```

## Running the Application

### Desktop (Windows/Linux)

```bash
python desktop/qr_scanner_desktop.py
```

The PyQt5 GUI will open with:
- Live camera preview
- Real-time QR detection
- Result history
- Export options

### Android (Pydroid 3)

1. Install Pydroid 3 from Google Play Store
2. Copy project to device storage:
   ```bash
   adb push . /storage/emulated/0/qr-code-scanner/
   ```
3. Open Pydroid 3
4. Navigate to project directory
5. Run: `python android/qr_scanner_android.py`

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Camera settings
CAMERA_INDEX=0              # Camera device (0 = default)
SCAN_TIMEOUT=30             # Max scanning duration (seconds)

# Image processing
IMAGE_QUALITY=95            # JPEG quality (0-100)
MAX_IMAGE_SIZE=2048         # Max resolution (pixels)

# Database
DB_PATH=./data/qr_scanner.db
DB_POOL_SIZE=5
DB_TIMEOUT=10

# Features
AUTO_SAVE=true              # Auto-save scans
ENABLE_LOGGING=true         # Console logging
DEBUG_MODE=false            # Debug output
```

### Default Paths

```
project_root/
├── data/                    # Scanned data (auto-created)
│   └── qr_scanner.db       # SQLite database
├── logs/                    # Log files (auto-created)
└── .env                     # Configuration (optional)
```

## Running Tests

### All Tests

```bash
pytest tests/ -v
```

### Specific Test File

```bash
pytest tests/test_qr_scanner.py -v
```

### With Coverage Report

```bash
pytest tests/ --cov=shared --cov-report=html
open htmlcov/index.html
```

## Troubleshooting

### Camera Not Found

```bash
# Check available cameras
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"

# Try different camera index in .env
CAMERA_INDEX=1
```

### Permission Denied (Linux)

```bash
# Add user to video group
sudo usermod -a -G video $USER
sudo usermod -a -G dialout $USER

# Log out and back in
```

### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### Database Lock Error

```bash
# Database is locked by another process
# Solution: Close all instances and delete lock file
rm data/*.db-journal
```

## Development Setup

### Install Development Dependencies

```bash
pip install pytest pytest-cov black flake8
```

### Code Formatting

```bash
black shared/ desktop/ android/ tests/
```

### Linting

```bash
flake8 shared/ --max-line-length=100
```

## Building for Distribution

### Windows Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed desktop/qr_scanner_desktop.py
```

### Linux AppImage

```bash
pip install appimage-builder
appimage-builder --recipe AppImageBuilder.yml
```

## Next Steps

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
2. Check [API.md](API.md) for API reference
3. See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
4. Try [examples/](../examples/) for sample usage
