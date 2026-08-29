"""
Android storage integration for Pydroid 3

Handles file storage and data persistence on Android devices.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AndroidStorage:
    """Android storage wrapper for Pydroid 3"""
    
    # Standard Android storage paths
    DOCUMENTS = Path.home() / "Documents"
    DOWNLOADS = Path.home() / "Downloads"
    APP_DATA = Path.home() / ".local" / "share" / "qr-scanner"
    
    def __init__(self):
        """Initialize Android storage"""
        self._ensure_directories()
        logger.info("AndroidStorage initialized")
    
    def _ensure_directories(self):
        """Create necessary directories"""
        try:
            self.APP_DATA.mkdir(parents=True, exist_ok=True)
            logger.info(f"App data directory: {self.APP_DATA}")
        
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
    
    def get_data_path(self) -> Path:
        """Get app data directory path"""
        return self.APP_DATA
    
    def save_file(self, filename: str, content: bytes, location: str = "app") -> Optional[Path]:
        """
        Save file to storage
        
        Args:
            filename: Name of file
            content: File content (bytes)
            location: Storage location ("app", "downloads", "documents")
        
        Returns:
            Path to saved file or None
        """
        try:
            if location == "downloads":
                target_dir = self.DOWNLOADS
            elif location == "documents":
                target_dir = self.DOCUMENTS
            else:
                target_dir = self.APP_DATA
            
            target_dir.mkdir(parents=True, exist_ok=True)
            file_path = target_dir / filename
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"File saved: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return None
    
    def read_file(self, file_path: Path) -> Optional[bytes]:
        """
        Read file from storage
        
        Args:
            file_path: Path to file
        
        Returns:
            File content or None
        """
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return None
