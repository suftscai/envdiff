"""Tests for envdiff.annotator."""

from __future__ import annotations

import pytest

from envdiff.annotator import AnnotatedEntry, annotate, annotation_summary
from envdiff.differ import DiffEntry, DiffResult, DiffStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def result() -> DiffResult:
    entries = [
        DiffEntry("ADDED_KEY", DiffStatus.ADDED, None, "prod_val"),
        DiffEntry("REMOVED_KEY", DiffStatus.REMOVED, "stg_val", None),
        DiffEntry("CHANGED_KEY", DiffStatus.CHANGED, "old", "new"),
        DiffEntry("SAME_KEY", DiffStatus.UNCHANGED, "same", "same"),
    ]
    return DiffResult(entries)


# ---------------------------------------------------------------------------
# annotate()
# ---------------------------------------------------------------------------

def test_unchanged_excluded_by_default(result):
    annotated = annotate(result)
    keys = [ae.entry.key for ae in annotated]
    assert "SAME_KEY" not in keys


def test_include_unchanged_flag(result):
    annotated = annotate(result, include_unchanged=True)
    keys = [ae.entry.key for ae in annotated]
    assert "SAME_KEY" in keys


def test_annotate_returns_annotated_entry_instances(result):
    annotated = annotate(result)
    assert all(isinstance(ae, AnnotatedEntry) for ae in annotated)


def test_added_annotation_mentions_production(result):
    annotated = annotate(result)
    added = next(ae for ae in annotated if ae.entry.key == "ADDED_KEY")
    assert "production" in added.annotation.lower()


def test_removed_annotation_mentions_staging(result):
    annotated = annotate(result)
    removed = next(ae for ae in annotated if ae.entry.key == "REMOVED_KEY")
    assert "staging" in removed.annotation.lower()


def test_changed_annotation_contains_arrow(result):
    annotated = annotate(result)
    changed = next(ae for ae in annotated if ae.entry.key == "CHANGED_KEY")
    assert "->" in changed.annotation


def test_changed_annotation_contains_both_values(result):
    annotated = annotate(result)
    changed = next(ae for ae in annotated if ae.entry.key == "CHANGED_KEY")
    assert "old" in changed.annotation
    assert "new" in changed.annotation


def test_unchanged_annotation_says_identical(result):
    annotated = annotate(result, include_unchanged=True)
    same = next(ae for ae in annotated if ae.entry.key == "SAME_KEY")
    assert "identical" in same.annotation.lower()


# ---------------------------------------------------------------------------
# annotation_summary()
# ---------------------------------------------------------------------------

def test_summary_none_for_empty_list():
    assert annotation_summary([]) is None


def test_summary_contains_added_count(result):
    annotated = annotate(result)
    summary = annotation_summary(annotated)
    assert summary is not None
    assert "1 added" in summary


def test_summary_contains_removed_count(result):
    annotated = annotate(result)
    summary = annotation_summary(annotated)
    assert "1 removed" in summary


def test_summary_contains_changed_count(result):
    annotated = annotate(result)
    summary = annotation_summary(annotated)
    assert "1 changed" in summary


def test_summary_ends_with_period(result):
    annotated = annotate(result)
    summary = annotation_summary(annotated)
    assert summary.endswith(".")
