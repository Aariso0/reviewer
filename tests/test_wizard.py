# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""Wizard dry runs and real writes in a temporary git repository."""

import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from reviewer import cli, defaults, ghcli  # noqa: E402


def make_repo(path):
    subprocess.run(["git", "init", "-q", path], check=True)
    return path


class WizardTest(unittest.TestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        self.addCleanup(os.chdir, self.old_cwd)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_repo(self.tmp.name)
        self.out = io.StringIO()

    def patches(self):
        return [
            mock.patch.object(ghcli, "repo_root", return_value=self.repo),
            mock.patch.object(ghcli, "gh_installed", return_value=False),
            mock.patch.object(ghcli, "has_github_remote", return_value=False),
            mock.patch.object(ghcli, "repo_name", return_value="Aariso0/reviewer"),
            mock.patch.object(ghcli, "commit_paths", return_value=(True, "")),
            mock.patch.object(ghcli, "push", return_value=(True, "")),
            mock.patch.object(defaults, "load_defaults", return_value={}),
            mock.patch.object(defaults, "save_defaults"),
            mock.patch.object(defaults, "load_saved_key", return_value=""),
        ]

    def run_cli(self, argv, answers="", getpass_value="", env=None):
        patchers = self.patches()
        for patcher in patchers:
            patcher.start()
        self.addCleanup(lambda: [patcher.stop() for patcher in reversed(patchers)])
        stdin_patch = mock.patch("sys.stdin", io.StringIO(answers))
        stdin_patch.start()
        self.addCleanup(stdin_patch.stop)
        getpass_patch = mock.patch("getpass.getpass", return_value=getpass_value)
        getpass_patch.start()
        self.addCleanup(getpass_patch.stop)
        environ = {"AI_REVIEW_API_KEY": ""}
        if env:
            environ.update(env)
        env_patch = mock.patch.dict(os.environ, environ, clear=False)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        return cli.main(argv, stream=self.out)

    def test_dry_run_writes_nothing(self):
        code = self.run_cli(["init", "--dry-run", "--yes", "--no-banner"], answers="\n" * 8)
        self.assertEqual(code, 0)
        text = self.out.getvalue()
        self.assertIn(".github/reviewer/review.py", text)
        self.assertIn(".github/workflows/pr-review.yml", text)
        self.assertIn("Dry run: no files were written.", text)
        self.assertFalse((Path(self.repo) / ".github").exists())

    def test_real_run_writes_three_files_and_sets_secret(self):
        with mock.patch.object(ghcli, "set_secret", return_value=(True, "")) as setter:
            code = self.run_cli(
                ["init", "--yes", "--no-banner"],
                answers="\n" * 8,
                getpass_value="wizard-secret",
                env={"AI_REVIEW_API_KEY": "wizard-secret"},
            )
        self.assertEqual(code, 0)
        for relpath in defaults.GENERATED_PATHS:
            path = Path(self.repo) / relpath
            self.assertTrue(path.is_file(), relpath)
            self.assertIn("SPDX-License-Identifier: Apache-2.0", path.read_text(encoding="utf-8"))
        setter.assert_called_once()
        self.assertEqual(setter.call_args[0][2], "wizard-secret")
        self.assertEqual(setter.call_args[1]["cwd"], self.repo)
        for relpath in defaults.GENERATED_PATHS:
            self.assertNotIn("wizard-secret", (Path(self.repo) / relpath).read_text(encoding="utf-8"))
        self.assertNotIn("wizard-secret", self.out.getvalue())

    def test_no_tty_banner_suppressed_by_flag(self):
        code = self.run_cli(["init", "--dry-run", "--yes", "--no-banner"], answers="\n" * 8)
        self.assertEqual(code, 0)
        self.assertNotIn("r e v i e w e r", self.out.getvalue())

    def test_confirm_prints_one_prompt(self):
        with mock.patch.object(defaults, "load_defaults", return_value={}):
            wizard_obj = cli.wizard.Wizard(yes=True, no_banner=True, stream=self.out)
        with mock.patch("sys.stdin", io.StringIO("y\n")):
            self.assertTrue(wizard_obj.confirm("Continue", False))
        self.assertEqual(self.out.getvalue(), "Continue [y/N]: ")

    def test_step_header_is_bold_on_tty(self):
        class TTYOut(io.StringIO):
            def isatty(self):
                return True

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(defaults, "load_defaults", return_value={}):
                wizard_obj = cli.wizard.Wizard(stream=TTYOut())
            wizard_obj._step(1, "Provider")
        self.assertIn("\x1b[1;37m[1/9] Provider\x1b[0m", wizard_obj.out.getvalue())


if __name__ == "__main__":
    unittest.main()
