"""فحص اعتماد الأنماط السينمائية في build_spec"""
import json
from pipeline import direct, rem
from pipeline.config import ROOT, FPS

# موقع وهمي بيانات جغرافية بسيطة
class DummyGeo:
    def has(self, c): return False
    def view_for(self, codes, pts): return {"S":1.0,"K":1.0,"lonc":0,"latc":0}
    c = {}
    def main_bbox(self, iso): return (0,0,1,1)

geo = DummyGeo()

# خطة وهمية مشابهة لخطة Run
script = {"title":"عنوان اختباري","sections":[{"role":"hook","narration":"هذا اختبار سينمائي"}]}
style = {"seed":42}
plan = [
    {
        "sc": {"id":"s1","role":"body","narration":"دراما سينمائية","_vi":{"visual_mode":"cinematic_dramatic","is_historical":False}},
        "audio":{"words":[("دراما",0.0,0.6),("سينمائية",0.6,1.2)]},
        "dur":1.2,"t0":0.0,
    }
]
total_frames = int(1.2*FPS)+10

spec = rem.build_spec(script, style, plan, total_frames, geo, photo=None, degrade=True, only_scene_idx=0)
print("spec keys:", sorted(spec.keys()))
sc = spec["scenes"][0]
print("scene visual_mode:", sc.get("visual_mode"))
for b in sc["beats"]:
    print("beat kind:", b.get("kind"), "scene_spec:", json.dumps(b.get("scene_spec"), ensure_ascii=False))
    print("  cues:", b.get("cues"))
