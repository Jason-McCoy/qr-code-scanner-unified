"""
Unit tests for QR Scanner module
"""

from pathlib import Path

import pytest
import numpy as np
from shared.qr_scanner import ScanResult, QRScanner

FIXTURES = Path(__file__).parent / "fixtures"


class TestScanResult:
    """Tests for ScanResult class"""

    def test_scan_result_creation(self):
        """Test creating a ScanResult"""
        result = ScanResult(
            data="https://example.com",
            format="QRCODE",
        )
        assert result.data == "https://example.com"
        assert result.format == "QRCODE"
        assert result.timestamp is not None

    def test_scan_result_with_rect(self):
        """Test ScanResult with rectangle coordinates"""
        rect = (10, 20, 100, 100)
        result = ScanResult(
            data="test",
            format="QRCODE",
            rect=rect,
        )
        assert result.rect == rect

    def test_scan_result_to_dict(self):
        """Test converting ScanResult to dictionary"""
        result = ScanResult(
            data="test",
            format="QRCODE",
            rect=(0, 0, 100, 100),
        )
        d = result.to_dict()
        assert "data" in d
        assert "format" in d
        assert "timestamp" in d
        assert "rect" in d
        assert d["data"] == "test"

    def test_scan_result_repr(self):
        """Test string representation"""
        result = ScanResult(data="test", format="QRCODE")
        assert "test" in repr(result)
        assert "QRCODE" in repr(result)


class TestQRScanner:
    """Tests for QRScanner class"""

    def test_scanner_initialization(self):
        """Test QRScanner initialization"""
        scanner = QRScanner(camera_index=0)
        assert scanner.camera_index == 0
        assert not scanner.is_running
        assert scanner.cap is None

    def test_get_status(self):
        """Test getting scanner status"""
        scanner = QRScanner()
        status = scanner.get_status()
        assert "is_running" in status
        assert "camera_index" in status
        assert not status["is_running"]

    def test_scanner_factory_singleton(self):
        """Test QRScanner factory returns same instance"""
        from shared.qr_scanner import QRScannerFactory

        scanner1 = QRScannerFactory.get_scanner()
        scanner2 = QRScannerFactory.get_scanner()

        assert scanner1 is scanner2

        # Cleanup
        QRScannerFactory.reset()

    def test_draw_detections_empty(self):
        """Test drawing detections on frame with no results"""
        scanner = QRScanner()

        # Create dummy frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        results = []

        annotated = scanner.draw_detections(frame, results)

        # Should return same frame if no detections
        assert annotated.shape == frame.shape

    def test_draw_detections_with_results(self):
        """Test drawing detections on frame with QR codes"""
        scanner = QRScanner()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        results = [
            ScanResult(data="test", format="QRCODE", rect=(100, 100, 50, 50))
        ]

        annotated = scanner.draw_detections(frame, results)

        assert annotated.shape == frame.shape
        # Frame should be modified (annotations added)
        assert annotated.sum() > frame.sum()

    def test_repr_escapes_control_characters(self):
        """repr() of hostile content must not carry raw escape codes"""
        result = ScanResult(data="x\x1b[2Jy", format="QRCODE")
        assert "\x1b" not in repr(result)


class TestImageScanning:
    """Decode real QR images (generated with qrencode, see tests/fixtures)"""

    def test_scan_image_file_url(self):
        results = QRScanner().scan_image_file(str(FIXTURES / "qr_url.png"))
        assert len(results) == 1
        assert results[0].data == "https://example.com/test"
        assert results[0].format == "QRCODE"
        assert results[0].rect is not None

    def test_scan_image_file_keeps_raw_content(self):
        """Stored data is the exact content; escaping is only for display"""
        results = QRScanner().scan_image_file(str(FIXTURES / "qr_escape.png"))
        assert len(results) == 1
        assert results[0].data == "HELLO\x1b[2J\x1b]0;pwned\x07=cmd"

    def test_scan_image_file_missing(self):
        assert QRScanner().scan_image_file(str(FIXTURES / "does-not-exist.png")) == []


class TestDuplicateFilter:
    """Tests for QRScanner.filter_new()"""

    def _result(self, data="abc"):
        return ScanResult(data=data, format="QRCODE")

    def test_same_code_reported_once_within_cooldown(self):
        scanner = QRScanner(duplicate_cooldown=5)
        assert len(scanner.filter_new([self._result()], now=100.0)) == 1
        assert scanner.filter_new([self._result()], now=101.0) == []
        assert scanner.filter_new([self._result()], now=104.9) == []

    def test_code_reported_again_after_cooldown(self):
        scanner = QRScanner(duplicate_cooldown=5)
        scanner.filter_new([self._result()], now=100.0)
        assert len(scanner.filter_new([self._result()], now=106.0)) == 1

    def test_code_held_in_view_not_repeated(self):
        """Seeing the code every second keeps it quiet, not repeat every 5 s"""
        scanner = QRScanner(duplicate_cooldown=5)
        reported = 0
        for second in range(20):
            reported += len(scanner.filter_new([self._result()], now=float(second)))
        assert reported == 1

    def test_different_codes_both_reported(self):
        scanner = QRScanner(duplicate_cooldown=5)
        fresh = scanner.filter_new([self._result("a"), self._result("b")], now=1.0)
        assert [r.data for r in fresh] == ["a", "b"]

    def test_cooldown_zero_reports_everything(self):
        scanner = QRScanner(duplicate_cooldown=0)
        assert len(scanner.filter_new([self._result()], now=1.0)) == 1
        assert len(scanner.filter_new([self._result()], now=1.0)) == 1

    def test_reset_duplicates(self):
        scanner = QRScanner(duplicate_cooldown=5)
        scanner.filter_new([self._result()], now=1.0)
        scanner.reset_duplicates()
        assert len(scanner.filter_new([self._result()], now=2.0)) == 1


class _FakeCapture:
    """Stands in for cv2.VideoCapture: returns the same frame N times"""

    def __init__(self, frame, frames):
        self.frame = frame
        self.remaining = frames
        self.released = False

    def read(self):
        if self.remaining <= 0:
            return False, None
        self.remaining -= 1
        return True, self.frame.copy()

    def release(self):
        self.released = True


class TestScanContinuous:
    """scan_continuous() with a fake camera"""

    def test_same_code_in_many_frames_saved_once(self):
        import cv2

        frame = cv2.imread(str(FIXTURES / "qr_url.png"))
        scanner = QRScanner(duplicate_cooldown=5)
        fake = _FakeCapture(frame, frames=30)
        scanner.cap = fake
        scanner.is_running = True  # already started, so no real camera opens

        calls = []

        def callback(results):
            calls.append([r.data for r in results])
            if fake.remaining <= 0:
                scanner.is_running = False

        # Stop once the fake camera runs out of frames
        original_read = fake.read

        def read_and_stop():
            ok, f = original_read()
            if not ok:
                scanner.is_running = False
            return ok, f

        fake.read = read_and_stop

        results = scanner.scan_continuous(callback=callback)

        # Before the fix, 30 frames gave 30 results (one save per frame)
        assert [r.data for r in results] == ["https://example.com/test"]
        assert calls == [["https://example.com/test"]]
        assert fake.released


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
