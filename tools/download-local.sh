#!/usr/bin/env bash
# Download Noosa Council's emergency documents into 12-noosa-tewantin/downloads/
# (not stored on GitHub). Re-run any time to get the latest versions.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/12-noosa-tewantin/downloads"
NOOSA="https://www.noosa.qld.gov.au/files/assets/public"

# name<TAB>url
FILES="
noosa-emergency-action-guide.pdf	$NOOSA/v/3/community/documents/noosa-emergency-action-guide-4th-edition.pdf
flood-map-tewantin-minor-moderate.pdf	$NOOSA/v/1/community/documents/mapping/minor-moderate-flood-maps/20250307_tewantinfloodmap.pdf
flood-map-tewantin-major-extreme.pdf	$NOOSA/v/1/community/documents/mapping/major-extreme-flood-maps/20250509_tewantinfloodmap-majorextreme.pdf
flood-map-noosaville-minor-moderate.pdf	$NOOSA/v/1/community/documents/mapping/minor-moderate-flood-maps/20250307_noosaville.pdf
flood-map-noosaville-major-extreme.pdf	$NOOSA/v/1/community/documents/mapping/major-extreme-flood-maps/20250509_noosaville-majorextreme.pdf
flood-map-noosa-heads-minor-moderate.pdf	$NOOSA/v/1/community/documents/mapping/minor-moderate-flood-maps/20250307_noosaheadsfloodmap.pdf
flood-map-noosa-heads-major-extreme.pdf	$NOOSA/v/1/community/documents/mapping/major-extreme-flood-maps/20250509_noosaheadsfloodmap-majorextreme.pdf
"

mkdir -p "$DEST"
failed=0
while IFS=$'\t' read -r name url; do
  [[ -z "$name" ]] && continue
  echo "↓ $name"
  if curl -fL --progress-bar --retry 3 -o "$DEST/$name.part" "$url"; then
    mv "$DEST/$name.part" "$DEST/$name"
  else
    rm -f "$DEST/$name.part"
    echo "✗ $name: download failed (the council may have moved it; see https://www.noosa.qld.gov.au/community/maps/disaster-mapping)" >&2
    failed=1
  fi
done <<<"$FILES"

echo "✓ Saved to 12-noosa-tewantin/downloads/"
exit $failed
