"""Tests for envdiff.scorer."""
import pytest

from envdiff.differ import DiffResult, DiffEntry, DiffStatus
from envdiff.scorer import score_diff, DivergenceScore, _grade


def _entry(key: str, status: DiffStatus) -> DiffEntry:
    staging = "s" if status is not DiffStatus.ADDED else None
    production = "p" if status is not DiffStatus.REMOVED else None
    return DiffEntry(key=key, staging_value=staging, production_value=production, status=status)


@pytest.fixture()
def identical_result() -> DiffResult:
    entries = [_entry(k, DiffStatus.UNCHANGED) for k in ("A", "B", "C")]
    return DiffResult(entries=entries)


@pytest.fixture()
def mixed_result() -> DiffResult:
    entries = [
        _entry("ADDED_KEY", DiffStatus.ADDED),
        _entry("REMOVED_KEY", DiffStatus.REMOVED),
        _entry("CHANGED_KEY", DiffStatus.CHANGED),
        _entry("SAME_KEY", DiffStatus.UNCHANGED),
    ]
    return DiffResult(entries=entries)


# ---------------------------------------------------------------------------
# _grade
# ---------------------------------------------------------------------------

def test_grade_zero_is_A():
    assert _grade(0.0) == "A"


def test_grade_low_is_B():
    assert _grade(0.05) == "B"


def test_grade_medium_is_C():
    assert _grade(0.15) == "C"


def test_grade_high_is_D():
    assert _grade(0.30) == "D"


def test_grade_very_high_is_F():
    assert _grade(0.75) == "F"


# ---------------------------------------------------------------------------
# score_diff — identical envs
# ---------------------------------------------------------------------------

def test_identical_score_is_zero(identical_result):
    ds = score_diff(identical_result)
    assert ds.score == 0.0


def test_identical_grade_is_A(identical_result):
    assert score_diff(identical_result).grade == "A"


def test_identical_counts(identical_result):
    ds = score_diff(identical_result)
    assert ds.added == 0
    assert ds.removed == 0
    assert ds.changed == 0
    assert ds.unchanged == 3


# ---------------------------------------------------------------------------
# score_diff — mixed result
# ---------------------------------------------------------------------------

def test_mixed_total(mixed_result):
    assert score_diff(mixed_result).total == 4


def test_mixed_added_count(mixed_result):
    assert score_diff(mixed_result).added == 1


def test_mixed_removed_count(mixed_result):
    assert score_diff(mixed_result).removed == 1


def test_mixed_changed_count(mixed_result):
    assert score_diff(mixed_result).changed == 1


def test_mixed_score_uses_weight(mixed_result):
    # added=1, removed=1, changed=1, weight=0.5, total=4
    # raw = (1 + 1 + 0.5) / 4 = 0.625
    ds = score_diff(mixed_result, weight_changed=0.5)
    assert ds.score == pytest.approx(0.625, abs=1e-4)


def test_weight_zero_ignores_changed(mixed_result):
    # raw = (1 + 1 + 0) / 4 = 0.5
    ds = score_diff(mixed_result, weight_changed=0.0)
    assert ds.score == pytest.approx(0.5, abs=1e-4)


def test_weight_one_treats_changed_fully(mixed_result):
    # raw = (1 + 1 + 1) / 4 = 0.75
    ds = score_diff(mixed_result, weight_changed=1.0)
    assert ds.score == pytest.approx(0.75, abs=1e-4)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_result_score_is_zero():
    ds = score_diff(DiffResult(entries=[]))
    assert ds.score == 0.0
    assert ds.total == 0


def test_score_clamped_to_one():
    # All keys added — score should not exceed 1.0
    entries = [_entry(f"K{i}", DiffStatus.ADDED) for i in range(10)]
    ds = score_diff(DiffResult(entries=entries), weight_changed=1.0)
    assert ds.score <= 1.0


def test_invalid_weight_raises():
    with pytest.raises(ValueError, match="weight_changed"):
        score_diff(DiffResult(entries=[]), weight_changed=1.5)


def test_returns_divergence_score_instance(mixed_result):
    assert isinstance(score_diff(mixed_result), DivergenceScore)
