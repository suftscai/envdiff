"""Tests for envdiff.normalizer."""

import pytest

from envdiff.normalizer import (
    NormalizeResult,
    normalize_env,
    normalize_keys,
    normalize_values,
)


# ---------------------------------------------------------------------------
# normalize_keys
# ---------------------------------------------------------------------------

def test_uppercase_keys_by_default():
    result = normalize_keys({"db_host": "localhost", "Port": "5432"})
    assert "DB_HOST" in result.normalized
    assert "PORT" in result.normalized


def test_lowercase_keys_option():
    result = normalize_keys({"DB_HOST": "localhost"}, uppercase=False)
    assert "db_host" in result.normalized


def test_renames_records_changed_keys():
    result = normalize_keys({"db_host": "localhost"})
    assert ("db_host", "DB_HOST") in result.renames


def test_already_normalized_key_not_in_renames():
    result = normalize_keys({"DB_HOST": "localhost"})
    assert result.renames == []


def test_whitespace_key_stripped_and_renamed():
    result = normalize_keys({"  MY_KEY  ": "value"})
    assert "MY_KEY" in result.normalized
    assert any(norm == "MY_KEY" for _, norm in result.renames)


def test_value_whitespace_stripped():
    result = normalize_keys({"KEY": "  hello  "})
    assert result.normalized["KEY"] == "hello"
    assert "KEY" in result.stripped


def test_clean_value_not_in_stripped():
    result = normalize_keys({"KEY": "hello"})
    assert result.stripped == []


def test_collision_last_value_wins():
    # Both 'key' and 'KEY' normalize to 'KEY'; last wins.
    result = normalize_keys({"key": "first", "KEY": "second"})
    assert result.normalized["KEY"] == "second"


# ---------------------------------------------------------------------------
# normalize_values
# ---------------------------------------------------------------------------

def test_normalize_values_strips_whitespace():
    result = normalize_values({"A": "  val  ", "B": "clean"})
    assert result.normalized["A"] == "val"
    assert result.normalized["B"] == "clean"


def test_normalize_values_records_stripped_keys():
    result = normalize_values({"A": "  val  ", "B": "clean"})
    assert "A" in result.stripped
    assert "B" not in result.stripped


def test_normalize_values_keys_unchanged():
    result = normalize_values({"lower_key": "value"})
    assert "lower_key" in result.normalized


def test_normalize_values_no_renames():
    result = normalize_values({"KEY": "value"})
    assert result.renames == []


# ---------------------------------------------------------------------------
# normalize_env (combined)
# ---------------------------------------------------------------------------

def test_normalize_env_returns_normalize_result():
    result = normalize_env({"db_host": "localhost"})
    assert isinstance(result, NormalizeResult)


def test_normalize_env_applies_key_and_value_normalization():
    result = normalize_env({"db_host": "  localhost  "})
    assert "DB_HOST" in result.normalized
    assert result.normalized["DB_HOST"] == "localhost"
