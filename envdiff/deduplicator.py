"""Deduplicator: detect and resolve duplicate keys across two env dicts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class DuplicateEntry:
    """Represents a key that appears in both envs with potentially different values."""

    key: str
    staging_value: str
    production_value: str

    @property
    def values_match(self) -> bool:
        return self.staging_value == self.production_value

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DuplicateEntry(key={self.key!r}, "
            f"staging={self.staging_value!r}, "
            f"production={self.production_value!r})"
        )


@dataclass
class DeduplicationReport:
    """Summary of duplicate-key analysis between two env dicts."""

    duplicates: List[DuplicateEntry] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.duplicates)

    @property
    def matching(self) -> List[DuplicateEntry]:
        return [d for d in self.duplicates if d.values_match]

    @property
    def conflicting(self) -> List[DuplicateEntry]:
        return [d for d in self.duplicates if not d.values_match]


def find_duplicates(
    staging: Dict[str, str],
    production: Dict[str, str],
) -> DeduplicationReport:
    """Return a DeduplicationReport of keys present in both envs."""
    shared_keys = sorted(set(staging) & set(production))
    entries = [
        DuplicateEntry(
            key=k,
            staging_value=staging[k],
            production_value=production[k],
        )
        for k in shared_keys
    ]
    return DeduplicationReport(duplicates=entries)


def resolve_duplicates(
    staging: Dict[str, str],
    production: Dict[str, str],
    prefer: str = "production",
) -> Tuple[Dict[str, str], DeduplicationReport]:
    """Merge two envs, resolving duplicate keys by *prefer* strategy.

    Args:
        staging: The staging environment dict.
        production: The production environment dict.
        prefer: ``'staging'`` or ``'production'`` (default).

    Returns:
        A tuple of (merged_env, DeduplicationReport).
    """
    if prefer not in ("staging", "production"):
        raise ValueError(f"prefer must be 'staging' or 'production', got {prefer!r}")

    report = find_duplicates(staging, production)
    merged = {**staging, **production} if prefer == "production" else {**production, **staging}
    return merged, report
