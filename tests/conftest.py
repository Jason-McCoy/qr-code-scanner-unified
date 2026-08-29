"""
Test configuration and fixtures
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import Config
from shared.data_manager import DataManager


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield str(db_path)


@pytest.fixture
def data_manager(temp_db):
    """Create DataManager instance with temporary database"""
    manager = DataManager(db_path=temp_db)
    yield manager
    manager.close()


@pytest.fixture
def sample_scan_result():
    """Create a sample scan result for testing"""
    from shared.qr_scanner import ScanResult
    
    return ScanResult(
        data="https://github.com/Jason-McCoy/qr-code-scanner-unified",
        format="QRCODE",
        rect=(100, 100, 200, 200),
    )
