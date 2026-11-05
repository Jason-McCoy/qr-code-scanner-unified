# QR Code Scanner Unified - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Review and fixes, November 5, 2026. Full details, test output and open items:
docs/REVIEW-RECORD-2026-11-05.md

### Fixed
- Desktop app failed to start: wrong import paths in desktop/ui/main_window.py
  and desktop/qr_scanner_desktop.py (ModuleNotFoundError)
- README commands `python desktop/...` and `python android/...` failed with
  "No module named 'shared'"; both script and `python -m` forms now work
- Continuous scanning saved the same code once per video frame (about 30 a
  second); now once per DUPLICATE_COOLDOWN (default 5 s)
- Continuous scanning crashed on OpenCV builds without a GUI (cv2.waitKey)
- Busy loop at 100% CPU when the camera returned no frames
- QR content with terminal control characters was printed raw (could clear
  the screen or change the terminal title)
- CSV export: formula injection, Python list text for tags, no UTF-8 on Windows
- SQLAlchemy 1.4 (allowed by requirements) crashed on start (pool_size)
- Log files logs/android.log and logs/desktop.log were always empty
- Desktop: Copy Selected copied the shortened text and needed a full-row
  selection; QPixmap made outside the GUI thread; Stop could hang
- scan_latest marked a photo as scanned even when saving failed
- .env.example started with a Python docstring that python-dotenv could not parse
- QUICKSTART.md was a corrupted tool payload and stated the MIT license
- Follow-up (record section 9): live scanning on desktop and Android no
  longer treats a code as done when its database write fails; it retries
- Follow-up: desktop worker now releases the camera itself on stop or error;
  a Stop that timed out no longer aborts the app (bug from this review)
- Desktop: a camera that stops answering no longer stays held until exit;
  the camera runs in its own process, which is ended after
  CAMERA_READ_TIMEOUT (record section 10; simulated camera only)
- Photo files: large phone photos of a QR code (for example of a screen)
  were not read; scan_image_file now retries on smaller and black-and-white
  copies (record section 14)
- Follow-up: CSV guard also catches line feed, leading spaces and invisible
  characters before a formula, and full-width = + - @

### Added
- shared/safety.py (safe_display, csv_safe_cell), shared/logging_setup.py
- QRScanner.filter_new() and reset_duplicates(); DUPLICATE_COOLDOWN setting
- QRScanner.mark_failed(); SAVE_RETRY_DELAY setting
- shared/camera_process.py; DESKTOP_CAMERA_PROCESS, CAMERA_OPEN_TIMEOUT,
  CAMERA_READ_TIMEOUT settings
- scan_latest --verbose, upper-case photo extensions, CAMERA_DIR setting
- Tests: real QR image fixtures, duplicate filter, safety helpers, CSV/JSON
  export, entry points, desktop window (offscreen)

## [1.0.0] - 2026-08-29

### Added
- Core QR scanning engine using OpenCV and pyzbar
- Real-time camera capture and processing
- SQLite-based persistence layer for scan results
- Configurable multi-format export (JSON, CSV)
- PyQt5-based desktop GUI for Windows/Linux
- Android support via Pydroid 3
- Comprehensive test suite with >80% coverage
- Complete API documentation
- Architecture documentation
- Contribution guidelines

### Features
- ✅ Real-time QR Code Detection
- ✅ Cross-Platform Support (Desktop + Android)
- ✅ Data Persistence with SQLite
- ✅ User-Friendly Interface
- ✅ Multi-format Export
- ✅ Search and Filtering
- ✅ Extensible Architecture

### Performance
- 30 FPS continuous scanning
- <100ms per frame detection
- ~50MB base memory footprint
- Support for 1000+ scan records

## Future Roadmap

### [1.1.0] - Planned
- [ ] PDF export support
- [ ] Batch scanning mode
- [ ] QR code filtering by date/type
- [ ] Cloud sync (Firebase/AWS)
- [ ] Web dashboard
- [ ] API server mode

### [1.2.0] - Planned
- [ ] Mobile app (Flutter/React Native)
- [ ] Multi-language support
- [ ] Advanced image processing
- [ ] Machine learning for format detection
