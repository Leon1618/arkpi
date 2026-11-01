#!/usr/bin/env bash
# Download offline libraries (Kiwix .zim files) listed in
# tools/library-sources.tsv into library/, verifying each sha256.
#
# Usage:
#   download-library.sh --list               show available libraries
#   download-library.sh <id> [<id> ...]      download specific libraries
#   download-library.sh --tier essential     download every library in a tier
#
# Downloads resume if interrupted. Older versions of a library are removed
# only after the new one has been verified.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCES="$ROOT/tools/library-sources.tsv"
DEST="$ROOT/library"
MIRROR="https://download.kiwix.org/zim"

sources() { grep -v '^#' "$SOURCES" | grep -v '^[[:space:]]*$'; }

list() {
  printf '%-22s %-12s %6s  %s\n' ID TIER SIZE DESCRIPTION
  sources | while IFS=$'\t' read -r id dir prefix size tier desc; do
    local mark=""
    ls "$DEST/${prefix}_"*.zim >/dev/null 2>&1 && mark=" [downloaded]"
    printf '%-22s %-12s %6s  %s%s\n' "$id" "$tier" "$size" "$desc" "$mark"
  done
}

# Newest file in $1 named <prefix>_YYYY-MM.zim
latest() {
  local dir="$1" prefix="$2"
  curl -fsSL "$MIRROR/$dir/" \
    | grep -oE "href=\"${prefix//./\\.}_[0-9]{4}-[0-9]{2}\.zim\"" \
    | sed -E 's/href="(.*)"/\1/' | sort | tail -1
}

fetch() {
  local id="$1" line dir prefix size tier desc file
  line="$(sources | awk -F'\t' -v id="$id" '$1 == id')"
  if [[ -z "$line" ]]; then
    echo "Unknown source: $id (see --list)" >&2
    return 1
  fi
  IFS=$'\t' read -r _ dir prefix size tier desc <<<"$line"

  file="$(latest "$dir" "$prefix")"
  if [[ -z "$file" ]]; then
    echo "No file matching ${prefix}_YYYY-MM.zim found in $MIRROR/$dir/" >&2
    return 1
  fi
  if [[ -f "$DEST/$file" ]]; then
    echo "✓ $id: $file already downloaded"
    return 0
  fi

  echo "↓ $id: $file (~$size)"
  curl -fL --progress-bar --retry 5 -C - -o "$DEST/$file.part" "$MIRROR/$dir/$file"

  echo "  verifying sha256…"
  local expected actual
  expected="$(curl -fsSL "$MIRROR/$dir/$file.sha256" | awk '{print $1}')"
  actual="$(shasum -a 256 "$DEST/$file.part" | awk '{print $1}')"
  if [[ "$expected" != "$actual" ]]; then
    echo "✗ $id: checksum mismatch, removing download" >&2
    rm -f "$DEST/$file.part"
    return 1
  fi
  mv "$DEST/$file.part" "$DEST/$file"

  # Remove superseded versions of the same source
  for old in "$DEST/${prefix}_"*.zim; do
    if [[ "$old" != "$DEST/$file" ]]; then
      rm -f "$old"
      echo "  removed old $(basename "$old")"
    fi
  done
  echo "✓ $id: $file"
}

mkdir -p "$DEST"

case "${1:-}" in
  ""|-h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//' ;;
  --list) list ;;
  --tier)
    [[ -n "${2:-}" ]] || { echo "Usage: $0 --tier <essential|recommended|optional|large>" >&2; exit 1; }
    ids="$(sources | awk -F'\t' -v t="$2" '$5 == t {print $1}')"
    [[ -n "$ids" ]] || { echo "No sources in tier: $2" >&2; exit 1; }
    for id in $ids; do fetch "$id"; done
    ;;
  *) for id in "$@"; do fetch "$id"; done ;;
esac
