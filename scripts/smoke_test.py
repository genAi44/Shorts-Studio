"""Visual smoke test.

Renders tests/fixtures/all_beats_spec.json (one scene per beat kind + map-overlay + LLM-scene cases, built by
scripts/build_fixture.py) at frames 1, 15, 45, 90 and 149 of every scene (the first and last frame of a scene are
its boundaries), then checks every frame:

  pixels   flat/near-uniform frame (nothing drawn)                          -> FAIL
  dom      text touching the canvas edge                                    -> FAIL   (remotion/src/layoutAudit.tsx)
  dom      two unrelated text boxes overlapping by > 25%                    -> FAIL
  dom      effective font size < 22 px (unreadable on a phone)              -> WARN

Writes outputs/smoke/report.json and contact sheets outputs/smoke/contact_NN.jpg.

Usage:  python scripts/smoke_test.py [--quick] [--scenes beat_stat,beat_bars] [--rebuild]
        --quick   frames 15 and 90 only
Exit code 1 if any FAIL.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
REMOTION = ROOT / "remotion"
FIXTURE = (ROOT / os.environ["SMOKE_FIXTURE"]).resolve() if os.environ.get("SMOKE_FIXTURE") else ROOT / "tests" / "fixtures" / "all_beats_spec.json"
OUT = ROOT / "outputs" / "smoke"
FRAMES = [1, 15, 45, 90, 149]
ENTRANCE_FRAMES = 30  # frames 1 and 15 are inside the entrance: edge/overlap there are warnings
FLAT_STD = 5.0  # grayscale std-dev of the beat zone below which a frame counts as flat


def pixel_check(path: Path) -> str | None:
    import numpy as np

    arr = np.asarray(Image.open(path).convert("L"), dtype="float32")
    zone = arr[280:1380, :]
    if float(zone.std()) < FLAT_STD:
        return f"flat frame (beat-zone std {zone.std():.1f} < {FLAT_STD})"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--scenes", default="")
    args = ap.parse_args()

    if args.rebuild or not FIXTURE.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_fixture.py")], check=True, cwd=ROOT)
    spec = json.loads(FIXTURE.read_text(encoding="utf-8"))
    only = {s for s in args.scenes.split(",") if s}
    scenes = [s for s in spec["scenes"] if not only or s["id"] in only]
    rel = [15, 90] if args.quick else FRAMES

    jobs = [(sc["id"], r, sc["from"] + r) for sc in scenes for r in rel]
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("f_*"):
        old.unlink()
    out_pat = str(OUT / "f_%d.jpg")
    print(f"rendering {len(jobs)} frames from {len(scenes)} scenes (audit on)...")
    env = dict(os.environ, AUDIT="1")
    proc = subprocess.run(["node", "still.mjs", str(FIXTURE), out_pat, ",".join(str(j[2]) for j in jobs), str(REMOTION / "public")],
                          cwd=REMOTION, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout[-1500:], proc.stderr[-1500:])
        return 2

    report, fails, warns = [], 0, 0
    for sid, rel_frame, abs_frame in jobs:
        img = OUT / f"f_{abs_frame}.jpg"
        entry = {"scene": sid, "frame": rel_frame, "abs": abs_frame, "fail": [], "warn": []}
        if not img.exists():
            entry["fail"].append("frame not rendered")
        else:
            flat = pixel_check(img)
            if flat:
                entry["fail"].append(flat)
            audit_file = Path(str(img) + ".audit.json")
            if audit_file.exists():
                aud = json.loads(audit_file.read_text(encoding="utf-8"))
                if aud.get("missing"):
                    entry["warn"].append("DOM audit produced no data")
                for it in aud.get("issues", []):
                    msg = f"{it['type']}: {it['text']!r}" + (f" x {it['other']!r}" if it.get("other") else "") + f" @{it['box']}" + (f" fs={it['fs']}" if it.get("fs") else "")
                    # entrance animations (first ~second) legitimately cross edges / overlap: judge settled frames only
                    soft = it["type"] == "tiny" or rel_frame < ENTRANCE_FRAMES
                    (entry["warn"] if soft else entry["fail"]).append(msg)
        fails += len(entry["fail"])
        warns += len(entry["warn"])
        report.append(entry)

    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    # contact sheets: 10 columns x 4 rows of 108x192 thumbnails per sheet, flagged frames outlined red
    tw, th, cols, rows = 216, 384, 8, 3
    per = cols * rows
    for si in range(0, len(report), per):
        sheet = Image.new("RGB", (tw * cols, th * rows), (12, 12, 12))
        d = ImageDraw.Draw(sheet)
        for k, e in enumerate(report[si: si + per]):
            p = OUT / f"f_{e['abs']}.jpg"
            if p.exists():
                sheet.paste(Image.open(p).resize((tw, th)), ((k % cols) * tw, (k // cols) * th))
            col = (255, 60, 60) if e["fail"] else (255, 200, 0) if e["warn"] else (80, 220, 120)
            x, y = (k % cols) * tw, (k // cols) * th
            d.rectangle([x, y, x + tw - 1, y + th - 1], outline=col, width=3)
            d.text((x + 6, y + 6), f"{e['scene'][:22]}@{e['frame']}", fill=col)
        sheet.save(OUT / f"contact_{si // per:02d}.jpg", quality=85)

    bad = [e for e in report if e["fail"]]
    print(f"\n{len(report)} frames | FAIL items: {fails} in {len(bad)} frames | WARN items: {warns}")
    for e in bad[:60]:
        print(f"FAIL {e['scene']}@{e['frame']}: " + " | ".join(m.encode('ascii', 'replace').decode() for m in e["fail"][:3]))
    print(f"report: {OUT / 'report.json'}\ncontact sheets: {OUT}")
    print("PASS" if not bad else "FAIL")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
