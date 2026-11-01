#!/usr/bin/env bash
# Preview the guides at http://localhost:8000 with live reload while editing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec "$ROOT/.venv/bin/mkdocs" serve -f "$ROOT/site/mkdocs.yml" -a 127.0.0.1:8000
