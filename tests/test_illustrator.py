"""Studio illustrator: the brief carries timings, palette and the allowed numbers; the model's reply is reduced to a
Hero component inside the fixed stage; maps keep their device; a failed drawing falls back (no LLM, no render)."""
import json
import unittest
from pathlib import Path

from pipeline import illustrator as il, studio

TEXT = "قُطع ٩٣٪ من شريان حياته عام 1964"
WORDS = [{"t": w, "s": round(0.4 * i, 2), "e": round(0.4 * i + 0.3, 2)} for i, w in enumerate(TEXT.split())]
CTX = {"id": "lead", "role": "lead", "dur": 120, "sentence": TEXT, "sentences": [TEXT], "entities": [], "words": WORDS, "map_overlay": None,
       "theme": {}}
STYLE = json.loads(Path("styles/atlas/style.json").read_text(encoding="utf-8"))["style"]
DS = studio.design_system(STYLE, {"core_metaphor": "خزان ماء", "objects": ["الخزان"]})


class TestIllustrator(unittest.TestCase):
    def test_brief(self):
        b = json.loads(il.brief(CTX, {"keyword": "شريان مقطوع", "behavior": "the river is cut"}, DS, "_lead"))
        self.assertEqual(b["words_with_times"][1], {"word": "٩٣٪", "start_s": 0.4})
        self.assertEqual(set(b["allowed_numbers"]), {"7", "93", "100", "1964"})  # 7 = rest of 93 %
        self.assertTrue(b["palette"]["accent2"].startswith("#"))
        self.assertEqual(b["video"]["core_metaphor"], "خزان ماء")

    def test_story_gives_the_direction_context(self):
        ctxs = [dict(CTX, id="a", sentence="البحر يجف وينخفض منسوبه"), dict(CTX, id="b", sentence="ثلاثة وثلاثين متراً بألفين وخمسين")]
        st = studio.story_for(ctxs, {"message": "البحر الميت يختفي", "scenes": [{"id": "b", "intent": "the drop goes on"}]})
        self.assertEqual(st["a"]["before"], [])
        self.assertEqual(st["b"]["before"], ["البحر يجف وينخفض منسوبه"])
        b = json.loads(il.brief(ctxs[1], None, DS, "_b", st["b"]))
        self.assertEqual((b["video_message"], b["scene_intent"]), ("البحر الميت يختفي", "the drop goes on"))
        self.assertIn("Direction:", il.SYSTEM)

    def test_reply_is_reduced_to_the_hero_inside_the_stage(self):
        reply = "Sure!\n```tsx\nimport React from 'react';\n/* PLAN: a river cut by a dam */\nexport const Hero: React.FC<{dur: number}> = () => <g />;\n```"
        hero = il.strip_code(reply)
        self.assertTrue(hero.startswith("/* PLAN"))
        self.assertNotIn("import", hero)
        self.assertIn("const Hero", hero)
        self.assertEqual(il.plan_of(hero), "a river cut by a dam")
        code = il.scene_code(hero, {"keyword": "شريان مقطوع", "keyword_at": "قُطع"}, CTX, DS)
        self.assertIn('<g data-hero-ink="1"><Hero dur={dur} /></g>', code)
        self.assertIn('viewBox="0 0 920 800"', code)
        self.assertIn("KeyLine", code)
        self.assertNotEqual(il.name_for(CTX, {"keyword": "a"}, DS), il.name_for(CTX, {"keyword": "b"}, DS))

    def test_no_code_no_hero(self):
        self.assertIsNone(il.draw(CTX, None, DS, "_x", write=lambda s, u: "I cannot draw that"))
        hero = il.draw(CTX, None, DS, "_x", problems=["too small"], previous="old", write=lambda s, u: "const Hero = () => <g/>;" if "too small" in u else "")
        self.assertIn("const Hero", hero)


if __name__ == "__main__":
    unittest.main()
