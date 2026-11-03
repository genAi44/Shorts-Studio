"""خادم الويب: واجهة + واجهات API. شغّله ثم افتح http://localhost:8000"""
import json
import threading
import time
import traceback
import uuid

import io

from flask import Flask, jsonify, request, send_file, send_from_directory

from pipeline import direct, llm, media, rem, scriptspec as sp, style as stl, tts
from pipeline.config import OUT, ROOT, SAMPLE, cfg, flag
from pipeline.geo import get_geo
from pipeline.render import preview_frame
from pipeline.run import pick_engine, plan_scenes, produce

app = Flask(__name__, static_folder=str(ROOT / "static"), static_url_path="/static")
JOBS, LOCK = {}, threading.Lock()


def err(msg, code=400):
    return jsonify({"error": msg}), code


def body():
    return request.get_json(silent=True) or {}


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/outputs/<path:p>")
def outputs(p):
    return send_from_directory(OUT, p)


@app.get("/api/status")
def status():
    return jsonify({
        "deepseek": bool(cfg("DEEPSEEK_API_KEY")), "gemini": bool(cfg("GEMINI_API_KEY")),
        "elevenlabs": bool(cfg("ELEVENLABS_API_KEY")),
        "photos": media.enabled(), "pexels": bool(cfg("PEXELS_API_KEY")), "rembg": media.has_rembg(),
        "script_model": cfg("SCRIPT_MODEL", "gemini").strip().lower(),
        "models": {"deepseek": cfg("DEEPSEEK_MODEL", "deepseek-chat"),
                   "gemini": cfg("GEMINI_MODEL", "gemini-2.5-flash"),
                   "elevenlabs": cfg("ELEVENLABS_MODEL", "eleven_multilingual_v2")},
    })


@app.get("/api/voices")
def voices():
    return jsonify({"voices": tts.voices(), "default": cfg("ELEVENLABS_VOICE_ID")})


@app.get("/api/sample")
def sample():
    return jsonify(json.load(open(SAMPLE, encoding="utf-8")))


def _pack(script):
    s = sp.normalize(script)
    return {"script": s, "issues": sp.validate(s, get_geo()), "estimate": sp.estimate(s)}


@app.post("/api/script")
def make_script():
    b = body()
    idea = (b.get("idea") or "").strip()
    if len(idea) < 4:
        return err("اكتب فكرة الفيديو أولاً.")
    note = (b.get("note") or "").strip()
    try:
        temp = float(b.get("temperature", 0.7))
    except (TypeError, ValueError):
        temp = 0.7

    model_pref = cfg("SCRIPT_MODEL", "gemini").strip().lower()
    user_prompt = sp.user_prompt(idea, note)

    raw = None
    used_model = None

    if model_pref == "deepseek":
        try:
            raw = llm.deepseek_json(sp.SYSTEM, user_prompt, temperature=temp)
            used_model = "deepseek"
        except llm.LLMError as e:
            return err(str(e), 502)
    else:
        # Default to Gemini; fall back to DeepSeek if Gemini fails
        try:
            raw = llm.gemini_json(sp.SYSTEM, user_prompt, grounding=True, temperature=temp)
            used_model = "gemini"
        except llm.LLMError:
            try:
                raw = llm.deepseek_json(sp.SYSTEM, user_prompt, temperature=temp)
                used_model = "deepseek"
            except llm.LLMError as e2:
                return err(str(e2), 502)

    script = sp.normalize(raw)
    geo = get_geo()
    errors = sp.script_errors(script, geo)

    # If validation fails, send the errors back to the model once and ask it to fix them
    if errors:
        fix_prompt = (
            "السكربت المُولّد يحتوي على مخالفات للشروط والمواصفات الإلزامية لهيكل الأجزاء الثمانية (8 parts):\n"
            + "\n".join(f"- {e}" for e in errors)
            + f"\n\nالسكربت الحالي:\n{sp.dumps(script)}"
            + "\n\nالمطلوب: أعد كتابة وتصحيح وتوسيع السكربت كاملاً بالترتيب الدقيق للأجزاء الثمانية دون أي مخالفة:\n"
            + "1. hook: 10–15 كلمة (سؤال أو تناقض أو رقم صادم، بلا تحية ولا يكشف الجواب).\n"
            + "2. lead: 14–22 كلمة (وعد مشوق وسياق كافٍ للبقاء).\n"
            + "3. body1: 18–28 كلمة (حقيقة ملموسة أولى بتفاصيل كافية ومحكية).\n"
            + "4. open_loop1: 8–14 كلمة (سطر تشويقي يطرح لغزاً جديداً بلا إجابة الآن).\n"
            + "5. body2: 18–28 كلمة (يجيب على open_loop1 بحقيقة أقوى ومفاجئة).\n"
            + "6. open_loop2: 8–14 كلمة (سطر تشويقي للذروة والمفاجأة الكبرى).\n"
            + "7. body3: 18–28 كلمة (أقوى حقيقة تكشف اللغز وتفي بوعد الـ hook بالكامل).\n"
            + "8. cta: 8–14 كلمة (إجراء واحد طبيعي، بلا شكر، وتتصل كلماته الأخيرة ببداية الـ hook).\n"
            + "- مجموع كلمات السرد الإجمالي: بين 110 و135 كلمة (إياك أن يقل عن 105 كلمات).\n"
            + "- facts: قائمة claims و sources موثقة لكل معلومة.\n"
            + "أعد JSON فقط بالمفاتيح الثمانية."
        )
        try:
            if used_model == "gemini":
                fixed_raw = llm.gemini_json(sp.SYSTEM, fix_prompt, grounding=True, temperature=0.2)
            else:
                fixed_raw = llm.deepseek_json(sp.SYSTEM, fix_prompt, temperature=0.2)
            script = sp.normalize(fixed_raw)
        except Exception:
            pass

    res = _pack(script)
    res["by"] = used_model
    return jsonify(res)


RECENT = []  # أسماء آخر الستايلات لتجنّب التكرار


@app.post("/api/style")
def make_style():
    """مدير فني: DeepSeek يصمّم ستايلاً للفيديو؛ وإلا (أو عند طلب random) ستايل عشوائي مبذور."""
    b = body()
    script = sp.normalize(b.get("script"))
    used = "random"
    if not b.get("random") and cfg("DEEPSEEK_API_KEY"):
        try:
            raw = llm.deepseek_json(stl.ART_SYSTEM, stl.art_prompt(script, RECENT[-5:]), temperature=1.1)
            st, used = stl.normalize(raw), "deepseek"
        except llm.LLMError:
            st = stl.random_style()
    else:
        st = stl.random_style()
    RECENT.append(st["name"])
    return jsonify({"style": st, "by": used})


@app.post("/api/direct")
def make_beats():
    """المخرج البصري: مشهد حركي لكل جملة (DeepSeek)، وإلا مقاطع آمنة من الـ visual الحالي."""
    b = body()
    script = sp.normalize(b.get("script"))
    geo = get_geo()
    by = "auto"
    if not b.get("auto") and cfg("DEEPSEEK_API_KEY"):
        try:
            mood = (b.get("style") or {}).get("name", "")
            use_ph = b.get("photos", True) is not False and media.enabled()
            raw = llm.deepseek_json(direct.director_system(use_ph), direct.director_prompt(script, sp.scenes_of(script), mood), temperature=0.9)
            script, by = direct.apply_beats(script, raw, geo), "deepseek"
        except llm.LLMError as e:
            script = direct.auto_beats(script, geo)
            return jsonify({**_pack(script), "by": "auto", "warning": str(e)})
    else:
        script = direct.auto_beats(script, geo)
    return jsonify({**_pack(script), "by": by})


@app.post("/api/preview")
def preview():
    """إطار معاينة سريع (بلا صوت حقيقي): Remotion إن توفّر وإلا PIL."""
    b = body()
    script = sp.normalize(b.get("script"))
    st = stl.normalize(b.get("style"))
    scenes = sp.scenes_of(script)
    i = max(0, min(int(b.get("scene", 0)), len(scenes) - 1))
    OUT.mkdir(exist_ok=True)
    work = OUT / "_prev"
    work.mkdir(exist_ok=True)
    # تقدير التوقيت من عدد الكلمات بلا استدعاء ElevenLabs
    auds = [tts.estimate_timing(sc["narration"]) for sc in scenes]
    plan, total = plan_scenes(script, auds)
    p = plan[i]
    if rem.available() and pick_engine(b.get("engine")) == "remotion":
        try:
            spec = rem.build_spec(script, st, plan, int(round(total * 30)), get_geo(), None, degrade=False)
            sc = spec["scenes"][i]
            bi = max(0, min(int(b.get("beat", 0)), len(sc["beats"]) - 1))
            fr = sc["from"] + sc["beats"][bi]["from"] + int(float(b.get("t", 2.0)) * 30)
            fr = min(fr, sc["from"] + sc["dur"] - 2)
            out = str(work / "preview.jpg")
            rem.render_still(spec, out, fr, str(work))
            return send_file(out, mimetype="image/jpeg")
        except rem.RemError as e:
            return err(str(e), 500)
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
    script = sp.normalize(body().get("script"))
    try:
        res = llm.gemini_json(sp.FACT_SYSTEM, json.dumps(script, ensure_ascii=False))
    except llm.LLMError as e:
        return err(str(e), 502)
    return jsonify(res)


@app.post("/api/render")
def render():
    b = body()
    script = sp.normalize(b.get("script"))
    style = stl.normalize(b.get("style"))
    if not cfg("ELEVENLABS_API_KEY"):
        return err("مفتاح ElevenLabs غير مضبوط. أضفه إلى .env")
    issues = sp.validate(script, get_geo())
    errs = [i["msg"] for i in issues if i["level"] == "error"]
    if errs:
        return err("أصلح الأخطاء أولاً: " + " | ".join(errs))
    jid = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:5]
    job = {"id": jid, "state": "running", "progress": 0.0, "log": [], "result": None, "error": None}
    with LOCK:
        JOBS[jid] = job

    def work():
        try:
            res = produce(script, style, b.get("voice_id", ""), str(OUT / jid), engine=b.get("engine"), photos=b.get("photos"),
                          log=lambda m: job["log"].append(m),
                          progress=lambda f: job.__setitem__("progress", round(f, 3)))
            res["url"] = f"/outputs/{jid}/{res['video']}"
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


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    app.run(host="127.0.0.1", port=int(cfg("PORT", "8000")), threaded=True)
