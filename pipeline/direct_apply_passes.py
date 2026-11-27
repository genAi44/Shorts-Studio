"""Split from `pipeline/direct_apply.py` (re-exported there); see that module."""
from typing import Any, Dict, List
from .direct import CAMERAS, _number_in_text
from . import areamap


def _diversify_beats(s, targets):
    """Phase of `apply_beats`: cosmetic variety only (camera move, stat/bigtext layout, area-map layout) plus the truthfulness
    guard on photo numbers. It never changes a beat's kind: the director's decision is final (an invalid decision goes back
    to the LLM through the retry in `_retry_failed_plan`, it is not swapped here)."""
    areamap.assign_layouts(targets)
    stat_choices = ["ring", "bar", "stack", "plain"]
    bigtext_choices = ["center", "stack", "diag", "left"]
    cam_choices = ["zoom-in", "pan-left", "zoom-out", "tilt-up", "parallax", "pan-right", "handheld"]
    used = {"stat": set(), "bigtext": set()}
    prev_cam, cam_counter = None, 0
    for target in targets:
        beats = target.get("beats", [])
        for bi, b in enumerate(beats):
            if not isinstance(b, dict):
                continue
            kind = b.get("kind")
            # a number on a photo that is not spoken in the scene belongs to another entity: drop it (truthfulness)
            if kind == "photo" and b.get("number") and not _number_in_text(b["number"], target.get("narration", "")):
                b = beats[bi] = {k: v for k, v in b.items() if k != "number"}
            cam = b.get("camera")
            if not cam or cam == prev_cam or cam not in CAMERAS:
                cam = b["camera"] = cam_choices[cam_counter % len(cam_choices)]
                cam_counter += 1
            prev_cam = cam
            if kind in used:
                choices = stat_choices if kind == "stat" else bigtext_choices
                lay = b.get("layout") or (None if kind == "stat" else "center")
                if not lay or lay in used[kind]:
                    avail = [x for x in choices if x not in used[kind]] or (used[kind].clear() or choices)
                    lay = b["layout"] = avail[0]
                used[kind].add(lay)


def _storyteller_pass(s):
    """Phase of `apply_beats`."""
    try:
        from . import visual_tools
        from .scriptspec import PART_IDS, PARTS_BY_ID
        from .storyteller import (
            _extract_all_cities,
            _extract_countries_from_text,
            design_scene_specification,
            evaluate_and_improve_scene,
            generate_dynamic_tsx_file,
        )

        transitions = visual_tools.pick_transitions(len(PART_IDS), seed=42)
        used_palettes: set = set()
        used_environments: set = set()
        used_approaches: set = set()
        used_cameras: set = set()
        prev_signatures: List[str] = []
        dynamic_tsx_beats: List[Dict[str, Any]] = []
        global_beat_idx = 0

        # استخراج السياق العام للفيديو بالكامل (العنوان + الحقائق الموثقة + الدول والمدن الرئيسية)
        full_video_title = str(s.get("title") or "").strip()
        facts_list: List[str] = []
        for f_item in (s.get("facts") or []):
            if isinstance(f_item, dict) and f_item.get("claim"):
                facts_list.append(str(f_item["claim"]).strip())
            elif isinstance(f_item, str) and f_item.strip():
                facts_list.append(f_item.strip())
        if isinstance(s.get("_facts_data"), dict) and s["_facts_data"].get("facts"):
            raw_facts_str = str(s["_facts_data"]["facts"]).strip()
            for line in raw_facts_str.splitlines():
                cl = line.strip("•-* \t")
                if len(cl) > 12 and cl not in facts_list:
                    facts_list.append(cl)
                if len(facts_list) >= 8:
                    break
        facts_summary = " | ".join(facts_list[:6])

        all_script_text_parts = [full_video_title]
        video_countries: List[str] = []
        video_cities: List[Dict[str, Any]] = []
        seen_vc_coords = set()
        for pid in PART_IDS:
            sc_dict = s.get(pid)
            if isinstance(sc_dict, dict):
                all_script_text_parts.append(str(sc_dict.get("on_screen") or ""))
                all_script_text_parts.append(str(sc_dict.get("narration") or ""))
                vis_d = sc_dict.get("visual") if isinstance(sc_dict.get("visual"), dict) else {}
                for c_iso in (vis_d.get("countries") or vis_d.get("highlight") or []):
                    c_up = str(c_iso).upper().strip()
                    if c_up and c_up not in video_countries:
                        video_countries.append(c_up)
                for pt in (vis_d.get("points") or []):
                    if isinstance(pt, dict) and "lat" in pt and "lon" in pt:
                        ck = (round(float(pt["lat"]), 1), round(float(pt["lon"]), 1))
                        if ck not in seen_vc_coords:
                            seen_vc_coords.add(ck)
                            video_cities.append({
                                "name": str(pt.get("name") or ""),
                                "lat": float(pt["lat"]),
                                "lon": float(pt["lon"]),
                            })
        full_script_text = " ".join(all_script_text_parts)
        for c_iso in _extract_countries_from_text(full_script_text):
            if c_iso not in video_countries:
                video_countries.append(c_iso)
        for c_obj in _extract_all_cities(full_script_text):
            ck = (round(float(c_obj["lat"]), 1), round(float(c_obj["lon"]), 1))
            if ck not in seen_vc_coords:
                seen_vc_coords.add(ck)
                video_cities.append({
                    "name": c_obj["name"],
                    "lat": float(c_obj["lat"]),
                    "lon": float(c_obj["lon"]),
                })
            if c_obj.get("iso") and c_obj["iso"] not in video_countries:
                video_countries.append(c_obj["iso"])

        for idx, pid in enumerate(PART_IDS):
            if pid in s and isinstance(s[pid], dict):
                sc_role = PARTS_BY_ID[pid]["role"]
                sc_obj = {**s[pid], "id": pid, "role": sc_role}
                s[pid]["visuals"] = visual_tools.enrich_scene_visuals(sc_obj, scene_index=idx, preferred_icon_set="lucide")
                s[pid]["transition"] = transitions[idx]

                prev_narr = s.get(PART_IDS[idx - 1], {}).get("narration", "") if idx > 0 else ""
                next_narr = s.get(PART_IDS[idx + 1], {}).get("narration", "") if idx + 1 < len(PART_IDS) else ""
                full_scene_narr = s[pid].get("narration", "")
                sc_beats = s[pid].get("beats") or []

                # دمج مقاطع المشهد الواحد في مقطع بصري متكامل واحد يغطي الجملة كاملة (8 مشاهد = 8 تصاميم متكاملة)
                if len(sc_beats) > 1 and not any(b.get("kind") == "area_map" for b in sc_beats if isinstance(b, dict)):
                    primary_beat = dict(sc_beats[0])
                    concepts = [str(b.get("concept") or "").strip() for b in sc_beats if isinstance(b, dict) and b.get("concept")]
                    if concepts:
                        primary_beat["concept"] = " — ".join(dict.fromkeys(c for c in concepts if c))
                    for b_other in sc_beats[1:]:
                        if isinstance(b_other, dict) and b_other.get("kind") == "map" and primary_beat.get("kind") != "map":
                            for mk in ("countries", "highlight", "points"):
                                if b_other.get(mk) and not primary_beat.get(mk):
                                    primary_beat[mk] = b_other[mk]
                    sc_beats = [primary_beat]
                    s[pid]["beats"] = sc_beats

                for b_idx, beat_item in enumerate(sc_beats):
                    if not isinstance(beat_item, dict):
                        continue
                    sent_txt = full_scene_narr
                    was_fallback = beat_item.get("_fallback")
                    designed = design_scene_specification(
                        scene_id=f"{pid}_{b_idx}",
                        role=sc_role,
                        narration=sent_txt,
                        on_screen=beat_item.get("title") or s[pid].get("on_screen", ""),
                        scene_index=global_beat_idx,
                        total_scenes=len(PART_IDS),
                        prev_narration=prev_narr,
                        next_narration=next_narr,
                        video_title=full_video_title,
                        used_palettes=used_palettes,
                        used_environments=used_environments,
                        used_approaches=used_approaches,
                        used_cameras=used_cameras,
                    )
                    if beat_item.get("kind") in ("generative_canvas", "custom_scene"):
                        improved, _ = evaluate_and_improve_scene(designed, sent_txt, global_beat_idx, prev_signatures)
                        used_palettes.add(improved.get("bg_mood") or improved.get("accent"))
                        used_environments.add(improved.get("environment"))
                        if was_fallback:
                            improved["_fallback"] = True
                        if beat_item.get("concept"):
                            improved["concept"] = beat_item["concept"]
                        for gk in ("countries", "highlight", "points"):
                            if beat_item.get(gk):
                                improved[gk] = beat_item[gk]
                        improved["tsx_id"] = f"DynamicScene_{pid}_{b_idx}_{global_beat_idx}"
                        improved["narration"] = sent_txt
                        improved["video_title"] = full_video_title
                        improved["facts_summary"] = facts_summary
                        improved["video_countries"] = video_countries[:3]
                        improved["video_cities"] = video_cities[:5]
                        sc_beats[b_idx] = improved
                        dynamic_tsx_beats.append(improved)
                    else:
                        beat_item["scene_spec"] = designed["scene_spec"]
                        beat_item["narration_cues"] = designed["narration_cues"]
                        if beat_item.get("kind") not in ("photo", "map", "map_pin", "area_map"):
                            beat_item["tsx_id"] = f"DynamicScene_{pid}_{b_idx}_{global_beat_idx}"
                            beat_item["narration"] = sent_txt
                            beat_item["video_title"] = full_video_title
                            beat_item["facts_summary"] = facts_summary
                            beat_item["video_countries"] = video_countries[:3]
                            beat_item["video_cities"] = video_cities[:5]
                            beat_item["accent"] = designed.get("accent") or "#38bdf8"
                            beat_item["secondary_accent"] = designed.get("secondary_accent") or "#818cf8"
                            dynamic_tsx_beats.append(beat_item)
                        else:
                            beat_item.pop("tsx_id", None)
                    global_beat_idx += 1

        if dynamic_tsx_beats:
            generate_dynamic_tsx_file(dynamic_tsx_beats, use_llm=False)
    except Exception:
        pass
