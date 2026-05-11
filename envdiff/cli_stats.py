"""CLI sub-command: envdiff stats — show change statistics for two env files."""
from __future__ import annotations

import argparse
import sys

from envdiff.differ import diff_envs
from envdiff.differ_stats import compute_stats, format_stats_text
from envdiff.parser import parse_env_file


def build_stats_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Display change statistics between two .env files."
    if subparsers is not None:
        parser = subparsers.add_parser("stats", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-stats", description=description)

    parser.add_argument("staging", help="Path to the staging .env file")
    parser.add_argument("production", help="Path to the production .env file")
    parser.add_argument(
        "--label",
        default=None,
        metavar="LABEL",
        help="Optional label shown in the stats header",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output stats as JSON instead of plain text",
    )
    return parser


def _run_stats(args: argparse.Namespace) -> int:
    try:
        staging_env = parse_env_file(args.staging)
        production_env = parse_env_file(args.production)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = diff_envs(staging_env, production_env)
    stats = compute_stats(result)

    if args.json:
        import json
        payload = {
            "label": args.label,
            "total": stats.total,
            "added": stats.added,
            "removed": stats.removed,
            "changed": stats.changed,
            "unchanged": stats.unchanged,
            "change_ratio": round(stats.change_ratio, 6),
            "churn_score": round(stats.churn_score, 6),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_stats_text(stats, label=args.label))

    return 0


def main() -> None:  # pragma: no cover
    parser = build_stats_parser()
    args = parser.parse_args()
    sys.exit(_run_stats(args))


if __name__ == "__main__":  # pragma: no cover
    main()
