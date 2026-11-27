"""وحدة البحث عن الحقائق قبل كتابة السكربت (Search Before Write).
تبحث في DuckDuckGo، Serper API، و Wikipedia العربية بالتوازي وتخزن النتائج في الكاش.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import requests
from .config import cfg

logger = logging.getLogger("pipeline.search")
CACHE_DIR = os.path.join("cache", "search")


def _cache_path(query: str) -> str:
    h = hashlib.sha1(query.strip().lower().encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{h}.json")


def _get_cached(query: str, ttl: int = 86400) -> Optional[List[Dict[str, Any]]]:
    path = _cache_path(query)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if time.time() - data.get("timestamp", 0) < ttl:
            return data.get("results")
    except Exception as e:
        logger.debug("Cache read error for '%s': %s", query, e)
    return None


def _set_cached(query: str, results: List[Dict[str, Any]]) -> None:
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        path = _cache_path(query)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {"timestamp": time.time(), "query": query, "results": results},
                f,
                ensure_ascii=False,
                indent=2,
            )
    except Exception as e:
        logger.warning("Cache write error for '%s': %s", query, e)


def _search_ddg(query: str, max_results: int = 5, timeout: int = 8) -> List[Dict[str, str]]:
    """المصدر 1: DuckDuckGo عبر مكتبة ddgs (مجاني بلا مفتاح)."""
    try:
        from ddgs import DDGS
        with DDGS(timeout=timeout) as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
            if not raw:
                # محاولة ثانية بـ backend='html' لبعض استعلامات اللغة العربية
                try:
                    raw = list(ddgs.text(query, max_results=max_results, backend="html"))
                except Exception:
                    pass
            items = []
            has_arabic_q = bool(re.search(r"[\u0600-\u06FF]", query or ""))
            for r in raw:
                title = (r.get("title") or "").strip()
                body = (r.get("body") or "").strip()
                href = (r.get("href") or "").strip()
                if title or body:
                    if has_arabic_q and not re.search(r"[\u0600-\u06FF]", f"{title} {body}"):
                        continue
                    items.append({
                        "title": title,
                        "snippet": body,
                        "url": href,
                        "source": "duckduckgo",
                    })
            return items
    except Exception as e:
        logger.warning("فشل بحث DuckDuckGo للاستعلام '%s': %s", query, e)
        return []


def _search_serper(query: str, max_results: int = 5, timeout: int = 8) -> List[Dict[str, str]]:
    """المصدر 2: Serper API إن كان SERPER_API_KEY مضبوطاً في .env."""
    key = cfg("SERPER_API_KEY") or os.environ.get("SERPER_API_KEY")
    if not key:
        return []
    try:
        endpoint = "https://google.serper.dev/search"
        headers = {"X-API-KEY": key.strip(), "Content-Type": "application/json"}
        payload = {"q": query, "num": max_results, "hl": "ar", "gl": "ae"}
        r = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            items = []
            for org in data.get("organic", []):
                title = (org.get("title") or "").strip()
                snippet = (org.get("snippet") or "").strip()
                link = (org.get("link") or "").strip()
                if title or snippet:
                    items.append({
                        "title": title,
                        "snippet": snippet,
                        "url": link,
                        "source": "serper",
                    })
            return items
        logger.warning("أعاد Serper API رمز الحالة %d: %s", r.status_code, r.text[:200])
    except Exception as e:
        logger.warning("فشل بحث Serper للاستعلام '%s': %s", query, e)
    return []


def _query_wiki_endpoint(query: str, lang: str = "ar", max_results: int = 3, timeout: int = 8) -> List[Dict[str, str]]:
    headers = {"User-Agent": "ShortsStudio/1.0 (https://github.com/shorts-studio; research-bot)"}
    try:
        search_url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": max_results,
        }
        r = requests.get(search_url, params=params, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return []
        data = r.json()
        search_results = data.get("query", {}).get("search", [])
        items = []
        for res in search_results:
            title = res.get("title")
            if not title:
                continue
            encoded_title = urllib.parse.quote(title.replace(" ", "_"))
            summary_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
            try:
                sr = requests.get(summary_url, headers=headers, timeout=timeout)
                if sr.status_code == 200:
                    sdata = sr.json()
                    extract = (sdata.get("extract") or "").strip()
                    page_url = (
                        sdata.get("content_urls", {}).get("desktop", {}).get("page")
                        or f"https://{lang}.wikipedia.org/wiki/{encoded_title}"
                    )
                    if extract:
                        items.append({
                            "title": title,
                            "snippet": extract,
                            "url": page_url,
                            "source": f"wikipedia_{lang}",
                        })
                        continue
            except Exception as e:
                logger.debug("تعذر جلب ملخص ويكيبيديا لـ '%s' (%s): %s", title, lang, e)

            # بديل: استخدام مقتطف البحث إن تعذر الملخص
            raw_snippet = re.sub(r"<[^>]+>", "", res.get("snippet", "")).strip()
            if raw_snippet:
                items.append({
                    "title": title,
                    "snippet": raw_snippet,
                    "url": f"https://{lang}.wikipedia.org/wiki/{encoded_title}",
                    "source": f"wikipedia_{lang}",
                })
        return items
    except Exception as e:
        logger.warning("فشل بحث Wikipedia (%s) للاستعلام '%s': %s", lang, query, e)
        return []


def _search_wikipedia(query: str, max_results: int = 3, timeout: int = 8) -> List[Dict[str, str]]:
    """المصدر 3: Wikipedia - an English query searches English Wikipedia (where most facts live), an Arabic one Arabic Wikipedia."""
    is_en = re.search(r"[a-zA-Z]{3,}", query or "") and not re.search(r"[؀-ۿ]", query or "")
    return _query_wiki_endpoint(query, lang="en" if is_en else "ar", max_results=max_results, timeout=timeout)


def search_query(query: str, timeout: int = 8) -> List[Dict[str, str]]:
    """يبحث في المصادر الثلاثة بالترتيب مع استخدام الكاش."""
    cached = _get_cached(query)
    if cached is not None:
        return cached

    results = _search_ddg(query, max_results=5, timeout=timeout)
    if not results:
        results = _search_serper(query, max_results=5, timeout=timeout)
    if not results:
        results = _search_wikipedia(query, max_results=3, timeout=timeout)

    if results:
        _set_cached(query, results)
    return results


def generate_queries(topic: str, n: int = 3) -> List[str]:
    """توليد 2-3 استعلامات بحث تلقائياً من فكرة وموضوع الفيديو."""
    t = topic.strip()
    # تنظيف العبارات التمهيدية
    t_clean = re.sub(
        r"^(أريد\s+|اكتب\s+|اعمل\s+|فيديو\s+عن\s+|فيديو\s+قصير\s+عن\s+|تحدث\s+عن\s+|معلومات\s+عن\s+|سؤال\s+عن\s+)",
        "",
        t,
        flags=re.IGNORECASE,
    ).strip()
    if not t_clean:
        t_clean = t

    # استخراج كبرى الكيانات والمدن إن وجدت لضمان دقة الاستعلامات
    candidates = [
        t_clean,
        f"{t_clean} قائمة",
        f"{t_clean} تاريخ وتأسيس",
        f"أهم {t_clean}",
    ]
    seen = set()
    queries = []
    for q in candidates:
        q_norm = q.strip().lower()
        if q_norm not in seen:
            seen.add(q_norm)
            queries.append(q.strip())
        if len(queries) >= n:
            break
    return queries


QUERY_SYSTEM = ("You write web search queries to research the facts of a short educational video. Reply with JSON only: "
                '{"en": ["2 precise English search queries"], "ar": ["1 precise Arabic search query"], "keywords": ["4-8 English and '
                'Arabic content words the facts must be about"]}. Queries name the concrete subject (places, people, the phenomenon), '
                "never generic words like list, history or facts on their own.")


def plan_queries(topic: str) -> Dict[str, List[str]]:
    """Specific search queries + the keywords a relevant fact must contain (LLM; falls back to the bare topic).
    The old fixed suffixes ("قائمة", "تاريخ وتأسيس") matched unrelated list pages (seen: 1990s films for a city-borders topic)."""
    try:
        from .llm import call_llm_json
        d = call_llm_json("script", QUERY_SYSTEM, topic, temperature=0.2)
        en = [str(q) for q in (d.get("en") or []) if str(q).strip()][:2]
        ar = [str(q) for q in (d.get("ar") or []) if str(q).strip()][:1]
        kw = [str(k) for k in (d.get("keywords") or []) if str(k).strip()][:8]
        if en or ar:
            return {"queries": en + ar, "keywords": kw}
    except Exception as e:  # noqa: BLE001 - search still runs on the topic itself
        logger.warning("query planning failed (%s): searching the topic as written", e)
    return {"queries": generate_queries(topic, n=1), "keywords": []}


_STOP = {"what", "why", "how", "the", "and", "for", "with", "from", "that", "this", "are", "was", "were", "list",
         "لماذا", "كيف", "ماذا", "التي", "الذي", "قائمة", "تاريخ", "أهم"}


def _content_words(text: str) -> set:
    return {w for w in re.findall(r"[\w؀-ۿ]{4,}", (text or "").lower()) if w not in _STOP}


def relevant(item: Dict[str, str], keywords: List[str], topic: str) -> bool:
    """Keep a result only if it shares a content word with the topic / planned keywords, and is not an unrelated list page."""
    title = (item.get("title") or "").lower()
    text = f"{title} {item.get('snippet', '')}".lower()
    if re.match(r"\s*(list of|قائمة)", title) and not re.search(r"\d|قائمة|list", topic.lower()):
        return False
    want = _content_words(topic) | {w for k in keywords for w in _content_words(k)}
    return bool(want) and any(w in text for w in want)


MIN_RELEVANT_FACTS = 3

JUDGE_SYSTEM = ("You check search results for a short educational video. Reply with JSON only: {\"keep\": [indices]} - the indices "
                "of the results that are ABOUT the video's topic and help explain it. Drop news, events and pages that only share a word "
                "with the topic (e.g. a storm or protests in American cities for a topic about why city borders look odd).")


def judge(topic: str, items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """LLM relevance check after the word filter (shared words alone let unrelated news through). Falls back to the input."""
    if not items:
        return items
    try:
        from .llm import call_llm_json
        listing = "\n".join(f"{i}. {it.get('title', '')}: {(it.get('snippet') or '')[:220]}" for i, it in enumerate(items))
        d = call_llm_json("script", JUDGE_SYSTEM, f"Topic: {topic}\n\nResults:\n{listing}", temperature=0.0)
        keep = {int(i) for i in (d.get("keep") or []) if str(i).lstrip("-").isdigit()}
        return [it for i, it in enumerate(items) if i in keep]
    except Exception as e:  # noqa: BLE001 - the word filter result is still used
        logger.warning("relevance check failed (%s): keeping the word-filtered results", e)
        return items


def search_facts(topic: str, n_queries: int = 3) -> dict:
    """يبحث في الويب عن حقائق موثوقة حول الموضوع ويعيد قائمة النقاط والمصادر."""
    if not topic or not topic.strip():
        return {"facts": "", "sources": [], "count": 0}

    plan = plan_queries(topic)
    queries = plan["queries"][:max(1, n_queries)]
    all_results: List[Dict[str, str]] = []

    with ThreadPoolExecutor(max_workers=min(4, max(1, len(queries)))) as executor:
        futures = {executor.submit(search_query, q, 8): q for q in queries}
        for future in as_completed(futures):
            try:
                res = future.result()
                if res:
                    all_results.extend(res)
            except Exception as e:
                logger.warning("خطأ في مهمة البحث المتوازية: %s", e)

    # إزالة التكرار بناءً على الرابط
    seen_urls = set()
    deduped: List[Dict[str, str]] = []
    for item in all_results:
        url = (item.get("url") or "").strip()
        if not url:
            continue
        norm_url = url.split("#")[0].rstrip("/")
        if norm_url not in seen_urls:
            seen_urls.add(norm_url)
            deduped.append(item)

    kept = judge(topic, [it for it in deduped if relevant(it, plan["keywords"], topic)])
    if len(kept) < len(deduped):
        logger.warning("search: %d result(s) unrelated to the topic dropped", len(deduped) - len(kept))
    deduped = kept

    bullets = []
    sources = []
    for item in deduped:
        snippet = (item.get("snippet") or "").strip()
        snippet = re.sub(r"\s+", " ", snippet)
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        if snippet:
            bullets.append(f"• {title}: {snippet} (المصدر: {url})")
            sources.append(url)

    if not bullets:
        logger.warning("لم يُعثر على أي حقائق من الويب للموضوع: '%s' (سيستمر التوليد بدون تعطيل).", topic)

    facts_text = "\n".join(bullets)
    return {
        "facts": facts_text,
        "sources": sources,
        "count": len(bullets),
        "queries": queries,
        "weak": len(bullets) < MIN_RELEVANT_FACTS,  # too little relevant material: the script may be inaccurate
    }
