import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "pipeline" / "direct.py"

content = TARGET.read_text(encoding="utf-8")

# 1. Update imports
old_imp = "from pathlib import Path"
new_imp = "from pathlib import Path\nfrom .icons import pick_icons_for_beat, get_icon_path"
if old_imp in content and "pick_icons_for_beat" not in content:
    content = content.replace(old_imp, new_imp, 1)

# 2. Update KINDS
old_kinds = 'KINDS = ["map", "stat", "bigtext", "bars", "timeline", "versus", "list", "icons", "canvas", "photo", "split", "ticker", "cardstack"]'
new_kinds = 'KINDS = ["icon_scene", "map_pin", "timeline_card", "stat_ring_v2", "map", "stat", "bigtext", "bars", "timeline", "versus", "list", "icons", "canvas", "photo", "split", "ticker", "cardstack"]'
if old_kinds in content:
    content = content.replace(old_kinds, new_kinds, 1)

# 3. Add handling in normalize_beat
old_norm_start = '    if kind == "bigtext":\n        return bigtext()'
new_norm_handlers = '''    if kind == "icon_scene":
        picked = pick_icons_for_beat(sentence, b.get("text", "") or b.get("title", ""), n=4)
        hero = b.get("hero_icon") or (picked[0] if picked else "icons/monument/monument.svg")
        o = {
            "kind": "icon_scene",
            "title": _words(b.get("title") or b.get("text") or fallback_text, 7),
            "hero_icon": hero,
            "center_label": _words(b.get("center_label") or b.get("label") or "المركز", 3),
        }
        if b.get("sub"):
            o["sub"] = _words(b.get("sub"), 8)
        badges = b.get("badges") or b.get("items")
        if badges and isinstance(badges, list):
            o["badges"] = [
                {
                    "icon": bg.get("icon") or (picked[i % len(picked)] if picked else "icons/history/pyramid.svg"),
                    "label": _words(bg.get("label") or bg.get("text"), 3),
                    "x": bg.get("x"),
                    "y": bg.get("y")
                }
                for i, bg in enumerate(badges[:4]) if isinstance(bg, dict)
            ]
        return _add_camera(o, b)

    if kind == "map_pin":
        region = b.get("region") or "egypt"
        pts = []
        for p in (b.get("points") or [])[:5]:
            if isinstance(p, dict):
                pts.append({
                    "name": _s(p.get("name"), 24),
                    "x": p.get("x", 540),
                    "y": p.get("y", 870),
                    "icon": p.get("icon") or "icons/map/map_pin.svg"
                })
        o = {
            "kind": "map_pin",
            "title": _words(b.get("title") or fallback_text, 7),
            "region": region,
            "points": pts
        }
        return _add_camera(o, b)

    if kind == "timeline_card":
        items = []
        for it in (b.get("items") or [])[:4]:
            if isinstance(it, dict):
                items.append({
                    "year": _s(it.get("year"), 12),
                    "label": _words(it.get("label") or it.get("text"), 6),
                    "icon": it.get("icon") or "icons/time/history_clock.svg"
                })
        o = {
            "kind": "timeline_card",
            "title": _words(b.get("title") or fallback_text, 7),
            "items": items
        }
        return _add_camera(o, b)

    if kind == "stat_ring_v2":
        if not _s(b.get("number")):
            return bigtext()
        picked = pick_icons_for_beat(sentence, b.get("label", ""), n=1)
        o = {
            "kind": "stat_ring_v2",
            "title": _words(b.get("title"), 7),
            "number": _s(b.get("number"), 16),
            "label": _words(b.get("label"), 8),
            "icon": b.get("icon") or (picked[0] if picked else "icons/coin/gold_bars.svg")
        }
        return _add_camera(o, b)

    if kind == "bigtext":
        return bigtext()'''

if old_norm_start in content:
    content = content.replace(old_norm_start, new_norm_handlers, 1)

# 4. Update fallback_beat
old_fallback_end = '    return {"kind": "bigtext", "title": "", "text": " ".join(sentence.split()[:4]).strip(".!؟?،:؛ ")}'
new_fallback_end = '''    picked = pick_icons_for_beat(sentence, n=3)
    return {
        "kind": "icon_scene",
        "title": " ".join(sentence.split()[:4]).strip(".!؟?،:؛ "),
        "sub": " ".join(sentence.split()[4:10]).strip(".!؟?،:؛ ") if len(sentence.split()) > 4 else "",
        "hero_icon": picked[0] if picked else "icons/monument/monument.svg",
        "center_label": "محور الحدث",
        "camera": "push-in",
    }'''

if old_fallback_end in content:
    content = content.replace(old_fallback_end, new_fallback_end, 1)

# 5. Update DIRECTOR prompt docs
old_prompt_kinds = 'أنواع المقاطع (kind) وحقولها:\n'
new_prompt_kinds = '''أنواع المقاطع (kind) وحقولها:

- "icon_scene": تكوين سينمائي ثلاثي الأبعاد مستوحى من الطراز الذهبي (أيقونة بطل كبيرة، نصوص عربية عريضة متوهجة، 2-4 أيقونات فرعية طافية حولها مع أسهم رابطة متحركة، وشرارات نارية). استعمله كمشهد إيضاحي متكامل غني بالرموز بدلاً من البطاقات المسطحة:
  {"kind":"icon_scene","title":"لماذا تغيرت عاصمة مصر؟","hero_icon":"icons/building/mosque.svg","center_label":"القاهرة","badges":[{"icon":"icons/history/pyramid.svg","label":"منف"},{"icon":"icons/monument/lighthouse.svg","label":"الإسكندرية"}],"camera":"push-in"}

- "map_pin": خريطة إقليمية مع دبابيس وأسماء مدن تسقط بالحركة النابضة وأسهم متصلة:
  {"kind":"map_pin","title":"مسار انتقال العواصم","region":"egypt","points":[{"name":"القاهرة","x":540,"y":780},{"name":"الإسكندرية","x":420,"y":560}]}

- "timeline_card": خط زمني عربي أفقي/عمودي مرسوم بانسيابية متحركة مع بطاقات محطات تاريخية وأيقونات:
  {"kind":"timeline_card","title":"تطور العواصم عبر الزمن","items":[{"year":"٦٤١ م","label":"تأسيس الفسطاط","icon":"icons/history/castle.svg"},{"year":"٩٦٩ م","label":"بناء القاهرة","icon":"icons/building/mosque.svg"}]}

- "stat_ring_v2": حلقة إحصائية محسّنة ثلاثية الأبعاد تحتوي أيقونة بطل في مركزها والرقم يتصاعد بتوهج ذهبي:
  {"kind":"stat_ring_v2","number":"1,000","label":"عام من التاريخ","icon":"icons/time/hourglass.svg"}

فئات الأيقونات المتاحة للاختيار:
[history, monument, map, person, science, number, arrow, fire, star, building, chart, time, world, book, sword, crown, coin, ship, tree]
فضل دائماً استخدام icon_scene أو map_pin أو stat_ring_v2 أو timeline_card على النصوص المجردة (bigtext).

'''

if old_prompt_kinds in content:
    content = content.replace(old_prompt_kinds, new_prompt_kinds, 1)

TARGET.write_text(content, encoding="utf-8")
print("pipeline/direct.py updated successfully!")

