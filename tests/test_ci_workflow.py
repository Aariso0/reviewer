# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""Guard the CI runner pin needed for Python 3.8 provisioning."""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

ROOT = Path(__file__).resolve().parents[1]
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"


class CiWorkflowTest(unittest.TestCase):
    def test_python_38_job_uses_supported_runner(self):
        text = CI_PATH.read_text(encoding="utf-8")
        self.assertIn('python-version: ["3.8", "3.12"]', text)
        self.assertIn("runs-on: ubuntu-24.04", text)
        self.assertNotIn("runs-on: ubuntu-latest", text)


if __name__ == "__main__":
    unittest.main()
