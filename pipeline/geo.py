"""حدود الدول (GeoJSON) وحساب إطار العرض."""
import json
import math
import threading

from .config import GEO

_lock = threading.Lock()
_geo = None


class Geo:
    def __init__(self, path):
        d = json.load(open(path, encoding="utf-8"))
        self.c = {}
        for f in d["features"]:
            p = f["properties"]
            iso = p.get("ISO3166-1-Alpha-3") or p.get("ISO_A3") or ""
            if len(iso) != 3 or not iso.isalpha():
                continue
            g = f["geometry"]
            polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            bbs = []
            for poly in polys:
                xs = [pt[0] for pt in poly[0]]
                ys = [pt[1] for pt in poly[0]]
                bbs.append((min(xs), min(ys), max(xs), max(ys)))
            self.c[iso] = {"name": p.get("name", iso), "polys": polys, "bbs": bbs}

    def has(self, iso):
        return iso in self.c

    def main_bbox(self, iso):
        bbs = self.c[iso]["bbs"]
        return max(bbs, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))

    def view_for(self, isos, points, bw=1000, bh=860, smax=420, pad=0.1):
        boxes = [self.main_bbox(i) for i in isos if i in self.c]
        boxes += [(p["lon"], p["lat"], p["lon"], p["lat"]) for p in points]
        if not boxes:
            boxes = [(-25, -35, 60, 38)]
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes)
        y1 = max(b[3] for b in boxes)
        dx, dy = max(x1 - x0, 1.5), max(y1 - y0, 1.5)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        x0, x1 = cx - dx / 2 * (1 + 2 * pad), cx + dx / 2 * (1 + 2 * pad)
        y0, y1 = cy - dy / 2 * (1 + 2 * pad), cy + dy / 2 * (1 + 2 * pad)
        k = math.cos(math.radians(cy))
        s = min(bw / ((x1 - x0) * k), bh / (y1 - y0), smax)
        return {"lonc": cx, "latc": cy, "K": k, "S": s}


def get_geo():
    global _geo
    with _lock:
        if _geo is None:
            _geo = Geo(GEO)
        return _geo
