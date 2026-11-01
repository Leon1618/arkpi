#!/usr/bin/env bash
# One-time setup: Python venv with MkDocs for building the guides site.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

python3 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/pip" install --quiet --upgrade pip
"$ROOT/.venv/bin/pip" install --quiet -r "$ROOT/site/requirements.txt"
echo "✓ MkDocs installed in .venv"

if ! command -v kiwix-serve >/dev/null; then
  echo "Optional: install kiwix-tools for the reference library: brew install kiwix-tools"
fi
