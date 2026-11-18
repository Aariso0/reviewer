<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 Aariso0 -->

# Security policy

## Reporting a vulnerability

Please report security issues privately using GitHub's private vulnerability reporting on this repository, or contact the maintainer directly through GitHub at <https://github.com/Aariso0>. Do not open a public issue for an unpatched vulnerability or for any API key.

Include the affected version, a description, reproduction steps and the impact. You should receive an acknowledgement within seven days.

## Supported versions

Only the latest released version receives security fixes.

## Secret handling

reviewer reads API keys with hidden input or from `AI_REVIEW_API_KEY`, sends them to `gh secret set` on stdin, and never writes them to generated files, logs or git. An optional saved key is stored in `~/.config/reviewer/api_key` with mode `600`. If you suspect a key was exposed, revoke it at the provider immediately and rotate the repository secret.
