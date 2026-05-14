"""Tests for envdiff.watchdog and envdiff.cli_watchdog."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from envdiff.watchdog import WatchEvent, _file_hash, watch
from envdiff.differ import diff_envs
from envdiff.cli_watchdog import build_watchdog_parser, _run_watchdog


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p
    return _write


def _args(watched: Path, baseline: Path, **kwargs):
    parser = build_watchdog_parser()
    parts = [str(watched), str(baseline)]
    if kwargs.get("summary_only"):
        parts.append("--summary-only")
    if kwargs.get("max_events") is not None:
        parts += ["--max-events", str(kwargs["max_events"])]
    if kwargs.get("interval") is not None:
        parts += ["--interval", str(kwargs["interval"])]
    return parser.parse_args(parts)


# ---------------------------------------------------------------------------
# WatchEvent
# ---------------------------------------------------------------------------

def test_watch_event_has_changes_when_hashes_differ(tmp_path: Path):
    f = tmp_path / "a.env"
    f.write_text("A=1")
    diff = diff_envs({"A": "1"}, {"A": "2"})
    event = WatchEvent(path=f, previous_hash="aaa", current_hash="bbb", diff=diff)
    assert event.has_changes is True


def test_watch_event_no_changes_when_hashes_equal(tmp_path: Path):
    f = tmp_path / "a.env"
    f.write_text("A=1")
    diff = diff_envs({"A": "1"}, {"A": "1"})
    event = WatchEvent(path=f, previous_hash="abc", current_hash="abc", diff=diff)
    assert event.has_changes is False


def test_file_hash_is_stable(tmp_path: Path):
    f = tmp_path / "stable.env"
    f.write_text("KEY=value")
    assert _file_hash(f) == _file_hash(f)


def test_file_hash_changes_on_content_change(tmp_path: Path):
    f = tmp_path / "changing.env"
    f.write_text("KEY=old")
    h1 = _file_hash(f)
    f.write_text("KEY=new")
    h2 = _file_hash(f)
    assert h1 != h2


# ---------------------------------------------------------------------------
# watch() function
# ---------------------------------------------------------------------------

def test_watch_fires_callback_on_change(tmp_path: Path):
    watched = tmp_path / "watched.env"
    watched.write_text("A=1")
    baseline = {"A": "1"}
    events: list[WatchEvent] = []

    def mutate_after_first_sleep():
        watched.write_text("A=2")

    call_count = 0

    def fake_sleep(_: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            mutate_after_first_sleep()

    with patch("envdiff.watchdog.time.sleep", side_effect=fake_sleep):
        watch(watched, baseline, events.append, interval=0.01, max_events=1)

    assert len(events) == 1
    assert events[0].has_changes


def test_watch_does_not_fire_when_file_unchanged(tmp_path: Path):
    watched = tmp_path / "static.env"
    watched.write_text("A=1")
    baseline = {"A": "1"}
    events: list[WatchEvent] = []
    call_count = 0

    def fake_sleep(_: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 3:
            raise StopIteration  # force exit

    with pytest.raises(StopIteration):
        with patch("envdiff.watchdog.time.sleep", side_effect=fake_sleep):
            watch(watched, baseline, events.append, interval=0.01)

    assert events == []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_run_watchdog_missing_watched_returns_2(tmp_env):
    baseline = tmp_env("base.env", "A=1")
    args = _args(Path("/nonexistent/watched.env"), baseline, max_events=0)
    assert _run_watchdog(args) == 2


def test_run_watchdog_missing_baseline_returns_2(tmp_env):
    watched = tmp_env("watched.env", "A=1")
    args = _args(watched, Path("/nonexistent/base.env"), max_events=0)
    assert _run_watchdog(args) == 2


def test_run_watchdog_exits_zero_after_max_events(tmp_env):
    watched = tmp_env("watched.env", "A=1")
    baseline = tmp_env("base.env", "A=1")
    args = _args(watched, baseline, max_events=1, interval=0.01)

    call_count = 0

    def fake_sleep(_: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            watched.write_text("A=changed")

    with patch("envdiff.watchdog.time.sleep", side_effect=fake_sleep):
        result = _run_watchdog(args)

    assert result == 0
