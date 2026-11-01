# Arkpi — Offline Knowledge Ark

A self-contained, offline library of survival guides and reference material
that runs on a Mac and keeps working during an internet outage. Everything is
served from `localhost` (or opened straight from disk), so no network is needed
once content has been downloaded.

## Layout

```
guides/           Markdown survival guides (source of truth for our own content)
site/             MkDocs config and theme overrides
content-sources/  Lists of external content (ZIMs, PDFs) with URLs
scripts/          Setup, download, build and serve scripts
data/             Downloaded content (ZIM files, PDFs) — not in git
```

## Quick start (on your Mac)

```bash
./scripts/setup.sh          # create Python venv and install MkDocs
./scripts/build-site.sh     # build guides into site/build/
./scripts/serve-guides.sh   # preview guides at http://localhost:8000
```

Offline reference library (Wikipedia, WikiMed, etc.):

```bash
brew install kiwix-tools                  # one-time
./scripts/fetch-content.sh --list             # see available sources
./scripts/fetch-content.sh zimgit-water       # download one source
./scripts/fetch-content.sh --tier essential   # ~1 GB of core survival content
./scripts/serve-kiwix.sh                  # browse at http://localhost:8080
```

## Writing a guide

Create a Markdown file under `guides/<category>/`. Every guide must start with
front matter recording where the information came from:

```yaml
---
title: Purifying Water
sources:
  - name: CDC — Making Water Safe in an Emergency
    url: https://www.cdc.gov/water-emergency/
    retrieved: 2026-11-01
reviewed: 2026-11-01
---
```

Medical and safety content must come from vetted sources (CDC, FEMA, WHO,
Red Cross, military field manuals) — never from memory.
