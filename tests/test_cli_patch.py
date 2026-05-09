"""Integration tests for the 'patch' CLI sub-command."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envdiff.cli_patch import build_patch_parser, _run_patch


@pytest.fixture()
def tmp_env(tmp_path: Path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _args(staging: Path, production: Path, **kwargs) -> argparse.Namespace:
    defaults = dict(
        staging=staging,
        production=production,
        output=None,
        only=None,
        dry_run=False,
        func=_run_patch,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_patch_writes_to_stdout(tmp_env, capsys):
    s = _write(tmp_env / "staging.env", "APP_ENV=staging\nSHARED=same\n")
    p = _write(tmp_env / "prod.env", "APP_ENV=production\nSHARED=same\n")
    code = _run_patch(_args(s, p))
    assert code == 0
    out = capsys.readouterr().out
    assert "APP_ENV=production" in out


def test_patch_writes_to_file(tmp_env):
    s = _write(tmp_env / "staging.env", "APP_ENV=staging\nDB=old\n")
    p = _write(tmp_env / "prod.env", "APP_ENV=production\nDB=new\n")
    out_file = tmp_env / "patched.env"
    code = _run_patch(_args(s, p, output=out_file))
    assert code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "APP_ENV=production" in content
    assert "DB=new" in content


def test_removed_key_absent_in_output(tmp_env, capsys):
    s = _write(tmp_env / "staging.env", "OLD=yes\nKEEP=1\n")
    p = _write(tmp_env / "prod.env", "KEEP=1\n")
    _run_patch(_args(s, p))
    out = capsys.readouterr().out
    assert "OLD" not in out


def test_added_key_present_in_output(tmp_env, capsys):
    s = _write(tmp_env / "staging.env", "KEEP=1\n")
    p = _write(tmp_env / "prod.env", "KEEP=1\nNEW_KEY=hello\n")
    _run_patch(_args(s, p))
    out = capsys.readouterr().out
    assert "NEW_KEY=hello" in out


def test_dry_run_prints_summary(tmp_env, capsys):
    s = _write(tmp_env / "staging.env", "X=1\n")
    p = _write(tmp_env / "prod.env", "X=2\n")
    code = _run_patch(_args(s, p, dry_run=True))
    assert code == 0
    out = capsys.readouterr().out
    assert "Would apply" in out


def test_only_added_does_not_change_existing(tmp_env, capsys):
    s = _write(tmp_env / "staging.env", "APP=staging\n")
    p = _write(tmp_env / "prod.env", "APP=production\nNEW=yes\n")
    _run_patch(_args(s, p, only=["added"]))
    out = capsys.readouterr().out
    assert "APP=staging" in out
    assert "NEW=yes" in out
