"""CLI entry point for the audit sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.differ import diff
from envdiff.auditor import build_audit, format_audit_text, AuditEvent


def _event_to_dict(event: AuditEvent) -> dict:
    return {
        "key": event.key,
        "status": event.status.value,
        "old_value": event.old_value,
        "new_value": event.new_value,
        "timestamp": event.timestamp,
        "label": event.label,
    }


def build_audit_parser(subparsers=None) -> argparse.ArgumentParser:  # type: ignore[assignment]
    desc = "Show an audit trail of changed keys between two env files."
    if subparsers is not None:
        parser = subparsers.add_parser("audit", help=desc)
    else:
        parser = argparse.ArgumentParser(prog="envdiff audit", description=desc)
    parser.add_argument("staging", help="Staging .env file")
    parser.add_argument("production", help="Production .env file")
    parser.add_argument("--label", default="", help="Optional label for this audit run")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output", "-o", default="-", help="Output file path (default: stdout)"
    )
    return parser


def _run_audit(args: argparse.Namespace) -> int:
    staging_env = parse_env_file(Path(args.staging))
    production_env = parse_env_file(Path(args.production))
    result = diff(staging_env, production_env)
    report = build_audit(result, label=args.label)

    if args.format == "json":
        output = json.dumps(
            {
                "label": report.label,
                "total": report.total,
                "events": [_event_to_dict(e) for e in report.events],
            },
            indent=2,
        )
    else:
        output = format_audit_text(report)

    if args.output == "-":
        print(output)
    else:
        Path(args.output).write_text(output, encoding="utf-8")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_audit_parser()
    args = parser.parse_args()
    sys.exit(_run_audit(args))


if __name__ == "__main__":  # pragma: no cover
    main()
