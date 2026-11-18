# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""Plain startup banner. No colour, no animation, no escape sequences."""

import locale
import os
import shutil
import sys

WIDTH = 52
INNER = WIDTH - 4  # "| " + text + " |"


def use_unicode(stream=None):
    """Choose box drawing only when the output encoding is UTF-8."""
    stream = stream or sys.stdout
    encoding = getattr(stream, "encoding", None) or locale.getpreferredencoding(False)
    return "utf-8" in str(encoding).lower().replace("_", "-")


def should_show(no_banner=False, stream=None):
    """Return True only when a banner should be printed."""
    if no_banner:
        return False
    if os.environ.get("REVIEWER_NO_BANNER") is not None:
        return False
    if os.environ.get("NO_COLOR") is not None:
        return False
    stream = stream or sys.stdout
    return bool(getattr(stream, "isatty", lambda: False)())


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
    rows = [
        "  r e v i e w e r",
        "  AI pull request review for any repo",
        "  v{0}".format(version),
        "  {0}".format(path),
    ]
    lines = [top]
    for row in rows:
        lines.append(side + " " + row.ljust(INNER) + " " + side)
    lines.append(bottom)
    return "\n".join(lines) + "\n"


def print_banner(repo_path, version, no_banner=False, stream=None):
    """Print the banner to the given stream (stdout by default)."""
    stream = stream or sys.stdout
    text = render(repo_path, version, no_banner, stream)
    if text:
        stream.write(text)
    return bool(text)
