"""Tests for envdiff.formatter."""

from envdiff.differ import diff_envs
from envdiff.formatter import format_summary, format_text


def _make_result():
    """Return a diff result with added, removed, and changed keys."""
    left = {"HOST": "staging", "DEBUG": "true", "OLD_KEY": "gone"}
    right = {"HOST": "prod", "DEBUG": "true", "NEW_KEY": "here"}
    return diff_envs(left, right)


def test_format_text_contains_added(tmp_path):
    result = _make_result()
    text = format_text(result)
    assert "+ NEW_KEY=here" in text


def test_format_text_contains_removed():
    result = _make_result()
    text = format_text(result)
    assert "- OLD_KEY=gone" in text


def test_format_text_contains_changed():
    result = _make_result()
    text = format_text(result)
    assert "~ HOST" in text
    assert "staging" in text
    assert "prod" in text


def test_format_text_no_differences():
    result = diff_envs({"A": "1"}, {"A": "1"})
    assert format_text(result) == "No differences found."


def test_format_summary_with_diffs():
    result = _make_result()
    summary = format_summary(result)
    assert "added" in summary
    assert "removed" in summary
    assert "changed" in summary


def test_format_summary_identical():
    result = diff_envs({"X": "1"}, {"X": "1"})
    assert format_summary(result) == "Environments are identical."


def test_format_text_color_contains_ansi():
    result = _make_result()
    text = format_text(result, color=True)
    assert "\033[" in text


def test_format_text_plain_no_ansi():
    result = _make_result()
    text = format_text(result, color=False)
    assert "\033[" not in text


def test_format_summary_only_added():
    result = diff_envs({}, {"NEW": "val"})
    summary = format_summary(result)
    assert "1 added" in summary
    assert "removed" not in summary


def test_format_summary_only_removed():
    """Verify summary correctly reports only removed keys with no added/changed."""
    result = diff_envs({"OLD": "val"}, {})
    summary = format_summary(result)
    assert "1 removed" in summary
    assert "added" not in summary
    assert "changed" not in summary
