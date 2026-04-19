#!/usr/bin/env bash
set -euo pipefail
pytest
ruff check .
black --check .
mypy app
bandit -r app
