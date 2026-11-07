"""خط الإنتاج: سكربت + ستايل ← صوت لكل مشهد ← رسم المشاهد (Remotion أو PIL احتياطاً) ← mp4."""
import json
import os
import time

from . import assemble, factcheck, llm, media, rem, tts
from .config import FPS, cfg, clear_warnings, get_last_warnings
from .geo import get_geo
from .render import render_scene
from .search import search_facts
from .scriptspec import normalize, scenes_of, validate
from .style import normalize as norm_style

PAD = {"hook": 0.18, "lead": 0.22, "body": 0.26, "open_loop": 0.20, "cta": 0.12, "loop": 0.10}


def plan_scenes(script, audios):
    """يحسب مدة كل مشهد (بعدد إطارات صحيح) والإزاحات الزمنية للأجزاء الثمانية."""
    scenes = scenes_of(script)
    out, t0 = [], 0.0
    for sc, a in zip(scenes, audios):
        pad_val = PAD.get(sc.get("role", "body"), 0.22)
        n = max(int(round((a["dur"] + pad_val) * FPS)), 1)
        out.append({"sc": sc, "audio": a, "dur": n / FPS, "t0": t0})
        t0 += n / FPS
    return out, t0


def pick_engine(engine=None):
    e = (engine or cfg("ENGINE") or "").lower()
    if e in ("remotion", "pil"):
        return e
    return "remotion" if rem.available() else "pil"


def produce(script, style, voice_id, job_dir, log=print, progress=lambda f: None, engine=None, photos=None, topic=None):
    clear_warnings()
    os.makedirs(job_dir, exist_ok=True)
    style = norm_style(style)

    # التحقق مما إذا كان المدخل فكرة/موضوع نصي للبحث قبل الكتابة (Search Before Write)
    facts_data = None
    topic_str = topic or (script if isinstance(script, str) else "")
    if topic_str:
        log(f"🔍 البحث عن الحقائق الموثقة في الويب: {topic_str}…")
        facts_data = search_facts(topic_str)
        n_facts = facts_data.get("count", 0)
        log(f"📚 تم العثور على {n_facts} حقيقة من الويب.")
        script = llm.write_script_with_facts(topic_str, facts_data.get("facts", ""), style)
        script["_facts_data"] = facts_data
    elif isinstance(script, dict):
        facts_data = script.get("_facts_data")
        if not facts_data:
            facts_file = os.path.join(job_dir, "facts.json")
            if os.path.exists(facts_file):
                try:
                    with open(facts_file, "r", encoding="utf-8") as ff:
                        facts_data = json.load(ff)
                except Exception:
                    pass
            elif script.get("title"):
                facts_data = search_facts(script["title"])
                n_facts = facts_data.get("count", 0)
                log(f"📚 تم العثور على {n_facts} حقيقة من الويب.")

    # حفظ الحقائق والمصادر في job_dir/facts.json
    if facts_data:
        facts_path = os.path.join(job_dir, "facts.json")
        try:
            with open(facts_path, "w", encoding="utf-8") as ff:
                json.dump(facts_data, ff, ensure_ascii=False, indent=2)
        except Exception as e:
            log(f"⚠️ تعذر حفظ facts.json: {e}")

    script = normalize(script)
    style = norm_style(style)
    geo = get_geo()
    errs = [i for i in validate(script, geo) if i["level"] == "error"]
    if errs:
        raise ValueError("السكربت فيه أخطاء تمنع التوليد: " + " | ".join(i["msg"] for i in errs))
    geo_errs = factcheck.check_script(script)
    if geo_errs:
        for ge in geo_errs:
            log(f"⚠️ تحقق جغرافي: {ge}")
    engine = pick_engine(engine)
    os.makedirs(job_dir, exist_ok=True)
    scenes = scenes_of(script)
    n = len(scenes)
    log(f"المحرّك: {engine}")

    audios = []
    for i, sc in enumerate(scenes):
        log(f"الصوت {i + 1}/{n}: {sc['id']}")
        audios.append(tts.synth(sc["narration"], voice_id, os.path.join(job_dir, f"a_{i}")))
        progress(0.08 * (i + 1) / n)
    plan, total = plan_scenes(script, audios)

    wavs = []
    for i, p in enumerate(plan):
        wav = os.path.join(job_dir, f"w_{i}.wav")
        assemble.to_wav(p["audio"]["path"], wav, p["dur"])
        wavs.append(wav)
    au = os.path.join(job_dir, "audio_all.wav")
    assemble.concat(wavs, au)
    final = os.path.join(job_dir, "short.mp4")
    info = [{"id": p["sc"]["id"], "dur": round(p["dur"], 2)} for p in plan]

    if engine == "remotion":
        use_photos = media.enabled() if photos is None else bool(photos)
        m = media.Media(os.path.join(job_dir, "public", "media"), log) if use_photos else None
        if m:
            log("البحث عن صور مرخّصة لكل جملة…")
        spec = rem.build_spec(script, style, plan, int(round(total * FPS)), geo,
                              photo=m.resolve if m else None, degrade=True)
        try:
            from . import visual_tools
            visual_tools.record_asset_credits(spec, job_dir)
        except Exception:
            pass
        if m:
            if m.credits:
                open(os.path.join(job_dir, "credits.txt"), "w", encoding="utf-8").write(m.credits_text())
            open(os.path.join(job_dir, "media_report.txt"), "w", encoding="utf-8").write(m.media_report_text())
            log(m.media_report_text())
        log(f"رسم {spec['total']} إطاراً بـ Remotion (حزمة + رندر)…")
        rem.render_video(spec, final, job_dir, au, progress=lambda f: progress(0.08 + 0.9 * f))
        info = [{"id": s["id"], "dur": round(s["dur"] / FPS, 2), "beats": [b["kind"] for b in s["beats"]]} for s in spec["scenes"]]
    else:
        clips = []
        for i, p in enumerate(plan):
            sc, a = p["sc"], p["audio"]
            log(f"الرسم {i + 1}/{n}: {sc['id']} ({p['dur']:.1f} ث)")
            clip = os.path.join(job_dir, f"v_{i}.mp4")
            render_scene(geo, sc, p["dur"], a["words"], clip, style, fast=(sc["role"] == "hook"),
                         settled=(sc["role"] == "loop"), t0=p["t0"], total=total)
            clips.append(clip)
            progress(0.08 + 0.9 * (i + 1) / n)
        v = os.path.join(job_dir, "video_only.mp4")
        assemble.concat(clips, v)
        assemble.mux(v, au, final)

    credits = open(os.path.join(job_dir, "credits.txt"), encoding="utf-8").read() if os.path.exists(os.path.join(job_dir, "credits.txt")) else ""
    if credits:
        script["description"] = (script["description"] + "\n\nالصور:\n" + credits).strip()
    if facts_data and facts_data.get("sources"):
        sources_text = "\n".join(f"• {src}" for src in facts_data["sources"])
        script["description"] = (script["description"] + "\n\nالمصادر الموثقة:\n" + sources_text).strip()
    media_rep = m.reports if (engine == "remotion" and m) else []
    facts_count = facts_data.get("count", len(facts_data.get("sources", []))) if facts_data else 0
    sources_list = facts_data.get("sources", []) if facts_data else []
    meta = {
        "title": script["title"],
        "description": script["description"],
        "tags": script["tags"],
        "duration": round(total, 1),
        "scenes": info,
        "style": style["name"],
        "engine": engine,
        "credits": credits,
        "media_report": media_rep,
        "facts_count": facts_count,
        "sources": sources_list,
    }
    for name, obj in (("meta.json", meta), ("script.json", script), ("style.json", style)):
        json.dump(obj, open(os.path.join(job_dir, name), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    for f in os.listdir(job_dir):
        if f.startswith(("a_", "w_", "v_")) or f in ("video_only.mp4", "audio_all.wav", "spec.json") or f.endswith(".part.mp4") or (f.endswith(".txt") and f not in ("credits.txt", "facts.txt")):
            try:
                os.remove(os.path.join(job_dir, f))
            except OSError:
                pass
    progress(1.0)
    log("اكتمل.")
    return {"video": "short.mp4", **meta}
