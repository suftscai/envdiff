"""CLI sub-command: envdiff patch — apply production values to a staging env file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ import diff_envs
from envdiff.parser import parse_env_file
from envdiff.patcher import patch_env
from envdiff.differ import DiffStatus


_STATUS_MAP = {
    "added": DiffStatus.ADDED,
    "removed": DiffStatus.REMOVED,
    "changed": DiffStatus.CHANGED,
}


def build_patch_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = parent.add_parser(
        "patch",
        help="Apply production values onto a staging .env file.",
    )
    p.add_argument("staging", type=Path, help="Base (staging) .env file.")
    p.add_argument("production", type=Path, help="Target (production) .env file.")
    p.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Write patched env to this file (default: stdout).",
    )
    p.add_argument(
        "--only",
        nargs="+",
        choices=list(_STATUS_MAP),
        default=None,
        metavar="STATUS",
        help="Limit patch to these change types: added, removed, changed.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing output.",
    )
    p.set_defaults(func=_run_patch)
    return p


def _run_patch(args: argparse.Namespace) -> int:
    staging_env = parse_env_file(args.staging)
    production_env = parse_env_file(args.production)
    diff = diff_envs(staging_env, production_env)

    statuses = None
    if args.only:
        statuses = [_STATUS_MAP[s] for s in args.only]

    result = patch_env(staging_env, diff, statuses=statuses, dry_run=args.dry_run)

    if args.dry_run:
        print(f"Would apply {len(result.applied)} change(s), skip {len(result.skipped)}.")
        for key in sorted(result.applied):
            print(f"  ~ {key}")
        return 0

    lines = [f"{k}={v}" for k, v in sorted(result.patched.items())]
    output = "\n".join(lines) + "\n"

    if args.output:
        args.output.write_text(output)
        print(f"Patched env written to {args.output} ({len(result.applied)} change(s) applied).")
    else:
        sys.stdout.write(output)

    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envdiff-patch")
    sub = parser.add_subparsers()
    build_patch_parser(sub)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))
