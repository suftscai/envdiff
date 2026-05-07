"""Tests for envdiff.linter."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envdiff.linter import lint_file, LintIssue


@pytest.fixture()
def tmp_env(tmp_path: Path):
    """Return a helper that writes an env file and returns its path."""
    def _write(content: str) -> str:
        p = tmp_path / "test.env"
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return str(p)
    return _write


def test_clean_file_has_no_issues(tmp_env):
    path = tmp_env("""
        APP_NAME=myapp
        APP_ENV=production
        MAX_RETRIES=3
    """)
    report = lint_file(path, label="prod")
    assert report.ok
    assert report.issues == []


def test_duplicate_key_is_error(tmp_env):
    path = tmp_env("""
        DB_HOST=localhost
        DB_HOST=remotehost
    """)
    report = lint_file(path)
    errors = report.errors
    assert len(errors) == 1
    assert errors[0].code == "E001"
    assert "DB_HOST" in errors[0].message


def test_lowercase_key_is_warning(tmp_env):
    path = tmp_env("""
        app_name=myapp
    """)
    report = lint_file(path)
    warnings = [i for i in report.warnings if i.code == "W001"]
    assert len(warnings) == 1
    assert "app_name" in warnings[0].message


def test_empty_value_is_warning(tmp_env):
    path = tmp_env("""
        SOME_TOKEN=
    """)
    report = lint_file(path)
    warnings = [i for i in report.warnings if i.code == "W002"]
    assert len(warnings) == 1
    assert "SOME_TOKEN" in warnings[0].message


def test_export_prefix_accepted(tmp_env):
    path = tmp_env("""
        export API_KEY=abc123
    """)
    report = lint_file(path)
    assert report.ok


def test_label_stored_in_report(tmp_env):
    path = tmp_env("FOO=bar\n")
    report = lint_file(path, label="staging")
    assert report.label == "staging"


def test_ok_false_when_errors_present(tmp_env):
    path = tmp_env("""
        DUPE=one
        DUPE=two
    """)
    report = lint_file(path)
    assert not report.ok


def test_comments_and_blanks_ignored(tmp_env):
    path = tmp_env("""
        # This is a comment

        APP=value
    """)
    report = lint_file(path)
    assert report.issues == []


def test_lint_issue_repr():
    issue = LintIssue(line=3, key="foo", code="W001", message="test", severity="warning")
    r = repr(issue)
    assert "W001" in r
    assert "foo" in r
