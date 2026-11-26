"""Split from `pipeline/visual_tools.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import os
from .visual_tools import ROOT, _load_emoji_catalog, _load_lottie_manifest  # noqa: E402


def qa_visual_review(spec: Dict[str, Any]) -> List[Dict[str, str]]:
    """QA Agent's visual review:
    Checks for visual clutter (>3 visuals per scene), mixed icon sets, emoji spam (>1 emoji per scene),
    unsafe 9:16 margins, and overlapping coordinates.
    """
    issues: List[Dict[str, str]] = []
    scenes = spec.get("scenes", []) if isinstance(spec, dict) else []
    icon_sets_seen = set()

    for sc in scenes:
        sid = sc.get("id", "scene")
        visuals = sc.get("visuals") or []
        if len(visuals) > 3:
            issues.append({
                "level": "warn",
                "where": sid,
                "msg": f"المشهد '{sid}' يحتوي على {len(visuals)} عناصر بصرية (الحد الأقصى الموصى به 3 لمنع الازدحام البصري).",
            })
        emoji_cnt = sum(1 for v in visuals if isinstance(v, dict) and v.get("kind") == "emoji")
        if emoji_cnt > 1:
            issues.append({
                "level": "warn",
                "where": sid,
                "msg": f"المشهد '{sid}' يحتوي على {emoji_cnt} رموز تعبيرية (ممنوع الإكثار من الإيموجي).",
            })
        coords = []
        for v in visuals:
            if not isinstance(v, dict):
                continue
            if v.get("kind") == "icon":
                name = str(v.get("spec", {}).get("name", ""))
                if ":" in name:
                    icon_sets_seen.add(name.split(":")[0])
            x, y = v.get("x"), v.get("y")
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                if x < 70 or x > 1010 or y < 160 or y > 1480:
                    issues.append({
                        "level": "warn",
                        "where": sid,
                        "msg": f"عنصر بصري في '{sid}' خارج الهوامش الآمنة لـ 9:16 ({x}, {y}).",
                    })
                for ox, oy in coords:
                    if abs(x - ox) < 70 and abs(y - oy) < 70:
                        issues.append({
                            "level": "warn",
                            "where": sid,
                            "msg": f"تداخل بصري محتمل بين عنصرين في المشهد '{sid}' عند ({x}, {y}).",
                        })
                coords.append((x, y))

    if len(icon_sets_seen) > 1:
        issues.append({
            "level": "warn",
            "where": "all",
            "msg": f"تعددت مجموعات الأيقونات في نفس الفيديو ({sorted(icon_sets_seen)})؛ يُفضّل توحيد أسلوب الأيقونات.",
        })

    return issues


def record_asset_credits(spec: Dict[str, Any], job_dir: Optional[str] = None) -> Dict[str, Any]:
    """Scans `spec` for all visual assets used and records per-asset attribution in `credits.json`."""
    root_credits_path = ROOT / "credits.json"
    base_credits = (
        json.loads(root_credits_path.read_text(encoding="utf-8"))
        if root_credits_path.exists()
        else {"project": "shorts-studio", "collections": {}, "usedAssets": []}
    )

    used_assets: List[Dict[str, Any]] = []
    emoji_cat = {e["char"]: e for e in _load_emoji_catalog().get("items", [])}
    lottie_cat = {m["id"]: m for m in _load_lottie_manifest().get("items", [])}

    for sc in spec.get("scenes", []) if isinstance(spec, dict) else []:
        for v in sc.get("visuals") or []:
            if not isinstance(v, dict):
                continue
            kind = v.get("kind")
            vspec = v.get("spec") or {}
            if kind == "icon":
                name = str(vspec.get("name", "lucide:landmark"))
                prefix = name.split(":")[0] if ":" in name else "lucide"
                used_assets.append({
                    "kind": "icon",
                    "id": name,
                    "collection": prefix,
                    "license": "ISC" if prefix == "lucide" else "MIT",
                    "attributionRequired": False,
                })
            elif kind == "emoji":
                ch = str(vspec.get("char", ""))
                em = emoji_cat.get(ch, {})
                col = em.get("collection", "noto-emoji")
                attr = col == "twemoji" or bool(em.get("attributionRequired", False))
                used_assets.append({
                    "kind": "emoji",
                    "id": ch,
                    "collection": col,
                    "license": "CC-BY 4.0" if col == "twemoji" else "Apache-2.0",
                    "attributionRequired": attr,
                    "credit": (
                        "Twemoji graphics by Twitter, Inc and contributors (CC-BY 4.0)"
                        if col == "twemoji"
                        else "Google Noto Color Emoji (Apache-2.0)"
                    ),
                })
            elif kind == "flag":
                code = str(vspec.get("code", "EG"))
                used_assets.append({
                    "kind": "flag",
                    "id": code,
                    "collection": "flag-icons",
                    "license": "MIT",
                    "attributionRequired": False,
                })
            elif kind == "lottie":
                lid = str(vspec.get("name", "checkmark"))
                lm = lottie_cat.get(lid, {})
                used_assets.append({
                    "kind": "lottie",
                    "id": lid,
                    "collection": "lottie-local",
                    "license": lm.get("license", "CC0-1.0"),
                    "sourceUrl": lm.get("sourceUrl", "packages/assets/lottie/manifest.json"),
                    "attributionRequired": bool(lm.get("attributionRequired", False)),
                })

    dedup = {}
    for ua in used_assets:
        dedup[f"{ua['kind']}:{ua['id']}"] = ua
    final_list = list(dedup.values())

    base_credits["usedAssets"] = final_list
    root_credits_path.write_text(json.dumps(base_credits, ensure_ascii=False, indent=2), encoding="utf-8")
    if job_dir and os.path.isdir(job_dir):
        Path(job_dir, "credits.json").write_text(
            json.dumps(base_credits, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return base_credits
