"""Phase 0 critic: grades a finished short.mp4 (not the spec, not the code) and says what is wrong, where, and which
production stage owns the defect. It only measures; it repairs nothing.

  python -m pipeline.critic outputs/<job>                 one video  -> <job>/critic/report.json + report.html
  python -m pipeline.critic --baseline outputs            every job  -> outputs/critic_baseline.json
  python -m pipeline.critic --calibrate frames docs/FRAME_REVIEW.md   vision recall vs the 71 hand-labelled frames
  add --no-vision for the deterministic metrics only, --provider gemini|freellmapi to pick the vision model.

Two layers: deterministic metrics from the decoded frames (motion, blank, flashes, rhythm, repetition, palette drift)
and a vision-model rubric per scene (6 frames + the neighbours' edge frames) plus one whole-video pass.
"""
import argparse
import html
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image

# --- deterministic thresholds (first guesses, tuned on the baseline; see docs/CRITIC.md)
GRAY_FPS, GW, GH = 10, 270, 480          # analysis proxy
STATIC_EPS = 0.35                         # mean |diff| (0-255) under which two proxy frames count as "no motion"
STATIC_MAX_S = 1.2                        # protocol: no static span longer than this
SPARSE_EDGE = 0.012                       # share of edge pixels in the beat zone under which a frame is (nearly) empty
CONTENT = (280 * GH // 1920, 1380 * GH // 1920)  # beat zone rows on the proxy
FLASH_DELTA, FLASH_MAX_PER_S = 40.0, 3
REPEAT_HAMMING = 6                        # dHash bits (of 64) under which two scene mid-frames look the same
PALETTE_DRIFT = 0.55                      # L1/2 distance of a scene's colour histogram from the video's median
SHEET_FRACTIONS = (0.10, 0.25, 0.40, 0.55, 0.75, 0.90)
PANEL_W, PANEL_H = 360, 640
OWNERS = ("concept", "layout", "style", "motion", "code")


# ------------------------------------------------------------------ decoding

def gray_frames(mp4: Path) -> np.ndarray:
    """All frames at GRAY_FPS as uint8 (N, GH, GW)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vf", f"fps={GRAY_FPS},scale={GW}:{GH},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, GH, GW)


def frame_jpeg(mp4: Path, t: float, w: int = PANEL_W) -> bytes:
    return subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(mp4), "-frames:v", "1",
                           "-vf", f"scale={w}:-2", "-f", "image2pipe", "-vcodec", "mjpeg", "-q:v", "3", "-"],
                          capture_output=True, check=True).stdout


def scene_bounds(meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    out, t = [], 0.0
    for sc in meta.get("scenes") or []:
        d = float(sc.get("dur") or 0)
        out.append({"id": sc.get("id"), "t0": t, "t1": t + d, "dur": d})
        t += d
    return out


# ------------------------------------------------------------------ deterministic metrics

def longest_static(diffs: np.ndarray) -> float:
    """Longest run (seconds) of consecutive proxy frames whose difference stays under STATIC_EPS."""
    best = run = 0
    for d in diffs:
        run = run + 1 if d < STATIC_EPS else 0
        best = max(best, run)
    return best / GRAY_FPS


def max_flashes_per_s(frames: np.ndarray) -> int:
    lum = frames.reshape(len(frames), -1).mean(1)
    jumps = np.flatnonzero(np.abs(np.diff(lum)) > FLASH_DELTA)
    return max((int(((jumps >= j) & (jumps < j + GRAY_FPS)).sum()) for j in jumps), default=0)


def edge_density(gray: np.ndarray) -> float:
    """Share of strong-gradient pixels in the beat zone: glows and gradients score ~0, real compositions >= ~0.025."""
    g = gray[CONTENT[0]:CONTENT[1]].astype(np.int16)
    return float(((np.abs(np.diff(g, axis=1))[:-1] + np.abs(np.diff(g, axis=0))[:, :-1]) > 24).mean())


def dhash(gray: np.ndarray) -> int:
    im = Image.fromarray(gray[CONTENT[0]:CONTENT[1]]).resize((9, 8), Image.BILINEAR)
    a = np.asarray(im, np.int16)
    return int("".join("1" if b else "0" for b in (a[:, 1:] > a[:, :-1]).flatten()), 2)


def color_hist(jpeg: bytes) -> np.ndarray:
    a = np.asarray(Image.open(io.BytesIO(jpeg)).convert("RGB").resize((60, 107)), np.int32) // 64
    h = np.bincount((a[..., 0] * 16 + a[..., 1] * 4 + a[..., 2]).ravel(), minlength=64).astype(float)
    return h / h.sum()


def monotone_runs(durs: List[float], tol: float = 0.15) -> List[int]:
    """Start indices of runs of > 3 consecutive scenes whose lengths are within tol of each other."""
    out, start = [], 0
    for i in range(1, len(durs) + 1):
        if i == len(durs) or abs(durs[i] - durs[i - 1]) > tol * max(durs[i], durs[i - 1], 1e-6):
            if i - start > 3:
                out.append(start)
            start = i
    return out


def metrics(mp4: Path, scenes: List[Dict[str, Any]], mids: List[bytes]) -> Dict[str, Any]:
    fr = gray_frames(mp4)
    per = []
    for sc, mid in zip(scenes, mids):
        a, b = int(sc["t0"] * GRAY_FPS), max(int(sc["t1"] * GRAY_FPS), int(sc["t0"] * GRAY_FPS) + 2)
        seg = fr[a:b].astype(np.int16)
        diffs = np.abs(np.diff(seg, axis=0)).mean((1, 2)) if len(seg) > 1 else np.zeros(1)
        midg = fr[min((a + b) // 2, len(fr) - 1)]
        per.append({"id": sc["id"], "dur": round(sc["dur"], 2), "motion_mean": round(float(diffs.mean()), 3),
                    "static_s": longest_static(diffs), "detail": round(edge_density(midg), 4),
                    "_hash": dhash(midg), "_hist": color_hist(mid)})
    med = np.median([p["_hist"] for p in per], axis=0) if per else None
    repeats = []
    for i in range(len(per)):
        p = per[i]
        p["palette_drift"] = round(float(np.abs(p.pop("_hist") - med).sum() / 2), 3)
        for j in range(i + 1, len(per)):
            dense = min(p["detail"], per[j]["detail"]) >= SPARSE_EDGE  # empty frames all hash alike
            if dense and bin(p["_hash"] ^ per[j]["_hash"]).count("1") <= REPEAT_HAMMING:
                repeats.append([p["id"], per[j]["id"]])
    for p in per:
        p.pop("_hash")
    durs = [p["dur"] for p in per]
    return {"scenes": per, "repeats": repeats, "flashes_per_s": max_flashes_per_s(fr),
            "monotone_runs": [per[i]["id"] for i in monotone_runs(durs)]}


def metric_defects(m: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {p["id"]: [] for p in m["scenes"]}
    for p in m["scenes"]:
        if p["detail"] < SPARSE_EDGE:
            out[p["id"]].append({"type": "sparse", "severity": "major", "owner": "layout",
                                 "detail": f"the beat zone is (nearly) empty at mid-scene (detail {p['detail']})"})
        if p["static_s"] > STATIC_MAX_S:
            out[p["id"]].append({"type": "static", "severity": "major" if p["static_s"] > 2 * STATIC_MAX_S else "minor",
                                 "owner": "motion", "detail": f"no visible motion for {p['static_s']:.1f}s"})
        if p["palette_drift"] > PALETTE_DRIFT:
            out[p["id"]].append({"type": "palette_drift", "severity": "minor", "owner": "style",
                                 "detail": f"colours far from the rest of the video ({p['palette_drift']})"})
    for a, b in m["repeats"]:
        # info only: on the baseline half of the flagged pairs shared a dark background, not a layout (docs/CRITIC.md)
        out[b].append({"type": "repeat", "severity": "info", "owner": "concept", "detail": f"may repeat scene {a} (pixel hash)"})
    return out


# ------------------------------------------------------------------ vision rubric

RUBRIC = """You are the senior motion-design critic of an Arabic educational Shorts studio (1080x1920 vertical video).
You judge FINISHED frames the way a demanding art director reviews a cut. Licensed photos are allowed. Do not judge
whether Arabic text is spelled correctly (you cannot read it reliably) — judge only what it looks like and where it sits.

FIRST list every defect you can see, each with the image number that proves it. THEN score. Be strict: a 3 is
"acceptable, generic", 5 is "would pass in a professional studio". Typical defects:
- relevance: the visual does not prove or express the sentence; an icon/symbol means something else (a lightbulb for
  "heritage", a star for "corruption", a rising chart for a decline); wrong place/country shown.
- hierarchy: no single hero element; everything the same size; the eye has nowhere to go.
- composition: empty or nearly empty frame; crowded; unbalanced; elements cut by the edge; text over text; text over the
  hero; bars/stripes leaking at the screen edge; leftover artefacts.
- consistency: looks like it belongs to another video (other palette, other type, other style) than its neighbours.
- motion: the 6 frames are nearly identical (nothing develops); elements jump without purpose.
- transition: the cut from the previous scene / into the next one is jarring or meaningless.
- template: a generic layout (three identical nodes, a lone card with a title) that would fit any video unchanged.
- text_only: only text on a plain ground, no graphic.

owner = the production stage that must fix it: concept (idea/metaphor/relevance), layout (positions, sizes, overlap,
empty), style (palette, type, identity), motion (movement, timing, transitions), code (rendering bug, artefact, leak).
severity: major = a viewer notices and it hurts the video; minor = a professional would fix it.
Write "detail" and "fix" in Arabic, short.

Return JSON only:
{"defects":[{"type":"relevance|hierarchy|composition|consistency|motion|transition|template|text_only|other",
 "severity":"major|minor","image":2,"owner":"concept|layout|style|motion|code","detail":"...","fix":"..."}],
 "scores":{"relevance":1-5,"hierarchy":1-5,"composition":1-5,"consistency":1-5,"motion":1-5,"transition":1-5}}"""

GLOBAL_RUBRIC = """You are the senior motion-design critic of an Arabic educational Shorts studio. Each image is the
middle frame of one scene of the SAME video, in order. Judge the video as a whole: visual identity consistency, repeated
layouts/templates, a visual arc (strong hook, escalation, a climax, an ending that echoes the opening), variety of
shot types. List defects first (with the image numbers), then score. Write "detail" and "fix" in Arabic. Return JSON only:
{"defects":[{"type":"consistency|repetition|arc|variety|other","severity":"major|minor","images":[1,4],"detail":"...","fix":"..."}],
 "scores":{"consistency":1-5,"variety":1-5,"arc":1-5}}"""


def vision(system: str, user: str, images: List[bytes], provider: Optional[str] = None) -> Any:
    from . import llm
    # the critic needs every frame at a size where icons and layout are legible (photo verification keeps 4 x 448 px)
    fns = {"gemini": llm.gemini_vision_json,
           "freellmapi": lambda s, u, im: llm.freellmapi_vision_json(s, u, im, max_images=len(im), max_side=PANEL_H)}
    order = [provider] if provider else ["gemini", "freellmapi"]
    errors = []
    for p in order:
        for _ in range(2):  # free routers fail transiently (502): one retry per provider
            try:
                r = fns[p](system, user, images)
                if isinstance(r, list):  # some free models drop the wrapper and return the defect list alone
                    r = {"defects": r}
                if not isinstance(r, dict):
                    raise ValueError(f"unexpected reply shape: {type(r).__name__}")
                r["defects"] = [d for d in r.get("defects") or [] if isinstance(d, dict)]
                return r
            except Exception as e:  # noqa: BLE001 - retry, then the next provider
                errors.append(f"{p}: {str(e)[:120]}")
    raise RuntimeError("no vision provider answered: " + " | ".join(errors))


def critique_scene(sc: Dict[str, Any], narration: str, frames: List[bytes], prev_end: Optional[bytes],
                   next_start: Optional[bytes], provider: Optional[str]) -> Dict[str, Any]:
    imgs, legend = [], []
    if prev_end:
        imgs.append(prev_end)
        legend.append(f"Image {len(imgs) - 1}: last frame of the PREVIOUS scene (context only)")
    first = len(imgs)
    imgs += frames
    legend.append(f"Images {first}-{len(imgs) - 1}: this scene at 10/25/40/55/75/90% of its length")
    if next_start:
        imgs.append(next_start)
        legend.append(f"Image {len(imgs) - 1}: first frame of the NEXT scene (context only)")
    user = (f"Scene '{sc['id']}' ({sc['dur']:.1f}s). Spoken sentence(s): {narration or '(unknown: judge from what is on screen)'}\n"
            + "\n".join(legend))
    out = vision(RUBRIC, user, imgs, provider)
    out.setdefault("defects", [])
    for d in out["defects"]:  # report image numbers relative to this scene's 6 frames when possible
        if isinstance(d.get("image"), int):
            d["image"] = d["image"] - first
    return out


# ------------------------------------------------------------------ one video

def narration_of(script: Dict[str, Any], sid: str) -> str:
    v = script.get(sid)
    return (v.get("narration") or "") if isinstance(v, dict) else ""


def critique_job(job: Path, use_vision: bool = True, provider: Optional[str] = None, log=print) -> Dict[str, Any]:
    job = Path(job)
    mp4, meta = job / "short.mp4", json.loads((job / "meta.json").read_text(encoding="utf-8"))
    script = json.loads((job / "script.json").read_text(encoding="utf-8")) if (job / "script.json").exists() else {}
    scenes = scene_bounds(meta)
    out_dir = job / "critic"
    out_dir.mkdir(exist_ok=True)
    sheets = {sc["id"]: [frame_jpeg(mp4, sc["t0"] + f * sc["dur"]) for f in SHEET_FRACTIONS] for sc in scenes}
    mids = [sheets[sc["id"]][3] for sc in scenes]
    m = metrics(mp4, scenes, mids)
    defects = metric_defects(m)
    scores: Dict[str, Dict[str, int]] = {}
    reviewed = set()
    video_review = None
    if use_vision:
        for i, sc in enumerate(scenes):
            log(f"critic: vision {sc['id']}")
            prev_end = frame_jpeg(mp4, scenes[i - 1]["t1"] - 0.1) if i else None
            next_start = frame_jpeg(mp4, scenes[i + 1]["t0"] + 0.1) if i + 1 < len(scenes) else None
            try:
                r = critique_scene(sc, narration_of(script, sc["id"]), sheets[sc["id"]], prev_end, next_start, provider)
                defects[sc["id"]] += [dict(d, source="vision") for d in r["defects"]]
                scores[sc["id"]] = r.get("scores") or {}
                reviewed.add(sc["id"])
            except Exception as e:  # noqa: BLE001 - a failed call is reported, never hidden
                defects[sc["id"]].append({"type": "critic_error", "severity": "minor", "owner": "code", "detail": str(e)[:200]})
        try:
            video_review = vision(GLOBAL_RUBRIC, f"Video '{meta.get('title', '')}', {len(mids)} scenes in order.", mids, provider)
        except Exception as e:  # noqa: BLE001
            video_review = {"error": str(e)[:200]}
    for sc in scenes:
        for k, b in enumerate(sheets[sc["id"]]):
            (out_dir / f"{sc['id']}_{k}.jpg").write_bytes(b)
    per = []
    for p in m["scenes"]:
        ds = defects[p["id"]]
        per.append({**p, "scores": scores.get(p["id"], {}), "defects": ds, "reviewed": p["id"] in reviewed or not use_vision,
                    "passed": not any(d["severity"] == "major" for d in ds if d["type"] != "critic_error")})
    rep = {"job": job.name, "title": meta.get("title"), "duration": meta.get("duration"), "vision": use_vision,
           "provider": provider or "auto", "flashes_per_s": m["flashes_per_s"], "repeats": m["repeats"],
           "monotone_runs": m["monotone_runs"], "video_review": video_review, "scenes": per,
           "passed_scenes": sum(s["passed"] and s["reviewed"] for s in per), "total_scenes": len(per),
           "unreviewed": [s["id"] for s in per if not s["reviewed"]]}  # a scene the critic could not see never counts as passed
    rep["passed"] = rep["passed_scenes"] == rep["total_scenes"] and m["flashes_per_s"] <= FLASH_MAX_PER_S
    (out_dir / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "report.html").write_text(render_html(rep), encoding="utf-8")
    return rep


def render_html(rep: Dict[str, Any]) -> str:
    e = html.escape
    rows = []
    for s in rep["scenes"]:
        imgs = "".join(f'<img src="{e(s["id"])}_{k}.jpg">' for k in range(len(SHEET_FRACTIONS)))
        ds = "".join(f'<li class="{e(d["severity"])}"><b>{e(d["type"])}</b> [{e(str(d.get("owner", "")))}]'
                     f'{" #" + str(d["image"]) if isinstance(d.get("image"), int) else ""}: {e(str(d.get("detail", "")))}'
                     f'{" ← " + e(str(d["fix"])) if d.get("fix") else ""}</li>' for d in s["defects"])
        sc = " ".join(f"{e(k)} {v}" for k, v in (s.get("scores") or {}).items())
        rows.append(f'<section class="{"ok" if s["passed"] else "bad"}"><h2>{e(s["id"])} · {s["dur"]}s · '
                    f'{("PASS" if s["passed"] else "FAIL") if s["reviewed"] else "NOT REVIEWED"}</h2><div class="m">motion {s["motion_mean"]} · static {s["static_s"]}s · detail {s["detail"]} · '
                    f'drift {s["palette_drift"]} · {sc}</div><div class="strip">{imgs}</div><ul>{ds}</ul></section>')
    vr = rep.get("video_review") or {}
    vd = "".join(f'<li class="{e(str(d.get("severity", "")))}"><b>{e(str(d.get("type", "")))}</b> {e(str(d.get("images", "")))}: '
                 f'{e(str(d.get("detail", "")))}</li>' for d in vr.get("defects", []))
    return f"""<!doctype html><html dir="auto"><meta charset="utf-8"><title>critic · {e(rep['job'])}</title>
<style>body{{font:14px system-ui;background:#111;color:#ddd;margin:24px}}section{{margin:18px 0;padding:12px;border-left:4px solid #3a3}}
section.bad{{border-color:#d33}}.strip img{{height:220px;margin-right:4px}}.m{{color:#999}}li.major{{color:#f77}}li.minor{{color:#fc6}}li.info{{color:#888}}</style>
<h1>{e(str(rep.get('title') or rep['job']))}</h1><p>{rep['passed_scenes']}/{rep['total_scenes']} scenes pass · flashes/s {rep['flashes_per_s']}
· repeats {e(str(rep['repeats']))} · monotone runs from {e(str(rep['monotone_runs']))} · video scores {e(str(vr.get('scores', '')))}</p>
<ul>{vd}</ul>{''.join(rows)}</html>"""


# ------------------------------------------------------------------ baseline over many jobs

def baseline(outputs: Path, use_vision: bool, provider: Optional[str], log=print) -> Dict[str, Any]:
    jobs = sorted(p for p in Path(outputs).iterdir() if (p / "short.mp4").exists() and (p / "meta.json").exists())
    reps, counts = [], {}
    for j in jobs:
        try:
            r = critique_job(j, use_vision, provider, log=lambda *_: None)
        except Exception as e:  # noqa: BLE001
            log(f"{j.name}: failed ({e})")
            continue
        reps.append(r)
        for s in r["scenes"]:
            for d in s["defects"]:
                if d["severity"] == "info":
                    continue
                key = f'{d["type"]}/{d["severity"]}'
                counts[key] = counts.get(key, 0) + 1
        log(f"{j.name}: {r['passed_scenes']}/{r['total_scenes']} scenes pass, {len(r['unreviewed'])} unreviewed")
    n_sc = sum(r["total_scenes"] - len(r["unreviewed"]) for r in reps)
    summary = {"videos": len(reps), "scenes_reviewed": n_sc, "scenes_unreviewed": sum(len(r["unreviewed"]) for r in reps), "scene_pass_rate": round(sum(r["passed_scenes"] for r in reps) / max(1, n_sc), 3),
               "video_pass_rate": round(sum(r["passed"] for r in reps) / max(1, len(reps)), 3),
               "defects": dict(sorted(counts.items(), key=lambda kv: -kv[1])),
               "static_s_median": float(np.median([s["static_s"] for r in reps for s in r["scenes"]] or [0])),
               "motion_mean_median": float(np.median([s["motion_mean"] for r in reps for s in r["scenes"]] or [0])),
               "jobs": [{k: r[k] for k in ("job", "passed_scenes", "total_scenes", "passed")} for r in reps]}
    (Path(outputs) / "critic_baseline.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


# ------------------------------------------------------------------ calibration on the hand-labelled frames

ROW = re.compile(r"^\|\s*(v\d_\d{3})\s*\|[^|]*\|([^|]*)\|\s*([^|]*?)\s*\|")
OBSOLETE = re.compile(r"1\.1|فوتوغرافية")  # vector-only rule: photos are allowed in this repo, those labels do not apply


def parse_labels(review_md: str) -> Dict[str, str]:
    """frame -> major | minor | ok (frames whose only defect is the obsolete photo rule are left out)."""
    out = {}
    for ln in review_md.splitlines():
        m = ROW.match(ln)
        if not m:
            continue
        frame, problem, sev = m.groups()
        if OBSOLETE.search(problem) and not re.search(r"\+|نص فقط|رقم", problem):
            continue
        out[frame] = "major" if "كبيرة" in sev else "minor" if "صغيرة" in sev else "ok"
    return out


def calibrate(frames_dir: Path, review_md: Path, provider: Optional[str], log=print) -> Dict[str, Any]:
    labels = parse_labels(review_md.read_text(encoding="utf-8"))
    pred: Dict[str, str] = {}
    by_video: Dict[str, List[str]] = {}
    for f in sorted(labels):
        by_video.setdefault(f[:2], []).append(f)
    for vid, fs in by_video.items():
        for k in range(0, len(fs), 6):  # the production format: 6 consecutive frames per call
            chunk = fs[k:k + 6]
            imgs = []
            for f in chunk:
                im = Image.open(Path(frames_dir) / f"{f}.jpg").convert("RGB")
                im.thumbnail((PANEL_W, PANEL_H))
                b = io.BytesIO()
                im.save(b, "JPEG", quality=85)
                imgs.append(b.getvalue())
            user = (f"These {len(chunk)} images are consecutive sampled frames of ONE video (not one scene). Narration unknown: "
                    "judge from what is on screen. Report every defect with the image number it is visible in.")
            try:
                r = vision(RUBRIC, user, imgs, provider)
            except Exception as e:  # noqa: BLE001
                log(f"{vid} {k}: vision failed ({e})")
                continue
            for f in chunk:
                pred.setdefault(f, "ok")
            for d in r.get("defects", []):
                i = d.get("image")
                if isinstance(i, int) and 0 <= i < len(chunk):
                    f = chunk[i]
                    if d.get("severity") == "major" or pred[f] == "ok":
                        pred[f] = "major" if d.get("severity") == "major" else "minor"
            log(f"{vid} frames {chunk[0]}..{chunk[-1]} done")
    seen = [f for f in labels if f in pred]
    major = [f for f in seen if labels[f] == "major"]
    ok = [f for f in seen if labels[f] == "ok"]
    res = {"provider": provider or "auto", "frames": len(seen),
           "major_recall": round(sum(pred[f] == "major" for f in major) / max(1, len(major)), 3),
           "major_recall_any": round(sum(pred[f] != "ok" for f in major) / max(1, len(major)), 3),
           "false_alarm_on_ok": round(sum(pred[f] == "major" for f in ok) / max(1, len(ok)), 3),
           "n_major": len(major), "n_ok": len(ok),
           "missed": [f for f in major if pred[f] == "ok"], "pred": pred, "labels": labels}
    return res


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", help="outputs/<job>, or the outputs folder with --baseline, or the frames folder with --calibrate")
    ap.add_argument("review", nargs="?", help="FRAME_REVIEW.md (with --calibrate)")
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--no-vision", action="store_true")
    ap.add_argument("--provider", choices=["gemini", "freellmapi"])
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.calibrate:
        res = calibrate(Path(a.target), Path(a.review or "docs/FRAME_REVIEW.md"), a.provider)
        print(json.dumps({k: v for k, v in res.items() if k not in ("pred", "labels")}, ensure_ascii=False, indent=1))
        Path("qa").mkdir(exist_ok=True)
        Path(f"qa/critic_calibration_{a.provider or 'auto'}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    elif a.baseline:
        s = baseline(Path(a.target), not a.no_vision, a.provider)
        print(json.dumps({k: v for k, v in s.items() if k != "jobs"}, ensure_ascii=False, indent=1))
    else:
        r = critique_job(Path(a.target), not a.no_vision, a.provider)
        print(f"{r['passed_scenes']}/{r['total_scenes']} scenes pass -> {Path(a.target) / 'critic' / 'report.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
