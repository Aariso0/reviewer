<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 Aariso0 -->

# Changelog

## 0.1.5

- Simplified the banner to a single bold-white `Reviewer` title.

## 0.1.4

- Larger ASCII wordmark in the startup banner.
- Step headers with divider rules and indented detail lines.
- `[ok]`, `[!]` and `[skip]` status markers with gated colour accents.
- Version assertion in tests now reads `__version__` instead of a hardcoded string.

## 0.1.3

- Initial release.
- `reviewer init` wizard with `--dry-run`, `--yes` and `--no-banner`.
- `reviewer doctor` environment checks.
- Standard-library-only generated runner for Gemini, Anthropic, OpenAI-compatible endpoints, Ollama and OpenCode Zen.
- Sparse-checkout GitHub Actions workflow with minimal permissions.
- Apache-2.0 license and NOTICE.
