"""Tests for envdiff.exporter."""

from __future__ import annotations

import csv
import io
import json

import pytest

from envdiff.differ import diff
from envdiff.exporter import export_csv, export_json, export_markdown


@pytest.fixture()
def staging() -> dict[str, str]:
    return {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "secret123",
        "LOG_LEVEL": "debug",
        "ONLY_STAGING": "yes",
    }


@pytest.fixture()
def production() -> dict[str, str]:
    return {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "prod_secret",
        "LOG_LEVEL": "info",
        "ONLY_PROD": "yes",
    }


@pytest.fixture()
def result(staging, production):
    return diff(staging, production)


# --- JSON ---

def test_export_json_is_valid_json(result):
    output = export_json(result)
    parsed = json.loads(output)
    assert "summary" in parsed
    assert "differences" in parsed


def test_export_json_excludes_unchanged(result):
    parsed = json.loads(export_json(result))
    statuses = {d["status"] for d in parsed["differences"]}
    assert "unchanged" not in statuses


def test_export_json_masks_sensitive(result):
    parsed = json.loads(export_json(result, mask=True))
    for entry in parsed["differences"]:
        if entry["key"] == "DB_PASSWORD":
            for val in (entry.get("staging_value", ""), entry.get("production_value", "")):
                if val:
                    assert val == "***", f"Expected masked value, got {val!r}"


# --- CSV ---

def test_export_csv_has_header(result):
    output = export_csv(result)
    reader = csv.reader(io.StringIO(output))
    header = next(reader)
    assert header == ["key", "status", "staging_value", "production_value"]


def test_export_csv_excludes_unchanged(result):
    output = export_csv(result)
    reader = csv.DictReader(io.StringIO(output))
    statuses = {row["status"] for row in reader}
    assert "unchanged" not in statuses


def test_export_csv_masks_sensitive(result):
    output = export_csv(result, mask=True)
    reader = csv.DictReader(io.StringIO(output))
    for row in reader:
        if row["key"] == "DB_PASSWORD":
            for col in ("staging_value", "production_value"):
                if row[col]:
                    assert row[col] == "***"


# --- Markdown ---

def test_export_markdown_contains_table_header(result):
    output = export_markdown(result)
    assert "| Key | Status | Staging | Production |" in output


def test_export_markdown_contains_summary(result):
    output = export_markdown(result)
    assert "**Summary**" in output


def test_export_markdown_excludes_unchanged(result):
    output = export_markdown(result)
    assert "unchanged" not in output.lower().split("**summary**")[0]
