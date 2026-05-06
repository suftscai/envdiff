"""Validate env files and diff results for common issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: str  # 'error' | 'warning'

    def __repr__(self) -> str:
        return f"ValidationIssue({self.severity}, {self.key!r}: {self.message})"


@dataclass
class ValidationReport:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def validate_env_dict(env: Dict[str, str], label: str = "env") -> ValidationReport:
    """Check a parsed env dict for structural issues."""
    report = ValidationReport()
    for key, value in env.items():
        if not key:
            report.issues.append(ValidationIssue(key="(empty)", message="Empty key found", severity="error"))
        if key != key.strip():
            report.issues.append(ValidationIssue(key=key, message="Key has leading/trailing whitespace", severity="warning"))
        if value == "":
            report.issues.append(ValidationIssue(key=key, message=f"[{label}] Key has an empty value", severity="warning"))
        if " " in key:
            report.issues.append(ValidationIssue(key=key, message="Key contains spaces", severity="error"))
    return report


def validate_diff(result: DiffResult) -> ValidationReport:
    """Inspect a DiffResult for noteworthy conditions."""
    report = ValidationReport()
    for entry in result.entries:
        if entry.status == DiffStatus.ADDED and entry.new_value == "":
            report.issues.append(
                ValidationIssue(key=entry.key, message="Added key has empty value in production", severity="warning")
            )
        if entry.status == DiffStatus.REMOVED:
            report.issues.append(
                ValidationIssue(key=entry.key, message="Key present in staging but missing in production", severity="error")
            )
        if entry.status == DiffStatus.CHANGED and (entry.new_value == "" or entry.old_value == ""):
            report.issues.append(
                ValidationIssue(key=entry.key, message="Changed key has an empty value on one side", severity="warning")
            )
    return report
