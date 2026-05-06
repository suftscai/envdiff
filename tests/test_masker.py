"""Tests for envdiff.masker."""

import pytest
from envdiff.masker import is_sensitive, mask_value, mask_env, MASK_PLACEHOLDER


# ---------------------------------------------------------------------------
# is_sensitive
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", [
    "PASSWORD",
    "db_password",
    "SECRET_KEY",
    "API_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
    "PRIVATE_KEY",
    "AUTH_TOKEN",
    "stripe_api_key",
    "CREDENTIAL",
    "PASSPHRASE",
])
def test_sensitive_keys_detected(key):
    assert is_sensitive(key) is True


@pytest.mark.parametrize("key", [
    "APP_ENV",
    "DATABASE_URL",
    "PORT",
    "LOG_LEVEL",
    "REDIS_HOST",
    "FEATURE_FLAG",
])
def test_non_sensitive_keys_pass_through(key):
    assert is_sensitive(key) is False


# ---------------------------------------------------------------------------
# mask_value
# ---------------------------------------------------------------------------

def test_mask_value_replaces_sensitive():
    assert mask_value("DB_PASSWORD", "s3cr3t") == MASK_PLACEHOLDER


def test_mask_value_keeps_non_sensitive():
    assert mask_value("APP_ENV", "production") == "production"


def test_mask_value_custom_placeholder():
    result = mask_value("API_TOKEN", "abc123", placeholder="<REDACTED>")
    assert result == "<REDACTED>"


# ---------------------------------------------------------------------------
# mask_env
# ---------------------------------------------------------------------------

def test_mask_env_replaces_all_sensitive():
    env = {
        "APP_ENV": "staging",
        "DB_PASSWORD": "hunter2",
        "SECRET_KEY": "topsecret",
        "PORT": "8080",
    }
    masked = mask_env(env)
    assert masked["APP_ENV"] == "staging"
    assert masked["PORT"] == "8080"
    assert masked["DB_PASSWORD"] == MASK_PLACEHOLDER
    assert masked["SECRET_KEY"] == MASK_PLACEHOLDER


def test_mask_env_does_not_mutate_original():
    env = {"API_TOKEN": "real_value"}
    mask_env(env)
    assert env["API_TOKEN"] == "real_value"


def test_mask_env_empty_dict():
    assert mask_env({}) == {}


def test_mask_env_custom_placeholder():
    env = {"DB_PASSWORD": "secret"}
    masked = mask_env(env, placeholder="XXX")
    assert masked["DB_PASSWORD"] == "XXX"
