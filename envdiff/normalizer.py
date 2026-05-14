"""Normalize environment variable keys and values for consistent comparison."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class NormalizeResult:
    """Result of normalizing an env dict."""

    normalized: Dict[str, str]
    renames: List[Tuple[str, str]] = field(default_factory=list)  # (original, normalized)
    stripped: List[str] = field(default_factory=list)  # keys whose values were stripped

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"NormalizeResult(keys={len(self.normalized)}, "
            f"renames={len(self.renames)}, stripped={len(self.stripped)})"
        )


def normalize_keys(env: Dict[str, str], *, uppercase: bool = True) -> NormalizeResult:
    """Normalize env keys to uppercase (or lowercase) and strip whitespace.

    If two keys collide after normalization the last one (in iteration order) wins.
    """
    normalized: Dict[str, str] = {}
    renames: List[Tuple[str, str]] = []
    stripped: List[str] = []

    for raw_key, value in env.items():
        clean_key = raw_key.strip()
        norm_key = clean_key.upper() if uppercase else clean_key.lower()

        if norm_key != raw_key:
            renames.append((raw_key, norm_key))

        clean_value = value.strip()
        if clean_value != value:
            stripped.append(norm_key)

        normalized[norm_key] = clean_value

    return NormalizeResult(normalized=normalized, renames=renames, stripped=stripped)


def normalize_values(env: Dict[str, str]) -> NormalizeResult:
    """Strip leading/trailing whitespace from all values only."""
    normalized: Dict[str, str] = {}
    stripped: List[str] = []

    for key, value in env.items():
        clean = value.strip()
        if clean != value:
            stripped.append(key)
        normalized[key] = clean

    return NormalizeResult(normalized=normalized, stripped=stripped)


def normalize_env(env: Dict[str, str], *, uppercase: bool = True) -> NormalizeResult:
    """Apply both key and value normalization in one pass."""
    return normalize_keys(env, uppercase=uppercase)
