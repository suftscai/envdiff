"""Redact sensitive values from env dicts before display or export."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.masker import is_sensitive, mask_value

DEFAULT_PLACEHOLDER = "***REDACTED***"


@dataclass
class RedactionReport:
    """Result of a redaction pass over an env dict."""

    original: Dict[str, str]
    redacted: Dict[str, str]
    redacted_keys: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RedactionReport(total={len(self.original)}, "
            f"redacted={len(self.redacted_keys)})"
        )

    @property
    def total(self) -> int:
        return len(self.original)

    @property
    def redaction_count(self) -> int:
        return len(self.redacted_keys)

    @property
    def clean(self) -> bool:
        """True when no keys were redacted."""
        return self.redaction_count == 0


def redact_env(
    env: Dict[str, str],
    placeholder: str = DEFAULT_PLACEHOLDER,
    extra_keys: Optional[List[str]] = None,
) -> RedactionReport:
    """Return a RedactionReport with sensitive values replaced by *placeholder*.

    Parameters
    ----------
    env:
        Raw key/value mapping to redact.
    placeholder:
        Replacement string for sensitive values.
    extra_keys:
        Additional key names (case-insensitive) to treat as sensitive beyond
        the defaults recognised by :func:`~envdiff.masker.is_sensitive`.
    """
    extra_keys = [k.upper() for k in (extra_keys or [])]
    redacted: Dict[str, str] = {}
    redacted_keys: List[str] = []

    for key, value in env.items():
        if is_sensitive(key) or key.upper() in extra_keys:
            redacted[key] = mask_value(key, value, placeholder=placeholder)
            redacted_keys.append(key)
        else:
            redacted[key] = value

    return RedactionReport(
        original=dict(env),
        redacted=redacted,
        redacted_keys=sorted(redacted_keys),
    )
