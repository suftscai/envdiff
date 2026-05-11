"""Tests for envdiff.baseline."""

from __future__ import annotations

import json
import pytest

from envdiff.baseline import BaselineDelta, BaselineReport, compare_to_baseline
from envdiff.differ import DiffEntry, DiffResult, DiffStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def snapshot_file(tmp_path):
    """Write a minimal snapshot JSON and return its path."""

    def _write(label: str, differences: list) -> str:
        data = {"label": label, "differences": differences}
        p = tmp_path / "baseline.json"
        p.write_text(json.dumps(data))
        return str(p)

    return _write


@pytest.fixture()
def current_result():
    return DiffResult(
        entries=[
            DiffEntry(key="DB_HOST", status=DiffStatus.CHANGED, staging="localhost", production="db.prod"),
            DiffEntry(key="DEBUG", status=DiffStatus.UNCHANGED, staging="true", production="true"),
            DiffEntry(key="NEW_KEY", status=DiffStatus.ADDED, staging=None, production="value"),
        ]
    )


# ---------------------------------------------------------------------------
# BaselineDelta properties
# ---------------------------------------------------------------------------


def test_is_new_when_baseline_status_none():
    d = BaselineDelta(
        key="X", baseline_status=None, current_status=DiffStatus.ADDED,
        baseline_staging=None, baseline_production=None,
        current_staging=None, current_production="v",
    )
    assert d.is_new is True


def test_is_resolved_when_was_changed_now_unchanged():
    d = BaselineDelta(
        key="X", baseline_status=DiffStatus.CHANGED, current_status=DiffStatus.UNCHANGED,
        baseline_staging="a", baseline_production="b",
        current_staging="a", current_production="a",
    )
    assert d.is_resolved is True


def test_is_regressed_when_was_unchanged_now_changed():
    d = BaselineDelta(
        key="X", baseline_status=DiffStatus.UNCHANGED, current_status=DiffStatus.CHANGED,
        baseline_staging="a", baseline_production="a",
        current_staging="a", current_production="b",
    )
    assert d.is_regressed is True


# ---------------------------------------------------------------------------
# compare_to_baseline
# ---------------------------------------------------------------------------


def test_returns_baseline_report(snapshot_file, current_result):
    path = snapshot_file("v1", [])
    report = compare_to_baseline(current_result, path)
    assert isinstance(report, BaselineReport)


def test_label_from_snapshot(snapshot_file, current_result):
    path = snapshot_file("release-42", [])
    report = compare_to_baseline(current_result, path)
    assert report.baseline_label == "release-42"


def test_new_issues_detected(snapshot_file, current_result):
    """Keys in current but absent from baseline are new issues."""
    path = snapshot_file("v1", [])
    report = compare_to_baseline(current_result, path)
    new_keys = {d.key for d in report.new_issues}
    assert "DB_HOST" in new_keys
    assert "NEW_KEY" in new_keys


def test_resolved_detected(snapshot_file, current_result):
    """Key that was CHANGED in baseline but UNCHANGED now is resolved."""
    baseline_diffs = [
        {"key": "DEBUG", "status": "changed", "staging": "false", "production": "true"},
    ]
    path = snapshot_file("v1", baseline_diffs)
    report = compare_to_baseline(current_result, path)
    resolved_keys = {d.key for d in report.resolved_issues}
    assert "DEBUG" in resolved_keys


def test_regression_detected(snapshot_file):
    """Key that was UNCHANGED in baseline but is now CHANGED is a regression."""
    baseline_diffs = [
        {"key": "DB_HOST", "status": "unchanged", "staging": "localhost", "production": "localhost"},
    ]
    path = snapshot_file("v1", baseline_diffs)
    result = DiffResult(
        entries=[
            DiffEntry(key="DB_HOST", status=DiffStatus.CHANGED, staging="localhost", production="db.prod"),
        ]
    )
    report = compare_to_baseline(result, path)
    assert len(report.regressions) == 1
    assert report.regressions[0].key == "DB_HOST"


def test_no_regressions_clean_diff(snapshot_file):
    baseline_diffs = [
        {"key": "DB_HOST", "status": "changed", "staging": "localhost", "production": "db.prod"},
    ]
    path = snapshot_file("v1", baseline_diffs)
    result = DiffResult(
        entries=[
            DiffEntry(key="DB_HOST", status=DiffStatus.CHANGED, staging="localhost", production="db.prod"),
        ]
    )
    report = compare_to_baseline(result, path)
    assert report.regressions == []
