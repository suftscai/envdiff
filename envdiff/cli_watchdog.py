"""CLI entry-point for the env file watcher."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.formatter import format_text, format_summary
from envdiff.watchdog import watch, WatchEvent


def build_watchdog_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    kwargs = dict(
        description="Watch an env file for drift against a baseline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser = parent.add_parser("watch", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("watched", type=Path, help="Env file to monitor for changes.")
    parser.add_argument("baseline", type=Path, help="Baseline env file to diff against.")
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 2.0).",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the summary line on each change.",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=None,
        metavar="N",
        help="Exit after N change events (useful for testing).",
    )
    return parser


def _run_watchdog(args: argparse.Namespace) -> int:
    watched_path: Path = args.watched
    baseline_path: Path = args.baseline

    if not watched_path.exists():
        print(f"error: watched file not found: {watched_path}", file=sys.stderr)
        return 2
    if not baseline_path.exists():
        print(f"error: baseline file not found: {baseline_path}", file=sys.stderr)
        return 2

    baseline_env = parse_env_file(baseline_path)

    def _on_change(event: WatchEvent) -> None:
        print(f"\n[envdiff watch] change detected in {event.path.name}")
        if args.summary_only:
            print(format_summary(event.diff))
        else:
            print(format_text(event.diff))
            print(format_summary(event.diff))

    print(f"Watching {watched_path} against {baseline_path} (interval={args.interval}s) …")
    print("Press Ctrl+C to stop.")
    try:
        watch(
            watched_path,
            baseline_env,
            _on_change,
            interval=args.interval,
            max_events=args.max_events,
        )
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
    return 0


def main() -> None:  # pragma: no cover
    parser = build_watchdog_parser()
    args = parser.parse_args()
    sys.exit(_run_watchdog(args))


if __name__ == "__main__":  # pragma: no cover
    main()
