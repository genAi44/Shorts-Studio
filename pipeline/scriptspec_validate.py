"""Split from `pipeline/scriptspec.py` (re-exported there): `validate`."""
import re
from .scriptspec import DANGLING_ENDS, DISALLOWED_CTA, GREET, OPEN_LOOP_TRIGGERS, PARTS, WPS, normalize, nwords, scenes_of, total_words  # noqa: E402


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
            # جملة ناقصة (تنتهي بحرف جر/اسم موصول بلا تكملة) = معلومة مقطوعة
            last = text.strip().rstrip(".،,:…؟?!").split()[-1:] or [""]
            if last[0] in DANGLING_ENDS:
                add("error", pid, f"الـ CTA ينتهي بجملة ناقصة ('{last[0]}'). أكمل الجملة.")
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
