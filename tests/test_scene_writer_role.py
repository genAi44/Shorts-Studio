"""Part 4: scenes are written by a dedicated 'scene_writer' role, DeepSeek by default, changeable like any role."""
import inspect

from pipeline import llm_router


def test_scene_writer_role_defaults_to_deepseek(tmp_path):
    r = llm_router.LLMRouter(config_path=tmp_path / "none.json")
    c = r.get_role_config("scene_writer")
    assert "scene_writer" in llm_router.ROLES and (c["provider"], c["model"]) == ("deepseek", "deepseek-chat")


def test_scene_writer_is_user_selectable(tmp_path):
    r = llm_router.LLMRouter(config_path=tmp_path / "cfg.json")
    r.update_role_config("scene_writer", provider="gemini", model="gemini-2.5-pro")
    r.save_config()
    again = llm_router.LLMRouter(config_path=tmp_path / "cfg.json").get_role_config("scene_writer")
    assert (again["provider"], again["model"]) == ("gemini", "gemini-2.5-pro")


def test_designer_and_storyteller_write_with_scene_writer():
    import pipeline.scene_author  # noqa: F401  (import order)
    from pipeline import scene_author_prompts, storyteller_llm
    assert 'role="scene_writer"' in inspect.getsource(scene_author_prompts.llm_write)
    assert 'role="scene_writer"' in inspect.getsource(storyteller_llm)


def test_reasoning_models_get_a_longer_request_timeout():
    """DeepSeek V4-Pro thinks ~2 min on the director's plan: the default 120 s cut it off and fell through to other providers."""
    from pipeline.llm_router import REASONING_TIMEOUT, request_timeout
    assert request_timeout("deepseek-v4-pro", 120) == REASONING_TIMEOUT
    assert request_timeout("deepseek-reasoner", 120) == REASONING_TIMEOUT
    assert request_timeout("deepseek-chat", 120) == 120 and request_timeout("auto", 90) == 90
