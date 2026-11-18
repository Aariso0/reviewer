# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""All subprocess calls to git and gh live here.

The API key is only ever passed as subprocess stdin; it is never an argument.
"""

import json
import re
import shutil
import subprocess

_GH = "gh"
_TIMEOUT = 30


def gh_installed():
    return shutil.which(_GH) is not None


def run(args, cwd=None, input_text=None):
    """Run a command with captured output. Returns (code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=_TIMEOUT,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except (OSError, subprocess.SubprocessError) as exc:
        return 127, "", str(exc)


def auth_ok():
    if not gh_installed():
        return False
    code, _, _ = run([_GH, "auth", "status"])
    return code == 0


def repo_root(start=None):
    code, out, _ = run(["git", "rev-parse", "--show-toplevel"], cwd=start)
    return out.strip() if code == 0 else ""


def has_github_remote(repo):
    code, out, _ = run(["git", "remote", "-v"], cwd=repo)
    return code == 0 and "github.com" in out


def repo_name(repo):
    """Return owner/repo, using gh first and the remote URL as fallback."""
    if gh_installed():
        code, out, _ = run(
            [_GH, "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            cwd=repo,
        )
        if code == 0:
            try:
                value = json.loads(out.strip())
                if isinstance(value, str) and "/" in value:
                    return value
            except ValueError:
                pass
    code, out, _ = run(["git", "remote", "-v"], cwd=repo)
    if code == 0:
        match = re.search(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?(?:\s|$)", out)
        if match:
            return "{0}/{1}".format(match.group(1), match.group(2))
    return ""


def set_secret(repo, name, value, cwd=None):
    """Store a secret via stdin. Returns (ok, safe message).

    `repo` is an owner/name string; `cwd` must be the local repository path.
    """
    if not repo:
        return False, "no GitHub repository could be determined"
    if not gh_installed():
        return False, "gh is not installed"
    code, _, _ = run([_GH, "secret", "set", name, "-R", repo], cwd=cwd, input_text=value)
    if code == 0:
        return True, ""
    return False, "gh secret set failed with exit code {0}".format(code)


def secret_exists(repo, name):
    """Check secret presence with gh secret list. Returns True/False/None."""
    if not repo or not gh_installed() or not auth_ok():
        return None
    code, out, _ = run([_GH, "secret", "list", "-R", repo])
    if code != 0:
        return None
    for line in out.splitlines():
        if line.split()[0:1] == [name]:
            return True
    return False


def commit_paths(repo, paths, message):
    code, _, err = run(["git", "add", "--"] + list(paths), cwd=repo)
    if code != 0:
        return False, err.strip() or "git add failed"
    code, _, err = run(["git", "commit", "-m", message], cwd=repo)
    if code != 0:
        return False, err.strip() or "git commit failed"
    return True, ""


def push(repo):
    code, _, err = run(["git", "push"], cwd=repo)
    if code != 0:
        return False, err.strip() or "git push failed"
    return True, ""
