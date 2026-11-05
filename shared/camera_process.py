"""
Camera capture in a separate process.

A camera read can hang inside the driver (for example when a USB camera
is unplugged). A Python thread stuck in such a call cannot be stopped, so
the camera stays held until the app exits. Running the camera in its own
process fixes that: if a read does not answer in time, the process is
ended and the operating system frees the camera.

ProcessCapture has the parts of cv2.VideoCapture that QRScanner uses
(isOpened, read, release). The main process asks for one frame at a time,
so frames are never stale and nothing piles up.
"""

import logging
import multiprocessing
import threading
from typing import Callable, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


class CameraTimeout(RuntimeError):
    """The camera did not answer in time; its process has been ended"""


def _open_cv_camera(index: int):
    import cv2
    return cv2.VideoCapture(index)


def _child_main(conn, opener: Callable, index: int, props: Sequence[Tuple[int, float]]):
    """Runs in the camera process: open the camera, answer read requests"""
    cap = None
    try:
        cap = opener(index)
        for prop, value in props:
            cap.set(prop, value)
        conn.send(("opened", bool(cap.isOpened())))
        while True:
            message = conn.recv()
            if message == "read":
                ok, frame = cap.read()
                conn.send((bool(ok), frame if ok else None))
            else:  # "stop"
                break
    except (EOFError, BrokenPipeError, OSError, KeyboardInterrupt):
        pass  # main process went away or asked to stop
    finally:
        if cap is not None:
            cap.release()
        conn.close()


class ProcessCapture:
    """
    Camera opened in a child process, with time limits on opening and reading.

    Args:
        index: Camera index, as for cv2.VideoCapture.
        props: (property, value) pairs passed to cap.set() after opening.
        open_timeout: Seconds to wait for the camera to open.
        read_timeout: Seconds to wait for one frame. When exceeded, the
            camera process is ended and read() raises CameraTimeout.
        opener: Function that opens the camera inside the child process.
            Must be importable by name (tests use it to fake a camera).
    """

    def __init__(self, index: int, props: Sequence[Tuple[int, float]] = (),
                 open_timeout: float = 10.0, read_timeout: float = 3.0,
                 opener: Optional[Callable] = None):
        self.read_timeout = read_timeout
        self.exitcode = None
        self._opened = False
        self._lock = threading.Lock()
        # "spawn" starts a clean interpreter: forking a process that runs Qt
        # and other threads is not safe, and spawn is what Windows uses anyway
        ctx = multiprocessing.get_context("spawn")
        self._conn, child_conn = ctx.Pipe()
        self._proc = ctx.Process(
            target=_child_main,
            args=(child_conn, opener or _open_cv_camera, index, list(props)),
            daemon=True,
        )
        self._proc.start()
        child_conn.close()

        try:
            if self._conn.poll(open_timeout):
                _, self._opened = self._conn.recv()
            else:
                logger.error(f"Camera did not open within {open_timeout:g} s")
        except (EOFError, OSError):
            logger.error("Camera process ended while opening the camera")
        if not self._opened:
            self.release(grace=0.5)

    def isOpened(self) -> bool:
        return self._opened and self._proc is not None and self._proc.is_alive()

    def read(self):
        if not self.isOpened():
            return False, None
        try:
            self._conn.send("read")
            if not self._conn.poll(self.read_timeout):
                logger.error(
                    f"Camera did not answer within {self.read_timeout:g} s; ending its process"
                )
                self.release(grace=0.2)
                raise CameraTimeout(
                    f"The camera stopped responding (no frame in {self.read_timeout:g} s)"
                )
            return self._conn.recv()
        except (EOFError, BrokenPipeError, OSError):
            logger.error("Camera process ended unexpectedly")
            self.release(grace=0.2)
            return False, None

    def set(self, prop, value) -> bool:
        # Properties are set in the child when the camera opens
        return False

    def release(self, grace: float = 1.0):
        """Stop the camera process; end it by force if it does not stop"""
        with self._lock:
            self._opened = False
            proc = self._proc
            if proc is None:
                return
            self._proc = None
            if proc.is_alive():
                try:
                    self._conn.send("stop")
                except (BrokenPipeError, OSError):
                    pass
                proc.join(grace)
            if proc.is_alive():
                logger.warning("Camera process did not stop; terminating it")
                proc.terminate()
                proc.join(grace)
            if proc.is_alive():
                proc.kill()
                proc.join(grace)
            self.exitcode = proc.exitcode
            self._conn.close()
