# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""Review posting: one COMMENT review and the 422 fallback."""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from review_loader import load  # noqa: E402

review = load()

INLINE = [{"path": "app.py", "line": 12, "severity": "bug", "comment": "Fix this"}]
OVERFLOW = [{"path": "app.py", "line": 99, "severity": "nit", "comment": "Later"}]


class PostReviewTest(unittest.TestCase):
    def test_single_comment_review(self):
        with mock.patch.object(review, "http_retry", return_value=(200, b"{}")) as retry:
            status = review.post_review("https://api.github.com", "tok", "o/r", "7", "Summary", INLINE, OVERFLOW)
        self.assertEqual(status, 200)
        self.assertEqual(retry.call_count, 1)
        method, url, headers, payload = retry.call_args[0]
        self.assertEqual(method, "POST")
        self.assertEqual(url, "https://api.github.com/repos/o/r/pulls/7/reviews")
        self.assertEqual(payload["event"], "COMMENT")
        self.assertEqual(payload["comments"], [{
            "path": "app.py", "line": 12, "side": "RIGHT", "body": "Fix this",
        }])
        self.assertEqual(payload["body"], "Summary")

    def test_422_folds_comments_into_body(self):
        responses = [(422, b"bad line"), (200, b"{}")]
        with mock.patch.object(review, "http_retry", return_value=responses[0]) as retry:
            with mock.patch.object(review, "http", return_value=responses[1]) as plain:
                status = review.post_review("https://api.github.com", "tok", "o/r", "7", "Summary", INLINE, OVERFLOW)
        self.assertEqual(status, 200)
        self.assertEqual(retry.call_count, 1)
        self.assertEqual(plain.call_count, 1)
        payload = plain.call_args[0][3]
        self.assertEqual(payload["comments"], [])
        self.assertIn("Fix this", payload["body"])
        self.assertIn("Later", payload["body"])

    def test_choose_comments_filters_and_caps(self):
        files = {"app.py": {1, 2, 3}}
        comments = [
            {"path": "app.py", "line": 3, "severity": "nit", "comment": "third"},
            {"path": "app.py", "line": 1, "severity": "security", "comment": "first"},
            {"path": "app.py", "line": 999, "severity": "bug", "comment": "invalid"},
            {"path": "app.py", "line": 1, "severity": "security", "comment": "first"},
        ]
        inline, overflow = review.choose_comments(comments, files, limit=1)
        self.assertEqual(len(inline), 1)
        self.assertEqual(inline[0]["comment"], "first")
        self.assertEqual(len(overflow), 2)


if __name__ == "__main__":
    unittest.main()
