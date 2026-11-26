"""Guards for the module split: old import paths keep working and no source file grows past 500 lines."""
import importlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_LINES = 500
# Written by the pipeline on every run (storyteller.generate_dynamic_tsx_file); its size follows the scene count.
GENERATED = {"remotion/src/generated/DynamicScenes.tsx"}


def test_every_pre_split_name_is_still_importable_from_its_module():
    api = json.loads((ROOT / "tests" / "fixtures" / "module_api.json").read_text(encoding="utf-8"))
    missing = {m: [n for n in names if not hasattr(importlib.import_module(m), n)] for m, names in api.items()}
    assert not {m: n for m, n in missing.items() if n}, missing


def test_no_source_file_exceeds_500_lines():
    files = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "*.py", "*.ts", "*.tsx"],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    too_long = {}
    for f in files:
        if f in GENERATED or "node_modules" in f or not (ROOT / f).exists():
            continue
        n = len((ROOT / f).read_text(encoding="utf-8", errors="replace").splitlines())
        if n > MAX_LINES:
            too_long[f] = n
    assert not too_long, too_long
