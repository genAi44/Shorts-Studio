import requests
from pathlib import Path
from fetch_icons import ICONS_SPEC, DEST_DIR

session = requests.Session()
updated = 0
for cat, filename, prefix, icon_name, symbol in ICONS_SPEC:
    fpath = DEST_DIR / cat / filename
    if fpath.exists():
        content = fpath.read_text(encoding="utf-8")
        if 'stroke-dasharray="3 3"' in content:
            url = f"https://api.iconify.design/{prefix}/{icon_name}.svg"
            try:
                r = session.get(url, timeout=4)
                if r.status_code == 200 and "<svg" in r.text:
                    fpath.write_text(r.text, encoding="utf-8")
                    updated += 1
            except Exception:
                pass
print(f"Upgraded {updated} placeholder icons to real Iconify SVGs!")

