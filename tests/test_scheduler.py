"""Tests for envdiff.scheduler."""
from __future__ import annotations

import os
import tempfile
from typing import Generator

import pytest

from envdiff.differ import DiffStatus
from envdiff.scheduler import ScheduleEvent, _result_has_changes, run_schedule


@pytest.fixture()
def tmp_env(tmp_path: "os.PathLike[str]") -> Generator[object, None, None]:
    def _write(name: str, content: str) -> str:
        p = tmp_path / name  # type: ignore[operator]
        p.write_text(content)
        return str(p)

    yield _write


def _noop_sleep(_: float) -> None:
    pass


def test_run_schedule_returns_events(tmp_env):
    staging = tmp_env("staging.env", "FOO=bar\nBAZ=qux\n")
    production = tmp_env("production.env", "FOO=bar\nBAZ=qux\n")

    events = run_schedule(
        staging, production, max_runs=2, interval=0, sleep_fn=_noop_sleep
    )
    assert len(events) == 2


def test_run_schedule_event_type(tmp_env):
    staging = tmp_env("staging.env", "FOO=bar\n")
    production = tmp_env("production.env", "FOO=bar\n")

    events = run_schedule(
        staging, production, max_runs=1, interval=0, sleep_fn=_noop_sleep
    )
    assert isinstance(events[0], ScheduleEvent)


def test_identical_files_no_changes(tmp_env):
    staging = tmp_env("staging.env", "FOO=bar\n")
    production = tmp_env("production.env", "FOO=bar\n")

    events = run_schedule(
        staging, production, max_runs=1, interval=0, sleep_fn=_noop_sleep
    )
    assert events[0].has_changes is False


def test_different_files_have_changes(tmp_env):
    staging = tmp_env("staging.env", "FOO=bar\n")
    production = tmp_env("production.env", "FOO=different\n")

    events = run_schedule(
        staging, production, max_runs=1, interval=0, sleep_fn=_noop_sleep
    )
    assert events[0].has_changes is True


def test_run_numbers_are_sequential(tmp_env):
    staging = tmp_env("staging.env", "A=1\n")
    production = tmp_env("production.env", "A=1\n")

    events = run_schedule(
        staging, production, max_runs=3, interval=0, sleep_fn=_noop_sleep
    )
    assert [e.run_number for e in events] == [1, 2, 3]


def test_on_event_callback_invoked(tmp_env):
    staging = tmp_env("staging.env", "A=1\n")
    production = tmp_env("production.env", "A=2\n")
    received: list[ScheduleEvent] = []

    run_schedule(
        staging,
        production,
        max_runs=2,
        interval=0,
        on_event=received.append,
        sleep_fn=_noop_sleep,
    )
    assert len(received) == 2


def test_elapsed_seconds_is_non_negative(tmp_env):
    staging = tmp_env("staging.env", "X=1\n")
    production = tmp_env("production.env", "X=1\n")

    events = run_schedule(
        staging, production, max_runs=1, interval=0, sleep_fn=_noop_sleep
    )
    assert events[0].elapsed_seconds >= 0.0


def test_result_has_changes_false_when_all_unchanged(tmp_env):
    staging = tmp_env("s.env", "A=1\n")
    production = tmp_env("p.env", "A=1\n")

    events = run_schedule(
        staging, production, max_runs=1, interval=0, sleep_fn=_noop_sleep
    )
    assert _result_has_changes(events[0].result) is False
