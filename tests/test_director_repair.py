"""Director plan: a partial / bare-list reply is repaired by re-asking only the missing scenes."""
import json
import tempfile
from pathlib import Path

from pipeline import director_plan as dp


def _scene(sid, narr):
    w = narr.split()
    return {"scene_id": sid, "objective": "o", "main_concept": "c", "narrative_description": "d", "key_information": [narr],
            "relation_to_previous": "p", "relation_to_next": "n", "visual_storytelling": "v", "transition_trigger": w[-1], "continuity": "k"}


def test_partial_list_reply_is_completed():
    spec = {"scenes": [{"id": s, "role": "body", "words": [{"t": "كلمة"}, {"t": s}]} for s in ("a", "b", "c")]}
    calls = []

    def llm(system, user):
        calls.append(user)
        if len(calls) == 1:
            return [_scene("a", "كلمة a")]  # bare list, one scene only (a cut-off reply)
        asked = [i["scene_id"] for i in json.loads(user.split("\n\n")[0])["scenes"]]
        return {"plan": [_scene(s, f"كلمة {s}") for s in asked]}

    out = dp.plan_video(spec, Path(tempfile.mkdtemp()), llm=llm, log=lambda m: None)
    assert list(out) == ["a", "b", "c"]
    assert all(out[s]["main_concept"] == "c" for s in out), "no scene fell back to the deterministic plan"
    assert len(calls) == 2 and '"a"' not in calls[1].split("\n\n")[0]
