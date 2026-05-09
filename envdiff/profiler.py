"""Profile an env file: count keys by status category and surface quick stats."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class EnvProfile:
    """Aggregated statistics for a diff result."""

    total: int = 0
    added: int = 0
    removed: int = 0
    changed: int = 0
    unchanged: int = 0
    sensitive_keys: List[str] = field(default_factory=list)
    prefixes: Dict[str, int] = field(default_factory=dict)

    @property
    def change_rate(self) -> float:
        """Fraction of non-unchanged keys relative to total (0.0 – 1.0)."""
        if self.total == 0:
            return 0.0
        return (self.added + self.removed + self.changed) / self.total

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"EnvProfile(total={self.total}, added={self.added}, "
            f"removed={self.removed}, changed={self.changed}, "
            f"unchanged={self.unchanged}, change_rate={self.change_rate:.2%})"
        )


_SENSITIVE_FRAGMENTS = ("SECRET", "PASSWORD", "PASSWD", "TOKEN", "KEY", "PRIVATE", "AUTH")


def _is_sensitive(key: str) -> bool:
    upper = key.upper()
    return any(frag in upper for frag in _SENSITIVE_FRAGMENTS)


def _prefix(key: str) -> str:
    """Return the first segment of a key split by '_', or the key itself."""
    return key.split("_")[0] if "_" in key else key


def profile_diff(result: DiffResult) -> EnvProfile:
    """Build an :class:`EnvProfile` from a :class:`DiffResult`."""
    prof = EnvProfile()
    for entry in result.entries:
        prof.total += 1
        if entry.status == DiffStatus.ADDED:
            prof.added += 1
        elif entry.status == DiffStatus.REMOVED:
            prof.removed += 1
        elif entry.status == DiffStatus.CHANGED:
            prof.changed += 1
        else:
            prof.unchanged += 1

        if _is_sensitive(entry.key):
            prof.sensitive_keys.append(entry.key)

        pfx = _prefix(entry.key)
        prof.prefixes[pfx] = prof.prefixes.get(pfx, 0) + 1

    return prof
