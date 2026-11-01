#!/usr/bin/env bash
# Build the guides into site/build/. The result works offline and can be
# opened straight from disk (site/build/index.html) or copied to a USB drive.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/.venv/bin/mkdocs" build --strict --clean -f "$ROOT/site/mkdocs.yml"
echo "✓ Built: $ROOT/site/build/index.html"
