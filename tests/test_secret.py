# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""Secret handling: stdin only, private file mode."""

import io
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from reviewer import defaults, ghcli  # noqa: E402


class SecretTest(unittest.TestCase):
    def test_set_secret_passes_value_on_stdin_never_argv(self):
        calls = []

        def fake_run(args, **kwargs):
            calls.append((args, kwargs))
            return 0, "", ""

        with mock.patch.object(ghcli, "gh_installed", return_value=True):
            with mock.patch.object(ghcli, "run", side_effect=fake_run):
                ok, message = ghcli.set_secret("Aariso0/reviewer", "AI_REVIEW_API_KEY", "super-secret")
        self.assertTrue(ok, message)
        self.assertEqual(calls[0][0], ["gh", "secret", "set", "AI_REVIEW_API_KEY", "-R", "Aariso0/reviewer"])
        self.assertEqual(calls[0][1]["input_text"], "super-secret")
        self.assertNotIn("super-secret", " ".join(calls[0][0]))

    def test_set_secret_without_repo_or_gh(self):
        with mock.patch.object(ghcli, "gh_installed", return_value=False):
            ok, message = ghcli.set_secret("Aariso0/reviewer", "AI_REVIEW_API_KEY", "key")
        self.assertFalse(ok)
        self.assertIn("not installed", message)

    def test_saved_key_is_mode_600(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(defaults, "config_dir", return_value=Path(tmp)):
                message = defaults.save_key("top-secret")
                self.assertEqual(message, "")
                path = Path(tmp) / "api_key"
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
                self.assertEqual(defaults.load_saved_key(), "top-secret")
                self.assertEqual(path.read_text(encoding="utf-8"), "top-secret\n")

    def test_defaults_persist_only_allowed_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(defaults, "config_dir", return_value=Path(tmp)):
                defaults.save_defaults({"provider": "openai", "model": "gpt-x", "api_key": "leak"})
                loaded = defaults.load_defaults()
                self.assertEqual(loaded["provider"], "openai")
                self.assertNotIn("api_key", loaded)
                text = (Path(tmp) / "defaults.json").read_text(encoding="utf-8")
                self.assertNotIn("leak", text)


if __name__ == "__main__":
    unittest.main()
