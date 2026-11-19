# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""The interactive `reviewer init` wizard."""

import getpass
import os
import sys

from . import banner, defaults, files, ghcli


class Cancelled(Exception):
    """User aborted; `written` lists files already changed."""

    def __init__(self, written=None):
        Exception.__init__(self, "cancelled")
        self.written = list(written or [])


class SetupError(Exception):
    """A setup precondition failed."""


def final_instructions(written, manual):
    """Return the plain numbered next steps printed at the end."""
    written_text = ", ".join(written) if written else "no new files"
    manual_text = ", ".join(manual) if manual else "nothing"
    return "\n".join([
        "1. Written: " + written_text + ". Still by hand: " + manual_text + ".",
        "2. Open a pull request containing these files. The workflow runs on pull requests, so it reviews itself.",
        '3. Read logs in the Actions tab, job "review".',
        "4. To change provider or model, re-run `reviewer init`.",
        "5. Limits: fork PRs get no secrets; diffs are sent to the chosen provider; free tiers may use data for "
        "training, so check the provider's terms before using private code; ollama needs a reachable URL or a "
        "self-hosted runner.",
        '6. Common errors: "Resource not accessible by integration" (workflow permissions), 429 (rate limit), '
        "review missing (draft PR or fork PR).",
    ])


class Wizard(object):
    def __init__(self, dry_run=False, yes=False, no_banner=False, stream=None):
        self.dry_run = dry_run
        self.yes = yes
        self.no_banner = no_banner
        self.out = stream or sys.stdout
        self.written = []
        self.manual = []
        self.saved = defaults.load_defaults()

    def say(self, text=""):
        self.out.write(str(text) + "\n")

    def detail(self, text=""):
        self.say(banner.style("  " + str(text), "dim", self.no_banner, self.out))

    def status(self, marker, text, tone):
        self.say(banner.style(marker, tone, self.no_banner, self.out) + " " + str(text))

    def ask(self, prompt, default=""):
        shown = prompt + " [" + default + "]: " if default else prompt + ": "
        try:
            self.out.write(shown)
            self.out.flush()
            answer = sys.stdin.readline()
        except (KeyboardInterrupt, EOFError):
            raise Cancelled(self.written)
        if not answer:
            raise Cancelled(self.written)
        answer = answer.strip()
        return answer if answer else default

    def confirm(self, prompt, default=False):
        hint = "[Y/n]" if default else "[y/N]"
        answer = self.ask(prompt + " " + hint).lower()
        return answer in ("y", "yes") or (not answer and default)

    def _step(self, number, title):
        self.say()
        heading = "[{0}/9] {1}".format(number, title)
        self.say(banner.style(heading, "step", self.no_banner, self.out))
        self.say(banner.style("  " + "-" * (len(heading) + 2), "dim", self.no_banner, self.out))

    def choose_provider(self):
        self._step(1, "Provider")
        default = self.saved.get("provider", "gemini")
        if default not in defaults.PROVIDERS:
            default = "gemini"
        while True:
            self.detail("Providers: " + ", ".join(defaults.PROVIDERS))
            provider = self.ask("Provider", default).lower()
            if provider in defaults.PROVIDERS:
                break
            self.status("[!]", "Unknown provider. Choose one of: " + ", ".join(defaults.PROVIDERS), "warn")
        info = defaults.PROVIDERS[provider]
        self.detail("Get a key: " + info["key_source"])
        if info["note"]:
            self.detail("Note: " + info["note"])
        return provider

    def choose_model(self, provider):
        self._step(2, "Model")
        default = self.saved.get("model") or defaults.PROVIDERS[provider]["default_model"]
        while True:
            model = self.ask("Model", default)
            if model:
                return model
            self.status("[!]", "A model name is required for this provider.", "warn")

    def choose_base_url(self, provider):
        self._step(3, "Base URL")
        info = defaults.PROVIDERS[provider]
        if not info["base_url"]:
            self.detail("Base URL is fixed for this provider.")
            return ""
        default = self.saved.get("base_url") or info["base_url"]
        self.detail("Default: " + default)
        if provider == "opencode":
            self.detail("UNVERIFIED: current docs show https://opencode.ai/inference/openai/v1 for Chat Completions.")
        return self.ask("Base URL", default)

    def choose_runner(self, provider, base_url):
        self._step(4, "Runner label")
        default = self.saved.get("runner") or "ubuntu-latest"
        if provider == "ollama" and "localhost" in base_url and default == "ubuntu-latest":
            self.status("[!]", "Warning: GitHub-hosted runners cannot reach localhost. Defaulting to self-hosted.", "warn")
            default = "self-hosted"
        return self.ask("Runner label", default)

    def choose_extra(self):
        self._step(5, "Extra review rules")
        default = self.saved.get("extra_instructions", "")
        if default:
            self.detail("Current: " + default)
        return self.ask("One-line extra rules (Enter for none)", default)

    def choose_key(self):
        self._step(6, "API key")
        key = os.environ.get(defaults.SECRET_NAME, "").strip()
        if key:
            self.status("[ok]", "Using " + defaults.SECRET_NAME + " from the environment.", "ok")
            return key
        if self.dry_run:
            self.status("[skip]", "Dry run: no API key needed.", "skip")
            return ""
        saved_key = defaults.load_saved_key()
        if saved_key and self.confirm("Use the saved key", False):
            return saved_key
        try:
            key = getpass.getpass("API key (hidden): ").strip()
        except (KeyboardInterrupt, EOFError):
            raise Cancelled(self.written)
        if key and not saved_key and self.confirm("Save this key to ~/.config/reviewer/ (mode 600)", False):
            error = defaults.save_key(key)
            if error:
                self.status("[!]", "Could not save the key: " + error, "bad")
        return key

    def confirm_unmarked(self, plan):
        unmarked = [row["path"] for row in plan if row["unmarked"]]
        if not unmarked:
            return True
        self.status("[!]", "Warning: these files lack the '" + defaults.MARKER + "' marker: " + ", ".join(unmarked), "warn")
        if self.yes:
            self.status("[ok]", "--yes supplied: overwriting.", "ok")
            return True
        return self.confirm("Overwrite these files", False)

    def handle_secret(self, key):
        self._step(9, "Repository secret")
        if self.dry_run:
            self.status("[skip]", "Dry run: secret not set.", "skip")
            return
        if not key:
            self.manual.append("add " + defaults.SECRET_NAME + " as a repository secret")
            self.status("[!]", "Manual: " + defaults.SECRET_NAME + " was not provided.", "warn")
            self.detail("gh secret set " + defaults.SECRET_NAME + " -R <owner/repo>")
            return
        repo = ghcli.repo_name(os.getcwd())
        if not repo:
            self.manual.append("set " + defaults.SECRET_NAME + " in the GitHub repo settings")
            self.status("[!]", "Manual: no GitHub repository could be determined; set the secret in GitHub settings.", "warn")
            return
        ok, message = ghcli.set_secret(repo, defaults.SECRET_NAME, key, cwd=os.getcwd())
        if ok:
            self.status("[ok]", "Secret " + defaults.SECRET_NAME + " set for " + repo + ".", "ok")
        else:
            self.manual.append("set " + defaults.SECRET_NAME + " for " + repo)
            self.status("[!]", "Could not set the secret: " + message, "bad")
            self.detail("gh secret set " + defaults.SECRET_NAME + " -R " + repo)

    def handle_git(self):
        if self.dry_run or not self.written:
            return
        if not self.confirm("Commit only the generated files", self.yes):
            self.manual.append("commit the generated files")
            return
        ok, message = ghcli.commit_paths(os.getcwd(), self.written, "Add AI pull request review workflow")
        if not ok:
            self.manual.append("commit the generated files")
            self.status("[!]", "Could not commit: " + message, "bad")
            return
        if self.confirm("Push the commit", self.yes):
            ok, message = ghcli.push(os.getcwd())
            if not ok:
                self.manual.append("push the commit")
                self.status("[!]", "Could not push: " + message, "bad")

    def run(self):
        root = ghcli.repo_root()
        if not root:
            raise SetupError("not inside a git repository")
        os.chdir(root)
        self.say("Repository: " + root)

        self.say(banner.style("Preflight", "step", self.no_banner, self.out))
        if not ghcli.gh_installed():
            self.status("[!]", "Warning: gh is not installed; continuing in manual-secret mode.", "warn")
        elif not ghcli.auth_ok():
            self.status("[!]", "Warning: gh is not logged in; continuing in manual-secret mode.", "warn")
        if not ghcli.has_github_remote(root):
            self.status("[!]", "Warning: no GitHub remote was found.", "warn")

        try:
            provider = self.choose_provider()
            model = self.choose_model(provider)
            base_url = self.choose_base_url(provider)
            runner = self.choose_runner(provider, base_url)
            extra = self.choose_extra()
            key = self.choose_key()
            config = {
                "provider": provider,
                "model": model,
                "base_url": base_url,
                "runner": runner,
                "extra_instructions": extra,
            }

            self._step(7, "Plan")
            plan = files.plan(root, files.build_contents(config))
            self.say(files.format_plan(plan))
            if not self.confirm_unmarked(plan):
                raise Cancelled([])

            self._step(8, "Write")
            if self.dry_run:
                self.status("[skip]", "Dry run: no files were written.", "skip")
            else:
                self.written = files.write_plan(root, plan)
                self.status("[ok]", "Wrote " + str(len(self.written)) + " file(s).", "ok")

            self.handle_secret(key)
            self.handle_git()

            if not self.dry_run:
                defaults.save_defaults(config)

            self.say("")
            self.say(final_instructions(self.written, sorted(set(self.manual))))
            return 0
        except KeyboardInterrupt:
            raise Cancelled(self.written)
