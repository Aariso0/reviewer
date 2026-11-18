# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""Load the bundled review.py as a standalone module for tests."""

import importlib.util
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REVIEW_PATH = os.path.join(_ROOT, "src", "reviewer", "data", "review.py")


def load():
    spec = importlib.util.spec_from_file_location("bundled_review", REVIEW_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
