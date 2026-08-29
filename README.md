# QR Code Scanner Unified

**Universal QR Code Scanner** - Android (Pydroid 3) & Desktop (Windows/Linux)

A high-performance, cross-platform QR code scanning application that runs seamlessly on both Android devices (via Pydroid 3) and desktop environments (Windows/Linux). Designed for reliability, ease of sharing, and extensibility.

## Features

✅ **Real-time QR Code Detection** - Fast, accurate scanning using OpenCV and pyzbar
✅ **Cross-Platform Support** - Single codebase for Android and Desktop
✅ **Data Persistence** - Save and manage scanned QR codes
✅ **User-Friendly Interface** - Intuitive UI for both touch and desktop
✅ **Shareable Results** - Export scanned data in multiple formats
✅ **Extensible Architecture** - Easy to add new features and integrations

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

**Desktop (Windows/Linux):**
```bash
python desktop/qr_scanner_desktop.py
```

**Android (Pydroid 3):**
```bash
python android/qr_scanner_android.py
```

## Project Structure

```
qr-code-scanner-unified/
├── shared/          # Shared code (core scanning logic)
├── desktop/         # Desktop application (PyQt5)
├── android/         # Android application (Pydroid 3)
├── tests/           # Test suite
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

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details

## Support

For issues, questions, or suggestions, please open an [Issue](https://github.com/Jason-McCoy/qr-code-scanner-unified/issues) on GitHub.

---

**Status**: 🚀 Active Development
