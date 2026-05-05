"""Core diffing logic for envdiff."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class DiffStatus(str, Enum):
    ADDED = "added"       # present in b, missing from a
    REMOVED = "removed"   # present in a, missing from b
    CHANGED = "changed"   # present in both, different values
    UNCHANGED = "unchanged"  # present in both, same value


@dataclass
class DiffEntry:
    key: str
    status: DiffStatus
    value_a: str | None = None
    value_b: str | None = None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DiffEntry(key={self.key!r}, status={self.status.value}, "
            f"value_a={self.value_a!r}, value_b={self.value_b!r})"
        )


@dataclass
class DiffResult:
    entries: List[DiffEntry] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Convenience filtered views
    # ------------------------------------------------------------------ #

    def added(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.ADDED]

    def removed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.REMOVED]

    def changed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.CHANGED]

    def unchanged(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.UNCHANGED]

    def is_identical(self) -> bool:
        """Return True when there are no added, removed, or changed keys."""
        return not (self.added() or self.removed() or self.changed())

    # ------------------------------------------------------------------ #
    # Counts
    # ------------------------------------------------------------------ #

    @property
    def n_added(self) -> int:
        return len(self.added())

    @property
    def n_removed(self) -> int:
        return len(self.removed())

    @property
    def n_changed(self) -> int:
        return len(self.changed())

    @property
    def n_unchanged(self) -> int:
        return len(self.unchanged())


def diff(
    env_a: Dict[str, str],
    env_b: Dict[str, str],
) -> DiffResult:
    """Compare two env dicts and return a :class:`DiffResult`."""
    result = DiffResult()
    all_keys = sorted(set(env_a) | set(env_b))

    for key in all_keys:
        in_a = key in env_a
        in_b = key in env_b

        if in_a and not in_b:
            result.entries.append(DiffEntry(key, DiffStatus.REMOVED, value_a=env_a[key]))
        elif in_b and not in_a:
            result.entries.append(DiffEntry(key, DiffStatus.ADDED, value_b=env_b[key]))
        elif env_a[key] != env_b[key]:
            result.entries.append(
                DiffEntry(key, DiffStatus.CHANGED, value_a=env_a[key], value_b=env_b[key])
            )
        else:
            result.entries.append(
                DiffEntry(key, DiffStatus.UNCHANGED, value_a=env_a[key], value_b=env_b[key])
            )

    return result
