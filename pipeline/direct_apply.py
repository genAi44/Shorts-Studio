"""Split from `pipeline/direct.py` (re-exported there); see that module."""
from typing import Any, Callable, Dict, List, Optional
from .geo import ISO3_TO_COUNTRY_EN, detect_city_in_text
from . import areamap
import copy
import re
from .config import record_fallback
from .direct import BEAT_RULES, CAMERAS, _number_in_text, _words, detect_photo_beat, fallback_beat, guard_beat, normalize_beat, sentences, validate_beat  # noqa: E402


MAX_CUSTOM_RUN = 2  # protocol 5.2: never more than ~3 near-equal scenes in a row; photo/map/area_map render natively


def variety_reasons(got: Dict[str, Any], scene_ids: List[str]) -> List[str]:
    """Scenes made only of custom_scene, in runs longer than MAX_CUSTOM_RUN (every one becomes an LLM drawing: no photo, no map)."""
    run: List[str] = []
    out: List[str] = []

    def flush():
        if len(run) > MAX_CUSTOM_RUN:
            out.append(f"{', '.join(run)}: {len(run)} consecutive scenes are all custom_scene (max {MAX_CUSTOM_RUN}): "
                       "turn the ones that name a real place, landmark, person or event into kind photo or map")

    for sid in scene_ids:
        beats = got.get(sid)
        kinds = [b.get("kind") for b in beats if isinstance(b, dict)] if isinstance(beats, list) else []
        if kinds and all(k == "custom_scene" for k in kinds):
            run.append(sid)
        else:
            flush()
            run = []
    flush()
    return out


def _retry_failed_plan(geo, got, llm_retry_fn, s, scenes_of):
    """Phase of `apply_beats`."""
    # Pre-check LLM beat plan against BEAT_RULES; allow max 1 retry to the LLM before forcing fallbacks
    if got and callable(llm_retry_fn):
        failed_reasons: List[str] = []
        for sc in scenes_of(s):
            raw_list = got.get(sc["id"])
            if not isinstance(raw_list, list):
                continue
            sents = sentences(sc["narration"])
            for i, s_txt in enumerate(sents):
                if i < len(raw_list) and isinstance(raw_list[i], dict):
                    rk = raw_list[i].get("kind")
                    rule = BEAT_RULES.get(rk)
                    if not rule or not rule["predicate"](raw_list[i], s_txt, geo):
                        failed_reasons.append(f"{sc['id']}[{i}] ({rk}): {rule['reason'] if rule else 'unknown kind'}")
            failed_reasons += areamap.missing_reasons(sc["id"], raw_list[:len(sents)])
        failed_reasons += variety_reasons(got, [sc["id"] for sc in scenes_of(s)])
        try:
            from . import entities as _ent
            failed_reasons += _ent.plan_errors(s, got, _ent.ensure_plan(s, geo))
        except Exception as _e:  # noqa: BLE001 - never silent
            record_fallback(f"entity validation of the director plan unavailable: {_e}", beat_id="entities")
        if failed_reasons:
            try:
                retry_res = llm_retry_fn(failed_reasons)
                if isinstance(retry_res, dict) and retry_res.get("scenes"):
                    got = {x.get("id"): x.get("beats") for x in (retry_res.get("scenes") or []) if isinstance(x, dict)}
            except Exception:
                pass
    return got


def _assign_scene_beats(geo, got, s, scenes_of):
    """Phase of `apply_beats`."""
    targets = []
    for sc in scenes_of(s):
        target = s.get(sc["id"])
        if not target:
            continue
        raw = got.get(sc["id"])
        sents = sentences(sc["narration"])
        raw = raw if isinstance(raw, list) else []
        # قاعدة المساحة: جملة تذكر مساحة مكان بلا مقطع area_map (حتى بعد إعادة المحاولة) => بديل مرئي مُعلَّم
        claims = [areamap.claim_of(raw[i]) if i < len(raw) else None for i in range(len(sents))]
        target["beats"] = [
            areamap.fallback_beat(claims[i], sc["id"], i) if claims[i] and raw[i].get("kind") != "area_map"
            else guard_beat(raw[i], sc, i, sents[i], geo) if i < len(raw)
            else validate_beat(normalize_beat(fallback_beat(sc, i, sents[i]), sents[i], geo))
            for i in range(len(sents))
        ]
        # إذا كان المشهد يحمل visual.type == "map" أو يذكر مدينة/عاصمة معروفة ولم يضع المخرج خريطة،
        # نضمن وجود مقطع خريطة حقيقي (map) للمدينة أو الدولة في أول جملة من المشهد
        vis = sc.get("visual") if isinstance(sc.get("visual"), dict) else {}
        det_city, det_info = detect_city_in_text(sc.get("on_screen", ""))
        if not det_city:
            det_city, det_info = detect_city_in_text(sc.get("narration", ""))

        has_map_beat = any(b.get("kind") in ("map", "map_pin", "area_map") for b in target["beats"])
        if not has_map_beat and sc.get("role") in ("body", "lead") and target["beats"]:
            orig_concept = target["beats"][0].get("concept")
            if vis.get("type") == "map" and (vis.get("countries") or vis.get("points")):
                map_cand = normalize_beat({
                    "kind": "map",
                    "title": sc.get("on_screen") or _words(sents[0], 5),
                    "countries": vis.get("countries") or [],
                    "highlight": vis.get("highlight") or vis.get("countries") or [],
                    "points": vis.get("points") or [],
                    "camera": "zoom-in",
                }, sents[0], geo)
                if map_cand.get("kind") == "map":
                    if orig_concept:
                        map_cand["concept"] = orig_concept
                    target["beats"][0] = map_cand
            elif det_city and det_info:
                map_cand = normalize_beat({
                    "kind": "map",
                    "title": sc.get("on_screen") or det_city,
                    "countries": [det_info["iso"]],
                    "highlight": [det_info["iso"]],
                    "points": [{"name": det_city, "lat": det_info["lat"], "lon": det_info["lon"], "dot": True}],
                    "camera": "zoom-in",
                }, sents[0], geo)
                if map_cand.get("kind") == "map":
                    if orig_concept:
                        map_cand["concept"] = orig_concept
                    target["beats"][0] = map_cand
        targets.append(target)
    return targets


def _merge_visual_plan(geo, result, s, targets):
    """Phase of `apply_beats`."""
    # دمج خطة محرك الذكاء البصري (Visual Intelligence Engine) لتوحيد السياق التاريخي والجغرافي عبر المشاهد
    try:
        from .visual_intelligence import analyze_script_visual_intelligence
        vi_plan = s.get("_visual_intelligence")
        if not isinstance(vi_plan, dict) or not vi_plan.get("scenes"):
            vi_plan = analyze_script_visual_intelligence(s, geo=geo, use_llm=bool(result))
            s["_visual_intelligence"] = vi_plan
        vi_by_id = {sc_v["id"]: sc_v for sc_v in (vi_plan.get("scenes") or []) if isinstance(sc_v, dict)}
        for t in targets:
            sc_vi = vi_by_id.get(t.get("id"))
            if not sc_vi:
                continue
            t["_vi"] = sc_vi
            for b in (t.get("beats") or []):
                if isinstance(b, dict):
                    b["visual_intelligence"] = {
                        "semantic_goal": sc_vi.get("semantic_goal"),
                        "historical_era": sc_vi.get("historical_era"),
                        "is_historical": sc_vi.get("is_historical"),
                        "visual_mode": sc_vi.get("visual_mode"),
                        "entities": [e.get("name") for e in (sc_vi.get("entities") or [])[:6]],
                        "relationships": sc_vi.get("relationships") or [],
                        "avoid": sc_vi.get("avoid"),
                    }
                    if b.get("kind") == "photo":
                        if not b.get("query") and sc_vi.get("media_query_en"):
                            b["query"] = sc_vi["media_query_en"]
                        if not b.get("must_show") and sc_vi.get("must_show"):
                            b["must_show"] = sc_vi["must_show"]
                        if not b.get("avoid") and sc_vi.get("avoid"):
                            b["avoid"] = sc_vi["avoid"]
                    if b.get("kind") == "photo" and sc_vi.get("media_query_en"):
                        b["query"] = sc_vi["media_query_en"]
                        if sc_vi.get("must_show"):
                            b["must_show"] = sc_vi["must_show"]
                        if sc_vi.get("avoid"):
                            b["avoid"] = sc_vi["avoid"]
    except Exception:
        pass


def _upgrade_photos(geo, s, targets):
    """Phase of `apply_beats`."""
    # ضمان تنوّع بصري سينمائي: ترقية حتى مشهدين (hook / body) إلى صور حقيقية مرخّصة (photo)
    # لتفعيل تخطيط الشاشة المقسّمة (Photo Top + Panoramic Map Bottom) بدلاً من الاقتصار على رسوم SVG فقط
    photo_count = sum(1 for t in targets for b in (t.get("beats") or []) if b.get("kind") == "photo")
    map_count = sum(1 for t in targets for b in (t.get("beats") or []) if b.get("kind") in ("map", "map_pin"))
    if photo_count < 2:
        for t in targets:
            if photo_count >= 2:
                break
            if t.get("role") not in ("hook", "body") or not t.get("beats"):
                continue
            cur_kind = t["beats"][0].get("kind")
            if cur_kind in ("photo", "area_map"):
                continue
            if cur_kind in ("map", "map_pin") and map_count <= 1:
                continue
            first_sent = (sentences(t.get("narration", "")) or [t.get("narration", "")])[0]
            pb = detect_photo_beat(first_sent) or detect_photo_beat(f"{t.get('on_screen', '')} {s.get('title', '')}")
            sc_vi = t.get("_vi") if isinstance(t.get("_vi"), dict) else {}
            if not pb and sc_vi.get("media_query_en"):
                pb = {
                    "kind": "photo",
                    "query": sc_vi["media_query_en"],
                    "text": _words(first_sent, 5),
                    "camera": "parallax",
                    "must_show": sc_vi.get("must_show") or sc_vi["media_query_en"],
                    "avoid": sc_vi.get("avoid") or "watermark text collage",
                    "alt_queries": [sc_vi["media_query_en"]],
                }
            if pb:
                if sc_vi.get("media_query_en"):
                    pb["query"] = sc_vi["media_query_en"]
                if sc_vi.get("must_show"):
                    pb["must_show"] = sc_vi["must_show"]
                if sc_vi.get("avoid"):
                    pb["avoid"] = sc_vi["avoid"]
                pb["text"] = _words(first_sent, 5)
                pb_norm = validate_beat(normalize_beat(pb, first_sent, geo))
                if pb_norm.get("kind") == "photo":
                    t["beats"][0] = pb_norm
                    photo_count += 1


def _enrich_hook_map(s, scenes_of):
    """Phase of `apply_beats`."""
    # إثراء خريطة المشهد الافتتاحي (Hook) بدبابيس جميع المدن/العواصم المذكورة في السكربت إن كانت نقاطها فارغة
    hook_target = s.get("hook")
    if hook_target and hook_target.get("beats"):
        for hb in hook_target["beats"]:
            if hb.get("kind") == "map" and not hb.get("points"):
                all_pts = []
                seen_c = set()
                for other_sc in scenes_of(s):
                    for txt in (other_sc.get("on_screen", ""), other_sc.get("narration", "")):
                        c_name, c_dict = detect_city_in_text(txt)
                        if c_name and c_name not in seen_c and c_dict:
                            seen_c.add(c_name)
                            all_pts.append({"name": c_name, "lat": c_dict["lat"], "lon": c_dict["lon"], "dot": True})
                if all_pts:
                    hb["points"] = all_pts[:6]


def apply_beats(script, result, geo=None, llm_retry_fn: Optional[Callable[[List[str]], dict]] = None):

    """يدمج ناتج المخرج في السكربت بعد فحصه عبر BEAT_RULES (مع إعادة محاولة واحدة كحد أقصى للـ LLM) وتنظيفه."""
    from .scriptspec import scenes_of
    s = copy.deepcopy(script)
    result = result if isinstance(result, dict) else {}
    got = {x.get("id"): x.get("beats") for x in (result.get("scenes") or []) if isinstance(x, dict)}

    got = _retry_failed_plan(geo, got, llm_retry_fn, s, scenes_of)

    targets = _assign_scene_beats(geo, got, s, scenes_of)

    _merge_visual_plan(geo, result, s, targets)

    _upgrade_photos(geo, s, targets)

    _enrich_hook_map(s, scenes_of)
    _diversify_beats(s, targets)
    _storyteller_pass(s)
    s['body'] = [s.get('body1', {}), s.get('body2', {}), s.get('body3', {})]
    s['loop'] = s.get('cta', {})
    return s


def auto_beats(script, geo=None):

    """مقاطع آمنة بلا نموذج (من الـ visual الحالي)."""
    return apply_beats(script, {}, geo)


# Re-exported so `pipeline.direct_apply.<name>` keeps working.
from .direct_apply_passes import (  # noqa: E402,F401
    _diversify_beats,
    _storyteller_pass,
)
