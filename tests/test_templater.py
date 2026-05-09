"""Tests for envdiff.templater."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.templater import env_to_template, template_from_diff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(key: str, status: DiffStatus, staging=None, production=None) -> DiffEntry:
    return DiffEntry(key=key, status=status, staging_value=staging, production_value=production)


@pytest.fixture()
def simple_env() -> dict:
    return {"APP_HOST": "localhost", "DB_PASSWORD": "s3cr3t", "PORT": "8080"}


@pytest.fixture()
def diff_result() -> DiffResult:
    entries = [
        _entry("NEW_KEY", DiffStatus.ADDED, production="prod_val"),
        _entry("OLD_KEY", DiffStatus.REMOVED, staging="stg_val"),
        _entry("CHANGED_KEY", DiffStatus.CHANGED, staging="old", production="new"),
        _entry("SAME_KEY", DiffStatus.UNCHANGED, staging="same", production="same"),
    ]
    return DiffResult(entries=entries)


# ---------------------------------------------------------------------------
# env_to_template
# ---------------------------------------------------------------------------

def test_template_contains_all_keys(simple_env):
    out = env_to_template(simple_env)
    for key in simple_env:
        assert key in out


def test_template_uses_placeholder(simple_env):
    out = env_to_template(simple_env)
    assert "<FILL_IN>" in out


def test_sensitive_key_gets_secret_placeholder(simple_env):
    out = env_to_template(simple_env)
    assert "DB_PASSWORD=<SECRET>" in out


def test_non_sensitive_key_gets_fill_in(simple_env):
    out = env_to_template(simple_env)
    assert "PORT=<FILL_IN>" in out


def test_include_values_adds_comment(simple_env):
    out = env_to_template(simple_env, include_values=True)
    assert "# was: 8080" in out


def test_header_is_prepended(simple_env):
    out = env_to_template(simple_env, header="Generated template")
    assert out.startswith("# Generated template")


def test_output_ends_with_newline(simple_env):
    out = env_to_template(simple_env)
    assert out.endswith("\n")


def test_keys_are_sorted(simple_env):
    out = env_to_template(simple_env)
    keys_in_output = [line.split("=")[0] for line in out.splitlines() if "=" in line]
    assert keys_in_output == sorted(keys_in_output)


# ---------------------------------------------------------------------------
# template_from_diff
# ---------------------------------------------------------------------------

def test_diff_template_excludes_unchanged_by_default(diff_result):
    out = template_from_diff(diff_result)
    assert "SAME_KEY" not in out


def test_diff_template_includes_added(diff_result):
    out = template_from_diff(diff_result)
    assert "NEW_KEY" in out


def test_diff_template_includes_removed(diff_result):
    out = template_from_diff(diff_result)
    assert "OLD_KEY" in out


def test_diff_template_includes_changed(diff_result):
    out = template_from_diff(diff_result)
    assert "CHANGED_KEY" in out


def test_diff_template_status_comment(diff_result):
    out = template_from_diff(diff_result)
    assert "[added]" in out or "[ADDED]" in out or "added" in out


def test_diff_template_custom_statuses(diff_result):
    out = template_from_diff(diff_result, statuses={DiffStatus.ADDED})
    assert "NEW_KEY" in out
    assert "OLD_KEY" not in out
    assert "CHANGED_KEY" not in out


def test_diff_template_include_values_shows_staging(diff_result):
    out = template_from_diff(diff_result, include_values=True)
    assert "old" in out  # staging value for CHANGED_KEY


def test_diff_template_empty_when_no_matches(diff_result):
    out = template_from_diff(diff_result, statuses=set())
    assert out == ""
