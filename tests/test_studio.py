"""Studio mode: the shot validator enforces the rules before any code, transitions follow the story links, the compiler
times slots from the anchor words, and the orchestration falls back loudly (no LLM, no render: gates=False)."""
import json
import tempfile
import unittest
from pathlib import Path

from pipeline import studio

TEXT = "في عام 1453 فتح العثمانيون القسطنطينية بجيش من ثمانين ألف جندي"
WORDS = [{"t": w, "s": round(0.4 * i, 2), "e": round(0.4 * i + 0.3, 2)} for i, w in enumerate(TEXT.split())]
CTX = {"id": "body1", "role": "body", "dur": 150, "sentence": TEXT, "sentences": [TEXT], "entities": [{"type": "number", "value": 80000}],
       "words": WORDS, "map_overlay": None}
STYLE = json.loads(Path("styles/atlas/style.json").read_text(encoding="utf-8"))["style"]


class TestValidator(unittest.TestCase):
    def test_good_number_shot_passes(self):
        shot = {"device": "number", "keyword": "عام الفتح", "keyword_at": "عام", "number": {"value": 1453, "year": True, "at": "1453"}}
        self.assertEqual(studio.validate_shot(shot, CTX, None, {}), [])

    def test_rules(self):
        errs = " | ".join(studio.validate_shot({"device": "number", "keyword": "كلمة مفتاحية طويلة جدا هنا", "number": {"value": 999, "at": "غائب"}},
                                               CTX, {"device": "number"}, {}))
        for needle in ("1-4 words", "not spoken", "not one of the spoken words", "previous scene already uses"):
            self.assertIn(needle, errs)

    def test_number_from_entities_and_icons_from_the_bundle(self):
        shot = {"device": "pinned", "keyword": "جيش ضخم", "number": {"value": 80000, "at": "ثمانين"}}
        self.assertEqual(studio.validate_shot(shot, CTX, None, {}), [])
        bad = {"device": "statement", "keyword": "سقوط", "hero_icon": "lucide:not-a-real-icon"}
        self.assertTrue(any("available_icons" in e for e in studio.validate_shot(bad, CTX, None, {})))

    def test_icon_budget(self):
        shot = {"device": "statement", "keyword": "سقوط", "hero_icon": "lucide:landmark"}
        prev = {"device": "number", "hero_icon": "lucide:landmark"}
        self.assertTrue(any("previous scene" in e for e in studio.validate_shot(shot, CTX, prev, {})))
        used = {}
        studio.count_use(used, {"device": "hub", "hero_icon": "lucide:landmark", "items": [{"icon": "lucide:landmark"}]})
        studio.count_use(used, {"device": "stack", "items": [{"icon": "lucide:landmark"}]})
        self.assertTrue(any("already used 2 times" in e for e in studio.validate_shot(shot, CTX, None, used)))

    def test_no_line_twice_on_screen(self):
        shot = {"device": "stack", "keyword": "انحسار", "tail": "حفر تبتلع الشواطئ",
                "items": [{"text": "سقوط", "icon": "lucide:landmark"}, {"text": "حفر تبتلع الشواطئ", "icon": "lucide:swords"}]}
        self.assertTrue(any("appears twice" in e for e in studio.validate_shot(shot, CTX, None, {})))

    def test_counter_value_not_repeated_in_a_label(self):
        shot = {"device": "versus", "keyword": "قبل وبعد", "sides": [{"label": "٨٠٠٠٠ جندي", "icon": "lucide:landmark", "value": 80000},
                                                                  {"label": "المدينة", "icon": "lucide:swords"}]}
        self.assertTrue(any("already shown by the counter" in e for e in studio.validate_shot(shot, CTX, None, {})))

    def test_map_scene_must_use_map_and_device_budget(self):
        ctx = dict(CTX, map_overlay={"waypoints": []})
        self.assertTrue(any("must be 'map'" in e for e in studio.validate_shot({"device": "number", "keyword": "x"}, ctx, None, {})))
        self.assertTrue(any("already used" in e for e in studio.validate_shot({"device": "steps", "keyword": "x"}, CTX, None, {"steps": 1})))


class TestNumbers(unittest.TestCase):
    def test_arabic_number_words(self):
        for text, n in (("سبعة عشر مليون وثمانون ألف ومئتان واثنان وأربعون كيلومترًا", 17080242),
                        ("بطول عشرون ألف ومئتان وواحد وأربعون كيلومترًا.", 20241), ("ثلاث مئة عام", 300), ("في ألفين وعشرين", 2020)):
            self.assertIn(n, studio.word_numbers(text))

    def test_numbers_inside_any_text_must_be_spoken(self):
        ctx = dict(CTX, sentence="حدود بطول عشرون ألف ومئتان وواحد وأربعون كيلومترًا", entities=[])
        ok = {"device": "statement", "keyword": "حدود طويلة", "lead": "20,241 كم", "hero_icon": "lucide:landmark"}
        self.assertEqual(studio.validate_shot(ok, ctx, None, {}), [])
        bad = dict(ok, lead="30,000 كم")
        self.assertTrue(any("30,000" in e for e in studio.validate_shot(bad, ctx, None, {})))


class TestDirection(unittest.TestCase):
    def test_transitions_follow_links_and_never_three_in_a_row(self):
        tr = studio.transitions_for(["continue", "continue", "continue", "continue", "contrast", "next_step"])
        self.assertEqual(tr[0]["type"], "none")
        types = [t["type"] for t in tr]
        self.assertNotEqual(types[1:4], ["fade"] * 3)
        self.assertEqual(types[4], "flip")
        self.assertEqual(tr[5]["direction"], "from-left")
        self.assertTrue(all(t["durationInFrames"] <= 12 for t in tr))

    def test_anchor_timing_with_anticipation_and_hero_cap(self):
        code = studio.compile_shot({"device": "number", "keyword": "عام الفتح", "keyword_at": "عام",
                                    "number": {"value": 1453, "year": True, "at": "جندي"}}, CTX, studio.design_system(STYLE, {}))
        # keyword 'عام' at 0.4 s -> KeyLine delay 0.4 - 0.1 - 0.12; 'جندي' at 4.0 s is capped at 25 % of 5 s = 1.25 s
        self.assertIn("delay={0.18}", code)
        self.assertIn("delay={1.25}", code)
        self.assertIn("opacity: interpolate(k.frame, [34, 40]", code)  # the counter is hidden until its word (no '0' on screen)
        self.assertIn("year", code)


class TestOrchestration(unittest.TestCase):
    def test_invalid_designs_fall_back_and_bible_is_written(self):
        scenes = [{"id": "hook", "role": "hook", "dur": 150, "words": WORDS, "entity_plan": [], "map_overlay": None, "beats": [{"kind": "x"}]},
                  {"id": "body1", "role": "body", "dur": 150, "words": WORDS, "entity_plan": [], "map_overlay": None, "beats": [{"kind": "y"}]}]
        spec = {"style": STYLE, "scenes": scenes}
        good = {"device": "number", "keyword": "عام الفتح", "keyword_at": "عام", "number": {"value": 1453, "year": True, "at": "1453"}}

        def ask(system, user, temperature):
            if "creative director" in system:
                return {"world": "أطلس يرسم", "scenes": [{"id": "hook", "function": "question", "link": "continue"},
                                                         {"id": "body1", "function": "quantity", "link": "contrast"}]}
            brief = json.loads(user.split("\n\n")[0])
            return good if brief["scene"]["id"] == "hook" else {"device": "nope"}

        with tempfile.TemporaryDirectory() as tmp:
            out = studio.direct_spec(spec, {"title": "t"}, tmp, log=lambda *_: None, ask=ask, gates=False)
            bible = json.loads((Path(tmp) / "production.json").read_text(encoding="utf-8"))
        self.assertEqual(out["scenes"][0]["beats"][0]["kind"], "authored")
        self.assertEqual(out["scenes"][1]["beats"], [{"kind": "y"}])  # legacy beats kept
        self.assertEqual(bible["fallback"], ["body1"])
        self.assertEqual(bible["shots"]["body1"]["tries"], studio.MAX_DESIGN_TRIES)
        self.assertEqual(out["scenes"][1]["transition"]["type"], "flip")  # contrast link


if __name__ == "__main__":
    unittest.main()
