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

SYSTEM = """أنت كاتب سكربتات محترف لفيديوهات Shorts العربية القصيرة (عمودية، 45 إلى 55 ثانية). مهمتك تحويل فكرة المستخدم إلى سكربت مقسّم بدقة صارمة إلى ثمانية أجزاء متسلسلة (8 Parts)، في هذا الترتيب الدقيق:

الهيكل الإلزامي (8 أجزاء):
1. HOOK (الخطاف — أول 3 ثوانٍ):
   - من 10 إلى 18 كلمة.
   - سؤال أو تناقض حقيقي أو رقم صادم يجبر المشاهد على التوقف.
   - ممنوع منعاً باتاً أي تحية (مثل: مرحباً، أهلاً، السلام عليكم) وممنوع كشف الجواب هنا.

2. LEAD (المقدمة والوعد):
   - من 14 إلى 24 كلمة.
   - تضع وعداً واضحاً ومثيراً للمشاهد ("في الثواني القادمة ستكتشف...") وتمنحه سياقاً كافياً للاستمرار في المشاهدة.

3. BODY 1 (الحقيقة الأولى):
   - من 18 إلى 30 كلمة.
   - حقيقة ملموسة أولى مدعومة ببيانات وتفاصيل واقعية، مكتوبة بلغة محكية طبيعية وممتعة دون حشو.

4. OPEN LOOP 1 (الحلقة المفتوحة الأولى — تشويق):
   - سطر واحد مشوّق جداً، من 8 إلى 16 كلمة.
   - يطرح سؤالاً مفاجئاً أو يشوّق للغز جديد دون الإجابة عليه الآن، لخلق توتر وفضول.

5. BODY 2 (الحقيقة الثانية):
   - من 18 إلى 30 كلمة.
   - يجيب على OPEN LOOP 1 ويقدم حقيقة أقوى وصادمة تكشف عمق القصة.

6. OPEN LOOP 2 (الحلقة المفتوحة الثانية — ذروة الترقب):
   - سطر تشويقي حاسم، من 8 إلى 16 كلمة.
   - يمهّد لأكبر كشف والمفاجأة الحاسمة في القصة.

7. BODY 3 (الذروة والإجابة الكبرى):
   - من 18 إلى 30 كلمة.
   - أقوى جواب وأهم معلومة؛ تحسم لغز OPEN LOOP 2 وتفي بوعد الـ HOOK بالكامل.

8. CTA (الدعوة والخاتمة الدائرية Loop):
   - سطر ذكي، من 8 إلى 18 كلمة.
   - إجراء طبيعي واحد فقط (متابعة الحساب، أو تعليق برأي، أو إجابة سؤال). ممنوع "شكراً للمشاهدة".
   - تنتهي كلماته الأخيرة بعبارة معلّقة (مثل فاصلة أو نقطتين) تتصل نحوياً ومفهوماً بأول كلمة في الـ HOOK، ليدور الفيديو إلى ما لا نهاية.

قواعد اللغة والطول والترابط السردي الإلزامي (هام جداً):
- قاعدة الوفاء بوعد الخطاف (Hook-to-Body Payoff): يمنع منعاً باتاً طرح سؤال أو لغز في الـ HOOK ثم تجاهله في المشاهد التالية بسرد معلومات عامة أو أرقام سطحية بديهية! يجب أن يشرح كل مشهد في المتن (BODY 1, BODY 2, BODY 3, OPEN LOOP) الحقيقة التاريخية أو الجغرافية المدهشة التي تجيب مباشرة على سؤال الـ HOOK (مثلاً: كيف انتقلت العاصمة من مدينة تاريخية سابقة كالفسطاط أو كيوتو أو ريو دي جانيرو أو فيلادلفيا، أو لماذا بُنيت العاصمة في موقع استراتيجي خاص).
- إذا طلب المستخدم استعراض عدة دول وعواصمها (مثل 5 دول وعواصمها)، يجب ذكر كل دولة وعاصمتها صراحةً بالاسم داخل السرد الصوتي (narration) مع حقيقة تاريخية/جغرافية ذكية ومقارنة حقيقية لكل منها.
- الطول الإجمالي الإلزامي: بين 100 و150 كلمة (المستهدف المثالي هو 115 إلى 145 كلمة ≈ 45 إلى 58 ثانية). إياك أن تجعل السكربت قصيراً (أقل من 95 كلمة سيتم رفضه). فصّل في سرد الحقائق لملء المدة المحددة (حتى 58 ثانية).
- لغة عربية فصحى معاصرة ومحكية بطبيعية تامة (كأنها حوار شفهي ذكي ومشوّق)، وليست لغة مقالات كتابية جافة.
- اكتب الأرقام والسنوات بالحروف كاملة داخل narration (مثال: ثلاثة آلاف وستمئة وخمسون متراً)، وبالأرقام في on_screen و visual.
- كل ادعاء يجب أن يكون ملموساً وقابلاً للتحقق مع ذكر مصدره في قائمة facts.

المشهد البصري (visual) لكل جزء من الأجزاء الثمانية:
- map: للأماكن والحدود {"type":"map","countries":["BOL"],"highlight":["BOL"],"points":[{"name":"لاباز","lat":-16.5,"lon":-68.15}]}
- stat: للأرقام والنسب {"type":"stat","number":"3,650","label":"متراً فوق سطح البحر"}
- text: لعبارة مميزة على الشاشة {"type":"text","text":"عبارة قصيرة"}

مثال واقعي للسكربت المطلوب (JSON — طول السرد فيه 118 كلمة متقنة):
{
  "title": "لماذا تملك بوليفيا عاصمتين؟",
  "description": "قصة الانقسام التاريخي بين سوكري ولاباز وعاصمتي بوليفيا.\\n\\n#جغرافيا #تاريخ #بوليفيا",
  "tags": ["بوليفيا", "عواصم العالم", "سوكري", "لاباز"],
  "hook": {
    "narration": "لماذا تملك دولة واحدة في قلب أمريكا الجنوبية عاصمتين رسميّتين بدلاً من عاصمة واحدة؟",
    "on_screen": "لغز عاصمتي بوليفيا",
    "visual": {"type": "map", "countries": ["BOL"], "highlight": ["BOL"], "points": []}
  },
  "lead": {
    "narration": "في الثواني القادمة ستكتشف السر التاريخي المثير الذي شطر مقاليد الحكم والسيادة بين مدينتين متباعدتين تماماً.",
    "on_screen": "سر الشطر التاريخي",
    "visual": {"type": "text", "text": "سر الشطر التاريخي"}
  },
  "body1": {
    "narration": "كانت مدينة سوكري العاصمة الدستورية الأصلية ومقر القضاء الأعلى منذ نيل الاستقلال عام ألف وثمانمئة وخمسة وعشرين.",
    "on_screen": "سوكري: العاصمة التاريخية",
    "visual": {"type": "stat", "number": "1825", "label": "سنة إعلان الاستقلال"}
  },
  "open_loop1": {
    "narration": "لكن ما الذي دفع نخب الشمال للتمرد وإشعال نزاع مسلح فجأة؟",
    "on_screen": "لماذا تمرد الشمال؟",
    "visual": {"type": "text", "text": "سر تمرد الشمال"}
  },
  "body2": {
    "narration": "اندلعت حرب أهلية دامية طاحنة عام ألف وثمانمئة وتسعة وتسعين جعلت لاباز المركز الاقتصادي والسياسي الفعلي للحكومة والبرلمان.",
    "on_screen": "لاباز: مقر السلطة",
    "visual": {"type": "map", "countries": ["BOL"], "highlight": ["BOL"], "points": [{"name": "لاباز", "lat": -16.5, "lon": -68.15}]}
  },
  "open_loop2": {
    "narration": "والسؤال الأكبر، كيف تفادى الدستور تجدد شبح الحرب الأهلية؟",
    "on_screen": "حسم النزاع الدستوري",
    "visual": {"type": "text", "text": "حسم النزاع"}
  },
  "body3": {
    "narration": "أقر الدستور بقاء سوكري العاصمة الرمزية والتاريخية، بينما تدير لاباز شؤون الدولة الفعلية لتفادي الاقتتال والانقسام.",
    "on_screen": "تسوية العاصمتين",
    "visual": {"type": "text", "text": "التسوية الدستورية"}
  },
  "cta": {
    "narration": "تابعنا للمزيد من أسرار العالم واكتب عاصمة بلدك في التعليقات، وتساءل معنا:",
    "on_screen": "شاركنا برأيك",
    "visual": {"type": "text", "text": "اكتب تعليقك"}
  },
  "facts": [
    {"claim": "سوكري هي العاصمة الدستورية لبوليفيا منذ 1825", "source": "دستور بوليفيا - المادة 11"},
    {"claim": "لاباز مقر الحكومة الفعلي منذ حرب 1899 الفيدرالية", "source": "وثائق التاريخ البوليفي المعاصر"},
    {"claim": "دستور بوليفيا لعام 2009 يثبت سوكري عاصمة تاريخية ولاباز مقراً للرئاسة", "source": "دستور بوليفيا 2009"}
  ]
}

أعد JSON فقط بهذا الشكل وبالمفاتيح الثمانية بالضبط."""

FACT_SYSTEM = """أنت مدقّق حقائق صارم. ستستلم سكربت فيديو قصير بصيغة JSON مكوناً من 8 أجزاء. افحص كل ادعاء واقعي في السرد وفي قائمة facts (أسماء، أرقام، تواريخ، أماكن، إحداثيات النقاط، رموز الدول ISO3). لا تخترع: إن لم تتأكد فقل uncertain.

أعد JSON فقط:
{
  "overall": "pass" | "warn" | "fail",
  "items": [{"claim": "...", "status": "correct" | "incorrect" | "uncertain", "note": "...", "fix": "نص بديل مقترح أو فارغ"}],
  "narration_fixes": [{"scene": "hook" | "lead" | "body1" | "open_loop1" | "body2" | "open_loop2" | "body3" | "cta", "narration": "السرد المصحَّح كاملاً"}],
  "packaging": {"title": "حتى 55 حرفاً", "description": "أول سطر يكرّر الكلمة المفتاحية", "tags": ["3 إلى 5 وسوم"]}
}"""

GREET = ("مرحبا", "مرحباً", "أهلا", "أهلاً", "السلام", "في هذا الفيديو", "اليوم سنتحدث", "اليوم سوف", "صباح", "مساء")
DISALLOWED_CTA = ("شكرا للمشاهدة", "شكراً للمشاهدة", "شكرا لمتابعتكم", "شكراً لمتابعتكم", "شكرا على المشاهدة")
OPEN_LOOP_TRIGGERS = ("؟", "?", "لكن", "كيف", "لماذا", "هل", "ماذا", "ما هو", "السر", "المفاجأة", "انتظر", "ترى", "ترى كيف", "يا ترى")


def user_prompt(idea, note=""):
    s = "فكرة الفيديو:\n" + idea.strip()
    if note.strip():
        s += "\n\nملاحظات إضافية:\n" + note.strip()
    return s


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
        scenes.append(sc)
    return scenes


def total_words(script):
    s = normalize(script)
    return sum(nwords(s[p["id"]]["narration"]) for p in PARTS)


def validate(script, geo=None):
    """يعيد قائمة بالملاحظات والأخطاء {level: error|warn, where, msg}. الأخطاء تمنع التوليد."""
    s = normalize(script)
    out = []

    def add(level, where, msg):
        out.append({"level": level, "where": where, "msg": msg})

    # 1. فحص كل جزء من الأجزاء الثمانية وقيود كلماته
    for p in PARTS:
        pid = p["id"]
        role = p["role"]
        max_w = p["max_words"]
        text = s[pid]["narration"]
        nw = nwords(text)

        if nw == 0:
            add("error", pid, f"الجزء '{p['name']}' ({p['title_ar']}) فارغ.")
            continue

        if nw > max_w:
            add("warn", pid, f"الجزء '{p['name']}' يحتوي {nw} كلمة وتجاوز الحد المستحسن ({max_w} كلمة).")

        # فحص خاص بالـ HOOK
        if role == "hook":
            if any(g in text for g in GREET):
                add("error", pid, "الـ HOOK يحتوي تحية أو مقدمة (ممنوع). ادخل مباشرة في التناقض أو السؤال.")
            has_q = "؟" in text or "?" in text
            has_num = bool(re.search(r"\d|[٠-٩]", text))
            has_paradox = any(w in text for w in ("لماذا", "كيف", "هل", "رغم", "لكن", "بينما"))
            if not (has_q or has_num or has_paradox):
                add("error", pid, "الـ HOOK يجب أن يحتوي صراحة على سؤال، أو رقم صادم، أو تناقض حقيقي.")

        # فحص خاص بحلقات التشويق OPEN LOOP 1 & 2
        if role == "open_loop":
            is_teaser = any(t in text for t in OPEN_LOOP_TRIGGERS)
            if not is_teaser:
                add("error", pid, f"الجزء '{p['name']}' يجب أن يكون سطراً تشويقياً يطرح لغزاً أو سؤالاً (يحتوي علامة استفهام أو أداة تشويق) وليس خبراً عادياً.")

        # فحص خاص بـ CTA
        if role == "cta":
            if any(d in text for d in DISALLOWED_CTA):
                add("error", pid, "الـ CTA يحتوي على عبارات مثل 'شكراً للمشاهدة'، وهذا ممنوع.")
            # التحقق من أن الكلمات الأخيرة تتصل بالبداية
            if not re.search(r"[:،,…ـ-]\s*$", text) and not text.endswith("؟"):
                add("warn", pid, "يُفضل أن تنتهي كلمات الـ CTA الأخيرة بنقطتين ':' أو فاصلة لربطها بالـ HOOK في دورة لا نهائية.")

        # فحص نص الشاشة
        if nwords(s[pid]["on_screen"]) > 6:
            add("warn", pid, f"نص الشاشة في '{p['name']}' أطول من 6 كلمات.")

    # 2. فحص مجموع الكلمات والمدة
    tw = total_words(s)
    est = tw / WPS
    if tw < 95:
        add("error", "all", f"مجموع كلمات السكربت {tw} كلمة وهو أقل من الحد الأدنى المطلوب (المطلوب 100–150 كلمة).")
    elif tw < 105:
        add("warn", "all", f"مجموع كلمات السكربت {tw} كلمة؛ المستحسن زيادة الكلمات لتكون بين 110 و145 كلمة.")
    elif tw > 155:
        add("warn", "all", f"مجموع كلمات السكربت {tw} كلمة وتجاوز الحد المستحسن (100–150 كلمة)؛ المدة المقدّرة ≈ {est:.0f} ثانية.")
    elif tw > 140:
        add("warn", "all", f"مجموع كلمات السكربت {tw} كلمة؛ المدة المقدّرة ≈ {est:.0f} ثانية (ضمن نطاق الـ Shorts).")

    if est > 60:
        add("warn", "all", f"المدة المقدّرة ≈ {est:.0f} ثانية؛ فوق 60 ثانية قد يتجاوز السقف الزمني للـ Shorts.")

    # 3. فحص المشاهد البصرية
    for p in PARTS:
        pid = p["id"]
        v = s[pid]["visual"]
        ty = v.get("type")
        if ty not in ("map", "stat", "text"):
            add("error", pid, f"نوع المشهد البصري في '{p['name']}' غير معروف: {ty!r} (يجب أن يكون map أو stat أو text).")
            continue
        if ty == "map":
            cs = [str(c).upper() for c in (v.get("countries") or []) + (v.get("highlight") or [])]
            pts = v.get("points") or []
            if not cs and not pts:
                add("error", pid, f"مشهد map في '{p['name']}' بلا دول ولا نقاط.")
            if geo is not None:
                for c in cs:
                    if not geo.has(c):
                        add("error", pid, f"رمز الدولة {c} غير موجود في بيانات الخرائط.")
            for pt in pts:
                try:
                    la, lo = float(pt["lat"]), float(pt["lon"])
                    assert -90 <= la <= 90 and -180 <= lo <= 180
                except Exception:
                    add("error", pid, f"نقطة بإحداثيات غير صالحة في '{p['name']}': {pt!r}")
        elif ty == "stat" and not str(v.get("number", "")).strip():
            add("error", pid, f"مشهد stat في '{p['name']}' بلا حقل number.")
        elif ty == "text" and not (str(v.get("text", "")).strip() or s[pid]["on_screen"]):
            add("error", pid, f"مشهد text في '{p['name']}' بلا نص.")

    # 4. التعبئة والحقائق
    if len(s["title"]) == 0:
        add("warn", "meta", "لا يوجد عنوان.")
    elif len(s["title"]) > 55:
        add("warn", "meta", f"العنوان {len(s['title'])} حرفاً والمستحسن 55 أو أقل.")
    if "#shorts" in s["title"].lower():
        add("warn", "meta", "لا حاجة لوسم #shorts في العنوان.")
    if not 3 <= len(s["tags"]) <= 5:
        add("warn", "meta", "المستحسن 3 إلى 5 وسوم.")
    if not s["facts"]:
        add("warn", "meta", "قائمة facts فارغة؛ سيضعف فحص الحقائق.")

    # 4b. التحقق من تطابق العدد الموعود (مثلاً "5 دول") مع عدد العناصر المذكورة في body1..body3
    title_lead = f"{s.get('title', '')} {s['lead']['narration']}"
    if re.search(r"(?:^|\s)(?:5|٥|خمس|خمسة)\s+(?:دول|عواصم|مدن|أماكن|حقائق|أشياء|أسباب|قواعد|أسرار)", title_lead):
        body_text = " ".join(s[bid]["narration"] for bid in ("body1", "body2", "body3"))
        if ("ثالثاً" in body_text or "ثالثا" in body_text) and not any(
            ord_w in body_text for ord_w in ("رابعاً", "رابعا", "الرابعة", "الرابع", "خامساً", "خامسا", "الخامسة", "الخامس")
        ):
            add("error", "body", "العنوان أو المقدمة تعد بـ 5 عناصر، لكن body1..body3 توقفت عند العنصر الثالث فقط! أضف العنصرين الرابع والخامس في body2 و body3.")

    # 5. فحص العناصر البصرية الإضافية (QA Visual Review: clutter, overlap, emoji spam, icon consistency)
    try:
        from . import visual_tools
        qa_issues = visual_tools.qa_visual_review({"scenes": scenes_of(s)})
        for qi in qa_issues:
            add(qi.get("level", "warn"), qi.get("where", "all"), qi.get("msg", ""))
    except Exception:
        pass

    return out


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
