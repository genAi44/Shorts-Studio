"""خادم الويب: واجهة + واجهات API. شغّله ثم افتح http://localhost:8742"""
import json
import logging
import shutil
import threading
import time
import traceback
import uuid

import io
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

from pipeline import direct, llm, llm_providers, llm_router, media, rem, scriptspec as sp, style as stl, tts, visual_tools
from pipeline.config import OUT, ROOT, SAMPLE, cfg, get_last_warnings
from pipeline.geo import get_geo
from pipeline.render import preview_frame
from pipeline.run import pick_engine, plan_scenes, produce

logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder=str(ROOT / "static"), static_url_path="/static")
JOBS, LOCK = {}, threading.Lock()


def err(msg, code=400):
    return jsonify({"error": msg}), code


def body():
    return request.get_json(silent=True) or {}


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/favicon.ico")
def favicon():
    return ("", 204)


@app.get("/outputs/<path:p>")
def outputs(p):
    return send_from_directory(OUT, p)


@app.get("/assets/<path:p>")
def public_assets(p):
    return send_from_directory(str(ROOT / "remotion" / "public"), p)


@app.post("/api/visual-library")
def visual_library():
    b = body()
    q = (b.get("query") or "").strip()
    set_name = (b.get("set") or "").strip() or None
    icons_res = visual_tools.search_icons(q or "landmark", set_name=set_name, limit=12)
    # Attach SVG body preview from catalog for UI rendering
    bundle_sets = visual_tools._load_icons_bundle().get("sets", {})
    for ic in icons_res:
        ic_obj = bundle_sets.get(ic["set"], {}).get(ic["name"], {})
        ic["body"] = ic_obj.get("body", "")
        ic["viewBox"] = f"0 0 {ic_obj.get('width', 24)} {ic_obj.get('height', 24)}"
    emojis_res = visual_tools.search_emoji(q, limit=12)
    flags_res = [
        visual_tools.resolve_flag(q, shape="rect")
    ] if q else [
        visual_tools.resolve_flag(c, shape="rect") for c in ("EG", "SA", "BO", "MA", "AE", "JO", "IQ", "SY")
    ]
    flags_res = [f for f in flags_res if f and f.get("found") and f.get("file")]
    lottie_res = visual_tools.search_lottie(q, limit=8)
    charts_res = [
        {"type": "generative_canvas", "name": "GenerativeCanvas (نظام ليغو التوليدي المخصص من الصفر)"},
        {"type": "elevation", "name": "ElevationProfile (جبل + بحر + العاصمة + عداد صاعد)"},
        {"type": "versus_battle", "name": "VersusBattle (سباق المقارنة المباشر)"},
        {"type": "animated_route", "name": "AnimatedRoute (مسار الرحلة الجغرافية)"},
        {"type": "balance_meter", "name": "BalanceMeter (ميزان القوى والاستفتاء)"},
        {"type": "deep_time_slider", "name": "DeepTimeSlider (شريط القرون والتاريخ)"},
        {"type": "stack_pyramid", "name": "StackPyramid (الهرم الطبقي وتشريح السلطة)"},
        {"type": "macro_zoom_globe", "name": "MacroZoomGlobe (زوم تلسكوبي من العالم للدولة)"},
        {"type": "subsurface_mine", "name": "SubsurfaceMine (تشريح باطن الأرض والتعدين)"},
        {"type": "dot_matrix_population", "name": "DotMatrixPopulation (مصفوفة الكثافة السكانية)"},
        {"type": "money_waterfall", "name": "MoneyWaterfall (شلال تدفق الأموال والميزانية)"},
        {"type": "frontline_clash", "name": "FrontlineClash (خط المواجهة وحصار المعارك)"},
        {"type": "bar", "name": "BarChart (مخطط أعمدة D3)"},
        {"type": "line", "name": "LineChart (مخطط خطي متحرك)"},
        {"type": "donut", "name": "PieDonutChart (مخطط دائري)"},
        {"type": "counter", "name": "NumberCounter (عداد رقمي)"},
        {"type": "progress_ring", "name": "ProgressRing (حلقة إنجاز)"},
        {"type": "timeline", "name": "Timeline (خط زمني)"},
    ]
    components_res = [
        {"component": "lower_third", "name": "LowerThird (شريط تعريفي سفلي)"},
        {"component": "title_card", "name": "TitleCard (بطاقة عنوان رئيسية)"},
        {"component": "quote_card", "name": "QuoteCard (بطاقة اقتباس)"},
        {"component": "bullet_list", "name": "BulletListReveal (قائمة نقطية متتابعة)"},
        {"component": "stat_callout", "name": "StatCallout (إبراز إحصائي)"},
        {"component": "animated_headline", "name": "AnimatedHeadline (عنوان متحرك بالكلمات)"},
    ]
    return jsonify({
        "icons": icons_res,
        "emojis": emojis_res,
        "flags": flags_res,
        "lottie": lottie_res,
        "charts": charts_res,
        "components": components_res,
    })


@app.post("/api/chat-edit-visual")
def chat_edit_visual():
    b = body()
    script = sp.normalize(b.get("script"))
    instruction = (b.get("instruction") or "").strip()
    scene_id = (b.get("scene") or "hook").strip()
    if not instruction:
        return err("اكتب أمر التعديل البصري أولاً (مثال: change the icon to a pyramid أو use a bar chart here).")
    edited = visual_tools.apply_chat_visual_edit(script, instruction, scene_id=scene_id)
    packed = _pack(edited["script"])
    packed["action"] = edited["action"]
    packed["scene"] = edited["scene"]
    packed["visuals"] = edited["visuals"]
    return jsonify(packed)


@app.get("/api/status")
def status():
    router = llm_router.get_router()
    return jsonify({
        "freellmapi": bool(cfg("FREELLMAPI_API_KEY")),
        "deepseek": bool(cfg("DEEPSEEK_API_KEY")),
        "gemini": bool(cfg("GEMINI_API_KEY")),
        "elevenlabs": bool(cfg("ELEVENLABS_API_KEY")),
        "photos": media.enabled(),
        "pexels": bool(cfg("PEXELS_API_KEY")),
        "rembg": media.has_rembg(),
        "roles": router.get_all_role_configs(),
        "models": {
            "freellmapi": "auto",
            "deepseek": cfg("DEEPSEEK_MODEL", "deepseek-chat"),
            "gemini": cfg("GEMINI_MODEL", "gemini-2.5-flash"),
            "elevenlabs": cfg("ELEVENLABS_MODEL", "eleven_multilingual_v2")
        },
    })


@app.get("/api/llm/providers")
def get_llm_providers():
    """قائمة المزوّدين المسجلين وحالتهم والنماذج المتاحة من كل مزوّد."""
    provs = llm_providers.get_all_providers()
    out = {}
    for pid, p in provs.items():
        out[pid] = {
            "id": p.id,
            "name": p.name,
            "configured": p.is_configured(),
            "supports_auto_mode": p.supports_auto_mode,
            "auto_mode_info": p.auto_mode_info(),
            "models": p.list_models(),
        }
    return jsonify(out)


@app.get("/api/llm/health")
def get_llm_health():
    """فحص صحة اتصال واستجابة المزوّدين (Health Check)."""
    provs = llm_providers.get_all_providers()
    res = {}
    for pid, p in provs.items():
        res[pid] = p.health_check()
    return jsonify(res)


@app.get("/api/llm/config")
def get_llm_config():
    """استرجاع إعدادات النماذج والأدوار الحالية."""
    router = llm_router.get_router()
    return jsonify({
        "roles": router.get_all_role_configs(),
        "available_roles": llm_router.ROLES,
    })


@app.post("/api/llm/config")
def update_llm_config():
    """تحديث مزوّد ونموذج كل دور من واجهة المستخدم."""
    b = body()
    router = llm_router.get_router()
    if "roles" in b and isinstance(b["roles"], dict):
        for role, c in b["roles"].items():
            if isinstance(c, dict):
                router.update_role_config(
                    role=role,
                    provider=c.get("provider", "freellmapi"),
                    model=c.get("model"),
                    fallback_chain=c.get("fallback_chain"),
                )
    elif "role" in b:
        router.update_role_config(
            role=b["role"],
            provider=b.get("provider", "freellmapi"),
            model=b.get("model"),
            fallback_chain=b.get("fallback_chain"),
        )
    else:
        return err("بيانات الإعدادات غير صالحة.")
    return jsonify({"status": "updated", "roles": router.get_all_role_configs()})


@app.get("/api/llm/logs")
def get_llm_logs():
    """سجل استدعاءات النماذج والتحويل الاحتياطي والتوكنز."""
    limit = int(request.args.get("limit", 50))
    router = llm_router.get_router()
    return jsonify({"logs": router.get_logs(limit)})


@app.post("/api/llm/test-call")
def test_llm_call():
    """اختبار تجريبي فوري لمزوّد ونموذج محدد."""
    b = body()
    provider_id = b.get("provider", "freellmapi")
    model = b.get("model")
    prompt = b.get("prompt", "أجب كـ JSON فقط بمفتاح reply: {\"reply\": \"مرحباً، الاتصال ناجح!\"}")
    try:
        p = llm_providers.get_provider(provider_id)
        resp = p.complete(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.2,
            json_mode=True,
            timeout=30,
        )
        return jsonify({
            "status": "success",
            "content": resp.content,
            "provider": resp.provider,
            "model": resp.model,
            "usage": resp.usage.to_dict(),
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 502


@app.get("/api/voices")
def voices():
    return jsonify({"voices": tts.voices(), "default": cfg("ELEVENLABS_VOICE_ID")})


@app.get("/api/sample")
def sample():
    with open(SAMPLE, encoding="utf-8") as f:
        return jsonify(json.load(f))


def _pack(script):
    s = sp.normalize(script)
    try:
        from pipeline import visual_tools
        for idx, p in enumerate(sp.PARTS):
            pid = p["id"]
            if pid in s and isinstance(s[pid], dict) and not s[pid].get("visuals"):
                sc_obj = {**s[pid], "id": pid, "role": p["role"]}
                s[pid]["visuals"] = visual_tools.enrich_scene_visuals(sc_obj, scene_index=idx, preferred_icon_set="lucide")
    except Exception:
        pass
    return {"script": s, "issues": sp.validate(s, get_geo()), "estimate": sp.estimate(s)}


@app.post("/api/script")
def make_script():
    b = body()
    idea = (b.get("idea") or "").strip()
    if len(idea) < 4:
        return err("اكتب فكرة الفيديو أولاً.")
    note = (b.get("note") or "").strip()
    session_id = b.get("session_id")
    try:
        temp = float(b.get("temperature", 0.7))
    except (TypeError, ValueError):
        temp = 0.7

    # خطوة البحث قبل الكتابة (Search before write): استخراج الحقائق الموثقة أولاً من الويب
    from pipeline.search import search_facts
    facts_data = search_facts(idea)
    facts_count = facts_data.get("count", 0)

    try:
        script = llm.write_script_with_facts(idea, facts_data.get("facts", ""), style=None)
        used_model = "router"
    except Exception as e:
        logger.warning("فشل write_script_with_facts: %s، الانتقال للمسار الاحتياطي", e)
        user_prompt = sp.user_prompt(idea, note)
        try:
            raw = llm.call_llm_json("script", sp.SYSTEM, user_prompt, temperature=temp, session_id=session_id)
            script = sp.normalize(raw)
            used_model = "router"
        except llm.LLMError as le:
            return err(str(le), 502)

    script["_facts_data"] = facts_data
    geo = get_geo()
    errors = sp.script_errors(script, geo)

    # If validation fails, send the errors back to the model once and ask it to fix them
    if errors:
        fix_prompt = (
            "السكربت المُولّد يحتوي على مخالفات للشروط والمواصفات الإلزامية لهيكل الأجزاء الثمانية (8 parts):\n"
            + "\n".join(f"- {e}" for e in errors)
            + f"\n\nالسكربت الحالي:\n{sp.dumps(script)}"
            + "\n\nالمطلوب: أعد كتابة وتصحيح وتوسيع السكربت كاملاً بالترتيب الدقيق للأجزاء الثمانية دون أي مخالفة:\n"
            + "1. hook: 10–18 كلمة (سؤال أو تناقض أو رقم صادم، بلا تحية ولا يكشف الجواب).\n"
            + "2. lead: 14–24 كلمة (وعد مشوق وسياق كافٍ للبقاء).\n"
            + "3. body1: 18–30 كلمة (حقيقة ملموسة أولى بتفاصيل كافية ومحكية).\n"
            + "4. open_loop1: 8–16 كلمة (سطر تشويقي يطرح لغزاً جديداً بلا إجابة الآن).\n"
            + "5. body2: 18–30 كلمة (يجيب على open_loop1 بحقيقة أقوى ومفاجئة).\n"
            + "6. open_loop2: 8–16 كلمة (سطر تشويقي للذروة والمفاجأة الكبرى).\n"
            + "7. body3: 18–30 كلمة (أقوى حقيقة تكشف اللغز وتفي بوعد الـ hook بالكامل).\n"
            + "8. cta: 8–18 كلمة (إجراء واحد طبيعي، بلا شكر، وتتصل كلماته الأخيرة ببداية الـ hook).\n"
            + "- مجموع كلمات السرد الإجمالي: بين 100 و150 كلمة (إياك أن يقل عن 95 كلمة).\n"
            + "- facts: قائمة claims و sources موثقة لكل معلومة.\n"
            + "أعد JSON فقط بالمفاتيح الثمانية."
        )
        try:
            fixed_raw = llm.call_llm_json("script", sp.SYSTEM, fix_prompt, temperature=0.2, session_id=session_id)
            script = sp.normalize(fixed_raw)
            script["_facts_data"] = facts_data
        except Exception:
            pass

    res = _pack(script)
    res["by"] = used_model
    res["facts_count"] = facts_count
    res["sources"] = facts_data.get("sources", [])
    return jsonify(res)


RECENT = []  # أسماء آخر الستايلات لتجنّب التكرار


@app.get("/api/presets")
def list_style_presets():
    from pipeline import presets
    return jsonify({"presets": presets.list_presets()})


@app.post("/api/style")
def make_style():
    """مدير فني: يصمّم ستايلاً للفيديو عبر نموذج style؛ وإلا ستايل عشوائي مبذور."""
    b = body()
    if b.get("preset"):  # a ready-made art direction from styles/<slug>/
        from pipeline import presets
        if not presets.has_preset(b["preset"]):
            return jsonify({"error": "ستايل جاهز غير موجود"}), 404
        st = presets.load_style(b["preset"])
        RECENT.append(st["name"])
        return jsonify({"style": st, "by": "preset"})
    script = sp.normalize(b.get("script"))
    session_id = b.get("session_id")
    used = "random"
    if not b.get("random"):
        try:
            raw = llm.call_llm_json("style", stl.ART_SYSTEM, stl.art_prompt(script, RECENT[-5:]), temperature=1.1, session_id=session_id)
            st, used = stl.normalize(raw), "style_model"
        except Exception as e:
            logger.warning("تعذّر توليد الستايل بالذكاء الاصطناعي، الانتقال للستايل العشوائي: %s", e)
            st = stl.random_style()
    else:
        st = stl.random_style()
    RECENT.append(st["name"])
    return jsonify({"style": st, "by": used})


@app.post("/api/direct")
def make_beats():
    """المخرج البصري: مشهد حركي لكل جملة عبر الموجه الذكي؛ وإلا مقاطع آمنة."""
    b = body()
    script = sp.normalize(b.get("script"))
    session_id = b.get("session_id")
    geo = get_geo()
    by = "auto"
    if not b.get("auto"):
        try:
            mood = (b.get("style") or {}).get("name", "")
            use_ph = b.get("photos", True) is not False and media.enabled()
            sys_p = direct.director_system(use_ph)
            usr_p = direct.director_prompt(script, sp.scenes_of(script), mood)
            from pipeline import presets as _presets
            _guide = _presets.guide((b.get("style") or {}).get("preset"))
            if _guide:
                usr_p += "\n\nدليل الإخراج الفني لهذا الفيديو (التزم بجوهره وبقائمة «ليس» وبتعليمات المخرج البصري):\n" + _guide
            raw = llm.call_llm_json("director", sys_p, usr_p, temperature=0.8, session_id=session_id)
            retry_fn = lambda reasons: llm.call_llm_json(
                "director",
                sys_p,
                usr_p + "\n\nFix these invalid beats: " + "; ".join(reasons),
                temperature=0.4,
                session_id=session_id,
            )
            script, by = direct.apply_beats(script, raw, geo, llm_retry_fn=retry_fn), "director_model"
        except Exception as e:
            logger.warning("تعذّر الإخراج بالذكاء الاصطناعي: %s", e)
            script = direct.auto_beats(script, geo)
            return jsonify({**_pack(script), "by": "auto", "warning": str(e)})
    else:
        script = direct.auto_beats(script, geo)
    return jsonify({**_pack(script), "by": by})


PREVIEW_LOCK = threading.Lock()  # remotion/src/generated + src/authored are shared files: one preview at a time


@app.post("/api/preview")
def preview():
    """إطار معاينة سريع (بلا صوت حقيقي): Remotion إن توفّر وإلا PIL."""
    b = body()
    script = sp.normalize(b.get("script"))
    st = stl.normalize(b.get("style"))
    scenes = sp.scenes_of(script)
    i = max(0, min(int(b.get("scene", 0)), len(scenes) - 1))
    OUT.mkdir(exist_ok=True)
    work = OUT / "_prev" / uuid.uuid4().hex[:10]  # per request: two tabs previewing at once must not overwrite each other's frame
    work.mkdir(parents=True, exist_ok=True)
    # تقدير التوقيت من عدد الكلمات بلا استدعاء ElevenLabs
    auds = [tts.estimate_timing(sc["narration"]) for sc in scenes]
    plan, total = plan_scenes(script, auds)
    p = plan[i]
    if rem.available() and pick_engine(b.get("engine")) == "remotion":
        try:
            with PREVIEW_LOCK:
                spec = rem.build_spec(script, st, plan, int(round(total * 30)), get_geo(), None, degrade=False, only_scene_idx=i)
                if cfg("AUTHORED_SCENES", "0") == "1":  # preview = the cached authored scene (same file the final render uses)
                    from pipeline import scene_author
                    spec = scene_author.author_spec(spec, str(work / "authored"), cache_only=True, only_ids={spec["scenes"][i]["id"]})
                sc = spec["scenes"][i]
                bi = max(0, min(int(b.get("beat", 0)), len(sc["beats"]) - 1))
                fr = sc["from"] + sc["beats"][bi]["from"] + int(float(b.get("t", 2.0)) * 30)
                fr = min(fr, sc["from"] + sc["dur"] - 2)
                out = str(work / "preview.jpg")
                rem.render_still(spec, out, fr, str(work))
                data = Path(out).read_bytes()
            return send_file(io.BytesIO(data), mimetype="image/jpeg")
        except rem.RemError as e:
            return err(str(e), 500)
        finally:
            shutil.rmtree(work, ignore_errors=True)
    t = min(float(b.get("t", 2.5)), p["dur"] - 0.05)
    im = preview_frame(get_geo(), p["sc"], p["dur"], p["audio"]["words"], st, t, t0=p["t0"], total=total,
                       fast=(p["sc"]["role"] == "hook"), settled=(p["sc"]["role"] == "loop"))
    buf = io.BytesIO()
    im.resize((540, 960)).save(buf, "JPEG", quality=88)
    buf.seek(0)
    return send_file(buf, mimetype="image/jpeg")


@app.post("/api/validate")
def validate():
    return jsonify(_pack(body().get("script")))


@app.post("/api/factcheck")
def factcheck():
    b = body()
    script = sp.normalize(b.get("script"))
    session_id = b.get("session_id")
    try:
        res = llm.call_llm_json("factcheck", sp.FACT_SYSTEM, json.dumps(script, ensure_ascii=False), temperature=0.2, session_id=session_id)
    except llm.LLMError as e:
        return err(str(e), 502)
    return jsonify(res)


@app.post("/api/render")
def render():
    b = body()
    raw_s = b.get("script") or {}
    script = sp.normalize(raw_s)
    if isinstance(raw_s, dict) and "_facts_data" in raw_s:
        script["_facts_data"] = raw_s["_facts_data"]
    style = stl.normalize(b.get("style"))
    if not cfg("ELEVENLABS_API_KEY"):
        return err("مفتاح ElevenLabs غير مضبوط. أضفه إلى .env")
    issues = sp.validate(script, get_geo())
    errs = [i["msg"] for i in issues if i["level"] == "error"]
    if errs:
        return err("أصلح الأخطاء أولاً: " + " | ".join(errs))
    jid = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:5]
    initial_facts_count = 0
    if isinstance(script, dict) and script.get("_facts_data"):
        initial_facts_count = script["_facts_data"].get("count", 0)
    job = {
        "id": jid,
        "state": "running",
        "progress": 0.0,
        "log": [],
        "result": None,
        "error": None,
        "facts_count": initial_facts_count,
        "warnings": [],
    }
    with LOCK:
        JOBS[jid] = job

    def work():
        try:
            res = produce(script, style, b.get("voice_id", ""), str(OUT / jid), engine=b.get("engine"), photos=b.get("photos"),
                          log=lambda m: job["log"].append(m),
                          progress=lambda f: (job.__setitem__("progress", round(f, 3)), job.__setitem__("warnings", get_last_warnings())))
            res["warnings"] = get_last_warnings()  # every fallback the pipeline took, visible to the UI
            res["url"] = f"/outputs/{jid}/{res['video']}"
            if res.get("facts_count"):
                job["facts_count"] = res["facts_count"]
            job["result"], job["state"] = res, "done"
        except Exception as e:  # noqa
            traceback.print_exc()
            job["error"], job["state"] = str(e), "error"

    threading.Thread(target=work, daemon=True).start()
    return jsonify({"job": jid})


@app.get("/api/job/<jid>")
def job(jid):
    j = JOBS.get(jid)
    return jsonify(j) if j else err("مهمة غير موجودة.", 404)


@app.get("/api/last_warnings")
def last_warnings():
    """يعيد قائمة التحذيرات الصريحة (Explicit Fallbacks) لآخر عملية رندر أو إخراج."""
    return jsonify({"warnings": get_last_warnings()})



if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    app.run(host="127.0.0.1", port=int(cfg("PORT", "8742")), threaded=True)
