"""Command-line interface for envdiff."""

import argparse
import sys
from pathlib import Path

from .parser import parse_env_file
from .differ import diff
from .formatter import format_text, format_summary


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff",
        description="Diff environment variable sets across config files.",
    )
    p.add_argument("file_a", metavar="FILE_A", help="First env file (e.g. staging)")
    p.add_argument("file_b", metavar="FILE_B", help="Second env file (e.g. production)")
    p.add_argument(
        "--label-a",
        default=None,
        help="Label for FILE_A (defaults to filename)",
    )
    p.add_argument(
        "--label-b",
        default=None,
        help="Label for FILE_B (defaults to filename)",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored output",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print only the summary line",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if differences are found",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    path_a = Path(args.file_a)
    path_b = Path(args.file_b)

    for path in (path_a, path_b):
        if not path.exists():
            print(f"envdiff: error: file not found: {path}", file=sys.stderr)
            return 2

    env_a = parse_env_file(path_a)
    env_b = parse_env_file(path_b)

    label_a = args.label_a or path_a.name
    label_b = args.label_b or path_b.name

    result = diff(env_a, env_b)
    color = not args.no_color

    if args.summary:
        print(format_summary(result, label_a=label_a, label_b=label_b))
    else:
        output = format_text(result, color=color, label_a=label_a, label_b=label_b)
        if output:
            print(output)
        print(format_summary(result, label_a=label_a, label_b=label_b))

    if args.exit_code and not result.is_identical():
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
