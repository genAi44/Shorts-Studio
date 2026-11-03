from pathlib import Path
import re

text = Path("remotion/src/beats.tsx").read_text(encoding="utf-8")
print("icon_scene in beats.tsx:", "icon_scene" in text)
for m in re.finditer(r"case\s+['\"][^'\"]+['\"]", text):
    print(m.group(0))

