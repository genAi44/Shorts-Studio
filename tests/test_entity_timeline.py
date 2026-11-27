"""Phase 1 — Entity Timeline + strict flag engine regression tests."""
import unittest

from pipeline import visual_tools
from pipeline.config import FPS
from pipeline.entity_timeline import apply_entity_flags, build_entity_timeline
from geodb_marker import needs_geodb


def _words(text, start=0.0, step=0.4):
    out, t = [], start
    for w in text.split():
        out.append({"t": w, "s": round(t, 3), "e": round(t + step - 0.05, 3)})
        t += step
    return out


class TestEntityTimeline(unittest.TestCase):
    @needs_geodb
    def test_flags_follow_spoken_country_in_same_scene(self):
        narration = "كوستاريكا ألغت جيشها نهائياً منذ عقود طويلة جداً ثم تليها بنما المجاورة التي تعتمد على القناة"
        words = _words(narration)
        dur = int(len(words) * 0.4 * FPS) + 10
        ents = build_entity_timeline({"narration": narration}, words, dur)
        codes = [e["iso2"] for e in ents]
        self.assertEqual(codes[:2], ["cr", "pa"], ents)
        self.assertEqual(ents[0]["from"], 0)
        # contiguous, non-overlapping
        self.assertEqual(ents[0]["to"], ents[1]["from"])
        self.assertEqual(ents[-1]["to"], dur)
        # Panama span must start around when "بنما" is spoken (word index 9 → 3.6s)
        self.assertGreater(ents[1]["from"], int(3.0 * FPS))

    def test_no_geo_mention_yields_empty_timeline(self):
        narration = "هذه حقيقة مدهشة لا يعرفها الكثيرون عن التاريخ"
        self.assertEqual(build_entity_timeline({"narration": narration}, _words(narration), 120), [])

    def test_apply_entity_flags_replaces_static_scene_flag(self):
        static = [
            {"kind": "flag", "placement": "badge-row", "spec": {"code": "CR"}},
            {"kind": "icon", "spec": {"name": "lucide:shield"}},
        ]
        ents = [
            {"from": 0, "to": 90, "iso2": "cr", "name_ar": "كوستاريكا"},
            {"from": 90, "to": 200, "iso2": "pa", "name_ar": "بنما"},
        ]
        out = apply_entity_flags(static, ents, scene_index=0)
        flags = [v for v in out if v["kind"] == "flag"]
        self.assertEqual([f["spec"]["code"] for f in flags], ["CR", "PA"])
        self.assertEqual((flags[1]["from"], flags[1]["to"]), (90, 200))
        self.assertTrue(any(v["kind"] == "icon" for v in out))

    def test_apply_entity_flags_without_entities_keeps_visuals(self):
        static = [{"kind": "icon", "spec": {"name": "lucide:shield"}}]
        self.assertEqual(apply_entity_flags(static, [], 0), static)


class TestStrictFlags(unittest.TestCase):
    def test_partial_arabic_word_does_not_resolve(self):
        self.assertFalse(visual_tools.resolve_flag("بنمائي")["found"])

    def test_iso3_extras_resolve(self):
        self.assertEqual(visual_tools.resolve_flag("PAN")["iso2"], "pa")
        self.assertEqual(visual_tools.resolve_flag("SLB")["iso2"], "sb")

    def test_normalize_flag_without_code_is_dropped_not_egypt(self):
        self.assertIsNone(visual_tools.normalize_visual_element({"kind": "flag", "spec": {}}))
        self.assertIsNone(visual_tools.normalize_visual_element({"kind": "flag", "spec": {"code": "مكان مجهول"}}))

    def test_normalize_preserves_timed_window(self):
        el = visual_tools.normalize_visual_element({"kind": "flag", "from": 30, "to": 90, "spec": {"code": "PA"}})
        self.assertEqual((el["from"], el["to"], el["spec"]["code"]), (30, 90, "PA"))


if __name__ == "__main__":
    unittest.main()
