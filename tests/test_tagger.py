"""Tests for envdiff.tagger."""

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.tagger import TagReport, TaggedEntry, tag_diff


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def result() -> DiffResult:
    entries = [
        DiffEntry("DB_HOST", DiffStatus.CHANGED, "localhost", "db.prod"),
        DiffEntry("DB_PASSWORD", DiffStatus.CHANGED, "pass", "s3cr3t"),
        DiffEntry("AWS_ACCESS_KEY", DiffStatus.ADDED, None, "AKID"),
        DiffEntry("LOG_LEVEL", DiffStatus.UNCHANGED, "INFO", "INFO"),
        DiffEntry("STRIPE_SECRET_KEY", DiffStatus.REMOVED, "sk_test", None),
    ]
    return DiffResult(entries=entries)


RULES = {
    "DB_*": ["database"],
    "*SECRET*": ["sensitive"],
    "AWS_*": ["cloud", "aws"],
}


# ---------------------------------------------------------------------------
# TagReport basics
# ---------------------------------------------------------------------------


def test_tag_diff_returns_tag_report(result):
    report = tag_diff(result, RULES)
    assert isinstance(report, TagReport)


def test_unchanged_excluded_by_default(result):
    report = tag_diff(result, RULES)
    keys = [te.key for te in report.tagged]
    assert "LOG_LEVEL" not in keys


def test_include_unchanged_flag(result):
    report = tag_diff(result, RULES, include_unchanged=True)
    keys = [te.key for te in report.tagged]
    assert "LOG_LEVEL" in keys


def test_len_matches_tagged_count(result):
    report = tag_diff(result, RULES)
    assert len(report) == len(report.tagged)


# ---------------------------------------------------------------------------
# Tag application
# ---------------------------------------------------------------------------


def test_db_host_gets_database_tag(result):
    report = tag_diff(result, RULES)
    entry = next(te for te in report.tagged if te.key == "DB_HOST")
    assert "database" in entry.tags


def test_aws_key_gets_cloud_and_aws_tags(result):
    report = tag_diff(result, RULES)
    entry = next(te for te in report.tagged if te.key == "AWS_ACCESS_KEY")
    assert "cloud" in entry.tags
    assert "aws" in entry.tags


def test_stripe_secret_key_gets_sensitive_tag(result):
    report = tag_diff(result, RULES)
    entry = next(te for te in report.tagged if te.key == "STRIPE_SECRET_KEY")
    assert "sensitive" in entry.tags


def test_entry_with_no_matching_rule_has_empty_tags(result):
    rules = {}  # no rules
    report = tag_diff(result, rules)
    for te in report.tagged:
        assert te.tags == []


# ---------------------------------------------------------------------------
# TagReport helpers
# ---------------------------------------------------------------------------


def test_by_tag_returns_correct_entries(result):
    report = tag_diff(result, RULES)
    db_entries = report.by_tag("database")
    assert all("database" in te.tags for te in db_entries)
    assert any(te.key == "DB_HOST" for te in db_entries)


def test_all_tags_is_sorted(result):
    report = tag_diff(result, RULES)
    tags = report.all_tags()
    assert tags == sorted(tags)


def test_all_tags_contains_expected_tags(result):
    report = tag_diff(result, RULES)
    tags = set(report.all_tags())
    assert {"database", "sensitive", "cloud", "aws"}.issubset(tags)


def test_tagged_entry_key_property(result):
    report = tag_diff(result, RULES)
    for te in report.tagged:
        assert te.key == te.entry.key
