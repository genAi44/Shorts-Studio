"""Authors the fixture scenes with the real LLM and the full gate (static check -> sandbox render -> automated checks).
Scenes: map, timeline, stat, person, comparison. Output: tests/fixtures/authored_spec.json + tests/fixtures/authored/*.tsx
(the accepted files are committed so the smoke test is deterministic and offline).
Usage: python scripts/build_authored_fixture.py            (needs the llm keys in .env)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("NO_NETWORK", "1")
os.environ.setdefault("DYNAMIC_TSX_LLM", "0")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from pipeline import entities, rem, scene_author  # noqa: E402
from pipeline.config import clear_warnings, get_last_warnings  # noqa: E402
from pipeline.geo import get_geo  # noqa: E402
from pipeline.style import normalize as norm_style  # noqa: E402

DUR = 6.0
FPS = 30
SCENES = [
    ("map", "القاهرة هي عاصمة مصر وأكبر مدنها على ضفاف النيل", [{"type": "place", "scale": "capital", "text": "القاهرة", "name_ar": "القاهرة", "name_en": "Cairo", "iso2": "EG", "lat": 30.06, "lon": 31.25}]),
    ("timeline", "من عام 1900 إلى عام 1950 تغيرت المدينة تغيرا كبيرا", [{"type": "time", "scale": "year", "text": "1900", "value": 1900, "to": 1950, "label_ar": "نصف قرن من التغيير"}]),
    ("stat", "يسكن المدينة اليوم مليون وثلاثمائة ألف نسمة", [{"type": "quantity", "scale": "population", "text": "مليون", "value": 1300000, "unit": "نسمة", "label_ar": "عدد السكان"}]),
    ("person", "ابن سينا طبيب وفيلسوف عاش بين 980 و1037", [{"type": "person", "text": "سينا", "name_ar": "ابن سينا", "name_en": "Avicenna", "born": 980, "died": 1037, "role_ar": "طبيب وفيلسوف"}]),
    ("comparison", "مساحة روسيا 17 مليون كيلومتر مربع وكندا 10 ملايين", [{"type": "quantity", "scale": "area", "text": "17", "value": 17, "unit": "مليون كم²", "label_ar": "مساحة روسيا", "compare": [{"label": "كندا", "value": 10}]}]),
]


def main() -> int:
    clear_warnings()
    geo = get_geo()
    plan, ents = [], {}
    for i, (sid, narr, raw) in enumerate(SCENES):
        toks = narr.split()
        words = [(w, round(0.15 + k * 0.4, 3), round(0.15 + k * 0.4 + 0.36, 3)) for k, w in enumerate(toks)]
        ents[sid] = [[v for v in (entities.validate_entity(e, narr) for e in raw) if v]]
        sc = {"id": sid, "role": "body", "narration": narr, "on_screen": toks[0], "beats": [{"kind": "bigtext", "text": " ".join(toks[:3])}]}
        plan.append({"sc": sc, "audio": {"words": words}, "dur": DUR, "t0": i * DUR})
    style = norm_style({"name": "ذهبي سينمائي", "seed": 806})
    from pipeline.storyteller import restore_dynamic_scenes, snapshot_dynamic_scenes
    backup = snapshot_dynamic_scenes()
    try:
        spec = rem.build_spec({"_entities": ents}, style, plan, int(round(len(plan) * DUR * FPS)), geo, audio_name="", photo=None, degrade=True)
    finally:
        restore_dynamic_scenes(backup)
    spec["audio"] = ""
    job = ROOT / "outputs" / "authored_fixture"
    shutil.rmtree(job, ignore_errors=True)
    job.mkdir(parents=True)
    spec = scene_author.author_spec(spec, str(job))
    rep = json.loads((job / "authoring_report.json").read_text(encoding="utf-8"))
    dest = ROOT / "tests" / "fixtures" / "authored"
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    for f in (job / "scenes").glob("s_*.tsx"):
        shutil.copyfile(f, dest / f.name)
    spec["authored_dir"] = "tests/fixtures/authored"  # repo-relative so the fixture is portable
    (ROOT / "tests" / "fixtures" / "authored_spec.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(rep["summary"], ensure_ascii=False))
    for sid, r in rep["scenes"].items():
        print(f"  {sid:<11} {r['status']:<9} attempts={r['attempts']} errors={len(r['errors'])}")
    for w in get_last_warnings():
        print("warning:", w.encode("ascii", "replace").decode()[:160])
    return 0


if __name__ == "__main__":
    sys.exit(main())
