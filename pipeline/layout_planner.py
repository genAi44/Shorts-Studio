"""محرّك تخطيط الخانات (Slot Layout Planner) — يمنع التداخل بين المشاهد والملحقات.

يقسّم الشاشة إلى خانات ثابتة متطابقة مع `pipeline/layout.py` و`remotion/src/layout.ts`:
- HEADER     (y: 72..252)
- STAGE_A    (y: 280..820)
- STAGE_B    (y: 840..1380)
- FULL_STAGE (y: 280..1380)
- CAPTION    (y: 1420..1760)
"""
from __future__ import annotations

from typing import Any, Dict, List

from .layout import BEAT_ZONE, CAPTION_ZONE, SAFE_TOP

SLOTS: Dict[str, Dict[str, int]] = {
    "HEADER": {"top": SAFE_TOP, "left": 60, "width": 960, "height": 180},
    "STAGE_A": {"top": BEAT_ZONE["top"], "left": 60, "width": 960, "height": 540},
    "STAGE_B": {"top": 840, "left": 60, "width": 960, "height": 540},
    "FULL_STAGE": {"top": BEAT_ZONE["top"], "left": 40, "width": 1000, "height": BEAT_ZONE["bottom"] - BEAT_ZONE["top"]},
    "CAPTION": {"top": CAPTION_ZONE["top"], "left": CAPTION_ZONE["left"], "width": 1000, "height": CAPTION_ZONE["bottom"] - CAPTION_ZONE["top"]},
}


def plan_scene_slots(scene: Dict[str, Any]) -> Dict[str, Any]:
    """يوزع الخانات على مقاطع المشهد وعناصره البصرية ويمنع التداخل الزمني على نفس الخانة."""
    beats: List[Dict[str, Any]] = scene.get("beats") or []
    has_map_overlay = bool(scene.get("map_overlay"))
    visual_mode = str(scene.get("visual_mode") or "")
    is_map_focused = visual_mode in ("map_zoom", "battle_map")

    # 1. فرز المقاطع زمنياً ومنع تداخل مقطعين في نفس اللحظة على نفس الخانة
    beats.sort(key=lambda b: int(b.get("from", 0)))
    for i in range(len(beats) - 1):
        cur = beats[i]
        nxt = beats[i + 1]
        cur_from = int(cur.get("from", 0))
        cur_dur = max(1, int(cur.get("dur", 1)))
        nxt_from = int(nxt.get("from", 0))
        if cur.get("_entity") or nxt.get("_entity"):
            continue  # inserted entity shots overlay (and hide) the beat under them: never cut either
        if cur_from + cur_dur > nxt_from:
            cur["dur"] = max(1, nxt_from - cur_from)

    # 2. تعيين الخانة المناسبة لكل مقطع
    for b in beats:
        has_tsx = bool(b.get("tsx_id"))
        kind = str(b.get("kind") or "")
        if has_tsx:
            b["slot"] = "FULL_STAGE"
        elif has_map_overlay and not is_map_focused and kind not in ("map", "map_pin"):
            # عند وجود خريطة منقسمة بالأسفل، يحتل المقطع النصف العلوي STAGE_A
            b["slot"] = "STAGE_A"
        else:
            b["slot"] = "FULL_STAGE"

    # 3. تعيين خانات العناصر البصرية (visuals) ومنع وضعها فوق المقطع الرئيسي
    visuals: List[Dict[str, Any]] = scene.get("visuals") or []
    for v in visuals:
        if not isinstance(v, dict):
            continue
        placement = str(v.get("placement") or "badge-row")
        if placement == "badge-row" or v.get("kind") == "flag":
            v["slot"] = "HEADER"
        elif placement in ("bottom-left", "bottom-right"):
            v["slot"] = "STAGE_B"
        else:
            v["slot"] = "HEADER"

    scene["slot_plan"] = {
        "beats": [{"from": int(b.get("from", 0)), "dur": int(b.get("dur", 0)), "slot": b.get("slot")} for b in beats],
        "has_split_map": has_map_overlay and not is_map_focused,
    }
    return scene
