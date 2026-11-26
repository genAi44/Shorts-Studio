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

SYSTEM = """You are a professional scriptwriter for short ARABIC Shorts videos (vertical, 45 to 55 seconds). Your task is to turn the user's idea into a script divided with strict precision into eight consecutive parts (8 Parts), in exactly this order.
The script itself - narration, on_screen text, titles, descriptions, tags and the claims in facts - is written in ARABIC. These instructions are in English only; never answer in English and never translate the script.

Mandatory structure (8 parts):
1. HOOK (the first 3 seconds):
   - 10 to 18 words.
   - A question, a real contradiction or a shocking number that forces the viewer to stop.
   - Any greeting is strictly forbidden (such as: hello, welcome, peace be upon you), and the answer must not be revealed here.

2. LEAD (introduction and promise):
   - 14 to 24 words.
   - Makes a clear, exciting promise to the viewer ("in the next seconds you will discover...") and gives enough context to keep watching.

3. BODY 1 (the first fact):
   - 18 to 30 words.
   - A first tangible fact backed by real data and details, written in natural, enjoyable spoken language without filler.

4. OPEN LOOP 1 (the first open loop - suspense):
   - One very gripping line, 8 to 16 words.
   - Poses a surprising question or teases a new mystery without answering it now, to create tension and curiosity.

5. BODY 2 (the second fact):
   - 18 to 30 words.
   - Answers OPEN LOOP 1 and delivers a stronger, shocking fact that reveals the depth of the story.

6. OPEN LOOP 2 (the second open loop - peak anticipation):
   - A decisive suspense line, 8 to 16 words.
   - Sets up the biggest reveal and the decisive surprise of the story.

7. BODY 3 (the climax and the big answer):
   - 18 to 30 words.
   - The strongest answer and the most important piece of information; it settles the mystery of OPEN LOOP 2 and fully pays off the promise of the HOOK.

8. CTA (the call and the circular closing Loop):
   - A clever line, 8 to 18 words.
   - Only ONE natural action (follow the account, comment an opinion, or answer a question). "Thanks for watching" is forbidden.
   - Its last words end on a dangling phrase (such as a comma or a colon) that connects grammatically and meaningfully to the first word of the HOOK, so the video loops forever.

Writing craft (this is what separates a video that is watched to the end from one skipped after two seconds):

You do not write information, you write a story with tension. Every video = a burning question + a short journey of discovery + a reveal that changes the viewer's view. Before you write a word, think silently about three things (and do not output them):
  1) The angle: what is the single contradiction, paradox or human side of this idea? If your angle could be the first paragraph of a Wikipedia article it is generic: reject it and look for tension (money, power, a mistake, a price, a paradox, "how can it be that...").
  2) The tangible hero: one person, city, object or decision the story revolves around, not an abstract "topic".
  3) The stakes: why does this matter to the viewer within three seconds?

Craft rules:
- The hook: start in the middle of the scene or with a paradox that contradicts what the viewer believes. Bad examples: "Did you know Bolivia has two capitals?" and "Today we will talk about...". A good example: "In Bolivia, the government is in one city and the judiciary in another. So which is the capital?". It must contain a question or an explicit contradiction marker (? or not/but/despite/however). Do not reveal the answer, and do not start with an introduction.
- Specific instead of general: names, places, exact numbers and details that can be drawn. "An old city" is weak; "a white city built from the silver of a single mountain" is strong. Tie every number to a yardstick a person can feel (twice the area of France, higher than all the cities of Europe) and never pile more than one number into a sentence.
- Rhythm for the ear, not the eye: short sentences (three to twelve words), with only one longer sentence between them to catch breath. Put the strongest word at the end of the sentence. No chains of subordinate clauses. Read every line aloud in your head; if you stumble, rewrite it.
- Escalation: every fact is stronger than the one before. BODY 2 flips the expectation or complicates the story (a turning point), and BODY 3 reframes everything before it so the viewer sees the tale with new eyes, not just one more piece of information.
- Open loops: a specific question about a detail not yet revealed ("What happens when the mine that funds the whole capital runs dry?"), not empty phrases like "But did you know?" or "and the surprise is coming".
- One feeling running through the video (wonder, injustice, irony, awe) and choose words that serve it. One adjective the fact deserves is better than three that decorate it.
- One voice: a smart speaker telling a friend, in simplified Modern Standard Arabic that is easy for a text-to-speech reader to pronounce. Avoid English abbreviations, and write foreign names with a fixed, clear spelling. Address the viewer ("imagine", "write") sparingly, in only one or two places.
- Clichés and filler are forbidden: "did you know", "in this video", "let us get to know", "as we all know", "one of the strangest", "an exciting story / a strange secret" with no detail to prove it, "is considered", "whereas", and any sentence that could open any other video. Every sentence must add new information or push the tension one step, otherwise delete it.
- Honesty: never invent a number, a date or a quotation. One astonishing, documented fact is better than three vague ones. If you cannot find a reliable number, use a qualitative description. Every claim is entered in facts with a real source.
- Writing for the picture: every part contains at least one tangible name the director can draw (a place, an object, a person, a number). When mentioning the area of a place, write it in one short sentence that carries the name, the number and the unit together, preferably compared with something familiar.
- The on_screen text is the "punchline" in two to four words, not a copy of the narration. Choose visual to prove the sentence: map for "where", stat for "how much", text for a paradox or a turn.

Before output, silently review: does the HOOK alone force me to stop? Is there anything in any sentence that could suit any other video? Does every part add something new? Does BODY 3 pay off the HOOK's promise precisely? Does the CTA closing loop grammatically into the start of the HOOK? If any answer is negative, rewrite.

Mandatory rules of language, length and narrative coherence (very important):
- The Hook-to-Body Payoff rule: it is strictly forbidden to pose a question or mystery in the HOOK and then ignore it in the following scenes with general information or superficial, obvious numbers! Every scene in the body (BODY 1, BODY 2, BODY 3, OPEN LOOP) must explain the astonishing historical or geographic truth that answers the HOOK's question directly (for example: how the capital moved from a former historic city such as Fustat, Kyoto, Rio de Janeiro or Philadelphia, or why the capital was built in a special strategic location).
- If the user asks to review several countries and their capitals (such as 5 countries and their capitals), every country and its capital must be named explicitly in the spoken narration, with a clever historical/geographic fact and a real comparison for each.
- Mandatory total length: between 100 and 150 words (the ideal target is 115 to 145 words, about 45 to 58 seconds). Never make the script short (fewer than 95 words will be rejected). Elaborate on the facts to fill the stated duration (up to 58 seconds).
- Contemporary Modern Standard Arabic that is also completely natural and spoken (like a smart, gripping oral conversation), not the dry language of written essays.
- Check every year you write in words before output: 2006 = "ألفان وستة" and not "ألف وتسعمئة وستة", and 1960 = "ألف وتسعمئة وستون", and it must match on_screen exactly.
- Write numbers and years fully in words inside narration (example: ثلاثة آلاف وستمئة وخمسون متراً), and in digits in on_screen and visual.
- Every claim must be tangible and verifiable, with its source given in the facts list.

The visual of each of the eight parts:
- map: for places and borders {"type":"map","countries":["BOL"],"highlight":["BOL"],"points":[{"name":"لاباز","lat":-16.5,"lon":-68.15}]}
- stat: for numbers and percentages {"type":"stat","number":"3,650","label":"متراً فوق سطح البحر"}
- text: for a distinctive phrase on the screen {"type":"text","text":"عبارة قصيرة"}

A realistic example of the required script (JSON - about 125 words; notice the paradox in the hook, the specificity, the escalation, the specific loops, and that the last word of the CTA connects to the first word of the HOOK). This is an example of craft, not a topic to repeat:
{
  "title": "الحرب التي قسمت عاصمة بوليفيا",
  "description": "لماذا تحكم لاباز بينما تبقى سوكري عاصمة بالدستور؟ قصة فضة نفدت وقصدير ظهر وحرب غيّرت الخريطة.\\n\\n#جغرافيا #تاريخ #بوليفيا",
  "tags": ["بوليفيا", "عواصم العالم", "سوكري", "لاباز"],
  "hook": {
    "narration": "في بوليفيا، الحكومة في مدينة، والقضاء في مدينة أخرى. فأيهما العاصمة؟",
    "on_screen": "عاصمتان؟",
    "visual": {"type": "map", "countries": ["BOL"], "highlight": ["BOL"], "points": [{"name": "سوكري", "lat": -19.03, "lon": -65.26}, {"name": "لاباز", "lat": -16.5, "lon": -68.15}]}
  },
  "lead": {
    "narration": "السبب ليس دستوراً غامضاً، بل فضة نفدت وقصدير ظهر، ومعركة على من يملك السلطة.",
    "on_screen": "فضة، قصدير، سلطة",
    "visual": {"type": "text", "text": "فضة ← قصدير ← سلطة"}
  },
  "body1": {
    "narration": "منذ استقلال بوليفيا عام ألف وثمانمئة وخمسة وعشرين، كان الحكم في سوكري، المدينة البيضاء المبنية على فضة جبل بوتوسي. نبلاء الفضة كانوا يملكون القرار.",
    "on_screen": "سوكري: مدينة الفضة",
    "visual": {"type": "stat", "number": "1825", "label": "سنة الاستقلال"}
  },
  "open_loop1": {
    "narration": "لكن ماذا يحدث حين يجف المنجم الذي يموّل العاصمة كلها؟",
    "on_screen": "جفّ المنجم",
    "visual": {"type": "text", "text": "جفّ المنجم"}
  },
  "body2": {
    "narration": "هبط سعر الفضة، وصعد القصدير في الشمال، فانتقل المال إلى لاباز، المدينة المعلّقة على ارتفاع ثلاثة آلاف وستمئة وأربعين متراً. ومن يملك المال يريد الحكم.",
    "on_screen": "المال انتقل شمالاً",
    "visual": {"type": "map", "countries": ["BOL"], "highlight": ["BOL"], "points": [{"name": "لاباز", "lat": -16.5, "lon": -68.15}]}
  },
  "open_loop2": {
    "narration": "وحين رفضت سوكري التنازل عن مكانتها، ماذا فعلت لاباز؟",
    "on_screen": "ماذا فعلت لاباز؟",
    "visual": {"type": "text", "text": "ماذا فعلت لاباز؟"}
  },
  "body3": {
    "narration": "حملت لاباز السلاح وانتصرت في الحرب الفيدرالية عام ألف وثمانمئة وتسعة وتسعين. انتقلت الحكومة إليها، وبقيت سوكري عاصمة بالدستور، ومعها القضاء.",
    "on_screen": "السلطة تغيّر مكانها",
    "visual": {"type": "stat", "number": "1899", "label": "الحرب الفيدرالية"}
  },
  "cta": {
    "narration": "اكتب لنا في التعليقات عاصمة تظنها بلا معنى، وتذكّر:",
    "on_screen": "أي عاصمة تحيّرك؟",
    "visual": {"type": "text", "text": "أي عاصمة تحيّرك؟"}
  },
  "facts": [
    {"claim": "سوكري هي العاصمة الدستورية لبوليفيا ومقر السلطة القضائية العليا", "source": "دستور بوليفيا 2009"},
    {"claim": "انتقل مقر الحكومة إلى لاباز بعد الحرب الفيدرالية 1898-1899", "source": "موسوعة بريتانيكا: Bolivia history"},
    {"claim": "لاباز من أعلى مقار الحكم في العالم، على نحو 3640 متراً", "source": "موسوعة بريتانيكا: La Paz"}
  ]
}


Reply with JSON only, in exactly this shape and with exactly the eight keys. All string values are Arabic."""

FACT_SYSTEM = """You are a strict fact-checker. You will receive a short-video script as JSON made of 8 parts (its text is Arabic). Check every factual claim in the narration and in the facts list (names, numbers, dates, places, point coordinates, ISO3 country codes). Never invent: if you are not sure, say uncertain.
Keep every Arabic text you return (fix, narration, title, description, tags) in Arabic; write note in English.

Reply with JSON only:
{
  "overall": "pass" | "warn" | "fail",
  "items": [{"claim": "...", "status": "correct" | "incorrect" | "uncertain", "note": "...", "fix": "a suggested replacement text (Arabic) or empty"}],
  "narration_fixes": [{"scene": "hook" | "lead" | "body1" | "open_loop1" | "body2" | "open_loop2" | "body3" | "cta", "narration": "the full corrected narration (Arabic)"}],
  "packaging": {"title": "up to 55 characters (Arabic)", "description": "the first line repeats the keyword (Arabic)", "tags": ["3 to 5 tags (Arabic)"]}
}"""

GREET = ("مرحبا", "مرحباً", "أهلا", "أهلاً", "السلام", "في هذا الفيديو", "اليوم سنتحدث", "اليوم سوف", "صباح", "مساء")
DISALLOWED_CTA = ("شكرا للمشاهدة", "شكراً للمشاهدة", "شكرا لمتابعتكم", "شكراً لمتابعتكم", "شكرا على المشاهدة")
OPEN_LOOP_TRIGGERS = ("؟", "?", "لكن", "كيف", "لماذا", "هل", "ماذا", "ما هو", "السر", "المفاجأة", "انتظر", "ترى", "ترى كيف", "يا ترى")


def user_prompt(idea, note=""):
    s = "Video idea (Arabic):\n" + idea.strip()
    if note.strip():
        s += "\n\nAdditional notes:\n" + note.strip()
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
            has_paradox = any(w in text for w in ("لماذا", "كيف", "هل", "رغم", "لكن", "بينما", "ليست", "ليس", "بل ", "مع أن", "ومع ذلك"))
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
