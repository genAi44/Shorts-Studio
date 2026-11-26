"""Models think in English, the video stays Arabic: prompts carry the contract, narration and timings are never touched."""
import json
import re

from pipeline import director_plan as dp
from pipeline import scene_author as sa
from pipeline import visual_intelligence as vi

AR = re.compile(r"[\u0600-\u06FF]")
NARR = "دمشق عاصمة سوريا منذ آلاف السنين"


def test_prompts_are_english_and_carry_the_contract():
    for name, text in (("director", dp.DIRECTOR_SYSTEM), ("designer", sa.SYSTEM), ("visual_intelligence", vi._vi_system())):
        assert not AR.search(text), f"{name} prompt contains Arabic"
        assert "LANGUAGE CONTRACT" in text.replace("{contract}", "LANGUAGE CONTRACT"), name
    assert "{contract}" not in vi._vi_system() and "LANGUAGE CONTRACT" in dp.DIRECTOR_SYSTEM
    assert "LANGUAGE CONTRACT" in sa.build_prompts({"id": "a", "role": "body", "dur": 90, "sentence": NARR, "sentences": [NARR], "entities": [],
                                                    "words": [], "map_overlay": None, "theme": {}})[0]


def _plan(trigger):
    return {"scenes": [{"scene_id": "s1", "objective": "hook the viewer", "main_concept": "oldest capital", "narrative_description": "Damascus is introduced.",
                        "key_information": ["Damascus has been a capital for thousands of years"], "relation_to_previous": "", "relation_to_next": "zoom out",
                        "visual_storytelling": "map journey", "transition_trigger": trigger, "continuity": "same gold accent"}]}


def test_english_plan_is_accepted_but_the_trigger_must_still_be_arabic_narration():
    items = [{"scene_id": "s1", "role": "hook", "narration": NARR}]
    assert dp.plan_errors(_plan("سوريا"), items) == []
    assert any("transition_trigger" in e for e in dp.plan_errors(_plan("Syria"), items))


def test_designer_gets_english_names_first_and_the_arabic_words_untouched():
    words = [{"t": "دمشق", "s": 0.1, "e": 0.5}, {"t": "عاصمة", "s": 0.6, "e": 1.0}]
    scene = {"id": "s1", "role": "body", "dur": 90, "words": words,
             "entity_plan": [[{"type": "place", "text": "دمشق", "name_ar": "دمشق", "name_en": "Damascus", "country_en": "Syria", "lat": 33.5, "lon": 36.3}]],
             "map_overlay": {"waypoints": [{"name_ar": "دمشق", "name_en": "Damascus"}], "features": []}}
    ctx = sa.scene_context(scene, {})
    assert ctx["sentence"] == "دمشق عاصمة" and [w["t"] for w in ctx["words"]] == ["دمشق", "عاصمة"]
    ent = ctx["entities"][0]
    assert list(ent).index("name_en") < list(ent).index("name_ar") and ent["country_en"] == "Syria"
    user = sa.build_prompts(ctx)[1]
    assert json.loads(user[user.index("{"):user.index("\n\nScene length")])["map_places"] == [{"name_en": "Damascus", "name_ar": "دمشق"}]


def test_beat_director_prompt_is_english_and_keeps_arabic_on_screen_rules():
    from pipeline import direct
    for photos in (True, False):
        text = direct.director_system(photos)
        assert not AR.search(text) and "LANGUAGE CONTRACT" in text
    full = direct.director_system(True)
    assert "ARABIC headline" in full and "short ARABIC phrase" in full      # on-screen text stays Arabic
    assert 'English only' in full                                            # photo queries stay English


def test_style_guides_given_to_the_models_are_english():
    from pipeline import presets
    slugs = [p["slug"] for p in presets.list_presets()]
    assert slugs
    for slug in slugs:
        g = presets.guide(slug)
        assert g and not AR.search(g), f"styles/{slug}/STYLE.md contains Arabic"


def test_style_script_and_factcheck_prompts_are_english_but_the_script_stays_arabic():
    from pipeline import scriptspec as sp
    from pipeline import style as stl
    assert not AR.search(stl.ART_SYSTEM) and not AR.search(stl.art_prompt({"title": "t"}, ["a"]).split("\n", 1)[0])
    assert not AR.search(sp.FACT_SYSTEM) and not AR.search(sp.user_prompt("idea", "note"))
    head, example = sp.SYSTEM.split('{\n  "title"', 1)
    assert len(AR.findall(head)) < 150 and len(AR.findall(example)) > 500   # instructions are English; Arabic is only inline examples and the few-shot JSON
    # the rules survived the translation: the eight parts, the word budgets and the Arabic output requirement
    for needle in ("HOOK", "OPEN LOOP 2", "CTA", "between 100 and 150 words", "ARABIC", "10 to 18 words"):
        assert needle in head, needle
    assert json.loads('{"title"' + example[:example.rindex("}") + 1])["hook"]["narration"]   # the example is still valid JSON
