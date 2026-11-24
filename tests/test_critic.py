"""Phase 0 critic: the deterministic layer must catch a static/empty scene and a repeated scene, and the calibration
label parser must read FRAME_REVIEW.md rows."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

from pipeline import critic


class TestCriticMetrics(unittest.TestCase):
    def test_static_runs_and_rhythm(self):
        self.assertEqual(critic.longest_static(np.array([1, 0, 0, 0, 1, 0])), 0.3)
        self.assertEqual(critic.monotone_runs([3, 3.1, 3, 2.9, 8, 2]), [0])
        self.assertEqual(critic.monotone_runs([3, 6, 3, 6]), [])

    def test_label_parser_skips_obsolete_photo_rule(self):
        md = ("| v1_001 | x | سليم | — |\n| v1_002 | x | **مصباح** لا علاقة له | كبيرة |\n"
              "| v2_007 | x | **انتهاك القاعدة 1.1 (فكتور فقط)** — صورة حقيقية | كبيرة |\n| v1_003 | x | تكرار | صغيرة |\n")
        self.assertEqual(critic.parse_labels(md), {"v1_001": "ok", "v1_002": "major", "v1_003": "minor"})

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg missing")
    def test_video_with_empty_static_scene_and_a_repeat(self):
        # scenes: a (moving test pattern) | b (flat colour: empty and static) | c (the same pattern as a: a repeat)
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            src = "testsrc2=size=1080x1920:rate=30:duration=2"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", src, "-f", "lavfi", "-i", "color=c=0x202020:size=1080x1920:rate=30:duration=2",
                            "-f", "lavfi", "-i", src, "-filter_complex", "[0][1][2]concat=n=3:v=1", "-pix_fmt", "yuv420p", str(job / "short.mp4")],
                           check=True)
            meta = {"title": "t", "duration": 6, "scenes": [{"id": "a", "dur": 2}, {"id": "b", "dur": 2}, {"id": "c", "dur": 2}]}
            (job / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
            rep = critic.critique_job(job, use_vision=False, log=lambda *_: None)
            by = {s["id"]: {d["type"] for d in s["defects"]} for s in rep["scenes"]}
            self.assertEqual(by["a"], set())
            self.assertTrue({"sparse", "static"} <= by["b"], by["b"])
            self.assertIn("repeat", by["c"])
            self.assertEqual(rep["passed_scenes"], 2)
            self.assertTrue((job / "critic" / "report.html").exists())


if __name__ == "__main__":
    unittest.main()
