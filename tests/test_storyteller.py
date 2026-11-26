"""Tests for AI-Driven Visual Storytelling & Original Scene Generation (pipeline/storyteller.py)."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.storyteller import (
    classify_narration_intent,
    design_scene_specification,
    evaluate_and_improve_scene,
)
from pipeline.direct import apply_beats


class TestVisualStoryteller(unittest.TestCase):
    def test_classify_narration_intent_categories(self):
        # Urban / City
        urban = classify_narration_intent("تعد طوكيو أكبر مدينة وحاضرة عمرانية مزدحمة بالأبراج في العالم", role="body")
        self.assertEqual(urban["primary_intent"], "urban_metropolis")
        self.assertEqual(urban["visual_approach"], "metropolis_skyline")

        # Comparison / Equilibrium
        comp = classify_narration_intent("بينما تتفوق شنغهاي في حجم الموانئ مقابل بكين في المركز السياسي", role="body")
        self.assertEqual(comp["primary_intent"], "comparative_analysis")
        self.assertEqual(comp["visual_approach"], "equilibrium_duel_stage")

        # Historical / Timeline
        hist = classify_narration_intent("تأسست إمبراطورية العلوم عام 762 ميلادي في العصر العباسي", role="body")
        self.assertEqual(hist["primary_intent"], "historical_chronicle")
        self.assertEqual(hist["visual_approach"], "chronicle_conduit")

        # Cause / Process / System
        proc = classify_narration_intent("يؤدي تدفق الطاقة عبر شبكات الترابط الصناعي إلى مضاعفة الإنتاج", role="body")
        self.assertIn(proc["primary_intent"], ("cause_and_consequence", "process_and_transformation"))
        self.assertEqual(proc["visual_approach"], "exploded_isometric_core")

    def test_six_part_scene_specification(self):
        beat = design_scene_specification(
            scene_id="body1_0",
            role="body",
            narration="تتصدر طوكيو مدن العالم بأكثر من 37 مليون نسمة في شبكة حضرية عملاقة.",
            on_screen="طوكيو: 37 مليون نسمة",
            scene_index=2,
            total_scenes=8,
            prev_narration="كيف توزعت أكبر الحواضر البشرية عبر القارات؟",
            next_narration="تليها دلهي وشنغهاي في سباق ديموغرافي متسارع.",
            video_title="أكبر مدن العالم",
        )
        self.assertIn("scene_spec", beat)
        spec = beat["scene_spec"]
        # Verify all 6 mandatory sections A-F
        for section_key in (
            "visual_concept",
            "composition",
            "svg_construction",
            "animation_direction",
            "narration_sync",
            "transition",
        ):
            self.assertIn(section_key, spec, f"Missing section {section_key} in scene_spec")
            self.assertIsInstance(spec[section_key], dict)

        # Verify custom SVG layers and phrase-synced cues
        self.assertTrue(len(beat.get("svg_layers", [])) >= 1)
        self.assertTrue(len(beat.get("narration_cues", [])) >= 2)
        self.assertTrue(len(beat.get("elements", [])) >= 6)
        self.assertTrue(beat.get("tsx_id", "").startswith("DynamicScene_"))

    def test_eight_criteria_quality_evaluation_and_auto_enrichment(self):
        # Create an intentionally sparse beat and verify evaluate_and_improve_scene upgrades it
        sparse_beat = {
            "kind": "generative_canvas",
            "title": "نمو المدن",
            "elements": [
                {"type": "badge", "text": "نمو", "x": 540, "y": 900}
            ],
        }
        improved, report = evaluate_and_improve_scene(
            sparse_beat,
            narration="شهدت المدن الكبرى تحولاً عمرانياً هائلاً رفع الكثافة إلى 85% خلال قرن واحد.",
            scene_index=1,
            prev_signatures=[],
        )
        self.assertTrue(report["passed"], f"Quality evaluation should pass after auto-improvement: {report}")
        self.assertEqual(len(report["criteria"]), 8)
        self.assertTrue(all(report["criteria"].values()))
        self.assertGreaterEqual(len(improved.get("elements", [])), 6)
        self.assertGreaterEqual(len(improved.get("svg_layers", [])), 1)
        self.assertIn("scene_spec", improved)

    def test_cross_scene_uniqueness_and_tsx_generation(self):
        script = {
            "title": "أكبر مدن العالم عبر التاريخ",
            "hook": {"narration": "هل تساءلت يوماً كيف نشأت أعظم الحواضر المليونية على كوكب الأرض؟", "on_screen": "أعظم الحواضر"},
            "lead": {"narration": "تطورت المدن من تجمعات زراعية صغيرة إلى شبكات ذكية عابرة للقارات.", "on_screen": "تطور الشبكات الحضرية"},
            "body1": {"narration": "تتصدر طوكيو القائمة بأكثر من 37 مليون نسمة في أفق عمراني مذهل.", "on_screen": "طوكيو في الصدارة"},
            "open_loop1": {"narration": "لكن المفاجأة الحقيقية تكمن في صعود المدن الآسيوية المتسارع.", "on_screen": "صعود آسيا"},
            "body2": {"narration": "بينما تتنافس دلهي وشنغهاي في الكثافة السكانية مقابل نيويورك في القوة المالية.", "on_screen": "منافسة العمالقة"},
            "open_loop2": {"narration": "فكيف ستبدو خريطة المدن العملاقة في المستقبل القريب؟", "on_screen": "مدن المستقبل"},
            "body3": {"narration": "بحلول عام 2050 ستعيش 68% من البشرية داخل منظومات حضرية مترابطة.", "on_screen": "عالم 2050"},
            "cta": {"narration": "شاركنا في التعليقات اسم مدينتك المفضلة واشترك لمتابعة المزيد.", "on_screen": "شاركنا رأيك"},
        }
        tsx_path = ROOT / "remotion" / "src" / "generated" / "DynamicScenes.tsx"
        from pipeline.storyteller import restore_dynamic_scenes, snapshot_dynamic_scenes
        prev_tsx = snapshot_dynamic_scenes()  # index + one file per scene
        try:
            directed = apply_beats(script, {})
            scene_ids = ["hook", "lead", "body1", "open_loop1", "body2", "open_loop2", "body3", "cta"]

            specs_found = 0
            canvas_envs = []
            for sid in scene_ids:
                beats = directed[sid].get("beats", [])
                self.assertTrue(len(beats) >= 1)
                for b in beats:
                    self.assertIn("scene_spec", b, f"Beat in {sid} missing scene_spec")
                    specs_found += 1
                    if b.get("kind") in ("generative_canvas", "custom_scene"):
                        canvas_envs.append((b.get("bg_mood"), b.get("environment"), b.get("accent")))

            self.assertGreaterEqual(specs_found, 8)
            # Verify no two generative_canvas beats share the exact same (bg_mood, environment, accent) tuple
            if len(canvas_envs) > 1:
                self.assertEqual(len(canvas_envs), len(set(canvas_envs)), "Canvas scenes must not repeat identical mood/environment/accent")

            # Verify DynamicScenes.tsx exists and contains DYNAMIC_SCENE_REGISTRY
            self.assertTrue(tsx_path.exists())
            tsx_content = tsx_path.read_text(encoding="utf-8")
            self.assertIn("DYNAMIC_SCENE_REGISTRY", tsx_content)
            for tid in re.findall(r"from './scenes/(\w+)'", tsx_content):  # every registered scene has its file
                self.assertTrue((tsx_path.parent / "scenes" / f"{tid}.tsx").exists(), tid)
        finally:
            restore_dynamic_scenes(prev_tsx)


if __name__ == "__main__":
    unittest.main()

