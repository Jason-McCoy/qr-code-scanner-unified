"""
Configuration management for QR Code Scanner

Handles environment variables, default settings, and runtime configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

_BASE_DIR = Path(__file__).resolve().parent.parent


def _path_from_env(name: str, default: Path) -> Path:
    """
    Read a path setting from the environment.

    "~" is expanded, and a relative path (such as ./data in .env) is taken
    relative to the project folder rather than the folder the command was
    run from, so the database is in the same place however the app starts.
    """
    value = os.getenv(name)
    if not value:
        return default
    path = Path(value).expanduser()
    return path if path.is_absolute() else (_BASE_DIR / path)


class Config:
    """Application configuration container"""

    # Application metadata
    APP_NAME = "QR Code Scanner Unified"
    APP_VERSION = "1.0.0"

    # Paths
    BASE_DIR = _BASE_DIR
    DATA_DIR = _path_from_env("DATA_DIR", BASE_DIR / "data")
    DB_PATH = _path_from_env("DB_PATH", DATA_DIR / "qr_scanner.db")
    LOGS_DIR = _path_from_env("LOGS_DIR", BASE_DIR / "logs")

    # Scanning configuration
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", 0))
    SCAN_TIMEOUT = int(os.getenv("SCAN_TIMEOUT", 30))  # seconds
    MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", 0.5))
    # Seconds before the same code is reported again during continuous scanning
    DUPLICATE_COOLDOWN = float(os.getenv("DUPLICATE_COOLDOWN", 5))

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
            "duplicate_cooldown": cls.DUPLICATE_COOLDOWN,
            "auto_save": cls.AUTO_SAVE,
            "debug_mode": cls.DEBUG_MODE,
        }


# Ensure directories exist on import
Config.ensure_directories()
