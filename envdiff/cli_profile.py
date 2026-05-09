"""CLI sub-command: envdiff profile — show a statistical profile of a diff."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.differ import compute_diff
from envdiff.parser import parse_env_file
from envdiff.profiler import profile_diff


def build_profile_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Display a statistical profile of differences between two env files."
    if subparsers is not None:
        parser = subparsers.add_parser("profile", description=description, help=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff profile", description=description)

    parser.add_argument("staging", help="Path to the staging .env file")
    parser.add_argument("production", help="Path to the production .env file")
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        default=False,
        help="Output profile as JSON",
    )
    return parser


def _run_profile(args: argparse.Namespace) -> int:
    staging_env = parse_env_file(args.staging, label="staging")
    production_env = parse_env_file(args.production, label="production")
    result = compute_diff(staging_env, production_env)
    prof = profile_diff(result)

    if args.as_json:
        data = {
            "total": prof.total,
            "added": prof.added,
            "removed": prof.removed,
            "changed": prof.changed,
            "unchanged": prof.unchanged,
            "change_rate": round(prof.change_rate, 4),
            "sensitive_keys": sorted(prof.sensitive_keys),
            "prefixes": prof.prefixes,
        }
        print(json.dumps(data, indent=2))
    else:
        print(f"Total keys   : {prof.total}")
        print(f"  Added      : {prof.added}")
        print(f"  Removed    : {prof.removed}")
        print(f"  Changed    : {prof.changed}")
        print(f"  Unchanged  : {prof.unchanged}")
        print(f"Change rate  : {prof.change_rate:.1%}")
        if prof.sensitive_keys:
            keys = ", ".join(sorted(prof.sensitive_keys))
            print(f"Sensitive    : {keys}")
        else:
            print("Sensitive    : none detected")
        if prof.prefixes:
            top = sorted(prof.prefixes.items(), key=lambda kv: -kv[1])[:5]
            top_str = ", ".join(f"{p}({c})" for p, c in top)
            print(f"Top prefixes : {top_str}")

    return 0


def main(argv: List[str] | None = None) -> None:  # pragma: no cover
    parser = build_profile_parser()
    args = parser.parse_args(argv)
    sys.exit(_run_profile(args))


if __name__ == "__main__":  # pragma: no cover
    main()
