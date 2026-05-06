"""CLI sub-command: filter — narrow down diff output by key pattern or status."""

from __future__ import annotations

import argparse
import sys

from envdiff.cli import _load_and_diff  # reuse common helper
from envdiff.differ import DiffStatus
from envdiff.filter import (
    exclude_unchanged,
    filter_by_pattern,
    filter_by_prefix,
    filter_by_regex,
    filter_by_status,
)
from envdiff.formatter import format_text

_STATUS_MAP = {
    "added": DiffStatus.ADDED,
    "removed": DiffStatus.REMOVED,
    "changed": DiffStatus.CHANGED,
    "unchanged": DiffStatus.UNCHANGED,
}


def build_filter_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = parent.add_parser("filter", help="Show a filtered subset of diff entries")
    p.add_argument("staging", help="Staging .env file")
    p.add_argument("production", help="Production .env file")
    p.add_argument("--prefix", metavar="PREFIX", help="Only keys starting with PREFIX")
    p.add_argument("--pattern", metavar="GLOB", help="Fnmatch glob pattern for keys")
    p.add_argument("--regex", metavar="REGEX", help="Regex pattern for keys")
    p.add_argument(
        "--status",
        metavar="STATUS",
        nargs="+",
        choices=list(_STATUS_MAP),
        help="Limit to one or more statuses: added removed changed unchanged",
    )
    p.add_argument(
        "--no-unchanged",
        action="store_true",
        default=False,
        help="Exclude unchanged entries (shorthand)",
    )
    p.add_argument("--color", action="store_true", default=False, help="Colorised output")
    return p


def _run_filter(args: argparse.Namespace) -> int:
    result = _load_and_diff(args.staging, args.production)

    if args.no_unchanged:
        result = exclude_unchanged(result)
    if args.status:
        statuses = [_STATUS_MAP[s] for s in args.status]
        result = filter_by_status(result, statuses)
    if args.prefix:
        result = filter_by_prefix(result, args.prefix)
    if args.pattern:
        result = filter_by_pattern(result, args.pattern)
    if args.regex:
        try:
            result = filter_by_regex(result, args.regex)
        except Exception as exc:  # re.error
            print(f"Invalid regex: {exc}", file=sys.stderr)
            return 2

    print(format_text(result, color=args.color))
    return 0
