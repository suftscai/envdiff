"""Integration tests for the 'filter' CLI sub-command."""

from __future__ import annotations

import pathlib
import textwrap

import pytest

from envdiff.cli_filter import _run_filter


@pytest.fixture()
def tmp_env(tmp_path: pathlib.Path):
    def _write(name: str, content: str) -> pathlib.Path:
        p = tmp_path / name
        p.write_text(textwrap.dedent(content))
        return p

    return _write


def _args(**kwargs):
    """Build a minimal namespace mimicking argparse output."""
    import argparse

    defaults = dict(
        staging=None,
        production=None,
        prefix=None,
        pattern=None,
        regex=None,
        status=None,
        no_unchanged=False,
        color=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_filter_no_unchanged(tmp_env, capsys):
    s = tmp_env("s.env", "A=1\nB=2\n")
    p = tmp_env("p.env", "A=1\nB=99\n")
    rc = _run_filter(_args(staging=str(s), production=str(p), no_unchanged=True))
    out = capsys.readouterr().out
    assert rc == 0
    assert "B" in out
    assert "A" not in out


def test_filter_by_prefix(tmp_env, capsys):
    s = tmp_env("s.env", "APP_HOST=localhost\nDB_URL=postgres\n")
    p = tmp_env("p.env", "APP_HOST=prod\nDB_URL=postgres\n")
    rc = _run_filter(_args(staging=str(s), production=str(p), prefix="APP_", no_unchanged=False))
    out = capsys.readouterr().out
    assert rc == 0
    assert "APP_HOST" in out
    assert "DB_URL" not in out


def test_filter_by_pattern(tmp_env, capsys):
    s = tmp_env("s.env", "AWS_KEY=k1\nAWS_SECRET=s1\nOTHER=x\n")
    p = tmp_env("p.env", "AWS_KEY=k2\nAWS_SECRET=s1\nOTHER=x\n")
    rc = _run_filter(_args(staging=str(s), production=str(p), pattern="AWS_*"))
    out = capsys.readouterr().out
    assert rc == 0
    assert "AWS_KEY" in out
    assert "OTHER" not in out


def test_filter_by_status_added(tmp_env, capsys):
    s = tmp_env("s.env", "A=1\n")
    p = tmp_env("p.env", "A=1\nB=2\n")
    rc = _run_filter(_args(staging=str(s), production=str(p), status=["added"]))
    out = capsys.readouterr().out
    assert rc == 0
    assert "B" in out
    assert "A" not in out


def test_filter_invalid_regex_returns_2(tmp_env, capsys):
    s = tmp_env("s.env", "A=1\n")
    p = tmp_env("p.env", "A=1\n")
    rc = _run_filter(_args(staging=str(s), production=str(p), regex="[invalid"))
    assert rc == 2
    err = capsys.readouterr().err
    assert "Invalid regex" in err


def test_filter_by_regex(tmp_env, capsys):
    s = tmp_env("s.env", "FEATURE_X=on\nFEATURE_Y=off\nDB=pg\n")
    p = tmp_env("p.env", "FEATURE_X=on\nFEATURE_Y=on\nDB=pg\n")
    rc = _run_filter(_args(staging=str(s), production=str(p), regex=r"^FEATURE_"))
    out = capsys.readouterr().out
    assert rc == 0
    assert "FEATURE_Y" in out
    assert "DB" not in out
