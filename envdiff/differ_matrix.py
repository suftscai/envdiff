"""Produce a cross-environment comparison matrix for multiple env sets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import diff_envs, DiffStatus


@dataclass
class MatrixCell:
    """A single cell in the comparison matrix."""

    left_label: str
    right_label: str
    added: int
    removed: int
    changed: int
    unchanged: int

    @property
    def total_differences(self) -> int:
        return self.added + self.removed + self.changed

    @property
    def is_identical(self) -> bool:
        return self.total_differences == 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"MatrixCell({self.left_label!r} vs {self.right_label!r}: "
            f"+{self.added} -{self.removed} ~{self.changed})"
        )


@dataclass
class DiffMatrix:
    """Matrix of pairwise diff statistics across N environments."""

    labels: List[str]
    cells: Dict[tuple, MatrixCell] = field(default_factory=dict)

    def get(self, left: str, right: str) -> Optional[MatrixCell]:
        return self.cells.get((left, right))

    def __len__(self) -> int:
        return len(self.cells)


def build_matrix(envs: Dict[str, Dict[str, str]]) -> DiffMatrix:
    """Build a pairwise diff matrix from a mapping of label -> env dict.

    Args:
        envs: Mapping of environment label to its key/value pairs.

    Returns:
        A DiffMatrix containing one MatrixCell per ordered pair (i, j) where i != j.
    """
    labels = list(envs.keys())
    matrix = DiffMatrix(labels=labels)

    for i, left_label in enumerate(labels):
        for j, right_label in enumerate(labels):
            if i == j:
                continue
            result = diff_envs(envs[left_label], envs[right_label])
            counts: Dict[DiffStatus, int] = {
                DiffStatus.ADDED: 0,
                DiffStatus.REMOVED: 0,
                DiffStatus.CHANGED: 0,
                DiffStatus.UNCHANGED: 0,
            }
            for entry in result.entries:
                counts[entry.status] += 1
            cell = MatrixCell(
                left_label=left_label,
                right_label=right_label,
                added=counts[DiffStatus.ADDED],
                removed=counts[DiffStatus.REMOVED],
                changed=counts[DiffStatus.CHANGED],
                unchanged=counts[DiffStatus.UNCHANGED],
            )
            matrix.cells[(left_label, right_label)] = cell

    return matrix


def format_matrix_text(matrix: DiffMatrix) -> str:
    """Render the matrix as a plain-text table."""
    if not matrix.labels:
        return "(no environments)"

    col_w = max(len(lbl) for lbl in matrix.labels) + 2
    header = f"{'':>{col_w}}" + "".join(f"{lbl:>{col_w}}" for lbl in matrix.labels)
    lines = [header]

    for left in matrix.labels:
        row = f"{left:>{col_w}}"
        for right in matrix.labels:
            if left == right:
                row += f"{'—':>{col_w}}"
            else:
                cell = matrix.cells.get((left, right))
                summary = f"+{cell.added}-{cell.removed}~{cell.changed}" if cell else "?"
                row += f"{summary:>{col_w}}"
        lines.append(row)

    return "\n".join(lines)
