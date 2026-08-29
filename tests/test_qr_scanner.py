"""
Unit tests for QR Scanner module
"""

import pytest
import numpy as np
from shared.qr_scanner import ScanResult, QRScanner


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
