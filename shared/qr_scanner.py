"""
Core QR Code Scanner Module

Handles real-time QR code detection and processing using OpenCV and pyzbar.
Platform-agnostic implementation for desktop and mobile use.
"""

import logging
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from pathlib import Path

import cv2
from pyzbar.pyzbar import decode, Decoded
from PIL import Image
import numpy as np

from .config import Config

# Configure logging
logging.basicConfig(level=logging.INFO if Config.ENABLE_LOGGING else logging.WARNING)
logger = logging.getLogger(__name__)


class ScanResult:
    """Represents a single QR code scan result"""
    
    def __init__(
        self,
        data: str,
        format: str,
        timestamp: Optional[datetime] = None,
        image_data: Optional[bytes] = None,
        rect: Optional[Tuple[int, int, int, int]] = None,
    ):
        self.data = data
        self.format = format
        self.timestamp = timestamp or datetime.now()
        self.image_data = image_data
        self.rect = rect  # (x, y, width, height)
        self.id = None  # Set by database
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            "data": self.data,
            "format": self.format,
            "timestamp": self.timestamp.isoformat(),
            "rect": self.rect,
        }
    
    def __repr__(self) -> str:
        return f"ScanResult(data={self.data[:50]}..., format={self.format}, timestamp={self.timestamp})"


class QRScanner:
    """
    High-performance QR code scanner
    
    Provides real-time scanning capabilities using OpenCV video capture
    and pyzbar for QR code decoding.
    """
    
    def __init__(self, camera_index: int = 0):
        """
        Initialize QR Scanner
        
        Args:
            camera_index: Index of the camera to use (default: 0)
        """
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False
        self.last_scan_time = None
        self.scanned_codes = set()  # Track seen codes to prevent duplicates
        
        logger.info(f"QRScanner initialized with camera index: {camera_index}")
    
    def start(self) -> bool:
        """
        Start the camera and scanner
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            
            if not self.cap.isOpened():
                logger.error("Failed to open camera")
                return False
            
            self.is_running = True
            logger.info("Scanner started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error starting scanner: {e}")
            return False
    
    def stop(self):
        """Stop the camera and scanner"""
        if self.cap is not None:
            self.cap.release()
        self.is_running = False
        logger.info("Scanner stopped")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from camera
        
        Returns:
            np.ndarray: Frame data or None if capture failed
        """
        if not self.is_running or self.cap is None:
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("Failed to capture frame")
            return None
        
        return frame
    
    def scan_frame(self, frame: np.ndarray) -> List[ScanResult]:
        """
        Scan a single frame for QR codes
        
        Args:
            frame: OpenCV frame (numpy array)
        
        Returns:
            List[ScanResult]: List of detected QR codes
        """
        results = []
        
        try:
            # Decode QR codes from frame
            decoded_objects = decode(frame)
            
            if not decoded_objects:
                return results
            
            for obj in decoded_objects:
                try:
                    data = obj.data.decode("utf-8")
                    format_type = obj.type
                    
                    # Create result object
                    result = ScanResult(
                        data=data,
                        format=format_type,
                        rect=(obj.rect.left, obj.rect.top, obj.rect.width, obj.rect.height),
                    )
                    
                    results.append(result)
                    logger.debug(f"QR Code detected: {data[:50]}...")
                
                except Exception as e:
                    logger.warning(f"Error processing detected QR code: {e}")
                    continue
            
            self.last_scan_time = datetime.now()
        
        except Exception as e:
            logger.error(f"Error scanning frame: {e}")
        
        return results
    
    def scan_continuous(self, callback=None, duration: Optional[int] = None) -> List[ScanResult]:
        """
        Continuously scan for QR codes until stopped
        
        Args:
            callback: Optional callback function(results) called on each detection
            duration: Optional maximum scanning duration in seconds
        
        Returns:
            List[ScanResult]: All scanned codes during session
        """
        if not self.start():
            return []
        
        all_results = []
        start_time = datetime.now()
        
        try:
            while self.is_running:
                # Check duration limit
                if duration:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > duration:
                        logger.info(f"Scan duration limit reached ({duration}s)")
                        break
                
                # Capture and scan
                frame = self.capture_frame()
                if frame is None:
                    continue
                
                results = self.scan_frame(frame)
                
                if results:
                    all_results.extend(results)
                    if callback:
                        callback(results)
                
                # Small delay to prevent CPU spinning
                cv2.waitKey(1)
        
        except KeyboardInterrupt:
            logger.info("Scanning interrupted by user")
        
        finally:
            self.stop()
        
        return all_results
    
    def scan_image_file(self, image_path: str) -> List[ScanResult]:
        """
        Scan a QR code from an image file
        
        Args:
            image_path: Path to image file
        
        Returns:
            List[ScanResult]: Detected QR codes
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return []
            
            return self.scan_frame(image)
        
        except Exception as e:
            logger.error(f"Error scanning image file: {e}")
            return []
    
    def draw_detections(self, frame: np.ndarray, results: List[ScanResult]) -> np.ndarray:
        """
        Draw QR code detections on frame
        
        Args:
            frame: OpenCV frame
            results: List of scan results
        
        Returns:
            np.ndarray: Frame with annotations
        """
        annotated = frame.copy()
        
        for result in results:
            if result.rect:
                x, y, w, h = result.rect
                # Draw rectangle
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Draw text
                text = result.data[:30] + "..." if len(result.data) > 30 else result.data
                cv2.putText(
                    annotated,
                    text,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )
        
        return annotated
    
    def get_status(self) -> Dict:
        """Get current scanner status"""
        return {
            "is_running": self.is_running,
            "camera_index": self.camera_index,
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
        }


class QRScannerFactory:
    """Factory for creating QR scanner instances"""
    
    _instance = None
    
    @classmethod
    def get_scanner(cls, camera_index: int = 0) -> QRScanner:
        """Get or create QR scanner instance (singleton pattern)"""
        if cls._instance is None:
            cls._instance = QRScanner(camera_index)
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset singleton instance"""
        if cls._instance:
            cls._instance.stop()
        cls._instance = None
