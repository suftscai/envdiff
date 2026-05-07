"""Tests for envdiff.merger."""

import pytest

from envdiff.merger import MergeConflict, MergeStrategy, merge_envs


@pytest.fixture()
def base() -> dict:
    return {"APP_HOST": "localhost", "APP_PORT": "8000", "DEBUG": "true"}


@pytest.fixture()
def override() -> dict:
    return {"APP_PORT": "9000", "APP_SECRET": "s3cr3t", "DEBUG": "true"}


def test_unique_keys_are_included(base, override):
    result = merge_envs(base, override)
    assert "APP_SECRET" in result


def test_right_strategy_prefers_override(base, override):
    result = merge_envs(base, override, strategy=MergeStrategy.RIGHT)
    assert result["APP_PORT"] == "9000"


def test_left_strategy_keeps_base(base, override):
    result = merge_envs(base, override, strategy=MergeStrategy.LEFT)
    assert result["APP_PORT"] == "8000"


def test_identical_values_cause_no_conflict(base, override):
    # DEBUG is "true" in both — should never raise regardless of strategy
    result = merge_envs(base, override, strategy=MergeStrategy.ERROR)
    assert result["DEBUG"] == "true"


def test_error_strategy_raises_on_conflict(base, override):
    with pytest.raises(MergeConflict) as exc_info:
        merge_envs(base, override, strategy=MergeStrategy.ERROR)
    assert exc_info.value.key == "APP_PORT"
    assert exc_info.value.left == "8000"
    assert exc_info.value.right == "9000"


def test_error_conflict_message_contains_key(base, override):
    with pytest.raises(MergeConflict, match="APP_PORT"):
        merge_envs(base, override, strategy=MergeStrategy.ERROR)


def test_prefix_filter_limits_override_keys(base, override):
    # Only APP_* keys from override should be merged
    result = merge_envs(base, override, prefix_filter="APP_")
    # APP_PORT and APP_SECRET are in override under APP_ prefix
    assert result["APP_SECRET"] == "s3cr3t"
    # DEBUG is not under APP_ prefix, so it should remain from base
    assert result["DEBUG"] == "true"


def test_prefix_filter_excludes_non_matching_keys():
    b = {"X_FOO": "1"}
    o = {"Y_BAR": "2", "X_BAZ": "3"}
    result = merge_envs(b, o, prefix_filter="X_")
    assert "Y_BAR" not in result
    assert result["X_BAZ"] == "3"


def test_base_not_mutated(base, override):
    original_base = dict(base)
    merge_envs(base, override)
    assert base == original_base


def test_empty_base_returns_override_copy(override):
    result = merge_envs({}, override)
    assert result == override
    assert result is not override


def test_empty_override_returns_base_copy(base):
    result = merge_envs(base, {})
    assert result == base
    assert result is not base
