"""CLI sub-command: annotate — print human-readable annotations for a diff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.annotator import annotate, annotation_summary
from envdiff.differ import diff
from envdiff.masker import mask_env
from envdiff.parser import parse_env_file


def build_annotate_parser(parent: "argparse._SubParsersAction | None" = None) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="envdiff annotate",
        description="Print annotated diff between two .env files.",
    )
    if parent is not None:
        parser = parent.add_parser("annotate", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("staging", type=Path, help="Staging .env file")
    parser.add_argument("production", type=Path, help="Production .env file")
    parser.add_argument(
        "--include-unchanged",
        action="store_true",
        default=False,
        help="Also annotate keys that are identical in both files",
    )
    parser.add_argument(
        "--mask",
        action="store_true",
        default=False,
        help="Mask sensitive values before displaying annotations",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        default=False,
        help="Suppress the summary line at the end",
    )
    return parser


def _run_annotate(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        staging_env = parse_env_file(args.staging)
        production_env = parse_env_file(args.production)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=err)
        return 2

    if args.mask:
        staging_env = mask_env(staging_env)
        production_env = mask_env(production_env)

    result = diff(staging_env, production_env)
    annotated = annotate(result, include_unchanged=args.include_unchanged)

    if not annotated:
        print("No differences found.", file=out)
        return 0

    for ae in annotated:
        print(f"{ae.entry.key}: {ae.annotation}", file=out)

    if not args.no_summary:
        summary = annotation_summary(annotated)
        if summary:
            print(f"\nSummary: {summary}", file=out)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_annotate_parser()
    args = parser.parse_args()
    sys.exit(_run_annotate(args))


if __name__ == "__main__":  # pragma: no cover
    main()
