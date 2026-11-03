"""يُعيد توليد pipeline/playbook.md من ملفات المهارات في ~/.claude/skills/.
الاستخدام: python tools/build_playbook.py"""
import pathlib
import textwrap

SKILLS_DIR = pathlib.Path.home() / ".claude" / "skills"
OUT = pathlib.Path(__file__).parent.parent / "pipeline" / "playbook.md"

SKILL_NAMES = [
    "remotion-best-practices",
    "remotion-markup",
    "remotion-captions",
]

# القواعد الأساسية المُقطَّرة يدوياً (محدِّثها: هذا السكربت).
PLAYBOOK = textwrap.dedent("""\
    # دليل الحركة — Motion Playbook

    ## الإيقاع والتوقيت
    - مقاطع سريعة: 0.8–1.5 ث. متوسطة: 1.5–3 ث. نقطة توقف: 3–4 ث.
    - الخروج أسرع من الدخول (0.26 ث خروج / 0.4 ث دخول).
    - لا إطار ساكن أكثر من 1.2 ث؛ شيء دائماً يتحرك.
    - تأخير التتابع بين عناصر المشهد: 3–6 إطارات (0.1–0.2 ث).
    - تقاطع انتباه كل 5–7 مقاطع: غيّر تخطيطاً أو منظور كاميرا أو لوناً.

    ## التيسير (Easing — Remotion)
    - دخول: ease-out `bezier(0.16, 1, 0.3, 1)` أو `spring({damping:22})`.
    - خروج: ease-in `bezier(0.7, 0, 0.84, 0)`.
    - انبثاق (pop/badge): `spring({damping:200})` — بلا ارتداد.
    - كل `interpolate()` يُكتب مضمّناً في style مباشرة (قابل للتحرير في Studio).

    ## الكاميرا لكل مقطع (beat.camera)
    - `push-in`: تكبير تدريجي 100%→107% طوال المقطع — للتأكيد والـ hook.
    - `pan`: انزلاق أفقي 0→–40px — للقوائم والتسلسل والجداول الزمنية.
    - `parallax`: طبقات بسرعات مختلفة — للصور والخرائط.
    - `static`: بلا حركة كاميرا (افتراضي).

    ## اختيار النوع
    - `bigtext` center: للتأكيد المنفرد. stack: للقوائم. diag: للحيوية. left: للتركيز الأيمن.
    - `stat` ring: رقم واحد بدائرة. bar: مقارنة. plain: بساطة.
    - `canvas`: ابدأ بالعنصر الرئيسي (delay=0) ثم المساندة (delay=0.2–0.6).
    - `photo` push-in: للوجوه/المباني. parallax: للمناظر. static: للأحداث التاريخية.

    ## التتابع
    - لا مقطعان متتاليان من نفس النوع.
    - hook: إيقاع سريع + push-in.
    - body: تنوّع الأنواع مع المستويات الثلاثة.
    - loop: يعكس بصريات الـ hook بصرياً.

    ## الصور (photo beats)
    - `query`: اسم صريح — مكان + بلد + سنة إن وجدت.
    - `alt_queries`: استعلامان احتياطيان أوسع تدريجياً.
    - `must_show`: الشيء الواجب تصويره (يُرفض أي صورة لا تُظهره).
    - `avoid`: ما يُستبعد (watermark text collage).
    - `cutout=true` للأجسام المفردة الواضحة فقط.
""")


def _read_skill(name: str) -> str:
    p = SKILLS_DIR / name / "SKILL.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main():
    present = [n for n in SKILL_NAMES if (_read_skill(n))]
    note = f"\n<!-- مولَّد من المهارات: {', '.join(present) or 'none'} -->\n" if present else ""
    OUT.write_text(PLAYBOOK + note, encoding="utf-8")
    print(f"✓ {OUT}")


if __name__ == "__main__":
    main()
