"""Phase 5 — Automated Visual QA Gate regression tests."""
import json
import tempfile
import unittest
from pathlib import Path

from pipeline.visual_qa import audit_spec


class TestVisualQA(unittest.TestCase):
    def test_clean_spec_passes_with_100_score_and_writes_report(self):
        spec = {
            "scenes": [
                {
                    "id": "body1",
                    "entities": [{"iso2": "pa", "from": 0, "to": 120}],
                    "beats": [
                        {"kind": "photo", "slot": "STAGE_A", "from": 0, "dur": 60},
                        {"kind": "photo", "slot": "STAGE_A", "from": 60, "dur": 60},
                    ],
                    "visuals": [{"kind": "flag", "spec": {"code": "PA"}}],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            rep = audit_spec(spec, job_dir=tmp, check_pixels=False)
            self.assertTrue(rep["passed"])
            self.assertEqual(rep["average_score"], 100.0)
            qa_file = Path(tmp) / "qa_report.json"
            self.assertTrue(qa_file.exists())
            loaded = json.loads(qa_file.read_text(encoding="utf-8"))
            self.assertTrue(loaded["passed"])

    def test_detects_slot_overlap_and_flag_mismatch(self):
        spec = {
            "scenes": [
                {
                    "id": "body2",
                    "entities": [{"iso2": "pa", "from": 0, "to": 120}],
                    "beats": [
                        {"kind": "photo", "slot": "FULL_STAGE", "from": 0, "dur": 90},
                        {"kind": "photo", "slot": "FULL_STAGE", "from": 60, "dur": 60},
                    ],
                    "visuals": [{"kind": "flag", "spec": {"code": "EG"}}],
                }
            ]
        }
        rep = audit_spec(spec, check_pixels=False)
        self.assertFalse(rep["passed"])
        issue_types = {i["type"] for i in rep["scenes"][0]["issues"]}
        self.assertIn("slot_overlap", issue_types)
        self.assertIn("flag_entity_mismatch", issue_types)


if __name__ == "__main__":
    unittest.main()
