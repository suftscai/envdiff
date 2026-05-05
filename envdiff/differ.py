"""Core diffing logic for comparing two environment variable sets."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class DiffStatus(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


@dataclass
class DiffEntry:
    key: str
    status: DiffStatus
    left_value: Optional[str] = None
    right_value: Optional[str] = None

    def __repr__(self) -> str:
        if self.status == DiffStatus.ADDED:
            return f"+{self.key}={self.right_value!r}"
        if self.status == DiffStatus.REMOVED:
            return f"-{self.key}={self.left_value!r}"
        if self.status == DiffStatus.CHANGED:
            return f"~{self.key}: {self.left_value!r} -> {self.right_value!r}"
        return f" {self.key}={self.left_value!r}"


@dataclass
class DiffResult:
    entries: List[DiffEntry] = field(default_factory=list)

    @property
    def added(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.ADDED]

    @property
    def removed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.REMOVED]

    @property
    def changed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.CHANGED]

    @property
    def unchanged(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.UNCHANGED]

    @property
    def has_differences(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def diff_envs(
    left: Dict[str, str],
    right: Dict[str, str],
    include_unchanged: bool = False,
) -> DiffResult:
    """Compare two env dicts and return a DiffResult.

    Args:
        left: The base environment (e.g. staging).
        right: The target environment (e.g. production).
        include_unchanged: Whether to include keys with identical values.

    Returns:
        A DiffResult containing all DiffEntry items.
    """
    result = DiffResult()
    all_keys = sorted(set(left) | set(right))

    for key in all_keys:
        in_left = key in left
        in_right = key in right

        if in_left and not in_right:
            result.entries.append(DiffEntry(key, DiffStatus.REMOVED, left_value=left[key]))
        elif in_right and not in_left:
            result.entries.append(DiffEntry(key, DiffStatus.ADDED, right_value=right[key]))
        elif left[key] != right[key]:
            result.entries.append(
                DiffEntry(key, DiffStatus.CHANGED, left_value=left[key], right_value=right[key])
            )
        elif include_unchanged:
            result.entries.append(
                DiffEntry(key, DiffStatus.UNCHANGED, left_value=left[key], right_value=right[key])
            )

    return result
