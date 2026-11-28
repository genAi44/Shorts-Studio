"""مواصفة السكربت: هيكل الأجزاء الثمانية (8 parts) — الموجّه، التطبيع، والتحقق.
1. HOOK (<=14 كلمة)
2. LEAD (<=20 كلمة)
3. BODY 1 (<=25 كلمة)
4. OPEN LOOP 1 (<=12 كلمة)
5. BODY 2 (<=25 كلمة)
6. OPEN LOOP 2 (<=12 كلمة)
7. BODY 3 (<=25 كلمة)
8. CTA / LOOP (<=12 كلمة)
المجموع: 100-140 كلمة.
"""
import copy
import json
import re

WPS = 2.6  # كلمات في الثانية (تقدير للسرد العربي)

# تعريف الأجزاء الثمانية بشكل قائم على البيانات (Data-Driven)
PARTS = [
    {
        "id": "hook",
        "name": "HOOK",
        "title_ar": "1. الخطاف (HOOK)",
        "role": "hook",
        "max_words": 18,
        "desc": "سؤال أو تناقض أو رقم صادم (10–18 كلمة)، بلا تحية ولا يكشف الجواب إطلاقاً."
    },
    {
        "id": "lead",
        "name": "LEAD",
        "title_ar": "2. المقدمة والوعد (LEAD)",
        "role": "lead",
        "max_words": 24,
        "desc": "جملة أو جملتان تضعان الوعد ('بنهاية الفيديو ستعرف كذا') وتمنحان سياقاً كافياً للبقاء (14–24 كلمة)."
    },
    {
        "id": "body1",
        "name": "BODY 1",
        "title_ar": "3. الحقيقة الأولى (BODY 1)",
        "role": "body",
        "max_words": 30,
        "desc": "حقيقة ملموسة أولى أو خطوة محددة تدعم الموضوع بتفاصيل وافية ومحكية (18–30 كلمة)."
    },
    {
        "id": "open_loop1",
        "name": "OPEN LOOP 1",
        "title_ar": "4. الحلقة المفتوحة الأولى (OPEN LOOP 1)",
        "role": "open_loop",
        "max_words": 16,
        "desc": "سطر تشويقي يطرح لغزاً أو تساؤلاً جديداً دون الإجابة عليه الآن (8–16 كلمة)."
    },
    {
        "id": "body2",
        "name": "BODY 2",
        "title_ar": "5. الحقيقة الثانية (BODY 2)",
        "role": "body",
        "max_words": 30,
        "desc": "يجيب على OPEN LOOP 1 ويقدم حقيقة أقوى وصادمة بمزيد من التفصيل (18–30 كلمة)."
    },
    {
        "id": "open_loop2",
        "name": "OPEN LOOP 2",
        "title_ar": "6. الحلقة المفتوحة الثانية (OPEN LOOP 2)",
        "role": "open_loop",
        "max_words": 16,
        "desc": "سطر تشويقي قصير يشوّق لأكبر كشف ومفاجأة قادمة في الفيديو (8–16 كلمة)."
    },
    {
        "id": "body3",
        "name": "BODY 3",
        "title_ar": "7. الذروة والإجابة الكبرى (BODY 3)",
        "role": "body",
        "max_words": 30,
        "desc": "أقوى حقيقة تكشف لغز OPEN LOOP 2 ووعد الـ HOOK بالكامل (18–30 كلمة)."
    },
    {
        "id": "cta",
        "name": "CTA",
        "title_ar": "8. الدعوة والخاتمة الدائرية (CTA)",
        "role": "cta",
        "max_words": 18,
        "desc": "إجراء طبيعي واحد (متابعة أو تعليق) وتتصل كلماته الأخيرة ببداية الـ HOOK لإكمال حلقة الدوران (8–18 كلمة)."
    }
]

PARTS_BY_ID = {p["id"]: p for p in PARTS}
PART_IDS = [p["id"] for p in PARTS]

from .scriptspec_prompts import SYSTEM, FACT_SYSTEM  # noqa: E402,F401 (split out)

GREET = ("مرحبا", "مرحباً", "أهلا", "أهلاً", "السلام", "في هذا الفيديو", "اليوم سنتحدث", "اليوم سوف", "صباح", "مساء")
DISALLOWED_CTA = ("شكرا للمشاهدة", "شكراً للمشاهدة", "شكرا لمتابعتكم", "شكراً لمتابعتكم", "شكرا على المشاهدة")
OPEN_LOOP_TRIGGERS = ("؟", "?", "لكن", "كيف", "لماذا", "هل", "ماذا", "ما هو", "السر", "المفاجأة", "انتظر", "ترى", "ترى كيف", "يا ترى")


def user_prompt(idea, note=""):
    s = "Video idea (Arabic):\n" + idea.strip()
    if note.strip():
        s += "\n\nAdditional notes:\n" + note.strip()
    return s


DANGLING_ENDS = {"التي", "الذي", "الذين", "اللتي", "اللاتي", "في", "من", "إلى", "على", "عن", "مع", "أن", "عندما", "حين", "و", "أو", "ثم", "لكن"}


def nwords(s):
    return len(re.findall(r"\S+", s or ""))


def _vis(v):
    return v if isinstance(v, dict) else {"type": "text"}


_STRAY_SCRIPT_RE = re.compile(r"[\u0400-\u04FF\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]+")


def _clean_stray_scripts(s: str) -> str:
    return _STRAY_SCRIPT_RE.sub("", s or "").strip()


def normalize_part(data, part_def):
    p = data if isinstance(data, dict) else {}
    out = {
        "narration": _clean_stray_scripts(str(p.get("narration", ""))),
        "on_screen": _clean_stray_scripts(str(p.get("on_screen", ""))),
        "visual": _vis(p.get("visual"))
    }
    if isinstance(p.get("beats"), list):
        out["beats"] = [x for x in p["beats"] if isinstance(x, dict)]
    if isinstance(p.get("visuals"), list):
        out["visuals"] = [x for x in p["visuals"] if isinstance(x, dict)]
    if isinstance(p.get("transition"), dict):
        out["transition"] = dict(p["transition"])
    return out


def normalize(script):
    """يطبّع السكربت وفق الهيكل الجديد المكون من 8 أجزاء مع الحفاظ الكامل على التوافق الرجعي للسكربتات القديمة."""
    s = copy.deepcopy(script) if isinstance(script, dict) else {}
    s["title"] = str(s.get("title", "")).strip()
    s["description"] = str(s.get("description", "")).strip()
    tags = s.get("tags", [])
    if isinstance(tags, str):
        tags = [t for t in re.split(r"[,،\n]", tags)]
    s["tags"] = [str(t).strip().lstrip("#") for t in tags if str(t).strip()]

    # فحص ما إذا كان السكربت بالصيغة القديمة (hook + body قائمة + loop)
    old_body = s.get("body") if isinstance(s.get("body"), list) else None
    is_old_format = old_body is not None and not any(k in s for k in ("lead", "body1", "open_loop1", "body2", "body3"))

    if is_old_format:
        # خريطة تحويل متوافقة من القديم إلى الأجزاء الثمانية الجديدة
        s["hook"] = normalize_part(s.get("hook"), PARTS_BY_ID["hook"])
        s["lead"] = normalize_part(old_body[0] if len(old_body) > 0 else {}, PARTS_BY_ID["lead"])
        s["body1"] = normalize_part(old_body[1] if len(old_body) > 1 else (old_body[0] if old_body else {}), PARTS_BY_ID["body1"])
        s["open_loop1"] = {
            "narration": "لكن ما السر الذي يخفيه هذا التاريخ؟",
            "on_screen": "لغز محيّر",
            "visual": {"type": "text", "text": "لغز محيّر"}
        }
        s["body2"] = normalize_part(old_body[2] if len(old_body) > 2 else (old_body[1] if len(old_body) > 1 else {}), PARTS_BY_ID["body2"])
        s["open_loop2"] = {
            "narration": "والسؤال الأكبر، كيف حُسم الأمر نهائياً؟",
            "on_screen": "المفاجأة الكبرى",
            "visual": {"type": "text", "text": "المفاجأة الكبرى"}
        }
        s["body3"] = normalize_part(old_body[3] if len(old_body) > 3 else (old_body[-1] if old_body else {}), PARTS_BY_ID["body3"])
        cta_obj = s.get("loop") if isinstance(s.get("loop"), dict) else {}
        cta_narr = str(cta_obj.get("narration", "")).strip()
        if not cta_narr:
            cta_narr = "تابعنا للمزيد واكتب رأيك في التعليقات، وتساءل معنا:"
        s["cta"] = {
            "narration": cta_narr,
            "on_screen": "شاركنا برأيك",
            "visual": {"type": "text", "text": "شارك برأيك"}
        }
    else:
        # السكربت بالصيغة الجديدة للأجزاء الثمانية
        for pdef in PARTS:
            pid = pdef["id"]
            raw_val = s.get(pid)
            if raw_val is None and pid == "cta":
                raw_val = s.get("loop")
            s[pid] = normalize_part(raw_val, pdef)

    # حقول التوافق الرجعي: body كقائمة و loop كمرادف لـ cta
    s["body"] = [s["body1"], s["body2"], s["body3"]]
    s["loop"] = {"narration": s["cta"]["narration"]}

    # قائمة الحقائق
    f = s.get("facts", [])
    norm_facts = []
    if isinstance(f, list):
        for x in f:
            if isinstance(x, dict):
                c = str(x.get("claim", "")).strip()
                src = str(x.get("source", "")).strip()
                if c:
                    norm_facts.append({"claim": c, "source": src})
            elif str(x).strip():
                norm_facts.append({"claim": str(x).strip(), "source": ""})
    s["facts"] = norm_facts
    return s


def scenes_of(script):
    """يعيد قائمة المشاهد الثمانية بالترتيب الدقيق، بحيث يحصل كل جزء على مشهده الخاص."""
    s = normalize(script)
    # every scene carries its visual-intelligence plan (locations, needs_map_overlay...): the copies built here used to lose it,
    # so the map builder never saw the scene's place (no map at all when the entity extractor found nothing, e.g. "مدن أمريكية")
    vi = script.get("_visual_intelligence") if isinstance(script, dict) else None
    vi_by_id = {v.get("id"): v for v in (vi.get("scenes") or []) if isinstance(v, dict)} if isinstance(vi, dict) else {}
    scenes = []
    for p in PARTS:
        pid = p["id"]
        sc = {
            "id": pid,
            "role": p["role"],
            "part_name": p["name"],
            "title_ar": p["title_ar"],
            **s[pid]
        }
        if pid in vi_by_id and not sc.get("_vi"):
            sc["_vi"] = vi_by_id[pid]
        scenes.append(sc)
    return scenes


def total_words(script):
    s = normalize(script)
    return sum(nwords(s[p["id"]]["narration"]) for p in PARTS)


def script_errors(script, geo=None):
    """يتحقق من القيود الصارمة؛ يعيد قائمة برسائل الأخطاء فقط (الأخطاء تمنع التوليد)."""
    s = normalize(script)
    issues = validate(s, geo)
    return [i["msg"] for i in issues if i["level"] == "error"]


def estimate(script):
    tw = total_words(script)
    return {"words": tw, "seconds": round(tw / WPS, 1)}


def dumps(o):
    return json.dumps(o, ensure_ascii=False, indent=2)


# Re-exported so `pipeline.scriptspec.validate` keeps working.
from .scriptspec_validate import validate  # noqa: E402,F401
