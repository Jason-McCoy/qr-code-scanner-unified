"""
Shared QR Code Scanner Core Module

This module provides the core scanning, data management, and configuration
functionality used by both desktop and Android implementations.
"""

from .qr_scanner import QRScanner
from .data_manager import DataManager
from .config import Config

__version__ = "1.0.0"
__all__ = ["QRScanner", "DataManager", "Config"]
