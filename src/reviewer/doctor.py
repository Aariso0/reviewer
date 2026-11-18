# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""Environment checks for `reviewer doctor`."""

import shutil
import sys
from pathlib import Path

from . import ghcli
from .defaults import GENERATED_PATHS, SECRET_NAME

FIX_GIT = "Install git and re-run inside a git repository."
FIX_GH = "Install the GitHub CLI from https://cli.github.com."
FIX_AUTH = "Run `gh auth login`."


def checks(repo_root=None):
    """Return a list of (name, status, fix) tuples. Status: ok/warn/missing."""
    root = repo_root or ghcli.repo_root()
    rows = []

    if sys.version_info >= (3, 8):
        rows.append(("python version", "ok", ""))
    else:
        rows.append(("python version", "missing", "Install Python 3.8 or newer."))

    rows.append(("git", "ok", "") if shutil.which("git") else ("git", "missing", FIX_GIT))

    gh_ok = ghcli.gh_installed()
    rows.append(("gh installed", "ok", "") if gh_ok else ("gh installed", "missing", FIX_GH))

    auth = ghcli.auth_ok()
    rows.append(("gh logged in", "ok", "") if auth else ("gh logged in", "missing", FIX_AUTH))

    remote = bool(root) and ghcli.has_github_remote(root)
    rows.append(("github remote", "ok", "") if remote else (
        "github remote", "warn", "Add a GitHub remote: `git remote add origin ...`."
    ))

    missing = [
        path for path in GENERATED_PATHS
        if not (Path(root or ".") / path).is_file()
    ]
    rows.append(("generated files", "ok", "") if not missing else (
        "generated files", "missing", "Run `reviewer init` to create " + ", ".join(missing) + "."
    ))

    name = ghcli.repo_name(root) if root else ""
    secret = ghcli.secret_exists(name, SECRET_NAME)
    if secret is True:
        rows.append((SECRET_NAME, "ok", ""))
    else:
        rows.append((SECRET_NAME, "missing", "Run `reviewer init` or `gh secret set " + SECRET_NAME + "`."))

    return rows


def run(repo_root=None, stream=None):
    """Print checks and return 0 when nothing is missing, else 1."""
    stream = stream or sys.stdout
    rows = checks(repo_root)
    width = max(len(name) for name, _, _ in rows)
    for name, status, fix in rows:
        line = "{0}: {1}".format(name.ljust(width), status)
        if fix:
            line += " - " + fix
        stream.write(line + "\n")
    return 1 if any(status == "missing" for _, status, _ in rows) else 0
