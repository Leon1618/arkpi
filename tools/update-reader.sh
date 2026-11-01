#!/usr/bin/env bash
# Rebuild START-HERE.html (the offline reader) after changing any guide.
# Needs Python 3 the first time, to install the Markdown and Pillow packages
# into tools/.venv. No internet is needed after that.
set -euo pipefail

TOOLS="$(cd "$(dirname "$0")" && pwd)"
VENV="$TOOLS/.venv"

if ! "$VENV/bin/python" -c "import markdown, PIL" 2>/dev/null; then
  echo "First run: installing Markdown and Pillow into tools/.venv…"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet -r "$TOOLS/requirements.txt"
fi

"$VENV/bin/python" "$TOOLS/build-reader.py"
