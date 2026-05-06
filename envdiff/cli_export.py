"""CLI sub-command: envdiff export — write diff to a file in a chosen format."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ import diff
from envdiff.exporter import export_csv, export_json, export_markdown
from envdiff.parser import parse_env_file

_FORMATS = {
    "json": export_json,
    "csv": export_csv,
    "markdown": export_markdown,
}


def build_export_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'export' sub-command on an existing subparser group."""
    p = subparsers.add_parser(
        "export",
        help="Export the diff to JSON, CSV, or Markdown.",
    )
    p.add_argument("staging", help="Path to the staging .env file.")
    p.add_argument("production", help="Path to the production .env file.")
    p.add_argument(
        "--format",
        choices=list(_FORMATS),
        default="json",
        dest="fmt",
        help="Output format (default: json).",
    )
    p.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write output to this file instead of stdout.",
    )
    p.add_argument(
        "--mask",
        action="store_true",
        default=False,
        help="Mask sensitive values in the output.",
    )
    p.set_defaults(func=_run_export)


def _run_export(args: argparse.Namespace) -> int:
    """Execute the export sub-command; return an exit code."""
    staging_path = Path(args.staging)
    production_path = Path(args.production)

    for path in (staging_path, production_path):
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 2

    staging_env = parse_env_file(staging_path)
    production_env = parse_env_file(production_path)
    result = diff(staging_env, production_env)

    formatter = _FORMATS[args.fmt]
    output = formatter(result, mask=args.mask)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Exported {args.fmt} diff to {args.output}")
    else:
        print(output)

    return 0
