"""Watch an env file for changes and report drift against a baseline snapshot."""

from __future__ import annotations

import time
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from envdiff.parser import parse_env_file
from envdiff.differ import diff_envs, DiffResult
from envdiff.differ_stats import compute_stats


@dataclass
class WatchEvent:
    """Emitted each time a watched file changes."""

    path: Path
    previous_hash: str
    current_hash: str
    diff: DiffResult

    @property
    def has_changes(self) -> bool:
        return self.previous_hash != self.current_hash

    def __repr__(self) -> str:  # pragma: no cover
        stats = compute_stats(self.diff)
        return (
            f"<WatchEvent path={self.path.name!r} "
            f"added={stats.added} removed={stats.removed} changed={stats.changed}>"
        )


def _file_hash(path: Path) -> str:
    """Return an MD5 hex-digest of *path* contents."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def watch(
    path: Path,
    baseline: dict[str, str],
    callback: Callable[[WatchEvent], None],
    *,
    interval: float = 2.0,
    max_events: Optional[int] = None,
) -> None:
    """Poll *path* every *interval* seconds and call *callback* on change.

    Parameters
    ----------
    path:       The ``.env`` file to monitor.
    baseline:   The reference env dict to diff against (e.g. production).
    callback:   Called with a :class:`WatchEvent` whenever the file changes.
    interval:   Polling interval in seconds (default 2).
    max_events: Stop after this many change events (``None`` = run forever).
    """
    prev_hash = _file_hash(path)
    events_fired = 0

    while True:
        time.sleep(interval)
        current_hash = _file_hash(path)

        if current_hash != prev_hash:
            current_env = parse_env_file(path)
            diff = diff_envs(current_env, baseline, label_a="watched", label_b="baseline")
            event = WatchEvent(
                path=path,
                previous_hash=prev_hash,
                current_hash=current_hash,
                diff=diff,
            )
            callback(event)
            prev_hash = current_hash
            events_fired += 1

            if max_events is not None and events_fired >= max_events:
                break
