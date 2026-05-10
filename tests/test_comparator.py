"""Tests for envdiff.comparator."""
from __future__ import annotations

import pytest

from envdiff.comparator import SimilarityReport, compare_envs, format_comparison_text


@pytest.fixture()
def staging() -> dict:
    return {
        "APP_ENV": "staging",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "SECRET_KEY": "abc123",
    }


@pytest.fixture()
def production() -> dict:
    return {
        "APP_ENV": "production",
        "DB_HOST": "db.prod.example.com",
        "DB_PORT": "5432",
        "NEW_RELIC_KEY": "xyz789",
    }


def test_returns_similarity_report(staging, production):
    report = compare_envs(staging, production)
    assert isinstance(report, SimilarityReport)


def test_total_keys_is_union(staging, production):
    report = compare_envs(staging, production)
    # union: APP_ENV, DB_HOST, DB_PORT, SECRET_KEY, NEW_RELIC_KEY = 5
    assert report.total_keys == 5


def test_shared_keys_is_intersection(staging, production):
    report = compare_envs(staging, production)
    # shared: APP_ENV, DB_HOST, DB_PORT = 3
    assert report.shared_keys == 3


def test_identical_keys(staging, production):
    report = compare_envs(staging, production)
    # only DB_PORT has the same value in both
    assert report.identical_keys == 1


def test_added_keys(staging, production):
    report = compare_envs(staging, production)
    # NEW_RELIC_KEY only in production
    assert report.added_keys == 1


def test_removed_keys(staging, production):
    report = compare_envs(staging, production)
    # SECRET_KEY only in staging
    assert report.removed_keys == 1


def test_changed_keys(staging, production):
    report = compare_envs(staging, production)
    # APP_ENV and DB_HOST differ
    assert report.changed_keys == 2


def test_similarity_pct_range(staging, production):
    report = compare_envs(staging, production)
    assert 0.0 <= report.similarity_pct <= 100.0


def test_jaccard_index_range(staging, production):
    report = compare_envs(staging, production)
    assert 0.0 <= report.jaccard_index <= 1.0


def test_identical_envs_full_similarity():
    env = {"KEY": "value", "OTHER": "data"}
    report = compare_envs(env, env.copy())
    assert report.similarity_pct == 100.0
    assert report.jaccard_index == 1.0
    assert report.changed_keys == 0
    assert report.added_keys == 0
    assert report.removed_keys == 0


def test_completely_disjoint_envs():
    left = {"A": "1"}
    right = {"B": "2"}
    report = compare_envs(left, right)
    assert report.identical_keys == 0
    assert report.jaccard_index == 0.0
    assert report.similarity_pct == 0.0


def test_empty_envs():
    report = compare_envs({}, {})
    assert report.total_keys == 0
    assert report.similarity_pct == 100.0
    assert report.jaccard_index == 1.0


def test_format_comparison_text_contains_keys(staging, production):
    report = compare_envs(staging, production)
    text = format_comparison_text(report)
    assert "Total keys" in text
    assert "Similarity" in text
    assert "Jaccard" in text


def test_format_comparison_text_shows_values(staging, production):
    report = compare_envs(staging, production)
    text = format_comparison_text(report)
    assert str(report.total_keys) in text
    assert f"{report.similarity_pct:.1f}%" in text
