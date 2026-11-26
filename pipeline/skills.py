"""Inject the rule sections of the repo's skills/*/SKILL.md into LLM system prompts (examples and tool how-tos left out)."""
import re
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"
_RULES = re.compile(r"^## (?:Core Rules|Rules|Mandatory[^\n]*)\n(.*?)(?=^---|^## |\Z)", re.M | re.S)

DESIGNER_SKILLS = ("motion-design-quality", "typography-components", "animated-charts", "icons-emoji-flags")
DIRECTOR_SKILLS = ("motion-design-quality", "transitions-and-effects")

_NOTE = ("STUDIO SKILL RULES (from skills/*/SKILL.md). Tool and component names in them belong to the pipeline: you cannot call them, "
         "apply the intent of each rule with what you are allowed to use. Where a coordinate here differs from LAYOUT/your contract, the contract wins.")


def rules(name: str) -> str:
    p = SKILLS_DIR / name / "SKILL.md"
    if not p.exists():
        return ""
    return "\n".join(m.strip() for m in _RULES.findall(p.read_text(encoding="utf-8")))


def skills_block(names) -> str:
    parts = [f"### {n}\n{r}" for n in names if (r := rules(n))]
    return ("\n\n" + _NOTE + "\n\n" + "\n\n".join(parts)) if parts else ""


if __name__ == "__main__":
    for n in DESIGNER_SKILLS + DIRECTOR_SKILLS:
        assert rules(n), f"no rules section parsed from skills/{n}/SKILL.md"
    assert "Worked Examples" not in skills_block(DESIGNER_SKILLS)
    print(skills_block(DESIGNER_SKILLS))
