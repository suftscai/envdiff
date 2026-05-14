"""Tag environment variable entries with user-defined labels."""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, Iterable, List, Optional

from envdiff.differ import DiffEntry, DiffResult


@dataclass
class TaggedEntry:
    """A diff entry decorated with a set of tags."""

    entry: DiffEntry
    tags: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"TaggedEntry(key={self.entry.key!r}, tags={self.tags!r})"

    @property
    def key(self) -> str:
        return self.entry.key


@dataclass
class TagReport:
    """Collection of tagged entries produced by :func:`tag_diff`."""

    tagged: List[TaggedEntry] = field(default_factory=list)

    def by_tag(self, tag: str) -> List[TaggedEntry]:
        """Return entries that carry *tag*."""
        return [e for e in self.tagged if tag in e.tags]

    def all_tags(self) -> List[str]:
        """Sorted list of every distinct tag used in this report."""
        seen: set = set()
        for te in self.tagged:
            seen.update(te.tags)
        return sorted(seen)

    def __len__(self) -> int:
        return len(self.tagged)


def tag_diff(
    result: DiffResult,
    rules: Dict[str, List[str]],
    *,
    include_unchanged: bool = False,
) -> TagReport:
    """Apply *rules* to entries in *result* and return a :class:`TagReport`.

    *rules* maps a glob pattern (matched against the key) to a list of tags::

        rules = {
            "DB_*": ["database"],
            "*SECRET*": ["sensitive"],
            "AWS_*": ["cloud", "aws"],
        }

    Entries whose status is ``UNCHANGED`` are skipped unless
    *include_unchanged* is ``True``.
    """
    from envdiff.differ import DiffStatus

    tagged: List[TaggedEntry] = []
    for entry in result.entries:
        if entry.status == DiffStatus.UNCHANGED and not include_unchanged:
            continue
        matched_tags: List[str] = []
        for pattern, tags in rules.items():
            if fnmatch(entry.key, pattern):
                for t in tags:
                    if t not in matched_tags:
                        matched_tags.append(t)
        tagged.append(TaggedEntry(entry=entry, tags=matched_tags))

    return TagReport(tagged=tagged)
