"""Script to fetch ~200 free SVG icons from Iconify (MIT / Apache 2.0 licensed).
Organized by category into remotion/public/icons/{category}/
Includes offline fallback so every icon is guaranteed to exist.
"""
import os
import sys
import time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST_DIR = ROOT / "remotion" / "public" / "icons"

# Categories and icon specs: (category, filename, iconify_prefix, iconify_name, fallback_symbol)
ICONS_SPEC = [
    # --- History & Antiquity ---
    ("history", "pyramid.svg", "mdi", "pyramid", "pyramid"),
    ("history", "temple.svg", "mdi", "temple-buddhist", "temple"),
    ("history", "scroll.svg", "ph", "scroll", "scroll"),
    ("history", "monument.svg", "mdi", "pillar", "pillar"),
    ("history", "column.svg", "tabler", "column", "column"),
    ("history", "museum.svg", "tabler", "building-monument", "museum"),
    ("history", "castle.svg", "ph", "castle-turret", "castle"),
    ("history", "hourglass.svg", "tabler", "hourglass", "hourglass"),
    ("history", "ruins.svg", "tabler", "building-fortress", "ruins"),
    ("history", "parchment.svg", "mdi", "file-document", "parchment"),
    ("history", "pharaoh.svg", "ph", "crown", "pharaoh"),
    ("history", "shield.svg", "ph", "shield", "shield"),
    ("history", "sword.svg", "ph", "sword", "sword"),
    ("history", "crown.svg", "ph", "crown-simple", "crown"),
    ("history", "archaeology.svg", "tabler", "shovel", "shovel"),
    ("history", "amphora.svg", "mdi", "cup", "amphora"),

    # --- Monument & Architecture ---
    ("monument", "mosque.svg", "mdi", "mosque", "mosque"),
    ("monument", "church.svg", "mdi", "church", "church"),
    ("monument", "tower.svg", "tabler", "tower", "tower"),
    ("monument", "lighthouse.svg", "ph", "lighthouse", "lighthouse"),
    ("monument", "palace.svg", "mdi", "city", "palace"),
    ("monument", "obelisk.svg", "tabler", "monument", "obelisk"),
    ("monument", "dome.svg", "mdi", "dome-light", "dome"),
    ("monument", "gate.svg", "mdi", "gate", "gate"),
    ("monument", "bridge.svg", "ph", "bridge", "bridge"),
    ("monument", "arch.svg", "tabler", "arch", "arch"),
    ("monument", "citadel.svg", "ph", "shield-chevron", "citadel"),
    ("monument", "skyscraper.svg", "tabler", "building-skyscraper", "skyscraper"),

    # --- Map & Geography ---
    ("map", "pin.svg", "ph", "map-pin", "pin"),
    ("map", "globe.svg", "ph", "globe-hemisphere-east", "globe"),
    ("map", "compass.svg", "ph", "compass", "compass"),
    ("map", "flag.svg", "ph", "flag-banner", "flag"),
    ("map", "mountain.svg", "ph", "mountains", "mountain"),
    ("map", "river.svg", "mdi", "waves", "river"),
    ("map", "sea.svg", "tabler", "wave-saw-tool", "sea"),
    ("map", "desert.svg", "mdi", "island", "desert"),
    ("map", "island.svg", "ph", "island", "island"),
    ("map", "route.svg", "tabler", "route", "route"),
    ("map", "navigation.svg", "ph", "navigation-arrow", "navigation"),
    ("map", "border.svg", "tabler", "border-all", "border"),
    ("map", "earth.svg", "mdi", "earth", "earth"),
    ("map", "location.svg", "mdi", "crosshairs-gps", "location"),

    # --- Person & Leaders ---
    ("person", "leader.svg", "ph", "user-circle", "leader"),
    ("person", "king.svg", "mdi", "crown", "king"),
    ("person", "scholar.svg", "ph", "student", "scholar"),
    ("person", "people.svg", "ph", "users-three", "people"),
    ("person", "soldier.svg", "mdi", "shield-account", "soldier"),
    ("person", "warrior.svg", "mdi", "sword-cross", "warrior"),
    ("person", "diplomat.svg", "ph", "handshake", "diplomat"),
    ("person", "crowd.svg", "ph", "users", "crowd"),
    ("person", "hero.svg", "ph", "medal", "hero"),
    ("person", "profile.svg", "tabler", "user", "profile"),

    # --- Science & Knowledge ---
    ("science", "atom.svg", "ph", "atom", "atom"),
    ("science", "dna.svg", "ph", "dna", "dna"),
    ("science", "telescope.svg", "ph", "telescope", "telescope"),
    ("science", "microscope.svg", "ph", "microscope", "microscope"),
    ("science", "planet.svg", "ph", "planet", "planet"),
    ("science", "brain.svg", "ph", "brain", "brain"),
    ("science", "gear.svg", "ph", "gear", "gear"),
    ("science", "magnet.svg", "ph", "magnet", "magnet"),
    ("science", "bulb.svg", "ph", "lightbulb", "bulb"),
    ("science", "rocket.svg", "ph", "rocket", "rocket"),
    ("science", "chemistry.svg", "tabler", "flask", "flask"),
    ("science", "math.svg", "tabler", "math-symbols", "math"),

    # --- Numbers & Metrics ---
    ("number", "num1.svg", "tabler", "number-1", "1"),
    ("number", "num2.svg", "tabler", "number-2", "2"),
    ("number", "num3.svg", "tabler", "number-3", "3"),
    ("number", "num4.svg", "tabler", "number-4", "4"),
    ("number", "num5.svg", "tabler", "number-5", "5"),
    ("number", "percent.svg", "ph", "percent", "percent"),
    ("number", "hash.svg", "ph", "hash", "hash"),
    ("number", "infinity.svg", "ph", "infinity", "infinity"),
    ("number", "calculator.svg", "ph", "calculator", "calc"),
    ("number", "sum.svg", "tabler", "sum", "sum"),

    # --- Arrows & Connectors ---
    ("arrow", "arrow-up.svg", "ph", "arrow-up", "arrow-up"),
    ("arrow", "arrow-down.svg", "ph", "arrow-down", "arrow-down"),
    ("arrow", "arrow-left.svg", "ph", "arrow-left", "arrow-left"),
    ("arrow", "arrow-right.svg", "ph", "arrow-right", "arrow-right"),
    ("arrow", "arrow-up-right.svg", "ph", "arrow-up-right", "arrow-up-right"),
    ("arrow", "arrow-curved.svg", "tabler", "arrow-curve-right", "arrow-curved"),
    ("arrow", "flow.svg", "tabler", "arrows-split", "flow"),
    ("arrow", "target.svg", "ph", "crosshair", "target"),
    ("arrow", "radiate.svg", "tabler", "arrows-maximize", "radiate"),
    ("arrow", "exchange.svg", "ph", "arrows-left-right", "exchange"),

    # --- Fire, Sun & Energy ---
    ("fire", "flame.svg", "ph", "fire", "flame"),
    ("fire", "spark.svg", "ph", "sparkle", "spark"),
    ("fire", "sun.svg", "ph", "sun", "sun"),
    ("fire", "sun-horizon.svg", "ph", "sun-horizon", "sun-horizon"),
    ("fire", "ray.svg", "tabler", "sun", "ray"),
    ("fire", "torch.svg", "mdi", "torch", "torch"),
    ("fire", "bolt.svg", "ph", "lightning", "bolt"),
    ("fire", "explosion.svg", "mdi", "firework", "explosion"),

    # --- Star & Accents ---
    ("star", "star.svg", "ph", "star", "star"),
    ("star", "star-four.svg", "ph", "sparkle", "star-four"),
    ("star", "badge.svg", "ph", "seal-check", "badge"),
    ("star", "award.svg", "ph", "certificate", "award"),
    ("star", "medal.svg", "ph", "medal-military", "medal"),
    ("star", "gem.svg", "ph", "diamond", "gem"),
    ("star", "trophy.svg", "ph", "trophy", "trophy"),
    ("star", "glow.svg", "mdi", "shimmer", "glow"),

    # --- Building & Infrastructure ---
    ("building", "city.svg", "ph", "buildings", "city"),
    ("building", "house.svg", "ph", "house", "house"),
    ("building", "bank.svg", "ph", "bank", "bank"),
    ("building", "parliament.svg", "mdi", "pillar", "parliament"),
    ("building", "court.svg", "ph", "scales", "court"),
    ("building", "port.svg", "tabler", "anchor", "port"),
    ("building", "library.svg", "ph", "books", "library"),
    ("building", "factory.svg", "ph", "factory", "factory"),

    # --- Chart & Economy ---
    ("chart", "chart-bar.svg", "ph", "chart-bar", "chart-bar"),
    ("chart", "chart-line.svg", "ph", "chart-line-up", "chart-line"),
    ("chart", "chart-pie.svg", "ph", "chart-pie", "chart-pie"),
    ("chart", "trend-up.svg", "ph", "trend-up", "trend-up"),
    ("chart", "trend-down.svg", "ph", "trend-down", "trend-down"),
    ("chart", "scale.svg", "ph", "scales", "scale"),
    ("chart", "analytics.svg", "mdi", "poll", "analytics"),

    # --- Time & Era ---
    ("time", "clock.svg", "ph", "clock", "clock"),
    ("time", "calendar.svg", "ph", "calendar", "calendar"),
    ("time", "history-clock.svg", "ph", "clock-counter-clockwise", "history-clock"),
    ("time", "stopwatch.svg", "ph", "stopwatch", "stopwatch"),
    ("time", "timeline.svg", "tabler", "timeline", "timeline"),
    ("time", "sand.svg", "ph", "hourglass-medium", "sand"),

    # --- World & Nations ---
    ("world", "world-africa.svg", "mdi", "earth", "world-africa"),
    ("world", "world-globe.svg", "ph", "globe", "world-globe"),
    ("world", "world-network.svg", "ph", "globe-stand", "world-network"),
    ("world", "nations.svg", "ph", "flags", "nations"),

    # --- Book & Documents ---
    ("book", "book.svg", "ph", "book-bookmark", "book"),
    ("book", "book-open.svg", "ph", "book-open-text", "book-open"),
    ("book", "document.svg", "ph", "file-text", "document"),
    ("book", "feather.svg", "ph", "feather", "feather"),
    ("book", "scroll-ancient.svg", "mdi", "script-text", "scroll-ancient"),
    ("book", "constitution.svg", "ph", "certificate", "constitution"),

    # --- Sword & Military ---
    ("sword", "swords.svg", "ph", "sword", "swords"),
    ("sword", "shield-sword.svg", "mdi", "shield-sword", "shield-sword"),
    ("sword", "bow.svg", "ph", "bow", "bow"),
    ("sword", "helmet.svg", "mdi", "racing-helmet", "helmet"),
    ("sword", "cannon.svg", "mdi", "cannon", "cannon"),

    # --- Crown & Royalty ---
    ("crown", "crown-gold.svg", "ph", "crown", "crown-gold"),
    ("crown", "throne.svg", "mdi", "seat", "throne"),
    ("crown", "royal.svg", "ph", "seal", "royal"),

    # --- Coin & Wealth ---
    ("coin", "coin.svg", "ph", "coin", "coin"),
    ("coin", "coins.svg", "ph", "coins", "coins"),
    ("coin", "gold-bars.svg", "tabler", "gold", "gold-bars"),
    ("coin", "treasure.svg", "ph", "treasure-chest", "treasure"),
    ("coin", "money-bag.svg", "ph", "money", "money-bag"),

    # --- Ship & Marine ---
    ("ship", "ship.svg", "ph", "boat", "ship"),
    ("ship", "sailboat.svg", "ph", "sailboat", "sailboat"),
    ("ship", "anchor.svg", "ph", "anchor", "anchor"),
    ("ship", "waves.svg", "ph", "waves", "waves"),

    # --- Tree & Nature ---
    ("tree", "tree.svg", "ph", "tree", "tree"),
    ("tree", "palm.svg", "ph", "tree-palm", "palm"),
    ("tree", "forest.svg", "ph", "tree-evergreen", "forest"),
    ("tree", "wheat.svg", "ph", "grains", "wheat"),
    ("tree", "leaf.svg", "ph", "leaf", "leaf"),
    ("tree", "oasis.svg", "mdi", "palm-tree", "oasis"),
]


def make_fallback_svg(name, symbol):
    """Generates a clean semantic vector SVG (no dashed boxes, no '+' crosshairs, no English text)."""
    sym = (symbol or name).lower().replace(".svg", "")
    if any(k in sym for k in ("coin", "gold", "money", "treasure")):
        body = '<circle cx="24" cy="24" r="17" stroke="currentColor" stroke-width="3"/><circle cx="24" cy="24" r="11" stroke="currentColor" stroke-width="2"/><path d="M24 16v16M20 20h6a2.5 2.5 0 0 1 0 5h-4a2.5 2.5 0 0 0 0 5h6" stroke="currentColor" stroke-width="2.5"/>'
    elif any(k in sym for k in ("crown", "royal", "throne")):
        body = '<path d="M6 36h36M8 31l-2-15 10 7 8-11 8 11 10-7-2 15H8z" stroke="currentColor" stroke-width="3" fill="currentColor" fill-opacity="0.2"/>'
    elif any(k in sym for k in ("column", "pillar", "arch", "obelisk")):
        body = '<path d="M8 10h32M10 14h28M14 14v22M24 14v22M34 14v22M10 36h28M6 40h36" stroke="currentColor" stroke-width="3"/>'
    elif any(k in sym for k in ("book", "document", "scroll", "constitution", "feather")):
        body = '<path d="M10 8h22a6 6 0 0 1 6 6v26H14a4 4 0 0 1-4-4V8z" stroke="currentColor" stroke-width="3"/><path d="M16 16h14M16 23h14M16 30h10" stroke="currentColor" stroke-width="2.5"/>'
    elif any(k in sym for k in ("sword", "bow", "cannon", "helmet", "shield")):
        body = '<path d="M38 10L18 30M13 25l10 10M10 38l6-6M32 10h6v6" stroke="currentColor" stroke-width="3"/><path d="M10 10l28 28" stroke="currentColor" stroke-width="2.5" opacity="0.7"/>'
    elif any(k in sym for k in ("ship", "sail", "anchor", "wave")):
        body = '<path d="M24 8v22M14 18h20M10 30l6 8h16l6-8H10zM6 42c4-3 8-3 12 0s8 3 12 0 8-3 12 0" stroke="currentColor" stroke-width="3"/>'
    elif any(k in sym for k in ("tree", "palm", "forest", "leaf", "wheat", "oasis")):
        body = '<path d="M24 10c-8 4-12 12-8 20 4 4 12 4 16 0 4-8 0-16-8-20zM24 22v18M18 34l6-4 6 4" stroke="currentColor" stroke-width="3" fill="currentColor" fill-opacity="0.2"/>'
    elif any(k in sym for k in ("clock", "sand", "stopwatch", "timeline", "time")):
        body = '<circle cx="24" cy="24" r="17" stroke="currentColor" stroke-width="3"/><path d="M24 14v10l7 5" stroke="currentColor" stroke-width="3"/>'
    elif any(k in sym for k in ("world", "globe", "nation", "africa")):
        body = '<circle cx="24" cy="24" r="17" stroke="currentColor" stroke-width="3"/><ellipse cx="24" cy="24" rx="8" ry="17" stroke="currentColor" stroke-width="2.5"/><path d="M7 24h34M10 16h28M10 32h28" stroke="currentColor" stroke-width="2"/>'
    else:
        body = '<circle cx="24" cy="24" r="16" stroke="currentColor" stroke-width="3"/><path d="M24 12l3.5 8 8.5 1-6.2 5.8 1.7 8.2L24 30.8 16.5 35l1.7-8.2L12 21l8.5-1L24 12z" stroke="currentColor" stroke-width="2.2" fill="currentColor" fill-opacity="0.25"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'''


def fetch_all():
    os.makedirs(DEST_DIR, exist_ok=True)
    count = 0
    categories = set()
    session = requests.Session()
    session.headers.update({"User-Agent": "ShortsStudio-AssetFetcher/1.0"})

    for cat, filename, prefix, icon_name, symbol in ICONS_SPEC:
        cat_dir = DEST_DIR / cat
        os.makedirs(cat_dir, exist_ok=True)
        categories.add(cat)
        file_path = cat_dir / filename

        if file_path.exists() and file_path.stat().st_size > 50:
            existing_txt = file_path.read_text(encoding="utf-8", errors="ignore")
            if 'stroke-dasharray="3 3"' not in existing_txt:
                count += 1
                continue

        # Try fetching from Iconify
        url = f"https://api.iconify.design/{prefix}/{icon_name}.svg"
        fetched = False
        try:
            r = session.get(url, timeout=4)
            if r.status_code == 200 and len(r.text) > 40 and "<svg" in r.text:
                file_path.write_text(r.text, encoding="utf-8")
                fetched = True
                count += 1
        except Exception:
            pass

        if not fetched:
            # Write fallback SVG
            svg = make_fallback_svg(filename, symbol)
            file_path.write_text(svg, encoding="utf-8")
            count += 1

    print(f"✓ Total icons bundled: {count} across {len(categories)} categories in {DEST_DIR}")
    return count, categories


if __name__ == "__main__":
    fetch_all()
