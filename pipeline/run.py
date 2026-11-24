"""خط الإنتاج: سكربت + ستايل ← صوت لكل مشهد ← رسم المشاهد (Remotion أو PIL احتياطاً) ← mp4."""
import json
import os

from . import assemble, factcheck, llm, media, rem, tts
from .config import FPS, cfg, clear_warnings
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
    # تشغيل وحفظ خطة محرك الذكاء البصري (Visual Intelligence Engine) في مجلد المهمة
    try:
        from .visual_intelligence import analyze_script_visual_intelligence
        vi_plan = script.get("_visual_intelligence")
        if not isinstance(vi_plan, dict) or not vi_plan.get("scenes"):
            vi_plan = analyze_script_visual_intelligence(script, geo=geo, use_llm=True)
            script["_visual_intelligence"] = vi_plan
        vi_by_id = {sv["id"]: sv for sv in (vi_plan.get("scenes") or []) if isinstance(sv, dict) and sv.get("id")}
        for sc_item in scenes_of(script):
            sv = vi_by_id.get(sc_item.get("id"))
            if sv and not sc_item.get("_vi"):
                sc_item["_vi"] = sv
        with open(os.path.join(job_dir, "visual_intelligence.json"), "w", encoding="utf-8") as vif:
            json.dump(vi_plan, vif, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"⚠️ تعذر حفظ visual_intelligence.json: {e}")
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
    if total > 60.0:
        scale = 60.0 / total
        for p in plan:
            p["dur"] *= scale
            p["t0"] *= scale
        total = 60.0

    wavs = []
    for i, p in enumerate(plan):
        wav = os.path.join(job_dir, f"w_{i}.wav")
        assemble.to_wav(p["audio"]["path"], wav, p["dur"])
        wavs.append(wav)
    au = os.path.join(job_dir, "audio_all.wav")
    assemble.concat(wavs, au)
    try:
        assemble.loudnorm(au)
    except Exception as e:
        log(f"⚠️ تعذر تطبيع جهارة الصوت (سيُستخدم الصوت الأصلي): {e}")
    final = os.path.join(job_dir, "short.mp4")
    info = [{"id": p["sc"]["id"], "dur": round(p["dur"], 2)} for p in plan]

    if engine == "remotion":
        use_photos = media.enabled() if photos is None else bool(photos)
        m = media.Media(os.path.join(job_dir, "public", "media"), log) if use_photos else None
        if m:
            log("البحث عن صور مرخّصة لكل جملة…")
        try:
            from . import entities
            entities.ensure_plan(script, geo)
        except Exception as _ee:  # noqa: BLE001
            from .config import record_fallback
            record_fallback(f"entity plan failed ({_ee}): legacy detection only", beat_id="entities")
        spec = rem.build_spec(script, style, plan, int(round(total * FPS)), geo,
                              photo=m.resolve if m else None, degrade=True)
        studio_left = None  # scene ids the studio could not pass (None = studio off: author every scene)
        if cfg("STUDIO_MODE", "0") == "1":  # direction before code: treatment -> design system -> shot specs -> compiled scenes
            try:
                from . import studio
                spec = studio.direct_spec(spec, script, job_dir, log=log)
                studio_left = {s["id"] for s in spec["scenes"] if not s.get("authored")}
            except Exception as _se:  # noqa: BLE001
                from .config import record_fallback
                record_fallback(f"studio failed ({_se}): legacy path", beat_id="studio")
        if cfg("AUTHORED_SCENES", "0") == "1" and studio_left != set():
            try:
                from . import scene_author
                spec = scene_author.author_spec(spec, job_dir, log=log, only_ids=studio_left)
            except Exception as _ae:  # noqa: BLE001
                from .config import record_fallback
                record_fallback(f"scene authoring failed ({_ae}): built-in beats", beat_id="authoring")
        try:
            from . import visual_tools
            visual_tools.record_asset_credits(spec, job_dir)
        except Exception:
            pass
        try:
            from . import visual_qa
            facts_txt = json.dumps(script.get("_facts_data") or script.get("facts") or "", ensure_ascii=False)
            qa_rep = visual_qa.audit_spec(spec, job_dir=job_dir, check_pixels=(cfg("VISUAL_QA", "0") == "1"), sourced_text=facts_txt)
            if not qa_rep.get("passed"):
                log(f"تحذير QA: متوسط الدرجة {qa_rep.get('average_score')}/100 — راجع qa_report.json")
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
        # تحسين جودة التمويج للجودة السينمائية
        assemble.mux(v, au, final, quality="high")

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
    if cfg("CRITIC", "0") == "1":  # Phase 0: grades the finished video, report only (critic/report.html)
        try:
            from . import critic
            r = critic.critique_job(job_dir, log=log)
            log(f"الناقد: {r['passed_scenes']}/{r['total_scenes']} مشاهد ناجحة، تقرير: critic/report.html")
        except Exception as e:  # noqa: BLE001 - the critic must never break a render
            log(f"⚠️ تعذر تشغيل الناقد: {e}")
    progress(1.0)
    log("اكتمل.")
    return {"video": "short.mp4", **meta}
