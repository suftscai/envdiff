"""CLI sub-command: validate one or two env files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.differ import diff
from envdiff.validator import validate_env_dict, validate_diff


def build_validate_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "validate",
        help="Validate one or two env files for structural issues and diff anomalies.",
    )
    p.add_argument("staging", metavar="STAGING", help="Staging / base env file")
    p.add_argument("production", metavar="PRODUCTION", nargs="?", help="Production env file (optional)")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any warnings are found (in addition to errors).",
    )
    p.set_defaults(func=_run_validate)
    return p


def _run_validate(args: argparse.Namespace) -> int:
    staging_env = parse_env_file(Path(args.staging))
    issues_found = False

    staging_report = validate_env_dict(staging_env, label="staging")
    _print_issues(staging_report.issues, source=args.staging)
    if staging_report.errors or (args.strict and staging_report.warnings):
        issues_found = True

    if args.production:
        production_env = parse_env_file(Path(args.production))
        prod_report = validate_env_dict(production_env, label="production")
        _print_issues(prod_report.issues, source=args.production)
        if prod_report.errors or (args.strict and prod_report.warnings):
            issues_found = True

        diff_result = diff(staging_env, production_env)
        diff_report = validate_diff(diff_result)
        _print_issues(diff_report.issues, source="diff")
        if diff_report.errors or (args.strict and diff_report.warnings):
            issues_found = True

    if not issues_found:
        print("validation passed")

    return 1 if issues_found else 0


def _print_issues(issues, source: str) -> None:
    for issue in issues:
        tag = issue.severity.upper()
        print(f"[{tag}] ({source}) {issue.key}: {issue.message}", file=sys.stderr)
