#!/usr/bin/env bash
# Serve every .zim file in library/ at http://localhost:8080
# Requires kiwix-tools (Mac: brew install kiwix-tools).
# Or skip this script and open the .zim files in the Kiwix app: https://kiwix.org
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8080}"

if ! command -v kiwix-serve >/dev/null; then
  echo "kiwix-serve not found. Install it with: brew install kiwix-tools" >&2
  exit 1
fi

shopt -s nullglob
zims=("$ROOT"/library/*.zim)
if (( ${#zims[@]} == 0 )); then
  echo "No .zim files in library/. Download some first:" >&2
  echo "  ./tools/download-library.sh --tier essential" >&2
  exit 1
fi

echo "Serving ${#zims[@]} librar$( (( ${#zims[@]} == 1 )) && echo y || echo ies) at http://localhost:$PORT"
exec kiwix-serve --address=127.0.0.1 --port="$PORT" "${zims[@]}"
