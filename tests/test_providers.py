# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""All five providers are exercised with canned HTTP responses."""

import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from review_loader import load  # noqa: E402

review = load()

RESULT = {"summary": "Looks good", "comments": [
    {"path": "app.py", "line": 12, "severity": "bug", "comment": "Check this"},
]}

PROMPT = "Review the diff"


class ProviderTest(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.payload = {"choices": [{"message": {"content": json.dumps(RESULT)}}]}

    def fake_retry(self, method, url, headers=None, body=None, attempts=4):
        self.calls.append((method, url, headers or {}, body or {}))
        return 200, json.dumps(self.payload).encode("utf-8")

    def test_gemini(self):
        payload = {"candidates": [{"content": {"parts": [{"text": json.dumps(RESULT)}]}}]}
        with mock.patch.object(review, "http_retry", side_effect=lambda *a, **k: (200, json.dumps(payload).encode())):
            got = review.call_gemini(PROMPT, "gemini-2.5-flash", "key")
        self.assertEqual(got, RESULT)

    def test_anthropic(self):
        payload = {"content": [{"type": "tool_use", "name": "submit_review", "input": RESULT}]}
        with mock.patch.object(review, "http_retry", side_effect=lambda *a, **k: (200, json.dumps(payload).encode())):
            got = review.call_anthropic(PROMPT, "claude-sonnet-5-5", "key")
        self.assertEqual(got, RESULT)

    def test_openai(self):
        payload = {"choices": [{"message": {"content": json.dumps(RESULT)}}]}
        with mock.patch.object(review, "http_retry", side_effect=self.fake_retry) as retry:
            with mock.patch.object(review, "http", side_effect=lambda *a, **k: (200, json.dumps(payload).encode())):
                got = review.call_openai_style("openai", PROMPT, "gpt-test", "https://api.openai.com/v1", "key")
        self.assertEqual(got, RESULT)
        self.assertEqual(retry.call_args[0][1], "https://api.openai.com/v1/chat/completions")
        self.assertIn("Authorization", retry.call_args[0][2])

    def test_ollama_no_key(self):
        self.payload = {"choices": [{"message": {"content": "Here: " + json.dumps(RESULT)}}]}
        with mock.patch.object(review, "http_retry", side_effect=self.fake_retry) as retry:
            with mock.patch.object(review, "http", side_effect=lambda *a, **k: (200, json.dumps(payload).encode())):
                got = review.call_openai_style("ollama", PROMPT, "llama3", "http://localhost:11434/v1", "")
        self.assertEqual(got, RESULT)
        self.assertNotIn("Authorization", retry.call_args[0][2])

    def test_opencode_uses_bundled_base_when_empty(self):
        payload = {"choices": [{"message": {"content": json.dumps(RESULT)}}]}
        with mock.patch.object(review, "http_retry", side_effect=self.fake_retry) as retry:
            with mock.patch.object(review, "http", side_effect=lambda *a, **k: (200, json.dumps(payload).encode())):
                got = review.call_openai_style("opencode", PROMPT, "model-x", "", "key")
        self.assertEqual(got, RESULT)
        self.assertEqual(retry.call_args[0][1], "https://opencode.ai/zen/v1/chat/completions")

    def test_extract_json_handles_prose_and_fences(self):
        text = "Sure!\n```json\n" + json.dumps(RESULT) + "\n```\n"
        self.assertEqual(review.extract_json(text), RESULT)

    def test_ask_model_dispatch(self):
        with mock.patch.object(review, "call_gemini", return_value=RESULT) as gemini:
            self.assertEqual(review.ask_model("gemini", PROMPT, "m", "", "k"), RESULT)
            gemini.assert_called_once()
        with mock.patch.object(review, "call_anthropic", return_value=RESULT) as anthropic:
            self.assertEqual(review.ask_model("anthropic", PROMPT, "m", "", "k"), RESULT)
            anthropic.assert_called_once()
        with mock.patch.object(review, "call_openai_style", return_value=RESULT) as openai:
            self.assertEqual(review.ask_model("openai", PROMPT, "m", "u", "k"), RESULT)
            openai.assert_called_once()


if __name__ == "__main__":
    unittest.main()
