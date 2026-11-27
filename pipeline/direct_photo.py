"""Split from `pipeline/direct.py` (re-exported there); see that module."""
from typing import Any, Dict, Optional
from .geo import WORLD_CITIES, ISO3_TO_COUNTRY_EN, detect_city_in_text
import re
from .config import record_fallback
from .direct import _words  # noqa: E402


def photo_to_text(b, sentence="", beat_id="photo"):
    """صورة تعذّر إيجادها ← لوحة رسم تعبيرية غنية بدلاً من شاشة سوداء مجردة."""
    text = sentence or b.get("text") or b.get("title") or "…"
    uid = str(b.get("id") or b.get("title") or beat_id)
    ent_iso3 = str(b.get("entity_iso3") or "").upper()
    if ent_iso3:
        try:
            from .geo import get_geo
            if get_geo().has(ent_iso3):
                return {
                    "kind": "map",
                    "countries": [ent_iso3],
                    "highlight": [ent_iso3],
                    "title": b.get("entity_name_ar") or b.get("title") or "",
                    "text": _words(text, 5),
                    "camera": b.get("camera") or "push-in",
                }
        except Exception:
            pass
    try:
        from .generative_visuals import compose_generative_canvas
        canvas = compose_generative_canvas(
            text,
            context=b.get("title") or "",
            is_fallback=True,
            fallback_reason="photo_to_text",
            beat_id=uid,
        )
        if b.get("camera"):
            canvas["camera"] = b["camera"]
        return canvas
    except Exception as exc:
        from .config import FallbackError
        if isinstance(exc, FallbackError):
            raise
        fb = {
            "kind": "bigtext",
            "title": "",
            "text": " ".join(text.split()[:5]).strip(".!؟?،:؛ "),
            "sub": " ".join(text.split()[5:10]).strip(".!؟?،:؛ ") if len(text.split()) > 5 else "",
            "layout": "center",
            "camera": b.get("camera", "push-in"),
            "_fallback": True,
        }
        record_fallback("photo_to_text_bigtext", beat_id=uid, beat=fb)
        return fb


# ------------------------------------------------------------------ تحسين غنى المشاهد البصرية
# أنماط المشاهد السينمائية لتنويع الحركة ولون المزاج
CINEMATIC_STYLES = [
    {"name": "cinematic_gold", "bg_grad": "radial-gradient(ellipse at 50% 30%, rgba(212,175,55,0.15) 0%, transparent 60%)", "accent": "#D4AF37", "lighting": "warm"},
    {"name": "cinematic_cool", "bg_grad": "radial-gradient(ellipse at 50% 30%, rgba(56,189,248,0.12) 0%, transparent 60%)", "accent": "#38bdf8", "lighting": "cool"},
    {"name": "cinematic_warm", "bg_grad": "radial-gradient(ellipse at 50% 30%, rgba(251,146,60,0.12) 0%, transparent 60%)", "accent": "#fb923c", "lighting": "warm"},
    {"name": "cinematic_dramatic", "bg_grad": "radial-gradient(ellipse at 50% 40%, rgba(244,63,94,0.10) 0%, transparent 60%)", "accent": "#f43f5e", "lighting": "dramatic"},
    {"name": "cinematic_neon", "bg_grad": "radial-gradient(ellipse at 50% 30%, rgba(168,85,247,0.12) 0%, transparent 60%)", "accent": "#a855f7", "lighting": "neon"},
]


CITY_EN = {
    "منف": "Memphis Egypt ancient capital",
    "طيبة": "Thebes Luxor Egypt temple",
    "طيبة (الأقصر)": "Thebes Luxor Egypt temple",
    "الإسكندرية": "Alexandria Egypt coast ancient",
    "الفسطاط": "Fustat ancient Cairo Egypt",
    "القاهرة": "Cairo Egypt historical citadel",
    "سوكري": "Sucre Bolivia colonial",
    "لاباز": "La Paz Bolivia city mountain",
    "القدس": "Jerusalem old city",
    "بغداد": "Baghdad historical architecture",
    "دمشق": "Damascus old city architecture",
    "مكة": "Mecca city holy",
    "المدينة": "Medina city historical",
    "الرياض": "Riyadh city skyline",
    "العاصمة الإدارية": "New Administrative Capital Egypt",
    "العاصمة الإدارية الجديدة": "New Administrative Capital Egypt"
}


# دمجه مع قاعدة البيانات العالمية
for _k, _v in WORLD_CITIES.items():
    if _k not in CITY_EN:
        CITY_EN[_k] = f"{_v['en']} {_v['country']} landmark historical architecture"


_PHOTO_PATTERNS = [
    (r"حضار|إمبراطور|شعوب|قبائل|قبيلة|سلالة", "ancient lost civilization ruins monument", "ancient stone ruins architecture", "modern tourist watermark"),
    (r"معبد|معابد|أهرام|أثر|آثار|صرح|مقابر", "ancient temple pyramid ruins archaeological site", "ancient temple structure", "watermark text collage"),
    (r"قصور|قصر|قلعة|حصن|أسوار", "ancient historical fortress castle architecture", "historical architecture building", "modern cars watermark"),
    (r"كنز|كنوز|ذهب|فضة|مجوهرات", "ancient golden treasures artifacts discovery", "golden artifacts discovery", "watermark modern text"),
    (r"فيضان|فيضانات|غرق|طوفان|أمطار|مياه|سدود|أنهار", "massive river flood deluge dramatic water disaster", "river flood water deluge", "watermark text"),
    (r"بركان|حمم|صهارة|فوهة", "active volcano lava eruption smoke landscape", "volcano eruption lava", "watermark text"),
    (r"محاصيل|زراعة|مخازن|قمح|طعام|غذاء|مجاعة", "ancient wheat agriculture grain harvest fields", "wheat grain fields harvest", "watermark text"),
    (r"دمار|انهيار|سقوط|موت|فناء|زوال", "ancient ruined city abandoned historical stone", "ruined stone architecture", "watermark modern text"),
    (r"حرب|معركة|جيش|عسكر|فرسان", "ancient historical army warriors fortress battlefield", "historical battle fortress", "watermark text"),
    (r"سفن|بحر|محيط|أسطول|ملاحة", "ancient wooden sailing ship ocean expedition", "wooden sailing ship", "watermark text"),
    (r"فضاء|نجوم|كواكب|مجرة", "deep space stars galaxy universe nebula astronomy", "deep space galaxy", "watermark text"),
    (r"صحراء|رمال|واحة", "vast desert sand dunes dramatic landscape", "desert sand dunes", "watermark text"),
    (r"غابة|طبيعة|أشجار|أدغال", "dense ancient rainforest jungle nature landscape", "rainforest jungle landscape", "watermark text"),
]


def _number_in_text(num, text: str) -> bool:
    """True if the digits of `num` occur in `text` (Arabic-Indic digits and separators normalized)."""
    tr = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,")
    norm = lambda x: re.sub(r"[,\s]", "", str(x).translate(tr))
    n = norm(num)
    return bool(n) and n in norm(text)


def detect_photo_beat(sentence: str, pt_name: str = "", cou_iso: str = "") -> Optional[Dict[str, Any]]:
    clean_pt = re.sub(r"\(.*?\)", "", pt_name).strip() if pt_name else ""
    try:
        from .geo_overlay import extract_timed_geo_mentions
        gm = extract_timed_geo_mentions(sentence, "", [], 150)
        if gm:
            m0 = next((x for x in gm if x.get("kind") in ("landmark", "capital", "city", "country")), gm[0])
            en_n = m0.get("name_en") or m0.get("name_ar") or ""
            if en_n and en_n.lower() == "marrakesh":
                en_n = "Marrakech"
            if en_n.lower() == "marrakesh":
                en_n = "Marrakech"
            m_iso3 = str(m0.get("iso3") or cou_iso or "").upper()
            c_en = ISO3_TO_COUNTRY_EN.get(m_iso3, "") or (ISO3_TO_COUNTRY_EN.get(cou_iso.upper(), "") if cou_iso else "")
            if en_n:
                q_base = f"{en_n} {c_en}".strip() if (c_en and c_en.lower() not in en_n.lower() and m0.get("kind") != "country") else en_n
                return {
                    "kind": "photo",
                    "query": f"{q_base} landmark architecture",
                    "text": _words(sentence, 5),
                    "camera": "parallax",
                    "must_show": q_base,
                    "avoid": "watermark text collage modern cars map flag",
                    "alt_queries": [f"{q_base} city", f"{en_n} landscape"],
                    "entity_iso3": m_iso3,
                    "entity_country_en": c_en,
                    "entity_name_ar": m0.get("name_ar") or "",
                }
    except Exception:
        pass
    detected_city, city_data = detect_city_in_text(sentence)
    if not clean_pt and detected_city:
        clean_pt = detected_city
        cou_iso = cou_iso or city_data.get("iso", "")

    # تحويل رمز الدولة إلى اسم إنجليزي حقيقي لتفادي مطابقات خاطئة مثل MAR -> Casa del Mar
    country_en = ISO3_TO_COUNTRY_EN.get(cou_iso.upper(), "") if cou_iso else ""

    if clean_pt or country_en:
        city_info = city_data or WORLD_CITIES.get(clean_pt)
        city_en = city_info["en"] if city_info else clean_pt
        if city_en and city_en.lower() == "marrakesh":
            city_en = "Marrakech"
        c_name = city_info["country"] if city_info else country_en
        
        if city_en and c_name:
            q = f"{city_en} {c_name} landmark historical architecture"
            must = f"{city_en} {c_name} historic architecture"
            alts = [f"{city_en} landmark", f"{c_name} historical place"]
        elif c_name:
            q = f"{c_name} landmark historical architecture"
            must = f"{c_name} historical architecture"
            alts = [f"{c_name} historical place", f"{c_name} architecture"]
        else:
            q = CITY_EN.get(clean_pt, f"{clean_pt} landmark historical architecture")
            must = clean_pt or "historical building"
            alts = [f"{clean_pt} landmark", f"{clean_pt} historical place"]

        return {
            "kind": "photo",
            "query": q,
            "text": _words(sentence, 5),
            "camera": "parallax",
            "must_show": must,
            "avoid": "watermark text collage modern cars",
            "alt_queries": alts,
            "entity_iso3": (cou_iso or "").upper(),
            "entity_country_en": country_en or c_name or "",
            "entity_name_ar": clean_pt or "",
        }
    try:
        from .geo_overlay import extract_timed_geo_mentions
        gm = extract_timed_geo_mentions(sentence, "", [], 150)
        if gm:
            m0 = next((x for x in gm if x.get("kind") in ("landmark", "capital", "city")), gm[0])
            en_n = m0.get("name_en") or m0.get("name_ar") or ""
            if en_n:
                return {
                    "kind": "photo",
                    "query": f"{en_n} historical landmark architecture",
                    "text": _words(sentence, 5),
                    "camera": "parallax",
                    "must_show": f"{en_n} architecture landmark",
                    "avoid": "watermark text collage modern cars",
                    "alt_queries": [f"{en_n} landmark", f"{en_n} heritage"],
                }
    except Exception:
        pass
    if not re.search(r"إحصائيات|ضحايا|مليون|مليار|نسبة|%|عدد السكان", sentence):
        for pat, query, must_show, avoid in _PHOTO_PATTERNS:
            if re.search(pat, sentence, re.I):
                return {
                    "kind": "photo",
                    "query": query,
                    "text": _words(sentence, 5),
                    "camera": "parallax",
                    "must_show": must_show,
                    "avoid": avoid,
                    "alt_queries": [" ".join(query.split()[:3]), "historical monument architecture"]
                }
    return None


def fallback_beat(scene, i, sentence):
    v = scene.get("visual") or {}

    # مشهد الحلقة المفتوحة (open_loop) مشهد توتر وتشويق وتساؤل ذكي متكامل بصرياً
    if scene.get("role") == "open_loop":
        from .generative_visuals import compose_generative_canvas
        return compose_generative_canvas(sentence, context=scene.get("on_screen") or "لغز وتساؤل")
    pts = v.get("points") or []
    cs = v.get("countries") or []
    cou_iso = cs[0] if cs else ""
    pt_name = pts[0].get("name", "") if pts else ""

    # فحص ما إذا كانت الجملة أو المشهد يذكر مدينة أو عاصمة معروفة
    detected_city, city_data = detect_city_in_text(sentence)
    if not detected_city:
        detected_city, city_data = detect_city_in_text(scene.get("on_screen", ""))

    # ملاحظة: الخرائط الجغرافية تُعرض الآن كطبقة MapOverlay ذكية متزامنة مع الصوت (pipeline/geo_overlay.py)،
    # لذلك يركز المشهد الأساسي على التكوين البصري والمعماري والتعبيري للجملة دون تكرار خريطة خلفية.

    # مشهد الـ Hook (الخطاف في أول ثوانٍ): يجب أن يكون مشهداً بطلاً جذاباً بصرياً (Hero Visual)
    if scene.get("role") == "hook" or i == 0:
        hero_photo = detect_photo_beat(sentence, pt_name, cou_iso)
        if hero_photo:
            hero_photo["camera"] = "parallax"
            return hero_photo
        from .generative_visuals import compose_generative_canvas
        return compose_generative_canvas(sentence, context=scene.get("on_screen") or v.get("text"))

    # إذا ورد ارتفاع/جبل → مخطط ارتفاع مرئي
    _HEIGHT_KW = re.compile(r"ارتفاع|قمة|جبل|سلسلة جبال|فوق سطح البحر|elevation|mountain|peak|above sea level|meters above|height", re.I)
    if _HEIGHT_KW.search(sentence):
        nums_h = re.findall(r"\d[\d,.]*", sentence)
        heights = []
        for n in nums_h:
            try:
                v = float(n.replace(",", ""))
                if 10 <= v <= 30000:
                    heights.append(n)
            except Exception:
                pass
        if heights:
            return {"kind": "elevation_profile", "title": _words(sentence, 5), "height": heights[0], "unit": "م", "sea_label": "سطح البحر", "camera": "push-in"}
    # نسب مئوية متعددة (≥2) → مخطط دائري
    pcts = re.findall(r"(\d+(?:\.\d+)?)\s*%", sentence)
    pct_labels = re.findall(r"([^\d،,]+?)\s+(\d+(?:\.\d+)?)\s*%", sentence)
    if len(pcts) >= 2:
        if pct_labels and len(pct_labels) >= 2:
            items = [{"label": _words(lbl.strip(), 4), "value": float(val)} for lbl, val in pct_labels[:5]]
        else:
            items = [{"label": f"{v}%", "value": float(v)} for v in pcts[:5]]
        return {"kind": "pie_chart", "title": _words(sentence, 5), "items": items, "camera": "push-in"}
    # سلسلة زمنية: ≥2 أزواج (سنة + قيمة) → line_chart
    year_val_pairs = re.findall(r"((?:19|20)\d{2})[^\d]{0,15}?(\d+(?:[\.,]\d+)?)", sentence)
    if len(year_val_pairs) >= 2:
        points = [{"label": yr, "value": float(val.replace(",", ""))} for yr, val in year_val_pairs[:6]]
        return {"kind": "line_chart", "title": _words(sentence, 5), "points": points, "camera": "push-in"}
    # إذا ورد تاريخ/سنة
    years = re.findall(r"\b(1\d{3}|20\d{2}|[1-9]\d{2})\b", sentence)
    if years:
        return {"kind": "timeline", "title": "", "items": [{"year": years[0], "label": _words(sentence, 5)}]}
    # إذا ورد رقم صريح
    nums = re.findall(r"\d+[\d,.]*", sentence)
    if nums and len(nums[0]) >= 2:
        return {"kind": "stat", "title": "", "number": nums[0], "label": _words(sentence, 5), "layout": "ring"}

    # إذا ورد مقارنة أو صراع أو تفوق طرفين
    _VS_KW = re.compile(r"مقابل|مقارنة|ضد|تنافس|صراع|حجم.*مقابل|تفوق|versus|vs|battle", re.I)
    # a VS chart needs two numbers SPOKEN in the sentence: it used to invent 100 vs 60 and "الطرف الأول/الثاني"
    # for any sentence with the word "صراع" (seen: "صراعات مالية" -> a fake 100/60 bar chart)
    if _VS_KW.search(sentence) and len(re.findall(r"\d[\d,.]*", sentence)) >= 2:
        tokens = re.split(r"مقابل|ضد|مقارنة", sentence)
        side_a = " ".join(tokens[0].strip().split()[-4:]) if len(tokens) > 1 else "الطرف الأول"
        side_b = _words(tokens[1].strip(), 4) if len(tokens) > 1 else "الطرف الثاني"
        nums = re.findall(r"\d[\d,.]*", sentence)
        v_a = float(nums[0].replace(",", "")) if nums else 100
        v_b = float(nums[1].replace(",", "")) if len(nums) > 1 else 60
        return {
            "kind": "versus_battle",
            "title": _words(sentence, 5),
            "left": {"title": side_a or "الطرف الأول", "subtitle": "", "badge": "طرف ١", "value": v_a},
            "right": {"title": side_b or "الطرف الثاني", "subtitle": "", "badge": "طرف ٢", "value": v_b},
            "camera": "push-in",
        }

    # إذا ورد ترتيب أو قائمة أو مراكز أولى (أغنى، أكبر، أفضل، المراكز) مع أرقام أو أسماء أعداد عربية
    _RANK_KW = re.compile(r"أغنى|أكبر|أفضل|أعلى|أقوى|المراكز|ترتيب|قائمة|ranking|top", re.I)
    _AR_NUM_WORDS = re.compile(r"ثلاث|أربع|خمس|ست|سبع|ثمان|تسع|عشر")
    if _RANK_KW.search(sentence) and not (cou_iso or pt_name):
        nums = re.findall(r"\d[\d,.]*", sentence)
        if len(nums) >= 3:
            return {
                "kind": "bars",
                "title": _words(sentence, 5),
                "items": [
                    {"label": _words(sentence, 2) + " ١", "value": 100, "display": nums[0]},
                    {"label": _words(sentence, 2) + " ٢", "value": 85, "display": nums[1]},
                    {"label": _words(sentence, 2) + " ٣", "value": 70, "display": nums[2]},
                ],
                "camera": "push-in",
            }
        if _AR_NUM_WORDS.search(sentence) or nums:
            return {
                "kind": "bars",
                "title": _words(sentence, 5),
                "items": [
                    {"label": "المركز ١", "value": 100, "display": "1"},
                    {"label": "المركز ٢", "value": 82, "display": "2"},
                    {"label": "المركز ٣", "value": 64, "display": "3"},
                ],
                "camera": "push-in",
            }

    # مفاهيم تخصصية تحتاج مشهد توليدي (بركان، غاز، طاقة، تضخم)
    _GEN_KW = re.compile(r"بركان|حمم|غاز طبيعي|طاقة|حصار|مضيق|ذكاء اصطناعي|بيانات|تضخم|صاروخ|باطن الأرض|ثروات", re.I)
    if _GEN_KW.search(sentence):
        from .generative_visuals import compose_generative_canvas
        return compose_generative_canvas(sentence, context=scene.get("on_screen"))

    # إذا كان المشهد خاتمة (CTA / دعوة للمتابعة والمشاركة): لا تبحث عن صورة عشوائية من الإنترنت (كتلافي خرائط منغوليا/الصين)
    if scene.get("role") in ("cta", "loop") or re.search(r"تابعنا|اشترك|اكتب.*التعليقات|شاركنا برأيك", sentence):
        from .generative_visuals import compose_generative_canvas
        return compose_generative_canvas(sentence, context=scene.get("on_screen") or "شاركنا في التعليقات")

    # إذا ارتبط المشهد بكيان ملموس، أثر، معلم، طبيعة أو بلد -> صورة حقيقية مرخصة
    photo_beat = detect_photo_beat(sentence, pt_name, cou_iso)
    if photo_beat:
        return photo_beat

    # بديل توليدي سياقي غني بدلاً من الشاشة الفارغة
    from .generative_visuals import compose_generative_canvas
    return compose_generative_canvas(sentence, context=scene.get("on_screen") or v.get("text"))
