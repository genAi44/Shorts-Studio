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
    """المصدر 1: DuckDuckGo عبر مكتبة duckduckgo_search (مجاني بلا مفتاح)."""
    try:
        from duckduckgo_search import DDGS
        with DDGS(timeout=timeout) as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
            if not raw:
                # محاولة ثانية بـ backend='html' لبعض استعلامات اللغة العربية
                try:
                    raw = list(ddgs.text(query, max_results=max_results, backend="html"))
                except Exception:
                    pass
            items = []
            for r in raw:
                title = (r.get("title") or "").strip()
                body = (r.get("body") or "").strip()
                href = (r.get("href") or "").strip()
                if title or body:
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
    """المصدر 3: Wikipedia REST API عالمياً (عربي أولاً مع تغطية شاملة لكل دول العالم)."""
    items = _query_wiki_endpoint(query, lang="ar", max_results=max_results, timeout=timeout)
    if not items:
        # البحث في النسخة العالمية الشاملة إن لم توجد في العربية
        items = _query_wiki_endpoint(query, lang="en", max_results=max_results, timeout=timeout)
    return items


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

    # تقسيم الاستعلامات لتغطية التاريخ، الإحصائيات، والحقائق البارزة
    candidates = [
        t_clean,
        f"{t_clean} تاريخ وحقائق",
        f"{t_clean} أرقام وإحصائيات",
        f"معلومات عن {t_clean}",
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


def search_facts(topic: str, n_queries: int = 3) -> dict:
    """يبحث في الويب عن حقائق موثوقة حول الموضوع ويعيد قائمة النقاط والمصادر."""
    if not topic or not topic.strip():
        return {"facts": "", "sources": [], "count": 0}

    queries = generate_queries(topic, n=n_queries)
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
    }
