"""بوابة الجودة الآلية (Visual QA Gate) — تفحص الـ spec قبل الرندر وتُصدر `qa_report.json`.

تفحص:
1. عدم تداخل مقطعين زمنياً على نفس الخانة (`slot`).
2. تطابق الأعلام مع الكيانات المنطوقة في `scene.entities` (وعدم وجود علم مصر الافتراضي خطأً).
3. بقاء كل الخانات فوق منطقة الترجمة (`CAPTION_ZONE`).
4. (اختياري عبر `VISUAL_QA=1`) فحص لقطات ثابتة للتأكد من عدم وجود فراغ مظلم مفرط.
5. بوابة SVG: كل مشهد مؤلَّف (authored) يحمل رسماً SVG صالحاً بمحتوى مرئي فعلي (`svg_problems`).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .layout_planner import SLOTS

# ------------------------------------------------------------------ SVG content gate
# Structure + content of the designer's hero SVG. The render half lives in scene_author.sandbox_render: the real scene is
# rendered in Chromium and the drawn box of the SVG is measured. Returns the list of problems (empty = accepted).
SVG_MAX_BYTES = 60_000
SVG_MIN_SHAPES = 3
_SVG_SHAPES = {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon"}
_SVG_NOT_RENDERED = {"defs", "clipPath", "mask", "symbol", "pattern", "linearGradient", "radialGradient", "marker", "filter",
                     "title", "desc", "metadata"}
# <style> leaks into the whole page (inline SVG); SMIL animation runs on wall-clock time (not frame-deterministic)
_SVG_FORBIDDEN = {"script", "foreignObject", "image", "iframe", "object", "embed", "video", "audio", "canvas", "style",
                  "animate", "animateTransform", "animateMotion", "set"}


def _svg_local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _svg_num(v: Any) -> float:
    m = re.match(r"\s*(-?\d*\.?\d+)", str(v if v is not None else ""))
    return float(m.group(1)) if m else 0.0


def _svg_props(el) -> Dict[str, str]:
    keys = ("fill", "stroke", "stroke-width", "opacity", "fill-opacity", "stroke-opacity", "display", "visibility")
    props = {k: v.strip() for k, v in el.attrib.items() if k in keys}
    for decl in str(el.attrib.get("style", "")).split(";"):
        if ":" in decl:
            k, v = decl.split(":", 1)
            if k.strip() in keys:
                props[k.strip()] = v.strip()
    return props


def _svg_has_geometry(el, tag: str) -> bool:
    a = el.attrib
    nums = lambda s: re.findall(r"-?\d*\.?\d+", s or "")  # noqa: E731
    if tag == "path":
        return bool(re.search(r"[LlHhVvCcSsQqTtAa]", a.get("d", ""))) and len(nums(a.get("d"))) >= 4
    if tag == "rect":
        return _svg_num(a.get("width")) > 0 and _svg_num(a.get("height")) > 0
    if tag == "circle":
        return _svg_num(a.get("r")) > 0
    if tag == "ellipse":
        return _svg_num(a.get("rx")) > 0 and _svg_num(a.get("ry")) > 0
    if tag == "line":
        return (_svg_num(a.get("x1")), _svg_num(a.get("y1"))) != (_svg_num(a.get("x2")), _svg_num(a.get("y2")))
    if tag in ("polyline", "polygon"):
        return len(nums(a.get("points"))) >= (4 if tag == "polyline" else 6)
    return False


def svg_problems(svg: Any) -> List[str]:
    """Rejects: no SVG, an empty string, a document that is not well-formed <svg> XML, unsafe / non-deterministic content,
    and SVGs that draw nothing (every shape hidden, transparent, unpainted, zero-sized, or only inside <defs>)."""
    import xml.etree.ElementTree as ET
    if svg is None:
        return ["the scene has no SVG"]
    if not isinstance(svg, str) or not svg.strip():
        return ["the SVG is an empty string"]
    size = len(svg.encode("utf-8"))
    if size > SVG_MAX_BYTES:
        return [f"the SVG is too large ({size} bytes > {SVG_MAX_BYTES}): simplify the paths"]
    if re.search(r"<!DOCTYPE|<!ENTITY", svg, re.I):
        return ["the SVG must not contain a DOCTYPE or entities"]
    try:
        root = ET.fromstring(svg.strip())
    except ET.ParseError as e:
        return [f"the SVG is not well-formed XML ({e})"]
    if _svg_local(root.tag) != "svg":
        return [f"the root element is <{_svg_local(root.tag)}>, not <svg>"]
    probs: List[str] = []
    vb = [_svg_num(x) for x in re.split(r"[\s,]+", root.attrib.get("viewBox", "").strip()) if x]
    if not (len(vb) == 4 and vb[2] > 0 and vb[3] > 0):
        probs.append('the <svg> needs a valid viewBox="0 0 W H" with W, H > 0')
    count = {"shapes": 0, "texts": 0}

    def walk(el, inherited: Dict[str, str], rendered: bool) -> None:
        tag = _svg_local(el.tag)
        if tag in _SVG_FORBIDDEN:
            probs.append(f"<{tag}> is forbidden in the SVG")
            return
        for k, v in el.attrib.items():
            name = _svg_local(k)
            if name.lower().startswith("on"):
                probs.append(f"event handler '{name}' is forbidden in the SVG")
            if name == "href" and not str(v).startswith("#"):
                probs.append("external href is forbidden in the SVG (only #id references)")
            elif re.search(r"javascript:|url\(\s*['\"]?(?!#)", str(v), re.I):
                probs.append(f"external reference in attribute '{name}' is forbidden (only url(#id))")
        own = _svg_props(el)
        props = {**inherited, **own}
        hidden = own.get("display") == "none" or ("opacity" in own and _svg_num(own["opacity"]) <= 0.02)
        rendered = rendered and tag not in _SVG_NOT_RENDERED and not hidden and props.get("visibility") != "hidden"
        if rendered and tag in _SVG_SHAPES and _svg_has_geometry(el, tag):
            fill_on = props.get("fill", "black") not in ("none", "transparent") and _svg_num(props.get("fill-opacity", "1")) > 0.02
            stroke_on = (props.get("stroke", "none") not in ("none", "transparent") and _svg_num(props.get("stroke-width", "1")) > 0
                         and _svg_num(props.get("stroke-opacity", "1")) > 0.02)
            if tag in ("line", "polyline") and not stroke_on:
                fill_on = False  # an open line is only visible through its stroke
            if fill_on or stroke_on:
                count["shapes"] += 1
        if rendered and tag in ("text", "tspan") and (el.text or "").strip():
            count["texts"] += 1
        for ch in el:
            walk(ch, {k: v for k, v in props.items() if k not in ("opacity", "display")}, rendered)

    walk(root, {}, True)
    if count["shapes"] < SVG_MIN_SHAPES:
        probs.append(f"the SVG draws only {count['shapes']} visible shape(s) (need >= {SVG_MIN_SHAPES} painted, non-empty shapes outside "
                     "<defs>): draw the real hero graphic, not an empty or token placeholder" + (" - text alone is not a graphic" if count["texts"] else ""))
    return list(dict.fromkeys(probs))


def _audit_scene(scene: Dict[str, Any]) -> Dict[str, Any]:
    sid = str(scene.get("id") or "scene")
    issues: List[Dict[str, str]] = []
    score = 100

    # 0b. Rule 1.2 — scene must have at least one non-text visual element
    beats = scene.get("beats") or []
    all_elements = []
    for b in beats:
        all_elements.extend(b.get("elements") or [])
    has_graphic = any(
        b.get("kind") in ("icon", "stat", "map", "map_pin", "chart", "gauge", "counter", "badge",
                          "generative_canvas", "lottie", "flag", "emoji", "photo", "canvas")
        or b.get("icon") or b.get("hero_icon") or b.get("nodes") or b.get("elements")
        for b in beats
    )
    text_only_kinds = {"text", "text_reveal", "text_only", "caption"}
    all_text_only = beats and all(
        b.get("kind") in text_only_kinds and not b.get("elements") and not b.get("icon")
        for b in beats
    )
    # authored scenes: the designer's hero SVG is the scene's graphic and must pass the SVG gate
    for b in beats:
        if b.get("kind") == "authored":
            sp = svg_problems((b.get("data") or {}).get("hero_svg"))
            if sp:
                issues.append({"type": "svg_invalid", "severity": "error", "detail": f"SVG المشهد {sid}: " + "; ".join(sp[:3])})
                score -= 30
            else:
                has_graphic = True
    if all_text_only or (beats and not has_graphic):
        issues.append({
            "type": "text_only_scene",
            "severity": "error",
            "detail": f"مشهد نصي خالص بدون عناصر مرئية — مخالفة القاعدة 1.2 (المشهد: {sid})",
        })
        score -= 25

    # 1. Beat time-window overlap check per slot
    beats = scene.get("beats") or []
    by_slot: Dict[str, List[Dict[str, Any]]] = {}
    for b in beats:
        slot = str(b.get("slot") or "FULL_STAGE")
        by_slot.setdefault(slot, []).append(b)
    for slot, sb in by_slot.items():
        sb_sorted = sorted(sb, key=lambda x: int(x.get("from", 0)))
        for i in range(len(sb_sorted) - 1):
            end_cur = int(sb_sorted[i].get("from", 0)) + int(sb_sorted[i].get("dur", 0))
            start_nxt = int(sb_sorted[i + 1].get("from", 0))
            if end_cur > start_nxt:
                issues.append({
                    "type": "slot_overlap",
                    "severity": "error",
                    "detail": f"تداخل في الخانة {slot} بين المقطعين {i} و{i + 1} ({end_cur} > {start_nxt})",
                })
                score -= 25

    # 2. Flag consistency check against scene.entities
    entities = scene.get("entities") or []
    ent_iso2s = {str(e.get("iso2") or "").upper() for e in entities if e.get("iso2")}
    for v in scene.get("visuals") or []:
        if not isinstance(v, dict) or v.get("kind") != "flag":
            continue
        code = str((v.get("spec") or {}).get("code") or "").upper()
        if not code or len(code) != 2:
            issues.append({"type": "invalid_flag", "severity": "error", "detail": f"علم برمز غير صالح: {code!r}"})
            score -= 25
        elif ent_iso2s and code not in ent_iso2s:
            issues.append({
                "type": "flag_entity_mismatch",
                "severity": "error",
                "detail": f"العلم {code} لا يطابق كيانات المشهد {sorted(ent_iso2s)}",
            })
            score -= 25

    # 3. Slot bounds above CAPTION_ZONE
    cap_top = SLOTS["CAPTION"]["top"]
    for b in beats:
        slot = str(b.get("slot") or "FULL_STAGE")
        rect = SLOTS.get(slot)
        if rect and rect["top"] + rect["height"] > cap_top:
            issues.append({
                "type": "caption_collision",
                "severity": "error",
                "detail": f"الخانة {slot} تتجاوز حد الترجمة ({cap_top})",
            })
            score -= 30

    return {
        "scene_id": sid,
        "score": max(0, score),
        "passed": all(iss["severity"] != "error" for iss in issues),
        "issues": issues,
    }


def _check_still_darkness(spec: Dict[str, Any], job_dir: str) -> Optional[Dict[str, Any]]:
    """اختياري: يرندر إطار منتصف كل مشهد (حزمة واحدة) ويفحص الفراغ المظلم في منطقة البيت (y: 280..1380)."""
    try:
        from PIL import Image
        import numpy as np
        from . import rem

        scenes = spec.get("scenes") or []
        if not rem.available() or not scenes:
            return None
        frames = [int(sc.get("from", 0)) + max(1, int(sc.get("dur", 30)) // 2) for sc in scenes]
        still_path = os.path.join(job_dir, "qa_still_%d.jpg")
        rem.render_still(spec, still_path, ",".join(map(str, frames)), job_dir)
        per_scene = []
        for sc, fr in zip(scenes, frames):
            rendered = os.path.join(job_dir, f"qa_still_{fr}.jpg")
            if not os.path.exists(rendered):
                continue
            arr = np.asarray(Image.open(rendered).convert("L"))
            dark_ratio = float((arr[280:1380, :] < 22).mean())
            per_scene.append({"scene": sc.get("id"), "frame": fr, "dark_ratio": round(dark_ratio, 3), "empty_warning": dark_ratio > 0.78})
            try:
                os.remove(rendered)
            except OSError:
                pass
        if not per_scene:
            return None
        worst = max(per_scene, key=lambda r: r["dark_ratio"])
        return {**worst, "scenes": per_scene, "empty_warning": any(r["empty_warning"] for r in per_scene)}
    except Exception:
        return None


def _audit_design_repetition(spec: Dict[str, Any]) -> List[Dict[str, str]]:
    """Flags when the same scene visual 'kind' appears more than MAX_REPEAT times in one video."""
    MAX_REPEAT = 2
    kind_counts: Dict[str, int] = {}
    for scene in spec.get("scenes") or []:
        for beat in (scene.get("beats") or []):
            k = str(beat.get("kind") or "unknown")
            kind_counts[k] = kind_counts.get(k, 0) + 1
    issues = []
    for k, cnt in kind_counts.items():
        if cnt > MAX_REPEAT and k not in ("text", "caption", "text_reveal"):
            issues.append({
                "type": "design_repetition",
                "severity": "warning",
                "detail": f"نوع المشهد '{k}' يتكرر {cnt} مرات (الحد المسموح: {MAX_REPEAT})",
            })
    return issues


_NUM_RE = re.compile(r"\d[\d,.٫٬]*\d|\d")
_DENY_KEYS = {"img", "query", "alt_queries", "must_show", "avoid", "tsx_id", "kind", "camera", "slot", "narration",
              "role", "cues", "concept", "scene_spec", "id", "layout", "view", "words", "entity_iso3"}
_TSX_TEXT_RE = re.compile(
    r"""(?:>([^<>{}]*[؀-ۿ][^<>{}]*)<)|(?:['"`]([^'"`
]*[؀-ۿ][^'"`
]*)['"`])"""
)
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,")


def _norm_nums(text: str, min_digits: int = 2) -> set:
    out = set()
    for m in _NUM_RE.findall(str(text).translate(_AR_DIGITS)):
        n = re.sub(r"[,.]", "", m)
        if len(n) >= min_digits:
            out.add(n)
    return out


def _shown_strings(obj: Any) -> List[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [t for k, v in obj.items() if k not in _DENY_KEYS for t in _shown_strings(v)]
    if isinstance(obj, list):
        return [t for v in obj for t in _shown_strings(v)]
    return []


def _tsx_shown_numbers(tsx_id: str) -> set:
    """Numbers inside Arabic text literals of a generated TSX scene (ignores colors/pixel values)."""
    try:
        from .storyteller import read_scene_block  # one generated file per scene
        src = read_scene_block(tsx_id)
        i = src.index(f"export const {tsx_id}:")
        body = src[i:]
    except (OSError, ValueError):
        return set()
    nums = set()
    for lit in _TSX_TEXT_RE.findall(body):
        nums |= _norm_nums(lit[0] or lit[1])
    return nums


def _audit_unsourced_numbers(spec: Dict[str, Any], sourced_text: str = "") -> List[Dict[str, str]]:
    """Rule 1.4: a number shown on screen must come from the narration or the researched facts."""
    allowed = _norm_nums(sourced_text)
    issues: List[Dict[str, str]] = []
    for sc in spec.get("scenes") or []:
        narr = " ".join(str(w.get("t", "")) for w in (sc.get("words") or []) if isinstance(w, dict))
        ok = allowed | _norm_nums(narr)
        shown = set()
        for b in sc.get("beats") or []:
            shown |= _norm_nums(" ".join(_shown_strings(b)))
            if b.get("tsx_id"):
                shown |= _tsx_shown_numbers(str(b["tsx_id"]))
        bad = sorted(shown - ok)
        if bad:
            issues.append({"type": "unsourced_number", "severity": "warning",
                           "detail": f"{sc.get('id')}: أرقام ظاهرة بلا مصدر في السرد/الحقائق: {', '.join(bad[:5])}"})
    return issues


def audit_spec(
    spec: Dict[str, Any],
    job_dir: Optional[str] = None,
    check_pixels: bool = False,
    sourced_text: str = "",
) -> Dict[str, Any]:
    """يفحص كل مشاهد الـ spec ويكتب `qa_report.json` إذا حُدّد `job_dir`."""
    scenes_rep = [_audit_scene(sc) for sc in (spec.get("scenes") or [])]
    avg_score = round(sum(r["score"] for r in scenes_rep) / max(1, len(scenes_rep)), 1)
    design_issues = _audit_design_repetition(spec) + _audit_unsourced_numbers(spec, sourced_text)
    report: Dict[str, Any] = {
        "passed": all(r["passed"] for r in scenes_rep) and not any(i["severity"] == "error" for i in design_issues),
        "average_score": avg_score,
        "scenes": scenes_rep,
        "design_issues": design_issues,
    }
    # No silent fallbacks: every degraded beat is marked `_fallback` in the spec and listed here.
    from .config import get_last_warnings
    report["fallback_beats"] = [
        {"scene": sc.get("id"), "kind": b.get("kind")}
        for sc in (spec.get("scenes") or []) for b in (sc.get("beats") or []) if b.get("_fallback")
    ]
    report["fallback_warnings"] = get_last_warnings()
    from .entities import spec_gaps
    report["entity_gaps"] = spec_gaps(spec)
    if report["entity_gaps"]:
        report["passed"] = False
    if check_pixels and job_dir:
        px = _check_still_darkness(spec, job_dir)
        if px:
            report["pixel_check"] = px
    if job_dir:
        try:
            os.makedirs(job_dir, exist_ok=True)
            with open(os.path.join(job_dir, "qa_report.json"), "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        except OSError:
            pass
    return report
