# QR Code Scanner Unified - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
