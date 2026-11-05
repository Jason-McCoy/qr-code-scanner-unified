"""
Android package initialization
"""


def main():
    """Start the live camera scanner (imported lazily so that running
    "python -m android.qr_scanner_android" does not import it twice)"""
    from .qr_scanner_android import main as _main

    return _main()


__all__ = ["main"]
