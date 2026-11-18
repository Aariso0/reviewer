# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""Banner gates and plain-text rendering tests."""

import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from reviewer import banner  # noqa: E402


class TTYStream(io.StringIO):
    def isatty(self):
        return True


class PlainStream(io.StringIO):
    encoding = "ascii"

    def isatty(self):
        return True


class BannerTest(unittest.TestCase):
    def test_no_banner_without_tty(self):
        self.assertFalse(banner.should_show(False, io.StringIO()))
        self.assertEqual(banner.render("/repo", "0.1.0", False, io.StringIO()), "")

    def test_env_gates(self):
        with mock.patch.dict(os.environ, {"REVIEWER_NO_BANNER": "1"}, clear=False):
            self.assertFalse(banner.should_show(False, TTYStream()))
        with mock.patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False):
            self.assertFalse(banner.should_show(False, TTYStream()))
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(banner.should_show(False, TTYStream()))

    def test_ascii_fallback(self):
        text = banner.render("/repo", "0.1.0", False, PlainStream(), columns=80)
        self.assertIn("+", text)
        self.assertNotIn("─", text)
        self.assertNotIn("\x1b", text)
        self.assertIn("repo: /repo", text)

    def test_unicode_box(self):
        class UTF8Stream(TTYStream):
            encoding = "utf-8"
        text = banner.render("/repo", "0.1.0", False, UTF8Stream(), columns=80)
        self.assertIn("┌", text)
        self.assertIn("│", text)

    def test_narrow_terminal(self):
        text = banner.render("/repo", "0.1.0", False, TTYStream(), columns=40)
        self.assertEqual(text, "reviewer v0.1.0\n")

    def test_print_banner(self):
        stream = TTYStream()
        self.assertTrue(banner.print_banner("/repo", "0.1.0", False, stream))
        self.assertIn("r e v i e w e r", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
