"""Re-render a job after editing its authored scenes.
Scene files live in outputs/<job>/scenes/s_*.tsx (the source of truth for that job): edit one, then
    python scripts/rerender_authored.py outputs/<job>            -> outputs/<job>/short_edited.mp4
The job's spec.json already references them; the files are synced into remotion/src/authored for the render only.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import rem  # noqa: E402


def main() -> int:
    job = Path(sys.argv[1]).resolve()
    spec = json.loads((job / "spec.json").read_text(encoding="utf-8"))
    spec["authored_dir"] = str(job / "scenes")
    audio = job / "audio_all.wav"
    out = job / "short_edited.mp4"
    rem.render_video(spec, str(out), str(job), str(audio) if audio.exists() else None, progress=lambda f: print(f"\r{f:.0%}", end=""))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
