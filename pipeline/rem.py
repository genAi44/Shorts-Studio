"""جسر Remotion: يبني مواصفة الفيديو (JSON) من السكربت والستايل والتوقيت، ويشغّل الرندر عبر Node."""
import copy
import re
import glob
import json
import os
import shutil
import subprocess

import numpy as np

from . import areamap, direct, sfx as _sfx
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


_AR_PUNCT = re.compile(r"[،؛؟.,:!?\"'()\-]")


def _norm_ar(t: str) -> str:
    t = _AR_PUNCT.sub("", str(t or "")).strip()
    return t[2:] if t.startswith("ال") and len(t) > 4 else t


def _entity_word_frame(sent_text: str, words, lo: int, hi: int):
    """Frame of the first word (in tokens lo..hi) naming the place the sentence is about, else None."""
    try:
        from .geo_overlay import extract_timed_geo_mentions
        gm = extract_timed_geo_mentions(sent_text, "", [], 150)
    except Exception:
        return None
    m0 = next((x for x in gm if x.get("kind") in ("landmark", "capital", "city", "country")), None)
    if not m0:
        return None
    want = [_norm_ar(w) for w in str(m0.get("matched_token") or m0.get("name_ar") or "").split() if w]
    want = [w for w in want if len(w) >= 3]
    if not want:
        return None
    for i in range(max(lo, 0), min(hi, len(words) - 1) + 1):
        tok = _norm_ar(words[i].get("t", ""))
        tok = tok[1:] if tok[:1] in "وبلف" and len(tok) > 4 and tok[1:] and tok not in want else tok
        if any(w == tok or (len(w) >= 4 and w in tok) for w in want):
            return int(round(words[i]["s"] * FPS))
    return None


def _align_photo_starts(beats, starts, groups, sents, words, ntok):
    """A photo of a place must appear when the place is NAMED (like its map waypoint), not at sentence start.
    Shifts a photo beat's start to the entity word (anticipation 3 frames) when that is <= 2.5 s later."""
    if len(words) != ntok:
        return
    for i, b in enumerate(beats):
        if i == 0 or i >= len(starts) or i >= len(groups) or not isinstance(b, dict) or b.get("kind") != "photo":
            continue
        fr = _entity_word_frame(sents[i] if i < len(sents) else "", words, groups[i][0], groups[i][-1])
        if fr is None:
            continue
        new = fr - 3
        limit = starts[i + 1] - 14 if i + 1 < len(starts) else new
        if 0 < new - starts[i] <= 75 and new <= limit:
            starts[i] = new


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
        _align_photo_starts(beats, starts, groups, sents, words, ntok)
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
        elif b["kind"] == "person_card" and photo and not b.get("img"):
            try:
                pb = photo({"kind": "photo", "query": b.get("query") or b.get("name"), "text": b.get("name"), "must_show": b.get("query") or b.get("name")}, sent_text)
                if isinstance(pb, dict) and pb.get("img"):
                    b["img"] = pb["img"]
            except Exception as _pe:  # noqa: BLE001
                from .config import record_fallback
                record_fallback(f"person photo unavailable ({_pe}): symbolic silhouette", beat_id="person_card")
        elif b["kind"] == "area_map":
            b["view"] = areamap.build_view(b)
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
        # entity -> visual rule: every registered entity gets its visual (insert shot if the plan missed it); places go to the overlay
        per_sentence = (script.get("_entities") or {}).get(sc["id"]) if isinstance(script, dict) else None
        entity_mentions = None
        if per_sentence:
            from . import entities as _ent
            beats = _ent.ensure_visuals(beats, per_sentence, words, dur, photo=photo)
            entity_mentions = _ent.geo_mentions(per_sentence, words, [])
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
                inherited_locations=inh_locs, entity_mentions=entity_mentions,
            )
            if map_overlay:
                prev_map_overlay = map_overlay
        except Exception as _mo_err:  # noqa: BLE001
            from .config import record_fallback
            record_fallback(f"map overlay failed for scene {sc.get('id')}: {_mo_err}", beat_id=str(sc.get("id")))
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
            "entity_plan": per_sentence or [],
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
            from .style import theme_from_style
            generate_dynamic_tsx_file(all_tsx_beats, only_indices=only_set, theme=theme_from_style(style))
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
    from .scene_author import sync_to_remotion  # authored scenes: the job's files are what gets rendered
    with sync_to_remotion(spec.get("authored_dir")):
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
    from .scene_author import sync_to_remotion  # same files as the final render
    with sync_to_remotion(spec.get("authored_dir")):
        _run(["node", "still.mjs", sp, out_jpg, str(frame), pub])
    shutil.rmtree(pub, ignore_errors=True)

# Re-exported so `pipeline.rem.<name>` keeps working.
from .rem_map import (  # noqa: E402,F401
    _MAP_VIEW_CACHE,
    _d,
    _make_cues,
    map_view,
)
