"""
Helpers for handling untrusted QR code content safely.

QR codes can carry any bytes, including terminal control sequences
(for example ESC [2J, which clears the screen) and spreadsheet formulas.
These helpers make that content safe to show in a terminal, a log line
or a CSV cell without changing what is stored in the database.
"""

import unicodedata

# Characters that start a formula when a CSV cell is opened in a spreadsheet
# (Excel, LibreOffice, Google Sheets). See OWASP "CSV Injection".
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

# Invisible format characters that ordinary text needs: zero-width
# non-joiner and zero-width joiner (used in many scripts and in emoji such
# as family or profession emoji). Other format characters, such as the
# right-to-left override U+202E that can disguise a link, are escaped.
_ALLOWED_FORMAT_CHARS = {"‌", "‍"}


def safe_display(text: str, max_length: int = 0) -> str:
    """
    Return text that is safe to print to a terminal or write to a log.

    Control characters (C0, DEL and C1, including ESC) and other
    invisible format characters are replaced with a visible escape such
    as \\x1b, so they cannot move the cursor, clear the screen, change the
    window title or hide part of a line. Ordinary printable text,
    including non-English letters and emoji, is left as is.

    Args:
        text: Untrusted text, such as decoded QR content.
        max_length: If above 0, cut the result to this many characters
            and add "..." when it was cut.
    """
    if text is None:
        return ""

    out = []
    for ch in str(text):
        category = unicodedata.category(ch)
        if category == "Cc" or (category == "Cf" and ch not in _ALLOWED_FORMAT_CHARS):
            code = ord(ch)
            if code <= 0xFF:
                out.append(f"\\x{code:02x}")
            else:
                out.append(f"\\u{code:04x}")
        else:
            out.append(ch)

    result = "".join(out)
    if max_length > 0 and len(result) > max_length:
        result = result[:max_length] + "..."
    return result


def csv_safe_cell(value):
    """
    Neutralise spreadsheet formulas in a value written to a CSV file.

    A cell that begins with =, +, -, @, tab or carriage return is run as a
    formula by most spreadsheet programs. Prefixing a single quote makes
    the spreadsheet show it as plain text. Non-string values are returned
    unchanged.
    """
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value
