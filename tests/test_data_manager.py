"""
Unit tests for Data Manager module
"""

import pytest
import json
import tempfile
from pathlib import Path

from shared.data_manager import DataManager, QRCodeRecord
from shared.qr_scanner import ScanResult


class TestDataManager:
    """Tests for DataManager class"""
    
    def test_initialization(self, temp_db):
        """Test DataManager initialization"""
        manager = DataManager(db_path=temp_db)
        assert manager.db_path == temp_db
        assert manager.engine is not None
        assert manager.SessionLocal is not None
        manager.close()
    
    def test_save_scan(self, data_manager, sample_scan_result):
        """Test saving a single scan"""
        scan_id = data_manager.save_scan(sample_scan_result)
        
        assert scan_id is not None
        assert isinstance(scan_id, int)
    
    def test_save_scan_with_tags(self, data_manager, sample_scan_result):
        """Test saving scan with tags"""
        tags = ["github", "project"]
        scan_id = data_manager.save_scan(sample_scan_result, tags=tags)
        
        assert scan_id is not None
        
        # Retrieve and verify
        scan = data_manager.get_scan(scan_id)
        assert scan is not None
        assert set(scan["tags"]) == set(tags)
    
    def test_save_scan_with_notes(self, data_manager, sample_scan_result):
        """Test saving scan with notes"""
        notes = "This is a test note"
        scan_id = data_manager.save_scan(sample_scan_result, notes=notes)
        
        scan = data_manager.get_scan(scan_id)
        assert scan["notes"] == notes
    
    def test_get_scan(self, data_manager, sample_scan_result):
        """Test retrieving a scan"""
        scan_id = data_manager.save_scan(sample_scan_result)
        scan = data_manager.get_scan(scan_id)
        
        assert scan is not None
        assert scan["data"] == sample_scan_result.data
        assert scan["format"] == sample_scan_result.format
    
    def test_get_nonexistent_scan(self, data_manager):
        """Test retrieving non-existent scan"""
        scan = data_manager.get_scan(9999)
        assert scan is None
    
    def test_get_all_scans(self, data_manager, sample_scan_result):
        """Test retrieving all scans"""
        # Save multiple scans
        data_manager.save_scan(sample_scan_result)
        data_manager.save_scan(sample_scan_result)
        
        scans = data_manager.get_all_scans()
        assert len(scans) >= 2
    
    def test_get_all_scans_pagination(self, data_manager, sample_scan_result):
        """Test pagination in get_all_scans"""
        # Save multiple scans
        for _ in range(5):
            data_manager.save_scan(sample_scan_result)
        
        scans_page1 = data_manager.get_all_scans(limit=2, offset=0)
        scans_page2 = data_manager.get_all_scans(limit=2, offset=2)
        
        assert len(scans_page1) == 2
        assert len(scans_page2) == 2
        assert scans_page1[0]["id"] != scans_page2[0]["id"]
    
    def test_save_scans_batch(self, data_manager, sample_scan_result):
        """Test batch saving scans"""
        results = [sample_scan_result] * 3
        count = data_manager.save_scans_batch(results)
        
        assert count == 3
        
        all_scans = data_manager.get_all_scans()
        assert len(all_scans) >= 3
    
    def test_search_scans(self, data_manager):
        """Test searching scans"""
        result1 = ScanResult(data="https://github.com", format="QRCODE")
        result2 = ScanResult(data="https://google.com", format="QRCODE")
        
        data_manager.save_scan(result1)
        data_manager.save_scan(result2)
        
        results = data_manager.search_scans("github")
        assert len(results) >= 1
        assert any("github" in r["data"] for r in results)
    
    def test_search_scans_empty(self, data_manager, sample_scan_result):
        """Test search with no matches"""
        data_manager.save_scan(sample_scan_result)
        
        results = data_manager.search_scans("nonexistent123")
        assert len(results) == 0
    
    def test_get_stats(self, data_manager, sample_scan_result):
        """Test getting database statistics"""
        data_manager.save_scan(sample_scan_result)
        
        stats = data_manager.get_stats()
        assert "total_scans" in stats
        assert "formats" in stats
        assert "database_path" in stats
        assert stats["total_scans"] >= 1
    
    def test_export_json(self, data_manager, sample_scan_result):
        """Test exporting to JSON"""
        data_manager.save_scan(sample_scan_result)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            success = data_manager.export_json(output_path)
            assert success
            
            # Verify JSON file
            with open(output_path, 'r') as f:
                data = json.load(f)
                assert isinstance(data, list)
                assert len(data) >= 1
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    def test_export_csv(self, data_manager, sample_scan_result):
        """Test exporting to CSV"""
        data_manager.save_scan(sample_scan_result)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name
        
        try:
            success = data_manager.export_csv(output_path)
            assert success
            
            # Verify CSV file exists and has content
            with open(output_path, 'r') as f:
                content = f.read()
                assert len(content) > 0
                assert "id" in content or "data" in content
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    def test_clear_old_scans(self, data_manager, sample_scan_result):
        """Test clearing old scans"""
        data_manager.save_scan(sample_scan_result)
        
        # Clear scans older than 0 days (should not delete fresh scans)
        deleted = data_manager.clear_old_scans(days=0)
        assert deleted == 0
        
        # Clear scans older than 1 day (should not delete today's scans)
        deleted = data_manager.clear_old_scans(days=1)
        assert deleted == 0


class TestQRCodeRecord:
    """Tests for QRCodeRecord model"""
    
    def test_record_creation(self):
        """Test creating a QRCodeRecord"""
        record = QRCodeRecord(
            data="https://example.com",
            format="QRCODE",
        )
        assert record.data == "https://example.com"
        assert record.format == "QRCODE"
    
    def test_record_to_dict(self):
        """Test converting record to dict"""
        record = QRCodeRecord(
            data="test",
            format="QRCODE",
            tags="tag1,tag2",
        )
        d = record.to_dict()
        assert d["data"] == "test"
        assert d["format"] == "QRCODE"
        assert d["tags"] == ["tag1", "tag2"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
