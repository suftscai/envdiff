"""Export diff results to various file formats (JSON, CSV, Markdown)."""

from __future__ import annotations

import csv
import io
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from envdiff.differ import DiffResult

from envdiff.differ import DiffStatus
from envdiff.reporter import build_report


def export_json(result: "DiffResult", mask: bool = False) -> str:
    """Serialize a DiffResult to a JSON string."""
    report = build_report(result, mask=mask)
    return json.dumps(report, indent=2)


def export_csv(result: "DiffResult", mask: bool = False) -> str:
    """Serialize a DiffResult to a CSV string.

    Columns: key, status, staging_value, production_value
    """
    from envdiff.masker import mask_env

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["key", "status", "staging_value", "production_value"])

    for entry in result.entries:
        if entry.status == DiffStatus.UNCHANGED:
            continue
        staging_val = entry.left_value or ""
        prod_val = entry.right_value or ""
        if mask:
            from envdiff.masker import is_sensitive, mask_value
            if is_sensitive(entry.key):
                staging_val = mask_value(staging_val) if staging_val else ""
                prod_val = mask_value(prod_val) if prod_val else ""
        writer.writerow([entry.key, entry.status.value, staging_val, prod_val])

    return buf.getvalue()


def export_markdown(result: "DiffResult", mask: bool = False) -> str:
    """Serialize a DiffResult to a Markdown table string."""
    from envdiff.masker import is_sensitive, mask_value

    lines: list[str] = []
    lines.append("| Key | Status | Staging | Production |")
    lines.append("|-----|--------|---------|------------|")

    for entry in result.entries:
        if entry.status == DiffStatus.UNCHANGED:
            continue
        staging_val = entry.left_value or ""
        prod_val = entry.right_value or ""
        if mask and is_sensitive(entry.key):
            staging_val = mask_value(staging_val) if staging_val else ""
            prod_val = mask_value(prod_val) if prod_val else ""
        lines.append(
            f"| `{entry.key}` | {entry.status.value} "
            f"| {staging_val} | {prod_val} |"
        )

    summary = result.summary
    lines.append("")
    lines.append(
        f"**Summary**: {summary['added']} added, "
        f"{summary['removed']} removed, "
        f"{summary['changed']} changed, "
        f"{summary['unchanged']} unchanged."
    )
    return "\n".join(lines)
