"""Director -> Designer -> SVG gate, inside the existing authoring stage. Offline (fake LLMs); the render half of the SVG gate is
covered by test_hero_svg_real_render (needs node + remotion/node_modules, skipped otherwise)."""
import copy
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

os.environ.setdefault("NO_NETWORK", "1")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import director_plan as dp  # noqa: E402
from pipeline import scene_author as sa  # noqa: E402
from pipeline import visual_qa  # noqa: E402
from pipeline.config import clear_warnings, get_last_warnings  # noqa: E402
from pipeline.visual_qa import svg_problems  # noqa: E402
sys.path.insert(0, str(ROOT / "tests"))
from test_scene_author import GOOD, STORYBOARD, SVG, _spec, director, reply  # noqa: E402


def _two_scene_spec():
    spec = _spec()
    b = copy.deepcopy(spec["scenes"][0])
    b["id"] = "b"
    b["words"] = [{"t": w, "s": 0.2 + i * 0.5, "e": 0.6 + i * 0.5} for i, w in enumerate("ويعبرها نهر النيل من الجنوب".split())]
    spec["scenes"].append(b)
    return spec


# ------------------------------------------------------------------ director

def test_director_plan_is_structured_and_independent(tmp_path):
    calls = []

    def llm(system, user):
        calls.append((system, user))
        plan = director(system, user)
        plan["scenes"][0]["extra"] = "dropped"  # keys outside the contract never reach the designer
        plan["scenes"][0]["transition_trigger"] = "مصر"
        return plan

    spec = _two_scene_spec()
    plans = dp.plan_video(spec, tmp_path, llm=llm, log=lambda m: None)
    assert len(calls) == 1                                                   # one call for the whole video
    assert calls[0][0] == dp.DIRECTOR_SYSTEM and dp.DIRECTOR_SYSTEM != sa.SYSTEM
    assert "عاصمة" in json.loads(calls[0][1])["scenes"][0]["narration"]      # text only reaches the director
    assert '"s"' not in calls[0][1] and '"e"' not in calls[0][1]             # no timings in its input
    assert list(plans) == ["a", "b"]
    for p in plans.values():
        assert set(p) == set(dp.PLAN_FIELDS) | {"narration"}
    assert plans["a"]["narration"] == "القاهرة عاصمة مصر"                    # system-owned narration
    # cached: same narration -> no second call
    dp.plan_video(spec, tmp_path, llm=llm, log=lambda m: None)
    assert len(calls) == 1


def test_director_timings_are_rejected_then_repaired(tmp_path):
    calls = []

    def llm(system, user):
        calls.append(user)
        plan = director(system, user)
        if len(calls) == 1:
            plan["scenes"][0]["start"] = 0.4
            plan["scenes"][1]["transition_trigger"] = "كلمة غير موجودة"
        return plan

    plans = dp.plan_video(_two_scene_spec(), tmp_path, llm=llm, log=lambda m: None)
    assert len(calls) == 2 and "REJECTED" in calls[1] and "timing data is forbidden" in calls[1] and "transition_trigger" in calls[1]
    assert "start" not in plans["a"]


def test_director_failure_falls_back_visibly_and_never_raises(tmp_path):
    clear_warnings()

    def boom(system, user):
        raise RuntimeError("provider down")

    plans = dp.plan_video(_two_scene_spec(), tmp_path, llm=boom, log=lambda m: None)
    assert set(plans) == {"a", "b"} and all(p["objective"] for p in plans.values())
    assert any("director plan llm call failed" in w for w in get_last_warnings())
    assert not list(tmp_path.glob("plan_*.json"))                          # a fallback is never cached

    clear_warnings()
    plans = dp.plan_video(_two_scene_spec(), tmp_path, llm=lambda s, u: {"scenes": [{"scene_id": "a", "end": 3}]}, log=lambda m: None)
    assert plans["a"]["objective"] and "end" not in plans["a"]                # timings void the whole plan
    assert any("deterministic plan" in w for w in get_last_warnings())


def test_plan_errors_contract():
    items = dp.scene_items(_two_scene_spec())
    assert dp.plan_errors(director("", json.dumps({"scenes": items})), items) == []
    assert dp.plan_errors({"nope": 1}, items)
    bad = director("", json.dumps({"scenes": items}))
    bad["scenes"].reverse()
    assert any("in this order" in e for e in dp.plan_errors(bad, items))
    bad = director("", json.dumps({"scenes": items}))
    bad["scenes"][0]["key_information"] = []
    bad["scenes"][1]["code"] = "<svg/>"
    errs = dp.plan_errors(bad, items)
    assert any("key_information" in e for e in errs) and any("must not produce SVG or code" in e for e in errs)


def test_find_word_handles_clitics_and_diacritics():
    words = "وَالقاهرةُ عاصمة مصر، وبرلين".split()
    assert dp.find_word(words, "القاهرة") == 0
    assert dp.find_word(words, "برلين") == 3
    assert dp.find_word(words, "عاصمة مصر") == 1
    assert dp.find_word(words, "باريس") is None
    assert dp.find_word(words, "القاهرة", start=1) is None


# ------------------------------------------------------------------ designer

def _patch(monkeypatch, tmp_path, render=None):
    monkeypatch.setattr(sa, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(dp, "llm_plan", director)
    monkeypatch.setattr(sa, "sandbox_render", render or (lambda items, style, wd: {n: [] for n in items}))


def test_designer_receives_the_plan_and_produces_storyboard_svg_and_states(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path)
    users = []
    spec = _spec()
    words_before = copy.deepcopy(spec["scenes"][0]["words"])
    out = sa.author_spec(spec, str(tmp_path / "job"), llm=lambda s, u: (users.append((s, u)), reply())[1], log=lambda m: None)
    system, user = users[0]
    assert "<storyboard>" in system and "<hero_svg>" in system and "TIMING IS READ-ONLY" in system
    assert '"director_plan"' in user and "prove the sentence" in user               # the director's plan is the designer's input
    beat = out["scenes"][0]["beats"][0]
    assert beat["kind"] == "authored"
    data = beat["data"]
    assert set(sa.STORYBOARD_FIELDS) <= set(data["storyboard"]) and len(sa.STORYBOARD_FIELDS) == 13
    assert data["hero_svg"] == SVG and svg_problems(data["hero_svg"]) == []
    # state 2 is triggered by "عاصمة" (word 1, s = 0.5 s): the frame comes from the EXISTING timing, minus the lead
    assert data["hero_states"] == [{"state": 1, "from": 0, "word": ""}, {"state": 2, "from": 15 - sa.STATE_LEAD_FRAMES, "word": "عاصمة"}]
    assert out["scenes"][0]["words"] == words_before and data["words"][1]["s"] == 0.5   # timings untouched
    job = tmp_path / "job"
    assert json.loads((job / "director_plan.json").read_text(encoding="utf-8"))["a"]["objective"] == "prove the sentence"
    saved = json.loads(next((job / "scenes").glob("s_*.json")).read_text(encoding="utf-8"))
    assert saved["svg"] == SVG and saved["storyboard"]["hero_element"] == "city"
    assert visual_qa._audit_scene(out["scenes"][0])["passed"]                   # existing QA + SVG gate accept it


@pytest.mark.parametrize("svg,needle", [
    (None, "no SVG"), ("", "empty string"),
    ('<svg viewBox="0 0 10 10"><rect width="5"', "not well-formed"),
    ('<div><rect width="5" height="5"/></div>', "not <svg>"),
    ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>', "draws only 0"),
    ('<svg viewBox="0 0 10 10"><defs><circle r="3"/><circle r="3"/><circle r="3"/></defs></svg>', "draws only 0"),
    ('<svg viewBox="0 0 10 10"><g opacity="0"><circle r="3"/><circle r="3"/><circle r="3"/></g></svg>', "draws only 0"),
    ('<svg viewBox="0 0 10 10"><g style="display:none"><circle r="3"/><circle r="3"/><circle r="3"/></g></svg>', "draws only 0"),
    ('<svg viewBox="0 0 10 10" fill="none"><circle r="3"/><circle r="3"/><circle r="3"/></svg>', "draws only 0"),
    ('<svg viewBox="0 0 10 10"><rect width="0" height="4"/><circle r="0"/><path d="M0 0"/><line x1="1" y1="1" x2="1" y2="1" stroke="red"/></svg>', "draws only 0"),
    ('<svg viewBox="0 0 10 10"><line x1="0" y1="0" x2="9" y2="9"/><line x1="0" y1="9" x2="9" y2="0"/><polyline points="0 0 5 5"/></svg>', "draws only 0"),
    ('<svg viewBox="0 0 10 10"><text>القاهرة</text></svg>', "text alone is not a graphic"),
    ('<svg><rect width="5" height="5"/><circle r="2"/><circle r="3"/></svg>', "viewBox"),
    ('<svg viewBox="0 0 10 10"><script>alert(1)</script><rect width="5" height="5"/><circle r="2"/><circle r="3"/></svg>', "<script> is forbidden"),
    ('<svg viewBox="0 0 10 10"><style>body{display:none}</style><rect width="5" height="5"/><circle r="2"/><circle r="3"/></svg>', "<style> is forbidden"),
    ('<svg viewBox="0 0 10 10" xmlns:xlink="http://www.w3.org/1999/xlink"><use xlink:href="http://x.y/a.svg#a"/><rect width="5" height="5"/><circle r="2"/><circle r="3"/></svg>', "external href"),
    ('<svg viewBox="0 0 10 10"><rect width="5" height="5" fill="url(https://x.y/p)"/><circle r="2"/><circle r="3"/></svg>', "external reference"),
    ('<svg viewBox="0 0 10 10"><rect width="5" height="5" onclick="x()"/><circle r="2"/><circle r="3"/></svg>', "event handler"),
    ('<svg viewBox="0 0 10 10"><circle r="2"><animate attributeName="r" to="5"/></circle><rect width="5" height="5"/><circle r="3"/></svg>', "<animate> is forbidden"),
    ('<!DOCTYPE svg [<!ENTITY a "x">]><svg viewBox="0 0 10 10"/>', "DOCTYPE"),
])
def test_svg_gate_rejects(svg, needle):
    probs = svg_problems(svg)
    assert probs and any(needle in p for p in probs), (needle, probs)


def test_svg_gate_accepts_real_graphics():
    assert svg_problems(SVG) == []
    ok = ('<svg viewBox="0 0 10 10"><defs><linearGradient id="g"><stop offset="0"/></linearGradient></defs>'
          '<path d="M0 0 L 9 9 L 0 9 Z" fill="url(#g)"/><line x1="0" y1="0" x2="9" y2="0" stroke="#000"/>'
          '<g style="fill:none;stroke:#f00;stroke-width:2"><circle cx="5" cy="5" r="3"/></g></svg>')
    assert svg_problems(ok) == []


@pytest.mark.parametrize("mutate,needle", [
    (lambda sb, svg: (sb.pop("layering"), svg)[1], "'layering' is missing"),
    (lambda sb, svg: (sb["visual_states"][1].update(trigger_word="باريس"), svg)[1], "trigger_word 'باريس'"),
    (lambda sb, svg: (sb["visual_states"][1].update(start=0.5), svg)[1], "timing data is forbidden"),
    (lambda sb, svg: svg.replace('data-state="2"', 'data-x="2"'), 'no <g data-state="2">'),
    (lambda sb, svg: svg.replace('id="nile"', 'id="river"'), "element 'nile' has layer 'svg'"),
    (lambda sb, svg: (sb.update(hero_element="ghost"), svg)[1], "hero_element 'ghost'"),
    (lambda sb, svg: (sb["visual_states"][0].update(elements=["ghost"]), svg)[1], "unknown elements"),
])
def test_storyboard_contract(mutate, needle):
    sb, svg = copy.deepcopy(STORYBOARD), SVG
    svg = mutate(sb, svg)
    ctx = sa.scene_context(_spec()["scenes"][0], {})
    errs = sa.storyboard_errors(sb, ctx, svg)
    assert any(needle in e for e in errs), (needle, errs)
    assert sa.storyboard_errors(copy.deepcopy(STORYBOARD), ctx, SVG) == []


def test_parse_reply_and_missing_parts():
    sb, svg, code = sa.parse_reply("thinking...\n" + reply())
    assert sb["hero_element"] == "city" and svg == SVG and code.startswith("import React")
    sb, svg, code = sa.parse_reply(GOOD)                                      # the old TSX-only reply
    assert sb is None and svg is None and code.startswith("import React")
    ctx = sa.scene_context(_spec()["scenes"][0], {})
    errs = sa.design_errors(sb, svg, code, ctx)
    assert any("no valid <storyboard>" in e for e in errs) and any("no SVG" in e for e in errs)
    sb, svg, code = sa.parse_reply(reply(tsx=GOOD.replace("<HeroSvg", "<Abs")))
    assert any("<HeroSvg" in e for e in sa.design_errors(sb, svg, code, ctx))


def test_scene_with_empty_or_invisible_svg_is_never_accepted(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path)
    clear_warnings()
    hidden = SVG.replace("<svg ", '<svg opacity="1" ').replace('<rect id="nile"', '<g opacity="0"><rect id="nile"').replace("</svg>", "</g></svg>")
    for i, bad_svg in enumerate(("", hidden)):
        users = []
        out = sa.author_spec(_spec(), str(tmp_path / f"job{i}"), llm=lambda s, u: (users.append(u), reply(svg=bad_svg))[1], log=lambda m: None)
        assert out["scenes"][0]["beats"] == [{"kind": "bigtext"}]            # built-in beats kept, the scene is not "done"
        assert len(users) == sa.MAX_RETRIES + 1 and ("empty string" in users[1] or "draws only" in users[1])
        assert not list((tmp_path / f"job{i}" / "scenes").glob("s_*.tsx"))
    assert sum("rejected after" in w for w in get_last_warnings()) == 2


def test_a_cached_scene_without_its_svg_is_not_reused(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path)
    calls = []
    sa.author_spec(_spec(), str(tmp_path / "job"), llm=lambda s, u: (calls.append(1), reply())[1], log=lambda m: None)
    for f in (tmp_path / "cache").glob("s_*.json"):
        f.unlink()                                                            # e.g. a v1 cache entry: TSX only
    sa.author_spec(_spec(), str(tmp_path / "job2"), llm=lambda s, u: (calls.append(1), reply())[1], log=lambda m: None)
    assert len(calls) == 2


def test_render_gate_reports_a_missing_or_empty_hero(tmp_path, monkeypatch):
    """The python side of the render check, fed with audit records like the ones layoutAudit.tsx writes."""
    class R:
        returncode, stderr, stdout = 0, "", ""

    hero = {"a": None, "b": {"box": [100, 300, 900, 860], "cover": 0.01, "painted": 1, "opacity": 1}}

    def run(cmd, **k):
        frames = [int(x) for x in cmd[4].split(",")]   # node still.mjs <spec> <out pattern> <frames> <public>
        for i, fr in enumerate(frames):
            img = Path(cmd[3].replace("%d", str(fr)))
            from PIL import Image, ImageDraw
            im = Image.new("RGB", (1080, 1920), "black")
            ImageDraw.Draw(im).rectangle([100, 300, 980, 1300], fill="white")
            im.save(img)
            name = "a" if i < 3 else "b"
            Path(str(img) + ".audit.json").write_text(json.dumps({"texts": 2, "bbox": [90, 280, 990, 1300], "issues": [], "hero": hero[name]}))
        return R()

    monkeypatch.setattr(sa.subprocess, "run", run)
    ctx = {"dur": 60, "words": [], "hero_svg": SVG}
    out = sa.sandbox_render({"a": {"ctx": ctx}, "b": {"ctx": ctx}}, {"seed": 1}, tmp_path)
    assert any("not rendered" in p for p in out["a"])
    assert any("draws almost nothing" in p for p in out["b"])


def test_sparse_check_counts_the_hero_svg(tmp_path, monkeypatch):
    """A short text block plus a big visible hero SVG is a full composition; the same text alone is still too sparse."""
    class R:
        returncode, stderr, stdout = 0, "", ""

    big = {"box": [100, 420, 980, 1150], "cover": 0.5, "painted": 6, "opacity": 1}
    hero = {"withhero": big, "nohero": None, "faded": {**big, "opacity": 0.1}}
    names = list(hero)

    def run(cmd, **k):
        for i, fr in enumerate(int(x) for x in cmd[4].split(",")):
            img = Path(cmd[3].replace("%d", str(fr)))
            from PIL import Image, ImageDraw
            im = Image.new("RGB", (1080, 1920), "black")
            ImageDraw.Draw(im).rectangle([100, 300, 980, 1300], fill="white")
            im.save(img)
            Path(str(img) + ".audit.json").write_text(json.dumps({"texts": 1, "bbox": [90, 300, 990, 400], "issues": [], "hero": hero[names[i // 3]]}))
        return R()

    monkeypatch.setattr(sa.subprocess, "run", run)
    out = sa.sandbox_render({n: {"ctx": {"dur": 60, "words": []}} for n in names}, {"seed": 1}, tmp_path)
    assert not any("too sparse" in p for p in out["withhero"]), out["withhero"]
    assert any("too sparse" in p for p in out["nohero"])
    assert any("too sparse" in p for p in out["faded"])


def test_existing_qa_reports_a_bad_authored_svg():
    sc = {"id": "a", "beats": [{"kind": "authored", "data": {"hero_svg": "<svg viewBox='0 0 1 1'></svg>"}}]}
    rep = visual_qa._audit_scene(sc)
    assert not rep["passed"] and any(i["type"] == "svg_invalid" for i in rep["issues"])
    sc["beats"][0]["data"]["hero_svg"] = SVG
    rep = visual_qa._audit_scene(sc)
    assert rep["passed"] and not any(i["type"] in ("svg_invalid", "text_only_scene") for i in rep["issues"])


def test_preview_cache_only_never_calls_an_llm(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path)

    def no_llm(*a):
        raise AssertionError("cache_only must not call a model")

    monkeypatch.setattr(dp, "llm_plan", no_llm)
    out = sa.author_spec(_spec(), str(tmp_path / "job"), llm=no_llm, cache_only=True, log=lambda m: None)
    assert out["scenes"][0]["beats"] == [{"kind": "bigtext"}]


@pytest.mark.skipif(not (ROOT / "remotion" / "node_modules").exists() or not shutil.which("node"), reason="needs node + remotion/node_modules")
def test_hero_svg_real_render(tmp_path):
    """The real composition renders the hero SVG in Chromium; the audit measures it (and an invisible SVG is caught)."""
    from pipeline.style import normalize as norm_style
    style = norm_style({"seed": 806})
    ctx = sa.scene_context(_spec()["scenes"][0], {})
    sb, svg, code = sa.parse_reply(reply())
    good = {**ctx, **sa._design_data({"storyboard": sb, "svg": svg}, ctx)}
    ghost = {**good, "hero_svg": SVG.replace("<svg ", '<svg style="opacity:0" ')}
    d = tmp_path / "scenes"
    d.mkdir()
    (d / "s_good.tsx").write_text(code, encoding="utf-8")
    (d / "s_ghost.tsx").write_text(code, encoding="utf-8")
    with sa.sync_to_remotion(str(d)):
        probs = sa.sandbox_render({"s_good": {"ctx": good}, "s_ghost": {"ctx": ghost}}, style, tmp_path / "chk")
    hero_probs = [p for p in probs["s_good"] if "hero SVG" in p]
    assert hero_probs == [], probs["s_good"]
    assert any("hero SVG" in p for p in probs["s_ghost"]), probs["s_ghost"]
