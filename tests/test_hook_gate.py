"""Part 5: the hook is composed from frame 0, one hero + a 2-4 word title, max 3 elements (checked on the real render)."""
from pipeline.scene_author import SYSTEM, hook_problems

HERO = {"box": [190, 500, 890, 1200], "opacity": 1}


def test_a_good_hook_passes():
    assert hook_problems({"texts": 1, "hero": HERO, "strings": ["سفينة تصعد جبلاً"]}, 0, False) == []
    assert hook_problems({"texts": 3, "hero": HERO, "strings": ["سفينة تصعد", "٢٦ متراً", "بنما"]}, 1, False) == []


def test_empty_first_frame_and_missing_hero_fail():
    errs = hook_problems({"texts": 0, "hero": {}}, 0, True)
    assert any("first frame is empty" in e for e in errs) and any("hero is not visible" in e for e in errs)


def test_too_many_or_too_long_texts_fail():
    errs = hook_problems({"texts": 4, "hero": HERO, "strings": ["هذه جملة طويلة جداً لا تصلح للخطاف أبداً"]}, 1, False)
    assert any("4 texts" in e for e in errs) and any("too long" in e for e in errs)


def test_designer_prompt_has_the_hook_rules():
    assert 'HOOK (data.role == "hook")' in SYSTEM and "Frame 0 is already the full composition" in SYSTEM
