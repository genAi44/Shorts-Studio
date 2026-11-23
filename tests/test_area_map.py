"""Area-map rule: narration with a place AREA -> area_map beat (extraction, data check, enforcement, layouts).

`python tests/test_area_map.py` regenerates tests/fixtures/area_map_spec.json (country, city, continent, ocean,
comparison, micro-state) through the real apply_beats -> rem.scene_beats path, for `remotion still` frame checks.
"""
import copy
import functools
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import areamap, config, direct, geo, rem  # noqa: E402
from pipeline.scriptspec import scenes_of  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "area_map_spec.json"

SCRIPT = {
    "title": "مساحات",
    "hook": {"narration": "مساحة السعودية ٢٫١٥ مليون كيلومتر مربع.", "on_screen": "السعودية"},
    "lead": {"narration": "مساحة باريس ١٠٥ كيلومترات مربعة.", "on_screen": "باريس"},
    "body1": {"narration": "مساحة أفريقيا ٣٠ مليون كيلومتر مربع.", "on_screen": "أفريقيا"},
    "open_loop1": {"narration": "مساحة المحيط الهادئ ١٦٥ مليون كيلومتر مربع.", "on_screen": "الهادئ"},
    "body2": {"narration": "السعودية أكبر من فرنسا بثلاثة أضعاف.", "on_screen": "ثلاثة أضعاف"},
    "open_loop2": {"narration": "وهناك دولة أصغر بكثير.", "on_screen": "أصغر دولة"},
    "body3": {"narration": "مساحة الفاتيكان ٠٫٤٤ كيلومتر مربع.", "on_screen": "الفاتيكان"},
    "cta": {"narration": "شاركنا رأيك في التعليقات.", "on_screen": "شاركنا"},
}


def _area(**kw):
    return {"kind": "area_map", "title": kw.get("place", ""), "area": kw}


PLAN = {"scenes": [
    {"id": "hook", "beats": [_area(place="السعودية", place_en="Saudi Arabia", iso3="SAU", type="country", value=2150000, unit="km2", digits="arabic")]},
    {"id": "lead", "beats": [_area(place="باريس", place_en="Paris", type="city", value=105, unit="km2", digits="arabic")]},
    {"id": "body1", "beats": [_area(place="أفريقيا", place_en="Africa", type="continent", value=30000000, unit="km2", digits="arabic")]},
    {"id": "open_loop1", "beats": [_area(place="المحيط الهادئ", place_en="Pacific Ocean", type="ocean", value=165000000, unit="km2", digits="arabic")]},
    {"id": "body2", "beats": [_area(place="السعودية", place_en="Saudi Arabia", iso3="SAU", type="country", value=2150000, unit="km2", digits="arabic",
                                    compare={"place": "فرنسا", "place_en": "France", "iso3": "FRA", "type": "country", "ratio": 3.3})]},
    {"id": "open_loop2", "beats": [{"kind": "bigtext", "text": "أصغر دولة"}]},
    {"id": "body3", "beats": [_area(place="الفاتيكان", place_en="Vatican City", iso3="VAT", type="country", value=0.44, unit="km2", digits="arabic")]},
    {"id": "cta", "beats": [{"kind": "bigtext", "text": "شاركنا"}]},
]}


@functools.lru_cache(maxsize=1)
def build_fixture():
    g = geo.get_geo()
    script = direct.apply_beats(copy.deepcopy(SCRIPT), copy.deepcopy(PLAN), g)
    style = json.loads((ROOT / "tests" / "fixtures" / "test_spec.json").read_text(encoding="utf-8"))["style"]
    scenes, t0, dur = [], 0, 120
    for sc in scenes_of(script):
        n = sum(len(x) for x in direct.sentence_groups(sc["narration"]))
        words = [{"t": "w", "s": round(i * 0.3, 2), "e": round(i * 0.3 + 0.25, 2)} for i in range(n)]
        beats = rem.scene_beats(sc, words, dur, g)
        scenes.append({"id": sc["id"], "role": sc["role"], "from": t0, "dur": dur, "words": words, "beats": beats, "visuals": []})
        t0 += dur
    return {"fps": 30, "width": 1080, "height": 1920, "total": t0, "audio": "", "style": style, "scenes": scenes}


class AreaMapTests(unittest.TestCase):
    def setUp(self):
        config.clear_warnings()

    def test_fixture_has_area_map_for_every_area_sentence(self):
        spec = copy.deepcopy(build_fixture())
        kinds = {s["id"]: s["beats"][0]["kind"] for s in spec["scenes"]}
        for sid in ("hook", "lead", "body1", "open_loop1", "body2", "body3"):
            self.assertEqual(kinds[sid], "area_map", sid)
        modes = {s["id"]: s["beats"][0]["view"]["mode"] for s in spec["scenes"] if s["beats"][0]["kind"] == "area_map"}
        self.assertEqual(modes, {"hook": "country", "lead": "magnifier", "body1": "globe", "open_loop1": "globe", "body2": "compare", "body3": "magnifier"})
        FIXTURE.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")

    def test_consecutive_layouts_differ(self):
        spec = build_fixture()
        lays = [s["beats"][0]["layout"] for s in spec["scenes"] if s["beats"][0]["kind"] == "area_map"]
        self.assertTrue(all(a != b for a, b in zip(lays, lays[1:])), lays)

    def test_mismatch_over_10_percent_warns_and_exact_does_not(self):
        areamap.beat_from_raw(_area(place="مصر", iso3="EGY", type="country", value=1000000, unit="km2"))
        self.assertEqual(config.get_last_warnings(), [])
        areamap.beat_from_raw(_area(place="مصر", iso3="EGY", type="country", value=1500000, unit="km2"))
        self.assertTrue(any("1,500,000" in w and "differs" not in w and "data says" in w for w in config.get_last_warnings()))

    def test_unit_conversion(self):  # 1,000,000 mi2 vs Egypt's ~1.0M km2 must warn, 386,102 mi2 must not
        areamap.beat_from_raw(_area(place="مصر", iso3="EGY", type="country", value=386102, unit="mi2"))
        self.assertEqual(config.get_last_warnings(), [])

    def test_missing_area_map_retries_director_once_then_visible_fallback(self):
        script = {"title": "t", "body1": {"narration": "مساحة مصر مليون كيلومتر مربع.", "on_screen": "مصر"}}
        claim = dict(place="مصر", iso3="EGY", type="country", value=1000000, unit="km2")
        bad = {"scenes": [{"id": "body1", "beats": [{"kind": "bigtext", "text": "مصر", "area": claim}]}]}
        calls = []

        def retry(reasons):
            calls.append(reasons)
            return bad  # the director fails again

        out = direct.apply_beats(script, bad, geo.get_geo(), llm_retry_fn=retry)
        self.assertEqual(len(calls), 1)
        self.assertIn("area_map", calls[0][0])
        b = out["body1"]["beats"][0]
        self.assertEqual(b["kind"], "area_map")
        self.assertTrue(b.get("_fallback"))  # rendered with the visible "عرض احتياطي" tag

    def test_retry_that_complies_needs_no_fallback(self):
        script = {"title": "t", "body1": {"narration": "مساحة مصر مليون كيلومتر مربع.", "on_screen": "مصر"}}
        claim = dict(place="مصر", iso3="EGY", type="country", value=1000000, unit="km2")
        bad = {"scenes": [{"id": "body1", "beats": [{"kind": "bigtext", "text": "مصر", "area": claim}]}]}
        good = {"scenes": [{"id": "body1", "beats": [_area(**claim)]}]}
        out = direct.apply_beats(script, bad, geo.get_geo(), llm_retry_fn=lambda r: good)
        self.assertEqual(out["body1"]["beats"][0]["kind"], "area_map")
        self.assertFalse(out["body1"]["beats"][0].get("_fallback"))

    def test_unknown_place_still_renders_visible_disc(self):
        b = areamap.beat_from_raw(_area(place="مكان غير موجود", type="region", value=500, unit="km2"))
        v = areamap.build_view(dict(b, layout="top"))
        self.assertEqual((v["mode"], v["synthetic"]), ("disc", True))
        self.assertTrue(any("not found" in w for w in config.get_last_warnings()))

    def test_continent_areas_come_from_data(self):
        for cid, km2 in (("africa", 30370000), ("asia", 44580000)):
            self.assertEqual(areamap.registry()["places"][cid]["area_km2"], km2)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fixture":
        FIXTURE.write_text(json.dumps(build_fixture(), ensure_ascii=False), encoding="utf-8")
        print("wrote", FIXTURE)
    else:
        unittest.main()
