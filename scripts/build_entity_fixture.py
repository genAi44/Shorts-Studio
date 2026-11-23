"""Builds tests/fixtures/entities_spec.json: one scene per entity type, through the REAL pipeline pieces
(entity validation -> rem.build_spec -> overlay builder / ensure_visuals). The "director" is deliberately lazy:
every scene's plan is a bare text beat, so each visual in the result is there because the entity rule put it there.
The entity extraction itself is injected (what the llm would return), so the fixture is deterministic and offline.
Usage: python scripts/build_entity_fixture.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("NO_NETWORK", "1")
os.environ.setdefault("DYNAMIC_TSX_LLM", "0")  # deterministic offline fixture: no llm scenes

from pipeline import entities, rem  # noqa: E402
from pipeline.config import clear_warnings, get_last_warnings  # noqa: E402
from pipeline.geo import get_geo  # noqa: E402
from pipeline.style import normalize as norm_style  # noqa: E402

DUR = 5.0
FPS = 30

# (id, narration, [entities as the llm returns them])
SCENES = [
    ("village", "في واحة سيوة الهادئة يعيش الناس ببساطة", [{"type": "place", "scale": "village", "text": "سيوة", "name_ar": "سيوة", "name_en": "Siwa", "iso2": "EG", "lat": 29.2, "lon": 25.5}]),
    ("capital", "القاهرة هي عاصمة مصر وأكبر مدنها", [{"type": "place", "scale": "capital", "text": "القاهرة", "name_ar": "القاهرة", "name_en": "Cairo", "iso2": "EG", "lat": 30.06, "lon": 31.25}]),
    ("country", "تقع السعودية في قلب الجزيرة العربية", [{"type": "place", "scale": "country", "text": "السعودية", "name_ar": "السعودية", "name_en": "Saudi Arabia", "iso2": "SA", "lat": 24, "lon": 45}]),
    ("continent", "قارة أفريقيا هي ثاني أكبر قارات العالم", [{"type": "place", "scale": "continent", "text": "أفريقيا", "name_ar": "أفريقيا", "name_en": "Africa", "lat": 4, "lon": 20}]),
    ("globe", "الكرة الأرضية كلها تدور حول الشمس", [{"type": "place", "scale": "globe", "text": "الأرضية", "name_ar": "الكرة الأرضية", "name_en": "Earth"}]),
    ("ocean", "المحيط الأطلسي يفصل بين القارتين", [{"type": "place", "scale": "ocean", "text": "الأطلسي", "name_ar": "المحيط الأطلسي", "name_en": "Atlantic Ocean", "lat": 5, "lon": -30}]),
    ("river", "نهر النيل يشق مصر من الجنوب إلى الشمال", [{"type": "terrain", "scale": "river", "text": "النيل", "name_ar": "نهر النيل", "name_en": "Nile", "lat": 26, "lon": 31}]),
    ("year", "في عام 1453 سقطت القسطنطينية", [{"type": "time", "scale": "year", "text": "1453", "value": 1453, "label_ar": "سقوط القسطنطينية"}]),
    ("quantity", "مساحة روسيا 17 مليون كيلومتر مربع", [{"type": "quantity", "scale": "area", "text": "17", "value": 17, "unit": "مليون كم²", "label_ar": "مساحة روسيا", "compare": [{"label": "كندا", "value": 10}, {"label": "الصين", "value": 9.6}]}]),
    ("person", "ابن سينا طبيب وفيلسوف عاش بين 980 و1037", [{"type": "person", "text": "سينا", "name_ar": "ابن سينا", "name_en": "Avicenna", "born": 980, "died": 1037, "role_ar": "طبيب وفيلسوف"}]),
    ("route", "عبرت طريق الحرير من شيان إلى إسطنبول", [{"type": "route", "text": "الحرير", "name_ar": "طريق الحرير", "stops": [{"name_ar": "شيان", "name_en": "Xi'an", "lat": 34.26, "lon": 108.93}, {"name_ar": "سمرقند", "name_en": "Samarkand", "lat": 39.65, "lon": 66.96}, {"name_ar": "إسطنبول", "name_en": "Istanbul", "lat": 41.01, "lon": 28.95}]}]),
    ("conflict", "وقعت معركة بين الجيشين عند الحدود", [{"type": "conflict", "text": "معركة", "name_ar": "معركة حطين", "a": {"name_ar": "الجيش الأول", "lat": 32.8, "lon": 35.4}, "b": {"name_ar": "الجيش الثاني", "lat": 33.5, "lon": 36.3}, "year": 1187}]),
    ("nature", "الأسد من أقوى الحيوانات المفترسة", [{"type": "nature", "scale": "animal", "text": "الأسد", "name_ar": "الأسد", "name_en": "Lion"}]),
    ("empire", "ازدهرت الإمبراطورية العثمانية لقرون", [{"type": "empire", "text": "العثمانية", "name_ar": "الإمبراطورية العثمانية", "name_en": "Ottoman Empire", "from": 1299, "to": 1922, "lat": 40, "lon": 33}]),
]


def make_plan(raw_scenes=SCENES):
    plan, script_ents = [], {}
    for i, (sid, narr, raw) in enumerate(raw_scenes):
        toks = narr.split()
        words = [(w, round(0.15 + k * 0.4, 3), round(0.15 + k * 0.4 + 0.36, 3)) for k, w in enumerate(toks)]
        sentences = [narr]
        per = [[v for v in (entities.validate_entity(e, narr) for e in raw) if v]]
        script_ents[sid] = per
        sc = {"id": sid, "role": "body", "narration": narr, "on_screen": toks[0],
              "beats": [{"kind": "bigtext", "text": " ".join(toks[:3])}]}  # the lazy director
        plan.append({"sc": sc, "audio": {"words": words}, "dur": DUR, "t0": i * DUR})
        del sentences
    return plan, script_ents


def main() -> int:
    clear_warnings()
    geo = get_geo()
    plan, script_ents = make_plan()
    style = norm_style({"name": "ذهبي سينمائي", "seed": 806})
    script = {"_entities": script_ents}
    total = int(round(len(plan) * DUR * FPS))
    gen = ROOT / "remotion" / "src" / "generated" / "DynamicScenes.tsx"
    backup = gen.read_text(encoding="utf-8") if gen.exists() else None
    try:
        spec = rem.build_spec(script, style, plan, total, geo, audio_name="", photo=None, degrade=True)
    finally:
        if backup is not None:  # build_spec regenerates this tracked file; the fixture must not depend on it
            gen.write_text(backup, encoding="utf-8")
    spec["audio"] = ""
    for sc in spec["scenes"]:  # generated TSX scenes are not part of the fixture: plain text beats stand in
        for i, b in enumerate(sc["beats"]):
            if b.get("tsx_id"):
                sc["beats"][i] = {"kind": "bigtext", "text": " ".join(str(b.get("title") or b.get("narration") or "").split()[:3]) or "…",
                                  "from": b.get("from", 0), "dur": b.get("dur", 90), "cues": b.get("cues", [])}
    out = ROOT / "tests" / "fixtures" / "entities_spec.json"
    out.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}: {len(spec['scenes'])} scenes, {total} frames")
    for sc in spec["scenes"]:
        ov = sc.get("map_overlay")
        wps = [w["name_ar"] for w in (ov or {}).get("waypoints", [])]
        print(f"  {sc['id']:<10} beats={[b['kind'] for b in sc['beats']]} overlay={'yes' if ov else 'no'} waypoints={wps} features={[f['shape'] for f in (ov or {}).get('features', [])]}".encode("ascii", "replace").decode())
    for w in get_last_warnings():
        print("warning:", w.encode("ascii", "replace").decode())
    return 0


if __name__ == "__main__":
    sys.exit(main())
