"""بوابة الجودة الآلية (Visual QA Gate) — تفحص الـ spec قبل الرندر وتُصدر `qa_report.json`.

تفحص:
1. عدم تداخل مقطعين زمنياً على نفس الخانة (`slot`).
2. تطابق الأعلام مع الكيانات المنطوقة في `scene.entities` (وعدم وجود علم مصر الافتراضي خطأً).
3. بقاء كل الخانات فوق منطقة الترجمة (`CAPTION_ZONE`).
4. (اختياري عبر `VISUAL_QA=1`) فحص لقطات ثابتة للتأكد من عدم وجود فراغ مظلم مفرط.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from .layout_planner import SLOTS


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


def audit_spec(
    spec: Dict[str, Any],
    job_dir: Optional[str] = None,
    check_pixels: bool = False,
) -> Dict[str, Any]:
    """يفحص كل مشاهد الـ spec ويكتب `qa_report.json` إذا حُدّد `job_dir`."""
    scenes_rep = [_audit_scene(sc) for sc in (spec.get("scenes") or [])]
    avg_score = round(sum(r["score"] for r in scenes_rep) / max(1, len(scenes_rep)), 1)
    design_issues = _audit_design_repetition(spec)
    report: Dict[str, Any] = {
        "passed": all(r["passed"] for r in scenes_rep) and not any(i["severity"] == "error" for i in design_issues),
        "average_score": avg_score,
        "scenes": scenes_rep,
        "design_issues": design_issues,
    }
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
