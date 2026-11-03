"""صور حقيقية مرخّصة لكل جملة: بحث (Wikimedia Commons + Pexels) ← اختيار (Gemini يرى الصور) ← تنزيل ← قص الخلفية (rembg اختياري).
لم تُجرَّب الاستدعاءات الحية في بيئة البناء (لا شبكة)؛ كل فشل يتحوّل بهدوء إلى نص كبير بدل الصورة."""
import hashlib
import io
import json
import os
import re
import time

import requests
from PIL import Image

from . import direct, llm
from .config import ROOT, cfg

UA = {"User-Agent": cfg("WIKI_USER_AGENT", "ShortsStudioApp/1.0 (https://github.com/shorts-studio-ai/shorts-studio; contact@shorts-studio-ai.org)")}  # Wikimedia يحجب UA بعنوان example.com
CACHE = ROOT / "cache"
BAD_LIC = re.compile(r"(\bnc\b|non-?commercial|\bnd\b|no[- ]?deriv|fair use|all rights|copyrighted)", re.I)
OK_LIC = re.compile(r"(public domain|\bpd\b|pd-|cc0|cc[ -]by|attribution|pexels|unsplash)", re.I)
MAX_BYTES = 18 * 1024 * 1024


def enabled():
    return cfg("PHOTOS", "1").strip().lower() not in ("0", "false", "no", "off")


def providers():
    return ["wikimedia"] + (["pexels"] if cfg("PEXELS_API_KEY") else [])


def has_rembg():
    try:
        import rembg  # noqa: F401
        return True
    except Exception:
        return False


# ------------------------------------------------------------------ البحث
def _get(url, **kw):
    kw.setdefault("timeout", 30)
    kw.setdefault("headers", UA)
    for k in range(2):
        r = requests.get(url, **kw)
        if r.status_code == 429 and k == 0:
            time.sleep(2.5)
            continue
        r.raise_for_status()
        return r
    raise requests.RequestException("429")


def _clean(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def search_wikimedia(q, n=8):
    r = _get("https://commons.wikimedia.org/w/api.php", params={
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": n,
        "gsrsearch": f"{q} filetype:bitmap", "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1280,
        "iiextmetadatafilter": "LicenseShortName|Artist|ObjectName|Credit"})
    pages = sorted((r.json().get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    out = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        lic = _clean((meta.get("LicenseShortName") or {}).get("value"))
        if ii.get("mime") not in ("image/jpeg", "image/png", "image/webp") or not lic or BAD_LIC.search(lic) or not OK_LIC.search(lic):
            continue
        w, h = ii.get("thumbwidth") or ii.get("width") or 0, ii.get("thumbheight") or ii.get("height") or 0
        if (w < 400 and h < 400) or w / max(h, 1) > 3.0:
            continue
        title = _clean((meta.get("ObjectName") or {}).get("value")) or p.get("title", "").replace("File:", "")
        artist = _clean((meta.get("Artist") or {}).get("value"))[:80] or "Wikimedia Commons"
        out.append({"url": ii.get("thumburl") or ii["url"], "thumb": ii.get("thumburl") or ii["url"], "title": title[:90],
                    "credit": artist, "license": lic, "source": "Wikimedia Commons", "page": ii.get("descriptionurl", "")})
    return out


def search_pexels(q, n=6):
    r = _get("https://api.pexels.com/v1/search", params={"query": q, "per_page": n, "size": "large"},
             headers={**UA, "Authorization": cfg("PEXELS_API_KEY")})
    out = []
    for p in r.json().get("photos", []):
        src = p.get("src") or {}
        out.append({"url": src.get("large2x") or src.get("large"), "thumb": src.get("medium") or src.get("large"),
                    "title": (p.get("alt") or q)[:90], "credit": f"{p.get('photographer', '')} (Pexels)", "license": "Pexels License",
                    "source": "Pexels", "page": p.get("url", "")})
    return [c for c in out if c["url"]]


def search_wikipedia_lead(subject, n=1):
    """صورة مقدمة مقالة ويكيبيديا (REST API، بلا مفتاح)."""
    try:
        r = _get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(subject)}",
                 headers={**UA, "Accept": "application/json"})
        d = r.json()
        thumb = (d.get("thumbnail") or {}).get("source")
        orig = (d.get("originalimage") or {}).get("source")
        url = orig or thumb
        if not url:
            return []
        w = (d.get("originalimage") or d.get("thumbnail") or {}).get("width", 0)
        h = (d.get("originalimage") or d.get("thumbnail") or {}).get("height", 0)
        if w < 400 or h < 300:
            return []
        return [{"url": url, "thumb": thumb or url, "title": (d.get("title") or subject)[:90],
                 "credit": "Wikipedia / Wikimedia Commons", "license": "CC BY-SA",
                 "source": "Wikipedia", "page": d.get("content_urls", {}).get("desktop", {}).get("page", "")}]
    except Exception:
        return []


def find(query, log=print, wikipedia=True):
    cands = []
    for name, fn, n in (("wikimedia", search_wikimedia, 8), ("pexels", search_pexels, 5)):
        if name not in providers():
            continue
        try:
            cands += fn(query, n)[:4 if name == "wikimedia" else 3]
        except Exception as e:  # noqa
            log(f"  بحث {name} فشل: {str(e)[:80]}")
    if wikipedia and not cands:
        try:
            cands += search_wikipedia_lead(query)
            if cands:
                log(f"  Wikipedia lead: {cands[0]['title']}")
        except Exception:
            pass
    return cands


# ------------------------------------------------------------------ التنزيل
def fetch_image(url):
    CACHE.mkdir(exist_ok=True)
    f = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".bin")
    if not f.exists():
        r = _get(url, stream=True, timeout=45)
        buf = io.BytesIO()
        for chunk in r.iter_content(65536):
            buf.write(chunk)
            if buf.tell() > MAX_BYTES:
                raise ValueError("ملف كبير جداً")
        f.write_bytes(buf.getvalue())
    im = Image.open(f)
    im.load()
    return im


def _jpeg_bytes(im, side=512):
    t = im.convert("RGB")
    t.thumbnail((side, side))
    b = io.BytesIO()
    t.save(b, "JPEG", quality=80)
    return b.getvalue()


# ------------------------------------------------------------------ الاختيار بالرؤية
PICK_SYSTEM = (
    "You are a photo editor for a short educational vertical video. "
    "You receive images and must pick the best one to illustrate a sentence.\n"
    "Score criteria (0-10):\n"
    "- 0: completely wrong subject, heavy watermark, or unreadable collage\n"
    "- 1-6: wrong subject, heavy text overlay, low quality, or shows 'avoid' content\n"
    "- 7-8: correct subject, reasonably clear, minor distractions\n"
    "- 9-10: exact match to must_show, clear, well-lit, uncluttered\n"
    "Return JSON only: {\"pick\": <index 0-based, or -1 if best score < 7>, \"score\": <0-10>, \"reason\": \"<one line>\"}."
)
MIN_SCORE = 5


def pick(cands, query, sentence, log=print, must_show="", avoid=""):
    """يعيد (المرشح المختار أو None، التقييم، السبب)."""
    if not cands:
        return None, 0, "لا توجد نتائج بحث"
    if not cfg("GEMINI_API_KEY"):
        log("  مفتاح Gemini غير مضبوط — اعتماد أول نتيجة مرخصة")
        return cands[0], 8, "تم اعتماد أول نتيجة (بدون مفتاح Gemini)"
    try:
        ims, keep = [], []
        for c in cands[:6]:
            try:
                ims.append(_jpeg_bytes(fetch_image(c["thumb"])))
                keep.append(c)
            except Exception as e:
                log(f"  فشل جلب صورة مصغرة: {str(e)[:60]}")
        if not keep:
            log("  تعذر جلب الصور المصغرة — اعتماد أول مرشح متوفر")
            return cands[0], 7, "تم الاعتماد الاحتياطي بعد تعذر معاينة المصغرات"
        payload = {"query": query, "sentence": sentence}
        if must_show:
            payload["must_show"] = must_show
        if avoid:
            payload["avoid"] = avoid
        res = llm.gemini_vision_json(PICK_SYSTEM, json.dumps(payload, ensure_ascii=False), ims)
        score = int(res.get("score", 0))
        reason = str(res.get("reason", ""))[:100]
        i = int(res.get("pick", -1))
        log(f"  Gemini pick={i} score={score} — {reason}")
        if score >= MIN_SCORE and (0 <= i < len(keep)):
            return keep[i], score, reason
        elif 0 <= i < len(keep) and score >= 4:
            log(f"  قبول استثنائي للدرجة {score} لتفادي السقوط في النص")
            return keep[i], score, f"{reason} (مقبولة بدرجة {score})"
        log(f"  رُفضت (score={score}<{MIN_SCORE}) — {reason}")
        return None, score, f"رفض النموذج (score={score}): {reason}"
    except Exception as e:  # noqa
        log(f"  اختيار Gemini تعذّر ({str(e)[:60]}) — اعتماد أول نتيجة مرخصة")
        return cands[0], 6, f"اعتماد تلقائي بعد تعذر Gemini ({str(e)[:40]})"


# ------------------------------------------------------------------ قص الخلفية
_SESS = {}


def cutout(im):
    """يعيد صورة RGBA مقصوصة أو None إن لم تتوفر rembg أو كانت النتيجة رديئة."""
    try:
        from rembg import new_session, remove
        if "s" not in _SESS:
            _SESS["s"] = new_session(cfg("REMBG_MODEL", "u2net"))
        src = im.convert("RGB")
        src.thumbnail((1200, 1200))
        out = remove(src, session=_SESS["s"]).convert("RGBA")
        a = out.getchannel("A")
        w, h = a.size
        cov = sum(1 for v in a.resize((64, 64)).getdata() if v > 25) / 4096
        if not (0.06 < cov < 0.88):
            return None
        bb = a.point(lambda v: 255 if v > 12 else 0).getbbox()
        if not bb:
            return None
        m = int(0.03 * max(w, h))
        out = out.crop((max(bb[0] - m, 0), max(bb[1] - m, 0), min(bb[2] + m, w), min(bb[3] + m, h)))
        out.thumbnail((1000, 1000))
        return out
    except Exception:
        return None


# ------------------------------------------------------------------ المحلّل: مقطع photo -> مقطع بصورة جاهزة
class Media:
    def __init__(self, dest_dir, log=print):
        self.dest, self.log = dest_dir, log
        self.credits, self.used, self.n = [], set(), 0
        self.reports = []
        os.makedirs(dest_dir, exist_ok=True)

    def resolve(self, beat, sentence=""):
        q = beat.get("query", "")
        must_show = beat.get("must_show", "")
        avoid = beat.get("avoid", "")
        alt_queries = list(beat.get("alt_queries") or [])
        queries_tried = [q]
        self.log(f"صورة للجملة: «{sentence[:50]}…» | استعلام: «{q}»{f' | must_show: {must_show}' if must_show else ''}")

        def _try_query(qry, wikipedia=True):
            cs = find(qry, self.log, wikipedia=wikipedia)
            for n in (3, 2):
                if not cs and len(qry.split()) > n:
                    sub_q = " ".join(qry.split()[:n])
                    if sub_q not in queries_tried:
                        queries_tried.append(sub_q)
                    cs = find(sub_q, self.log, wikipedia=False)
            return [c for c in cs if c["url"] not in self.used]

        cands = _try_query(q)
        # جرّب الاستعلامات الاحتياطية إن لم تُعطِ الأولى نتائج
        for aq in alt_queries:
            if cands:
                break
            if aq not in queries_tried:
                queries_tried.append(aq)
            self.log(f"  بحث بديل: «{aq}»")
            cands += [c for c in find(aq, self.log) if c["url"] not in self.used]

        c, score, reason = pick(cands, q, sentence, self.log, must_show=must_show, avoid=avoid)
        # إذا رفض Gemini الكل، جرّب الاستعلامات الاحتياطية بالبحث والاختيار مجدداً
        if not c:
            for aq in alt_queries:
                if aq not in queries_tried:
                    queries_tried.append(aq)
                self.log(f"  بحث احتياطي بعد الرفض: «{aq}»")
                extra = [c2 for c2 in find(aq, self.log) if c2["url"] not in self.used]
                if extra:
                    c, score, reason = pick(extra, aq, sentence, self.log, must_show=must_show, avoid=avoid)
                if c:
                    break

        if not c:
            rep = {
                "sentence": sentence,
                "query": q,
                "queries_tried": queries_tried,
                "candidates_count": len(cands),
                "score": score,
                "status": "fallback",
                "reason": reason or "لا توجد صور مرخصة مطابقة",
                "fallback": "icon_scene"
            }
            self.reports.append(rep)
            self.log(f"  [تقرير الوسائط] تعذّرت الصورة: «{sentence[:40]}…» (استعلامات: {', '.join(queries_tried)} | نتائج: {len(cands)} | سبب: {rep['reason']}) ← icon_scene بديلاً")
            return direct.photo_to_text(beat)

        try:
            im = fetch_image(c["url"])
            im.thumbnail((1600, 1600))
            self.n += 1
            cut = None
            if beat.get("cutout"):
                cut = cutout(im)
                if cut is None:
                    self.log("  تعذّر قص الخلفية ← صورة بإطار")
            name = f"p{self.n}.png" if cut is not None else f"p{self.n}.jpg"
            path = os.path.join(self.dest, name)
            if cut is not None:
                cut.save(path, "PNG")
            else:
                im.convert("RGB").save(path, "JPEG", quality=90)
        except Exception as e:  # noqa
            rep = {
                "sentence": sentence,
                "query": q,
                "queries_tried": queries_tried,
                "candidates_count": len(cands),
                "score": score,
                "status": "error",
                "reason": f"فشل التنزيل: {str(e)[:60]}",
                "fallback": "icon_scene"
            }
            self.reports.append(rep)
            self.log(f"  [تقرير الوسائط] تنزيل الصورة فشل: {str(e)[:80]} ← icon_scene بديلاً")
            return direct.photo_to_text(beat)

        self.used.add(c["url"])
        self.credits.append({k: c[k] for k in ("title", "credit", "license", "source", "page")})
        rep = {
            "sentence": sentence,
            "query": q,
            "queries_tried": queries_tried,
            "candidates_count": len(cands),
            "score": score,
            "status": "accepted",
            "reason": reason,
            "image": f"media/{name}",
            "credit": f"{c.get('title')} ({c.get('source')})",
            "fallback": None
        }
        self.reports.append(rep)
        self.log(f"  [تقرير الوسائط] تم اعتماد صورة: «{sentence[:40]}…» (استعلام: «{q}» | نتائج: {len(cands)} | تقييم: {score}/10 | مصدر: {c.get('source')})")
        return {**beat, "img": f"media/{name}", "cut": cut is not None}

    def media_report_text(self):
        lines = ["=== تقرير الوسائط والصور لكل جملة ==="]
        for i, r in enumerate(self.reports, 1):
            s = f"{i}. الجملة: «{r['sentence']}»\n   الاستعلامات: {', '.join(r['queries_tried'])} (المرشحات: {r['candidates_count']})\n"
            if r['status'] == 'accepted':
                s += f"   الحالة: تم القبول ✓ (التقييم: {r['score']}/10) | {r['reason']}\n   الملف: {r['image']} | الحقوق: {r.get('credit', '')}"
            else:
                s += f"   الحالة: بديل نصي ({r['fallback']}) | السبب: {r['reason']}"
            lines.append(s)
        return "\n".join(lines)

    def credits_text(self):
        seen, lines = set(), []
        for c in self.credits:
            key = (c["title"], c["credit"])
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"• {c['title']} — {c['credit']} — {c['license']} — {c['page']}")
        return "\n".join(lines)
