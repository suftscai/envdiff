"""Lint env files for common style and correctness issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.parser import parse_env_file


@dataclass
class LintIssue:
    line: int
    key: str
    code: str
    message: str
    severity: str  # "error" | "warning" | "info"

    def __repr__(self) -> str:  # pragma: no cover
        return f"LintIssue(line={self.line}, key={self.key!r}, code={self.code}, severity={self.severity})"


@dataclass
class LintReport:
    label: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


_NAMING_CONVENTION_CHARS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
)


def lint_file(path: str, label: str = "") -> LintReport:
    """Parse *path* and return a LintReport with style/correctness issues."""
    report = LintReport(label=label or path)
    raw_lines: list[str] = []
    with open(path, encoding="utf-8") as fh:
        raw_lines = fh.readlines()

    env = parse_env_file(path)
    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Detect duplicate keys
        key_part = stripped.lstrip("export ").split("=")[0].strip()
        if key_part in seen_keys:
            report.issues.append(LintIssue(
                line=lineno,
                key=key_part,
                code="E001",
                message=f"Duplicate key '{key_part}' (first seen on line {seen_keys[key_part]})",
                severity="error",
            ))
        else:
            seen_keys[key_part] = lineno

        # Naming convention: should be UPPER_SNAKE_CASE
        if key_part and not all(c in _NAMING_CONVENTION_CHARS for c in key_part):
            report.issues.append(LintIssue(
                line=lineno,
                key=key_part,
                code="W001",
                message=f"Key '{key_part}' does not follow UPPER_SNAKE_CASE convention",
                severity="warning",
            ))

    # Check for empty values via parsed dict
    for key, value in env.items():
        if value == "":
            lineno = next(
                (i for i, l in enumerate(raw_lines, 1)
                 if key in l and "=" in l), 0
            )
            report.issues.append(LintIssue(
                line=lineno,
                key=key,
                code="W002",
                message=f"Key '{key}' has an empty value",
                severity="warning",
            ))

    return report
