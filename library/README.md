# Library

Large offline libraries: Wikipedia, a medical encyclopedia, survival manuals,
repair guides and more. They are too big for GitHub, so they are downloaded
separately into this folder as `.zim` files.

## Get the libraries (needs internet, do it now)

```bash
./tools/download-library.sh --list                # see what's available
./tools/download-library.sh --tier essential      # about 1 GB of core survival content
```

## Survival manual (PDF, 24 MB)

The US Army's *ATP 3-50.21 Survival* (2018) is public domain and covers water,
fire, shelter, navigation and knots in depth. Many drawings in this ark come
from it. Save it here:

```bash
curl -L -o library/atp-3-50-21-survival.pdf "https://armypubs.army.mil/epubs/DR_pubs/DR_a/pdf/web/ARN12086_ATP%203-50x21%20FINAL%20WEB%202.pdf"
```

## Read the libraries (no internet needed)

- **Easiest:** install the free **Kiwix** app (Mac, Windows, Linux, Android,
  iPhone) from https://kiwix.org and open any `.zim` file from this folder.
- **In a browser:** `./tools/open-library.sh`, then go to http://localhost:8080
