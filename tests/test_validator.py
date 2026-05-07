"""Tests for envdiff.validator."""

import pytest

from envdiff.validator import validate_env_dict, validate_diff, ValidationIssue
from envdiff.differ import diff, DiffStatus


# ---------------------------------------------------------------------------
# validate_env_dict
# ---------------------------------------------------------------------------

def test_clean_env_has_no_issues():
    env = {"DATABASE_URL": "postgres://localhost/db", "DEBUG": "true"}
    report = validate_env_dict(env)
    assert report.ok
    assert report.issues == []


def test_empty_value_produces_warning():
    env = {"SECRET_KEY": ""}
    report = validate_env_dict(env)
    assert any(i.key == "SECRET_KEY" and i.severity == "warning" for i in report.issues)


def test_key_with_spaces_produces_error():
    env = {"BAD KEY": "value"}
    report = validate_env_dict(env)
    assert not report.ok
    assert any(i.key == "BAD KEY" and i.severity == "error" for i in report.issues)


def test_key_with_whitespace_padding_produces_warning():
    env = {" PADDED": "value"}
    report = validate_env_dict(env)
    assert any(" PADDED" in i.key and i.severity == "warning" for i in report.issues)


def test_label_appears_in_empty_value_message():
    env = {"TOKEN": ""}
    report = validate_env_dict(env, label="staging")
    assert any("staging" in i.message for i in report.issues)


def test_multiple_issues_collected():
    env = {"A B": "", "GOOD": "ok"}
    report = validate_env_dict(env)
    # space-in-key error + empty-value warning
    assert len(report.issues) >= 2


# ---------------------------------------------------------------------------
# validate_diff
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    return {"HOST": "localhost", "PORT": "5432", "REMOVED_KEY": "gone"}


@pytest.fixture()
def production():
    return {"HOST": "prod.db", "PORT": "", "NEW_KEY": ""}


def test_removed_key_is_error(staging, production):
    result = diff(staging, production)
    report = validate_diff(result)
    removed_errors = [i for i in report.errors if i.key == "REMOVED_KEY"]
    assert removed_errors, "Expected an error for REMOVED_KEY"


def test_added_empty_value_is_warning(staging, production):
    result = diff(staging, production)
    report = validate_diff(result)
    warnings = [i for i in report.warnings if i.key == "NEW_KEY"]
    assert warnings


def test_changed_to_empty_is_warning(staging, production):
    result = diff(staging, production)
    report = validate_diff(result)
    warnings = [i for i in report.warnings if i.key == "PORT"]
    assert warnings


def test_report_ok_false_when_errors_present(staging, production):
    result = diff(staging, production)
    report = validate_diff(result)
    assert not report.ok


def test_clean_diff_has_no_issues():
    s = {"KEY": "value"}
    p = {"KEY": "value"}
    result = diff(s, p)
    report = validate_diff(result)
    assert report.ok
    assert report.issues == []


def test_validate_diff_errors_and_warnings_are_subsets_of_issues(staging, production):
    """report.errors and report.warnings must be consistent subsets of report.issues."""
    result = diff(staging, production)
    report = validate_diff(result)
    assert all(i.severity == "error" for i in report.errors)
    assert all(i.severity == "warning" for i in report.warnings)
    assert set(report.errors) | set(report.warnings) <= set(report.issues)
