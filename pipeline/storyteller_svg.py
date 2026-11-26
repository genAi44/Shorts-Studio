"""Split from `pipeline/storyteller.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from .storyteller import _words  # noqa: E402


def build_svg_construction_layers(
    approach: str,
    intent_info: Dict[str, Any],
    palette: Dict[str, str],
    phrases: List[str],
    scene_index: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Creates bespoke SVG vector layers and coordinated motion elements for the scene."""
    p_col = palette["primary"]
    s_col = palette["secondary"]
    h_col = palette["highlight"]
    surf = palette["surface"]

    nums = intent_info["numbers"]
    cities = intent_info["cities"]
    city_name = intent_info["primary_city_name"] or ""

    svg_layers: List[Dict[str, Any]] = []
    elements: List[Dict[str, Any]] = []

    # 1. Bespoke SVG Vector Illustration Layer tailored to the visual approach
    if approach in ("animated_city_environment", "layered_historical_citadel") or intent_info["has_population"]:
        # Custom SVG Metropolis / Citadel Skyline with illuminated architectural silhouettes & radar halo
        svg_layers.append({
            "kind": "metropolis_skyline",
            "x": 540,
            "y": 900,
            "primary": p_col,
            "secondary": s_col,
            "highlight": h_col,
            "seed": scene_index * 37 + 11,
            "city_label": city_name or (phrases[0] if phrases else ""),
            "population_display": nums[0]["display"] if nums else "",
        })
    elif approach in ("spatial_geographic_diagram", "data_driven_elevation_spire") or cities:
        # Custom SVG Orbital Globe + Spatial Coordinate Rings + Trajectory Arcs
        if cities:
            _lat0, _lon0 = float(cities[0]["lat"]), float(cities[0]["lon"])
            _coords = f"{abs(_lat0):.2f}°{'N' if _lat0 >= 0 else 'S'}, {abs(_lon0):.2f}°{'E' if _lon0 >= 0 else 'W'}"
        else:
            _coords = ""
        svg_layers.append({
            "kind": "orbital_cartography",
            "x": 540,
            "y": 860,
            "primary": p_col,
            "secondary": s_col,
            "highlight": h_col,
            "cities": [c["name"] for c in cities[:4]],
            "coords": _coords,
        })
    elif approach in ("comparative_duel_stage", "visual_metaphor_equilibrium") or intent_info["has_comparison"]:
        # Custom SVG Twin Force Pillars + Dynamic Equilibrium Beam
        _first_ph = phrases[0] if phrases else ""
        _split_pt = max(1, len(_first_ph.split()) // 2)
        svg_layers.append({
            "kind": "equilibrium_duel_stage",
            "x": 540,
            "y": 880,
            "primary": p_col,
            "secondary": s_col,
            "highlight": h_col,
            "left_label": _words(_first_ph, _split_pt) if (len(phrases) == 1 and len(_first_ph.split()) > 2) else _first_ph,
            "right_label": phrases[1] if len(phrases) > 1 else _words(_first_ph, 4, start_word=_split_pt),
        })
    elif approach in ("animated_timeline_expedition", "cause_and_effect_demonstration") or intent_info["has_history"]:
        # Custom SVG Time-Spiral & Cause-Effect Gear/Wave Conduit
        svg_layers.append({
            "kind": "chronicle_conduit",
            "x": 540,
            "y": 890,
            "primary": p_col,
            "secondary": s_col,
            "highlight": h_col,
            "milestones": phrases[:4],
        })
    else:
        # Custom SVG Exploded Isometric Core & Radial Information Nodes
        svg_layers.append({
            "kind": "exploded_isometric_core",
            "x": 540,
            "y": 880,
            "primary": p_col,
            "secondary": s_col,
            "highlight": h_col,
            "nodes": phrases[:4],
        })

    # 2. Coordinated Foreground & Midground Motion Primitives (spread across Y=380..1380)
    # Ambient geometric framing rings & structural paths
    elements.append({
        "id": f"sc_{scene_index}_outer_ring",
        "type": "shape",
        "shape": "ring",
        "x": 540,
        "y": 860,
        "w": 680,
        "stroke": p_col,
        "strokeWidth": 2,
        "fill": "rgba(255,255,255,0.01)",
        "motion": "scale",
        "loop": "spin",
        "delay": 0,
    })
    elements.append({
        "id": f"sc_{scene_index}_inner_shield",
        "type": "shape",
        "shape": "circle" if scene_index % 2 == 0 else "shield",
        "x": 540,
        "y": 860,
        "w": 360,
        "h": 360,
        "stroke": s_col,
        "strokeWidth": 3,
        "fill": surf,
        "motion": "pop",
        "loop": "pulse",
        "delay": 3,
    })

    # Animated trajectory paths connecting upper, center, and lower visual zones
    elements.append({
        "id": f"sc_{scene_index}_curve_top",
        "type": "path",
        "curve": "bezier" if scene_index % 2 == 0 else "arc",
        "from": [180, 500],
        "to": [900, 500],
        "control": [540, 360],
        "stroke": p_col,
        "strokeWidth": 4,
        "motion": "draw",
        "delay": 4,
    })
    elements.append({
        "id": f"sc_{scene_index}_curve_bottom",
        "type": "path",
        "curve": "wave" if scene_index % 3 == 0 else "mountain",
        "from": [140, 1280],
        "to": [940, 1280],
        "control": [540, 1180],
        "stroke": s_col,
        "strokeWidth": 4,
        "motion": "draw",
        "delay": 8,
    })

    # Phrase-synchronized visual cards/badges positioned at distinct vertical & horizontal anchors
    anchors = [
        (540, 460, "drop", "lg"),
        (300, 740, "slide_right", "md"),
        (780, 740, "slide_left", "md"),
        (540, 1140, "rise", "lg"),
    ]
    icons_cycle = [
        "lucide:compass",
        "lucide:landmark",
        "lucide:Layers",
        "lucide:sparkles",
        "lucide:flame",
        "lucide:globe",
        "lucide:crown",
        "lucide:trending-up",
    ]

    for idx, ph in enumerate(phrases[:4]):
        ax, ay, mot, sz = anchors[idx % len(anchors)]
        ic = icons_cycle[(scene_index * 3 + idx) % len(icons_cycle)]
        elements.append({
            "id": f"sc_{scene_index}_phrase_{idx}",
            "type": "badge",
            "x": ax,
            "y": ay,
            "text": _words(ph, 5),
            "sub": cities[idx]["country"] if idx < len(cities) else "",
            "icon": ic,
            "flag": cities[idx]["iso2"].lower() if idx < len(cities) and cities[idx].get("iso2") else undefined_or_str(intent_info, idx),
            "size": sz,
            "bg": surf,
            "borderColor": p_col if idx % 2 == 0 else s_col,
            "textColor": "#ffffff",
            "motion": mot,
            "delay": 6 + idx * 7,
        })
        if idx > 0:
            prev_ax, prev_ay, _, _ = anchors[(idx - 1) % len(anchors)]
            elements.append({
                "id": f"sc_{scene_index}_conn_{idx}",
                "type": "connector",
                "from": [prev_ax, prev_ay],
                "to": [ax, ay],
                "color": h_col,
                "dashed": idx % 2 == 1,
                "delay": 5 + idx * 7,
            })

    # If numbers exist in narration, add real animated counters & gauges
    if nums:
        primary_num = nums[0]
        elements.append({
            "id": f"sc_{scene_index}_hero_counter",
            "type": "counter",
            "x": 540,
            "y": 920,
            "from": 0,
            "to": primary_num["value"],
            "unit": "%" if "%" in primary_num["display"] else "",
            "label": primary_num["label"],
            "color": h_col,
            "fontSize": 76,
            "motion": "pop",
            "delay": 10,
        })
        if len(nums) >= 2:
            v1 = max(1.0, nums[0]["value"])
            v2 = max(1.0, nums[1]["value"])
            ratio = int(round(min(95, max(15, (v1 / (v1 + v2)) * 100))))
            elements.append({
                "id": f"sc_{scene_index}_comp_gauge",
                "type": "gauge",
                "x": 540,
                "y": 1340,
                "value": ratio,
                "label": f"{_words(nums[0]['label'], 2)} vs {_words(nums[1]['label'], 2)}",
                "unit": "%",
                "kind": "linear",
                "width": 660,
                "color": p_col,
                "motion": "rise",
                "delay": 16,
            })
    else:
        # Central hero icon emblem when no raw number is present
        hero_ic = icons_cycle[(scene_index * 5) % len(icons_cycle)]
        elements.append({
            "id": f"sc_{scene_index}_center_icon",
            "type": "icon",
            "name": hero_ic,
            "x": 540,
            "y": 860,
            "size": 124,
            "color": h_col,
            "motion": "pop",
            "loop": "float",
            "delay": 8,
        })

    return svg_layers, elements


def undefined_or_str(intent_info: Dict[str, Any], idx: int) -> Optional[str]:
    if idx == 0 and intent_info.get("primary_city") and intent_info["primary_city"].get("iso2"):
        return str(intent_info["primary_city"]["iso2"]).lower()
    return None
