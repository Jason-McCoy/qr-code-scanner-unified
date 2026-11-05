"""
Tests that the documented commands start, and that the Termux photo
scanner (android/scan_latest.py) works end to end on real QR images.

These run the commands in a separate Python process, with DATA_DIR and
LOGS_DIR pointed at a temporary folder so no real data is touched.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).parent / "fixtures"


def _run(args, tmp_path, timeout=60):
    env = dict(os.environ)
    env["DATA_DIR"] = str(tmp_path / "data")
    env["LOGS_DIR"] = str(tmp_path / "logs")
    env.pop("DB_PATH", None)
    env["QT_QPA_PLATFORM"] = "offscreen"
    return subprocess.run(
        [sys.executable] + args,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@pytest.mark.parametrize(
    "args",
    [
        ["android/scan_latest.py"],
        ["-m", "android.scan_latest"],
    ],
)
def test_scan_latest_both_ways_of_starting(args, tmp_path):
    proc = _run(args + [str(FIXTURES / "qr_url.png")], tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "[QRCODE] https://example.com/test" in proc.stdout
    assert "Saved 1 code(s)" in proc.stdout
    # Quiet by default: no INFO log lines on screen
    assert "INFO" not in proc.stdout + proc.stderr


def test_scan_latest_skips_already_scanned(tmp_path):
    image = str(FIXTURES / "qr_url.png")
    assert _run(["-m", "android.scan_latest", image], tmp_path).returncode == 0
    second = _run(["-m", "android.scan_latest", image], tmp_path)
    assert second.returncode == 0
    assert "Already scanned" in second.stdout
    forced = _run(["-m", "android.scan_latest", "--force", image], tmp_path)
    assert "Saved 1 code(s)" in forced.stdout


def test_scan_latest_escapes_terminal_control_codes(tmp_path):
    """A QR code must not be able to clear the screen or retitle the terminal"""
    proc = _run(["-m", "android.scan_latest", str(FIXTURES / "qr_escape.png")], tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "\x1b" not in proc.stdout
    assert "\x07" not in proc.stdout
    assert "HELLO\\x1b[2J\\x1b]0;pwned\\x07=cmd" in proc.stdout


def test_scan_latest_no_image(tmp_path):
    env_dir = tmp_path / "empty"
    env_dir.mkdir()
    proc = _run(["-m", "android.scan_latest", str(env_dir / "missing.jpg")], tmp_path)
    assert proc.returncode == 1
    assert "No image found" in proc.stdout


@pytest.mark.parametrize(
    "module",
    ["android.qr_scanner_android", "desktop.qr_scanner_desktop", "android.scan_latest"],
)
def test_modules_import_without_side_effects(module, tmp_path):
    """Importing an entry point must not start anything or write log files"""
    proc = _run(["-c", f"import {module}"], tmp_path)
    if "No module named 'PyQt5'" in proc.stderr:
        pytest.skip("PyQt5 not installed")
    assert proc.returncode == 0, proc.stderr
    assert not (tmp_path / "logs" / "android.log").exists()
    assert not (tmp_path / "logs" / "desktop.log").exists()


def test_desktop_script_path_finds_shared(tmp_path):
    """
    'python desktop/qr_scanner_desktop.py' used to fail with
    ModuleNotFoundError: No module named 'shared'. Check the imports it
    needs resolve when started that way (without opening a window).
    """
    pytest.importorskip("PyQt5")
    code = (
        "import runpy, sys; sys.argv=['desktop/qr_scanner_desktop.py'];"
        "g = runpy.run_path('desktop/qr_scanner_desktop.py', run_name='not_main');"
        "from desktop.ui.main_window import MainWindow; print('ok')"
    )
    proc = _run(["-c", code], tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert "ok" in proc.stdout
