"""One director: the designer receives the beat director's decision and no second director re-plans the scenes."""
import tempfile
from pathlib import Path

from pipeline import director_plan
from pipeline.scene_author import director_decision, scene_context


def _spec():
    w = lambda txt: [{"t": t, "s": i * 0.3, "e": i * 0.3 + 0.25} for i, t in enumerate(txt.split())]
    return {"scenes": [
        {"id": "hook", "role": "hook", "dur": 120, "words": w("سفينة تصعد جبلاً من الماء"),
         "beats": [{"kind": "generative_canvas", "title": "سفينة تصعد", "concept": "A giant ship rising up a staircase of water", "camera": "push-in"}]},
        {"id": "lead", "role": "body", "dur": 150, "words": w("الأهوسة ترفع السفن ستة وعشرين متراً"),
         "beats": [{"kind": "photo", "img": "media/p1.jpg"}]},  # native photo scene: no concept
    ]}


def test_designer_context_carries_the_binding_decision():
    ctx = scene_context(_spec()["scenes"][0], {})
    assert ctx["director_decision"] == [{"kind": "generative_canvas", "title": "سفينة تصعد",
                                         "concept": "A giant ship rising up a staircase of water", "camera": "push-in"}]
    assert director_decision(_spec()["scenes"][1]) == []


def test_no_second_director_call_when_the_beat_director_decided():
    def boom(system, user):
        raise AssertionError("a second director must not be called")
    plans = director_plan.plan_video(_spec(), Path(tempfile.mkdtemp()), llm=boom, log=lambda m: None)
    assert plans["hook"]["visual_storytelling"] == "A giant ship rising up a staircase of water"
    assert plans["hook"]["main_concept"] == "سفينة تصعد"
    assert plans["lead"]["objective"]                      # undecided scene: deterministic plan, still complete
