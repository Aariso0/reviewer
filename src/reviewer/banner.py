# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""Startup banner and gated terminal styling."""

import locale
import os
import shutil
import sys

WIDTH = 52
INNER = WIDTH - 4  # "| " + text + " |"
RESET = "\033[0m"
STYLES = {
    "title": "\033[1;36m",
    "step": "\033[1;37m",
    "dim": "\033[2m",
    "skip": "\033[2m",
    "ok": "\033[32m",
    "warn": "\033[33m",
    "bad": "\033[31m",
}
WORDMARK = [
    r"  ___  ___  __  __  _  ___  ___  ___ ",
    r" | _ \| _ \ \ \/ / / \| _ \| _ \/ __|",
    r" | __/| __/  >  < | __| __/| __/ \__ \ ",
    r" |_|  |_|   /_/\_\|_| |_|  |_|  |___/",
]


def use_unicode(stream=None):
    """Choose box drawing only when the output encoding is UTF-8."""
    stream = stream or sys.stdout
    encoding = getattr(stream, "encoding", None) or locale.getpreferredencoding(False)
    return "utf-8" in str(encoding).lower().replace("_", "-")


def should_show(no_banner=False, stream=None):
    """Return True only when decoration should be printed."""
    if no_banner:
        return False
    if os.environ.get("REVIEWER_NO_BANNER") is not None:
        return False
    if os.environ.get("NO_COLOR") is not None:
        return False
    stream = stream or sys.stdout
    return bool(getattr(stream, "isatty", lambda: False)())


def style(text, tone, no_banner=False, stream=None):
    """Apply a terminal style only where decoration is allowed."""
    if not should_show(no_banner, stream):
        return str(text)
    return STYLES[tone] + str(text) + RESET


def render(repo_path, version, no_banner=False, stream=None, columns=None):
    """Return the banner text, or '' when it should be skipped."""
    if not should_show(no_banner, stream):
        return ""
    if columns is None:
        try:
            columns = shutil.get_terminal_size((80, 24)).columns
        except (OSError, ValueError):
            columns = 80
    if columns < WIDTH:
        return "reviewer v{0}\n".format(version)

    unicode_box = use_unicode(stream)
    if unicode_box:
        top = "┌" + "─" * (WIDTH - 2) + "┐"
        bottom = "└" + "─" * (WIDTH - 2) + "┘"
        side = "│"
    else:
        top = "+" + "-" * (WIDTH - 2) + "+"
        bottom = "+" + "-" * (WIDTH - 2) + "+"
        side = "|"

    path = "repo: {0}".format(repo_path)
    if len(path) > INNER:
        path = path[: INNER - 3] + "..."
    rows = [(row, "title") for row in WORDMARK]
    rows.extend([
        ("  AI pull request review for any repo", None),
        ("  v{0}".format(version), None),
        ("  {0}".format(path), None),
    ])
    lines = [top]
    for text, tone in rows:
        padded = text.ljust(INNER)
        if tone:
            padded = style(padded, tone, no_banner, stream)
        lines.append(side + " " + padded + " " + side)
    lines.append(bottom)
    return "\n".join(lines) + "\n"


def print_banner(repo_path, version, no_banner=False, stream=None):
    """Print the banner to the given stream (stdout by default)."""
    stream = stream or sys.stdout
    text = render(repo_path, version, no_banner, stream)
    if text:
        stream.write(text)
    return bool(text)
