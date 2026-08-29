"""
Camera worker thread for real-time frame capture and processing

Runs in separate thread to prevent UI blocking during scanning.
"""

import logging
from typing import Optional

import cv2
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage

from shared.qr_scanner import QRScanner
from shared.data_manager import DataManager

logger = logging.getLogger(__name__)


class CameraWorker(QObject):
    """Worker thread for camera operations"""
    
    frame_ready = pyqtSignal(QPixmap)  # Emits processed frame for display
    scan_result = pyqtSignal(dict)     # Emits scan result dictionary
    error_occurred = pyqtSignal(str)   # Emits error message
    
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
                    continue
                
                # Scan for QR codes
                results = self.scanner.scan_frame(frame)
                
                # Draw detections on frame
                annotated_frame = self.scanner.draw_detections(frame, results)
                
                # Emit frame for display
                pixmap = self._cv_to_pixmap(annotated_frame)
                self.frame_ready.emit(pixmap)
                
                # Process and emit results
                for result in results:
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
    
    def stop(self):
        """Stop the camera worker"""
        self.is_running = False
        logger.info("CameraWorker stop requested")
    
    def _cv_to_pixmap(self, cv_frame: np.ndarray) -> QPixmap:
        """Convert OpenCV frame to QPixmap for display"""
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
            
            # Convert to QPixmap
            return QPixmap.fromImage(qt_image)
        
        except Exception as e:
            logger.error(f"Error converting frame to pixmap: {e}")
            return QPixmap()
