"""CLI sub-commands for snapshot management: save and compare."""
from __future__ import annotations

import argparse
import sys

from envdiff.differ import diff
from envdiff.formatter import format_text, format_summary
from envdiff.parser import parse_env_file
from envdiff.snapshot import load_snapshot, save_snapshot, snapshot_metadata


def build_snapshot_parser(parent: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    sp = parent.add_parser("snapshot", help="Save or compare environment snapshots")
    sub = sp.add_subparsers(dest="snapshot_cmd", required=True)

    # save sub-command
    save_p = sub.add_parser("save", help="Save a diff result to a snapshot file")
    save_p.add_argument("left", help="Left (staging) .env file")
    save_p.add_argument("right", help="Right (production) .env file")
    save_p.add_argument("output", help="Destination snapshot JSON file")
    save_p.add_argument("--label", default="", help="Optional label for the snapshot")

    # compare sub-command
    cmp_p = sub.add_parser("compare", help="Compare current env files against a saved snapshot")
    cmp_p.add_argument("snapshot", help="Previously saved snapshot JSON file")
    cmp_p.add_argument("left", help="Left (staging) .env file")
    cmp_p.add_argument("right", help="Right (production) .env file")
    cmp_p.add_argument("--color", action="store_true", help="Colorised output")

    # info sub-command
    sub.add_parser("info", help="Show metadata for a snapshot file").add_argument("snapshot")


def _run_snapshot(args: argparse.Namespace) -> int:
    if args.snapshot_cmd == "save":
        left = parse_env_file(args.left)
        right = parse_env_file(args.right)
        result = diff(left, right)
        save_snapshot(result, args.output, label=args.label)
        print(f"Snapshot saved to {args.output}")
        return 0

    if args.snapshot_cmd == "compare":
        saved = load_snapshot(args.snapshot)
        left = parse_env_file(args.left)
        right = parse_env_file(args.right)
        current = diff(left, right)
        # Show both snapshots side-by-side as text
        print("=== Saved snapshot ===")
        print(format_text(saved, color=False))
        print("=== Current diff ===")
        print(format_text(current, color=getattr(args, "color", False)))
        print(format_summary(current))
        return 0

    if args.snapshot_cmd == "info":
        meta = snapshot_metadata(args.snapshot)
        for key, value in meta.items():
            print(f"{key}: {value}")
        return 0

    print(f"Unknown snapshot command: {args.snapshot_cmd}", file=sys.stderr)
    return 1
