"""جسر Remotion: يبني مواصفة الفيديو (JSON) من السكربت والستايل والتوقيت، ويشغّل الرندر عبر Node."""
import copy
import glob
import json
import math
import os
import shutil
import subprocess

import numpy as np

from . import direct, sfx as _sfx
from . import icons as _icons
from .config import ROOT, FPS

REM = ROOT / "remotion"
OVERLAP = 8  # إطارات تتداخل فيها نهاية مقطع مع بداية التالي

# توليد SFX في public/ عند أول استيراد (للمعاينة في Studio)
try:
    _sfx.ensure_sfx(str(REM / "public"))
except Exception:
    pass


class RemError(Exception):
    pass


def available():
    return bool(shutil.which("node")) and (REM / "node_modules" / "remotion").exists()


def find_browser():
    if os.environ.get("REMOTION_BROWSER"):
        return os.environ["REMOTION_BROWSER"]
    for pat in ("/opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell",
                "/opt/pw-browsers/chromium_headless_shell-*/*/headless_shell"):
        m = sorted(glob.glob(pat))
        if m:
            return m[-1]
    return None


# ------------------------------------------------------------------ خريطة -> مسارات SVG
def _d(xy, min_d=2.0):
    out, last = [], None
    for x, y in xy:
        if last is None or (x - last[0]) ** 2 + (y - last[1]) ** 2 >= min_d ** 2:
            out.append((x, y))
            last = (x, y)
    if len(out) < 3:
        return ""
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in out) + "Z"


_MAP_VIEW_CACHE: dict = {}


def map_view(geo, beat):
    hl = [c for c in (beat.get("highlight") or beat.get("countries") or []) if geo.has(c)]
    extra = [c for c in (beat.get("countries") or []) if geo.has(c)]
    pts = [p for p in (beat.get("points") or []) if "lat" in p and "lon" in p]
    cache_key = (
        tuple(hl),
        tuple(extra),
        tuple((round(float(p["lat"]), 3), round(float(p["lon"]), 3), str(p.get("name") or ""), bool(p.get("dot"))) for p in pts),
    )
    if cache_key in _MAP_VIEW_CACHE:
        import copy as _copy
        return _copy.deepcopy(_MAP_VIEW_CACHE[cache_key])
    v = geo.view_for(list(dict.fromkeys(extra + hl)), pts)
    S, K, lonc, latc = v["S"], v["K"], v["lonc"], v["latc"]
    CY = 870

    # حماية الدبابيس من التصادم مع شريط العنوان (HEADLINE_ZONE ينتهي عند 440px)
    if pts:
        min_proj_y = min(CY - (float(p["lat"]) - latc) * S for p in pts)
        if min_proj_y < 540:
            shift_y = 540 - min_proj_y
            CY = min(CY + shift_y, 1000)

    def proj(a):
        a = np.asarray(a, np.float64)
        return np.stack([540 + (a[:, 0] - lonc) * S * K, CY - (a[:, 1] - latc) * S], 1)

    hw, hh = 700 / (S * K), 1500 / S
    win = (lonc - hw, latc - hh, lonc + hw, latc + hh)

    def sect(b):
        return not (b[2] < win[0] or b[0] > win[2] or b[3] < win[1] or b[1] > win[3])

    def country_d(iso):
        c = geo.c[iso]
        parts = []
        for poly, bb in zip(c["polys"], c["bbs"]):
            if not sect(bb):
                continue
            if (bb[2] - bb[0]) * S * K < 3 and (bb[3] - bb[1]) * S < 3:
                continue
            for ring in poly:
                parts.append(_d(proj(ring)))
        return "".join(p for p in parts if p)

    ctx = "".join(country_d(iso) for iso in geo.c if iso not in hl)
    hls = []
    SMALL_PX = 60  # عتبة البكسل للكيانات الصغيرة (تشغّل عدسة التكبير)
    for iso in hl:
        bb = geo.main_bbox(iso)
        (x0, y0), (x1, y1) = proj([[bb[0], bb[1]], [bb[2], bb[3]]])
        cx, cy = round((x0 + x1) / 2, 1), round((y0 + y1) / 2, 1)
        bw, bh = abs(x1 - x0), abs(y1 - y0)
        is_small = bool(bw < SMALL_PX or bh < SMALL_PX)
        entry = {"iso": iso, "d": country_d(iso), "cx": cx, "cy": cy, "small": is_small}
        if is_small:
            entry["vz"] = round(max(max(bw, bh) * 4, 20), 1)
        hls.append(entry)

    neighbours = []
    for iso in geo.c:
        if iso not in hl and sect(geo.main_bbox(iso)):
            d = country_d(iso)
            if d:
                cbb = geo.main_bbox(iso)
                (nx0, ny0), (nx1, ny1) = proj([[cbb[0], cbb[1]], [cbb[2], cbb[3]]])
                neighbours.append({"iso": iso, "d": d, "cx": round((nx0 + nx1) / 2, 1), "cy": round((ny0 + ny1) / 2, 1), "name": geo.c[iso].get("name", iso)})

    placed, ptsv = [], []
    for p in pts:
        x, y = proj([[float(p["lon"]), float(p["lat"])]])[0]
        side = -1
        for _ in range(2):
            ly = y + side * 85
            if all(abs(ly - q[1]) > 75 or abs(x - q[0]) > 340 for q in placed):
                break
            side = 1
        ly = y + side * 85
        placed.append((x, ly))
        ptsv.append({"name": p.get("name", ""), "x": round(x, 1), "y": round(y, 1), "ly": round(ly, 1), "dot": p.get("dot", True)})

    target = None
    if ptsv:
        target = {"x": ptsv[0]["x"], "y": ptsv[0]["y"]}
    elif hls:
        target = {"x": hls[0]["cx"], "y": hls[0]["cy"]}

    res_view = {"ctx": ctx, "hl": hls, "pts": ptsv, "target": target, "neighbours": neighbours[:12]}
    _MAP_VIEW_CACHE[cache_key] = res_view
    return res_view


# ------------------------------------------------------------------ نقاط الإشارة (Cue-Point Orchestrator)
def _make_cues(kind: str, fps: int, visual_mode: str = "") -> list:
    """Generate cascading reveal cues (frame offsets from beat start).
    Components read beat.cues[type] to stagger their entrances.
    Now includes cinematographic cues for dynamic background lighting."""
    f = fps
    cues = [
        {"frame": 0,              "type": "bg_enter"},
        {"frame": round(0.15 * f), "type": "lighting_ambient"},
        {"frame": round(0.2 * f), "type": "badge_slide"},
        {"frame": round(0.6 * f), "type": "secondary_enter"},
    ]
    # Cinematographic lighting cues based on visual mode
    if visual_mode in ("historical_photo", "modern_photo"):
        cues.append({"frame": round(0.3 * f), "type": "photo_reveal"})
        cues.append({"frame": round(0.7 * f), "type": "photo_focus"})
    elif visual_mode in ("battle_map", "map_zoom"):
        cues.append({"frame": round(0.25 * f), "type": "map_overlay"})
        cues.append({"frame": round(0.5 * f), "type": "battle_intensity"})
    elif visual_mode in ("comparison_chart", "split_diagram"):
        cues.append({"frame": round(0.35 * f), "type": "split_reveal"})
        cues.append({"frame": round(0.6 * f), "type": "comparison_flash"})
    elif visual_mode == "timeline":
        cues.append({"frame": round(0.25 * f), "type": "time_rise"})
        cues.append({"frame": round(0.55 * f), "type": "era_flash"})
    elif visual_mode == "stat_infographic":
        cues.append({"frame": round(0.4 * f), "type": "metric_start"})
        cues.append({"frame": round(0.8 * f), "type": "metric_punch"})
    elif visual_mode in ("cinematic_dramatic", "architectural_blueprint", "celestial_constellation", "kinetic_wave_field", "radial_light_cathedral", "topographic_contour"):
        cues.append({"frame": round(0.25 * f), "type": "cinematic_enter"})
        cues.append({"frame": round(0.45 * f), "type": "lighting_key_fill"})
        cues.append({"frame": round(0.75 * f), "type": "cinematic_release"})
    if kind in ("stat", "stat_ring_v2", "bars", "bigtext"):
        cues.append({"frame": round(0.4 * f), "type": "metric_start"})
        cues.append({"frame": round(0.8 * f), "type": "metric_punch"})
    if kind in ("map", "map_pin"):
        cues.append({"frame": round(0.15 * f), "type": "zoom_city"})
        cues.append({"frame": round(0.45 * f), "type": "pin_drop"})
        cues.append({"frame": round(0.70 * f), "type": "ripple"})
    if kind in ("canvas", "icons"):
        cues.append({"frame": round(0.4 * f),  "type": "icon_drop"})
        cues.append({"frame": round(0.65 * f), "type": "arrow_draw"})
    if kind == "elevation_profile":
        cues.append({"frame": round(0.3 * f), "type": "sea_line"})
        cues.append({"frame": round(0.5 * f), "type": "metric_start"})
        cues.append({"frame": round(0.85 * f), "type": "metric_punch"})
    if kind == "line_chart":
        cues.append({"frame": round(0.25 * f), "type": "grid_enter"})
        cues.append({"frame": round(0.4 * f), "type": "line_draw"})
        cues.append({"frame": round(0.75 * f), "type": "dots_pop"})
    if kind == "pie_chart":
        cues.append({"frame": round(0.2 * f), "type": "seg_enter"})
        cues.append({"frame": round(0.65 * f), "type": "labels_enter"})
    return cues


# ------------------------------------------------------------------ مقاطع المشهد بالتوقيت
def scene_beats(scene, words, dur_frames, geo, hook_first=None, photo=None, degrade=True, visual_mode=""):
    """يقسّم الجمل على توقيت الكلمات: كل مقطع يبدأ عند نطق أول كلمة في جملته."""
    if scene["role"] == "loop":
        b = copy.deepcopy(hook_first) if hook_first else {"kind": "custom_scene", "text": "…"}
        if hook_first and hook_first.get("tsx_id"):
            b["tsx_id"] = f"{hook_first['tsx_id']}_loop"
        b["narration"] = scene.get("narration") or (hook_first.get("narration", "") if hook_first else "")
        b["role"] = "loop"
        b.update({"from": 0, "dur": dur_frames, "settled": True})
        return [b]
    beats = direct.beats_for_scene(scene, geo)
    # توصيل الأنماط البصرية السينمائية الجديدة إلى مسار الاختيار: إذا كان visual_mode سينمائياً ولم يكن kindSinema، نحول إلى custom_scene مع scene_spec.cinematic و lighting.
    _cinematic_modes = {"cinematic_dramatic", "architectural_blueprint", "celestial_constellation", "kinetic_wave_field", "radial_light_cathedral", "topographic_contour"}
    _cinematic_lighting = {
        "cinematic_dramatic": "dramatic",
        "architectural_blueprint": "soft-top",
        "celestial_constellation": "deep-space",
        "kinetic_wave_field": "cool-flow",
        "radial_light_cathedral": "radial-core",
        "topographic_contour": "earth-tones",
    }
    if len(beats) == 1 and isinstance(beats[0], dict) and beats[0].get("tsx_id"):
        starts = [0]
        sents = [scene.get("narration", "")]
    else:
        groups = direct.sentence_groups(scene["narration"])
        ntok = sum(len(g) for g in groups)
        starts = []
        for i, g in enumerate(groups):
            if i == 0:
                starts.append(0)
                continue
            wi = min(g[0], len(words) - 1) if len(words) == ntok else min(int(g[0] / max(ntok, 1) * len(words)), len(words) - 1)
            starts.append(max(int(round(words[wi]["s"] * FPS)) - 3, starts[-1] + 14))
        sents = direct.sentences(scene["narration"])
    out = []
    for i, b in enumerate(beats):
        sent_text = sents[i] if i < len(sents) else (b.get("narration") or scene.get("narration", ""))
        orig_tsx_id = b.get("tsx_id")
        orig_title = b.get("title")
        orig_spec = b.get("scene_spec")
        orig_concept = b.get("concept")
        orig_ctx = {k: b[k] for k in ("video_title", "facts_summary", "video_countries", "video_cities", "narration_cues") if k in b}
        if b["kind"] == "photo":
            if photo:
                sc_vi = scene.get("_vi") if isinstance(scene.get("_vi"), dict) else None
                try:
                    b = photo(b, sent_text, vi_scene=sc_vi)
                except TypeError:
                    b = photo(b, sent_text)
            elif degrade:
                b = direct.photo_to_text(b, sent_text)
                if b.get("kind") in ("map", "map_pin"):
                    b = {"kind": "bigtext", "title": orig_title or "", "text": direct._words(sent_text, 6)}
                if orig_tsx_id:
                    b["tsx_id"] = orig_tsx_id
                    b["kind"] = "custom_scene"
                if orig_title and not b.get("title"):
                    b["title"] = orig_title
                if orig_spec and not b.get("scene_spec"):
                    b["scene_spec"] = orig_spec
                if orig_concept and not b.get("concept"):
                    b["concept"] = orig_concept
                for ck, cv in orig_ctx.items():
                    if ck not in b:
                        b[ck] = cv
            # بلا محلّل وبلا تحويل (معاينة): يبقى photo بمكان محجوز
        fr = starts[i]
        end = starts[i + 1] + OVERLAP if i + 1 < len(starts) else dur_frames
        b = dict(b)
        b["narration"] = b.get("narration") or sent_text
        b["role"] = b.get("role") or scene.get("role", "body")
        for ck, cv in orig_ctx.items():
            if ck not in b:
                b[ck] = cv
        if orig_tsx_id and not b.get("tsx_id"):
            b["tsx_id"] = orig_tsx_id
        if b.get("kind") in ("map", "map_pin", "photo"):
            b.pop("tsx_id", None)
        if b["kind"] == "map":
            b["view"] = map_view(geo, b)
        elif b["kind"] == "map_pin":
            # Use scene's visual data (has lat/lon + ISO codes) to build a real GeoJSON view
            vis = scene.get("visual", {})
            if vis.get("countries") or vis.get("points"):
                b["view"] = map_view(geo, vis)
        if visual_mode in _cinematic_modes and b["kind"] not in _cinematic_modes and b.get("kind") != "custom_scene":
            b = dict(b)
            b["kind"] = "custom_scene"
            b["scene_spec"] = b.get("scene_spec") or {}
            if not isinstance(b["scene_spec"], dict):
                b["scene_spec"] = {}
            b["scene_spec"]["cinematic"] = visual_mode
            lit = _cinematic_lighting.get(visual_mode)
            if lit:
                b["scene_spec"]["lighting"] = lit
            b["scene_spec"]["approach"] = b.get("approach") or f"سينما {visual_mode}"
        b.update({"from": fr, "dur": max(end - fr, 12), "cues": _make_cues(b["kind"], FPS, visual_mode or "")})
        out.append(b)
    return out


def build_spec(script, style, plan, total_frames, geo, audio_name="audio.wav", photo=None, degrade=True, only_scene_idx=None):
    """plan: [{sc, audio:{words:[(w,s,e)]}, dur, t0}] من run.plan_scenes."""
    from . import visual_tools
    from .geo_overlay import build_scene_map_overlay
    scenes, hook_first = [], None
    prev_map_overlay = None
    seed = int(style.get("seed", 42)) if isinstance(style, dict) else 42
    icon_sets = ["lucide", "ph", "tabler"]
    preferred_icon_set = icon_sets[seed % len(icon_sets)]
    transitions = visual_tools.pick_transitions(len(plan), seed=seed)

    for idx, p in enumerate(plan):
        sc = p["sc"]
        dur = int(round(p["dur"] * FPS))
        words = [{"t": w, "s": round(s, 3), "e": round(e, 3)} for (w, s, e) in p["audio"]["words"]]
        sc_vi = sc.get("_vi") if isinstance(sc.get("_vi"), dict) else {}
        beats = scene_beats(sc, words, dur, geo, hook_first, photo, degrade, visual_mode=sc_vi.get("visual_mode", ""))
        if sc["role"] == "hook":
            # first frame must be thumbnail-quality; settle beat[0] so springs render at full state
            if beats:
                beats[0] = dict(beats[0])
                beats[0]["settled"] = True
            hook_first = beats[0] if beats else None
        visuals = visual_tools.enrich_scene_visuals(sc, scene_index=idx, preferred_icon_set=preferred_icon_set)
        entities = []
        try:
            from .entity_timeline import apply_entity_flags, build_entity_timeline
            entities = build_entity_timeline(sc, words, dur)
            visuals = apply_entity_flags(visuals, entities, scene_index=idx)
        except Exception as _ent_err:
            import logging as _log
            _log.getLogger("pipeline.rem").warning("Entity timeline failed for %s: %s", sc.get("id"), _ent_err)
        transition = sc.get("transition") if isinstance(sc.get("transition"), dict) else transitions[idx]
        map_overlay = None
        try:
            sc_vi = sc.get("_vi") if isinstance(sc.get("_vi"), dict) else {}
            inh_locs = sc_vi.get("explicit_and_inherited_locations") or []
            map_overlay = build_scene_map_overlay(
                sc, words, dur, geo=geo, scene_idx=idx, prev_overlay=prev_map_overlay,
                inherited_locations=inh_locs,
            )
            if map_overlay:
                prev_map_overlay = map_overlay
        except Exception:
            map_overlay = None
        sc_vi = sc.get("_vi") if isinstance(sc.get("_vi"), dict) else {}
        scene_obj = {
            "id": sc["id"],
            "role": sc["role"],
            "from": int(round(p["t0"] * FPS)),
            "dur": dur,
            "words": words,
            "beats": beats,
            "visuals": visuals,
            "entities": entities,
            "transition": transition,
            "map_overlay": map_overlay,
            "visual_mode": sc_vi.get("visual_mode"),
            "is_historical": bool(sc_vi.get("is_historical")),
            "sfx_cue": sc_vi.get("sfx_cue"),
        }
        try:
            from .layout_planner import plan_scene_slots
            scene_obj = plan_scene_slots(scene_obj)
        except Exception as _lp_err:
            import logging as _log
            _log.getLogger("pipeline.rem").warning("Slot planner failed for %s: %s", sc.get("id"), _lp_err)
        scenes.append(scene_obj)
        # التحقق الإلزامي من وجود الخريطة عند ذكر دولة/مدينة/عاصمة/قارة/حدث جغرافي
        if sc_vi.get("needs_map_overlay") and not map_overlay and not any(b.get("kind") == "map" for b in beats):
            import logging as _log
            _log.getLogger("pipeline.rem").warning(
                "Mandatory map rule: scene %s (%s) requires geographic map but map_overlay is None",
                sc.get("id"), sc_vi.get("explicit_and_inherited_locations"),
            )
    try:
        from .storyteller import generate_dynamic_tsx_file
        all_tsx_beats = [
            b for sc_item in scenes for b in (sc_item.get("beats") or [])
            if isinstance(b, dict) and (b.get("tsx_id") or b.get("kind") in ("generative_canvas", "custom_scene"))
        ]
        if all_tsx_beats:
            only_set = {only_scene_idx} if only_scene_idx is not None else None
            generate_dynamic_tsx_file(all_tsx_beats, only_indices=only_set)
    except Exception as _tsx_err:
        import logging as _log
        _log.getLogger("pipeline.rem").exception("Dynamic TSX generation failed: %s", _tsx_err)
    return {"fps": FPS, "width": 1080, "height": 1920, "total": total_frames, "audio": audio_name, "style": style,
            "scenes": scenes}


# ------------------------------------------------------------------ تشغيل Node
def make_public(pub, audio_wav=None):
    os.makedirs(os.path.join(pub, "fonts"), exist_ok=True)
    for f in glob.glob(str(ROOT / "data" / "*.ttf")):
        shutil.copy(f, os.path.join(pub, "fonts"))
    if (REM / "public" / "grain.png").exists():
        shutil.copy(REM / "public" / "grain.png", pub)
    for asset_folder in ("icons", "maps", "emoji", "flags", "lottie", "sfx"):
        src_folder = REM / "public" / asset_folder
        if src_folder.exists():
            shutil.copytree(src_folder, os.path.join(pub, asset_folder), dirs_exist_ok=True)
    _sfx.ensure_sfx(pub)
    if audio_wav:
        shutil.copy(audio_wav, os.path.join(pub, "audio.wav"))


def _run(cmd, progress=None):
    if not available():
        raise RemError("Remotion غير جاهز: ثبّت Node.js 18+ ثم شغّل «npm install» داخل مجلد remotion.")
    env = dict(os.environ)
    b = find_browser()
    if b:
        env["REMOTION_BROWSER"] = b
    p = subprocess.Popen(cmd, cwd=str(REM), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    tail = []
    for line in p.stdout:
        line = line.strip()
        try:
            j = json.loads(line)
            if progress and "progress" in j:
                progress(float(j["progress"]))
            continue
        except Exception:
            tail.append(line)
            tail = tail[-50:]
    if p.wait() != 0:
        raise RemError("فشل رندر Remotion:\n" + "\n".join(tail[-50:]))


def render_video(spec, out_mp4, work_dir, audio_wav, progress=None):
    work_dir = os.path.abspath(work_dir)
    out_mp4 = os.path.abspath(out_mp4)
    pub = os.path.join(work_dir, "public")
    make_public(pub, audio_wav)
    spec = _icons.sanitize_spec_assets(copy.deepcopy(spec))
    sp = os.path.join(work_dir, "spec.json")
    json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
    _run(["node", "render.mjs", sp, out_mp4, pub], progress)
    shutil.rmtree(pub, ignore_errors=True)


def render_still(spec, out_jpg, frame, work_dir):
    """frame: رقم أو قائمة مفصولة بفواصل مع %d في اسم الملف."""
    work_dir = os.path.abspath(work_dir)
    out_jpg = os.path.abspath(out_jpg)
    pub = os.path.join(work_dir, "public")
    make_public(pub, None)
    spec = _icons.sanitize_spec_assets(copy.deepcopy(spec))
    sp = os.path.join(work_dir, "spec_still.json")
    json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
    _run(["node", "still.mjs", sp, out_jpg, str(frame), pub])
    shutil.rmtree(pub, ignore_errors=True)
