"""Tests for envdiff.auditor."""
import pytest

from envdiff.differ import DiffResult, DiffEntry, DiffStatus
from envdiff.auditor import AuditEvent, AuditReport, build_audit, format_audit_text


@pytest.fixture()
def staging() -> dict:
    return {"DB_HOST": "localhost", "API_KEY": "abc", "PORT": "8080"}


@pytest.fixture()
def production() -> dict:
    return {"DB_HOST": "prod-db", "API_KEY": "abc", "NEW_KEY": "hello"}


@pytest.fixture()
def result(staging, production) -> DiffResult:
    from envdiff.differ import diff
    return diff(staging, production)


@pytest.fixture()
def report(result) -> AuditReport:
    """Pre-built audit report used by multiple tests."""
    return build_audit(result)


def test_build_audit_returns_audit_report(result):
    report = build_audit(result)
    assert isinstance(report, AuditReport)


def test_build_audit_excludes_unchanged(report):
    statuses = [e.status for e in report.events]
    assert DiffStatus.UNCHANGED not in statuses


def test_build_audit_total_count(report):
    # DB_HOST changed, PORT removed, NEW_KEY added = 3 events
    assert report.total == 3


def test_build_audit_label_stored(result):
    report = build_audit(result, label="sprint-42")
    assert report.label == "sprint-42"
    for event in report.events:
        assert event.label == "sprint-42"


def test_keys_added(report):
    assert "NEW_KEY" in report.keys_added()


def test_keys_removed(report):
    assert "PORT" in report.keys_removed()


def test_keys_changed(report):
    assert "DB_HOST" in report.keys_changed()


def test_by_status_grouping(report):
    grouped = report.by_status
    assert DiffStatus.ADDED in grouped
    assert DiffStatus.REMOVED in grouped
    assert DiffStatus.CHANGED in grouped


def test_format_audit_text_contains_key(report):
    text = format_audit_text(report)
    assert "DB_HOST" in text
    assert "NEW_KEY" in text
    assert "PORT" in text


def test_format_audit_text_empty_report():
    report = AuditReport(events=[])
    text = format_audit_text(report)
    assert "No audit events" in text


def test_format_audit_text_shows_label(result):
    report = build_audit(result, label="release-v2")
    text = format_audit_text(report)
    assert "release-v2" in text


def test_event_has_timestamp():
    event = AuditEvent(
        key="FOO", status=DiffStatus.ADDED, old_value=None, new_value="bar"
    )
    assert event.timestamp  # non-empty ISO string
    assert "T" in event.timestamp  # rough ISO format check


def test_build_audit_default_label_is_none(result):
    """Verify that label defaults to None when not provided."""
    report = build_audit(result)
    assert report.label is None
    for event in report.events:
        assert event.label is None
