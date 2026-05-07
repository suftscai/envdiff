"""Merge two env dicts with configurable conflict resolution strategies."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional


class MergeStrategy(str, Enum):
    """How to resolve key conflicts when merging two env dicts."""

    LEFT = "left"    # keep value from base (left) env
    RIGHT = "right"  # keep value from override (right) env
    ERROR = "error"  # raise on any conflict


class MergeConflict(Exception):
    """Raised when MergeStrategy.ERROR is used and a conflict is detected."""

    def __init__(self, key: str, left: str, right: str) -> None:
        self.key = key
        self.left = left
        self.right = right
        super().__init__(
            f"Conflict on key '{key}': left={left!r}, right={right!r}"
        )


def merge_envs(
    base: Dict[str, str],
    override: Dict[str, str],
    strategy: MergeStrategy = MergeStrategy.RIGHT,
    prefix_filter: Optional[str] = None,
) -> Dict[str, str]:
    """Return a new dict that is the merge of *base* and *override*.

    Args:
        base: The primary env dict ("left" side).
        override: The secondary env dict ("right" side).
        strategy: Conflict-resolution strategy for keys present in both dicts.
        prefix_filter: When given, only keys whose names start with this
            prefix are taken from *override*; all other override keys are
            ignored.

    Returns:
        Merged dict.  Original dicts are not mutated.
    """
    result: Dict[str, str] = dict(base)

    for key, value in override.items():
        if prefix_filter is not None and not key.startswith(prefix_filter):
            continue

        if key not in result:
            result[key] = value
            continue

        if result[key] == value:
            # identical — no real conflict
            continue

        if strategy is MergeStrategy.RIGHT:
            result[key] = value
        elif strategy is MergeStrategy.LEFT:
            pass  # keep existing base value
        elif strategy is MergeStrategy.ERROR:
            raise MergeConflict(key, result[key], value)

    return result
