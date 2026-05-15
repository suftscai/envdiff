"""Trimmer: remove keys from an env dict based on patterns or an explicit list."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TrimResult:
    """Result of a trim operation."""

    env: Dict[str, str]
    removed: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"TrimResult(kept={len(self.env)}, removed={len(self.removed)})"
        )

    @property
    def total_removed(self) -> int:
        return len(self.removed)


def trim_keys(
    env: Dict[str, str],
    *,
    keys: Optional[List[str]] = None,
    prefix: Optional[str] = None,
    pattern: Optional[str] = None,
) -> TrimResult:
    """Return a new env dict with matching keys removed.

    Parameters
    ----------
    env:
        Source environment mapping.
    keys:
        Explicit list of key names to remove.
    prefix:
        Remove all keys whose name starts with this prefix (case-sensitive).
    pattern:
        Remove all keys matching this regular-expression pattern.

    At least one of *keys*, *prefix*, or *pattern* must be supplied.
    Multiple criteria are combined with OR logic.
    """
    if not any([keys, prefix, pattern]):
        raise ValueError("At least one of keys, prefix, or pattern must be provided.")

    key_set = set(keys or [])
    compiled: Optional[re.Pattern[str]] = re.compile(pattern) if pattern else None

    kept: Dict[str, str] = {}
    removed: List[str] = []

    for k, v in env.items():
        should_remove = (
            k in key_set
            or (prefix is not None and k.startswith(prefix))
            or (compiled is not None and compiled.search(k) is not None)
        )
        if should_remove:
            removed.append(k)
        else:
            kept[k] = v

    return TrimResult(env=kept, removed=sorted(removed))
