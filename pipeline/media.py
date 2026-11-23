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
from .config import ROOT, cfg, record_fallback

UA = {"User-Agent": cfg("WIKI_USER_AGENT", "ShortsStudioApp/1.0 (https://github.com/shorts-studio-ai/shorts-studio; contact@shorts-studio-ai.org)")}  # Wikimedia يحجب UA بعنوان example.com
CACHE = ROOT / "cache"
BAD_LIC = re.compile(r"(\bnc\b|non-?commercial|\bnd\b|no[- ]?deriv|fair use|all rights|copyrighted)", re.I)
OK_LIC = re.compile(r"(public domain|\bpd\b|pd-|cc0|cc[ -]by|attribution|pexels|unsplash)", re.I)
NON_PHOTO_RE = re.compile(
    r"((?:^|[\W_])map(?:$|[\W_])|flag[_ ]of|coat[_ ]of[_ ]arms|seal[_ ]of|emblem[_ ]of|map[_ ]of|locator[_ ]map|location[_ ]map|orthographic|\.svg(?:\b|$))",
    re.I,
)
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


_WIKI_NOISE_RE = re.compile(r"\b(historical photo|archival|documentary|landmark architecture|photo|image)\b", re.I)


def search_wikimedia(q, n=8):
    clean_q = re.sub(r"\s+", " ", _WIKI_NOISE_RE.sub("", q or "")).strip()
    search_q = clean_q if len(clean_q.split()) >= 2 else q
    r = _get("https://commons.wikimedia.org/w/api.php", params={
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": n,
        "gsrsearch": f"{search_q} filetype:bitmap", "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1280,
        "iiextmetadatafilter": "LicenseShortName|Artist|ObjectName|Credit|GPSLatitude|GPSLongitude|Categories"})
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
        if NON_PHOTO_RE.search(title) or NON_PHOTO_RE.search(ii.get("url", "")):
            continue
        artist = _clean((meta.get("Artist") or {}).get("value"))[:80] or "Wikimedia Commons"
        cats = _clean((meta.get("Categories") or {}).get("value"))[:300]
        lat, lon = None, None
        try:
            raw_lat = _clean((meta.get("GPSLatitude") or {}).get("value"))
            raw_lon = _clean((meta.get("GPSLongitude") or {}).get("value"))
            if raw_lat and raw_lon:
                lat, lon = float(raw_lat), float(raw_lon)
        except (TypeError, ValueError):
            lat, lon = None, None
        item = {"url": ii.get("thumburl") or ii["url"], "thumb": ii.get("thumburl") or ii["url"], "title": title[:90],
                "credit": artist, "license": lic, "source": "Wikimedia Commons", "page": ii.get("descriptionurl", ""),
                "categories": cats}
        if lat is not None and lon is not None:
            item["lat"] = lat
            item["lon"] = lon
        out.append(item)
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
        if not url or NON_PHOTO_RE.search(url):
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
    if wikipedia:
        # محاولة البحث عن الصورة الرئيسية في ويكيبيديا للموضوع أو المدينة
        sub_terms = [query]
        words = query.split()
        if len(words) >= 2:
            sub_terms.append(" ".join(words[:2]))
        if len(words) >= 1:
            sub_terms.append(words[0])
        for st in sub_terms:
            if len(st) >= 3:
                try:
                    w_cands = search_wikipedia_lead(st)
                    if w_cands:
                        log(f"  Wikipedia lead: {w_cands[0]['title']}")
                        cands += w_cands
                        break
                except Exception:
                    pass

    for name, fn, n in (("wikimedia", search_wikimedia, 8), ("pexels", search_pexels, 5)):
        if name not in providers():
            continue
        try:
            cands += fn(query, n)[:4 if name == "wikimedia" else 3]
        except Exception as e:  # noqa
            log(f"  بحث {name} فشل: {str(e)[:80]}")
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
    "You are a documentary photo editor for a short educational vertical video. "
    "You receive images and must pick the best authentic one to illustrate a sentence.\n"
    "Strict Documentary & Historical Rules:\n"
    "- Match the exact location, landmark, person, or event in 'must_show'.\n"
    "- Respect 'is_historical' / 'historical_era': if historical, REJECT modern skyscrapers, contemporary cars, modern tourists, or AI-generated illustrations; prefer authentic archival/period photography.\n"
    "- REJECT any image containing 'avoid' elements, heavy watermarks, collages, or generic unrelated stock.\n"
    "Score criteria (0-10):\n"
    "- 0: completely wrong subject, heavy watermark, anachronistic modern photo for historical scene, or unreadable collage\n"
    "- 1-6: wrong subject, heavy text overlay, low quality, or shows 'avoid' content\n"
    "- 7-8: correct subject & era, reasonably clear, minor distractions\n"
    "- 9-10: exact match to must_show and era, clear, authentic, uncluttered\n"
    "Return JSON only: {\"pick\": <index 0-based, or -1 if best score < 7>, \"score\": <0-10>, \"reason\": \"<one line>\"}."
)
MIN_SCORE = 5


def _geo_verify_candidate(c, entity_iso3="", entity_country_en=""):
    """تحقق جغرافي فعلي: مقارنة إحداثيات Wikimedia مع حدود الدولة، ثم تصنيفاتها."""
    iso3 = (entity_iso3 or "").strip().upper()
    if iso3 and c.get("lat") is not None and c.get("lon") is not None:
        try:
            from .geo import get_geo
            g = get_geo()
            if g.has(iso3):
                min_lon, min_lat, max_lon, max_lat = g.main_bbox(iso3)
                margin = 0.75
                lat, lon = float(c["lat"]), float(c["lon"])
                if (min_lat - margin) <= lat <= (max_lat + margin) and (min_lon - margin) <= lon <= (max_lon + margin):
                    return "verified", 30
                return "mismatch", -100
        except Exception:
            pass
    c_en = (entity_country_en or "").strip().lower()
    if c_en and len(c_en) >= 3:
        cats = (c.get("categories") or "").lower()
        title = (c.get("title") or "").lower()
        if c_en in cats:
            return "cat_match", 15
        if c_en in title:
            return "title_match", 10
    return "unknown", 0


def pick(cands, query, sentence, log=print, must_show="", avoid="", entity_iso3="", entity_country_en=""):
    """يعيد (المرشح المختار أو None، التقييم، السبب)."""
    if not cands:
        return None, 0, "لا توجد نتائج بحث"

    # تصفية المرشحات وترتيبها حسب الصلة الجغرافية والموضوعية والتاريخية
    target_terms = set(re.findall(r"\w+", f"{query} {must_show}".lower()))
    is_hist_ctx = ("modern" in (avoid or "").lower()) or bool(re.search(r"\b1[0-9]{3}\b|archival|wwii|world war|historical", f"{query} {must_show}".lower()))
    def _cand_score(c):
        title = (c.get("title") or "").lower()
        score = 0
        if c.get("source") == "Wikipedia":
            score += 15
        geo_status, geo_delta = _geo_verify_candidate(c, entity_iso3, entity_country_en)
        score += geo_delta
        if geo_status == "verified":
            c["_geo_verified"] = True
        for term in target_terms:
            if len(term) >= 3 and term in title:
                score += 8
        if is_hist_ctx:
            for ht in ("1945", "1944", "1943", "1942", "1939", "1989", "bundesarchiv", "wwii", "world war", "archival", "ruins", "allied", "soviet", "army", "troops"):
                if ht in title:
                    score += 14
            for mt in ("fernsehturm", "tv tower", "skyline", "modern", "night view", "sunset", "tourism", "bode-museum"):
                if mt in title:
                    score -= 22
            if c.get("source") == "Pexels":
                score -= 12  # Pexels is mostly modern stock photos
        # معاقبة الكولاج والملصقات والأعلام والمواقع الجغرافية المناقضة تماماً
        if NON_PHOTO_RE.search(title) or NON_PHOTO_RE.search(c.get("url") or ""):
            score -= 60
        for bad_t in ("collage", "montage", "logo", "icon", "diagram"):
            if bad_t in title:
                score -= 30
        unrelated_geo = ["california", "san simeon", "ireland", "scotland", "mongolia", "china", "texas", "florida", "ohio", "khartoum"]
        for u in unrelated_geo:
            if u in title and u not in target_terms:
                score -= 35
        return score

    cands = sorted(cands, key=_cand_score, reverse=True)
    cands = [c for c in cands if _cand_score(c) >= -10]
    if not cands:
        return None, 0, "تم استبعاد النتائج غير المرتبطة جغرافياً"

    if not cfg("GEMINI_API_KEY"):
        log(f"  مفتاح Gemini غير مضبوط — اعتماد النتيجة الأكثر تطابقاً: «{cands[0].get('title')}»")
        return cands[0], 8, f"تم الاعتماد بناء على التطابق الجغرافي ({cands[0].get('title')[:40]})"
    try:
        ims, keep = [], []
        for c in cands[:6]:
            try:
                ims.append(_jpeg_bytes(fetch_image(c.get("thumb") or c["url"])))
                keep.append(c)
            except Exception as e:
                log(f"  فشل جلب صورة مصغرة: {str(e)[:60]}")
        if not keep:
            raise RuntimeError("تعذر جلب الصور المصغرة للمعاينة")
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
        elif not entity_iso3 and 0 <= i < len(keep) and score >= 4:
            log(f"  قبول استثنائي للدرجة {score} لتفادي السقوط في النص")
            return keep[i], score, f"{reason} (مقبولة بدرجة {score})"
        log(f"  رُفضت (score={score}<{MIN_SCORE}) — {reason}")
        return None, score, f"رفض النموذج (score={score}): {reason}"
    except Exception as e:  # noqa
        # عند تعذر Gemini (مثل 429): لا نقبل إلا صورة موثقة جغرافياً أو صورة Wikipedia الرئيسية أو Pexels تطابق اسم الدولة صراحةً
        c_en = (entity_country_en or "").strip().lower()
        for cand in cands:
            if cand.get("_geo_verified"):
                log(f"  تعذر Gemini ({str(e)[:40]}) — اعتماد صورة موثقة بالإحداثيات: {cand.get('title')}")
                return cand, 8, "صورة موثقة بالإحداثيات الجغرافية"
            if str(cand.get("source") or cand.get("src") or "").lower() == "wikipedia":
                log(f"  تعذر Gemini ({str(e)[:40]}) — اعتماد صورة Wikipedia الرئيسية: {cand.get('title')}")
                return cand, 7, "صورة Wikipedia الرئيسية للكيان"
            blob = f"{cand.get('title', '')} {cand.get('categories', '')}".lower()
            if c_en and c_en in blob and not NON_PHOTO_RE.search(blob):
                log(f"  تعذر Gemini ({str(e)[:40]}) — اعتماد صورة مطابقة صراحةً للدولة: {cand.get('title')}")
                return cand, 7, f"مطابقة صريحة للدولة ({c_en})"
        log(f"  اختيار Gemini تعذّر ({str(e)[:50]}) — لا توجد صورة موثقة جغرافياً")
        return None, 0, f"تعذر Gemini ولم تتوفر صورة موثقة جغرافياً ({str(e)[:40]})"


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
        self.done = {}  # query / iso3 -> accepted image file: a place named again reuses its photo
        os.makedirs(dest_dir, exist_ok=True)

    def resolve(self, beat, sentence="", vi_scene=None):
        vi_sc = vi_scene if isinstance(vi_scene, dict) else {}
        beat_q = (beat.get("query") or "").strip()
        vi_q = str(vi_sc.get("media_query_en") or "").strip()
        is_generic_beat_q = any(g in beat_q.lower() for g in ("landmark historical architecture", "ancient historical army", "ancient ruined city"))
        if vi_q and (not beat_q or is_generic_beat_q):
            q = vi_q
            must_show = vi_sc.get("must_show") or beat.get("must_show") or ""
        else:
            q = beat_q or vi_q
            must_show = beat.get("must_show") or vi_sc.get("must_show") or ""
        avoid = beat.get("avoid") or vi_sc.get("avoid") or ""
        if vi_sc.get("is_historical") and "modern" not in avoid.lower():
            avoid = f"{avoid} modern skyscrapers contemporary cars neon".strip()
        alt_queries = list(beat.get("alt_queries") or [])
        if beat_q and beat_q != q and beat_q not in alt_queries:
            alt_queries.append(beat_q)
        if vi_q and vi_q != q and vi_q not in alt_queries:
            alt_queries.insert(0, vi_q)
        iso_key = str(beat.get("entity_iso3") or "").strip().upper()
        for key in (("q", q.lower()), ("iso", iso_key) if iso_key else None):
            if key and key in self.done and not beat.get("cutout"):
                self.log(f"  نفس المكان ذُكر سابقاً ← إعادة استخدام صورته: «{q}»")
                self.reports.append({"sentence": sentence, "query": q, "queries_tried": [q], "candidates_count": 0, "score": 8,
                                     "status": "accepted", "reason": "إعادة استخدام صورة المكان نفسه", "image": self.done[key], "credit": "", "fallback": None})
                return {**beat, "img": self.done[key], "cut": False}
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

        entity_iso3 = str(beat.get("entity_iso3") or "").strip().upper()
        entity_country_en = str(beat.get("entity_country_en") or "").strip()

        def _entity_cache_dir(iso3_code):
            return CACHE / "entity_media" / iso3_code

        def _save_entity_cache(iso3_code, cand, img_obj):
            if not iso3_code or cut is not None:
                return
            try:
                cdir = _entity_cache_dir(iso3_code)
                cdir.mkdir(parents=True, exist_ok=True)
                key = hashlib.sha256(cand["url"].encode("utf-8")).hexdigest()[:12]
                img_obj.convert("RGB").save(cdir / f"{key}.jpg", "JPEG", quality=90)
                meta_out = {k: cand.get(k, "") for k in ("url", "title", "credit", "license", "source", "page")}
                meta_out["query"] = q
                (cdir / f"{key}.json").write_text(json.dumps(meta_out, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass

        def _load_entity_cache(iso3_code):
            if not iso3_code:
                return None, None
            cdir = _entity_cache_dir(iso3_code)
            if not cdir.exists():
                return None, None
            for jf in sorted(cdir.glob("*.json")):
                try:
                    meta_in = json.loads(jf.read_text(encoding="utf-8"))
                    jpg = jf.with_suffix(".jpg")
                    if jpg.exists() and meta_in.get("url") not in self.used:
                        return meta_in, jpg
                except Exception:
                    continue
            return None, None

        c, score, reason = pick(
            cands, q, sentence, self.log,
            must_show=must_show, avoid=avoid,
            entity_iso3=entity_iso3, entity_country_en=entity_country_en,
        )
        # إذا رفض Gemini الكل، جرّب الاستعلامات الاحتياطية بالبحث والاختيار مجدداً
        if not c:
            for aq in alt_queries:
                if aq not in queries_tried:
                    queries_tried.append(aq)
                self.log(f"  بحث احتياطي بعد الرفض: «{aq}»")
                extra = [c2 for c2 in find(aq, self.log) if c2["url"] not in self.used]
                if extra:
                    c, score, reason = pick(
                        extra, aq, sentence, self.log,
                        must_show=must_show, avoid=avoid,
                        entity_iso3=entity_iso3, entity_country_en=entity_country_en,
                    )
                if c:
                    break

        if not c and entity_iso3:
            cached_meta, cached_jpg = _load_entity_cache(entity_iso3)
            if cached_meta and cached_jpg:
                self.n += 1
                name = f"p{self.n}.jpg"
                path = os.path.join(self.dest, name)
                Image.open(cached_jpg).convert("RGB").save(path, "JPEG", quality=90)
                self.used.add(cached_meta["url"])
                self.credits.append({k: cached_meta.get(k, "") for k in ("title", "credit", "license", "source", "page")})
                self.reports.append({
                    "sentence": sentence, "query": q, "queries_tried": queries_tried,
                    "candidates_count": len(cands), "score": 8, "status": "accepted",
                    "reason": f"من كاش الكيان الموثّق ({entity_iso3})",
                    "image": f"media/{name}",
                    "credit": f"{cached_meta.get('title')} ({cached_meta.get('source')})",
                    "fallback": None,
                })
                return {**beat, "img": f"media/{name}", "cut": False, "entity_iso3": entity_iso3}

        if not c:
            reason_txt = reason or "لا توجد صور مرخصة مطابقة"
            rep = {
                "sentence": sentence,
                "query": q,
                "queries_tried": queries_tried,
                "candidates_count": len(cands),
                "score": score,
                "status": "fallback",
                "reason": reason_txt,
                "fallback": "generative_canvas"
            }
            self.reports.append(rep)
            beat_id = str(beat.get("id") or beat.get("title") or q or "photo")
            fb = direct.photo_to_text(beat, sentence)
            record_fallback(reason_txt, beat_id=beat_id, beat=fb, log_fn=self.log)
            return fb

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
            err_words = " ".join(str(e).split()[:10])
            reason_txt = f"فشل التنزيل: {err_words}"
            rep = {
                "sentence": sentence,
                "query": q,
                "queries_tried": queries_tried,
                "candidates_count": len(cands),
                "score": score,
                "status": "error",
                "reason": reason_txt,
                "fallback": "generative_canvas"
            }
            self.reports.append(rep)
            beat_id = str(beat.get("id") or beat.get("title") or q or "photo")
            fb = direct.photo_to_text(beat, sentence)
            record_fallback(reason_txt, beat_id=beat_id, beat=fb, log_fn=self.log)
            return fb

        self.used.add(c["url"])
        _save_entity_cache(entity_iso3, c, im)
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
        if cut is None:
            self.done[("q", q.lower())] = f"media/{name}"
            if iso_key:
                self.done[("iso", iso_key)] = f"media/{name}"
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
