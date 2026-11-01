"""Build START-HERE.html: the offline reader for the whole ark.

Usage:
    tools/.venv/bin/python tools/build-reader.py

Reads every guide (Markdown) in the numbered folders, turns it into HTML and
packs it into one file at the top of the ark, START-HERE.html. That file opens
in any browser straight from the folder or a USB stick: no internet, no server.
Pictures, PDFs and books are linked where they already are, so keep
START-HERE.html in the ark's top folder.

Run it again after changing any guide. Needs the `markdown` package
(installed by tools/update-reader.sh, or: pip install markdown).
"""
import html
import json
import posixpath
import re
import subprocess
from pathlib import Path

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "tools" / "reader-template.html"
OUTPUT = ROOT / "START-HERE.html"

# The red bar shown on every screen
CALL_BAR = {
    "number": "000",
    "text": "Emergency · 112 from a mobile · ABC Sunshine Coast 90.3 FM",
    "link": "12-noosa-tewantin/emergency-contacts",
}

# Big buttons on the home screen: (page, label, hint, life-threatening?)
URGENT = [
    ("01-emergency/severe-bleeding", "Severe bleeding", "Pressure, tourniquet", True),
    ("01-emergency/cpr", "Not breathing", "CPR, step by step", True),
    ("01-emergency/choking", "Choking", "Back blows, chest thrusts", True),
    ("01-emergency/burns", "Burns", "Cool water 20 minutes", False),
    ("02-first-aid/bites-and-stings-australia", "Snake or spider bite", "Pressure bandage", False),
    ("01-emergency/home-fire", "Fire at home", "Get low, get out", False),
    ("01-emergency/flood", "Flood", "If it's flooded, forget it", False),
    ("01-emergency/gas-leak", "Gas leak", "No switches, leave", False),
    ("01-emergency/power-outage", "Power out", "Fridge 4 h, freezer 48 h", False),
]

# Plain words people use, mapped to the page they're looking for
SYNONYMS = {
    "heimlich": "01-emergency/choking", "choke": "01-emergency/choking", "throat": "01-emergency/choking",
    "not breathing": "01-emergency/cpr", "unconscious": "01-emergency/cpr", "unresponsive": "01-emergency/cpr",
    "collapse": "01-emergency/cpr", "heart": "01-emergency/cpr", "aed": "01-emergency/cpr", "drsabcd": "01-emergency/cpr",
    "blood": "01-emergency/severe-bleeding", "bleed": "01-emergency/severe-bleeding", "tourniquet": "01-emergency/severe-bleeding",
    "stab": "01-emergency/severe-bleeding", "cut": "02-first-aid/cuts-and-wounds", "infection": "02-first-aid/cuts-and-wounds",
    "broken": "02-first-aid/broken-bones", "fracture": "02-first-aid/broken-bones", "splint": "02-first-aid/broken-bones",
    "sling": "02-first-aid/broken-bones", "scald": "01-emergency/burns", "snake": "02-first-aid/bites-and-stings-australia",
    "spider": "02-first-aid/bites-and-stings-australia", "tick": "02-first-aid/bites-and-stings-australia",
    "bluebottle": "02-first-aid/bites-and-stings-australia", "jellyfish": "02-first-aid/bites-and-stings-australia",
    "diarrhoea": "02-first-aid/dehydration", "diarrhea": "02-first-aid/dehydration", "vomit": "02-first-aid/dehydration",
    "ors": "02-first-aid/dehydration", "cold": "02-first-aid/hypothermia", "hot": "02-first-aid/heat-illness",
    "heatstroke": "02-first-aid/heat-illness", "drink": "03-water/making-water-safe", "boil": "03-water/making-water-safe",
    "bleach": "03-water/making-water-safe", "co": "01-emergency/carbon-monoxide", "generator": "01-emergency/carbon-monoxide",
    "blackout": "01-emergency/power-outage", "fridge": "01-emergency/power-outage", "000": "12-noosa-tewantin/emergency-contacts",
    "phone": "12-noosa-tewantin/emergency-contacts", "ses": "12-noosa-tewantin/emergency-contacts",
    "hospital": "10-navigation-and-maps/key-places-noosa", "radio": "09-communication/emergency-communication",
    "cyclone": "12-noosa-tewantin/cyclone-and-storm-tide", "storm": "12-noosa-tewantin/cyclone-and-storm-tide",
    "bushfire": "12-noosa-tewantin/bushfire", "warning": "12-noosa-tewantin/warnings", "kit": "11-preparedness/emergency-kit",
    "allergy": "01-emergency/anaphylaxis", "anaphylaxis": "01-emergency/anaphylaxis", "epipen": "01-emergency/anaphylaxis",
    "baby": "01-emergency/cpr-babies-and-children", "infant": "01-emergency/cpr-babies-and-children", "child": "01-emergency/cpr-babies-and-children",
    "tornado": "01-emergency/tornado", "sprain": "02-first-aid/sprains-and-strains", "ankle": "02-first-aid/sprains-and-strains",
    "eye": "02-first-aid/eye-injuries", "medicine": "02-first-aid/medicines-in-an-emergency", "insulin": "02-first-aid/medicines-in-an-emergency",
    "prescription": "02-first-aid/medicines-in-an-emergency", "rain": "03-water/collecting-water", "well": "03-water/disinfecting-a-well",
    "food": "04-food/food-safety-in-an-emergency", "freezer": "04-food/food-safety-in-an-emergency",
    "shelter": "05-shelter-and-warmth/improvised-shelter", "tarp": "05-shelter-and-warmth/improvised-shelter",
    "knot": "05-shelter-and-warmth/knots", "rope": "05-shelter-and-warmth/knots", "stay inside": "05-shelter-and-warmth/shelter-in-place",
    "fire": "06-fire-and-light/lighting-a-fire", "matches": "06-fire-and-light/lighting-a-fire", "candle": "06-fire-and-light/safe-lighting",
    "torch": "06-fire-and-light/safe-lighting", "toilet": "07-sanitation-and-hygiene/toilets-and-hygiene", "wash": "07-sanitation-and-hygiene/toilets-and-hygiene",
    "battery": "08-power/generators-and-backup-power", "uhf": "09-communication/emergency-communication", "cb": "09-communication/emergency-communication",
    "signal": "09-communication/emergency-communication", "map": "10-navigation-and-maps/maps-noosa", "north": "10-navigation-and-maps/finding-direction",
    "south": "10-navigation-and-maps/finding-direction", "compass": "10-navigation-and-maps/finding-direction", "direction": "10-navigation-and-maps/finding-direction",
    "pharmacy": "10-navigation-and-maps/key-places-noosa", "plan": "11-preparedness/family-emergency-plan", "evacuate": "11-preparedness/family-emergency-plan",
    "book": "13-literature/README", "read": "13-literature/README", "novel": "13-literature/README",
}

GUIDE_FOLDERS = sorted(p.name for p in ROOT.iterdir() if p.is_dir() and re.match(r"\d\d-", p.name))
EXTRA_PAGES = ["README.md", "library/README.md", "tools/README.md"]


def tracked_markdown():
    """Guide pages: README plus every .md in the numbered folders (not images/ credits or downloads)."""
    files = [ROOT / p for p in EXTRA_PAGES if (ROOT / p).exists()]
    for folder in GUIDE_FOLDERS:
        for f in sorted((ROOT / folder).rglob("*.md")):
            rel = f.relative_to(ROOT).as_posix()
            if "/downloads/" not in rel:
                files.append(f)
    return files


def page_key(rel_path):
    """'01-emergency/cpr.md' -> '01-emergency/cpr'."""
    return rel_path[:-3] if rel_path.endswith(".md") else rel_path


def tidy_source(text):
    # Python-Markdown needs 4-space indents to keep pictures and sub-lists inside a list item
    text = re.sub(r"^( {2,3})(?=\S)", "    ", text, flags=re.M)
    # Checklists: show a box people can tick on paper
    return re.sub(r"^(\s*[-*]) \[ \] ", r"\1 ☐ ", text, flags=re.M)


class LinkRewriter(Treeprocessor):
    """Point links at reader routes (#/page) or at files next to START-HERE.html."""

    def __init__(self, md, page_dir):
        super().__init__(md)
        self.page_dir = page_dir

    def resolve(self, target):
        return posixpath.normpath(posixpath.join(self.page_dir, target)) if self.page_dir else posixpath.normpath(target)

    def run(self, root):
        for el in root.iter():
            if el.tag == "a":
                href = el.get("href", "")
                if re.match(r"^[a-z]+:", href):
                    el.set("target", "_blank")
                    el.set("rel", "noopener")
                    el.set("class", "ext")
                elif href.startswith("#"):
                    el.set("href", "#/" + self.md.page + href.replace("#", "~", 1))
                else:
                    path, _, anchor = href.partition("#")
                    target = self.resolve(path)
                    if target.endswith(".md"):
                        el.set("href", "#/" + page_key(target) + ("~" + anchor if anchor else ""))
                    else:
                        el.set("href", target)
                        el.set("target", "_blank")
            elif el.tag == "img":
                el.set("src", self.resolve(el.get("src", "")))
                el.set("loading", "lazy")


class ArkExtension(Extension):
    def __init__(self, page_dir):
        super().__init__()
        self.page_dir = page_dir

    def extendMarkdown(self, md):
        md.treeprocessors.register(LinkRewriter(md, self.page_dir), "ark-links", 1)


def plain_text(html_text):
    text = re.sub(r"<[^>]+>", " ", html_text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def build_pages():
    pages = {}
    for f in tracked_markdown():
        rel = f.relative_to(ROOT).as_posix()
        key = page_key(rel)
        md = markdown.Markdown(extensions=["tables", "toc", "attr_list", "sane_lists", ArkExtension(posixpath.dirname(rel))])
        md.page = key
        body = md.convert(tidy_source(f.read_text(encoding="utf-8")))
        title_match = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
        title = plain_text(title_match.group(1)) if title_match else key
        folder = key.split("/")[0] if "/" in key else ""
        pages[key] = {"title": title, "folder": folder, "html": body, "text": plain_text(body)[:6000]}
    return pages


def build_books():
    """Each book in the literature catalog becomes a search result that opens the text file."""
    readme = ROOT / "13-literature" / "README.md"
    books = []
    if readme.exists():
        for title, path, author in re.findall(r"^\| \[(.+?)\]\((.+?)\) \| (.+?) \|", readme.read_text(encoding="utf-8"), re.M):
            books.append({"title": title, "author": re.sub(r"\s*\(.*?\)", "", author), "path": "13-literature/" + path})
    return books


def build():
    pages = build_pages()
    sections = []
    for folder in GUIDE_FOLDERS:
        key = f"{folder}/README"
        if key in pages:
            count = sum(1 for k in pages if k.startswith(folder + "/") and not k.endswith("README") and "/images/" not in k)
            sections.append({"key": key, "number": folder[:2], "title": re.sub(r"^\d+\s*·\s*", "", pages[key]["title"]), "count": count})
    missing = [k for k, *_ in URGENT if k not in pages] + [v for v in SYNONYMS.values() if v not in pages]
    if missing:
        raise SystemExit(f"Home screen or search points to missing pages: {sorted(set(missing))}")

    try:
        version = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%cs"], capture_output=True, text=True).stdout.strip()
    except OSError:
        version = ""
    data = {
        "pages": pages, "sections": sections, "urgent": URGENT, "synonyms": SYNONYMS,
        "books": build_books(), "call": CALL_BAR, "updated": version,
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    OUTPUT.write_text(TEMPLATE.read_text(encoding="utf-8").replace("/*ARK_DATA*/null", payload), encoding="utf-8")
    print(f"✓ {OUTPUT.name}: {len(pages)} pages, {len(data['books'])} books, {OUTPUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    build()
