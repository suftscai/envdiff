"""CLI sub-command: envdiff merge — merge two env files and print the result."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envdiff.merger import MergeConflict, MergeStrategy, merge_envs
from envdiff.parser import parse_env_file


def build_merge_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # noqa: SLF001
    description = "Merge two .env files and write the combined result to stdout."
    if parent is not None:
        parser = parent.add_parser("merge", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff merge", description=description)

    parser.add_argument("base", help="Base .env file (left side).")
    parser.add_argument("override", help="Override .env file (right side).")
    parser.add_argument(
        "--strategy",
        choices=[s.value for s in MergeStrategy],
        default=MergeStrategy.RIGHT.value,
        help="Conflict resolution strategy (default: right).",
    )
    parser.add_argument(
        "--prefix",
        metavar="PREFIX",
        default=None,
        help="Only merge keys from override that start with PREFIX.",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write output to FILE instead of stdout.",
    )
    return parser


def _run_merge(args: argparse.Namespace) -> int:
    try:
        base_env = parse_env_file(args.base)
        override_env = parse_env_file(args.override)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    strategy = MergeStrategy(args.strategy)

    try:
        merged = merge_envs(
            base_env,
            override_env,
            strategy=strategy,
            prefix_filter=args.prefix,
        )
    except MergeConflict as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    lines: List[str] = [f"{key}={value}" for key, value in sorted(merged.items())]
    output = "\n".join(lines) + ("\n" if lines else "")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
    else:
        sys.stdout.write(output)

    return 0


def main(argv: Optional[List[str]] = None) -> None:  # pragma: no cover
    parser = build_merge_parser()
    args = parser.parse_args(argv)
    sys.exit(_run_merge(args))
