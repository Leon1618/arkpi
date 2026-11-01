#!/usr/bin/env bash
# Serve every downloaded ZIM in data/zim/ at http://localhost:8080
# Requires kiwix-tools: brew install kiwix-tools
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8080}"

if ! command -v kiwix-serve >/dev/null; then
  echo "kiwix-serve not found. Install it with: brew install kiwix-tools" >&2
  exit 1
fi

shopt -s nullglob
zims=("$ROOT"/data/zim/*.zim)
if (( ${#zims[@]} == 0 )); then
  echo "No ZIM files in data/zim/. Download some first:" >&2
  echo "  ./scripts/fetch-content.sh --tier essential" >&2
  exit 1
fi

echo "Serving ${#zims[@]} librar$( (( ${#zims[@]} == 1 )) && echo y || echo ies) at http://localhost:$PORT"
exec kiwix-serve --address=127.0.0.1 --port="$PORT" "${zims[@]}"
