from pathlib import Path

TARGET = Path("remotion/src/beats.tsx")
content = TARGET.read_text(encoding="utf-8")

old_line = "{beat.title ? <div style={{opacity: 1 - exit}}><Headline text={beat.title} /></div> : null}"
new_line = "{beat.title && !['icon_scene', 'map_pin', 'timeline_card'].includes(beat.kind) ? <div style={{opacity: 1 - exit}}><Headline text={beat.title} /></div> : null}"

if old_line in content:
    content = content.replace(old_line, new_line, 1)
    TARGET.write_text(content, encoding="utf-8")
    print("Successfully patched Headline condition in BeatShell")
else:
    print("Could not find old_line in beats.tsx")

