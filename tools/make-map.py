"""Draw printable black-and-white maps from OpenStreetMap data.

Usage:
    tools/.venv/bin/python tools/make-map.py

Downloads roads, water, coastline, place names and key places (hospitals,
police, fire and ambulance stations, pharmacies, fuel, drinking water...) for
Noosa Shire from OpenStreetMap (needs internet the first time; the data is
kept in tools/.map-cache.json), then writes SVG maps and a list of places into
10-navigation-and-maps/. Edit AREAS below for another region.

Map data © OpenStreetMap contributors, available under the Open Database
License (https://www.openstreetmap.org/copyright).
"""
import html
import json
import math
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "tools" / ".map-cache.json"
OUT = ROOT / "10-navigation-and-maps"
BBOX = (-26.62, 152.72, -26.15, 153.16)  # south, west, north, east: all of Noosa Shire

# name, file, (south, west, north, east), width in px, show minor roads?
AREAS = [
    ("Noosa Shire", "map-noosa-shire", BBOX, 1400, False),
    ("Tewantin, Noosaville and Noosa Heads", "map-tewantin-noosa", (-26.42, 153.015, -26.37, 153.105), 1400, True),
]

# What counts as a key place, and its symbol letter on the map
PLACES = {
    ("amenity", "hospital"): ("H", "Hospital"),
    ("amenity", "clinic"): ("+", "Clinic"),
    ("amenity", "doctors"): ("+", "Doctor"),
    ("amenity", "pharmacy"): ("Rx", "Pharmacy"),
    ("amenity", "police"): ("P", "Police"),
    ("amenity", "fire_station"): ("F", "Fire station"),
    ("emergency", "ambulance_station"): ("A", "Ambulance station"),
    ("emergency", "ses_station"): ("S", "SES"),
    ("emergency", "lifeguard"): ("L", "Lifeguard"),
    ("amenity", "fuel"): ("⛽", "Fuel"),
    ("shop", "supermarket"): ("$", "Supermarket"),
    ("amenity", "drinking_water"): ("W", "Drinking water"),
    ("amenity", "community_centre"): ("C", "Community centre"),
}
# Shown on the whole-shire map (the rest only on the close-up)
SHIRE_PLACES = {"Hospital", "Police", "Fire station", "Ambulance station", "SES", "Clinic"}

ROAD_STYLE = {  # stroke width, grey, drawn on shire map?
    "motorway": (5, "#000", True), "trunk": (4.5, "#000", True), "primary": (4, "#111", True),
    "secondary": (3, "#333", True), "tertiary": (2.2, "#444", True), "unclassified": (1.2, "#666", True),
    "residential": (1.1, "#777", False),
}


def fetch():
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    s, w, n, e = BBOX
    b = f"({s},{w},{n},{e})"
    query = f"""[out:json][timeout:180];(
      way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential)(_link)?$"]{b};
      way["natural"="coastline"]{b}; way["natural"="water"]{b}; relation["natural"="water"]{b};
      way["waterway"~"^(river|stream)$"]{b};
      node["place"~"^(town|suburb|village|hamlet|locality)$"]{b};
      nwr["amenity"~"^(hospital|clinic|doctors|pharmacy|police|fire_station|fuel|drinking_water|community_centre)$"]{b};
      nwr["emergency"~"^(ses_station|ambulance_station|lifeguard)$"]{b};
      nwr["shop"="supermarket"]{b};
    );out geom;"""
    print("Downloading map data from OpenStreetMap…")
    req = urllib.request.Request("https://overpass-api.de/api/interpreter",
                                 data=urllib.parse.urlencode({"data": query}).encode(),
                                 headers={"User-Agent": "arkpi-offline-library/1.0"})
    data = json.load(urllib.request.urlopen(req, timeout=300))
    CACHE.write_text(json.dumps(data))
    return data


def centre(el):
    if "lat" in el:
        return el["lat"], el["lon"]
    if "center" in el:
        return el["center"]["lat"], el["center"]["lon"]
    pts = el.get("geometry") or [p for m in el.get("members", []) for p in (m.get("geometry") or [])]
    pts = [p for p in pts if p]
    return (sum(p["lat"] for p in pts) / len(pts), sum(p["lon"] for p in pts) / len(pts)) if pts else (None, None)


def rings(rel):
    """Join a water relation's outer ways into closed rings."""
    parts = [[(p["lat"], p["lon"]) for p in m["geometry"]] for m in rel.get("members", [])
             if m.get("role") == "outer" and m.get("geometry")]
    out = []
    while parts:
        ring = parts.pop(0)
        changed = True
        while changed and ring[0] != ring[-1]:
            changed = False
            for i, p in enumerate(parts):
                if p[0] == ring[-1]: ring += p[1:]
                elif p[-1] == ring[-1]: ring += p[::-1][1:]
                elif p[-1] == ring[0]: ring = p + ring[1:]
                elif p[0] == ring[0]: ring = p[::-1] + ring[1:]
                else: continue
                parts.pop(i); changed = True; break
        out.append(ring)
    return out


def key_places(data):
    found, seen = [], set()
    for el in data["elements"]:
        tags = el.get("tags", {})
        for (k, v), (sym, kind) in PLACES.items():
            if tags.get(k) == v:
                lat, lon = centre(el)
                if lat is None: continue
                name = tags.get("name") or kind
                # Only general medical clinics, not dentists, physio, podiatry etc.
                if kind in ("Clinic", "Doctor") and not any(w in name.lower() for w in ("medical", "health", "doctor", "gp", "family", "practice", "surgery")):
                    break
                spot = (kind, round(lat, 3), round(lon, 3))
                if spot in seen: continue
                seen.add(spot)
                addr = " ".join(x for x in [tags.get("addr:housenumber"), tags.get("addr:street"), tags.get("addr:suburb") or tags.get("addr:city")] if x)
                found.append({"sym": sym, "kind": kind, "name": name, "lat": lat, "lon": lon, "addr": addr,
                              "phone": tags.get("phone") or tags.get("contact:phone") or ""})
                break
    order = list(dict.fromkeys(k for _, k in PLACES.values()))
    found.sort(key=lambda p: (order.index(p["kind"]), -p["lat"], p["lon"]))
    for i, p in enumerate(found, 1):
        p["n"] = i
    return found


def draw(data, places, title, bbox, width, minor):
    s, w, n, e = bbox
    kx = math.cos(math.radians((s + n) / 2))
    scale = width / ((e - w) * kx)
    height = round((n - s) * scale)
    xy = lambda lat, lon: ((lon - w) * kx * scale, (n - lat) * scale)

    def pts(geom):
        # Drop points closer than 1.5 px to the last one kept: same look, much smaller file
        kept, last = [], None
        coords = [xy(p["lat"], p["lon"]) for p in geom if p]
        for i, (x, y) in enumerate(coords):
            if last is None or i == len(coords) - 1 or math.dist(last, (x, y)) >= 1.5:
                kept.append(f"{x:.0f},{y:.0f}"); last = (x, y)
        return " ".join(kept)
    inside = lambda lat, lon: s <= lat <= n and w <= lon <= e
    pad = 0.01
    near = lambda geom: any(p and s - pad <= p["lat"] <= n + pad and w - pad <= p["lon"] <= e + pad for p in geom)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height + 60}" width="{width}" height="{height + 60}" font-family="Helvetica, Arial, sans-serif">',
           f'<rect width="100%" height="100%" fill="#fff"/>',
           f'<clipPath id="c"><rect width="{width}" height="{height}"/></clipPath><g clip-path="url(#c)">']
    # Water
    for el in data["elements"]:
        t = el.get("tags", {})
        if t.get("natural") == "water":
            shapes = [el["geometry"]] if el["type"] == "way" else [[{"lat": a, "lon": b} for a, b in r] for r in rings(el)]
            for g in shapes:
                if not near(g): continue
                out.append(f'<polygon points="{pts(g)}" fill="#d4d8dc" stroke="#7a8288" stroke-width="1"/>')
    for el in data["elements"]:
        t = el.get("tags", {})
        if not el.get("geometry") or not near(el["geometry"]):
            continue
        if t.get("waterway") in ("river", "stream"):
            sw = 2.5 if t["waterway"] == "river" else 0.8
            out.append(f'<polyline points="{pts(el["geometry"])}" fill="none" stroke="#8a9298" stroke-width="{sw}"/>')
        if t.get("natural") == "coastline":
            out.append(f'<polyline points="{pts(el["geometry"])}" fill="none" stroke="#000" stroke-width="2.5"/>')
    # Roads, minor first
    for kind in ["residential", "unclassified", "tertiary", "secondary", "primary", "trunk", "motorway"]:
        sw, col, on_shire = ROAD_STYLE[kind]
        if not minor and not on_shire: continue
        if not minor: sw *= 0.7
        for el in data["elements"]:
            hw = el.get("tags", {}).get("highway", "")
            if hw.replace("_link", "") == kind and el.get("geometry") and near(el["geometry"]):
                out.append(f'<polyline points="{pts(el["geometry"])}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')
    # Road names on the close-up (main roads, along the longest piece of each)
    if minor:
        longest = {}
        for el in data["elements"]:
            t = el.get("tags", {})
            if t.get("highway") in ("primary", "secondary", "tertiary", "trunk") and t.get("name") and el.get("geometry"):
                g = [p for p in el["geometry"] if p and inside(p["lat"], p["lon"])]
                if len(g) < 2: continue
                length = sum(math.dist(xy(a["lat"], a["lon"]), xy(b["lat"], b["lon"])) for a, b in zip(g, g[1:]))
                if length > longest.get(t["name"], (0,))[0]:
                    longest[t["name"]] = (length, g)
        for i, (name, (length, g)) in enumerate(longest.items()):
            if length < len(name) * 8: continue
            if xy(g[0]["lat"], g[0]["lon"])[0] > xy(g[-1]["lat"], g[-1]["lon"])[0]: g = g[::-1]
            out.append(f'<path id="r{i}" d="M {pts(g).replace(" ", " L ")}" fill="none"/>'
                       f'<text font-size="13" fill="#000" stroke="#fff" stroke-width="3" paint-order="stroke" dy="-4"><textPath href="#r{i}" startOffset="50%" text-anchor="middle">{html.escape(name)}</textPath></text>')
    # Key places: numbered markers
    for p in places:
        if not inside(p["lat"], p["lon"]) or (not minor and p["kind"] not in SHIRE_PLACES): continue
        x, y = xy(p["lat"], p["lon"])
        r = 11 if minor else 10
        shape = (f'<rect x="{x - r:.0f}" y="{y - r:.0f}" width="{2 * r}" height="{2 * r}" fill="#000" stroke="#fff" stroke-width="2"/>'
                 if p["kind"] in SHIRE_PLACES else f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" stroke="#000" stroke-width="2"/>')
        col = "#fff" if p["kind"] in SHIRE_PLACES else "#000"
        out.append(f'{shape}<text x="{x:.0f}" y="{y + 4:.0f}" font-size="11" font-weight="700" text-anchor="middle" fill="{col}">{p["n"]}</text>')
    # Place names
    sizes = {"town": 26, "suburb": 18, "village": 18, "hamlet": 13, "locality": 12}
    for el in data["elements"]:
        t = el.get("tags", {})
        if el["type"] == "node" and t.get("place") in sizes and inside(el["lat"], el["lon"]):
            if not minor and t["place"] in ("locality", "hamlet"): continue
            x, y = xy(el["lat"], el["lon"])
            fs = sizes[t["place"]] * (1 if minor else 0.8)
            out.append(f'<text x="{x:.0f}" y="{y:.0f}" font-size="{fs:.0f}" font-weight="700" text-anchor="middle" fill="#000" stroke="#fff" stroke-width="4" paint-order="stroke">{html.escape(t.get("name", ""))}</text>')
    out.append("</g>")
    # Frame, scale bar, north arrow, title, credit
    km = scale * 1 / 111.32  # pixels per km (north-south)
    bar = 5 if (width / km) > 15 else 1
    out += [f'<rect width="{width}" height="{height}" fill="none" stroke="#000" stroke-width="2"/>',
            f'<g transform="translate(20,{height + 18})"><rect width="{bar * km:.0f}" height="8" fill="#000"/>'
            f'<text x="{bar * km + 8:.0f}" y="9" font-size="14">{bar} km</text></g>',
            f'<g transform="translate({width - 40},50)"><path d="M0,-30 L12,10 L0,2 L-12,10 Z" fill="#000"/><text y="30" font-size="16" font-weight="700" text-anchor="middle">N</text></g>',
            f'<text x="{width / 2:.0f}" y="{height + 28}" font-size="20" font-weight="700" text-anchor="middle">{html.escape(title)}</text>',
            f'<text x="{width - 20}" y="{height + 50}" font-size="12" text-anchor="end">Map data © OpenStreetMap contributors (ODbL). Black squares: hospital, clinic, police, fire, ambulance, SES. Numbers match the list of places.</text>',
            "</svg>"]
    return "\n".join(out)


def places_page(places):
    lines = ["# Key Places: Noosa Shire", "",
             "Numbers match the markers on the maps. **Black squares** on the maps are emergency",
             "services and health; white circles are everything else. Coordinates are latitude, longitude",
             "(enter them in a GPS or offline map app).", "",
             "> Map data comes from OpenStreetMap volunteers and may be incomplete or out of date.",
             "> In an emergency, call **000**.", ""]
    kinds = list(dict.fromkeys(p["kind"] for p in places))
    for kind in kinds:
        sel = [p for p in places if p["kind"] == kind]
        lines += [f"## {kind} ({len(sel)})", "", "| No. | Name | Address | Lat, Lon |", "|---|---|---|---|"]
        for p in sel:
            addr = p["addr"] + (f" · {p['phone']}" if p["phone"] else "")
            lines.append(f"| {p['n']} | {p['name']} | {addr or '–'} | {p['lat']:.5f}, {p['lon']:.5f} |")
        lines.append("")
    lines += ["---", "", "**Source:** OpenStreetMap, © OpenStreetMap contributors, Open Database License",
              "(https://www.openstreetmap.org/copyright). Downloaded with `tools/make-map.py`.", ""]
    return "\n".join(lines)


def main():
    data = fetch()
    places = key_places(data)
    maps_dir = OUT / "maps"
    maps_dir.mkdir(parents=True, exist_ok=True)
    for title, name, bbox, width, minor in AREAS:
        svg = draw(data, places, title, bbox, width, minor)
        (maps_dir / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(f"✓ {name}.svg ({len(svg) // 1024} KB)")
    (OUT / "key-places-noosa.md").write_text(places_page(places), encoding="utf-8")
    print(f"✓ key-places-noosa.md ({len(places)} places)")


if __name__ == "__main__":
    sys.exit(main())
