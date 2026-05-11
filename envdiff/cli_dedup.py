"""CLI sub-command: envdiff dedup — report or resolve duplicate keys."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.deduplicator import DeduplicationReport, find_duplicates, resolve_duplicates
from envdiff.parser import parse_env_file


def build_dedup_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Detect and optionally resolve duplicate keys between two .env files."
    if subparsers is not None:
        parser = subparsers.add_parser("dedup", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff dedup", description=description)

    parser.add_argument("staging", help="Path to the staging .env file")
    parser.add_argument("production", help="Path to the production .env file")
    parser.add_argument(
        "--resolve",
        choices=["staging", "production"],
        default=None,
        help="Merge and resolve duplicates, preferring the given side.",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Write resolved env to FILE instead of stdout (requires --resolve).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output duplicate report as JSON.",
    )
    return parser


def _print_report(report: DeduplicationReport, as_json: bool) -> None:
    if as_json:
        data = {
            "total": report.total,
            "matching": [d.key for d in report.matching],
            "conflicting": [
                {"key": d.key, "staging": d.staging_value, "production": d.production_value}
                for d in report.conflicting
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(f"Duplicate keys: {report.total}  "
              f"(matching: {len(report.matching)}, conflicting: {len(report.conflicting)}"  
              f")")
        for d in report.conflicting:
            print(f"  CONFLICT  {d.key}")
            print(f"    staging:    {d.staging_value}")
            print(f"    production: {d.production_value}")
        for d in report.matching:
            print(f"  SAME      {d.key} = {d.staging_value}")


def _run_dedup(args: argparse.Namespace) -> int:
    staging = parse_env_file(args.staging)
    production = parse_env_file(args.production)

    if args.resolve:
        merged, report = resolve_duplicates(staging, production, prefer=args.resolve)
        _print_report(report, as_json=args.json)
        lines = [f"{k}={v}\n" for k, v in sorted(merged.items())]
        if args.output:
            with open(args.output, "w") as fh:
                fh.writelines(lines)
        else:
            sys.stdout.writelines(lines)
    else:
        report = find_duplicates(staging, production)
        _print_report(report, as_json=args.json)

    return 1 if report.conflicting else 0


def main(argv: List[str] | None = None) -> None:  # pragma: no cover
    parser = build_dedup_parser()
    args = parser.parse_args(argv)
    sys.exit(_run_dedup(args))


if __name__ == "__main__":  # pragma: no cover
    main()
