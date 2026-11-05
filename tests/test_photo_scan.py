"""
Photo files (android/scan_latest.py): a large phone photo of a QR code shown
on a screen. zbar finds nothing in the full-size photo, so scan_image_file()
retries on smaller and black-and-white copies. See record section 14.

Fixture: a crop of Jason's photo (taken on his phone on November 4, 2026)
of a Wikipedia sample QR code on a phone screen, EXIF removed.
"""

from pathlib import Path

import cv2
import numpy as np
from pyzbar.pyzbar import decode

from shared.qr_scanner import QRScanner

FIXTURE = Path(__file__).parent / "fixtures" / "photo_screen_qr.jpg"


def test_fixture_defeats_plain_zbar():
    # Keeps the test honest: if zbar ever reads it directly, this fixture no
    # longer exercises the fallback
    assert decode(cv2.imread(str(FIXTURE))) == []


def test_photo_of_screen_is_decoded():
    results = QRScanner().scan_image_file(str(FIXTURE))
    assert [(r.format, r.data) for r in results] == [("QRCODE", "http://en.m.wikipedia.org")]


def test_fallback_rect_is_in_original_pixels():
    image = cv2.imread(str(FIXTURE))
    (result,) = QRScanner().scan_image_file(str(FIXTURE))
    x, y, w, h = result.rect
    assert 0 <= x < image.shape[1] and 0 <= y < image.shape[0]
    assert w > image.shape[1] * 0.5  # the code fills most of the crop


def test_clean_image_still_uses_first_pass(monkeypatch):
    called = []
    monkeypatch.setattr(
        QRScanner, "_scan_photo_fallbacks", lambda self, img: called.append(1) or []
    )
    results = QRScanner().scan_image_file(str(Path(__file__).parent / "fixtures" / "qr_url.png"))
    assert results and not called


def test_no_code_returns_empty(tmp_path):
    blank = tmp_path / "blank.png"
    cv2.imwrite(str(blank), np.full((3000, 2000, 3), 255, dtype=np.uint8))
    assert QRScanner().scan_image_file(str(blank)) == []
