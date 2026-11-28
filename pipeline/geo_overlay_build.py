"""Split from `pipeline/geo_overlay.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from .config import FPS
from .geo import get_geo
import json
import math
import numpy as np
from .geo_overlay import _d_svg, _find_word_timestamp, _format_gps, extract_timed_geo_mentions  # noqa: E402


MAP_FILL = 0.80  # share of the view the main subject fills. 0.86 was tried: it zoomed Russia to 1.27 and the camera, centred on the pin, cut its east off


def _fills_width(geo: Any, iso: Any, S: float, K: float) -> bool:
    """True when the country already spans (almost) the whole view width: any extra zoom would crop its far edge
    (Russia's east, USA's Alaska), so such a country is shown at zoom 1."""
    if not iso or not geo.has(iso):
        return False
    bb = geo.main_bbox(iso)
    return (bb[2] - bb[0]) * S * K >= 0.9 * 688.0


def _fit_zoom(geo: Any, iso: Any, S: float, K: float) -> Optional[float]:
    """Zoom (1..4) at which the country's main bbox fills ~MAP_FILL of the 688x412 view; None if unknown."""
    if not iso or not geo.has(iso):
        return None
    bb = geo.main_bbox(iso)
    w_px = max((bb[2] - bb[0]) * S * K, 1.0)
    h_px = max((bb[3] - bb[1]) * S, 1.0)
    return max(1.0, min(4.0, MAP_FILL * min(688.0 / w_px, 412.0 / h_px)))


_SCALE_LABEL = {"village": "قرية", "town": "بلدة", "city": "مدينة", "capital": "عاصمة", "region": "منطقة", "country": "دولة",
                "continent": "قارة", "ocean": "محيط", "globe": "الكرة الأرضية", "district": "حي", "landmark": "معلم"}


_TERRAIN_LABEL = {"river": "نهر", "mountain": "جبل", "desert": "صحراء", "lake": "بحيرة", "strait": "مضيق", "island": "جزيرة"}


def _geojson_extent(gj: str) -> List[Tuple[float, float]]:
    try:
        geom = json.loads(gj)
        pts: List[Tuple[float, float]] = []

        def walk(c: Any) -> None:
            if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
                pts.append((float(c[1]), float(c[0])))
            elif isinstance(c, (list, tuple)):
                for x in c:
                    walk(x)

        walk(geom.get("coordinates"))
        if not pts:
            return []
        lats, lons = [p[0] for p in pts], [p[1] for p in pts]
        return [(min(lats), min(lons)), (max(lats), max(lons))]
    except Exception:
        return []


def mention_from_entity(e: Dict[str, Any], words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validated entity (pipeline/entities.py) -> overlay mention dicts, timed on the spoken word. One entity can
    yield several mentions (a route has one per stop, a conflict has two sides)."""
    scene_dur = max([float(w.get("e", 0.0)) for w in words] + [3.0])

    def mk(kind: str, label: str, name_ar: str, name_en: str, lat: float, lon: float, token: str, nth: int = 0, **extra: Any) -> Dict[str, Any]:
        s, en, wi = _find_word_timestamp(token, words, scene_dur, fallback_ratio=0.15)
        s += 0.55 * nth
        m = {"matched_token": token, "kind": kind, "kind_label": label, "name_ar": name_ar, "name_en": name_en,
             "country_ar": extra.pop("country_ar", "") or "", "iso3": (extra.pop("iso3", "") or "").upper(),
             "iso2": (extra.pop("iso2", "") or "").lower(), "lat": float(lat), "lon": float(lon), "coords": _format_gps(float(lat), float(lon)),
             "is_microstate": False, "start_sec": round(s, 3), "end_sec": round(en + 0.55 * nth, 3), "word_index": wi, "char_pos": wi}
        m.update(extra)
        return m

    t = e.get("type")
    token = str(e.get("text") or e.get("name_ar") or "")
    if t == "place":
        sc = e.get("scale") or "city"
        label = _SCALE_LABEL.get(sc, "مدينة")
        common = dict(country_ar=e.get("country_ar"), iso3=e.get("iso3"), iso2=e.get("iso2"), scale=sc)
        if sc in ("village", "town", "city", "district", "landmark"):
            return [mk("city", label, e["name_ar"], e["name_en"], e["lat"], e["lon"], token, **common)]
        if sc == "capital":
            return [mk("capital", label, e["name_ar"], e["name_en"], e["lat"], e["lon"], token, **common)]
        if sc == "country":
            return [mk("country", label, e["name_ar"], e["name_en"], e["lat"], e["lon"], token, country_ar=e["name_ar"], iso3=e.get("iso3"), iso2=e.get("iso2"), scale=sc)]
        if sc == "continent":
            m = mk("continent", label, e["name_ar"], e["name_en"], e["lat"], e["lon"], token, iso3=e.get("iso3"), scale=sc)
            m["continent_isos"] = list(e.get("continent_isos") or [])
            return [m]
        hh, hw = float(e.get("half_h", 12.0)), float(e.get("half_w", 18.0))
        if sc == "globe":
            return [mk("globe", label, e["name_ar"] or "الكرة الأرضية", e["name_en"] or "Earth", 15.0, 10.0, token, scale=sc,
                       extent=[(-58.0, -175.0), (72.0, 175.0)], feature={"shape": "area", "half_h": 0.0, "half_w": 0.0})]
        if sc == "ocean":
            return [mk("ocean", label, e["name_ar"], e["name_en"], e["lat"], e["lon"], token, scale=sc,
                       extent=[(e["lat"] - hh, e["lon"] - hw), (e["lat"] + hh, e["lon"] + hw)],
                       feature={"shape": "area", "half_h": hh, "half_w": hw})]
        # region (administrative area without a polygon in the data): marked area around the point
        return [mk("region", label, e["name_ar"], e["name_en"], e["lat"], e["lon"], token, scale=sc, iso3=e.get("iso3"), iso2=e.get("iso2"),
                   extent=[(e["lat"] - 1.6, e["lon"] - 2.0), (e["lat"] + 1.6, e["lon"] + 2.0)], feature={"shape": "area", "half_h": 1.6, "half_w": 2.0})]
    if t == "terrain":
        sc = e.get("scale") or "river"
        label = _TERRAIN_LABEL.get(sc, "معلم")
        ext = _geojson_extent(e["geojson"]) if e.get("geojson") else []
        ext = ext or [(e["lat"] - 1.4, e["lon"] - 1.8), (e["lat"] + 1.4, e["lon"] + 1.8)]
        shape = sc if sc in ("river", "lake", "mountain") else "area"
        if e.get("line_id"):
            shape = "range"                       # a drawn line from data/geo_lines.json (range, boundary, equator ...)
        if shape in ("river", "lake") and not e.get("geojson"):
            shape = "area"
        ft: Dict[str, Any] = {"shape": shape, "geojson": e.get("geojson"), "approx": bool(e.get("approx")),
                              "half_h": (ext[1][0] - ext[0][0]) / 2.0, "half_w": (ext[1][1] - ext[0][1]) / 2.0}
        if e.get("line_id"):
            ft.update(line_id=e["line_id"], line_kind=e.get("line_kind"), divides=e.get("divides"))
        return [mk("terrain", label, e["name_ar"], e["name_en"], e["lat"], e["lon"], token, scale=sc, extent=ext, feature=ft)]
    if t == "route":
        out = []
        for i, s in enumerate(e["stops"]):
            out.append(mk("city", "محطة", str(s.get("name_ar") or f"{i + 1}"), str(s.get("name_en") or ""), s["lat"], s["lon"], token, nth=i, scale="town", route=True))
        return out
    if t == "conflict":
        out = []
        for i, side in enumerate((e["a"], e["b"])):
            lat, lon = float(side.get("lat", 0.0)), float(side.get("lon", 0.0))
            out.append(mk("city", "طرف", str(side.get("name_ar") or ""), "", lat, lon, token, nth=i, scale="city", arrow="attack"))
        return out
    if t == "empire":
        hh, hw = 7.0, 10.0
        return [mk("empire", "إمبراطورية", e["name_ar"], e.get("name_en") or "", float(e["lat"]), float(e["lon"]), token, scale="region",
                   extent=[(float(e["lat"]) - hh, float(e["lon"]) - hw), (float(e["lat"]) + hh, float(e["lon"]) + hw)],
                   feature={"shape": "area", "half_h": hh, "half_w": hw, "approx": True})]
    return []


def build_scene_map_overlay(
    sc: Dict[str, Any],
    words: List[Dict[str, Any]],
    dur_frames: int,
    geo: Any = None,
    scene_idx: int = 0,
    prev_overlay: Optional[Dict[str, Any]] = None,
    inherited_locations: Optional[List[Dict[str, Any]]] = None,
    entity_mentions: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Builds a complete, self-contained `map_overlay` specification for a Remotion Scene
    whenever countries, capitals, or cities are mentioned in the scene's narration.
    Falls back to `inherited_locations` from Visual Context Memory when the scene
    continues talking about the same place without repeating its name.
    Returns `None` if no geographic locations are mentioned or inherited.
    """
    role = str(sc.get("role") or "")
    narration = str(sc.get("narration") or sc.get("text") or "")
    on_screen = str(sc.get("on_screen") or sc.get("title") or "")

    # validated entity plan (pipeline/entities.py) wins; the legacy dictionary matcher only runs when there is none
    mentions = entity_mentions if entity_mentions is not None else extract_timed_geo_mentions(narration, on_screen, words, dur_frames)
    if not mentions and inherited_locations and role not in ("cta", "loop"):
        from .place_names import mentions_place
        # only a place THIS sentence names (its name or its adjective: "مدن أمريكية"), never every scene of the video
        inh_text = " ".join(str(loc.get("name_ar") or "") for loc in inherited_locations[:2]
                            if isinstance(loc, dict) and mentions_place(narration, str(loc.get("name_ar") or ""), str(loc.get("name_en") or "")))
        if inh_text.strip():
            mentions = extract_timed_geo_mentions(inh_text, "", words, dur_frames)
    if not mentions:
        return None

    # Render the overlay on every scene where a country, capital, or city is mentioned
    if role == "loop" and not any(m["kind"] in ("capital", "city", "country") for m in mentions):
        return None

    if geo is None:
        geo = get_geo()

    # Collect ISO3 codes and point coordinates for viewport projection (840x520 high-res local SVG box)
    W_BOX, H_BOX = 840.0, 520.0
    CX_BOX, CY_BOX = W_BOX / 2.0, H_BOX / 2.0

    # Map each ISO3 to its primary capital/city mention in this scene (if any)
    city_by_iso3: Dict[str, Dict[str, Any]] = {}
    distinct_cities: List[str] = []
    for m in mentions:
        if m.get("kind") in ("capital", "city"):
            iso_k = m.get("iso3") or ""
            if iso_k and iso_k not in city_by_iso3:
                city_by_iso3[iso_k] = m
            c_name = str(m.get("name_ar") or "")
            if c_name and c_name not in distinct_cities:
                distinct_cities.append(c_name)

    isos: List[str] = []
    pts_for_view: List[Dict[str, float]] = []
    for m in mentions:
        for c_iso in (m.get("continent_isos") or []):
            if c_iso and geo.has(c_iso) and c_iso not in isos:
                isos.append(c_iso)
        iso3 = m.get("iso3") or ""
        if iso3 and geo.has(iso3) and iso3 not in isos:
            isos.append(iso3)
        dv = (m.get("feature") or {}).get("divides") if isinstance(m.get("feature"), dict) else None
        for c_iso in ((dv or {}).get("countries") or []):   # a line that divides a country: that country is drawn so it can be cut
            if geo.has(c_iso) and c_iso not in isos:
                isos.append(c_iso)
        # If this is a country mention and we already have a city/capital in the same country,
        # use the city coordinates so the country centroid doesn't skew the pin or bbox.
        ref_m = city_by_iso3.get(iso3, m) if m.get("kind") == "country" else m
        pts_for_view.append({"lat": float(ref_m["lat"]), "lon": float(ref_m["lon"])})
        for (elat, elon) in (m.get("extent") or []):
            pts_for_view.append({"lat": float(elat), "lon": float(elon)})

    # Include previous overlay's last point ONLY if continuing within the exact same country (iso3)
    prev_wp = None
    if isinstance(prev_overlay, dict) and prev_overlay.get("waypoints"):
        last_prev = prev_overlay["waypoints"][-1]
        prev_iso = str(last_prev.get("iso3") or "")
        first_iso = str(mentions[0].get("iso3") or "")
        dist_deg = math.hypot(
            float(last_prev.get("lat", 0.0)) - float(mentions[0]["lat"]),
            float(last_prev.get("lon", 0.0)) - float(mentions[0]["lon"]),
        )
        if prev_iso and prev_iso == first_iso and 0.05 < dist_deg <= 25.0:
            prev_wp = last_prev
            pts_for_view.insert(0, {"lat": float(last_prev["lat"]), "lon": float(last_prev["lon"])})

    # a city with a real boundary (OSM city limits): the camera frames the boundary itself, not the whole country
    from . import city_boundary
    city_geoms = city_boundary.attach(mentions)
    if city_geoms:
        view = geo.view_for([], city_boundary.corners(city_geoms), bw=688, bh=412, smax=40000, pad=0.30, min_span=0.02)
    else:
        view = geo.view_for(isos, pts_for_view, bw=688, bh=412, smax=440, pad=0.24)
    S, K, lonc, latc = view["S"], view["K"], view["lonc"], view["latc"]

    def proj_xy(lon_val: float, lat_val: float) -> Tuple[float, float]:
        px = CX_BOX + (lon_val - lonc) * S * K
        py = CY_BOX - (lat_val - latc) * S
        return round(float(px), 1), round(float(py), 1)

    def proj_arr(a: Any) -> np.ndarray:
        arr = np.asarray(a, np.float64)
        return np.stack([CX_BOX + (arr[:, 0] - lonc) * S * K, CY_BOX - (arr[:, 1] - latc) * S], 1)

    hw, hh = 520.0 / max(S * K, 1e-3), 360.0 / max(S, 1e-3)
    win = (lonc - hw, latc - hh, lonc + hw, latc + hh)

    def sect(b: Tuple[float, float, float, float]) -> bool:
        return not (b[2] < win[0] or b[0] > win[2] or b[3] < win[1] or b[1] > win[3])

    world_view = any(m.get("kind") in ("globe", "ocean") for m in mentions)
    ctx_budget, ctx_min_d = (160000, 3.0) if world_view else (18000, 1.6)

    def country_path(iso_code: str) -> str:
        if not geo.has(iso_code):
            return ""
        c = geo.c[iso_code]
        parts = []
        for poly, bb in zip(c["polys"], c["bbs"]):
            if not sect(bb):
                continue
            if (bb[2] - bb[0]) * S * K < 1.5 and (bb[3] - bb[1]) * S < 1.5:
                continue
            for ring in poly:
                parts.append(_d_svg(proj_arr(ring), min_d=ctx_min_d if iso_code not in isos else 1.6))
        return "".join(p for p in parts if p)

    ctx_paths: List[str] = []
    acc_ctx_len = 0
    for iso_code in geo.c:
        if iso_code in isos:
            continue
        if sect(geo.main_bbox(iso_code)):
            d_str = country_path(iso_code)
            if d_str:
                if acc_ctx_len + len(d_str) > ctx_budget and ctx_paths:
                    break
                ctx_paths.append(d_str)
                acc_ctx_len += len(d_str)

    countries_out: List[Dict[str, Any]] = []
    for iso_code in isos:
        d_str = country_path(iso_code)
        bb = geo.main_bbox(iso_code)
        cx, cy = proj_xy((bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0)
        c_name_ar = next((m["country_ar"] for m in mentions if m["iso3"] == iso_code and m["country_ar"]), iso_code)
        countries_out.append({
            "iso3": iso_code,
            "name_ar": c_name_ar,
            "d": d_str,
            "cx": cx,
            "cy": cy,
        })

    # terrain / sea / region / empire features (rivers, lakes, areas, mountains) drawn on top of the land
    features: List[Dict[str, Any]] = []
    for idx_f, m in enumerate(mentions):
        ft = m.get("feature")
        if not isinstance(ft, dict):
            continue
        fx, fy = proj_xy(float(m["lon"]), float(m["lat"]))
        item: Dict[str, Any] = {"id": f"ft_{scene_idx}_{idx_f}", "shape": ft.get("shape"), "label": m["name_ar"], "kind_label": m["kind_label"],
                                "cx": fx, "cy": fy, "approx": bool(ft.get("approx")),
                                "trigger_frame": max(0, int(round(m["start_sec"] * FPS)) - 4), "d": "", "rx": 0.0, "ry": 0.0}
        if ft.get("shape") == "range" and ft.get("geojson"):
            try:
                geom = json.loads(ft["geojson"])
                xy = proj_arr(np.asarray(geom["coordinates"], np.float64)[:, :2])
                item["d"] = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in xy)
                item["line_kind"] = ft.get("line_kind") or "range"
                step = max(1, len(xy) // 7)
                item["pts"] = [[round(float(x), 1), round(float(y), 1)] for x, y in xy[::step]]   # where the ridge glyphs stand
            except Exception:
                item["d"] = ""
        if ft.get("shape") in ("river", "lake") and ft.get("geojson"):
            try:
                geom = json.loads(ft["geojson"])
                lines = geom["coordinates"] if geom["type"] in ("MultiLineString", "MultiPolygon") else [geom["coordinates"]]
                parts = []
                for ln in lines:
                    rings = ln if geom["type"] in ("Polygon", "MultiPolygon") else [ln]
                    if geom["type"] == "MultiPolygon":
                        rings = [r for poly in ln for r in poly]
                    for ring in rings:
                        parts.append(_d_svg(proj_arr(np.asarray(ring, np.float64)[:, :2]), min_d=1.0, close=ft.get("shape") == "lake"))
                item["d"] = "".join(p for p in parts if p)
            except Exception:
                item["d"] = ""
        if ft.get("shape") == "city" and ft.get("geom"):
            item["d"] = "".join(p for p in (_d_svg(proj_arr(np.asarray(r, np.float64)[:, :2]), min_d=0.8, close=True)
                                            for r in city_boundary.rings(ft["geom"])) if p)
        if ft.get("shape") in ("area",) or not item["d"] and ft.get("shape") in ("river", "lake"):
            item["shape"] = "area" if item["shape"] in ("river", "lake") else item["shape"]
            item["rx"] = max(14.0, float(ft.get("half_w", 3.0)) * S * K)
            item["ry"] = max(14.0, float(ft.get("half_h", 3.0)) * S)
        features.append(item)

    # a dividing line (the Urals) cuts its country into two coloured halves with labels
    split_out: Optional[Dict[str, Any]] = None
    for m in mentions:
        ft_s = m.get("feature") if isinstance(m.get("feature"), dict) else {}
        dv = ft_s.get("divides")
        if not dv or not ft_s.get("geojson"):
            continue
        try:
            from . import geolines
            line_pts = json.loads(ft_s["geojson"])["coordinates"]
            iso_s = next((c for c in dv["countries"] if c in isos and geo.has(c)), None)
            if not iso_s:
                continue
            west_parts, east_parts = [], []
            wpts, epts = [], []
            for poly, bb in zip(geo.c[iso_s]["polys"], geo.c[iso_s]["bbs"]):
                if not sect(bb) or ((bb[2] - bb[0]) * S * K < 1.5 and (bb[3] - bb[1]) * S < 1.5):
                    continue
                for ring in poly:
                    w_r, e_r = geolines.split_polygon(np.asarray(ring, np.float64).tolist(), line_pts)
                    if w_r:
                        xy_w = proj_arr(w_r)
                        west_parts.append(_d_svg(xy_w, min_d=1.6))
                        wpts.append(xy_w)
                    if e_r:
                        xy_e = proj_arr(e_r)
                        east_parts.append(_d_svg(xy_e, min_d=1.6))
                        epts.append(xy_e)
            if not west_parts or not east_parts:
                continue
            big_w = max(wpts, key=lambda a: len(a))
            big_e = max(epts, key=lambda a: len(a))
            line_xy = proj_arr(np.asarray(line_pts, np.float64)[:, :2])
            split_out = {"iso3": iso_s, "west_d": "".join(p for p in west_parts if p), "east_d": "".join(p for p in east_parts if p),
                         "line_d": "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in line_xy),
                         "west_label": dv.get("west_label", ""), "east_label": dv.get("east_label", ""),
                         "west_xy": [round(float(big_w[:, 0].mean()) - 70.0, 1), round(float(big_w[:, 1].mean()) + 40.0, 1)],
                         "east_xy": [round(float(big_e[:, 0].mean()) + 60.0, 1), round(float(big_e[:, 1].mean()), 1)],
                         "trigger_frame": max(0, int(round(m["start_sec"] * FPS)) - 4)}
            break
        except Exception:  # noqa: BLE001 - the split is decoration: the line itself is still drawn
            split_out = None

    # Compute frame timing for each waypoint synced to the voiceover
    single_country_scene = len(isos) <= 1
    waypoints: List[Dict[str, Any]] = []
    for idx_m, m in enumerate(mentions):
        iso_m = m.get("iso3") or ""
        # When a country is mentioned alongside its capital/city in the same scene,
        # keep the pin locked on the capital/city's exact location rather than jumping to the country centroid.
        pin_m = city_by_iso3.get(iso_m, m) if m.get("kind") == "country" else m
        px, py = proj_xy(float(pin_m["lon"]), float(pin_m["lat"]))

        trig_frame = max(0, int(round(m["start_sec"] * FPS)) - 4)
        if idx_m == 0 and trig_frame <= 14:
            trig_frame = 0

        # Vary zoom when previous scene covered the same country to avoid identical consecutive maps
        prev_same_country = (
            isinstance(prev_overlay, dict)
            and prev_overlay.get("waypoints")
            and str(prev_overlay["waypoints"][-1].get("iso3") or "") == str(iso_m or "")
        )
        zoom_variety = 0.18 if prev_same_country else 0.0

        if city_geoms or m.get("kind") in ("continent", "ocean", "globe", "terrain", "empire", "region", "conflict", "route") or m.get("route") or m.get("arrow"):
            target_zoom = 1.0  # fitted view already frames the whole subject (all highlighted countries / the feature)
        elif m.get("is_microstate"):
            target_zoom = 2.15 + zoom_variety
        elif single_country_scene:
            if len(distinct_cities) >= 2:
                target_zoom = 1.22 + zoom_variety if m["kind"] in ("capital", "city") else 1.08 + zoom_variety
            else:
                target_zoom = 1.12 + zoom_variety if m["kind"] in ("capital", "city") else 1.06 + zoom_variety
            fit = _fit_zoom(geo, iso_m, S, K)  # tiny country (Bahrain): view scale is capped, so zoom in to fill
            if fit and fit > target_zoom:
                target_zoom = round(fit, 2)
            if _fills_width(geo, iso_m, S, K):
                target_zoom = 1.0  # a wide country (Russia, USA, China) is already framed edge to edge: zooming only crops it
        else:
            # Multi-country scene: the view is fitted to ALL countries, so a small one (UAE next to Saudi) would be
            # a speck. Zoom until the active country's main bbox fills ~70% of the 688x412 view.
            target_zoom = 1.65 + zoom_variety if m["kind"] in ("capital", "city") else 1.38 + zoom_variety
            fit = _fit_zoom(geo, iso_m, S, K)
            if fit:
                target_zoom = round(fit + zoom_variety, 2)
        if m.get("scale") in ("village", "town") and not m.get("route"):
            target_zoom = max(target_zoom, 2.6)  # tiny place: the magnifier lens shows the close-up

        waypoints.append({
            "id": f"wp_{scene_idx}_{idx_m}",
            "kind": m["kind"],
            "arrow": m.get("arrow"),
            "scale": m.get("scale"),
            "kind_label": m["kind_label"],
            "name_ar": m["name_ar"],
            "name_en": m["name_en"],
            "country_ar": m["country_ar"],
            "iso3": m["iso3"],
            "iso2": m["iso2"],
            "lat": float(pin_m["lat"]),
            "lon": float(pin_m["lon"]),
            "coords": pin_m["coords"],
            "x": px,
            "y": py,
            "trigger_frame": trig_frame,
            "zoom": target_zoom,
        })

    for i in range(len(waypoints)):
        if i + 1 < len(waypoints):
            waypoints[i]["end_frame"] = max(waypoints[i]["trigger_frame"] + 18, waypoints[i + 1]["trigger_frame"])
        else:
            waypoints[i]["end_frame"] = dur_frames

    enter_frame = max(0, waypoints[0]["trigger_frame"] - 6)
    exit_frame = dur_frames

    # Project previous scene's last waypoint if available for cross-scene continuity
    prev_projected = None
    if prev_wp is not None:
        ppx, ppy = proj_xy(float(prev_wp["lon"]), float(prev_wp["lat"]))
        if 10.0 <= ppx <= W_BOX - 10.0 and 10.0 <= ppy <= H_BOX - 10.0:
            prev_projected = {
                "name_ar": prev_wp.get("name_ar", ""),
                "x": ppx,
                "y": ppy,
            }

    # Place only in top-left or top-right HUD corners so lower/center counters and captions are never obstructed
    placements = ["top-left", "top-right"]
    placement = placements[scene_idx % len(placements)]

    sc_vi = sc.get("_vi") if isinstance(sc.get("_vi"), dict) else {}
    is_hist_map = bool(sc_vi.get("is_historical"))
    primary_kind = waypoints[0]["kind"] if waypoints else "country"
    zoom_hierarchy = (
        ["world", "continent", "country", "city"]
        if primary_kind in ("city", "capital", "landmark")
        else (["world", "continent", "country"] if primary_kind == "country" else ["world", "continent"])
    )

    return {
        "enabled": True,
        "placement": placement,
        "enter_frame": enter_frame,
        "exit_frame": exit_frame,
        "viewport": {"w": int(W_BOX), "h": int(H_BOX)},
        "ctx_path": "".join(ctx_paths),
        "countries": countries_out,
        "waypoints": waypoints,
        "prev_waypoint": prev_projected,
        "features": features,
        "split": split_out,
        "zoom_hierarchy": zoom_hierarchy,
        "map_style": "historical" if is_hist_map else "modern",
        "attribution": city_boundary.ATTRIBUTION if city_geoms else "",   # ODbL: shown on the map when OSM boundaries are drawn
    }
