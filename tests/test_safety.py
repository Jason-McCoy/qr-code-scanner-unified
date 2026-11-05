"""
Unit tests for shared.safety (handling untrusted QR content)
"""

from shared.safety import safe_display, csv_safe_cell


class TestSafeDisplay:
    """Tests for safe_display()"""

    def test_plain_text_unchanged(self):
        assert safe_display("https://example.com/a?b=1") == "https://example.com/a?b=1"

    def test_escape_sequences_made_visible(self):
        text = "HELLO\x1b[2J\x1b]0;pwned\x07"
        shown = safe_display(text)
        assert "\x1b" not in shown
        assert "\x07" not in shown
        assert shown == "HELLO\\x1b[2J\\x1b]0;pwned\\x07"

    def test_newlines_tabs_del_and_c1_escaped(self):
        shown = safe_display("a\nb\tc\x7fd\x9be")
        assert shown == "a\\x0ab\\x09c\\x7fd\\x9be"

    def test_right_to_left_override_escaped(self):
        # U+202E can make "moc.live//:sptth" look like a different link
        assert safe_display("abc\u202edef") == "abc\\u202edef"

    def test_non_english_text_and_emoji_kept(self):
        text = "Café Ελληνικά 日本語 👩\u200d💻"
        assert safe_display(text) == text

    def test_max_length(self):
        assert safe_display("abcdefgh", 5) == "abcde..."
        assert safe_display("abc", 5) == "abc"

    def test_none(self):
        assert safe_display(None) == ""


class TestCsvSafeCell:
    """Tests for csv_safe_cell()"""

    def test_formula_prefixes_neutralised(self):
        for value in ["=1+1", "+1", "-1", "@SUM(A1)", "\tx", "\rx"]:
            assert csv_safe_cell(value) == "'" + value

    def test_normal_values_unchanged(self):
        assert csv_safe_cell("https://example.com") == "https://example.com"
        assert csv_safe_cell("") == ""
        assert csv_safe_cell(5) == 5
        assert csv_safe_cell(None) is None
