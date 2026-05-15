"""Tests for envdiff.cli_scheduler."""
from __future__ import annotations

import os
from typing import Generator

import pytest

from envdiff.cli_scheduler import _on_event, _run_scheduler, build_scheduler_parser
from envdiff.scheduler import ScheduleEvent, run_schedule


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)

    return _write


def _noop_sleep(_: float) -> None:
    pass


def _args(staging, production, *, runs=1, interval=0.0, changes_only=False):
    parser = build_scheduler_parser()
    argv = [staging, production, "--runs", str(runs), "--interval", str(interval)]
    if changes_only:
        argv.append("--changes-only")
    return parser.parse_args(argv)


def test_build_parser_returns_parser():
    parser = build_scheduler_parser()
    assert parser is not None


def test_run_scheduler_exit_zero(tmp_env, monkeypatch):
    import envdiff.scheduler as sched_mod

    monkeypatch.setattr(sched_mod, "time", __import__("time"))
    staging = tmp_env("s.env", "FOO=1\n")
    production = tmp_env("p.env", "FOO=1\n")
    args = _args(staging, production, runs=1)
    assert _run_scheduler(args) == 0


def test_on_event_prints_when_changes(tmp_env, capsys):
    staging = tmp_env("s.env", "A=1\n")
    production = tmp_env("p.env", "A=2\n")
    events = run_schedule(
        staging, production, max_runs=1, interval=0, sleep_fn=_noop_sleep
    )
    _on_event(events[0], changes_only=False)
    captured = capsys.readouterr()
    assert "CHANGED" in captured.out


def test_on_event_suppressed_when_changes_only_and_identical(tmp_env, capsys):
    staging = tmp_env("s.env", "A=1\n")
    production = tmp_env("p.env", "A=1\n")
    events = run_schedule(
        staging, production, max_runs=1, interval=0, sleep_fn=_noop_sleep
    )
    _on_event(events[0], changes_only=True)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_on_event_shows_run_number(tmp_env, capsys):
    staging = tmp_env("s.env", "A=1\n")
    production = tmp_env("p.env", "A=1\n")
    events = run_schedule(
        staging, production, max_runs=1, interval=0, sleep_fn=_noop_sleep
    )
    _on_event(events[0], changes_only=False)
    captured = capsys.readouterr()
    assert "run 1" in captured.out


def test_interval_default_is_60():
    parser = build_scheduler_parser()
    args = parser.parse_args(["s.env", "p.env", "--runs", "1"])
    assert args.interval == 60.0


def test_changes_only_default_false():
    parser = build_scheduler_parser()
    args = parser.parse_args(["s.env", "p.env", "--runs", "1"])
    assert args.changes_only is False
