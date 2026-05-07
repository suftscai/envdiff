"""Tests for envdiff.cli_snapshot."""
import json
import os
import pytest

from envdiff.cli_snapshot import _run_snapshot


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


def _args(**kwargs):
    """Build a simple namespace for testing."""
    import argparse
    ns = argparse.Namespace(**kwargs)
    return ns


def test_save_creates_snapshot(tmp_env, tmp_path):
    left = tmp_env("left.env", "APP=staging\nDEBUG=true\n")
    right = tmp_env("right.env", "APP=production\nNEW=1\n")
    out = str(tmp_path / "snap.json")
    args = _args(snapshot_cmd="save", left=left, right=right, output=out, label="ci")
    rc = _run_snapshot(args)
    assert rc == 0
    assert os.path.isfile(out)


def test_save_snapshot_has_label(tmp_env, tmp_path):
    left = tmp_env("l.env", "X=1\n")
    right = tmp_env("r.env", "X=2\n")
    out = str(tmp_path / "snap.json")
    _run_snapshot(_args(snapshot_cmd="save", left=left, right=right, output=out, label="my-label"))
    with open(out) as fh:
        data = json.load(fh)
    assert data["label"] == "my-label"


def test_compare_returns_zero(tmp_env, tmp_path):
    left = tmp_env("l.env", "X=1\n")
    right = tmp_env("r.env", "X=2\n")
    snap = str(tmp_path / "snap.json")
    _run_snapshot(_args(snapshot_cmd="save", left=left, right=right, output=snap, label=""))
    rc = _run_snapshot(_args(snapshot_cmd="compare", snapshot=snap, left=left, right=right, color=False))
    assert rc == 0


def test_info_returns_zero(tmp_env, tmp_path):
    left = tmp_env("l.env", "A=1\n")
    right = tmp_env("r.env", "A=2\n")
    snap = str(tmp_path / "snap.json")
    _run_snapshot(_args(snapshot_cmd="save", left=left, right=right, output=snap, label="info-test"))
    rc = _run_snapshot(_args(snapshot_cmd="info", snapshot=snap))
    assert rc == 0


def test_unknown_cmd_returns_one(tmp_path):
    args = _args(snapshot_cmd="nonexistent")
    rc = _run_snapshot(args)
    assert rc == 1


def test_save_records_all_statuses(tmp_env, tmp_path):
    left = tmp_env("l.env", "SAME=x\nOLD=y\nCHG=a\n")
    right = tmp_env("r.env", "SAME=x\nNEW=z\nCHG=b\n")
    snap = str(tmp_path / "snap.json")
    _run_snapshot(_args(snapshot_cmd="save", left=left, right=right, output=snap, label=""))
    with open(snap) as fh:
        data = json.load(fh)
    statuses = {e["key"]: e["status"] for e in data["entries"]}
    assert statuses["SAME"] == "unchanged"
    assert statuses["OLD"] == "removed"
    assert statuses["NEW"] == "added"
    assert statuses["CHG"] == "changed"
