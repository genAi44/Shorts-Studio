"""Generate and bundle simplified public-domain SVG maps for regions and countries.
Stored in remotion/public/maps/{name}.svg.
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
MAPS_DIR = ROOT / "remotion" / "public" / "maps"
MAPS_DIR.mkdir(parents=True, exist_ok=True)

# High-quality simplified SVG paths normalized to 800x800 or 1000x1000 viewBox
# Coordinates and silhouettes of regions based on public domain Natural Earth / Carto boundaries.
MAPS_DATA = {
    "egypt": {
        "viewBox": "0 0 800 800",
        "path": "M 150 120 L 700 120 L 680 180 L 650 210 L 660 300 L 630 380 L 720 480 L 680 620 L 620 700 L 150 700 L 150 120 Z",
        "river": "M 480 700 Q 470 550 460 420 Q 450 320 440 240 Q 435 200 450 180 Q 430 140 400 125 M 450 180 Q 480 150 510 130",
        "cities": [
            {"name": "القاهرة", "name_en": "cairo", "x": 445, "y": 235},
            {"name": "الإسكندرية", "name_en": "alexandria", "x": 395, "y": 140},
            {"name": "الأقصر", "name_en": "luxor", "x": 490, "y": 510},
            {"name": "أسوان", "name_en": "aswan", "x": 495, "y": 620},
            {"name": "الفسطاط", "name_en": "fustat", "x": 447, "y": 242},
            {"name": "منف", "name_en": "memphis", "x": 442, "y": 260},
        ],
    },
    "world": {
        "viewBox": "0 0 1000 600",
        "path": "M 120 180 Q 180 140 260 170 Q 280 240 240 320 L 260 480 L 210 520 L 170 380 L 110 260 Z "
                "M 450 140 Q 520 120 580 160 L 590 260 L 530 320 L 550 490 L 480 520 L 440 340 L 420 220 Z "
                "M 620 120 Q 780 110 880 180 Q 860 320 780 380 L 720 340 L 660 360 L 600 240 Z "
                "M 740 420 Q 840 410 860 480 L 820 540 L 730 500 Z",
        "cities": [
            {"name": "الشرق الأوسط", "name_en": "middle_east", "x": 560, "y": 270},
            {"name": "أوروبا", "name_en": "europe", "x": 490, "y": 180},
            {"name": "آسيا", "name_en": "asia", "x": 730, "y": 220},
            {"name": "أمريكا", "name_en": "americas", "x": 220, "y": 300},
        ],
    },
    "middle_east": {
        "viewBox": "0 0 800 800",
        "path": "M 200 250 Q 320 180 460 210 Q 580 240 680 320 L 640 480 L 560 620 Q 420 680 340 580 L 280 440 L 180 360 Z",
        "cities": [
            {"name": "الرياض", "name_en": "riyadh", "x": 480, "y": 450},
            {"name": "مكة", "name_en": "mecca", "x": 360, "y": 480},
            {"name": "المدينة", "name_en": "medina", "x": 370, "y": 420},
            {"name": "بغداد", "name_en": "baghdad", "x": 450, "y": 270},
            {"name": "دمشق", "name_en": "damascus", "x": 370, "y": 280},
            {"name": "القاهرة", "name_en": "cairo", "x": 260, "y": 340},
            {"name": "دبي", "name_en": "dubai", "x": 600, "y": 430},
        ],
    },
    "saudi_arabia": {
        "viewBox": "0 0 800 800",
        "path": "M 220 220 L 480 200 L 580 280 L 680 380 L 620 540 L 520 640 L 380 620 L 260 520 L 200 360 Z",
        "cities": [
            {"name": "الرياض", "name_en": "riyadh", "x": 460, "y": 400},
            {"name": "جدة", "name_en": "jeddah", "x": 270, "y": 460},
            {"name": "مكة", "name_en": "mecca", "x": 290, "y": 480},
            {"name": "المدينة", "name_en": "medina", "x": 300, "y": 380},
            {"name": "الدمام", "name_en": "dammam", "x": 560, "y": 360},
        ],
    },
    "bolivia": {
        "viewBox": "0 0 800 800",
        "path": "M 320 180 L 520 220 L 600 380 L 540 580 L 420 660 L 280 580 L 240 420 L 260 280 Z",
        "cities": [
            {"name": "لاباز", "name_en": "la_paz", "x": 340, "y": 360},
            {"name": "سوكري", "name_en": "sucre", "x": 420, "y": 480},
            {"name": "سانتا كروز", "name_en": "santa_cruz", "x": 480, "y": 430},
            {"name": "أويوني", "name_en": "uyuni", "x": 360, "y": 540},
        ],
    },
}

def generate_svg(region_id: str, data: dict) -> str:
    viewBox = data["viewBox"]
    path_d = data["path"]
    river = data.get("river", "")
    
    river_tag = f'<path d="{river}" fill="none" stroke="#38bdf8" stroke-width="6" stroke-linecap="round" opacity="0.8" />' if river else ""
    
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewBox}" fill="none" data-region="{region_id}">
  <defs>
    <linearGradient id="mapGrad_{region_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2a3342" stop-opacity="0.9" />
      <stop offset="50%" stop-color="#18202c" stop-opacity="0.85" />
      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.95" />
    </linearGradient>
    <filter id="mapGlow_{region_id}" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="12" flood-color="#D4AF37" flood-opacity="0.25"/>
    </filter>
  </defs>
  <!-- Background border subtle glow -->
  <path d="{path_d}" fill="url(#mapGrad_{region_id})" stroke="#D4AF37" stroke-width="3" stroke-opacity="0.6" filter="url(#mapGlow_{region_id})"/>
  {river_tag}
</svg>"""

def main():
    import json
    index = {}
    for region_id, data in MAPS_DATA.items():
        svg_content = generate_svg(region_id, data)
        out_file = MAPS_DIR / f"{region_id}.svg"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(svg_content)
        index[region_id] = {
            "file": f"maps/{region_id}.svg",
            "viewBox": data["viewBox"],
            "cities": data["cities"],
        }
    
    with open(MAPS_DIR / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"Bundled {len(MAPS_DATA)} region maps into {MAPS_DIR}")

if __name__ == "__main__":
    main()

