# Tools

**Optional.** You don't need anything here to read the ark: just open
`START-HERE.html`. These scripts are for people who maintain the ark.
They run on Mac and Linux.

| Script | What it does |
|---|---|
| `update-reader.sh` | Rebuilds `START-HERE.html` from the guides. **Run it after changing any guide.** |
| `download-library.sh` | Downloads offline libraries into `library/` (needs internet) |
| `open-library.sh` | Opens the downloaded libraries in a browser at http://localhost:8080 |
| `download-local.sh` | Downloads Noosa Council's emergency guide and local flood maps into `12-noosa-tewantin/downloads/` (needs internet) |

Run them from the Arkpi folder, for example:

```bash
./tools/download-library.sh --list
```

Other files here:

- `make-image.py`: turns any picture into a small greyscale PNG for a guide
  (`tools/.venv/bin/python tools/make-image.py input.jpg 03-water/images/name.png 480`)
- `build-reader.py`, `reader-template.html`: how `START-HERE.html` is made. The
  home screen buttons, the red call bar and the search words are set at the
  top of `build-reader.py`.
- `library-sources.tsv`: the list of libraries the download script knows about
- `requirements.txt`: Python packages for the reader build and image tool
