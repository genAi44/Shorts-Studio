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
    """اختياري: يفحص نسبة البكسلات المظلمة في إطار منتصف المشهد الأول عبر render_still."""
    try:
        from PIL import Image
        import numpy as np
        from . import rem

        if not rem.available() or not spec.get("scenes"):
            return None
        mid_frame = max(1, int(spec["scenes"][0].get("dur", 30) // 2))
        still_path = os.path.join(job_dir, "qa_still_%d.jpg")
        rem.render_still(spec, still_path, mid_frame, job_dir)
        rendered = os.path.join(job_dir, f"qa_still_{mid_frame}.jpg")
        if not os.path.exists(rendered):
            return None
        im = Image.open(rendered).convert("L")
        arr = np.asarray(im)
        # Inspect STAGE_A + STAGE_B region (y: 280..1380)
        roi = arr[280:1380, :]
        dark_ratio = float((roi < 22).mean())
        try:
            os.remove(rendered)
        except OSError:
            pass
        return {"frame": mid_frame, "dark_ratio": round(dark_ratio, 3), "empty_warning": dark_ratio > 0.78}
    except Exception:
        return None


def audit_spec(
    spec: Dict[str, Any],
    job_dir: Optional[str] = None,
    check_pixels: bool = False,
) -> Dict[str, Any]:
    """يفحص كل مشاهد الـ spec ويكتب `qa_report.json` إذا حُدّد `job_dir`."""
    scenes_rep = [_audit_scene(sc) for sc in (spec.get("scenes") or [])]
    avg_score = round(sum(r["score"] for r in scenes_rep) / max(1, len(scenes_rep)), 1)
    report: Dict[str, Any] = {
        "passed": all(r["passed"] for r in scenes_rep),
        "average_score": avg_score,
        "scenes": scenes_rep,
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
