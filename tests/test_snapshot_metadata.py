"""Additional edge-case tests for snapshot metadata and versioning."""
import json
import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.snapshot import load_snapshot, save_snapshot, snapshot_metadata


@pytest.fixture()
def minimal_result():
    return DiffResult(
        entries=[
            DiffEntry(key="K", status=DiffStatus.UNCHANGED, left="v", right="v"),
        ]
    )


def test_empty_result_roundtrip(tmp_path):
    empty = DiffResult(entries=[])
    path = str(tmp_path / "empty.json")
    save_snapshot(empty, path)
    loaded = load_snapshot(path)
    assert loaded.entries == []


def test_metadata_empty_label_default(tmp_path, minimal_result):
    path = str(tmp_path / "s.json")
    save_snapshot(minimal_result, path)  # no label arg
    meta = snapshot_metadata(path)
    assert meta["label"] == ""


def test_metadata_version_field(tmp_path, minimal_result):
    path = str(tmp_path / "s.json")
    save_snapshot(minimal_result, path)
    meta = snapshot_metadata(path)
    assert meta["version"] == 1


def test_none_values_preserved(tmp_path):
    result = DiffResult(
        entries=[
            DiffEntry(key="ADDED", status=DiffStatus.ADDED, left=None, right="new"),
            DiffEntry(key="REMOVED", status=DiffStatus.REMOVED, left="old", right=None),
        ]
    )
    path = str(tmp_path / "nulls.json")
    save_snapshot(result, path)
    loaded = load_snapshot(path)
    assert loaded.entries[0].left is None
    assert loaded.entries[1].right is None


def test_snapshot_file_is_human_readable(tmp_path, minimal_result):
    path = str(tmp_path / "s.json")
    save_snapshot(minimal_result, path)
    raw = open(path).read()
    # indent=2 means newlines present
    assert "\n" in raw
    assert "  " in raw


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_snapshot(str(tmp_path / "nonexistent.json"))
