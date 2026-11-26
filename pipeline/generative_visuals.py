"""Generative Motion Primitives & LLM Canvas Composer (`pipeline/generative_visuals.py`).

Enables the LLM to generate custom animated motion-graphic scenes from scratch
by composing declarative primitives (shapes, paths, badges, counters, gauges,
connectors, icons, emoji, flags) without writing raw JSX or risking runtime crashes.
Works 100% offline with robust fallback procedural generators for any concept.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .config import record_fallback

GENERATIVE_VISUAL_GRAMMAR = """
You are the Lead Motion Graphics Director. Instead of using rigid pre-made templates,
you compose custom animated scenes from scratch using declarative motion primitives.

Canvas Coordinate System:
- Aspect ratio: 9:16 Vertical (1080 x 1920)
- Safe content zone: X: 80..1000 (Center: 540), Y: 320..1420 (Center: 960)
- The bottom area (Y > 1460) is reserved for captions.

Available Primitives:
1. "shape":
   - shape: "rect" | "circle" | "ring" | "triangle" | "pill" | "star" | "shield"
   - x, y, w, h, fill, stroke, strokeWidth, r (radius)
   - motion: "pop" | "rise" | "drop" | "fade" | "scale"
   - loop: "pulse" | "float" | "spin" | "glow" | "breathe" | "shake"
2. "path":
   - curve: "bezier" | "wave" | "mountain" | "arc" | "zigzag"
   - from: [x, y], to: [x, y], control: [x, y]
   - stroke, strokeWidth, strokeDasharray
   - motion: "draw" (animated stroke evolution)
3. "badge":
   - text, sub, icon (e.g. "lucide:flame"), emoji (e.g. "⚠️"), flag (ISO2), bg, borderColor, textColor, size ("sm"|"md"|"lg")
   - motion: "pop" | "drop" | "rise"
4. "counter":
   - from, to, unit, prefix, label, color, fontSize
   - motion: "pop" | "rise"
5. "gauge":
   - value (0..100), label, unit, kind ("linear" | "ring"), width, color
   - motion: "rise" | "pop"
6. "connector":
   - from: [x, y], to: [x, y], label, dashed, color
7. "icon":
   - name (e.g. "lucide:rocket", "ph:sword"), size, color, strokeWidth
8. "text":
   - text, size, color, weight, align, bgChip

Return ONLY valid JSON matching:
{
  "kind": "generative_canvas",
  "title": "عنوان المشهد التوضيحي",
  "subtitle": "شرح فرعي مختصر",
  "accent": "#hexColor",
  "grid": "dots" | "lines" | "radar",
  "elements": [ ... ]
}
"""


def _clean_str(s: Any) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def _words(s: Any, max_words: int = 5, start_word: int = 0) -> str:
    """Truncates text strictly on whole word boundaries, never slicing mid-word."""
    cleaned = _clean_str(s).strip(".!؟?،:؛- ")
    if not cleaned:
        return ""
    toks = cleaned.split()
    sliced = toks[start_word : start_word + max_words]
    return " ".join(sliced).strip(".!؟?،:؛- ")


def _has_any_whole_word(text: str, words: List[str]) -> bool:
    """Matches whole words in Arabic or English using Unicode non-word boundaries (not substring)."""
    if not text:
        return False
    low = text.lower()
    for w in words:
        w_clean = w.strip().lower()
        if not w_clean:
            continue
        pattern = rf"(?<![\w\u0600-\u06FF])(?:[وفبكل]?(?:ال)?)?{re.escape(w_clean)}(?:ات|ون|ين|ان|ة|ه|ها|هم)?(?![\w\u0600-\u06FF])"
        if re.search(pattern, low):
            return True
    return False


def validate_generative_canvas_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures spec is safe, bounds-checked, and conforms to vertical 9:16 format."""
    out = dict(spec)
    out["kind"] = "generative_canvas"
    out["title"] = _words(out.get("title"), 6)
    out["subtitle"] = _words(out.get("subtitle"), 7)
    if out["subtitle"] == out["title"]:
        out["subtitle"] = ""
    out["accent"] = out.get("accent") or "#f59e0b"
    grid = out.get("grid")
    if grid not in (True, False, "dots", "lines", "radar"):
        out["grid"] = "dots"

    raw_elements = out.get("elements") or []
    cleaned_elements: List[Dict[str, Any]] = []

    for i, el in enumerate(raw_elements[:16]):  # max 16 primitives to keep rendering swift
        if not isinstance(el, dict):
            continue
        e = dict(el)
        e_type = e.get("type", "shape")
        e["type"] = e_type
        # Coordinate sanity bounds
        e["x"] = max(40, min(1040, int(e.get("x", 540))))
        e["y"] = max(100, min(1750, int(e.get("y", 960))))
        e["delay"] = max(0, min(300, int(e.get("delay", i * 4))))
        e["motion"] = e.get("motion", "pop")
        e["loop"] = e.get("loop", "none")
        if e_type == "badge":
            e["text"] = _words(e.get("text"), 6)
            if e.get("sub"):
                e["sub"] = _words(e.get("sub"), 6)
            if not e["text"]:
                continue
        elif e_type == "text":
            e["text"] = _words(e.get("text"), 8)
            if not e["text"]:
                continue
        elif e_type == "counter":
            raw_to = e.get("to") if e.get("to") is not None else (e.get("value") if e.get("value") is not None else e.get("number"))
            try:
                num_str = re.sub(r"[^\d.\-]", "", str(raw_to)) if raw_to is not None else ""
                to_val = float(num_str) if num_str else None
            except Exception:
                to_val = None
            if to_val is None:
                lbl = _words(e.get("label") or e.get("text"), 6)
                if not lbl:
                    continue
                e["type"] = "badge"
                e["text"] = lbl
            else:
                e["to"] = int(to_val) if to_val.is_integer() else to_val
                e["from"] = int(e.get("from", 0)) if isinstance(e.get("from", 0), (int, float)) else 0
        elif e_type == "connector":
            fx = e.get("fromX", 300)
            fy = e.get("fromY", 1000)
            tx = e.get("toX", 780)
            ty = e.get("toY", 800)
            from_pt = e.get("from")
            if isinstance(from_pt, (list, tuple)) and len(from_pt) >= 2:
                fx, fy = from_pt[0], from_pt[1]
            to_pt = e.get("to")
            if isinstance(to_pt, (list, tuple)) and len(to_pt) >= 2:
                tx, ty = to_pt[0], to_pt[1]
            e["from"] = [int(fx), int(fy)]
            e["to"] = [int(tx), int(ty)]
            e["fromX"] = int(fx)
            e["fromY"] = int(fy)
            e["toX"] = int(tx)
            e["toY"] = int(ty)
            if e.get("style") == "dashed":
                e["dashed"] = True
        elif e_type == "path":
            from_pt = e.get("from")
            if not isinstance(from_pt, (list, tuple)) or len(from_pt) < 2:
                e["from"] = [180, 1100]
            to_pt = e.get("to")
            if not isinstance(to_pt, (list, tuple)) or len(to_pt) < 2:
                e["to"] = [900, 600]
        cleaned_elements.append(e)

    out["elements"] = cleaned_elements

    # Ensure rich AI Visual Storyteller layers (scene_spec, svg_layers, environment, narration_cues)
    if not out.get("scene_spec") or not out.get("svg_layers") or not out.get("environment"):
        try:
            from .storyteller import design_scene_specification
            story_spec = design_scene_specification(
                scene_id=str(out.get("id") or "gen"),
                role="body",
                narration=str(out.get("title") or "") + " " + str(out.get("subtitle") or ""),
                on_screen=str(out.get("title") or ""),
                scene_index=len(cleaned_elements),
                total_scenes=8,
                prev_narration="",
                next_narration="",
                video_title=str(out.get("title") or ""),
                used_palettes=set(),
                used_environments=set(),
                used_approaches=set(),
                used_cameras=set(),
            )
            for k in ("scene_spec", "svg_layers", "environment", "narration_cues", "background", "secondary_accent", "tsx_id"):
                if not out.get(k) and story_spec.get(k):
                    out[k] = story_spec[k]
        except Exception:
            pass

    return out


def compose_procedural_scene(topic: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Procedurally generates an intricate scene from primitives based on semantic keywords."""
    t = f"{topic} {context or ''}".lower()

    # 1. بركان / حرارة / صهارة
    if _has_any_whole_word(t, ["بركان", "حمم", "صهارة", "انفجار", "لافا", "volcano", "lava", "eruption", "magma"]):
        return _scene_volcano()

    # 2. حصار بحري / مضيق / سفن / ممرات مائية
    if _has_any_whole_word(t, ["بحر", "بحري", "مضيق", "حصار", "سفينة", "سفن", "ملاحة", "قناة", "قراصنة", "naval", "blockade", "strait", "ship", "maritime"]):
        return _scene_sea()

    # 3. ذكاء اصطناعي / شبكة عصبية / حوسبة / بيانات
    if _has_any_whole_word(t, ["ذكاء", "اصطناعي", "عصبية", "بيانات", "حوسبة", "تكنولوجيا", "خوارزمية", "روبوت", "ai", "neural", "computing", "tech"]):
        return _scene_ai()

    # 4. تضخم / صعود الأسعار / صاروخ اقتصادي
    if _has_any_whole_word(t, ["تضخم", "أسعار", "غلاء", "عملة", "صاروخ", "inflation", "rocket", "prices"]):
        return _scene_inflation()

    # 5. حضارات قديمة / إمبراطوريات / آثار / معابد / أهرامات
    if _has_any_whole_word(t, ["حضارة", "حضارات", "إمبراطورية", "أثر", "آثار", "معبد", "أهرام", "أهرامات", "كنز", "كنوز", "فراعنة", "فرعون", "بابل", "آشور", "سومر", "مايا", "إنكا", "رومان", "إغريق", "civilization", "empire", "ancient", "ruin", "temple"]):
        return _scene_civilization(context, topic)

    # 6. فيضانات / مياه / غرق / سيول / أمطار
    if _has_any_whole_word(t, ["فيضان", "فيضانات", "غرق", "طوفان", "أمطار", "مياه", "أنهار", "سدود", "flood", "water", "rain", "deluge", "river"]):
        return _scene_flood(context, topic)

    # 7. محاصيل / غذاء / زراعة / مخازن / قمح / جوع
    if _has_any_whole_word(t, ["محاصيل", "غذاء", "زراعة", "مخازن", "قمح", "جوع", "مجاعة", "إنتاجية", "طعام", "غذائية", "crops", "agriculture", "food", "famine", "grain", "storage"]):
        return _scene_crops(context, topic)

    # 8. دمار / انهيار كامل / سقوط / موت / نهاية الحضارة
    if _has_any_whole_word(t, ["دمار", "انهيار", "سقوط", "هلاك", "موت", "نهاية", "فناء", "زوال", "collapse", "fall", "destruction", "extinction"]):
        return _scene_collapse(context, topic)

    # 9. تصميم مشهد أصيل متكامل عبر محرك السرد البصري (AI Visual Storyteller)
    from .storyteller import design_scene_specification, evaluate_and_improve_scene

    seed_idx = sum(ord(ch) for ch in (topic or "scene")) % 10
    designed = design_scene_specification(
        scene_id=f"gen_{seed_idx}",
        role="body",
        narration=topic,
        on_screen=context or _words(topic, 5),
        scene_index=seed_idx,
        total_scenes=8,
        prev_narration="",
        next_narration="",
        video_title=context or _words(topic, 5),
        used_palettes=set(),
        used_environments=set(),
        used_approaches=set(),
        used_cameras=set(),
    )
    improved, _ = evaluate_and_improve_scene(designed, topic, seed_idx, [])
    return improved


def compose_generative_canvas(
    prompt_or_sentence: str,
    context: Optional[str] = None,
    is_fallback: bool = False,
    fallback_reason: str = "",
    beat_id: str = "generative_canvas",
) -> Dict[str, Any]:
    """Generates a complete GenerativeCanvas beat.

    If `is_fallback` is True, logs an explicit fallback warning, marks `_fallback: True`,
    and raises in DEBUG=1 mode.
    """
    raw_spec = compose_procedural_scene(prompt_or_sentence, context)
    validated = validate_generative_canvas_spec(raw_spec)
    if is_fallback:
        record_fallback(fallback_reason or "generative_canvas_fallback", beat_id=beat_id, beat=validated)
    return validated

# Re-exported so `pipeline.generative_visuals.<name>` keeps working.
from .generative_scenes_b import (  # noqa: E402,F401
    _scene_civilization,
    _scene_collapse,
    _scene_crops,
    _scene_flood,
    _scene_inflation,
)

# Re-exported so `pipeline.generative_visuals.<name>` keeps working.
from .generative_scenes_a import (  # noqa: E402,F401
    _scene_ai,
    _scene_sea,
    _scene_volcano,
)
