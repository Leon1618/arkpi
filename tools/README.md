# Tools

**Optional.** You don't need anything here to read the guides. These scripts
are for downloading the big libraries and making a searchable website.
They run on Mac and Linux.

| Script | What it does |
|---|---|
| `download-library.sh` | Downloads offline libraries into `library/` (needs internet) |
| `open-library.sh` | Opens the downloaded libraries in a browser at http://localhost:8080 |
| `build-website.sh` | Turns the guides into a searchable website in `website/` |
| `download-local.sh` | Downloads Noosa Council's emergency guide and local flood maps into `12-noosa-tewantin/downloads/` (needs internet) |

Run them from the Arkpi folder, for example:

```bash
./tools/download-library.sh --list
```

Other files here:

- `make-image.py`: turns any picture into a small greyscale PNG for a guide
  (`tools/.venv/bin/python tools/make-image.py input.jpg 03-water/images/name.png 480`)
- `library-sources.tsv`: the list of libraries the download script knows about
- `website-config.yml`, `requirements.txt`: settings and Python packages for the
  website build and image tool
