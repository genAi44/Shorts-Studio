"""Split from `pipeline/areamap.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict
import math
import numpy as np
from .areamap import BOX, LAYOUTS, pick_mode, registry  # noqa: E402


# ------------------------------------------------------------------ view (all outlines projected to the 1080x1920 canvas)
def _d(xy, min_d: float = 2.0) -> str:
    out, last = [], None
    for x, y in xy:
        if last is None or (x - last[0]) ** 2 + (y - last[1]) ** 2 >= min_d ** 2:
            out.append((x, y))
            last = (x, y)
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in out) + "Z" if len(out) >= 3 else ""


def _paths(polys, proj, min_d=2.0, skip_px=0.0) -> str:
    parts = []
    for poly in polys:
        for ring in poly:
            xy = proj(np.asarray(ring, float))
            if skip_px and np.ptp(xy[:, 0]) < skip_px and np.ptp(xy[:, 1]) < skip_px:
                continue
            parts.append(_d(xy, min_d))
    return "".join(p for p in parts if p)


def _bbox(polys):
    xs = [p[0] for poly in polys for r in poly for p in r]
    ys = [p[1] for poly in polys for r in poly for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def _main(p: dict):
    """Polygons of a place without far-flung overseas parts (uses the project's mainland bbox for countries)."""
    if p["type"] != "country":
        return p["polys"]
    from .geo import get_geo
    bb = get_geo().main_bbox(p["id"])
    keep = []
    for poly in p["polys"]:
        b = _bbox([poly])
        if bb[0] - 1 <= (b[0] + b[2]) / 2 <= bb[2] + 1 and bb[1] - 1 <= (b[1] + b[3]) / 2 <= bb[3] + 1:
            keep.append(poly)
    return keep or p["polys"]


def _equi(lonc, latc, s, cx, cy):
    k = math.cos(math.radians(latc))
    return lambda a: np.stack([cx + (a[:, 0] - lonc) * k * s, cy - (a[:, 1] - latc) * s], 1)


def _fit(bb, bw, bh, pad=0.12, smax=420.0):
    dx, dy = max(bb[2] - bb[0], 0.4), max(bb[3] - bb[1], 0.4)
    lonc, latc = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    k = math.cos(math.radians(latc))
    return lonc, latc, min(bw / (dx * (1 + 2 * pad) * k), bh / (dy * (1 + 2 * pad)), smax)


def _ctx(proj, exclude, win) -> str:
    """Neighbouring countries inside the window (x0,y0,x1,y1 in lon/lat) as one path."""
    from .geo import get_geo
    g = get_geo()
    parts = []
    for iso, c in g.c.items():
        if iso == exclude:
            continue
        keep = [poly for poly, bb in zip(c["polys"], c["bbs"]) if not (bb[2] < win[0] or bb[0] > win[2] or bb[3] < win[1] or bb[1] > win[3])]
        if keep:
            parts.append(_paths(keep, proj, 2.0, 3.0))
    return "".join(parts)


def _orth(lon0, lat0, R, cx, cy):
    l0, f0 = math.radians(lon0), math.radians(lat0)

    def proj(a):
        lam, phi = np.radians(a[:, 0]) - l0, np.radians(a[:, 1])
        x = np.cos(phi) * np.sin(lam)
        y = math.cos(f0) * np.sin(phi) - math.sin(f0) * np.cos(phi) * np.cos(lam)
        vis = math.sin(f0) * np.sin(phi) + math.cos(f0) * np.cos(phi) * np.cos(lam) >= 0
        n = np.maximum(np.hypot(x, y), 1e-9)
        x, y = np.where(vis, x, x / n), np.where(vis, y, y / n)  # behind-horizon points ride the rim
        return np.stack([cx + R * x, cy - R * y], 1)
    return proj


def _centroid(d_polys, proj):
    xy = np.concatenate([proj(np.asarray(r, float)) for poly in d_polys for r in poly[:1]])
    return round(float(xy[:, 0].mean()), 1), round(float(xy[:, 1].mean()), 1)


def build_view(beat: dict) -> dict:
    """Projected geometry for the Remotion `area_map` component (all coordinates in canvas px)."""
    c = beat["area"]
    reg = registry()["places"]
    p = reg.get(c.get("res_id") or "")
    layout = beat.get("layout") if beat.get("layout") in LAYOUTS else LAYOUTS[0]
    cy, bh = BOX[layout]
    bw = 920
    view: Dict[str, Any] = {"layout": layout, "mode": "disc", "box": {"cx": 540, "cy": cy, "w": bw, "h": bh},
                            "ctx": "", "hl": [], "marker": None, "inset": None, "link": None, "globe": None,
                            "synthetic": True, "ratio": None, "under": False}
    if not p:  # unresolved place: a plain disc stands in for the footprint, tagged as approximate
        r = min(bh, bw) * 0.34
        pr = _equi(0, 0, 1, 540, cy)
        ring = np.array([[540 + r * math.cos(t), cy + r * math.sin(t)] for t in np.linspace(0, 2 * math.pi, 64, endpoint=False)])
        view["hl"] = [{"d": _d(ring), "cx": 540, "cy": cy, "role": "main", "label": c["place"] or c["place_en"], "tiny": False}]
        return view
    mode = pick_mode(c)
    view["mode"], view["synthetic"] = mode, bool(p["synthetic"])
    view["under"] = p["type"] in ("ocean", "sea")  # water is drawn beneath the land
    mp = _main(p)

    if mode == "globe":
        R = min(bh / 2, 430.0)
        pj = _orth(p["lon"], p["lat"], R, 540, cy)
        from .geo import get_geo
        view["ctx"] = "".join(_paths(c_["polys"], pj, 3.0, 3.0) for c_ in get_geo().c.values())
        view["hl"] = [{"d": _paths(p["polys"], pj, 2.6), "cx": 540, "cy": cy, "role": "main", "label": c["place"] or c["place_en"], "tiny": False}]
        view["globe"] = {"cx": 540, "cy": cy, "r": R}
    elif mode == "compare":
        q = reg[c["compare"]["res_id"]]
        view["ratio"] = c["compare"]["ratio"]
        shapes = []
        for pl, name, role in ((p, c["place"] or c["place_en"], "main"), (q, c["compare"]["place"] or c["compare"]["place_en"], "other")):
            polys = _main(pl)
            bb = _bbox(polys)
            lat0, lon0 = (bb[1] + bb[3]) / 2, (bb[0] + bb[2]) / 2
            kx, ky = 111.32 * math.cos(math.radians(lat0)), 110.574
            shapes.append({"polys": polys, "lon0": lon0, "lat0": lat0, "kx": kx, "ky": ky, "w": (bb[2] - bb[0]) * kx, "h": (bb[3] - bb[1]) * ky,
                           "name": name, "role": role})
        A, B = shapes
        side = layout != "overlay"
        gap = 40
        H = bh - 190
        s = min((bw - gap) / (A["w"] + B["w"]), H / max(A["h"], B["h"])) if side else min(bw / max(A["w"], B["w"]), H / max(A["h"], B["h"]))
        x0 = 540 - ((A["w"] + B["w"]) * s + gap) / 2
        for sh in (B, A):  # RTL reading order: reference (B) on the left, subject (A) on the right
            w = sh["w"] * s
            ccx = (x0 + w / 2) if side else 540
            if side:
                x0 += w + gap
            ccy = cy + 35

            def pj(a, sh=sh, ccx=ccx, ccy=ccy):
                return np.stack([ccx + (a[:, 0] - sh["lon0"]) * sh["kx"] * s, ccy - (a[:, 1] - sh["lat0"]) * sh["ky"] * s], 1)
            tiny = max(sh["w"], sh["h"]) * s < 16
            view["hl"].append({"d": _paths(sh["polys"], pj, 1.2), "cx": round(ccx, 1), "cy": round(ccy, 1), "role": sh["role"],
                               "label": sh["name"], "tiny": tiny, "lx": round(ccx, 1), "ly": round(ccy + sh["h"] * s / 2 + 52, 1)})
        view["synthetic"] = bool(p["synthetic"] or q["synthetic"])
    elif mode == "magnifier":
        iso = p["iso3"] if p["type"] == "city" else ""
        from .geo import get_geo
        g = get_geo()
        bb = g.main_bbox(iso) if iso in g.c else (p["lon"] - 3.5, p["lat"] - 3.5, p["lon"] + 3.5, p["lat"] + 3.5)
        lonc, latc, s = _fit(bb, bw, bh * 0.9)
        pj = _equi(lonc, latc, s, 540, cy)
        view["ctx"] = _ctx(pj, p["id"], (lonc - 0.5 * bw / (s * math.cos(math.radians(latc))), latc - 0.5 * bh / s,
                                          lonc + 0.5 * bw / (s * math.cos(math.radians(latc))), latc + 0.5 * bh / s))
        mx, my = pj(np.array([[p["lon"], p["lat"]]]))[0]
        mx, my = float(mx), float(my)
        view["marker"] = {"x": round(mx, 1), "y": round(my, 1)}
        view["hl"] = [{"d": _paths(mp, pj, 0.5), "cx": round(mx, 1), "cy": round(my, 1), "role": "main", "label": c["place"] or c["place_en"], "tiny": True}]
        r = 205.0
        cands = [(540 + sx * (bw / 2 - r - 10), cy + sy * (bh / 2 - r - 10)) for sx in (-1, 1) for sy in (-1, 1)]
        icx, icy = max(cands, key=lambda q_: (q_[0] - mx) ** 2 + (q_[1] - my) ** 2)
        fb = _bbox(mp)
        fs = (r * 1.45) / max((fb[2] - fb[0]) * math.cos(math.radians(p["lat"])), fb[3] - fb[1], 1e-6)
        fj = _equi((fb[0] + fb[2]) / 2, (fb[1] + fb[3]) / 2, fs, icx, icy)
        view["inset"] = {"cx": round(icx, 1), "cy": round(icy, 1), "r": r, "d": _paths(mp, fj, 0.8)}
        view["link"] = [round(mx, 1), round(my, 1), round(icx, 1), round(icy, 1)]
    else:  # country-sized outline (also seas / lakes / islands)
        bb = _bbox(mp)
        lonc, latc, s = _fit(bb, bw, bh, smax=300.0)
        pj = _equi(lonc, latc, s, 540, cy)
        k = math.cos(math.radians(latc))
        view["ctx"] = _ctx(pj, p["id"], (lonc - 0.5 * bw / (s * k), latc - 0.5 * bh / s, lonc + 0.5 * bw / (s * k), latc + 0.5 * bh / s))
        hx, hy = _centroid(mp[:1], pj)
        view["hl"] = [{"d": _paths(mp, pj, 1.0), "cx": hx, "cy": hy, "role": "main", "label": c["place"] or c["place_en"], "tiny": False}]
    return view
