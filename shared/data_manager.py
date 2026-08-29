"""
Data Management Module

Handles persistence, retrieval, and export of scanned QR codes using SQLite.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, DateTime, LargeBinary, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from .config import Config
from .qr_scanner import ScanResult

logger = logging.getLogger(__name__)

Base = declarative_base()


class QRCodeRecord(Base):
    """SQLAlchemy model for storing QR code scans"""
    
    __tablename__ = "qr_codes"
    
    id = Column(Integer, primary_key=True)
    data = Column(String(2048), nullable=False, index=True)
    format = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.now)
    image_data = Column(LargeBinary, nullable=True)
    rect_info = Column(String(100), nullable=True)  # JSON string (x,y,w,h)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    notes = Column(Text, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "data": self.data,
            "format": self.format,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags.split(",") if self.tags else [],
            "notes": self.notes,
        }
    
    def __repr__(self) -> str:
        return f"QRCodeRecord(id={self.id}, data={self.data[:50]}..., timestamp={self.timestamp})"


class DataManager:
    """
    Manages QR code data persistence and retrieval
    
    Provides high-level interface for saving, loading, filtering, and exporting scans.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Data Manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or str(Config.DB_PATH)
        self.engine = None
        self.SessionLocal = None
        
        self._initialize_database()
        logger.info(f"DataManager initialized with database: {self.db_path}")
    
    def _initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            # Create engine
            self.engine = create_engine(
                f"sqlite:///{self.db_path}",
                connect_args={"timeout": Config.DB_TIMEOUT},
                pool_size=Config.DB_POOL_SIZE,
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(bind=self.engine)
            
            # Create all tables
            Base.metadata.create_all(self.engine)
            
            logger.info("Database initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def save_scan(
        self,
        result: ScanResult,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> Optional[int]:
        """
        Save a scan result to database
        
        Args:
            result: ScanResult object
            tags: Optional list of tags
            notes: Optional notes/description
        
        Returns:
            int: ID of saved record or None if failed
        """
        session = self.get_session()
        
        try:
            record = QRCodeRecord(
                data=result.data,
                format=result.format,
                timestamp=result.timestamp,
                image_data=result.image_data,
                rect_info=json.dumps(result.rect) if result.rect else None,
                tags=",".join(tags) if tags else None,
                notes=notes,
            )
            
            session.add(record)
            session.commit()
            record_id = record.id
            
            logger.info(f"Scan saved with ID {record_id}: {result.data[:50]}...")
            return record_id
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving scan: {e}")
            return None
        
        finally:
            session.close()
    
    def save_scans_batch(self, results: List[ScanResult]) -> int:
        """
        Save multiple scan results in batch
        
        Args:
            results: List of ScanResult objects
        
        Returns:
            int: Number of records saved
        """
        session = self.get_session()
        count = 0
        
        try:
            for result in results:
                record = QRCodeRecord(
                    data=result.data,
                    format=result.format,
                    timestamp=result.timestamp,
                    image_data=result.image_data,
                    rect_info=json.dumps(result.rect) if result.rect else None,
                )
                session.add(record)
                count += 1
            
            session.commit()
            logger.info(f"Batch saved {count} scans")
            return count
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error batch saving scans: {e}")
            return count
        
        finally:
            session.close()
    
    def get_scan(self, scan_id: int) -> Optional[Dict]:
        """
        Retrieve a specific scan by ID
        
        Args:
            scan_id: ID of scan record
        
        Returns:
            Dict with scan data or None
        """
        session = self.get_session()
        
        try:
            record = session.query(QRCodeRecord).filter(QRCodeRecord.id == scan_id).first()
            return record.to_dict() if record else None
        
        finally:
            session.close()
    
    def get_all_scans(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Retrieve all scans with pagination
        
        Args:
            limit: Maximum number of records
            offset: Number of records to skip
        
        Returns:
            List of scan dictionaries
        """
        session = self.get_session()
        
        try:
            records = (
                session.query(QRCodeRecord)
                .order_by(QRCodeRecord.timestamp.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )
            return [r.to_dict() for r in records]
        
        finally:
            session.close()
    
    def search_scans(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search scans by data content
        
        Args:
            query: Search query string
            limit: Maximum results
        
        Returns:
            List of matching scan dictionaries
        """
        session = self.get_session()
        
        try:
            records = (
                session.query(QRCodeRecord)
                .filter(QRCodeRecord.data.contains(query))
                .order_by(QRCodeRecord.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [r.to_dict() for r in records]
        
        finally:
            session.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        session = self.get_session()
        
        try:
            total_scans = session.query(QRCodeRecord).count()
            formats = (
                session.query(QRCodeRecord.format).distinct().all()
            )
            
            return {
                "total_scans": total_scans,
                "formats": [f[0] for f in formats],
                "database_path": self.db_path,
            }
        
        finally:
            session.close()
    
    def export_json(self, output_path: str, limit: int = 1000) -> bool:
        """
        Export scans to JSON file
        
        Args:
            output_path: Path to save JSON file
            limit: Maximum records to export
        
        Returns:
            bool: Success status
        """
        try:
            scans = self.get_all_scans(limit=limit)
            
            with open(output_path, "w") as f:
                json.dump(scans, f, indent=2)
            
            logger.info(f"Exported {len(scans)} scans to {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            return False
    
    def export_csv(self, output_path: str, limit: int = 1000) -> bool:
        """
        Export scans to CSV file
        
        Args:
            output_path: Path to save CSV file
            limit: Maximum records to export
        
        Returns:
            bool: Success status
        """
        try:
            import csv
            
            scans = self.get_all_scans(limit=limit)
            
            if not scans:
                logger.warning("No scans to export")
                return False
            
            with open(output_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=scans[0].keys())
                writer.writeheader()
                writer.writerows(scans)
            
            logger.info(f"Exported {len(scans)} scans to {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return False
    
    def clear_old_scans(self, days: int = 30) -> int:
        """
        Delete scans older than specified days
        
        Args:
            days: Age threshold in days
        
        Returns:
            int: Number of records deleted
        """
        from datetime import timedelta
        
        session = self.get_session()
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted = (
                session.query(QRCodeRecord)
                .filter(QRCodeRecord.timestamp < cutoff_date)
                .delete()
            )
            session.commit()
            
            logger.info(f"Deleted {deleted} scans older than {days} days")
            return deleted
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error clearing old scans: {e}")
            return 0
        
        finally:
            session.close()
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
