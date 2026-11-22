"""الستايل البصري: لا قالب ثابت. كل فيديو يحصل على ستايل خاص (من المدير الفني DeepSeek أو عشوائي مبذور)."""
import colorsys
import copy
import json
import random

FONTS = {  # الاسم -> (الملف، هل متغيّر الوزن، الأوزان المتاحة)
    "kufi": ("NotoKufi.ttf", True, (500, 900)),
    "cairo": ("Cairo.ttf", True, (500, 900)),
    "changa": ("Changa.ttf", True, (500, 800)),
    "messiri": ("ElMessiri.ttf", True, (500, 700)),
    "reem": ("ReemKufi.ttf", True, (500, 700)),
    "markazi": ("Markazi.ttf", True, (500, 700)),
    "amiri": ("Amiri-Bold.ttf", False, (700, 700)),
    "lalezar": ("Lalezar.ttf", False, (400, 400)),
    "tajawal": ("Tajawal-ExtraBold.ttf", False, (800, 800)),
}
ENUMS = {
    "font": list(FONTS),
    # plain backgrounds first (the default look); the rest are legacy names kept valid for old specs / LLM output
    "bg.type": ["paper", "kraft", "solid", "ink", "grid", "dots", "stripes", "cinematic", "map", "gradient", "radial", "waves", "aurora", "rays"],
    "headline.pos": ["top", "upper", "center", "lower"],
    "headline.box": ["none", "pill", "bar", "underline", "tag"],
    "headline.enter": ["rise", "drop", "pop", "fade", "wipe", "slide"],
    "caption.mode": ["pill", "bar", "stroke", "underline", "box_word", "plain"],
    "caption.hl": ["color", "scale", "box"],
    "map.fill": ["flat", "gradient", "hatch"],
    "map.marker": ["ring", "pin", "square", "diamond"],
    "stat.layout": ["ring", "bar", "plain", "stack"],
    "text.layout": ["center", "stack", "diag", "left"],
    "deco.frame": ["none", "corners", "border", "ticks"],
    "deco.progress": ["none", "top", "bottom"],  # "side" removed: creates edge-bleed artifact in 9:16
    "edit.photo": ["bleed", "polaroid", "arch", "tilt", "circle"],
    "edit.cutout": ["ring", "glow", "blob", "plain"],
    "edit.mixpat": ["alt", "tail", "head", "none"],
    "edit.shapes": ["stars", "diamonds", "dots", "crosses", "none"],
    "edit.ken": ["in", "out", "pan"],
}

# لوحات مرجعية للألوان تُمزج وتُدوَّر درجاتها عشوائياً؛ ليست قوالب مشاهد.
MOODS = {
    "ذهبي سينمائي": dict(c1=(14, 16, 22), c2=(6, 8, 12), accent=(255, 215, 0), accent2=(56, 189, 248), text=(255, 255, 255), dark=True),
    "ليلي": dict(c1=(8, 26, 52), c2=(4, 12, 28), accent=(255, 214, 120), accent2=(96, 162, 232), text=(255, 255, 255), dark=True),
    "غروب": dict(c1=(58, 18, 52), c2=(20, 8, 30), accent=(255, 150, 90), accent2=(255, 98, 130), text=(255, 246, 236), dark=True),
    "ورق": dict(c1=(244, 236, 220), c2=(226, 214, 190), accent=(190, 60, 40), accent2=(40, 90, 120), text=(34, 28, 22), dark=False),
    "نيون": dict(c1=(14, 8, 36), c2=(4, 2, 18), accent=(60, 255, 200), accent2=(255, 70, 190), text=(240, 250, 255), dark=True),
    "غابة": dict(c1=(10, 44, 38), c2=(4, 22, 20), accent=(190, 240, 120), accent2=(255, 200, 90), text=(240, 252, 244), dark=True),
    "أحمر وأسود": dict(c1=(26, 10, 12), c2=(8, 4, 6), accent=(255, 70, 70), accent2=(255, 230, 200), text=(255, 255, 255), dark=True),
    "باستيل": dict(c1=(252, 228, 236), c2=(214, 228, 252), accent=(236, 84, 128), accent2=(84, 120, 220), text=(40, 34, 60), dark=False),
    "رمل": dict(c1=(238, 210, 160), c2=(214, 170, 110), accent=(120, 40, 24), accent2=(24, 80, 90), text=(38, 24, 14), dark=False),
    "فولاذ": dict(c1=(44, 52, 66), c2=(20, 24, 32), accent=(255, 190, 60), accent2=(120, 200, 255), text=(236, 240, 246), dark=True),
    "محيط": dict(c1=(6, 70, 110), c2=(2, 24, 52), accent=(255, 236, 150), accent2=(120, 255, 220), text=(246, 252, 255), dark=True),
    # plain, saturated-but-flat grounds (no glow): these carry the default look
    "ورق عاجي": dict(c1=(246, 240, 226), c2=(232, 224, 204), accent=(178, 52, 38), accent2=(22, 104, 120), text=(30, 26, 22), dark=False),
    "كرافت": dict(c1=(205, 170, 125), c2=(186, 150, 106), accent=(96, 36, 24), accent2=(20, 70, 84), text=(36, 24, 14), dark=False),
    "حبر": dict(c1=(20, 22, 28), c2=(12, 14, 18), accent=(255, 196, 0), accent2=(80, 190, 240), text=(250, 248, 240), dark=True),
    "نيلي": dict(c1=(22, 40, 84), c2=(14, 26, 60), accent=(255, 205, 90), accent2=(120, 220, 255), text=(250, 250, 255), dark=True),
    "زيتوني": dict(c1=(52, 68, 40), c2=(36, 50, 28), accent=(240, 214, 110), accent2=(210, 236, 160), text=(248, 250, 240), dark=True),
    "طوبي": dict(c1=(168, 70, 48), c2=(140, 52, 34), accent=(255, 226, 170), accent2=(255, 255, 255), text=(255, 248, 240), dark=True),
    "خردل": dict(c1=(232, 182, 56), c2=(210, 160, 36), accent=(40, 32, 24), accent2=(120, 40, 30), text=(34, 26, 16), dark=False),
    "طباشير": dict(c1=(36, 44, 46), c2=(26, 32, 34), accent=(240, 236, 200), accent2=(130, 214, 190), text=(244, 244, 238), dark=True),
}

# which grounds suit which background type (the palette's c1 IS the background colour)
BG_MOODS = {
    "paper": ["ورق عاجي", "ورق", "باستيل"],
    "kraft": ["كرافت", "رمل"],
    "solid": ["نيلي", "زيتوني", "طوبي", "خردل", "غابة", "فولاذ", "ورق عاجي"],
    "ink": ["حبر", "ذهبي سينمائي", "أحمر وأسود", "طباشير"],
    "grid": ["ورق عاجي", "نيلي", "طباشير", "ورق"],
    "dots": ["ورق", "خردل", "حبر", "باستيل"],
    "stripes": ["باستيل", "كرافت", "نيلي", "ورق عاجي"],
    "cinematic": ["ذهبي سينمائي", "ليلي", "نيون"],
}
# default mix of background types for new videos (weights); plain ones dominate, cinematic is rare
BG_WEIGHTS = [("paper", 24), ("kraft", 8), ("solid", 24), ("ink", 14), ("grid", 10), ("dots", 8), ("stripes", 6), ("cinematic", 6)]


def _rot(rgb, dh, ds=1.0, dv=1.0):
    h, s, v = colorsys.rgb_to_hsv(*[c / 255 for c in rgb])
    h = (h + dh) % 1.0
    s = min(max(s * ds, 0), 1)
    v = min(max(v * dv, 0), 1)
    return tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(h, s, v))


def _mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _lum(c):
    return 0.2126 * (c[0] / 255) ** 2.2 + 0.7152 * (c[1] / 255) ** 2.2 + 0.0722 * (c[2] / 255) ** 2.2


def _contrast(a, b):
    return (max(_lum(a), _lum(b)) + 0.05) / (min(_lum(a), _lum(b)) + 0.05)


def random_style(seed=None, mood=None):
    seed = random.SystemRandom().randrange(1, 10**9) if seed is None else int(seed)
    r = random.Random(seed)
    bg_type = r.choices([k for k, _ in BG_WEIGHTS], weights=[w for _, w in BG_WEIGHTS])[0]
    name = mood if mood in MOODS else r.choice(BG_MOODS[bg_type])
    m = MOODS[name]
    dh = r.uniform(-0.12, 0.12)
    c1, c2 = _rot(m["c1"], dh), _rot(m["c2"], dh)
    # hue rotation changes luminance: keep text readable on the ground (WCAG 4.5:1), darkening/lightening c1/c2 if needed
    for _ in range(14):
        if _contrast(m["text"], c1) >= 4.5:
            break
        k = 0.9 if m["dark"] else 1.06
        c1, c2 = _rot(c1, 0, 1.0, k), _rot(c2, 0, 1.0, k)
    acc, acc2 = _rot(m["accent"], r.uniform(-0.08, 0.08)), _rot(m["accent2"], r.uniform(-0.1, 0.1))
    text = m["text"]
    dark = m["dark"]
    ctx = _mix(c1, text, 0.10 if dark else 0.14)
    edge = _mix(c1, text, 0.34 if dark else 0.38)
    hl = [acc, acc2, _rot(acc, 0.33), _rot(acc2, 0.5), _rot(acc, 0.66)]
    font = r.choice(list(FONTS))
    lo, hi = FONTS[font][2]
    font2 = r.choice([f for f in FONTS if f != font])
    s = {
        "name": f"{name}-{seed % 1000}",
        "seed": seed,
        "dark": dark,
        "font": font,
        "weight": r.choice([w for w in (lo, (lo + hi) // 2, hi)]),
        "palette": {"c1": c1, "c2": c2, "accent": acc, "accent2": acc2, "text": text, "ctx": ctx, "ctx_edge": edge, "hl": hl},
        "bg": {"type": bg_type, "angle": r.randrange(0, 180), "motion": r.random() < 0.8,
               "intensity": round(r.uniform(0.5, 1.0), 2)},
        "headline": {"pos": r.choice([p for p in ENUMS["headline.pos"] if p != "lower"]), "size": r.choice([72, 80, 88, 96]),
                     "box": r.choice(ENUMS["headline.box"]), "enter": r.choice(ENUMS["headline.enter"])},
        "caption": {"mode": r.choice(ENUMS["caption.mode"]), "y": r.choice([1350, 1400, 1450, 1490]),
                    "size": r.choice([56, 62, 68, 74]), "hl": r.choice(ENUMS["caption.hl"])},
        "map": {"fill": r.choice(ENUMS["map.fill"]), "edge": r.choice([2, 3, 4, 6]),
                "ctx_alpha": round(r.uniform(0.35, 1.0), 2), "marker": r.choice(ENUMS["map.marker"])},
        "stat": {"layout": r.choice(ENUMS["stat.layout"])},
        "text": {"layout": r.choice(ENUMS["text.layout"]), "size": r.choice([104, 116, 128])},
        "deco": {"frame": r.choice(ENUMS["deco.frame"]), "progress": r.choice(ENUMS["deco.progress"])},
        "pace": round(r.uniform(0.75, 1.3), 2),
        "font2": font2, "weight2": FONTS[font2][2][0],
        "edit": {"photo": r.choice(["bleed", "polaroid", "tilt"]), "cutout": r.choice(ENUMS["edit.cutout"]),
                 "mixpat": r.choice(["alt", "alt", "tail", "head", "none"]), "shapes": "none",
                 "ken": r.choice(ENUMS["edit.ken"]), "glow": r.random() < 0.7, "blur": r.random() < 0.6,
                 "duo": r.random() < 0.3},
    }
    return s


def _rgb(v, d):
    try:
        a = [int(max(0, min(255, round(float(x))))) for x in v]
        return tuple(a[:3]) if len(a) >= 3 else d
    except Exception:
        return d


def _enum(v, key, d):
    return v if v in ENUMS[key] else d


def _num(v, lo, hi, d):
    try:
        return max(lo, min(hi, float(v)))
    except Exception:
        return d


def normalize(style, seed=None):
    """يدمج ستايلاً جزئياً (من LLM مثلاً) فوق ستايل عشوائي مبذور، ويقصّ القيم لنطاقات آمنة."""
    st = style if isinstance(style, dict) else {}
    base = random_style(st.get("seed", seed))
    out = copy.deepcopy(base)
    out["name"] = str(st.get("name") or base["name"])[:40]
    out["font"] = _enum(st.get("font"), "font", base["font"])
    lo, hi = FONTS[out["font"]][2]
    out["weight"] = int(_num(st.get("weight"), lo, hi, base["weight"]))
    pal = st.get("palette") if isinstance(st.get("palette"), dict) else {}
    bp = base["palette"]
    out["palette"] = {k: _rgb(pal.get(k), bp[k]) for k in ("c1", "c2", "accent", "accent2", "text", "ctx", "ctx_edge")}
    hls = pal.get("hl") if isinstance(pal.get("hl"), list) and pal.get("hl") else bp["hl"]
    out["palette"]["hl"] = [_rgb(c, bp["hl"][i % 5]) for i, c in enumerate(hls[:6])]
    # الوضوح: نص قريب من الخلفية => نعيد النص لتباين مقبول
    lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    if abs(lum(out["palette"]["text"]) - lum(out["palette"]["c1"])) < 90:
        out["palette"]["text"] = (255, 255, 255) if lum(out["palette"]["c1"]) < 128 else (24, 20, 16)
    out["dark"] = lum(out["palette"]["c1"]) < 128
    for sec, keys in (("bg", {"type": "bg.type"}), ("headline", {"pos": "headline.pos", "box": "headline.box", "enter": "headline.enter"}),
                      ("caption", {"mode": "caption.mode", "hl": "caption.hl"}), ("map", {"fill": "map.fill", "marker": "map.marker"}),
                      ("stat", {"layout": "stat.layout"}), ("text", {"layout": "text.layout"}),
                      ("deco", {"frame": "deco.frame", "progress": "deco.progress"})):
        src = st.get(sec) if isinstance(st.get(sec), dict) else {}
        for k, ek in keys.items():
            out[sec][k] = _enum(src.get(k), ek, base[sec][k])
    sb, sh, sc, sm, stx = (st.get(k) if isinstance(st.get(k), dict) else {} for k in ("bg", "headline", "caption", "map", "text"))
    out["bg"]["angle"] = int(_num(sb.get("angle"), 0, 180, base["bg"]["angle"]))
    out["bg"]["intensity"] = _num(sb.get("intensity"), 0.2, 1.0, base["bg"]["intensity"])
    out["bg"]["motion"] = bool(sb.get("motion", base["bg"]["motion"]))
    out["headline"]["size"] = int(_num(sh.get("size"), 60, 104, base["headline"]["size"]))
    out["caption"]["y"] = int(_num(sc.get("y"), 1340, 1500, base["caption"]["y"]))
    out["caption"]["size"] = int(_num(sc.get("size"), 50, 78, base["caption"]["size"]))
    out["map"]["edge"] = int(_num(sm.get("edge"), 1, 8, base["map"]["edge"]))
    out["map"]["ctx_alpha"] = _num(sm.get("ctx_alpha"), 0.2, 1.0, base["map"]["ctx_alpha"])
    out["text"]["size"] = int(_num(stx.get("size"), 80, 140, base["text"]["size"]))
    out["pace"] = _num(st.get("pace"), 0.6, 1.5, base["pace"])
    out["seed"] = int(st.get("seed") or base["seed"])
    f2 = _enum(st.get("font2"), "font", base["font2"])
    out["font2"] = f2 if f2 != out["font"] else base["font2"] if base["font2"] != out["font"] else "amiri"
    out["weight2"] = int(_num(st.get("weight2"), FONTS[out["font2"]][2][0], FONTS[out["font2"]][2][1], FONTS[out["font2"]][2][0]))
    se = st.get("edit") if isinstance(st.get("edit"), dict) else {}
    for k, ek in (("photo", "edit.photo"), ("cutout", "edit.cutout"), ("mixpat", "edit.mixpat"), ("shapes", "edit.shapes"), ("ken", "edit.ken")):
        out["edit"][k] = _enum(se.get(k), ek, base["edit"][k])
    for k in ("glow", "blur", "duo"):
        out["edit"][k] = bool(se.get(k, base["edit"][k]))
    return out


ART_SYSTEM = """أنت مدير فني لفيديوهات Shorts عربية. الطابع البصري المفضل: خلفية سادة نظيفة غير باهتة وبلا توهج أو جزيئات: ورق عاجي (paper)، كرافت (kraft)، لون واحد مشبع (solid)، حبر داكن (ink)، أو شبكة/نقاط/خطوط خفيفة جداً فوق لون سادة، مع نصوص عريضة عالية التباين. نوّع الخلفية من فيديو لآخر (لا تكرر نفس الخلفية)؛ وc1 هو لون الخلفية نفسه. مهمتك تصميم ستايل بصري فريد لهذا الفيديو بالذات يناسب موضوعه ومزاجه، ولا يشبه الفيديوهات السابقة. لا تستخدم ستايلاً محايداً مكرراً؛ اتخذ قراراً جريئاً ومتماسكاً (لوحة ألوان واحدة منسجمة، ونص مقروء بتباين عالٍ فوق الخلفية).

مبادئ الحركة: الخروج أسرع من الدخول. pace يتحكم في سرعة النوابض (0.75=هادئ، 1.3=حيوي). edit.ken يحدد حركة الكاميرا الافتراضية على الصور (in=push-in, out=zoom-out, pan=انزلاق). edit.shapes وedit.glow يضيفان بُعداً بصرياً.

أعد JSON فقط بهذا الشكل (كل الألوان [r,g,b] من 0 إلى 255):
{
 "name": "اسم قصير للستايل",
 "font": "kufi|cairo|changa|messiri|reem|markazi|amiri|lalezar|tajawal",
 "weight": 500-900,
 "palette": {"c1":[..],"c2":[..],"accent":[..],"accent2":[..],"text":[..],"ctx":[..],"ctx_edge":[..],"hl":[[..],[..],[..]]},
 "bg": {"type":"paper|kraft|solid|ink|grid|dots|stripes|cinematic","angle":0-180,"motion":true,"intensity":0.2-1},
 "headline": {"pos":"top|upper|center|lower","size":60-104,"box":"none|pill|bar|underline|tag","enter":"rise|drop|pop|fade|wipe|slide"},
 "caption": {"mode":"pill|bar|stroke|underline|box_word|plain","y":1340-1500,"size":50-78,"hl":"color|scale|box"},
 "map": {"fill":"flat|gradient|hatch","edge":1-8,"ctx_alpha":0.2-1,"marker":"ring|pin|square|diamond"},
 "stat": {"layout":"ring|bar|plain|stack"},
 "text": {"layout":"center|stack|diag|left","size":80-140},
 "deco": {"frame":"none|corners|border|ticks","progress":"none|top|bottom|side"},
 "pace": 0.6-1.5,
 "font2": "خط ثانٍ مختلف عن الأول يُمزج معه داخل الجملة الواحدة (خفيف/كتابي)، من نفس قائمة الخطوط", "weight2": 400-700,
 "edit": {"photo":"bleed|polaroid|arch|tilt|circle","cutout":"ring|glow|blob|plain","mixpat":"alt|tail|head|none","shapes":"stars|diamonds|dots|crosses|none","ken":"in|out|pan","glow":true,"blur":true,"duo":false}
}
edit هو «أسلوب المونتاج» لهذا الفيديو: photo شكل الصور المستطيلة، cutout إطار الصور المقصوصة، mixpat كيف تتبدل الخطوط بين كلمات الجملة، shapes الأشكال الزخرفية الصغيرة المتحركة، ken حركة الكاميرا على الصور، glow توهج الأرقام، blur ظهور الكلمات بتمويه، duo صبغة لونين على الصور. اختر تركيباً متماسكاً يناسب المزاج ويختلف عن الفيديوهات السابقة.
c1 وc2 لون الخلفية (تدرّج). ctx لون الدول المحيطة وctx_edge حدودها (قريبان من الخلفية). hl ألوان الدول المُبرزة وتكون لافتة. text لون النص ويجب أن يتباين بقوة مع c1."""


def art_prompt(script, avoid=()):
    s = {"title": script.get("title"), "hook": script.get("hook", {}).get("narration"),
         "scene_types": [b.get("visual", {}).get("type") for b in script.get("body", [])]}
    t = "السكربت:\n" + json.dumps(s, ensure_ascii=False)
    if avoid:
        t += "\n\nستايلات استُخدمت مؤخراً، ابتعد عنها: " + "، ".join(map(str, avoid))
    return t
