"""
Camera worker thread for real-time frame capture and processing

Runs in separate thread to prevent UI blocking during scanning.
"""

import logging
import time

import cv2
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage

from shared.qr_scanner import QRScanner
from shared.data_manager import DataManager

logger = logging.getLogger(__name__)


class CameraWorker(QObject):
    """Worker thread for camera operations"""

    # QImage, not QPixmap: Qt does not allow QPixmap outside the GUI thread
    frame_ready = pyqtSignal(QImage)   # Emits processed frame for display
    scan_result = pyqtSignal(dict)     # Emits scan result dictionary
    error_occurred = pyqtSignal(str)   # Emits error message
    finished = pyqtSignal()            # Emitted when the loop has ended

    def __init__(self, scanner: QRScanner, manager: DataManager):
        super().__init__()
        self.scanner = scanner
        self.manager = manager
        self.is_running = False

    def run(self):
        """Main loop for camera worker"""
        try:
            self.is_running = True
            logger.info("CameraWorker starting main loop")

            while self.is_running:
                # Capture frame
                frame = self.scanner.capture_frame()
                if frame is None:
                    # No frame: wait a little instead of spinning the CPU
                    time.sleep(0.05)
                    continue

                # Scan for QR codes
                results = self.scanner.scan_frame(frame)

                # Draw every detection, but save each code only once per
                # duplicate cooldown (it was saved on every frame before)
                annotated_frame = self.scanner.draw_detections(frame, results)
                new_results = self.scanner.filter_new(results)

                # Emit frame for display
                self.frame_ready.emit(self._cv_to_qimage(annotated_frame))

                # Process and emit results
                for result in new_results:
                    # Save to database
                    scan_id = self.manager.save_scan(result)

                    if scan_id:
                        # Emit result dictionary
                        result_dict = result.to_dict()
                        result_dict['id'] = scan_id
                        self.scan_result.emit(result_dict)
                        logger.debug(f"Scan saved with ID {scan_id}")

        except Exception as e:
            logger.error(f"Error in CameraWorker: {e}")
            self.error_occurred.emit(str(e))

        finally:
            self.is_running = False
            logger.info("CameraWorker stopped")
            self.finished.emit()

    def stop(self):
        """Stop the camera worker"""
        self.is_running = False
        logger.info("CameraWorker stop requested")

    def _cv_to_qimage(self, cv_frame: np.ndarray) -> QImage:
        """Convert OpenCV frame to QImage for display"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)

            # Convert to QImage
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(
                rgb_frame.data,
                w, h,
                bytes_per_line,
                QImage.Format_RGB888
            )

            # copy(): the QImage above points into rgb_frame's memory, which
            # is freed when this function returns
            return qt_image.copy()

        except Exception as e:
            logger.error(f"Error converting frame to image: {e}")
            return QImage()
