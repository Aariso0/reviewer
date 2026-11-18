# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""Diff parser tests. No network, no filesystem writes."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from reviewer.data.review import parse_diff, should_skip  # noqa: E402
from review_loader import load  # noqa: E402

review = load()


DIFF = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -10,3 +10,4 @@ def main():
 context line
-old line
+new line
+added line
"""


class DiffParserTest(unittest.TestCase):
    def test_valid_new_side_lines(self):
        files, blocks = review.parse_diff(DIFF)
        self.assertEqual(files, {"app.py": {10, 11, 12}})
        self.assertTrue(any("    11 | +new line" in line for _, lines in blocks for line in lines))
        self.assertTrue(any("     - | -old line" in line for _, lines in blocks for line in lines))

    def test_no_hunks_means_no_comment_lines(self):
        files, _ = review.parse_diff("diff --git a/README.md b/README.md\n--- a/README.md\n+++ b/README.md\n")
        self.assertEqual(files, {})

    def test_skip_rules(self):
        for path in (
            "package-lock.json", "app.min.js", "image.PNG", "dist/out.js",
            "node_modules/pkg/index.js", "vendor/lib.c", "build/out.o",
        ):
            self.assertTrue(review.should_skip(path), path)
        self.assertFalse(review.should_skip("src/app.py"))

    def test_filtered_diff_truncates(self):
        files, blocks = review.parse_diff(DIFF)
        skipped = []
        text = review.filtered_diff(blocks, files, skipped)
        self.assertIn("app.py", text)
        self.assertEqual(skipped, [])

        review.MAX_DIFF_CHARS = 10
        try:
            text = review.filtered_diff(blocks, files, skipped)
            self.assertEqual(len(text), 10)
            self.assertTrue(any("truncated" in item for item in skipped))
        finally:
            review.MAX_DIFF_CHARS = 60000

    def test_module_loader_matches_package_copy(self):
        self.assertEqual(parse_diff(DIFF)[0], review.parse_diff(DIFF)[0])
        self.assertEqual(should_skip("package-lock.json"), review.should_skip("package-lock.json"))


if __name__ == "__main__":
    unittest.main()
