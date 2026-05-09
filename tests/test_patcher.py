"""Tests for envdiff.patcher."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffStatus, diff_envs
from envdiff.patcher import patch_env, PatchResult


@pytest.fixture()
def staging() -> dict:
    return {
        "APP_ENV": "staging",
        "DB_HOST": "staging-db.internal",
        "OLD_FLAG": "yes",
        "SHARED": "same",
    }


@pytest.fixture()
def production() -> dict:
    return {
        "APP_ENV": "production",
        "DB_HOST": "prod-db.internal",
        "NEW_KEY": "prod-only",
        "SHARED": "same",
    }


@pytest.fixture()
def diff(staging, production):
    return diff_envs(staging, production)


def test_patch_result_is_patch_result(staging, diff):
    result = patch_env(staging, diff)
    assert isinstance(result, PatchResult)


def test_changed_key_gets_production_value(staging, diff):
    result = patch_env(staging, diff)
    assert result.patched["APP_ENV"] == "production"
    assert result.patched["DB_HOST"] == "prod-db.internal"


def test_removed_key_is_absent(staging, diff):
    result = patch_env(staging, diff)
    assert "OLD_FLAG" not in result.patched


def test_added_key_is_present(staging, diff):
    result = patch_env(staging, diff)
    assert result.patched["NEW_KEY"] == "prod-only"


def test_unchanged_key_preserved(staging, diff):
    result = patch_env(staging, diff)
    assert result.patched["SHARED"] == "same"


def test_applied_list_contains_changed_keys(staging, diff):
    result = patch_env(staging, diff)
    assert "APP_ENV" in result.applied
    assert "DB_HOST" in result.applied


def test_applied_list_contains_removed_key(staging, diff):
    result = patch_env(staging, diff)
    assert "OLD_FLAG" in result.applied


def test_unchanged_keys_in_skipped(staging, diff):
    result = patch_env(staging, diff)
    assert "SHARED" in result.skipped


def test_limit_to_added_only(staging, diff):
    result = patch_env(staging, diff, statuses=[DiffStatus.ADDED])
    assert result.patched["NEW_KEY"] == "prod-only"
    # CHANGED keys should be untouched
    assert result.patched["APP_ENV"] == "staging"
    # REMOVED key should still be present
    assert "OLD_FLAG" in result.patched


def test_base_dict_not_mutated(staging, diff):
    original = dict(staging)
    patch_env(staging, diff)
    assert staging == original


def test_dry_run_returns_same_result(staging, diff):
    normal = patch_env(staging, diff)
    dry = patch_env(staging, diff, dry_run=True)
    assert normal.patched == dry.patched
