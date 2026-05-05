"""envdiff — Diff environment variable sets across staging and production configs."""

__version__ = "0.1.0"
__author__ = "envdiff contributors"

from envdiff.parser import parse_env_file

__all__ = ["parse_env_file"]
