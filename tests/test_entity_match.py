"""Flag/number-vs-photo matching guards."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.direct import _number_in_text
from pipeline.visual_tools import enrich_scene_visuals  # noqa: F401  (import guard)
from geodb_marker import needs_geodb


def test_number_must_appear_in_narration():
    assert _number_in_text("2,147,109", "عدد ٢٬١٤٧٬١٠٩ نسمة")
    assert _number_in_text("1,379,000", "ميلانو بـ 1379000")
    assert not _number_in_text("2,147,109", "ميلانو بـ 1,379,000")
    assert not _number_in_text("", "أي نص")


def test_multi_country_scene_gets_no_flag():
    sc = {"narration": "", "on_screen": "", "visual": {"countries": ["اليابان", "الصين"]}}
    assert [v for v in enrich_scene_visuals(sc) if v["kind"] == "flag"] == []
    one = {"narration": "", "on_screen": "", "visual": {"countries": ["اليابان"]}}
    assert [v for v in enrich_scene_visuals(one) if v["kind"] == "flag"]


@needs_geodb
def test_geo_mentions_arabic_ambiguity_and_regions():
    from pipeline.geo_overlay import extract_timed_geo_mentions as ex
    names = lambda t: [m["name_ar"] for m in ex(t, "", [], 150)]
    assert "مالي" not in names("المنامة تبرز كمركز مالي ومصرفي")
    assert "مالي" in names("عاصمة جمهورية مالي هي باماكو")
    assert "مدينة الكويت" in names("وتليها مدينة الكويت عاصمة دولة الكويت")
    assert "العالم العربي" in names("بعض العواصم العربية تتجاوز ثروتها")
    assert "دول الخليج" in names("ما هي العواصم الخليجية الأخرى")


def test_photo_start_moves_to_entity_word():
    from pipeline import direct, rem
    n = "الرياض عاصمة السعودية تبرز كثيرا. الأغنى عالمياً وتتميز أبوظبي عاصمة الإمارات."
    groups = direct.sentence_groups(n)
    ntok = sum(len(g) for g in groups)
    toks = n.split()[:ntok]
    words = [{"t": t, "s": j * 0.42, "e": j * 0.42 + 0.38} for j, t in enumerate(toks)]
    sents = direct.sentences(n)
    beats = [{"kind": "map"}, {"kind": "photo"}]
    starts = [0, int(round(words[groups[1][0]]["s"] * 30)) - 3]
    first = starts[1]
    rem._align_photo_starts(beats, starts, groups, sents, words, ntok)
    assert starts[1] > first  # photo now waits for «أبوظبي»
    assert starts[0] == 0
