"""Standalone entry-point shim for the baseline sub-command.

Allows running::

    python -m envdiff.cli_baseline_main staging.env prod.env baseline.json

or via the ``envdiff-baseline`` console script defined in pyproject.toml.
"""

from __future__ import annotations

import sys

from envdiff.cli_baseline import build_baseline_parser, _run_baseline


def main() -> None:
    parser = build_baseline_parser()
    args = parser.parse_args()
    sys.exit(_run_baseline(args))


if __name__ == "__main__":
    main()
