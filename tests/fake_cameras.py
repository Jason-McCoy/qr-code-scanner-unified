"""
Fake cameras for tests of shared/camera_process.py.

These run inside the camera's child process, so they must be importable
by name (module-level functions). Each fake writes a marker file when it
is released, so a test can tell a clean stop from a forced end.
"""

import os
import time

import numpy as np


class _Fake:
    def __init__(self, hang_read=False, marker=None):
        self.hang_read = hang_read
        self.marker = marker

    def set(self, prop, value):
        return True

    def isOpened(self):
        return True

    def read(self):
        if self.hang_read:
            time.sleep(3600)  # stands in for a driver call that never returns
        return True, np.zeros((720, 1280, 3), dtype=np.uint8)

    def release(self):
        if self.marker:
            with open(self.marker, "w") as f:
                f.write("released")


def working(index):
    return _Fake(marker=os.environ.get("FAKE_CAMERA_MARKER"))


def hanging_read(index):
    return _Fake(hang_read=True, marker=os.environ.get("FAKE_CAMERA_MARKER"))


def hanging_open(index):
    time.sleep(3600)
