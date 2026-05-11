"""CLI entry-point for baseline comparison."""

from __future__ import annotations

import argparse
import sys

from envdiff.baseline import compare_to_baseline
from envdiff.differ import diff_envs
from envdiff.parser import parse_env_file


def build_baseline_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs: dict = dict(
        description="Compare the current env diff against a saved snapshot baseline."
    )
    if parent is not None:
        parser = parent.add_parser("baseline", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-baseline", **kwargs)

    parser.add_argument("staging", help="Staging .env file")
    parser.add_argument("production", help="Production .env file")
    parser.add_argument("snapshot", help="Path to the baseline snapshot JSON file")
    parser.add_argument(
        "--show-unchanged",
        action="store_true",
        default=False,
        help="Include unchanged keys in delta output",
    )
    return parser


def _run_baseline(args: argparse.Namespace) -> int:
    staging = parse_env_file(args.staging, label="staging")
    production = parse_env_file(args.production, label="production")
    current = diff_envs(staging, production)
    report = compare_to_baseline(current, args.snapshot)

    print(f"Baseline: {report.baseline_label}")
    print(f"  New issues   : {len(report.new_issues)}")
    print(f"  Resolved     : {len(report.resolved_issues)}")
    print(f"  Regressions  : {len(report.regressions)}")

    if report.regressions:
        print("\nRegressions (was unchanged, now differs):")
        for d in report.regressions:
            print(f"  [{d.current_status.value}] {d.key}")

    if report.new_issues:
        print("\nNew issues (not in baseline):")
        for d in report.new_issues:
            print(f"  [{d.current_status.value if d.current_status else '?'}] {d.key}")

    if report.resolved_issues:
        print("\nResolved (was differing, now unchanged):")
        for d in report.resolved_issues:
            print(f"  [resolved] {d.key}")

    return 1 if report.regressions else 0


def main() -> None:  # pragma: no cover
    parser = build_baseline_parser()
    args = parser.parse_args()
    sys.exit(_run_baseline(args))


if __name__ == "__main__":  # pragma: no cover
    main()
