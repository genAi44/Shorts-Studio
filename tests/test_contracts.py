"""Cross-language contracts: Python beats, the shared JSON schema and the Remotion renderer must agree."""
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LEGACY_RENDER_ONLY = {"chart", "typography", "visuals"}  # renderer + schema know them, the director never emits them


def _schema_kinds():
    return set(json.load(open(ROOT / "spec_schema.json", encoding="utf-8"))["beats"])


def _tsx_kinds():
    src = (ROOT / "remotion" / "src" / "beats.tsx").read_text(encoding="utf-8")
    return set(re.findall(r"case '(\w+)':", src[src.index("export const BeatView"):])) | {"bigtext"}  # bigtext = default


def test_every_director_kind_is_in_schema_and_renderer():
    from pipeline import direct
    py, sch, tsx = set(direct.KINDS), _schema_kinds() | {"bigtext"}, _tsx_kinds()
    assert py <= sch, f"director can emit kinds the schema does not know: {sorted(py - sch)}"
    assert py <= tsx, f"director can emit kinds the renderer does not draw: {sorted(py - tsx)}"
    assert (sch - {"bigtext"}) - LEGACY_RENDER_ONLY <= py, "schema kinds the director cannot emit"


def test_schema_ts_is_generated_not_hand_edited():
    spec = importlib.util.spec_from_file_location("gen_schema", ROOT / "scripts" / "generate_schema.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    committed = (ROOT / "remotion" / "src" / "schema.ts").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert mod.generate_schema_ts().replace("\r\n", "\n") == committed, "run: python scripts/generate_schema.py"


def test_layout_py_and_ts_match():
    import subprocess
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_layout.py")], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def test_every_director_kind_has_a_precondition_rule():
    from pipeline import direct
    assert set(direct.KINDS) <= set(direct.BEAT_RULES), sorted(set(direct.KINDS) - set(direct.BEAT_RULES))


def test_map_precondition_requires_a_real_place():
    from pipeline import direct
    from pipeline.geo import get_geo
    g = get_geo()
    assert direct.BEAT_RULES["map"]["predicate"]({"points": [{"name": "xyzzy nowhere"}]}, "", g) is False
    assert direct.BEAT_RULES["map"]["predicate"]({"countries": ["SAU"]}, "", g) is True
    assert direct.BEAT_RULES["map"]["predicate"]({"points": [{"name": "x", "lat": 24.7, "lon": 46.7}]}, "", g) is True
    assert direct.BEAT_RULES["map_pin"]["predicate"]({"points": [{"name": "الدوحة"}]}, "", g) is True
