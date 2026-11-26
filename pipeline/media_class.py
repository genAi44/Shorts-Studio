"""Split from `pipeline/media.py` (re-exported there); see that module."""
from PIL import Image
from . import direct
import hashlib
import json
import os
from .config import record_fallback
from . import media as _media  # patched names (find, pick, fetch_image, CACHE) are looked up on `media` at call time
from .media import cutout  # noqa: E402


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
            cs = _media.find(qry, self.log, wikipedia=wikipedia)
            for n in (3, 2):
                if not cs and len(qry.split()) > n:
                    sub_q = " ".join(qry.split()[:n])
                    if sub_q not in queries_tried:
                        queries_tried.append(sub_q)
                    cs = _media.find(sub_q, self.log, wikipedia=False)
            return [c for c in cs if c["url"] not in self.used]

        cands = _try_query(q)
        # جرّب الاستعلامات الاحتياطية إن لم تُعطِ الأولى نتائج
        for aq in alt_queries:
            if cands:
                break
            if aq not in queries_tried:
                queries_tried.append(aq)
            self.log(f"  بحث بديل: «{aq}»")
            cands += [c for c in _media.find(aq, self.log) if c["url"] not in self.used]

        entity_iso3 = str(beat.get("entity_iso3") or "").strip().upper()
        entity_country_en = str(beat.get("entity_country_en") or "").strip()

        def _entity_cache_dir(iso3_code):
            return _media.CACHE / "entity_media" / iso3_code

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

        c, score, reason = _media.pick(
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
                extra = [c2 for c2 in _media.find(aq, self.log) if c2["url"] not in self.used]
                if extra:
                    c, score, reason = _media.pick(
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
            im = _media.fetch_image(c["url"])
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
