"""Test script for TSX scene generator."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def test_gen():
    from pipeline.storyteller import classify_narration_intent
    from pipeline.geo import detect_city_in_text, get_geo
    from pipeline.rem import map_view

    t = "تعد طوكيو أكبر مدينة في العالم بأكثر من 37 مليون نسمة."
    intent = classify_narration_intent(t)
    print("Intent:", intent["primary_intent"], intent["visual_approach"])
    city_name, city_info = detect_city_in_text(t)
    print("City:", city_name, city_info["iso"] if city_info else None)
    if city_info:
        g = get_geo()
        mv = map_view(g, {
            "countries": [city_info["iso"]],
            "highlight": [city_info["iso"]],
            "points": [{"name": city_name, "lat": city_info["lat"], "lon": city_info["lon"]}],
        })
        print("Map view keys:", mv.keys())
        print("HL len:", len(mv["hl"]), "PTS:", mv["pts"])

if __name__ == "__main__":
    test_gen()
