"""
Tests for the desktop window (run without a screen using Qt's offscreen
platform). Skipped where PyQt5 is not installed, such as Termux.
"""

import os

import pytest

pytest.importorskip("PyQt5")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication, QMessageBox  # noqa: E402

from shared.config import Config  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def window(qapp, temp_db, monkeypatch):
    monkeypatch.setattr(Config, "DB_PATH", temp_db)
    # Never show real message boxes during tests
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: None)
    from desktop.ui.main_window import MainWindow

    win = MainWindow()
    yield win
    win.manager.close()


def _long_result(scan_id=1):
    return {
        "id": scan_id,
        "data": "https://example.com/" + "x" * 300,
        "format": "QRCODE",
        "timestamp": "2026-11-05T00:00:00",
    }


def test_copy_selected_copies_full_text(window, qapp):
    """Copy used to copy the table's 100-character preview"""
    window.on_scan_result(_long_result())
    window.results_table.selectRow(0)
    window.copy_selected()
    assert qapp.clipboard().text() == _long_result()["data"]


def test_clicking_a_cell_selects_the_row(window):
    """Copy needs a whole selected row; cells alone used to give 'No Selection'"""
    window.on_scan_result(_long_result())
    window.results_table.setCurrentCell(0, 2)
    assert len(window.results_table.selectionModel().selectedRows()) == 1


def test_table_shows_escaped_text(window):
    window.on_scan_result({"id": 1, "data": "a\x1bb", "format": "QRCODE", "timestamp": "t"})
    assert window.results_table.item(0, 1).text() == "a\\x1bb"


def test_filter_results(window):
    window.on_scan_result({"id": 1, "data": "github", "format": "QRCODE", "timestamp": "t"})
    window.on_scan_result({"id": 2, "data": "google", "format": "QRCODE", "timestamp": "t"})
    window.search_input.setText("git")
    assert window.results_table.rowCount() == 1
    assert window.results_table.item(0, 1).data(0x0100) == "github"
