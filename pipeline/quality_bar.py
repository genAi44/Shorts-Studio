"""Quality bar: measure a finished short against the user's reference videos (C:/Users/<you>/Desktop/references + GeoLoop).

Three numbers that separate the references from our weak renders (measured 2026-11-27 on the 9 reference videos):
  motion       mean absolute frame difference at 10 fps (0-255 luma)   references 3.4 .. 13.8   (our weak render: 1.05)
  still_pct    share of frames that barely change (diff < 0.6)          references 2 .. 13 %     (our weak render: 54 %)
  luma         mean brightness                                          references 90 .. 217     (our weak render: 22)
Writes outputs/<job>/quality_bar.json and contact_sheet.jpg (a frame every 2 s) so every run can be compared by eye too.
Run on any video:  python -m pipeline.quality_bar path/to/short.mp4 [reference_dir]
"""
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# band measured on the references; a render outside it is flagged (not blocked)
BAND = {"motion": (3.0, 14.0), "still_pct": (0.0, 15.0), "luma": (90.0, 225.0)}


def _yavg(video: str, vf: str) -> list:
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", video, "-vf", f"{vf},signalstats,metadata=print:key=lavfi.signalstats.YAVG",
                        "-an", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return [float(x) for x in re.findall(r"YAVG=([0-9.]+)", r.stderr)]


def measure(video: str) -> Dict[str, float]:
    diff = _yavg(video, "fps=10,scale=180:-1,format=gray,tblend=all_mode=difference")
    luma = _yavg(video, "fps=2,scale=180:-1")
    return {"motion": round(sum(diff) / max(1, len(diff)), 2),
            "still_pct": round(100 * sum(1 for d in diff if d < 0.6) / max(1, len(diff)), 1),
            "luma": round(sum(luma) / max(1, len(luma)), 1)}


def compare(m: Dict[str, float]) -> Dict[str, Any]:
    issues = []
    for k, (lo, hi) in BAND.items():
        if not lo <= m[k] <= hi:
            issues.append(f"{k}={m[k]} outside the reference band {lo}..{hi}")
    return {"metrics": m, "band": BAND, "passed": not issues, "issues": issues}


def contact_sheet(video: str, out: str, every_s: float = 2.0) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps=1/{every_s},scale=180:-1,tile=8x4",
                    "-frames:v", "1", out], check=False)


def report(job_dir: str, video: Optional[str] = None) -> Dict[str, Any]:
    video = video or str(Path(job_dir) / "short.mp4")
    rep = compare(measure(video))
    contact_sheet(video, str(Path(job_dir) / "contact_sheet.jpg"))
    (Path(job_dir) / "quality_bar.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


if __name__ == "__main__":
    v = sys.argv[1]
    print(json.dumps(compare(measure(v)), ensure_ascii=False, indent=1))
    if len(sys.argv) > 2:
        for ref in sorted(Path(sys.argv[2]).glob("*.mp4")):
            print(ref.name[:40], measure(str(ref)))
