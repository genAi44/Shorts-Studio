from pathlib import Path

TARGET = Path("pipeline/rem.py")
content = TARGET.read_text(encoding="utf-8").replace("\r\n", "\n")

old_render = """def render_video(spec, out_mp4, work_dir, audio_wav, progress=None):
    pub = os.path.join(work_dir, "public")
    make_public(pub, audio_wav)
    sp = os.path.join(work_dir, "spec.json")
    json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
    _run(["node", "render.mjs", sp, out_mp4, pub], progress)
    shutil.rmtree(pub, ignore_errors=True)


def render_still(spec, out_jpg, frame, work_dir):
    \"\"\"frame: رقم أو قائمة مفصولة بفواصل مع %d في اسم الملف.\"\"\"
    pub = os.path.join(work_dir, "public")
    make_public(pub, None)
    sp = os.path.join(work_dir, "spec_still.json")
    json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
    _run(["node", "still.mjs", sp, out_jpg, str(frame), pub])
    shutil.rmtree(pub, ignore_errors=True)"""

new_render = """def render_video(spec, out_mp4, work_dir, audio_wav, progress=None):
    work_dir = os.path.abspath(work_dir)
    out_mp4 = os.path.abspath(out_mp4)
    pub = os.path.join(work_dir, "public")
    make_public(pub, audio_wav)
    sp = os.path.join(work_dir, "spec.json")
    json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
    _run(["node", "render.mjs", sp, out_mp4, pub], progress)
    shutil.rmtree(pub, ignore_errors=True)


def render_still(spec, out_jpg, frame, work_dir):
    \"\"\"frame: رقم أو قائمة مفصولة بفواصل مع %d في اسم الملف.\"\"\"
    work_dir = os.path.abspath(work_dir)
    out_jpg = os.path.abspath(out_jpg)
    pub = os.path.join(work_dir, "public")
    make_public(pub, None)
    sp = os.path.join(work_dir, "spec_still.json")
    json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
    _run(["node", "still.mjs", sp, out_jpg, str(frame), pub])
    shutil.rmtree(pub, ignore_errors=True)"""

if old_render in content:
    content = content.replace(old_render, new_render, 1)
    TARGET.write_text(content, encoding="utf-8")
    print("Successfully patched render_video and render_still in pipeline/rem.py")
else:
    print("Could not match old_render in pipeline/rem.py")

