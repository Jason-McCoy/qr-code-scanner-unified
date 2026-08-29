"""
Event handlers for desktop application

Manages user interactions and business logic triggers.
"""

import logging
from typing import Optional
from datetime import datetime

from shared.data_manager import DataManager
from shared.qr_scanner import ScanResult

logger = logging.getLogger(__name__)


class EventHandler:
    """Handles application events and callbacks"""
    
    def __init__(self, manager: DataManager):
        """
        Initialize EventHandler
        
        Args:
            manager: DataManager instance for persistence
        """
        self.manager = manager
    
    def on_scan_detected(self, result: ScanResult, tags: Optional[list] = None):
        """Handle QR code detection event"""
        try:
            scan_id = self.manager.save_scan(result, tags=tags)
            logger.info(f"Scan saved: {result.data[:50]}... (ID: {scan_id})")
            return scan_id
        
        except Exception as e:
            logger.error(f"Error handling scan detection: {e}")
            return None
    
    def on_export_requested(self, format_type: str, output_path: str) -> bool:
        """Handle export request event"""
        try:
            if format_type == "json":
                success = self.manager.export_json(output_path)
            elif format_type == "csv":
                success = self.manager.export_csv(output_path)
            else:
                logger.warning(f"Unsupported export format: {format_type}")
                return False
            
            if success:
                logger.info(f"Exported {format_type.upper()} to {output_path}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error exporting {format_type}: {e}")
            return False
    
    def on_search_requested(self, query: str) -> list:
        """Handle search request event"""
        try:
            results = self.manager.search_scans(query)
            logger.info(f"Search for '{query}' returned {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def on_clear_requested(self) -> bool:
        """Handle clear all scans request"""
        try:
            logger.warning("Clear all scans requested (no action taken in handler)")
            return True
        
        except Exception as e:
            logger.error(f"Error in clear handler: {e}")
            return False
