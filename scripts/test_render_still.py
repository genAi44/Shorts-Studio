import os
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import rem, geo, style
job_dir = ROOT / "outputs" / "20261102-231124-13360"
script = json.load(open(job_dir / "script.json", encoding="utf-8"))
st = json.load(open(job_dir / "style.json", encoding="utf-8"))

# Build dummy plan
plan = [
    {
        "sc": {
            "id": "hook",
            "role": "hook",
            "narration": "هل تعلم أن الرياض أصبحت عاصمة السعودية قبل توحيد المملكة بعقود؟",
            "on_screen": "الرياض: عاصمة السعودية؟",
            "beats": [{"kind": "icon_scene", "title": "لماذا أصبحت الرياض عاصمة السعودية؟", "center_label": "الرياض"}]
        },
        "audio": {"words": [("هل", 0.0, 0.4), ("تعلم", 0.4, 0.8), ("أن", 0.8, 1.0), ("الرياض", 1.0, 1.6), ("عاصمة", 1.6, 2.2), ("السعودية", 2.2, 3.0)]},
        "dur": 4.5,
        "t0": 0.0
    }
]

g = geo.get_geo()
spec = rem.build_spec(script, st, plan, 135, g, audio_name=None, photo=None, degrade=True)

test_out_dir = ROOT / "outputs" / "test_stills"
test_out_dir.mkdir(parents=True, exist_ok=True)
out_jpg = str(test_out_dir / "cinematic_bg_test.jpg")

print("Rendering test still frame 45...")
rem.render_still(spec, out_jpg, 45, str(test_out_dir))
print(f"Still generated: {out_jpg}, size: {os.path.getsize(out_jpg)} bytes")
