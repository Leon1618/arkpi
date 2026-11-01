#!/usr/bin/env bash
# Optional: turn the guides into a searchable website in website/.
# Open website/index.html in any browser. It works offline and from a USB drive.
# Needs Python 3 the first time (to install MkDocs into tools/.venv).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/tools"
VENV="$TOOLS/.venv"
SRC="$TOOLS/.website-src"

if [[ ! -x "$VENV/bin/mkdocs" ]]; then
  echo "First run: installing MkDocs into tools/.venv…"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet -r "$TOOLS/website-requirements.txt"
fi

# Gather the readable pages (not the big .zim libraries) into a temp folder
rm -rf "$SRC"
rsync -a \
  --exclude '.*' --exclude 'website/' --exclude 'private/' \
  --exclude '*.zim' --exclude '*.sh' --exclude '*.tsv' --exclude '*.yml' --exclude '*.txt' \
  "$ROOT/" "$SRC/"

"$VENV/bin/mkdocs" build --quiet --strict --clean -f "$TOOLS/website-config.yml"
rm -rf "$SRC"
echo "✓ Website ready: open website/index.html"
