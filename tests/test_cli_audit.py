"""Tests for envdiff.cli_audit."""
import json
from pathlib import Path

import pytest

from envdiff.cli_audit import build_audit_parser, _run_audit


@pytest.fixture()
def tmp_env(tmp_path: Path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _args(tmp_env, staging_content, production_content, **kwargs):
    staging = _write(tmp_env / "staging.env", staging_content)
    production = _write(tmp_env / "production.env", production_content)
    parser = build_audit_parser()
    argv = [str(staging), str(production)]
    for k, v in kwargs.items():
        argv += [f"--{k.replace('_', '-')}", str(v)]
    return parser.parse_args(argv)


def test_run_audit_returns_zero(tmp_env):
    args = _args(tmp_env, "FOO=bar\n", "FOO=baz\n")
    assert _run_audit(args) == 0


def test_text_output_contains_key(tmp_env, capsys):
    args = _args(tmp_env, "DB=old\n", "DB=new\n")
    _run_audit(args)
    captured = capsys.readouterr()
    assert "DB" in captured.out


def test_json_output_is_valid(tmp_env, capsys):
    args = _args(tmp_env, "X=1\n", "X=2\n", format="json")
    _run_audit(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "events" in data
    assert "total" in data


def test_json_excludes_unchanged(tmp_env, capsys):
    args = _args(tmp_env, "A=same\nB=old\n", "A=same\nB=new\n", format="json")
    _run_audit(args)
    data = json.loads(capsys.readouterr().out)
    keys = [e["key"] for e in data["events"]]
    assert "A" not in keys
    assert "B" in keys


def test_label_appears_in_json(tmp_env, capsys):
    args = _args(tmp_env, "K=1\n", "K=2\n", format="json", label="my-label")
    _run_audit(args)
    data = json.loads(capsys.readouterr().out)
    assert data["label"] == "my-label"
    for event in data["events"]:
        assert event["label"] == "my-label"


def test_output_to_file(tmp_env):
    out_file = tmp_env / "audit.txt"
    staging = _write(tmp_env / "s.env", "FOO=1\n")
    production = _write(tmp_env / "p.env", "FOO=2\n")
    parser = build_audit_parser()
    args = parser.parse_args([str(staging), str(production), "--output", str(out_file)])
    _run_audit(args)
    assert out_file.exists()
    assert "FOO" in out_file.read_text()


def test_no_changes_empty_events(tmp_env, capsys):
    args = _args(tmp_env, "A=1\n", "A=1\n", format="json")
    _run_audit(args)
    data = json.loads(capsys.readouterr().out)
    assert data["total"] == 0
    assert data["events"] == []
