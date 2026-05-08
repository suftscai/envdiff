"""Rename keys across an env mapping, with optional dry-run support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class RenameResult:
    """Outcome of applying a rename mapping to an env dict."""

    renamed: Dict[str, str] = field(default_factory=dict)   # new_key -> value
    unchanged: Dict[str, str] = field(default_factory=dict) # key -> value
    applied: List[Tuple[str, str]] = field(default_factory=list)  # (old, new)
    skipped: List[str] = field(default_factory=list)  # old keys not found

    @property
    def env(self) -> Dict[str, str]:
        """Merged view: unchanged keys + renamed keys."""
        return {**self.unchanged, **self.renamed}


def rename_keys(
    env: Dict[str, str],
    mapping: Dict[str, str],
    *,
    overwrite: bool = False,
) -> RenameResult:
    """Rename keys in *env* according to *mapping* (old -> new).

    Parameters
    ----------
    env:
        Source environment dict.
    mapping:
        Dict of {old_key: new_key} renames to apply.
    overwrite:
        If *True*, allow the new key to overwrite an existing key in *env*.
        If *False* (default) the rename is skipped when the target key already
        exists and the old key is added to ``skipped``.
    """
    result = RenameResult()
    working = dict(env)

    for old_key, new_key in mapping.items():
        if old_key not in working:
            result.skipped.append(old_key)
            continue

        if new_key in working and not overwrite:
            result.skipped.append(old_key)
            continue

        value = working.pop(old_key)
        working[new_key] = value
        result.applied.append((old_key, new_key))

    for key, value in working.items():
        if any(new == key for _, new in result.applied):
            result.renamed[key] = value
        else:
            result.unchanged[key] = value

    return result
