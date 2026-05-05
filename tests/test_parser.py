"""Tests for envdiff.parser module."""

import pytest
from pathlib import Path

from envdiff.parser import parse_env_file


@pytest.fixture
def env_file(tmp_path: Path):
    """Factory fixture that writes a .env file to a temp directory."""
    def _write(contents: str) -> str:
        p = tmp_path / ".env"
        p.write_text(contents, encoding="utf-8")
        return str(p)
    return _write


def test_basic_key_value(env_file):
    path = env_file("APP_ENV=production\nDEBUG=false\n")
    result = parse_env_file(path)
    assert result == {"APP_ENV": "production", "DEBUG": "false"}


def test_export_prefix(env_file):
    path = env_file("export DATABASE_URL=postgres://localhost/db\n")
    result = parse_env_file(path)
    assert result["DATABASE_URL"] == "postgres://localhost/db"


def test_double_quoted_value(env_file):
    path = env_file('SECRET_KEY="my secret key"\n')
    result = parse_env_file(path)
    assert result["SECRET_KEY"] == "my secret key"


def test_single_quoted_value(env_file):
    path = env_file("API_TOKEN='abc123'\n")
    result = parse_env_file(path)
    assert result["API_TOKEN"] == "abc123"


def test_inline_comment_stripped(env_file):
    path = env_file("PORT=8080 # web server port\n")
    result = parse_env_file(path)
    assert result["PORT"] == "8080"


def test_blank_lines_and_comments_ignored(env_file):
    contents = "# This is a comment\n\nFOO=bar\n\n# Another comment\nBAZ=qux\n"
    path = env_file(contents)
    result = parse_env_file(path)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_empty_value(env_file):
    path = env_file("EMPTY=\n")
    result = parse_env_file(path)
    assert result["EMPTY"] == ""


def test_file_not_found():
    with pytest.raises(FileNotFoundError, match="Env file not found"):
        parse_env_file("/nonexistent/path/.env")


def test_invalid_lines_skipped(env_file):
    contents = "VALID=yes\nthis is not valid\nALSO_VALID=true\n"
    path = env_file(contents)
    result = parse_env_file(path)
    assert result == {"VALID": "yes", "ALSO_VALID": "true"}
