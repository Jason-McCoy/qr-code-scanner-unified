"""
Desktop application package initialization
"""


def main():
    """Start the desktop app (imported lazily so that running
    "python -m desktop.qr_scanner_desktop" does not import it twice)"""
    from .qr_scanner_desktop import main as _main

    return _main()


__all__ = ["main"]
