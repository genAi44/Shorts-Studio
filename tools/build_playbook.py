"""يُعيد توليد pipeline/playbook.md من ملفات مهارات Remotion الرسمية (remotion-dev/skills).
الاستخدام: python tools/build_playbook.py"""
import pathlib
import textwrap

ROOT = pathlib.Path(__file__).parent.parent
WORKSPACE_SKILLS = ROOT / ".agents" / "skills"
CONFIG_SKILLS = pathlib.Path.home() / ".gemini" / "config" / "skills"
CLAUDE_SKILLS = pathlib.Path.home() / ".claude" / "skills"
OUT = ROOT / "pipeline" / "playbook.md"

SKILL_NAMES = [
    "remotion-best-practices",
    "remotion-markup",
    "remotion-maps",
    "remotion-captions",
    "remotion-interactivity",
    "remotion-multimedia",
    "remotion-create",
    "remotion-render",
    "remotion-studio",
    "remotion-saas",
    "remotion-docs",
    "remotion-upgrade",
    "remotion-license",
]

PLAYBOOK = textwrap.dedent("""\
    # دليل الحركة وإخراج المشاهد — Remotion Official Motion Playbook
    # مستند إلى توجيهات ومهارات Remotion الرسمية الـ 13 (remotion-dev/skills v4.0.541)

    ## 1. قواعد التحريك والتوقيت (remotion-best-practices & remotion-create)
    - التحريك دالة نقية ومحددة زمنياً في الإطارات (Deterministic `useCurrentFrame()`).
    - أبعاد الفيديو الرأسي: 1080×1920، بمعدل 30 إطاراً في الثانية (fps=30).
    - ممنوع الإطارات الثابتة الميتة؛ الحركة مستمرة طوال المقطع (لا سكون يتجاوز 1.0 ثانية).
    - التوقيت الإيقاعي:
      - مقاطع خاطفة (Hook / Punch): 0.8–1.5 ثانية.
      - مقاطع السرد والشرح: 1.5–3.0 ثانية.
      - نقاط التركيز والتأمل: 3.0–4.0 ثانية.
    - خروج العناصر أسرع دائماً من دخولها (0.22 ثانية خروج / 0.38 ثانية دخول).
    - تأخير التتابع (Stagger): إزاحة 3–6 إطارات بين عناصر المشهد الواحد لإعطاء عمق وتدفق بصري طبيعي.

    ## 2. فيزياء الحركة وتيسير الانتقالات (remotion-markup)
    - الظهور المفاجئ والبطاقات والشارات (Badges): استخدام `spring({damping: 200, mass: 0.8})` لمنع الاهتزاز الزائد.
    - الحركات الحية المنسابة (Scale & Pop): `spring({damping: 22, mass: 0.5})`.
    - الدخول السلس: `Easing.bezier(0.16, 1, 0.3, 1)`.
    - الخروج السريع: `Easing.bezier(0.7, 0, 0.84, 0)`.
    - استخدام خواص التحويل الحديثة `scale`, `translate`, `rotate` مباشرة داخل الـ style بدلاً من سلاسل CSS transform المعقدة.
    - احترام مناطق الأمان (Keep-out Zones): الحفاظ على وضوح منطقة العنوان العلوي ومنطقة الترجمة السفلية.

    ## 3. الوسائط والمؤثرات الصوتية (remotion-multimedia & remotion-render)
    - الصور الحقيقية: معالجة كاميرا سينمائية (Ken Burns Pan/Zoom) بألوان طبيعية مشبعة وتباين عالي (ممنوع الفلاتر الرمادية الباهتة).
    - المؤثرات الصوتية (SFX): تُستخدم بحذر وعند اللحظات الحاسمة أو الصدمات فقط؛ ممنوع تكرار نفس المؤثر الصوتي (مثل whoosh) في كل مشهد.
    - التوافق مع الرندر الأوفلاين: جميع الأصول والخطوط تُحمّل محلياً لضمان الثبات التام.

    ## 4. الخرائط والمسارات الجغرافية (remotion-maps)
    - استخدام دبابيس الخرائط المتحركة (`map_pin`) والمسارات التفاعلية (`animated_route`).
    - مسارات متصلة بانحناءات ناعمة وحركات انتقال سلسة بين المدن والمواقع.
    - تجنب وضع خرائط متتالية بدون فاصل مشهدي غني.

    ## 5. النصوص والترجمة التفاعلية (remotion-captions)
    - تزامن الكلمات كلمة بكلمة بدقة عالية.
    - توهج ولون مميز للكلمة النشطة لشد انتباه المشاهد.
    - تجنب وضع أي عناصر بصرية عشوائية تغطي الترجمة أو تتداخل معها.

    ## 6. توجيه حركة الكاميرا السينمائية (Camera Motion)
    - `zoom-in` / `push-in`: تقريب عدسة سينمائي متدرج (100%→112%) — أساسي في الـ hook، الصور الواقعية، والحقائق البارزة.
    - `zoom-out`: كشف بانورامي واسع (114%→100%) — ممتاز للخرائط والمخططات الهرمية والشبكات.
    - `pan-left` / `pan-right`: انزلاق أفقي سينمائي — للمقارنات المتوازية (versus)، خطوط السير، والخطوط الزمنية.
    - `tilt-up` / `tilt-down`: مسح رأسي — للمباني التاريخية الشاهقة، القمم، والهرميات.
    - `parallax`: طبقات حركة متعددة السرعات ثلاثية الأبعاد للصور والخرائط.
    - تنويع حركة الكاميرا إلزامي بين كل مقطع والمقطع الذي يليه (ممنوع تكرار نفس حركة الكاميرا).

    ## 7. بنية المشاهد التفاعلية وقوالب السرد (remotion-interactivity & remotion-saas)
    - `generative_canvas`: أولوية قصوى عند تمثيل المفاهيم، العمليات التفاعلية، الشبكات، والتدفقات الحركية باستخدام الأشكال والشارات والروابط المتحركة والعدادات.
    - `versus_battle`: مقارنة ملحمية بين طرفين أو قوتين متصارعتين مع شارة VS مركزية.
    - `stack_pyramid`: هرم طبقي أو ترتيب هرمي تصاعدي من القمة للقاعدة.
    - `balance_meter`: ميزان فيزيائي يتأرجح بين قيمتين أو وزنين.
    - `animated_route`: مسار انتقال أو رحلة بين محطات متعددة بخط تقدم متحرك.
    - `deep_time_slider`: خط زمني للمحطات التاريخية والعصور المتعاقبة.
    - `elevation_profile`: قطاع رأسي متحرك لارتفاع قمة أو جبل بالمتر فوق سطح البحر.
    - `stat_ring_v2`: حلقة إحصائية ثلاثية الأبعاد برقم ذهبي وأيقونة بطلة في المركز.
    - `bars`: أعمدة بيانية لمقارنة كميات أو نسب مئوية.
    - `photo`: صور حقيقية عالية الدقة بدون أي فلتر رمادي باهت وبإطار عصري زجاجي أنيق.
    - `map_pin` / `map`: خرائط إقليمية ودبابيس دقيقة للمواقع والمدن.

    ## 8. ضوابط الجودة الصارمة
    - ممنوع استخدام نوع `icons` نهائياً (الدوائر التي تحتوي على نجوم مكررة محظورة).
    - ممنوع تكرار `bigtext` أو الاعتماد عليه كبديل سهل؛ يُسمح به مرة واحدة فقط كحد أقصى في الافتتاحية (Hook) إن لزم.
    - تنويع صارم: لا مقطعان متتاليان من نفس النوع أبداً في الفيديو.
    - عدم إدخال أو اختراع أي أرقام أو وقائع لم ترد صراحة في facts والسكربت.
""")


def _find_skill_file(name: str) -> pathlib.Path:
    for base in [WORKSPACE_SKILLS, CONFIG_SKILLS, CLAUDE_SKILLS]:
        candidate = base / name / "SKILL.md"
        if candidate.exists():
            return candidate
    return pathlib.Path("")


def main():
    found = []
    for name in SKILL_NAMES:
        f = _find_skill_file(name)
        if f.exists():
            found.append(f"{name} ({f.parent})")

    note = f"\n<!-- تم البناء والتحقق من مهارات Remotion الرسمية: {', '.join(found)} -->\n"
    OUT.write_text(PLAYBOOK + note, encoding="utf-8")
    print(f"✓ Playbook generated successfully at: {OUT}")
    print(f"✓ Sourced from: {len(found)} Remotion official skills")


if __name__ == "__main__":
    main()
