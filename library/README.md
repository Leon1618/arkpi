# Library

Large offline libraries: Wikipedia, a medical encyclopedia, survival manuals,
repair guides and more. They are too big for GitHub, so they are downloaded
separately into this folder as `.zim` files.

## Get the libraries (needs internet, do it now)

```bash
./tools/download-library.sh --list                # see what's available
./tools/download-library.sh --tier essential      # about 1 GB of core survival content
```

## Read the libraries (no internet needed)

- **Easiest:** install the free **Kiwix** app (Mac, Windows, Linux, Android,
  iPhone) from https://kiwix.org and open any `.zim` file from this folder.
- **In a browser:** `./tools/open-library.sh`, then go to http://localhost:8080
