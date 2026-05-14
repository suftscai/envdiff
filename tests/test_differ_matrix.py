"""Tests for envdiff.differ_matrix."""

import pytest

from envdiff.differ_matrix import build_matrix, format_matrix_text, DiffMatrix, MatrixCell


@pytest.fixture()
def three_envs():
    return {
        "dev": {"A": "1", "B": "2", "C": "3"},
        "staging": {"A": "1", "B": "99", "D": "4"},
        "prod": {"A": "1", "B": "2", "C": "3", "E": "5"},
    }


@pytest.fixture()
def matrix(three_envs):
    return build_matrix(three_envs)


def test_returns_diff_matrix(matrix):
    assert isinstance(matrix, DiffMatrix)


def test_labels_preserved(matrix, three_envs):
    assert matrix.labels == list(three_envs.keys())


def test_cell_count_is_n_squared_minus_n(matrix, three_envs):
    n = len(three_envs)
    assert len(matrix) == n * (n - 1)


def test_no_self_pairs(matrix):
    for left, right in matrix.cells:
        assert left != right


def test_get_returns_matrix_cell(matrix):
    cell = matrix.get("dev", "staging")
    assert isinstance(cell, MatrixCell)


def test_get_missing_pair_returns_none(matrix):
    assert matrix.get("dev", "dev") is None


def test_identical_pair_is_identical():
    envs = {"a": {"X": "1"}, "b": {"X": "1"}}
    m = build_matrix(envs)
    assert m.get("a", "b").is_identical


def test_added_count():
    envs = {"left": {"A": "1"}, "right": {"A": "1", "B": "2", "C": "3"}}
    m = build_matrix(envs)
    # from left's perspective, B and C are added in right
    cell = m.get("left", "right")
    assert cell.added == 2


def test_removed_count():
    envs = {"left": {"A": "1", "B": "2"}, "right": {"A": "1"}}
    m = build_matrix(envs)
    cell = m.get("left", "right")
    assert cell.removed == 1


def test_changed_count():
    envs = {"left": {"A": "old"}, "right": {"A": "new"}}
    m = build_matrix(envs)
    cell = m.get("left", "right")
    assert cell.changed == 1


def test_unchanged_count():
    envs = {"left": {"A": "1", "B": "2"}, "right": {"A": "1", "B": "99"}}
    m = build_matrix(envs)
    cell = m.get("left", "right")
    assert cell.unchanged == 1


def test_total_differences():
    envs = {"left": {"A": "1", "B": "old"}, "right": {"A": "1", "B": "new", "C": "3"}}
    m = build_matrix(envs)
    cell = m.get("left", "right")
    assert cell.total_differences == cell.added + cell.removed + cell.changed


def test_format_matrix_text_contains_labels(matrix):
    text = format_matrix_text(matrix)
    for label in ["dev", "staging", "prod"]:
        assert label in text


def test_format_matrix_text_contains_diff_symbols(matrix):
    text = format_matrix_text(matrix)
    assert "+" in text
    assert "-" in text
    assert "~" in text


def test_format_matrix_text_empty():
    m = DiffMatrix(labels=[])
    assert "no environments" in format_matrix_text(m)


def test_format_matrix_text_single_env():
    envs = {"only": {"A": "1"}}
    m = build_matrix(envs)
    text = format_matrix_text(m)
    assert "only" in text
    assert "—" in text
