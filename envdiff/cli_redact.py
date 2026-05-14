"""CLI sub-command: envdiff redact — print a redacted view of an env file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.redactor import DEFAULT_PLACEHOLDER, redact_env


def build_redact_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "redact",
        help="Print an env file with sensitive values replaced by a placeholder.",
    )
    p.add_argument("file", help="Path to the .env file to redact.")
    p.add_argument(
        "--placeholder",
        default=DEFAULT_PLACEHOLDER,
        help="Replacement string for sensitive values (default: %(default)s).",
    )
    p.add_argument(
        "--extra-keys",
        nargs="*",
        default=[],
        metavar="KEY",
        help="Additional key names to treat as sensitive.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print a short summary line instead of the full redacted file.",
    )
    return p


def _run_redact(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(str(path))
    report = redact_env(env, placeholder=args.placeholder, extra_keys=args.extra_keys)

    if args.summary:
        print(
            f"Redacted {report.redaction_count} of {report.total} keys: "
            + (', '.join(report.redacted_keys) if report.redacted_keys else "(none)")
        )
        return 0

    for key, value in report.redacted.items():
        print(f"{key}={value}")

    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envdiff-redact")
    sub = parser.add_subparsers(dest="command")
    build_redact_parser(sub)
    args = parser.parse_args()
    sys.exit(_run_redact(args))
