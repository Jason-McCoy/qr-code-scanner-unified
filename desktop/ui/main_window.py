"""
Main window UI component

Provides the primary user interface with camera preview, scanning,
and results management.
"""

import logging
from typing import Optional, List
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QSplitter, QComboBox, QLineEdit, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal

from shared.config import Config
from shared.qr_scanner import QRScanner
from shared.data_manager import DataManager

from .camera import CameraWorker
from .handlers import EventHandler

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle(f"{Config.APP_NAME} v{Config.APP_VERSION}")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize components
        self.scanner = QRScanner()
        self.manager = DataManager()
        self.event_handler = EventHandler(self.manager)
        
        # Camera worker thread
        self.camera_thread = None
        self.camera_worker = None
        
        # Scanning state
        self.is_scanning = False
        self.scan_results = []
        
        logger.info("MainWindow initialized")
        
        # Build UI
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Build the user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left side: Camera preview and controls
        left_layout = QVBoxLayout()
        
        # Title
        title = QLabel("QR Code Scanner")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        left_layout.addWidget(title)
        
        # Camera preview label
        self.camera_label = QLabel()
        self.camera_label.setStyleSheet("border: 2px solid #cccccc; background-color: #000000;")
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setText("Camera Preview\n(Click 'Start Scanning' to begin)")
        left_layout.addWidget(self.camera_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Scanning")
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.start_button.clicked.connect(self.start_scanning)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Scanning")
        self.stop_button.setStyleSheet("background-color: #f44336; color: white; padding: 10px;")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_scanning)
        button_layout.addWidget(self.stop_button)
        
        self.clear_button = QPushButton("Clear Results")
        self.clear_button.setStyleSheet("background-color: #2196F3; color: white; padding: 10px;")
        self.clear_button.clicked.connect(self.clear_results)
        button_layout.addWidget(self.clear_button)
        
        left_layout.addLayout(button_layout)
        
        # Scan stats
        self.stats_label = QLabel(f"Scans: 0 | Format: All")
        self.stats_label.setStyleSheet("padding: 10px; background-color: #f5f5f5;")
        left_layout.addWidget(self.stats_label)
        
        # Right side: Results table and management
        right_layout = QVBoxLayout()
        
        # Results title
        results_title = QLabel("Scan Results")
        results_title_font = QFont()
        results_title_font.setPointSize(12)
        results_title_font.setBold(True)
        results_title.setFont(results_title_font)
        right_layout.addWidget(results_title)
        
        # Search/Filter
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by content...")
        self.search_input.textChanged.connect(self.filter_results)
        search_layout.addWidget(self.search_input)
        right_layout.addLayout(search_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["ID", "Data", "Format", "Timestamp"])
        self.results_table.setColumnWidth(0, 50)
        self.results_table.setColumnWidth(1, 400)
        self.results_table.setColumnWidth(2, 100)
        self.results_table.setColumnWidth(3, 200)
        self.results_table.itemSelectionChanged.connect(self.on_result_selected)
        right_layout.addWidget(self.results_table)
        
        # Export buttons
        export_layout = QHBoxLayout()
        
        self.export_json_button = QPushButton("Export JSON")
        self.export_json_button.clicked.connect(self.export_json)
        export_layout.addWidget(self.export_json_button)
        
        self.export_csv_button = QPushButton("Export CSV")
        self.export_csv_button.clicked.connect(self.export_csv)
        export_layout.addWidget(self.export_csv_button)
        
        self.copy_button = QPushButton("Copy Selected")
        self.copy_button.clicked.connect(self.copy_selected)
        export_layout.addWidget(self.copy_button)
        
        right_layout.addLayout(export_layout)
        
        # Add layouts to main
        splitter = QSplitter(Qt.Horizontal)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
    
    def _connect_signals(self):
        """Connect signal handlers"""
        pass
    
    def start_scanning(self):
        """Start camera and QR scanning"""
        try:
            logger.info("Starting scanner")
            
            if not self.scanner.start():
                QMessageBox.critical(self, "Error", "Failed to open camera")
                return
            
            self.is_scanning = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.camera_label.setText("Scanning...")
            
            # Start camera worker thread
            self.camera_thread = QThread()
            self.camera_worker = CameraWorker(self.scanner, self.manager)
            self.camera_worker.moveToThread(self.camera_thread)
            
            # Connect signals
            self.camera_worker.frame_ready.connect(self.on_frame_ready)
            self.camera_worker.scan_result.connect(self.on_scan_result)
            
            self.camera_thread.started.connect(self.camera_worker.run)
            self.camera_thread.start()
            
            logger.info("Scanner started successfully")
        
        except Exception as e:
            logger.error(f"Error starting scanner: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start scanner: {e}")
            self.is_scanning = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
    
    def stop_scanning(self):
        """Stop camera and QR scanning"""
        try:
            logger.info("Stopping scanner")
            
            self.is_scanning = False
            
            if self.camera_worker:
                self.camera_worker.stop()
            
            if self.camera_thread:
                self.camera_thread.quit()
                self.camera_thread.wait()
            
            self.scanner.stop()
            
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.camera_label.setText("Camera Preview\n(Click 'Start Scanning' to begin)")
            
            logger.info("Scanner stopped")
        
        except Exception as e:
            logger.error(f"Error stopping scanner: {e}")
    
    def on_frame_ready(self, pixmap: QPixmap):
        """Handle camera frame ready signal"""
        self.camera_label.setPixmap(pixmap.scaledToWidth(self.camera_label.width()))
    
    def on_scan_result(self, result_dict: dict):
        """Handle new scan result"""
        try:
            self.scan_results.append(result_dict)
            self.update_results_table()
            self.update_stats()
            logger.debug(f"Scan result received: {result_dict['data'][:50]}")
        
        except Exception as e:
            logger.error(f"Error handling scan result: {e}")
    
    def update_results_table(self):
        """Update the results table with current data"""
        self.results_table.setRowCount(len(self.scan_results))
        
        for row, result in enumerate(self.scan_results):
            # ID
            id_item = QTableWidgetItem(str(result.get('id', 'N/A')))
            self.results_table.setItem(row, 0, id_item)
            
            # Data
            data = result.get('data', '')[:100]
            data_item = QTableWidgetItem(data)
            self.results_table.setItem(row, 1, data_item)
            
            # Format
            format_item = QTableWidgetItem(result.get('format', 'N/A'))
            self.results_table.setItem(row, 2, format_item)
            
            # Timestamp
            timestamp = result.get('timestamp', 'N/A')
            timestamp_item = QTableWidgetItem(timestamp)
            self.results_table.setItem(row, 3, timestamp_item)
    
    def update_stats(self):
        """Update statistics display"""
        stats = self.manager.get_stats()
        self.stats_label.setText(
            f"Scans: {stats['total_scans']} | Formats: {', '.join(stats['formats']) if stats['formats'] else 'None'}"
        )
    
    def filter_results(self):
        """Filter results based on search input"""
        query = self.search_input.text()
        
        if not query:
            self.update_results_table()
            return
        
        filtered = [r for r in self.scan_results if query.lower() in r['data'].lower()]
        
        self.results_table.setRowCount(len(filtered))
        for row, result in enumerate(filtered):
            self.results_table.setItem(row, 0, QTableWidgetItem(str(result.get('id', 'N/A'))))
            self.results_table.setItem(row, 1, QTableWidgetItem(result.get('data', '')[:100]))
            self.results_table.setItem(row, 2, QTableWidgetItem(result.get('format', 'N/A')))
            self.results_table.setItem(row, 3, QTableWidgetItem(result.get('timestamp', 'N/A')))
    
    def on_result_selected(self):
        """Handle result selection in table"""
        pass
    
    def clear_results(self):
        """Clear all results"""
        reply = QMessageBox.question(
            self, 
            "Clear Results", 
            "Are you sure you want to clear all results?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.scan_results = []
            self.update_results_table()
            self.search_input.clear()
            logger.info("Results cleared")
    
    def export_json(self):
        """Export results to JSON"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Export to JSON",
                "",
                "JSON Files (*.json)"
            )
            
            if path:
                if self.manager.export_json(path):
                    QMessageBox.information(self, "Success", f"Exported to {path}")
                    logger.info(f"Exported JSON to {path}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to export JSON")
        
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            QMessageBox.critical(self, "Error", str(e))
    
    def export_csv(self):
        """Export results to CSV"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Export to CSV",
                "",
                "CSV Files (*.csv)"
            )
            
            if path:
                if self.manager.export_csv(path):
                    QMessageBox.information(self, "Success", f"Exported to {path}")
                    logger.info(f"Exported CSV to {path}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to export CSV")
        
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            QMessageBox.critical(self, "Error", str(e))
    
    def copy_selected(self):
        """Copy selected result to clipboard"""
        try:
            from PyQt5.QtWidgets import QApplication
            
            selected_rows = self.results_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "No Selection", "Please select a result to copy")
                return
            
            row = selected_rows[0].row()
            data = self.results_table.item(row, 1).text()
            
            clipboard = QApplication.clipboard()
            clipboard.setText(data)
            
            QMessageBox.information(self, "Success", "Copied to clipboard")
            logger.info(f"Copied to clipboard: {data[:50]}")
        
        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.is_scanning:
            self.stop_scanning()
        
        self.manager.close()
        logger.info("Application closed")
        event.accept()
