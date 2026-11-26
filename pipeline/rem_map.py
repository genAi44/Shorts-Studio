"""Split from `pipeline/rem.py` (re-exported there); see that module."""
import numpy as np


# ------------------------------------------------------------------ خريطة -> مسارات SVG
def _d(xy, min_d=2.0):
    out, last = [], None
    for x, y in xy:
        if last is None or (x - last[0]) ** 2 + (y - last[1]) ** 2 >= min_d ** 2:
            out.append((x, y))
            last = (x, y)
    if len(out) < 3:
        return ""
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in out) + "Z"


_MAP_VIEW_CACHE: dict = {}


def map_view(geo, beat):
    hl = [c for c in (beat.get("highlight") or beat.get("countries") or []) if geo.has(c)]
    extra = [c for c in (beat.get("countries") or []) if geo.has(c)]
    pts = [p for p in (beat.get("points") or []) if "lat" in p and "lon" in p]
    cache_key = (
        tuple(hl),
        tuple(extra),
        tuple((round(float(p["lat"]), 3), round(float(p["lon"]), 3), str(p.get("name") or ""), bool(p.get("dot"))) for p in pts),
    )
    if cache_key in _MAP_VIEW_CACHE:
        import copy as _copy
        return _copy.deepcopy(_MAP_VIEW_CACHE[cache_key])
    v = geo.view_for(list(dict.fromkeys(extra + hl)), pts)
    S, K, lonc, latc = v["S"], v["K"], v["lonc"], v["latc"]
    CY = 870

    # حماية الدبابيس من التصادم مع شريط العنوان (HEADLINE_ZONE ينتهي عند 440px)
    if pts:
        min_proj_y = min(CY - (float(p["lat"]) - latc) * S for p in pts)
        if min_proj_y < 540:
            shift_y = 540 - min_proj_y
            CY = min(CY + shift_y, 1000)

    def proj(a):
        a = np.asarray(a, np.float64)
        return np.stack([540 + (a[:, 0] - lonc) * S * K, CY - (a[:, 1] - latc) * S], 1)

    hw, hh = 700 / (S * K), 1500 / S
    win = (lonc - hw, latc - hh, lonc + hw, latc + hh)

    def sect(b):
        return not (b[2] < win[0] or b[0] > win[2] or b[3] < win[1] or b[1] > win[3])

    def country_d(iso):
        c = geo.c[iso]
        parts = []
        for poly, bb in zip(c["polys"], c["bbs"]):
            if not sect(bb):
                continue
            if (bb[2] - bb[0]) * S * K < 3 and (bb[3] - bb[1]) * S < 3:
                continue
            for ring in poly:
                parts.append(_d(proj(ring)))
        return "".join(p for p in parts if p)

    ctx = "".join(country_d(iso) for iso in geo.c if iso not in hl)
    hls = []
    SMALL_PX = 60  # عتبة البكسل للكيانات الصغيرة (تشغّل عدسة التكبير)
    for iso in hl:
        bb = geo.main_bbox(iso)
        (x0, y0), (x1, y1) = proj([[bb[0], bb[1]], [bb[2], bb[3]]])
        cx, cy = round((x0 + x1) / 2, 1), round((y0 + y1) / 2, 1)
        bw, bh = abs(x1 - x0), abs(y1 - y0)
        is_small = bool(bw < SMALL_PX or bh < SMALL_PX)
        entry = {"iso": iso, "d": country_d(iso), "cx": cx, "cy": cy, "small": is_small}
        if is_small:
            entry["vz"] = round(max(max(bw, bh) * 4, 20), 1)
        hls.append(entry)

    neighbours = []
    for iso in geo.c:
        if iso not in hl and sect(geo.main_bbox(iso)):
            d = country_d(iso)
            if d:
                cbb = geo.main_bbox(iso)
                (nx0, ny0), (nx1, ny1) = proj([[cbb[0], cbb[1]], [cbb[2], cbb[3]]])
                neighbours.append({"iso": iso, "d": d, "cx": round((nx0 + nx1) / 2, 1), "cy": round((ny0 + ny1) / 2, 1), "name": geo.c[iso].get("name", iso)})

    placed, ptsv = [], []
    for p in pts:
        x, y = proj([[float(p["lon"]), float(p["lat"])]])[0]
        side = -1
        for _ in range(2):
            ly = y + side * 85
            if all(abs(ly - q[1]) > 75 or abs(x - q[0]) > 340 for q in placed):
                break
            side = 1
        ly = y + side * 85
        placed.append((x, ly))
        ptsv.append({"name": p.get("name", ""), "x": round(x, 1), "y": round(y, 1), "ly": round(ly, 1), "dot": p.get("dot", True)})

    target = None
    if ptsv:
        target = {"x": ptsv[0]["x"], "y": ptsv[0]["y"]}
    elif hls:
        target = {"x": hls[0]["cx"], "y": hls[0]["cy"]}

    res_view = {"ctx": ctx, "hl": hls, "pts": ptsv, "target": target, "neighbours": neighbours[:12]}
    _MAP_VIEW_CACHE[cache_key] = res_view
    return res_view


# ------------------------------------------------------------------ نقاط الإشارة (Cue-Point Orchestrator)
def _make_cues(kind: str, fps: int, visual_mode: str = "") -> list:
    """Generate cascading reveal cues (frame offsets from beat start).
    Components read beat.cues[type] to stagger their entrances.
    Now includes cinematographic cues for dynamic background lighting."""
    f = fps
    cues = [
        {"frame": 0,              "type": "bg_enter"},
        {"frame": round(0.15 * f), "type": "lighting_ambient"},
        {"frame": round(0.2 * f), "type": "badge_slide"},
        {"frame": round(0.6 * f), "type": "secondary_enter"},
    ]
    # Cinematographic lighting cues based on visual mode
    if visual_mode in ("historical_photo", "modern_photo"):
        cues.append({"frame": round(0.3 * f), "type": "photo_reveal"})
        cues.append({"frame": round(0.7 * f), "type": "photo_focus"})
    elif visual_mode in ("battle_map", "map_zoom"):
        cues.append({"frame": round(0.25 * f), "type": "map_overlay"})
        cues.append({"frame": round(0.5 * f), "type": "battle_intensity"})
    elif visual_mode in ("comparison_chart", "split_diagram"):
        cues.append({"frame": round(0.35 * f), "type": "split_reveal"})
        cues.append({"frame": round(0.6 * f), "type": "comparison_flash"})
    elif visual_mode == "timeline":
        cues.append({"frame": round(0.25 * f), "type": "time_rise"})
        cues.append({"frame": round(0.55 * f), "type": "era_flash"})
    elif visual_mode == "stat_infographic":
        cues.append({"frame": round(0.4 * f), "type": "metric_start"})
        cues.append({"frame": round(0.8 * f), "type": "metric_punch"})
    elif visual_mode in ("cinematic_dramatic", "architectural_blueprint", "celestial_constellation", "kinetic_wave_field", "radial_light_cathedral", "topographic_contour"):
        cues.append({"frame": round(0.25 * f), "type": "cinematic_enter"})
        cues.append({"frame": round(0.45 * f), "type": "lighting_key_fill"})
        cues.append({"frame": round(0.75 * f), "type": "cinematic_release"})
    if kind in ("stat", "stat_ring_v2", "bars", "bigtext"):
        cues.append({"frame": round(0.4 * f), "type": "metric_start"})
        cues.append({"frame": round(0.8 * f), "type": "metric_punch"})
    if kind in ("map", "map_pin"):
        cues.append({"frame": round(0.15 * f), "type": "zoom_city"})
        cues.append({"frame": round(0.45 * f), "type": "pin_drop"})
        cues.append({"frame": round(0.70 * f), "type": "ripple"})
    if kind in ("canvas", "icons"):
        cues.append({"frame": round(0.4 * f),  "type": "icon_drop"})
        cues.append({"frame": round(0.65 * f), "type": "arrow_draw"})
    if kind == "elevation_profile":
        cues.append({"frame": round(0.3 * f), "type": "sea_line"})
        cues.append({"frame": round(0.5 * f), "type": "metric_start"})
        cues.append({"frame": round(0.85 * f), "type": "metric_punch"})
    if kind == "line_chart":
        cues.append({"frame": round(0.25 * f), "type": "grid_enter"})
        cues.append({"frame": round(0.4 * f), "type": "line_draw"})
        cues.append({"frame": round(0.75 * f), "type": "dots_pop"})
    if kind == "pie_chart":
        cues.append({"frame": round(0.2 * f), "type": "seg_enter"})
        cues.append({"frame": round(0.65 * f), "type": "labels_enter"})
    return cues
