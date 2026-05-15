"""Tests for envdiff.trimmer."""

from __future__ import annotations

import pytest

from envdiff.trimmer import TrimResult, trim_keys


ENV = {
    "APP_NAME": "myapp",
    "APP_VERSION": "1.0",
    "DB_HOST": "localhost",
    "DB_PASSWORD": "secret",
    "SECRET_KEY": "abc123",
    "DEBUG": "true",
}


def test_returns_trim_result():
    result = trim_keys(ENV, keys=["DEBUG"])
    assert isinstance(result, TrimResult)


def test_trim_by_explicit_keys():
    result = trim_keys(ENV, keys=["DEBUG", "APP_NAME"])
    assert "DEBUG" not in result.env
    assert "APP_NAME" not in result.env


def test_trim_by_explicit_keys_preserves_others():
    result = trim_keys(ENV, keys=["DEBUG"])
    assert "APP_NAME" in result.env
    assert "DB_HOST" in result.env


def test_trim_by_prefix():
    result = trim_keys(ENV, prefix="DB_")
    assert "DB_HOST" not in result.env
    assert "DB_PASSWORD" not in result.env


def test_trim_by_prefix_keeps_non_matching():
    result = trim_keys(ENV, prefix="DB_")
    assert "APP_NAME" in result.env
    assert "SECRET_KEY" in result.env


def test_trim_by_pattern():
    result = trim_keys(ENV, pattern=r"SECRET|PASSWORD")
    assert "DB_PASSWORD" not in result.env
    assert "SECRET_KEY" not in result.env


def test_trim_by_pattern_keeps_non_matching():
    result = trim_keys(ENV, pattern=r"SECRET|PASSWORD")
    assert "APP_NAME" in result.env
    assert "DEBUG" in result.env


def test_removed_list_is_sorted():
    result = trim_keys(ENV, prefix="APP_")
    assert result.removed == sorted(result.removed)


def test_total_removed_count():
    result = trim_keys(ENV, prefix="APP_")
    assert result.total_removed == 2


def test_combined_criteria_uses_or_logic():
    result = trim_keys(ENV, keys=["DEBUG"], prefix="DB_")
    assert "DEBUG" not in result.env
    assert "DB_HOST" not in result.env
    assert "DB_PASSWORD" not in result.env
    assert "APP_NAME" in result.env


def test_no_criteria_raises_value_error():
    with pytest.raises(ValueError, match="At least one of"):
        trim_keys(ENV)


def test_unknown_key_in_keys_list_is_ignored():
    result = trim_keys(ENV, keys=["NONEXISTENT"])
    assert result.total_removed == 0
    assert result.env == ENV


def test_empty_env_returns_empty_result():
    result = trim_keys({}, keys=["FOO"])
    assert result.env == {}
    assert result.removed == []
