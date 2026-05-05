"""Tests for envdiff.differ."""

import pytest

from envdiff.differ import DiffStatus, diff_envs


@pytest.fixture
def staging():
    return {"DB_HOST": "staging-db", "DEBUG": "true", "SECRET": "abc123"}


@pytest.fixture
def production():
    return {"DB_HOST": "prod-db", "DEBUG": "false", "PORT": "8080"}


def test_added_keys(staging, production):
    result = diff_envs(staging, production)
    keys = {e.key for e in result.added}
    assert keys == {"PORT"}


def test_removed_keys(staging, production):
    result = diff_envs(staging, production)
    keys = {e.key for e in result.removed}
    assert keys == {"SECRET"}


def test_changed_keys(staging, production):
    result = diff_envs(staging, production)
    keys = {e.key for e in result.changed}
    assert keys == {"DB_HOST", "DEBUG"}


def test_no_unchanged_by_default(staging, production):
    result = diff_envs(staging, production)
    assert result.unchanged == []


def test_include_unchanged(staging):
    result = diff_envs(staging, staging, include_unchanged=True)
    assert all(e.status == DiffStatus.UNCHANGED for e in result.entries)
    assert len(result.entries) == len(staging)


def test_has_differences_true(staging, production):
    result = diff_envs(staging, production)
    assert result.has_differences is True


def test_has_differences_false(staging):
    result = diff_envs(staging, staging)
    assert result.has_differences is False


def test_identical_envs_empty_result():
    env = {"FOO": "bar"}
    result = diff_envs(env, env)
    assert result.entries == []


def test_empty_left():
    result = diff_envs({}, {"NEW": "val"})
    assert len(result.added) == 1
    assert result.added[0].key == "NEW"
    assert result.added[0].right_value == "val"


def test_empty_right():
    result = diff_envs({"OLD": "val"}, {})
    assert len(result.removed) == 1
    assert result.removed[0].left_value == "val"


def test_entries_sorted():
    left = {"Z": "1", "A": "2", "M": "3"}
    right = {"Z": "1", "A": "changed", "M": "3"}
    result = diff_envs(left, right, include_unchanged=True)
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)
