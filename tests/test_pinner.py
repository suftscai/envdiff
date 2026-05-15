"""Tests for envdiff.pinner."""

import pytest

from envdiff.pinner import (
    PinReport,
    PinViolation,
    format_pin_report,
    pin_env,
)


@pytest.fixture()
def pinned() -> dict:
    return {
        "DATABASE_URL": "postgres://prod/db",
        "SECRET_KEY": "s3cr3t",
        "DEBUG": "false",
    }


@pytest.fixture()
def current() -> dict:
    return {
        "DATABASE_URL": "postgres://prod/db",
        "SECRET_KEY": "changed!",
        "EXTRA_KEY": "extra",
    }


def test_returns_pin_report(pinned, current):
    report = pin_env(pinned, current)
    assert isinstance(report, PinReport)


def test_ok_key_when_values_match(pinned, current):
    report = pin_env(pinned, current)
    assert "DATABASE_URL" in report.ok


def test_violation_when_value_changed(pinned, current):
    report = pin_env(pinned, current)
    keys = [v.key for v in report.violations]
    assert "SECRET_KEY" in keys


def test_violation_stores_both_values(pinned, current):
    report = pin_env(pinned, current)
    v = next(v for v in report.violations if v.key == "SECRET_KEY")
    assert v.pinned_value == "s3cr3t"
    assert v.current_value == "changed!"


def test_missing_when_key_absent(pinned, current):
    report = pin_env(pinned, current)
    assert "DEBUG" in report.missing


def test_has_drift_true_when_violations(pinned, current):
    report = pin_env(pinned, current)
    assert report.has_drift is True


def test_has_drift_false_when_all_ok():
    env = {"A": "1", "B": "2"}
    report = pin_env(env, env.copy())
    assert report.has_drift is False


def test_total_counts_all_categories(pinned, current):
    report = pin_env(pinned, current)
    assert report.total == len(report.violations) + len(report.missing) + len(report.ok)


def test_subset_keys_limits_check(pinned, current):
    report = pin_env(pinned, current, keys=["DATABASE_URL"])
    assert report.ok == ["DATABASE_URL"]
    assert report.violations == []
    assert report.missing == []


def test_key_not_in_pinned_is_skipped(pinned, current):
    """Keys listed in `keys` but absent from pinned are silently ignored."""
    report = pin_env(pinned, current, keys=["EXTRA_KEY"])
    assert report.total == 0


def test_format_pin_report_contains_drift(pinned, current):
    report = pin_env(pinned, current)
    text = format_pin_report(report)
    assert "DRIFT" in text
    assert "SECRET_KEY" in text


def test_format_pin_report_contains_missing(pinned, current):
    report = pin_env(pinned, current)
    text = format_pin_report(report)
    assert "MISSING" in text
    assert "DEBUG" in text


def test_format_pin_report_no_keys_message():
    report = pin_env({}, {})
    text = format_pin_report(report)
    assert "No pinned keys checked" in text
