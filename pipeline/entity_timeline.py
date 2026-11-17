"""الخط الزمني للكيانات الجغرافية (Entity Timeline) — مصدر الحقيقة الوحيد للأعلام.

يحدد لكل مشهد: أي دولة/مدينة يتحدث عنها التعليق الصوتي في كل لحظة (بالإطارات)،
بحيث تتبدل الأعلام (وبقية الطبقات لاحقاً) مع الكلام بدلاً من تثبيت أول دولة طوال المشهد.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from .config import FPS, ROOT

FLAG_KINDS = ("country", "capital", "city", "landmark")
_FLAGS_DIR = ROOT / "remotion" / "public" / "flags" / "4x3"
# أول كيان يُعرض من بداية المشهد إذا ذُكر خلال هذا الجزء الأول من المشهد
_LEAD_IN_RATIO = 0.35
# أقصر مدة مسموحة لعرض علم (أقل من ذلك يسبب وميضاً مزعجاً)
_MIN_SPAN_FRAMES = int(0.8 * FPS)


def _flag_asset_exists(iso2: str) -> bool:
    return bool(iso2) and os.path.exists(_FLAGS_DIR / f"{iso2.lower()}.svg")


def _resolve_iso2(mention: Dict[str, Any]) -> str:
    """رمز ISO2 نهائي ومُتحقق من وجود ملف العلم، أو نص فارغ."""
    from .visual_tools import resolve_flag

    iso3 = str(mention.get("iso3") or "").upper()
    if len(iso3) == 3:
        fl = resolve_flag(iso3)
        if fl.get("found") and _flag_asset_exists(fl.get("iso2") or ""):
            return str(fl["iso2"]).lower()
    iso2 = str(mention.get("iso2") or "").lower()
    if len(iso2) == 2 and _flag_asset_exists(iso2):
        return iso2
    return ""


def build_entity_timeline(sc: Dict[str, Any], words: List[Dict[str, Any]], dur_frames: int) -> List[Dict[str, Any]]:
    """يبني قائمة مقاطع زمنية متتالية غير متداخلة: [{from, to, iso3, iso2, kind, name_ar, name_en, lat, lon}]."""
    from .geo_overlay import extract_timed_geo_mentions

    dur_frames = max(1, int(dur_frames))
    try:
        mentions = extract_timed_geo_mentions(sc.get("narration", ""), "", words, dur_frames)
    except Exception:
        return []

    spans: List[Dict[str, Any]] = []
    for m in mentions:
        if m.get("kind") not in FLAG_KINDS:
            continue
        iso2 = _resolve_iso2(m)
        if not iso2:
            continue
        start = max(0, min(dur_frames - 1, int(round(float(m.get("start_sec", 0.0)) * FPS)) - 4))
        if spans and spans[-1]["iso2"] == iso2:
            continue  # مدينة ثم دولتها (أو العكس) → نفس العلم، لا تبديل
        spans.append({
            "from": start,
            "iso3": str(m.get("iso3") or "").upper(),
            "iso2": iso2,
            "kind": m.get("kind"),
            "name_ar": m.get("name_ar", ""),
            "name_en": m.get("name_en", ""),
            "country_ar": m.get("country_ar", ""),
            "lat": m.get("lat"),
            "lon": m.get("lon"),
        })

    if not spans:
        return []

    if spans[0]["from"] <= dur_frames * _LEAD_IN_RATIO:
        spans[0]["from"] = 0

    # دمج المقاطع القصيرة جداً مع التالية لتفادي الوميض
    merged: List[Dict[str, Any]] = []
    for i, sp in enumerate(spans):
        nxt_from = spans[i + 1]["from"] if i + 1 < len(spans) else dur_frames
        if nxt_from - sp["from"] < _MIN_SPAN_FRAMES and i + 1 < len(spans):
            spans[i + 1]["from"] = sp["from"] if not merged else spans[i + 1]["from"]
            continue
        merged.append(sp)

    for i, sp in enumerate(merged):
        sp["to"] = merged[i + 1]["from"] if i + 1 < len(merged) else dur_frames
    return [sp for sp in merged if sp["to"] > sp["from"]]


def apply_entity_flags(
    visuals: Optional[List[Dict[str, Any]]],
    entities: List[Dict[str, Any]],
    scene_index: int = 0,
) -> List[Dict[str, Any]]:
    """يستبدل أعلام المشهد الثابتة بأعلام مؤقتة متزامنة مع الكيان المذكور صوتياً."""
    base = [v for v in (visuals or []) if isinstance(v, dict)]
    if not entities:
        return base
    others = [v for v in base if v.get("kind") != "flag"]
    shape = "round" if scene_index % 2 else "rect"
    flags = [
        {
            "kind": "flag",
            "placement": "badge-row",
            "from": int(e["from"]),
            "to": int(e["to"]),
            "spec": {
                "code": e["iso2"].upper(),
                "shape": shape,
                "size": 84,
                "animation": "pop",
                "label": e.get("name_ar") or "",
            },
        }
        for e in entities
    ]
    # علم واحد نشط في أي لحظة + حتى عنصرين آخرين
    return flags + others[:2]
