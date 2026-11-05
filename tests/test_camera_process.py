"""
Camera in a separate process (shared/camera_process.py): a read that never
returns must not keep the camera held. See record section 10.

The hanging camera is simulated (tests/fake_cameras.py). No real camera
was used.
"""

import os
import time

import pytest
from PyQt5.QtWidgets import QApplication

from shared.camera_process import CameraTimeout, ProcessCapture
from tests import fake_cameras


@pytest.fixture
def marker(tmp_path, monkeypatch):
    path = tmp_path / "released.txt"
    monkeypatch.setenv("FAKE_CAMERA_MARKER", str(path))  # inherited by the child
    return path


def test_working_camera_reads_and_stops_cleanly(marker):
    cap = ProcessCapture(0, open_timeout=20, read_timeout=5, opener=fake_cameras.working)
    assert cap.isOpened()
    ok, frame = cap.read()
    assert ok and frame.shape == (720, 1280, 3)
    cap.release()
    assert cap.exitcode == 0          # stopped on request, not killed
    assert marker.read_text() == "released"


def test_hanging_read_ends_process_and_frees_camera(marker):
    cap = ProcessCapture(0, open_timeout=20, read_timeout=1, opener=fake_cameras.hanging_read)
    assert cap.isOpened()
    proc = cap._proc
    t0 = time.monotonic()
    with pytest.raises(CameraTimeout):
        cap.read()
    elapsed = time.monotonic() - t0
    assert elapsed < 3, elapsed
    assert not proc.is_alive()        # process ended, so the OS frees the camera
    assert cap.exitcode not in (None, 0)
    assert not marker.exists()        # release() never ran: it was stuck in read()
    assert cap.read() == (False, None)
    cap.release()                     # second release is harmless


def test_hanging_open_gives_up(marker):
    t0 = time.monotonic()
    cap = ProcessCapture(0, open_timeout=1, read_timeout=1, opener=fake_cameras.hanging_open)
    assert time.monotonic() - t0 < 4
    assert not cap.isOpened()
    assert cap.exitcode not in (None, 0)
    assert cap.read() == (False, None)


def test_desktop_stop_with_hanging_read(marker, monkeypatch, tmp_path):
    """The window: a hanging read ends with an error, the camera process is
    ended and Start can be used again, all without the app aborting."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    from shared.config import Config
    from desktop.ui import main_window as mw

    monkeypatch.setattr(Config, "CAMERA_READ_TIMEOUT", 1.0)
    monkeypatch.setattr(Config, "CAMERA_OPEN_TIMEOUT", 20.0)
    errors = []
    monkeypatch.setattr(mw.QMessageBox, "critical", lambda *a: errors.append(a[2]))
    monkeypatch.setattr(Config, "DB_PATH", tmp_path / "t.db")

    window = mw.MainWindow()
    window.scanner.camera_in_process = True
    window.scanner.camera_opener = fake_cameras.hanging_read
    window.start_scanning()
    assert window.is_scanning
    proc = window.scanner.cap._proc

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and (proc.is_alive() or window.is_scanning):
        app.processEvents()
        time.sleep(0.05)

    assert not proc.is_alive()
    assert not window.is_scanning
    assert window.start_button.isEnabled()
    assert errors and "stopped responding" in errors[0]
    window.close()
