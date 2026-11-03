from pathlib import Path

TARGET = Path("pipeline/style.py")
content = TARGET.read_text(encoding="utf-8").replace("\r\n", "\n")

# 1. Update ENUMS["bg.type"]
old_bg_type = '"bg.type": ["gradient", "radial", "grid", "dots", "stripes", "waves", "paper", "aurora", "rays"],'
new_bg_type = '"bg.type": ["cinematic", "map", "gradient", "radial", "grid", "dots", "stripes", "waves", "paper", "aurora", "rays"],'

if old_bg_type in content:
    content = content.replace(old_bg_type, new_bg_type, 1)

# 2. Add "ذهبي سينمائي" to MOODS
old_moods = 'MOODS = {'
new_moods = '''MOODS = {
    "ذهبي سينمائي": dict(c1=(14, 16, 22), c2=(6, 8, 12), accent=(255, 215, 0), accent2=(56, 189, 248), text=(255, 255, 255), dark=True),'''

if old_moods in content and "ذهبي سينمائي" not in content:
    content = content.replace(old_moods, new_moods, 1)

# 3. Update random_style to prefer "ذهبي سينمائي"
old_choice = '    name = mood if mood in MOODS else r.choice(list(MOODS))'
new_choice = '    name = mood if mood in MOODS else ("ذهبي سينمائي" if r.random() < 0.6 else r.choice(list(MOODS)))'

if old_choice in content:
    content = content.replace(old_choice, new_choice, 1)

# 4. Update ART_SYSTEM
old_art = 'ART_SYSTEM = """أنت مدير فني لفيديوهات Shorts عربية.'
new_art = '''ART_SYSTEM = """أنت مدير فني لفيديوهات Shorts عربية بمظهر سينمائي ذهبي داكن عالي التباين (Cinematic Dark Gold). الطابع البصري المفضل: خلفية داكنة فخمة مع جزيئات لهب متصاعدة وتأطير سينمائي (Vignette)، ونصوص عريضة بتدرج ذهبي متوهج (#D4AF37 و#38bdf8).'''

if old_art in content:
    content = content.replace(old_art, new_art, 1)

TARGET.write_text(content, encoding="utf-8")
print("pipeline/style.py updated successfully!")

