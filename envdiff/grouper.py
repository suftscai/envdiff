"""Group diff entries by key prefix (e.g. DB_, AWS_, APP_)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffEntry, DiffResult


@dataclass
class PrefixGroup:
    """A named group of DiffEntry objects sharing a common key prefix."""

    prefix: str
    entries: List[DiffEntry] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"PrefixGroup(prefix={self.prefix!r}, count={len(self.entries)})"

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def prefixes_used(self) -> List[str]:
        """Distinct first-segment prefixes present in this group."""
        return [self.prefix]


@dataclass
class GroupReport:
    """Collection of PrefixGroup objects produced by group_by_prefix."""

    groups: Dict[str, PrefixGroup] = field(default_factory=dict)
    ungrouped: List[DiffEntry] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"GroupReport(groups={list(self.groups.keys())}, "
            f"ungrouped={len(self.ungrouped)})"
        )

    @property
    def total(self) -> int:
        return sum(g.total for g in self.groups.values()) + len(self.ungrouped)

    def get(self, prefix: str) -> Optional[PrefixGroup]:
        return self.groups.get(prefix.upper())


def group_by_prefix(
    result: DiffResult,
    prefixes: Optional[List[str]] = None,
    *,
    include_unchanged: bool = False,
    separator: str = "_",
) -> GroupReport:
    """Group diff entries by key prefix.

    Args:
        result: DiffResult to group.
        prefixes: Explicit list of prefixes to group by.  When *None* every
            key segment before the first *separator* is used as the prefix.
        include_unchanged: When False (default) UNCHANGED entries are skipped.
        separator: Character used to split a key into prefix + rest.

    Returns:
        GroupReport with one PrefixGroup per discovered (or requested) prefix
        and an *ungrouped* list for keys that did not match any prefix.
    """
    from envdiff.differ import DiffStatus

    buckets: Dict[str, List[DiffEntry]] = defaultdict(list)
    ungrouped: List[DiffEntry] = []

    explicit = [p.upper() for p in prefixes] if prefixes else None

    for entry in result.entries:
        if not include_unchanged and entry.status == DiffStatus.UNCHANGED:
            continue

        key_upper = entry.key.upper()
        matched = False

        if explicit is not None:
            for p in explicit:
                if key_upper.startswith(p + separator) or key_upper == p:
                    buckets[p].append(entry)
                    matched = True
                    break
        else:
            if separator in entry.key:
                auto_prefix = key_upper.split(separator, 1)[0]
                buckets[auto_prefix].append(entry)
                matched = True

        if not matched:
            ungrouped.append(entry)

    groups = {p: PrefixGroup(prefix=p, entries=entries) for p, entries in buckets.items()}
    return GroupReport(groups=groups, ungrouped=ungrouped)
