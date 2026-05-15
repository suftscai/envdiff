"""Pin environment variable values to a reference snapshot for drift detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PinViolation:
    key: str
    pinned_value: str
    current_value: Optional[str]

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PinViolation(key={self.key!r}, "
            f"pinned={self.pinned_value!r}, "
            f"current={self.current_value!r})"
        )


@dataclass
class PinReport:
    violations: List[PinViolation] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    ok: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.violations) + len(self.missing) + len(self.ok)

    @property
    def has_drift(self) -> bool:
        return bool(self.violations or self.missing)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PinReport(violations={len(self.violations)}, "
            f"missing={len(self.missing)}, ok={len(self.ok)})"
        )


def pin_env(
    pinned: Dict[str, str],
    current: Dict[str, str],
    keys: Optional[List[str]] = None,
) -> PinReport:
    """Compare *current* env against *pinned* reference values.

    Args:
        pinned: Reference key/value mapping (the "pinned" state).
        current: The env to check for drift.
        keys: Subset of keys to check. Defaults to all keys in *pinned*.

    Returns:
        A :class:`PinReport` describing any drift found.
    """
    check_keys = keys if keys is not None else list(pinned.keys())
    report = PinReport()

    for key in check_keys:
        if key not in pinned:
            continue
        pinned_value = pinned[key]
        if key not in current:
            report.missing.append(key)
        elif current[key] != pinned_value:
            report.violations.append(
                PinViolation(
                    key=key,
                    pinned_value=pinned_value,
                    current_value=current[key],
                )
            )
        else:
            report.ok.append(key)

    return report


def format_pin_report(report: PinReport) -> str:
    """Return a human-readable summary of a :class:`PinReport`."""
    lines: List[str] = []
    for v in report.violations:
        lines.append(f"[DRIFT]   {v.key}: pinned={v.pinned_value!r}  current={v.current_value!r}")
    for k in report.missing:
        lines.append(f"[MISSING] {k}: key absent from current env")
    for k in report.ok:
        lines.append(f"[OK]      {k}")
    if not lines:
        return "No pinned keys checked."
    return "\n".join(lines)
