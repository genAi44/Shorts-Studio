"""Builds tests/fixtures/all_beats_spec.json: one 5-second scene per beat kind (plus map-overlay and
LLM-scene cases), every beat passed through the real `direct.normalize_beat` so the fixture also proves the
director vocabulary is valid. Usage: python scripts/build_fixture.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import direct, rem  # noqa: E402
from pipeline.config import clear_warnings, get_last_warnings  # noqa: E402
from pipeline.geo import get_geo  # noqa: E402
from pipeline.geo_overlay import build_scene_map_overlay  # noqa: E402
from pipeline.style import normalize as norm_style  # noqa: E402

SCENE_FRAMES = 150
FPS = 30

# raw director output per kind (what the LLM would send); sentence = narration for that scene
RAW = [
    ("bigtext", {"kind": "bigtext", "text": "ثروة هائلة تتجاوز الدول", "sub": "عنوان فرعي"}, "ثروة هائلة تتجاوز الدول بأكملها"),
    ("stat", {"kind": "stat", "number": "1,379,000", "label": "نسمة في ميلانو", "layout": "ring"}, "يسكن ميلانو مليون وثلاثمائة ألف نسمة"),
    ("stat_ring_v2", {"kind": "stat_ring_v2", "title": "نمو سريع", "number": "68", "label": "نسبة النمو السنوي"}, "نمو سنوي بنسبة ثمانية وستين بالمئة"),
    ("bars", {"kind": "bars", "title": "أكبر المدن", "items": [{"label": "الرياض", "value": 7}, {"label": "دبي", "value": 3.5}, {"label": "الدوحة", "value": 2.4}]}, "الرياض أكبر من دبي والدوحة"),
    ("pie_chart", {"kind": "pie_chart", "title": "مصادر الدخل", "items": [{"label": "نفط", "value": 50}, {"label": "تجارة", "value": 30}, {"label": "سياحة", "value": 20}]}, "النفط نصف الدخل والتجارة ثلاثون بالمئة"),
    ("line_chart", {"kind": "line_chart", "title": "النمو عبر السنين", "points": [{"label": "2000", "value": 10}, {"label": "2010", "value": 25}, {"label": "2020", "value": 60}], "y_label": "مليار"}, "ارتفع الناتج عبر العقود الماضية"),
    ("timeline", {"kind": "timeline", "title": "مراحل", "items": [{"year": "1932", "label": "التأسيس"}, {"year": "1960", "label": "اكتشاف النفط"}, {"year": "2016", "label": "رؤية جديدة"}]}, "تأسست ثم اكتشف النفط ثم جاءت الرؤية"),
    ("timeline_card", {"kind": "timeline_card", "title": "محطات", "items": [{"year": "1900", "label": "البداية"}, {"year": "1950", "label": "التوسع"}, {"year": "2000", "label": "الازدهار"}]}, "بداية ثم توسع ثم ازدهار"),
    ("versus", {"kind": "versus", "left": {"title": "الرياض", "value": "7M"}, "right": {"title": "جدة", "value": "4M"}}, "الرياض مقابل جدة"),
    ("split", {"kind": "split", "left": {"title": "قبل", "sub": "مدينة صغيرة"}, "right": {"title": "بعد", "sub": "عاصمة عالمية"}}, "قبل وبعد التحول الكبير"),
    ("list", {"kind": "list", "title": "أهم النقاط", "items": ["النفط والغاز", "التجارة والمال", "السياحة والثقافة"]}, "ثلاثة مصادر رئيسية للقوة"),
    ("icons", {"kind": "icons", "title": "ركائز", "items": [{"icon": "building", "label": "عمران"}, {"icon": "coin", "label": "اقتصاد"}, {"icon": "book", "label": "علم"}]}, "عمران واقتصاد وعلم"),
    ("ticker", {"kind": "ticker", "items": ["نفط", "غاز", "استثمار", "سياحة"]}, "نفط وغاز واستثمار وسياحة"),
    ("cardstack", {"kind": "cardstack", "items": [{"text": "الأولى", "value": "1"}, {"text": "الثانية", "value": "2"}, {"text": "الثالثة", "value": "3"}]}, "أولا وثانيا وثالثا"),
    ("canvas", {"kind": "canvas", "elements": [{"type": "icon", "name": "globe", "x": 540, "y": 800}]}, "عالم واسع"),
    ("map", {"kind": "map", "countries": ["SAU"], "highlight": ["SAU"], "points": [{"name": "الرياض", "lat": 24.7, "lon": 46.7}]}, "الرياض عاصمة السعودية"),
    ("map_pin", {"kind": "map_pin", "region": "gulf", "points": [{"name": "الدوحة", "lat": 25.28, "lon": 51.53}]}, "الدوحة عاصمة قطر"),
    ("photo", {"kind": "photo", "query": "Riyadh skyline landmark", "text": "برج المملكة", "img": "grain.png"}, "برج المملكة في الرياض"),
    ("elevation_profile", {"kind": "elevation_profile", "title": "قمة جبل", "capital": "لاباز", "height": "3640", "unit": "م", "country": "بوليفيا"}, "ترتفع لاباز ثلاثة آلاف وستمائة متر فوق سطح البحر"),
    ("versus_battle", {"kind": "versus_battle", "title": "نزال", "left": {"title": "الشمال", "value": "40"}, "right": {"title": "الجنوب", "value": "60"}, "result_badge": "فوز الجنوب"}, "صراع الشمال والجنوب"),
    ("animated_route", {"kind": "animated_route", "title": "الرحلة", "from_city": "الرياض", "to_city": "دبي", "distance": "980 كم", "duration_label": "10 ساعات"}, "من الرياض إلى دبي"),
    ("balance_meter", {"kind": "balance_meter", "title": "الميزان", "left_label": "الصادرات", "right_label": "الواردات", "left_weight": 60, "right_weight": 40, "verdict": "فائض تجاري"}, "الصادرات أكبر من الواردات"),
    ("deep_time_slider", {"kind": "deep_time_slider", "title": "عبر الزمن", "from_year": "1900", "to_year": "2025", "era_label": "قرن ونيف", "milestone": "اكتشاف النفط"}, "عبر أكثر من قرن"),
    ("stack_pyramid", {"kind": "stack_pyramid", "title": "الهرم", "tiers": [{"label": "القمة", "value": "1"}, {"label": "الوسط", "value": "2"}, {"label": "القاعدة", "value": "3"}]}, "هرم من ثلاث طبقات"),
    ("macro_zoom_globe", {"kind": "macro_zoom_globe", "title": "تقريب", "region_label": "الخليج", "city_label": "المنامة", "coords": "26.2N 50.6E", "stat_badge": "مدينة"}, "تقريب على الخليج ثم المنامة"),
    ("subsurface_mine", {"kind": "subsurface_mine", "title": "المنجم", "depth": "1200", "mineral": "ذهب", "temp": "45", "layers": ["تربة", "صخر", "خام"]}, "ذهب على عمق ألف ومئتي متر"),
    ("dot_matrix_population", {"kind": "dot_matrix_population", "title": "السكان", "total_dots": 100, "highlighted_dots": 35, "ratio_label": "35%", "group_a": "شباب", "group_b": "آخرون"}, "خمسة وثلاثون بالمئة من السكان شباب"),
    ("money_waterfall", {"kind": "money_waterfall", "title": "التدفق", "amount": "12 مليار", "direction": "down", "cause": "هبوط الأسعار", "impact_pct": "15%"}, "خسارة اثني عشر مليارا"),
    ("frontline_clash", {"kind": "frontline_clash", "title": "المواجهة", "side_a": "الشمال", "side_b": "الجنوب", "location": "الحدود", "year": "1991", "outcome": "هدنة"}, "مواجهة على الحدود"),
    ("city_skyline", {"kind": "city_skyline", "title": "أفق المدينة", "subtitle": "ليلا", "seed": 3}, "أفق المدينة في الليل"),
    ("architecture", {"kind": "architecture", "title": "عمارة قديمة", "subtitle": "قلعة", "era": "القرن 17", "seed": 5}, "قلعة من القرن السابع عشر"),
    ("mystery_scene", {"kind": "mystery_scene", "question": "من يملك أغنى عاصمة؟", "subtitle": "سؤال", "variant": 1, "seed": 2}, "من يملك أغنى عاصمة"),
    ("custom_scene", {"kind": "custom_scene", "title": "مشهد مخصص", "scene_spec": {"approach": "radial"}}, "مشهد مخصص بالكامل"),
    ("cinematic_dramatic", {"kind": "cinematic_dramatic", "title": "درامي", "scene_spec": {"cinematic": "cinematic_dramatic"}}, "لحظة درامية"),
]

OVERLAY_SCENES = [
    ("overlay_country", "الرياض عاصمة السعودية وأكبر مدنها", "map_zoom"),
    ("overlay_microstate", "المنامة عاصمة مملكة البحرين الصغيرة", "map_zoom"),
    ("overlay_region", "هل تعلم أن بعض العواصم العربية غنية جدا", "map_zoom"),
]

LLM_SCENES = [("llm_plain", "DynamicScene_hook_0_0", None), ("llm_with_map", "DynamicScene_lead_0_1", "وتليها مدينة الكويت عاصمة الكويت")]


def words_for(text: str, start: float = 0.15, step: float = 0.38):
    return [{"t": w, "s": round(start + i * step, 2), "e": round(start + i * step + step - 0.04, 2)} for i, w in enumerate(text.split())]


def main() -> int:
    clear_warnings()
    geo = get_geo()
    base = json.load(open(ROOT / "tests" / "fixtures" / "test_spec.json", encoding="utf-8"))
    spec = {k: base[k] for k in ("fps", "width", "height", "audio")}
    # the house look (dark gold / cyan, "ذهبي سينمائي"), fixed seed so the fixture is reproducible
    spec["style"] = norm_style({"name": "ذهبي سينمائي", "seed": 806})
    scenes, t, bad = [], 0, []

    def add(sid, beats, narration, role="body", overlay=None, visual_mode=""):
        nonlocal t
        sc = {"id": sid, "role": role, "from": t, "dur": SCENE_FRAMES, "words": words_for(narration), "visuals": [],
              "beats": [dict(b, **{"from": 0, "dur": SCENE_FRAMES}) for b in beats]}
        if overlay:
            sc["map_overlay"] = overlay
        if visual_mode:
            sc["visual_mode"] = visual_mode
        scenes.append(sc)
        t += SCENE_FRAMES

    for kind, raw, sentence in RAW:
        b = direct.normalize_beat(copy.deepcopy(raw), sentence, geo)
        if b.get("kind") != kind or b.get("_fallback"):
            bad.append(f"{kind} -> {b.get('kind')} (fallback={bool(b.get('_fallback'))})")
        if kind == "map":
            b["view"] = rem.map_view(geo, b)  # what rem.scene_beats does at build time
        elif kind == "map_pin" and (b.get("points") or b.get("countries")):
            b["view"] = rem.map_view(geo, {"countries": ["QAT"], "highlight": ["QAT"], "points": b.get("points")})
        if kind == "photo":
            b["img"] = "grain.png"  # media resolution happens at render time; a bundled texture stands in for a photo
        add(f"beat_{kind}", [b], sentence)

    for sid, narration, mode in OVERLAY_SCENES:
        words = words_for(narration, step=0.3)
        ov = build_scene_map_overlay({"id": sid, "role": "body", "narration": narration, "on_screen": ""}, words, SCENE_FRAMES, geo=geo, scene_idx=1)
        if not ov:
            bad.append(f"{sid}: no map overlay")
        add(sid, [{"kind": "bigtext", "text": narration.split()[0]}], narration, overlay=ov, visual_mode=mode)

    for sid, tsx_id, narration in LLM_SCENES:
        ov = None
        if narration:
            ov = build_scene_map_overlay({"id": sid, "role": "body", "narration": narration, "on_screen": ""}, words_for(narration, step=0.3), SCENE_FRAMES, geo=geo, scene_idx=2)
        add(sid, [{"kind": "generative_canvas", "tsx_id": tsx_id, "elements": [], "settled": True}], narration or "مشهد من توليد النموذج", overlay=ov)

    spec["scenes"] = scenes
    spec["total"] = t
    out = ROOT / "tests" / "fixtures" / "all_beats_spec.json"
    out.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}: {len(scenes)} scenes, {t} frames")
    for w in get_last_warnings():
        print("fallback:", w.encode("ascii", "replace").decode())
    if bad:
        print("FIXTURE PROBLEMS:\n  " + "\n  ".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
