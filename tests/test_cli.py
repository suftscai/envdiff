"""Tests for the CLI entry point."""

import textwrap
from pathlib import Path

import pytest

from envdiff.cli import main


@pytest.fixture()
def tmp_env(tmp_path):
    """Return a helper that writes an env file and returns its path."""

    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(textwrap.dedent(content))
        return p

    return _write


def test_identical_files_exit_zero(tmp_env):
    a = tmp_env("a.env", "KEY=value\n")
    b = tmp_env("b.env", "KEY=value\n")
    assert main([str(a), str(b)]) == 0


def test_different_files_exit_zero_without_flag(tmp_env):
    a = tmp_env("a.env", "KEY=foo\n")
    b = tmp_env("b.env", "KEY=bar\n")
    assert main([str(a), str(b)]) == 0


def test_different_files_exit_one_with_flag(tmp_env):
    a = tmp_env("a.env", "KEY=foo\n")
    b = tmp_env("b.env", "KEY=bar\n")
    assert main([str(a), str(b), "--exit-code"]) == 1


def test_identical_files_exit_zero_with_flag(tmp_env):
    """--exit-code should still return 0 when files are identical."""
    a = tmp_env("a.env", "KEY=value\n")
    b = tmp_env("b.env", "KEY=value\n")
    assert main([str(a), str(b), "--exit-code"]) == 0


def test_missing_file_returns_2(tmp_env, capsys):
    a = tmp_env("a.env", "KEY=value\n")
    rc = main([str(a), "/nonexistent/path.env"])
    assert rc == 2
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_summary_flag(tmp_env, capsys):
    a = tmp_env("a.env", "A=1\nB=2\n")
    b = tmp_env("b.env", "A=1\nC=3\n")
    main([str(a), str(b), "--summary"])
    captured = capsys.readouterr()
    # summary line should mention counts, not individual keys
    assert "added" in captured.out.lower() or "removed" in captured.out.lower()


def test_no_color_flag_does_not_crash(tmp_env):
    a = tmp_env("a.env", "X=1\n")
    b = tmp_env("b.env", "X=2\n")
    assert main([str(a), str(b), "--no-color"]) == 0


def test_custom_labels_appear_in_output(tmp_env, capsys):
    a = tmp_env("staging.env", "ONLY_A=yes\n")
    b = tmp_env("prod.env", "")
    main([str(a), str(b), "--label-a", "staging", "--label-b", "production", "--summary"])
    captured = capsys.readouterr()
    assert "staging" in captured.out or "production" in captured.out


def test_added_and_removed_shown(tmp_env, capsys):
    a = tmp_env("a.env", "OLD=1\n")
    b = tmp_env("b.env", "NEW=2\n")
    main([str(a), str(b), "--no-color"])
    captured = capsys.readouterr()
    assert "OLD" in captured.out
    assert "NEW" in captured.out
