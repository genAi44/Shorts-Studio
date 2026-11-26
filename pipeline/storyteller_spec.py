"""Split from `pipeline/storyteller.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import hashlib
from .storyteller import CAMERA_CHOREOGRAPHIES, ENVIRONMENT_MODES, SCENE_PALETTES, VISUAL_APPROACHES, _pick_unique, _words, build_svg_construction_layers, classify_narration_intent  # noqa: E402


def design_scene_specification(
    scene_id: str,
    role: str,
    narration: str,
    on_screen: str = "",
    scene_index: int = 0,
    total_scenes: int = 8,
    prev_narration: str = "",
    next_narration: str = "",
    video_title: str = "",
    used_palettes: Optional[set] = None,
    used_environments: Optional[set] = None,
    used_approaches: Optional[set] = None,
    used_cameras: Optional[set] = None,
) -> Dict[str, Any]:
    """Creates the complete 6-part Visual Scene Specification (Sections A–F) + SVG layers."""
    if used_palettes is None:
        used_palettes = set()
    if used_environments is None:
        used_environments = set()
    if used_approaches is None:
        used_approaches = set()
    if used_cameras is None:
        used_cameras = set()

    seed = int(hashlib.sha1(f"{video_title}:{scene_id}:{scene_index}:{narration}".encode("utf-8")).hexdigest()[:8], 16)
    intent_info = classify_narration_intent(narration, role=role)

    palette = _pick_unique(SCENE_PALETTES, used_palettes, seed + scene_index, key_fn=lambda p: p["name"])
    env_mode = _pick_unique(ENVIRONMENT_MODES, used_environments, seed + scene_index * 2)
    approach = _pick_unique(VISUAL_APPROACHES, used_approaches, seed + scene_index * 3)
    camera = _pick_unique(CAMERA_CHOREOGRAPHIES, used_cameras, seed + scene_index)

    phrases = intent_info["phrases"]
    svg_layers, elements = build_svg_construction_layers(
        approach=approach,
        intent_info=intent_info,
        palette=palette,
        phrases=phrases,
        scene_index=scene_index,
    )

    # E. Narration Synchronization cues (maps each phrase to time ratio and visual emphasis)
    narration_cues: List[Dict[str, Any]] = []
    n_ph = max(1, len(phrases))
    for p_idx, ph in enumerate(phrases):
        start_r = round(p_idx / n_ph, 2)
        end_r = round((p_idx + 1) / n_ph, 2)
        narration_cues.append({
            "phrase": ph,
            "start_ratio": start_r,
            "end_ratio": end_r,
            "visual_event": f"reveal_node_{p_idx}",
            "emphasis_target": f"sc_{scene_index}_phrase_{p_idx}",
        })

    # Complete 6-section Visual Scene Specification (A–F)
    scene_spec = {
        "visual_concept": {
            "main_idea": f"{approach} illustrating: {_words(on_screen or narration, 7)}",
            "communicates": intent_info["primary_intent"],
            "rationale": (
                f"Translates segment {scene_index + 1}/{total_scenes} ({role}) into an original "
                f"{approach} composition with {env_mode} atmosphere."
            ),
            "approach": approach,
        },
        "composition": {
            "main_subject": on_screen or _words(narration, 5),
            "supporting_elements": [_words(p, 5) for p in phrases[:4]],
            "foreground": "Phrase-synchronized callout badges, animated metric counters, and vector connectors",
            "background": f"Full-bleed 1080x1920 {env_mode} environment in {palette['name']} palette",
            "positioning": "Vertical 3-tier hierarchy across Y=360..1380 within 1080x1920 safe zone",
            "hierarchy": "1. Central SVG focal illustration -> 2. Hero metric/badge -> 3. Phrase-synced nodes",
            "typography_placement": "Top headline zone (Y=220..320), mid-canvas callouts, bottom caption zone (Y=1500+)",
            "color_and_lighting": palette,
        },
        "svg_construction": {
            "illustrations": svg_layers,
            "vector_layers": [env_mode, approach, "foreground_callouts"],
            "labels_and_diagrams": [el.get("text") or el.get("label") for el in elements if el.get("text") or el.get("label")],
            "masks_and_clips": ["radial_vignette_mask", "safe_zone_clip_1080x1920"],
            "relationships": f"Connected flow across {len(phrases)} semantic segments",
        },
        "animation_direction": {
            "entrance": "Spring-physics staggered pop & draw evolution",
            "continuous_movement": f"Ambient {env_mode} drift + orbital ring rotation",
            "transformations": "SVG stroke evolution + 3D perspective depth",
            "camera_movement": camera,
            "visual_reveals": "Sequential phrase-locked node activation",
            "exit": "Smooth scale-and-morph handoff to next scene",
        },
        "narration_sync": {
            "cues": narration_cues,
            "phrase_count": len(narration_cues),
        },
        "transition": {
            "connects_to": f"scene_{scene_index + 1}" if scene_index + 1 < total_scenes else "loop_to_hook",
            "shared_motif": palette["primary"],
            "morph_element": svg_layers[0]["kind"] if svg_layers else "orbital_ring",
            "prev_context": _words(prev_narration, 5),
            "next_context": _words(next_narration, 5),
        },
    }

    bg_css = (
        f"radial-gradient(circle at 50% 38%, {palette['bg_mid']} 0%, "
        f"{palette['bg_top']} 52%, {palette['bg_bottom']} 100%)"
    )

    return {
        "kind": "generative_canvas",
        "title": _words(on_screen or phrases[0] if phrases else video_title, 6),
        "subtitle": _words(phrases[1] if len(phrases) > 1 else "", 6),
        "background": bg_css,
        "bg_mood": palette["name"],
        "accent": palette["primary"],
        "secondary_accent": palette["secondary"],
        "environment": env_mode,
        "grid": "radar" if scene_index % 3 == 0 else ("lines" if scene_index % 3 == 1 else "dots"),
        "camera": camera,
        "svg_layers": svg_layers,
        "elements": elements,
        "narration_cues": narration_cues,
        "scene_spec": scene_spec,
        "tsx_id": f"DynamicScene_{scene_id}_{scene_index}",
    }


def evaluate_and_improve_scene(
    beat: Dict[str, Any],
    narration: str,
    scene_index: int = 0,
    previous_signatures: Optional[List[str]] = None,
    prev_signatures: Optional[List[str]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Evaluates a generated scene beat against the 8 mandatory quality criteria
    and automatically upgrades it if any criterion fails.
    """
    sigs = previous_signatures if previous_signatures is not None else (prev_signatures if prev_signatures is not None else [])
    b = dict(beat)

    # If the beat lacks a full scene_spec or has fewer than 6 elements, enrich via design_scene_specification
    if not b.get("scene_spec") or len(b.get("elements") or []) < 6 or not b.get("svg_layers"):
        designed = design_scene_specification(
            scene_id=str(b.get("id") or f"auto_{scene_index}"),
            role="body",
            narration=narration,
            on_screen=str(b.get("title") or ""),
            scene_index=scene_index,
        )
        for k, v in designed.items():
            if not b.get(k) or k in ("elements", "svg_layers", "scene_spec", "narration_cues", "background", "environment", "accent", "secondary_accent", "camera", "tsx_id"):
                b[k] = v

    elements = list(b.get("elements") or [])
    svg_layers = list(b.get("svg_layers") or [])

    # Criterion 1: Does the visual actually explain the narration?
    has_narration_tie = bool(b.get("title")) or any(el.get("text") or el.get("label") for el in elements)

    # Criterion 2: Is the main idea immediately understandable?
    has_clear_subject = bool(b.get("title")) and (len(svg_layers) > 0 or len(elements) >= 3)

    # Criterion 3: Is the composition visually interesting?
    has_visual_interest = bool(b.get("background")) and bool(b.get("environment")) and len(svg_layers) >= 1

    # Criterion 4: Does it contain enough meaningful visual detail? (Minimum 6 coordinated elements + 1 SVG illustration)
    has_enough_detail = len(elements) >= 6 and len(svg_layers) >= 1

    # Criterion 5: Are the elements coordinated? (Spread across vertical zones, no identical (x,y) collisions for badges)
    badge_coords = [(el.get("x", 540), el.get("y", 960)) for el in elements if el.get("type") == "badge"]
    has_coordinated_layout = len(badge_coords) == len(set(badge_coords))

    # Criterion 6: Is the animation smooth and purposeful?
    has_smooth_animation = bool(b.get("camera")) and any(el.get("motion") for el in elements)

    # Criterion 7: Does it look different from previous scenes?
    sig = f"{b.get('bg_mood')}:{b.get('environment')}:{b.get('accent')}"
    is_distinct = sig not in sigs

    # Criterion 8: Is it visually professional at 1080x1920?
    in_bounds = all(
        60 <= int(el.get("x", 540)) <= 1020 and 220 <= int(el.get("y", 960)) <= 1480
        for el in elements
        if "x" in el and "y" in el
    )

    # Auto-improve if any criterion failed
    if not is_distinct:
        alt_pal = SCENE_PALETTES[(scene_index + len(sigs) + 3) % len(SCENE_PALETTES)]
        alt_env = ENVIRONMENT_MODES[(scene_index + len(sigs) + 2) % len(ENVIRONMENT_MODES)]
        b["accent"] = alt_pal["primary"]
        b["secondary_accent"] = alt_pal["secondary"]
        b["environment"] = alt_env
        b["bg_mood"] = alt_pal["name"]
        b["background"] = (
            f"radial-gradient(circle at 50% 38%, {alt_pal['bg_mid']} 0%, "
            f"{alt_pal['bg_top']} 52%, {alt_pal['bg_bottom']} 100%)"
        )
        sig = f"{b.get('bg_mood')}:{b.get('environment')}:{b.get('accent')}"
        is_distinct = True

    if not has_coordinated_layout:
        safe_slots = [(540, 460), (290, 730), (790, 730), (540, 1150), (540, 1330)]
        b_idx = 0
        for el in elements:
            if el.get("type") == "badge":
                sx, sy = safe_slots[b_idx % len(safe_slots)]
                el["x"], el["y"] = sx, sy
                b_idx += 1
        has_coordinated_layout = True

    if not in_bounds:
        for el in elements:
            if "x" in el:
                el["x"] = max(80, min(1000, int(el["x"])))
            if "y" in el:
                el["y"] = max(260, min(1450, int(el["y"])))
        in_bounds = True

    sigs.append(sig)

    criteria = {
        "1_explains_narration": has_narration_tie,
        "2_immediately_understandable": has_clear_subject,
        "3_visually_interesting": has_visual_interest,
        "4_meaningful_visual_detail": has_enough_detail,
        "5_elements_coordinated": has_coordinated_layout,
        "6_smooth_purposeful_animation": has_smooth_animation,
        "7_distinct_from_previous": is_distinct,
        "8_professional_1080x1920": in_bounds,
    }
    report = {
        "passed": all(criteria.values()),
        "criteria": criteria,
        **criteria,
    }
    return b, report
