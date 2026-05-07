"""Tests for envdiff.snapshot."""
import json
import os
import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.snapshot import load_snapshot, save_snapshot, snapshot_metadata


@pytest.fixture()
def result() -> DiffResult:
    return DiffResult(
        entries=[
            DiffEntry(key="APP_ENV", status=DiffStatus.CHANGED, left="staging", right="production"),
            DiffEntry(key="DEBUG", status=DiffStatus.REMOVED, left="true", right=None),
            DiffEntry(key="NEW_KEY", status=DiffStatus.ADDED, left=None, right="value"),
            DiffEntry(key="PORT", status=DiffStatus.UNCHANGED, left="8080", right="8080"),
        ]
    )


def test_save_creates_file(tmp_path, result):
    path = str(tmp_path / "snap.json")
    save_snapshot(result, path, label="test-snap")
    assert os.path.isfile(path)


def test_save_valid_json(tmp_path, result):
    path = str(tmp_path / "snap.json")
    save_snapshot(result, path)
    with open(path) as fh:
        data = json.load(fh)
    assert data["version"] == 1
    assert "entries" in data
    assert len(data["entries"]) == 4


def test_roundtrip_preserves_entries(tmp_path, result):
    path = str(tmp_path / "snap.json")
    save_snapshot(result, path)
    loaded = load_snapshot(path)
    assert len(loaded.entries) == len(result.entries)
    for orig, restored in zip(result.entries, loaded.entries):
        assert restored.key == orig.key
        assert restored.status == orig.status
        assert restored.left == orig.left
        assert restored.right == orig.right


def test_label_is_stored(tmp_path, result):
    path = str(tmp_path / "snap.json")
    save_snapshot(result, path, label="my-label")
    meta = snapshot_metadata(path)
    assert meta["label"] == "my-label"


def test_metadata_entry_count(tmp_path, result):
    path = str(tmp_path / "snap.json")
    save_snapshot(result, path)
    meta = snapshot_metadata(path)
    assert meta["entry_count"] == 4


def test_load_wrong_version_raises(tmp_path):
    path = str(tmp_path / "bad.json")
    with open(path, "w") as fh:
        json.dump({"version": 99, "entries": []}, fh)
    with pytest.raises(ValueError, match="Unsupported snapshot version"):
        load_snapshot(path)


def test_created_at_present(tmp_path, result):
    path = str(tmp_path / "snap.json")
    save_snapshot(result, path)
    meta = snapshot_metadata(path)
    assert meta["created_at"] is not None
    assert "T" in meta["created_at"]  # ISO format


def test_save_creates_parent_dirs(tmp_path, result):
    path = str(tmp_path / "nested" / "dir" / "snap.json")
    save_snapshot(result, path)
    assert os.path.isfile(path)
