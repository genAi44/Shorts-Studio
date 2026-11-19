"""Unit tests for the Offline Visual Assets & Motion Elements Layer (`tests/test_visual_assets.py`)."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import visual_tools


class TestVisualAssetsLayer(unittest.TestCase):
    def test_remotion_packages_exact_version_pinned(self):
        pkg = json.loads((ROOT / "remotion" / "package.json").read_text(encoding="utf-8"))
        deps = pkg.get("dependencies", {})
        remotion_pkgs = [k for k in deps if k == "remotion" or k.startswith("@remotion/")]
        self.assertGreaterEqual(len(remotion_pkgs), 12)
        for k in remotion_pkgs:
            v = deps[k]
            self.assertFalse(v.startswith("^") or v.startswith("~"), f"{k} has non-exact version {v}")
            self.assertEqual(v, "4.0.539", f"{k} must be pinned to 4.0.539, got {v}")

    def test_docs_and_licenses_exist(self):
        self.assertTrue((ROOT / "docs" / "LINKS.md").exists())
        self.assertTrue((ROOT / "docs" / "LICENSES.md").exists())
        self.assertTrue((ROOT / "credits.json").exists())
        for skill_name in (
            "icons-emoji-flags",
            "lottie-usage",
            "animated-charts",
            "transitions-and-effects",
            "typography-components",
            "motion-design-quality",
        ):
            skill_md = ROOT / "skills" / skill_name / "SKILL.md"
            self.assertTrue(skill_md.exists(), f"Missing skill {skill_md}")
            content = skill_md.read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---\nname:"), f"Invalid frontmatter in {skill_md}")

    def test_search_icons_offline(self):
        # English search
        res = visual_tools.search_icons("landmark", set_name="lucide", limit=3)
        self.assertTrue(len(res) >= 1)
        self.assertEqual(res[0]["id"], "lucide:landmark")

        # Arabic semantic search
        res_ar = visual_tools.search_icons("هرم", set_name="lucide", limit=3)
        self.assertTrue(any(r["id"] == "lucide:pyramid" for r in res_ar))

        # Phosphor set filter
        res_ph = visual_tools.search_icons("مسجد", set_name="ph", limit=2)
        self.assertTrue(all(r["set"] == "ph" for r in res_ph))
        self.assertEqual(res_ph[0]["id"], "ph:mosque")

    def test_search_emoji_localized_and_bundled(self):
        res_ar = visual_tools.search_emoji("تاج", limit=3)
        self.assertGreaterEqual(len(res_ar), 1)
        self.assertEqual(res_ar[0]["char"], "👑")
        svg_path = ROOT / "remotion" / "public" / res_ar[0]["file"]
        self.assertTrue(svg_path.exists())

        res_en = visual_tools.search_emoji("classical building", limit=2)
        self.assertEqual(res_en[0]["char"], "🏛️")

    def test_resolve_flag_arabic_english_iso(self):
        f_eg = visual_tools.resolve_flag("مصر", shape="rect")
        self.assertEqual(f_eg["code"], "EG")
        self.assertTrue((ROOT / "remotion" / "public" / f_eg["file"]).exists())

        f_bo = visual_tools.resolve_flag("بوليفيا", shape="round")
        self.assertEqual(f_bo["code"], "BO")
        self.assertEqual(f_bo["file"], "flags/1x1/bo.svg")
        self.assertTrue((ROOT / "remotion" / "public" / f_bo["file"]).exists())

        f_iso3 = visual_tools.resolve_flag("SAU", shape="rect")
        self.assertEqual(f_iso3["code"], "SA")

    def test_search_lottie_manifest(self):
        res = visual_tools.search_lottie("صح", limit=2)
        self.assertGreaterEqual(len(res), 1)
        self.assertEqual(res[0]["id"], "checkmark")
        self.assertIn("sourceUrl", res[0])
        self.assertIn("license", res[0])
        lottie_file = ROOT / "packages" / "assets" / "lottie" / res[0]["file"]
        self.assertTrue(lottie_file.exists())

    def test_draw_chart_validation(self):
        chart = visual_tools.draw_chart({
            "type": "bar",
            "data": [{"label": "لاباز", "value": 3650}, {"label": "سوكري", "value": 2790}],
            "style": {"title": "ارتفاع العواصم", "rtl": True, "arabicNumerals": True, "unit": "م"},
            "animation": "spring",
            "durationInFrames": 90,
        })
        self.assertEqual(chart["kind"], "chart")
        self.assertEqual(chart["spec"]["type"], "bar")
        self.assertTrue(chart["spec"]["style"]["rtl"])
        self.assertTrue(chart["spec"]["style"]["arabicNumerals"])

        with self.assertRaises(ValueError):
            visual_tools.draw_chart({"type": "invalid_chart", "data": [{"label": "A", "value": 1}]})

        with self.assertRaises(ValueError):
            visual_tools.draw_chart({"type": "bar", "data": []})

    def test_pick_transitions_never_repeats_consecutively(self):
        trans = visual_tools.pick_transitions(8, seed=42)
        self.assertEqual(len(trans), 8)
        self.assertEqual(trans[0]["type"], "none")
        for i in range(2, len(trans)):
            self.assertNotEqual(
                trans[i]["type"],
                trans[i - 1]["type"],
                f"Consecutive transition repeat at {i}: {trans[i]['type']}",
            )

    def test_qa_visual_review_catches_clutter_and_emoji_spam(self):
        bad_spec = {
            "scenes": [
                {
                    "id": "hook",
                    "visuals": [
                        {"kind": "emoji", "spec": {"char": "🏛️"}},
                        {"kind": "emoji", "spec": {"char": "👑"}},
                        {"kind": "icon", "spec": {"name": "lucide:landmark"}},
                        {"kind": "flag", "spec": {"code": "EG"}},
                    ],
                }
            ]
        }
        issues = visual_tools.qa_visual_review(bad_spec)
        self.assertGreaterEqual(len(issues), 2)

    def test_chat_visual_edits(self):
        from pipeline.config import SAMPLE
        sample = json.loads(Path(SAMPLE).read_text(encoding="utf-8"))
        r1 = visual_tools.apply_chat_visual_edit(sample, "change the icon to a pyramid", scene_id="hook")
        self.assertIn("lucide:pyramid", r1["action"])
        self.assertTrue(any(v["kind"] == "icon" and v["spec"]["name"] == "lucide:pyramid" for v in r1["visuals"]))

        r2 = visual_tools.apply_chat_visual_edit(r1["script"], "use a bar chart here", scene_id="body1")
        self.assertEqual(r2["action"], "draw_chart(bar)")
        self.assertTrue(any(v["kind"] == "chart" and v["spec"]["type"] == "bar" for v in r2["visuals"]))


if __name__ == "__main__":
    unittest.main()
