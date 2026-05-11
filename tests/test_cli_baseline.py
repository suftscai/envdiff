"""Integration tests for cli_baseline."""

from __future__ import annotations

import json
import pytest

from envdiff.cli_baseline import _run_baseline, build_baseline_parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path


def _write(path, content: str) -> str:
    p = path
    p.write_text(content)
    return str(p)


def _snapshot(tmp_path, label: str, differences: list) -> str:
    data = {"label": label, "differences": differences}
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(data))
    return str(p)


def _args(staging, production, snapshot, show_unchanged=False):
    parser = build_baseline_parser()
    return parser.parse_args(
        [staging, production, snapshot]
        + (["--show-unchanged"] if show_unchanged else [])
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_exit_zero_no_regressions(tmp_env):
    s = _write(tmp_env / "staging.env", "DB=localhost\n")
    p = _write(tmp_env / "prod.env", "DB=localhost\n")
    snap = _snapshot(tmp_env, "v1", [])
    args = _args(s, p, snap)
    assert _run_baseline(args) == 0


def test_exit_one_on_regression(tmp_env):
    s = _write(tmp_env / "staging.env", "DB=localhost\n")
    p = _write(tmp_env / "prod.env", "DB=db.prod\n")
    # Baseline says DB was unchanged — now it's changed → regression
    snap = _snapshot(
        tmp_env,
        "v1",
        [{"key": "DB", "status": "unchanged", "staging": "localhost", "production": "localhost"}],
    )
    args = _args(s, p, snap)
    assert _run_baseline(args) == 1


def test_output_contains_baseline_label(tmp_env, capsys):
    s = _write(tmp_env / "staging.env", "X=1\n")
    p = _write(tmp_env / "prod.env", "X=1\n")
    snap = _snapshot(tmp_env, "my-baseline", [])
    args = _args(s, p, snap)
    _run_baseline(args)
    out = capsys.readouterr().out
    assert "my-baseline" in out


def test_output_shows_regression_key(tmp_env, capsys):
    s = _write(tmp_env / "staging.env", "SECRET=old\n")
    p = _write(tmp_env / "prod.env", "SECRET=new\n")
    snap = _snapshot(
        tmp_env,
        "v1",
        [{"key": "SECRET", "status": "unchanged", "staging": "old", "production": "old"}],
    )
    args = _args(s, p, snap)
    _run_baseline(args)
    out = capsys.readouterr().out
    assert "SECRET" in out


def test_parser_returns_parser():
    parser = build_baseline_parser()
    assert parser is not None


def test_resolved_shows_in_output(tmp_env, capsys):
    # DB was CHANGED in baseline, now UNCHANGED → resolved
    s = _write(tmp_env / "staging.env", "DB=same\n")
    p = _write(tmp_env / "prod.env", "DB=same\n")
    snap = _snapshot(
        tmp_env,
        "v1",
        [{"key": "DB", "status": "changed", "staging": "a", "production": "b"}],
    )
    args = _args(s, p, snap)
    _run_baseline(args)
    out = capsys.readouterr().out
    assert "Resolved" in out or "resolved" in out
