"""Turn any image into a small black-and-white PNG for the ark.

Usage:
    tools/.venv/bin/python tools/make-image.py <input> <output.png> [max-width]

Converts to greyscale, shrinks to max-width pixels (default 480) and reduces
to 16 shades of grey, so most drawings end up well under 50 KB.
Needs Pillow (installed by tools/update-reader.sh, or: pip install pillow).
"""
import sys

from PIL import Image, ImageOps

src, dst = sys.argv[1], sys.argv[2]
max_width = int(sys.argv[3]) if len(sys.argv) > 3 else 480

img = Image.open(src)
if img.mode in ("RGBA", "LA", "P"):
    # Put transparent images on white before dropping colour
    img = img.convert("RGBA")
    background = Image.new("RGBA", img.size, "white")
    img = Image.alpha_composite(background, img)
img = img.convert("L")

# Some scanned line drawings are stored white-on-black; flip them
if sum(img.getdata()) / (img.width * img.height) < 100:
    img = ImageOps.invert(img)

if img.width > max_width:
    img = img.resize((max_width, round(img.height * max_width / img.width)), Image.LANCZOS)

img = img.quantize(colors=16)
img.save(dst, optimize=True)
print(f"{dst}: {img.width}x{img.height}")
