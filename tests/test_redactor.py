"""Tests for envdiff.redactor."""

from __future__ import annotations

import pytest

from envdiff.redactor import DEFAULT_PLACEHOLDER, RedactionReport, redact_env


@pytest.fixture()
def env() -> dict:
    return {
        "DATABASE_URL": "postgres://user:pass@host/db",
        "API_KEY": "supersecret",
        "APP_ENV": "production",
        "SECRET_TOKEN": "tok_abc123",
        "PORT": "8080",
    }


def test_returns_redaction_report(env):
    report = redact_env(env)
    assert isinstance(report, RedactionReport)


def test_sensitive_keys_are_redacted(env):
    report = redact_env(env)
    assert report.redacted["API_KEY"] == DEFAULT_PLACEHOLDER
    assert report.redacted["SECRET_TOKEN"] == DEFAULT_PLACEHOLDER


def test_non_sensitive_keys_are_unchanged(env):
    report = redact_env(env)
    assert report.redacted["APP_ENV"] == "production"
    assert report.redacted["PORT"] == "8080"


def test_redacted_keys_list_contains_sensitive(env):
    report = redact_env(env)
    assert "API_KEY" in report.redacted_keys
    assert "SECRET_TOKEN" in report.redacted_keys


def test_redacted_keys_sorted(env):
    report = redact_env(env)
    assert report.redacted_keys == sorted(report.redacted_keys)


def test_original_is_unchanged(env):
    original_copy = dict(env)
    report = redact_env(env)
    assert report.original == original_copy


def test_total_matches_input_length(env):
    report = redact_env(env)
    assert report.total == len(env)


def test_redaction_count_correct(env):
    report = redact_env(env)
    # API_KEY, DATABASE_URL (contains password), SECRET_TOKEN at minimum
    assert report.redaction_count >= 2


def test_custom_placeholder(env):
    report = redact_env(env, placeholder="<hidden>")
    assert report.redacted["API_KEY"] == "<hidden>"


def test_extra_keys_are_redacted(env):
    report = redact_env(env, extra_keys=["APP_ENV"])
    assert report.redacted["APP_ENV"] == DEFAULT_PLACEHOLDER
    assert "APP_ENV" in report.redacted_keys


def test_extra_keys_case_insensitive(env):
    report = redact_env(env, extra_keys=["port"])
    assert report.redacted["PORT"] == DEFAULT_PLACEHOLDER


def test_clean_property_false_when_redactions(env):
    report = redact_env(env)
    assert report.clean is False


def test_clean_property_true_when_no_sensitive():
    report = redact_env({"APP_ENV": "staging", "PORT": "3000"})
    assert report.clean is True


def test_empty_env_produces_clean_report():
    report = redact_env({})
    assert report.total == 0
    assert report.clean is True
    assert report.redacted_keys == []
