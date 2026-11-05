"""
Core QR Code Scanner Module

Handles real-time QR code detection and processing using OpenCV and pyzbar.
Platform-agnostic implementation for desktop and mobile use.
"""

import logging
import time
from typing import Optional, List, Dict, Tuple
from datetime import datetime

import cv2
from pyzbar.pyzbar import decode
import numpy as np

from .config import Config
from .safety import safe_display

# Logging is configured by the entry points (desktop, android, scan_latest).
# A library module should not call logging.basicConfig(): doing so here
# took over the root logger before the apps could set up their log files,
# which left logs/android.log and logs/desktop.log empty.
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
        return (
            f"ScanResult(data={safe_display(self.data, 50)}, "
            f"format={self.format}, timestamp={self.timestamp})"
        )


class QRScanner:
    """
    High-performance QR code scanner

    Provides real-time scanning capabilities using OpenCV video capture
    and pyzbar for QR code decoding.
    """

    def __init__(self, camera_index: int = 0, duplicate_cooldown: Optional[float] = None,
                 camera_in_process: bool = False, camera_opener=None):
        """
        Initialize QR Scanner

        Args:
            camera_index: Index of the camera to use (default: 0)
            duplicate_cooldown: Seconds during which the same code is not
                reported again by continuous scanning. Defaults to
                Config.DUPLICATE_COOLDOWN. Use 0 to report every frame.
            camera_in_process: Open the camera in a separate process
                (shared/camera_process.py), so a read that hangs can be
                ended and the camera freed. Used by the desktop app.
            camera_opener: For tests: function that opens the camera
                inside that process instead of cv2.VideoCapture.
        """
        self.camera_index = camera_index
        self.camera_in_process = camera_in_process
        self.camera_opener = camera_opener
        self.cap = None
        self.is_running = False
        self.last_scan_time = None
        self.duplicate_cooldown = (
            Config.DUPLICATE_COOLDOWN if duplicate_cooldown is None else duplicate_cooldown
        )
        # (format, data) -> time.monotonic() when last seen, used to stop the
        # same code being saved once per video frame
        self._last_seen: Dict[Tuple[str, str], float] = {}
        # (format, data) -> time.monotonic() before which a code whose save
        # failed is not retried (see mark_failed())
        self._retry_at: Dict[Tuple[str, str], float] = {}

        logger.info(f"QRScanner initialized with camera index: {camera_index}")

    def start(self) -> bool:
        """
        Start the camera and scanner

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Camera properties for better performance
            props = [
                (cv2.CAP_PROP_FRAME_WIDTH, 1280),
                (cv2.CAP_PROP_FRAME_HEIGHT, 720),
                (cv2.CAP_PROP_FPS, 30),
                (cv2.CAP_PROP_AUTOFOCUS, 1),
            ]
            if self.camera_in_process:
                from .camera_process import ProcessCapture
                self.cap = ProcessCapture(
                    self.camera_index, props,
                    open_timeout=Config.CAMERA_OPEN_TIMEOUT,
                    read_timeout=Config.CAMERA_READ_TIMEOUT,
                    opener=self.camera_opener,
                )
            else:
                self.cap = cv2.VideoCapture(self.camera_index)
                for prop, value in props:
                    self.cap.set(prop, value)

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
                    # zbar returns UTF-8; replace any invalid bytes instead of
                    # dropping the whole code
                    data = obj.data.decode("utf-8", errors="replace")
                    format_type = obj.type

                    # Create result object
                    result = ScanResult(
                        data=data,
                        format=format_type,
                        rect=(obj.rect.left, obj.rect.top, obj.rect.width, obj.rect.height),
                    )

                    results.append(result)
                    logger.debug(f"QR Code detected: {safe_display(data, 50)}")

                except Exception as e:
                    logger.warning(f"Error processing detected QR code: {e}")
                    continue

            self.last_scan_time = datetime.now()

        except Exception as e:
            logger.error(f"Error scanning frame: {e}")

        return results

    def filter_new(
        self, results: List[ScanResult], now: Optional[float] = None
    ) -> List[ScanResult]:
        """
        Drop results already seen within the duplicate cooldown.

        A camera sees the same QR code in every frame (about 30 times a
        second), so without this filter one code held in front of the
        camera for two seconds was saved about 60 times.

        Args:
            results: Results from scan_frame()
            now: Current time from time.monotonic() (for tests)

        Two codes count as the same only when both the format (QRCODE,
        EAN13, ...) and the exact text match. A code that stays in view
        keeps counting as seen; once it has been out of view for the
        cooldown, it is reported again.

        Args:
            results: Results from scan_frame()
            now: Current time from time.monotonic() (for tests)

        Returns:
            List[ScanResult]: Results not seen within the cooldown
        """
        now = time.monotonic() if now is None else now
        fresh = []
        for result in results:
            key = (result.format, result.data)

            # A code whose save failed is retried once its short retry
            # delay has passed, even if it never left view
            retry_at = self._retry_at.get(key)
            if retry_at is not None:
                if now < retry_at:
                    continue
                del self._retry_at[key]
                last = None
            else:
                last = self._last_seen.get(key)

            if self.duplicate_cooldown <= 0:
                fresh.append(result)
                continue

            # Refresh the time even for duplicates, so a code that stays in
            # view is reported once, not once per cooldown period
            self._last_seen[key] = now
            if last is None or (now - last) >= self.duplicate_cooldown:
                fresh.append(result)

        # Keep memory bounded during long sessions
        if len(self._last_seen) > 1000:
            cutoff = now - self.duplicate_cooldown
            self._last_seen = {k: t for k, t in self._last_seen.items() if t >= cutoff}

        return fresh

    def mark_failed(
        self, result: ScanResult, retry_after: Optional[float] = None, now: Optional[float] = None
    ):
        """
        Record that saving a reported code failed, so it is not treated as
        done.

        Without this, a code whose database write failed counted as seen
        and was not tried again while it stayed in view. After this call
        the code is reported again by filter_new() once retry_after seconds
        have passed (a short delay, so a database that keeps failing is
        not retried on every frame). retry_after defaults to
        Config.SAVE_RETRY_DELAY (1 second).
        """
        now = time.monotonic() if now is None else now
        if retry_after is None:
            retry_after = Config.SAVE_RETRY_DELAY
        key = (result.format, result.data)
        self._last_seen.pop(key, None)
        self._retry_at[key] = now + retry_after

    def reset_duplicates(self):
        """Forget which codes have been seen, so they are reported again"""
        self._last_seen.clear()
        self._retry_at.clear()

    def scan_continuous(self, callback=None, duration: Optional[int] = None) -> List[ScanResult]:
        """
        Continuously scan for QR codes until stopped

        Args:
            callback: Optional callback function(results) called on each detection
            duration: Optional maximum scanning duration in seconds

        Returns:
            List[ScanResult]: All scanned codes during session (each code
            once per duplicate cooldown, see filter_new())
        """
        if not self.is_running and not self.start():
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
                    # Camera gave no frame: wait a little instead of
                    # spinning the CPU at 100%
                    time.sleep(0.05)
                    continue

                results = self.filter_new(self.scan_frame(frame))

                if results:
                    all_results.extend(results)
                    if callback:
                        callback(results)

                # Small delay to prevent CPU spinning. This used
                # cv2.waitKey(1), which raises cv2.error on OpenCV builds
                # without a GUI (opencv-python-headless and similar).
                time.sleep(0.005)

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
                # Draw text (control characters escaped, kept on screen)
                text = safe_display(result.data, 30)
                cv2.putText(
                    annotated,
                    text,
                    (x, max(y - 10, 12)),
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
