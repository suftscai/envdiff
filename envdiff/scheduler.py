"""Schedule periodic diff checks between env files and emit change events."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from envdiff.differ import DiffResult, diff_envs
from envdiff.parser import parse_env_file


@dataclass
class ScheduleEvent:
    """Emitted each time a scheduled diff run completes."""

    run_number: int
    result: DiffResult
    has_changes: bool
    elapsed_seconds: float

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ScheduleEvent(run={self.run_number}, "
            f"has_changes={self.has_changes}, "
            f"elapsed={self.elapsed_seconds:.3f}s)"
        )


def _result_has_changes(result: DiffResult) -> bool:
    from envdiff.differ import DiffStatus

    return any(
        e.status != DiffStatus.UNCHANGED for e in result.entries
    )


def run_schedule(
    staging_path: str,
    production_path: str,
    *,
    interval: float = 60.0,
    max_runs: Optional[int] = None,
    on_event: Optional[Callable[[ScheduleEvent], None]] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> list[ScheduleEvent]:
    """Repeatedly diff two env files, calling *on_event* after each run.

    Parameters
    ----------
    staging_path:    Path to the staging .env file.
    production_path: Path to the production .env file.
    interval:        Seconds to wait between runs (default 60).
    max_runs:        Stop after this many runs; ``None`` runs forever.
    on_event:        Optional callback invoked with each :class:`ScheduleEvent`.
    sleep_fn:        Injectable sleep function (useful for testing).

    Returns
    -------
    List of all :class:`ScheduleEvent` instances produced.
    """
    events: list[ScheduleEvent] = []
    run = 0

    while max_runs is None or run < max_runs:
        start = time.monotonic()
        staging = parse_env_file(staging_path)
        production = parse_env_file(production_path)
        result = diff_envs(staging, production)
        elapsed = time.monotonic() - start

        event = ScheduleEvent(
            run_number=run + 1,
            result=result,
            has_changes=_result_has_changes(result),
            elapsed_seconds=elapsed,
        )
        events.append(event)
        if on_event:
            on_event(event)

        run += 1
        if max_runs is None or run < max_runs:
            sleep_fn(interval)

    return events
