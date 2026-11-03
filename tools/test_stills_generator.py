import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import geo, style, rem, config

def generate_all():
    g = geo.get_geo()
    pub = ROOT / "outputs" / "test_stills" / "public"
    os.makedirs(pub / "fonts", exist_ok=True)
    for f in (ROOT / "data").glob("*.ttf"):
        shutil.copy(f, pub / "fonts")
    shutil.copy(ROOT / "remotion" / "public" / "grain.png", pub)
    
    # Copy a cached jpeg as sample_photo.jpg
    cached_jpegs = list((ROOT / "cache").glob("*.bin"))
    if cached_jpegs:
        shutil.copy(cached_jpegs[0], pub / "sample_photo.jpg")

    # Define all 13 beat types with rich, realistic content
    beats_templates = [
        # 1. map
        {
            "kind": "map",
            "title": "موقع بوليفيا في القارة",
            "countries": ["BOL"],
            "highlight": ["BOL"],
            "points": [{"name": "لاباز", "lat": -16.5, "lon": -68.15, "dot": True}]
        },
        # 2. stat
        {
            "kind": "stat",
            "title": "مؤشر الارتفاع القياسي",
            "number": "3,640",
            "label": "متر فوق مستوى سطح البحر",
            "layout": "ring"
        },
        # 3. bigtext
        {
            "kind": "bigtext",
            "title": "السؤال المحوري",
            "text": "لماذا دولتان بعاصمتين؟",
            "sub": "أسرار التاريخ والجغرافيا"
        },
        # 4. bars
        {
            "kind": "bars",
            "title": "مقارنة الارتفاعات الجبلية",
            "items": [
                {"label": "لاباز", "value": 3640, "display": "3640م"},
                {"label": "سوكري", "value": 2810, "display": "2810م"},
                {"label": "القدس", "value": 754, "display": "754م"}
            ]
        },
        # 5. timeline
        {
            "kind": "timeline",
            "title": "محطات الصراع السياسي",
            "items": [
                {"year": "1825", "label": "تأسيس سوكري عاصمة"},
                {"year": "1899", "label": "اندلاع الحرب ونقل الإدارة"},
                {"year": "2009", "label": "اعتماد الدستور الجديد"}
            ]
        },
        # 6. versus
        {
            "kind": "versus",
            "title": "مقارنة العاصمتين",
            "left": {"title": "سوكري", "value": "دستورية", "sub": "المحكمة العليا", "icon": "scale"},
            "right": {"title": "لاباز", "value": "تنفيذية", "sub": "مقر الحكومة", "icon": "building"}
        },
        # 7. list (Testing the new list beat with fixed row heights and spacing)
        {
            "kind": "list",
            "title": "أسباب بقاء التقسيم",
            "items": [
                {"text": "حسم الحرب الأهلية لصالح الشمال", "icon": "shield"},
                {"text": "النمو الاقتصادي السريع في لاباز", "icon": "coin"},
                {"text": "تسوية تحفظ مكانة سوكري التاريخية", "icon": "scale"}
            ]
        },
        # 8. icons
        {
            "kind": "icons",
            "title": "ركائز الدولة البوليفية",
            "items": [
                {"icon": "mountain", "label": "الجبال"},
                {"icon": "building", "label": "الحكومة"},
                {"icon": "coin", "label": "الثروة"},
                {"icon": "people", "label": "الشعب"}
            ]
        },
        # 9. canvas
        {
            "kind": "canvas",
            "title": "رمزية السيادة الوطنية",
            "elements": [
                {"type": "icon", "name": "flag", "x": 540, "y": 700, "size": 220, "color": "accent", "enter": "pop"},
                {"type": "text", "text": "دولة واحدة بعاصمتين", "x": 540, "y": 1000, "size": 68, "color": "text", "enter": "rise"},
                {"type": "shape", "shape": "ring", "x": 540, "y": 700, "size": 280, "color": "accent2", "enter": "pop"}
            ]
        },
        # 10. photo
        {
            "kind": "photo",
            "title": "قصر الحكومة التاريخي",
            "src": "sample_photo.jpg",
            "credit": "Wikimedia Commons",
            "camera": "push-in"
        },
        # 11. split
        {
            "kind": "split",
            "title": "توزيع الاختصاصات",
            "left": {"title": "القضاء الدستوري", "value": "سوكري", "sub": "المقر التاريخي", "icon": "book"},
            "right": {"title": "السلطة التنفيذية", "value": "لاباز", "sub": "مقر الرئاسة", "icon": "crown"}
        },
        # 12. ticker
        {
            "kind": "ticker",
            "title": "بيانات جغرافية حاسمة",
            "items": [
                {"text": "لاباز أعلى مقر حكومي في العالم", "icon": "mountain"},
                {"text": "سوكري العاصمة الدستورية منذ 1825", "icon": "home"},
                {"text": "عدد السكان يتجاوز 12 مليون نسمة", "icon": "people"}
            ]
        },
        # 13. cardstack
        {
            "kind": "cardstack",
            "title": "المحطات الرئيسية",
            "items": [
                {"text": "استقلال بوليفيا عام 1825", "value": "1825", "icon": "scale"},
                {"text": "نقل البرلمان إلى لاباز", "value": "1899", "icon": "building"},
                {"text": "إقرار الدستور التعددي", "value": "2009", "icon": "book"}
            ]
        }
    ]

    styles = [
        ("default", style.normalize({})),
        ("sunset", style.random_style(101, mood="غروب")),
        ("ocean", style.random_style(202, mood="محيط")),
    ]

    BEAT_DUR = 90  # 3 seconds per beat
    frames_to_render = [i * BEAT_DUR + 45 for i in range(len(beats_templates))]
    frames_arg = ",".join(str(f) for f in frames_to_render)
    
    kinds = [b["kind"] for b in beats_templates]

    for style_name, st in styles:
        work_dir = ROOT / "outputs" / "test_stills" / f"work_{style_name}"
        os.makedirs(work_dir, exist_ok=True)
        
        scenes = []
        for i, b in enumerate(beats_templates):
            beat = copy.deepcopy(b)
            if beat["kind"] == "map":
                beat["view"] = rem.map_view(g, beat)
            beat["from"] = 0
            beat["dur"] = BEAT_DUR
            
            # Words for captions
            words = [
                {"t": w, "s": round(0.1 + j * 0.4, 2), "e": round(0.4 + j * 0.4, 2)}
                for j, w in enumerate(beat.get("title", "مشهد تجريبي").split())
            ]
            
            scenes.append({
                "id": f"sc_{i}",
                "role": "body" if i > 0 else "hook",
                "from": i * BEAT_DUR,
                "dur": BEAT_DUR,
                "words": words,
                "beats": [beat]
            })
            
        spec = {
            "fps": config.FPS,
            "width": 1080,
            "height": 1920,
            "total": len(beats_templates) * BEAT_DUR,
            "audio": "audio.wav",
            "style": st,
            "scenes": scenes
        }
        
        spec_path = work_dir / "spec.json"
        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)

        out_pattern = str(ROOT / "outputs" / "test_stills" / f"{style_name}_%d.jpg")
        cmd = ["node", "still.mjs", str(spec_path), out_pattern, frames_arg, str(pub)]
        print(f"Rendering stills for style: {style_name}...")
        proc = subprocess.run(cmd, cwd=str(ROOT / "remotion"), capture_output=True, text=True, encoding="utf-8")
        if proc.returncode != 0:
            print(f"Error rendering {style_name}: {proc.stderr}")
        else:
            print(f"Success rendering {style_name}")
            # Rename rendered files to meaningful names: {style_name}_{kind}.jpg
            for i, kind in enumerate(kinds):
                src = ROOT / "outputs" / "test_stills" / f"{style_name}_{frames_to_render[i]}.jpg"
                dst = ROOT / "outputs" / "test_stills" / f"{style_name}_{kind}.jpg"
                if src.exists():
                    if dst.exists():
                        dst.unlink()
                    src.rename(dst)
                    print(f"  -> Generated: {dst.name}")

if __name__ == "__main__":
    generate_all()
