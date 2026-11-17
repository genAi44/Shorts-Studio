import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.generative_visuals import (
    compose_generative_canvas,
    validate_generative_canvas_spec,
    GENERATIVE_VISUAL_GRAMMAR,
)
from pipeline.visual_tools import apply_chat_visual_edit


class TestGenerativeVisuals(unittest.TestCase):
    def test_grammar_not_empty(self):
        self.assertTrue(len(GENERATIVE_VISUAL_GRAMMAR) > 200)
        self.assertIn("shape", GENERATIVE_VISUAL_GRAMMAR)
        self.assertIn("connector", GENERATIVE_VISUAL_GRAMMAR)
        self.assertIn("counter", GENERATIVE_VISUAL_GRAMMAR)

    def test_compose_volcano_scene(self):
        spec = compose_generative_canvas("انفجار بركاني مع حمم منصهرة")
        self.assertEqual(spec["kind"], "generative_canvas")
        self.assertEqual(spec["accent"], "#ef4444")
        self.assertTrue(len(spec["elements"]) >= 4)
        types = [el["type"] for el in spec["elements"]]
        self.assertIn("triangle", [el.get("shape") for el in spec["elements"] if el.get("type") == "shape"])
        self.assertIn("counter", types)
        self.assertIn("badge", types)

    def test_compose_naval_blockade(self):
        spec = compose_generative_canvas("حصار بحري وإغلاق مضيق مائي")
        self.assertEqual(spec["kind"], "generative_canvas")
        types = [el["type"] for el in spec["elements"]]
        self.assertIn("path", types)
        self.assertIn("connector", types)
        self.assertIn("counter", types)

    def test_compose_ai_neural_scene(self):
        spec = compose_generative_canvas("ثورة الذكاء الاصطناعي والشبكات العصبية")
        self.assertEqual(spec["kind"], "generative_canvas")
        self.assertEqual(spec["grid"], "radar")
        types = [el["type"] for el in spec["elements"]]
        self.assertIn("connector", types)
        self.assertIn("gauge", types)

    def test_compose_inflation_scene(self):
        spec = compose_generative_canvas("تضخم اقتصادي وصعود صاروخي للأسعار")
        self.assertEqual(spec["kind"], "generative_canvas")
        types = [el["type"] for el in spec["elements"]]
        self.assertIn("path", types)
        self.assertIn("counter", types)

    def test_validate_spec_bounds(self):
        bad_spec = {
            "title": "Test Title",
            "elements": [
                {"type": "shape", "x": -500, "y": 9999, "delay": -10},
                {"type": "counter", "x": 1200, "y": -100, "to": 500},
            ],
        }
        cleaned = validate_generative_canvas_spec(bad_spec)
        self.assertEqual(cleaned["kind"], "generative_canvas")
        self.assertEqual(cleaned["elements"][0]["x"], 40)
        self.assertEqual(cleaned["elements"][0]["y"], 1750)
        self.assertEqual(cleaned["elements"][0]["delay"], 0)
        self.assertEqual(cleaned["elements"][1]["x"], 1040)
        self.assertEqual(cleaned["elements"][1]["y"], 100)

    def test_chat_edit_triggers_generative_canvas(self):
        dummy_script = {
            "hook": {
                "narration": "المشهد الافتتاحي المثير",
                "on_screen": "بداية القصة",
                "visuals": [],
                "beats": [],
            }
        }
        res = apply_chat_visual_edit(dummy_script, "اصنع رسم توضيحي لبركان ينفجر وتخرج منه حمم", "hook")
        self.assertIn("script", res)
        beats = res["script"]["hook"].get("beats") or []
        self.assertTrue(len(beats) > 0)
        self.assertEqual(beats[0]["kind"], "generative_canvas")
        self.assertIn("بركان", beats[0]["title"])


if __name__ == "__main__":
    unittest.main()
