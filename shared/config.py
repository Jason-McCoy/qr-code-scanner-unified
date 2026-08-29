"""
Configuration management for QR Code Scanner

Handles environment variables, default settings, and runtime configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration container"""

    # Application metadata
    APP_NAME = "QR Code Scanner Unified"
    APP_VERSION = "1.0.0"
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
    DB_PATH = Path(os.getenv("DB_PATH", DATA_DIR / "qr_scanner.db"))
    LOGS_DIR = Path(os.getenv("LOGS_DIR", BASE_DIR / "logs"))
    
    # Scanning configuration
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", 0))
    SCAN_TIMEOUT = int(os.getenv("SCAN_TIMEOUT", 30))  # seconds
    MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", 0.5))
    
    # Image processing
    IMAGE_QUALITY = int(os.getenv("IMAGE_QUALITY", 95))
    MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", 2048))  # pixels
    
    # Database
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 5))
    DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", 10))  # seconds
    
    # Feature flags
    AUTO_SAVE = os.getenv("AUTO_SAVE", "true").lower() == "true"
    ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    # Export formats
    EXPORT_FORMATS = ["csv", "json", "txt", "pdf"]
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def to_dict(cls):
        """Return configuration as dictionary"""
        return {
            "app_name": cls.APP_NAME,
            "app_version": cls.APP_VERSION,
            "data_dir": str(cls.DATA_DIR),
            "db_path": str(cls.DB_PATH),
            "camera_index": cls.CAMERA_INDEX,
            "scan_timeout": cls.SCAN_TIMEOUT,
            "auto_save": cls.AUTO_SAVE,
            "debug_mode": cls.DEBUG_MODE,
        }


# Ensure directories exist on import
Config.ensure_directories()
