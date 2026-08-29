"""
Reusable UI widgets and dialogs
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import pyqtSignal


class TagDialog(QDialog):
    """Dialog for adding tags to scan results"""
    
    tags_submitted = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Tags")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Enter tags (comma-separated):"))
        
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("e.g., github, project, important")
        layout.addWidget(self.tags_input)
        
        submit_button = QPushButton("Add Tags")
        submit_button.clicked.connect(self._on_submit)
        layout.addWidget(submit_button)
        
        self.setLayout(layout)
    
    def _on_submit(self):
        """Handle submit button click"""
        tags_text = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        self.tags_submitted.emit(tags)
        self.accept()
