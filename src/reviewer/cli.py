# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aariso0

"""Command line entry point for reviewer."""

import argparse
import sys

from . import __version__, banner, doctor, ghcli, wizard

EXIT_OK = 0
EXIT_ERROR = 1


def build_parser():
    parser = argparse.ArgumentParser(
        prog="reviewer",
        description="Set up an AI pull request reviewer for this repository.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="reviewer " + __version__,
        help="show the version and exit",
    )
    sub = parser.add_subparsers(dest="command")

    init = sub.add_parser("init", help="interactively set up the reviewer")
    init.add_argument("--dry-run", action="store_true", help="show the plan without writing")
    init.add_argument("--yes", action="store_true", help="accept defaults and overwrite without asking")
    init.add_argument("--no-banner", action="store_true", help="do not print the startup banner")

    sub.add_parser("doctor", help="check the local setup and report problems")
    return parser


def show_banner(args, stream=None):
    if getattr(args, "command", None) == "init" and getattr(args, "no_banner", False):
        return False
    if getattr(args, "command", None) == "doctor":
        return False
    repo = ghcli.repo_root() or "."
    return banner.print_banner(repo, __version__, stream=stream)


def main(argv=None, stream=None):
    """Run the CLI. Returns a process exit code."""
    stream = stream or sys.stdout
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help(stream)
        return EXIT_OK

    show_banner(args, stream)

    try:
        if args.command == "init":
            return wizard.Wizard(
                dry_run=args.dry_run,
                yes=args.yes,
                no_banner=getattr(args, "no_banner", False),
                stream=stream,
            ).run()
        if args.command == "doctor":
            return doctor.run(stream=stream)
    except wizard.Cancelled:
        stream.write("Cancelled.\n")
        return EXIT_ERROR
    except wizard.SetupError as exc:
        stream.write("Error: " + str(exc) + "\n")
        return EXIT_ERROR
    except KeyboardInterrupt:
        stream.write("Cancelled.\n")
        return EXIT_ERROR

    parser.print_help(stream)
    return EXIT_ERROR
