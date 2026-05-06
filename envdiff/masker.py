"""Utilities for masking sensitive environment variable values."""

from __future__ import annotations

import re
from typing import Dict

# Patterns whose values should be redacted in output
_SENSITIVE_PATTERNS = re.compile(
    r"(password|secret|token|key|api_key|auth|credential|private|passphrase)",
    re.IGNORECASE,
)

MASK_PLACEHOLDER = "***"


def is_sensitive(key: str) -> bool:
    """Return True if *key* looks like it holds a sensitive value."""
    return bool(_SENSITIVE_PATTERNS.search(key))


def mask_value(key: str, value: str, *, placeholder: str = MASK_PLACEHOLDER) -> str:
    """Return *value* unchanged, or *placeholder* if *key* is sensitive."""
    return placeholder if is_sensitive(key) else value


def mask_env(
    env: Dict[str, str],
    *,
    placeholder: str = MASK_PLACEHOLDER,
) -> Dict[str, str]:
    """Return a copy of *env* with sensitive values replaced by *placeholder*."""
    return {
        k: mask_value(k, v, placeholder=placeholder) for k, v in env.items()
    }
