# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""CLI surface: version, help, doctor and exit codes."""

import contextlib
import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from reviewer import cli  # noqa: E402


class CliTest(unittest.TestCase):
    def test_version(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as raised:
                cli.main(["--version"], stream=out)
        self.assertEqual(raised.exception.code, 0)
        self.assertIn("reviewer 0.1.0", out.getvalue())

    def test_help(self):
        out = io.StringIO()
        code = cli.main([], stream=out)
        self.assertEqual(code, 0)
        self.assertIn("usage: reviewer", out.getvalue())
        self.assertIn("init", out.getvalue())
        self.assertIn("doctor", out.getvalue())

    def test_doctor_returns_one_when_missing(self):
        rows = [("python version", "ok", ""), ("git", "missing", "install git")]
        out = io.StringIO()
        with mock.patch.object(cli.doctor, "run", return_value=1) as run:
            with mock.patch.object(cli.doctor, "checks", return_value=rows):
                code = cli.main(["doctor"], stream=out)
        self.assertEqual(code, 1)
        run.assert_called_once()

    def test_setup_error_maps_to_exit_one(self):
        out = io.StringIO()
        with mock.patch.object(cli.wizard.Wizard, "run", side_effect=cli.wizard.SetupError("bad repo")):
            code = cli.main(["init", "--no-banner"], stream=out)
        self.assertEqual(code, 1)
        self.assertIn("Error: bad repo", out.getvalue())

    def test_cancel_maps_to_exit_one(self):
        out = io.StringIO()
        with mock.patch.object(cli.wizard.Wizard, "run", side_effect=cli.wizard.Cancelled()):
            code = cli.main(["init", "--no-banner"], stream=out)
        self.assertEqual(code, 1)
        self.assertIn("Cancelled.", out.getvalue())


if __name__ == "__main__":
    unittest.main()
