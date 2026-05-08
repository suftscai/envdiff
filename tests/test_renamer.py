"""Tests for envdiff.renamer."""

import pytest
from envdiff.renamer import rename_keys, RenameResult


@pytest.fixture()
def env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_SECRET": "s3cr3t",
    }


def test_basic_rename_applies(env):
    result = rename_keys(env, {"DB_HOST": "DATABASE_HOST"})
    assert "DATABASE_HOST" in result.env
    assert result.env["DATABASE_HOST"] == "localhost"


def test_renamed_key_removed_from_env(env):
    result = rename_keys(env, {"DB_HOST": "DATABASE_HOST"})
    assert "DB_HOST" not in result.env


def test_unchanged_keys_preserved(env):
    result = rename_keys(env, {"DB_HOST": "DATABASE_HOST"})
    assert result.env["DB_PORT"] == "5432"
    assert result.env["APP_SECRET"] == "s3cr3t"


def test_applied_records_rename(env):
    result = rename_keys(env, {"DB_HOST": "DATABASE_HOST"})
    assert ("DB_HOST", "DATABASE_HOST") in result.applied


def test_missing_old_key_goes_to_skipped(env):
    result = rename_keys(env, {"MISSING_KEY": "NEW_KEY"})
    assert "MISSING_KEY" in result.skipped
    assert ("MISSING_KEY", "NEW_KEY") not in result.applied


def test_no_overwrite_skips_when_target_exists(env):
    env_with_target = {**env, "DATABASE_HOST": "other"}
    result = rename_keys(env_with_target, {"DB_HOST": "DATABASE_HOST"}, overwrite=False)
    assert "DB_HOST" in result.skipped
    assert result.env["DATABASE_HOST"] == "other"


def test_overwrite_replaces_existing_target(env):
    env_with_target = {**env, "DATABASE_HOST": "other"}
    result = rename_keys(env_with_target, {"DB_HOST": "DATABASE_HOST"}, overwrite=True)
    assert result.env["DATABASE_HOST"] == "localhost"
    assert "DB_HOST" not in result.env


def test_multiple_renames_applied(env):
    mapping = {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"}
    result = rename_keys(env, mapping)
    assert "DATABASE_HOST" in result.env
    assert "DATABASE_PORT" in result.env
    assert len(result.applied) == 2


def test_empty_mapping_returns_original(env):
    result = rename_keys(env, {})
    assert result.env == env
    assert result.applied == []
    assert result.skipped == []


def test_result_env_combines_renamed_and_unchanged(env):
    result = rename_keys(env, {"DB_HOST": "DATABASE_HOST"})
    combined = {**result.unchanged, **result.renamed}
    assert combined == result.env
