"""CLI entry-point for the envdiff scheduler sub-command."""
from __future__ import annotations

import argparse
import sys

from envdiff.formatter import format_summary
from envdiff.scheduler import ScheduleEvent, run_schedule


def build_scheduler_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envdiff schedule",
        description="Periodically diff two env files and report changes.",
    )
    if parent is not None:
        parser = parent.add_parser("schedule", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("staging", help="Path to staging .env file")
    parser.add_argument("production", help="Path to production .env file")
    parser.add_argument(
        "--interval",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Seconds between diff runs (default: 60)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        metavar="N",
        help="Maximum number of runs (omit for infinite)",
    )
    parser.add_argument(
        "--changes-only",
        action="store_true",
        help="Only print output when differences are detected",
    )
    return parser


def _on_event(event: ScheduleEvent, *, changes_only: bool) -> None:
    if changes_only and not event.has_changes:
        return
    status = "CHANGED" if event.has_changes else "IDENTICAL"
    print(f"[run {event.run_number}] {status} ({event.elapsed_seconds:.3f}s)")
    print(format_summary(event.result))


def _run_scheduler(args: argparse.Namespace) -> int:
    changes_only: bool = args.changes_only

    run_schedule(
        args.staging,
        args.production,
        interval=args.interval,
        max_runs=args.runs,
        on_event=lambda e: _on_event(e, changes_only=changes_only),
    )
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = build_scheduler_parser()
    args = parser.parse_args(argv)
    sys.exit(_run_scheduler(args))


if __name__ == "__main__":  # pragma: no cover
    main()
