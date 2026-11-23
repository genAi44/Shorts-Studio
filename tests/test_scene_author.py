"""Scene authoring gate: static check (AST allowlist + tsc), retries, fallback, cache, files."""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("NO_NETWORK", "1")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import scene_author as sa  # noqa: E402
from pipeline.config import clear_warnings, get_last_warnings  # noqa: E402
from pipeline.style import normalize as norm_style  # noqa: E402

GOOD = """import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, ArText, Card, LAYOUT, useSpr, enter, SceneProps} from '../kit';

export default function Scene({dur, data}: SceneProps) {
  const p = useSpr(0.1, 'snappy');
  return (
    <AbsoluteFill>
      <Abs x={90} y={LAYOUT.beat.top + 40} w={900} style={enter(p, 'rise', 60)}>
        <Card style={{padding: 30}}><ArText size={56}>{String(data.sentence)}</ArText></Card>
      </Abs>
    </AbsoluteFill>
  );
}
"""
BAD = GOOD.replace("import React from 'react';", "import React, {useState} from 'react';\nimport fs from 'fs';").replace(
    "const p = useSpr", "const [n] = useState(0); fetch('https://evil.example.com'); const t = Date.now() + Math.random(); const p = useSpr")


def _check(tmp_path, code):
    f = tmp_path / "s_test.tsx"
    f.write_text(code, encoding="utf-8")
    return sa.static_check(f)


def test_static_gate_accepts_a_kit_scene(tmp_path):
    assert _check(tmp_path, GOOD) == []


def test_static_gate_rejects_network_fs_state_time_and_urls(tmp_path):
    errs = " | ".join(_check(tmp_path, BAD))
    for needle in ("'fs' is not allowed", "useState", "'fetch'", "Date", "Math.random", "external URL"):
        assert needle in errs, (needle, errs)


def test_static_gate_catches_type_errors_and_missing_default(tmp_path):
    errs = _check(tmp_path, GOOD.replace("LAYOUT.beat.top", "LAYOUT.beat.center_x"))
    assert any("center_x" in e for e in errs)
    errs = _check(tmp_path, GOOD.replace("export default function Scene", "export function Scene"))
    assert any("export default" in e for e in errs)


def test_extract_code_drops_reasoning_fences_and_duplicate_copies():
    one = "We need code.\nimport React from 'react';\nexport default function S(){return null}\n"
    assert sa.extract_code(one).startswith("import React")
    dup = ("import React from 'react';\nconst x = 1;\n" + "\n".join(f"// c{i}" for i in range(15))
           + "\nimport React from 'react';\nexport default function S(){return null}\n")
    assert sa.extract_code(dup).count("import React") == 1
    assert sa.extract_code("```tsx\nimport React from 'react';\nexport default 1\n```\nthanks").strip().endswith("export default 1")


def test_hints_follow_the_error_kind():
    h = sa.hints_for(["text touches/overflows the canvas edge: x", "Arabic text not right-to-left (use ArText): y"])
    assert any("LAYOUT.cx" in x for x in h) and any("ArText" in x for x in h)


def _spec(sentence="القاهرة عاصمة مصر"):
    words = [{"t": w, "s": 0.1 + i * 0.4, "e": 0.4 + i * 0.4} for i, w in enumerate(sentence.split())]
    return {"style": norm_style({"seed": 806}), "scenes": [{"id": "a", "role": "body", "dur": 90, "words": words, "beats": [{"kind": "bigtext"}],
                                                          "entity_plan": [], "map_overlay": None}]}


def _patch(monkeypatch, tmp_path):
    monkeypatch.setattr(sa, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(sa, "sandbox_render", lambda items, style, wd: {n: [] for n in items})  # render gate is exercised by the smoke test


def test_retry_then_accept_cache_and_files(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path)
    calls = []

    def llm(system, user):
        calls.append(user)
        return BAD if len(calls) == 1 else GOOD

    clear_warnings()
    spec = sa.author_spec(_spec(), str(tmp_path / "job"), llm=llm, log=lambda m: None)
    assert spec["scenes"][0]["beats"][0]["kind"] == "authored" and len(calls) == 2
    assert "REJECTED" in calls[1] and "fs" in calls[1]                       # the errors went back to the model
    assert any((tmp_path / "job" / "scenes").glob("s_*.tsx"))                # kept as a file in the job folder
    assert not get_last_warnings()
    # same content again: served from the cache, the model is not called
    calls.clear()
    spec2 = sa.author_spec(_spec(), str(tmp_path / "job2"), llm=llm, log=lambda m: None)
    assert spec2["scenes"][0]["beats"][0]["kind"] == "authored" and calls == []
    rep = json.loads((tmp_path / "job2" / "authoring_report.json").read_text(encoding="utf-8"))
    assert rep["scenes"]["a"]["status"] == "cache"


def test_exhausted_retries_fall_back_visibly(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path)
    clear_warnings()
    spec = sa.author_spec(_spec(), str(tmp_path / "job"), llm=lambda s, u: BAD, log=lambda m: None)
    assert spec["scenes"][0]["beats"] == [{"kind": "bigtext"}]                # built-in beats kept
    assert any("rejected after 3 attempt" in w for w in get_last_warnings())  # 1 try + MAX_RETRIES (2)
    assert not list((tmp_path / "job" / "scenes").glob("s_*.tsx"))            # a rejected file never stays


def test_render_gate_failures_are_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(sa, "CACHE_DIR", tmp_path / "cache")
    seen = []

    def gate(items, style, wd):
        seen.append(1)
        return {n: (["text touches/overflows the canvas edge: 'x'"] if len(seen) == 1 else []) for n in items}

    monkeypatch.setattr(sa, "sandbox_render", gate)
    users = []
    spec = sa.author_spec(_spec(), str(tmp_path / "job"), llm=lambda s, u: (users.append(u), GOOD)[1], log=lambda m: None)
    assert spec["scenes"][0]["beats"][0]["kind"] == "authored" and len(users) == 2 and "LAYOUT.cx" in users[1]


def test_content_hash_changes_with_the_sentence_and_theme():
    from pipeline.style import theme_from_style
    th = theme_from_style(norm_style({"seed": 806}))
    a = sa.scene_context(_spec()["scenes"][0], th)
    b = sa.scene_context(_spec("جملة أخرى تماما")["scenes"][0], th)
    c = sa.scene_context(_spec()["scenes"][0], theme_from_style(norm_style({"seed": 11})))
    assert sa.content_hash(a) == sa.content_hash(sa.scene_context(_spec()["scenes"][0], th))
    assert len({sa.content_hash(a), sa.content_hash(b), sa.content_hash(c)}) == 3


def test_fixture_authored_files_pass_the_static_gate():
    d = ROOT / "tests" / "fixtures" / "authored"
    files = sorted(d.glob("s_*.tsx"))
    assert files, "build with scripts/build_authored_fixture.py"
    for f in files:
        assert sa.static_check(f) == [], f.name


def test_recipe_fixture_scenes_pass_the_static_gate():
    for f in sorted((ROOT / "tests" / "fixtures" / "recipes").glob("s_*.tsx")):
        assert sa.static_check(f) == [], f.name


def test_hints_cover_unknown_css_keys_and_prop_types():
    h = sa.hints_for(["line 57: TS2353 Object literal may only specify known properties, and 'justify' does not exist"])
    assert any("justifyContent" in x for x in h)
