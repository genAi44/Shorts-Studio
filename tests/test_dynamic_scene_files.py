"""DynamicScenes.tsx is an index over one generated file per scene; the cache parser still sees every verified block."""
import pipeline.storyteller  # noqa: F401  (loads the split modules in order)
from pipeline import storyteller_tsx_tools as tt

FC = "React.FC<{frame?: number; fps?: number; dur?: number}>"


def _block(tid, sig=None):
    code = f"export const {tid}: {FC} = () => <AbsoluteFill />;"
    return f"/* @llm_verified:{tid}:{sig} */\n{code}" if sig else code


def test_scene_files_index_cache_and_stale_cleanup(tmp_path, monkeypatch):
    index = tmp_path / "DynamicScenes.tsx"
    monkeypatch.setattr(tt, "DYNAMIC_TSX_PATH", index)
    monkeypatch.setattr(tt, "SCENES_DIR", tmp_path / "scenes")

    tt._write_dynamic_files([_block("A", "aa11"), _block("B")], ["A", "B"], {"A": "const _GEO_A = {};"})
    text = index.read_text(encoding="utf-8")
    assert "import {A} from './scenes/A';" in text and "'B': B," in text and "DYNAMIC_SCENE_REGISTRY" in text
    assert "const _GEO_A = {};" in (tmp_path / "scenes" / "A.tsx").read_text(encoding="utf-8")
    assert tt.read_scene_block("B") == _block("B")
    # only LLM-verified blocks are cached, and only their own code (not the next fallback scene)
    assert tt._verified_blocks_on_disk() == {("A", "aa11"): f"export const A: {FC} = () => <AbsoluteFill />;"}

    snap = tt.snapshot_dynamic_scenes()
    tt._write_dynamic_files([_block("C")], ["C"], {})
    assert sorted(p.stem for p in (tmp_path / "scenes").glob("*.tsx")) == ["C"]  # stale scenes removed
    tt.restore_dynamic_scenes(snap)
    assert sorted(p.stem for p in (tmp_path / "scenes").glob("*.tsx")) == ["A", "B"]
    assert index.read_text(encoding="utf-8") == text
