"""Split from `pipeline/studio.py` (re-exported there): the deterministic shot -> TSX compiler."""
import hashlib
import json
import re
import shutil
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from .config import FPS, cfg, record_fallback

from .studio import CAMERA_BOB, CAMERA_PUSH, MECHANISMS  # noqa: E402
from .studio_validate import _num, find_word, icon_ok  # noqa: E402


# ------------------------------------------------------------------ 4. Animation Engineer (deterministic compiler)

def _js(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False)


HERO_CAP = 0.25  # the hero is on screen by 25 % of the scene at the latest (an empty first half fails the sparse gate)
_CAP: Dict[str, float] = {"s": 1e9}


def _at(words: List[Dict[str, Any]], anchor: Any, default: float, lead: float = 0.1, hero: bool = True) -> float:
    """Seconds into the scene at which a slot appears: just before its word (anticipation), never later; a hero slot
    whose word comes late enters earlier (by HERO_CAP of the scene)."""
    w = find_word(words, anchor) if anchor else None
    t = max(0.0, float(w["s"]) - lead) if w else default
    return round(min(t, _CAP["s"]) if hero else t, 2)


def _keyline(shot: Dict[str, Any], words, y: str, size_hint: int = 0) -> str:
    kw = str(shot.get("keyword") or "").strip()
    size = size_hint or (120 if len(kw) <= 12 else 92)
    delay = max(0.0, _at(words, shot.get("keyword_at"), 0.0) - 0.12)  # KeyLine shows the keyword 0.12 s after its delay
    attrs = f"keyword={{{_js(kw)}}} size={{{size}}} delay={{{delay}}}"
    for k in ("lead", "tail"):
        if str(shot.get(k) or "").strip():
            attrs += f" {k}={{{_js(str(shot[k]).strip())}}}"
    return f"""      <Abs x={{90}} y={{{y}}} w={{900}} style={{{{display: 'flex', justifyContent: 'center'}}}}>
        <KeyLine {attrs} />
      </Abs>"""


def _unit_label(num: Dict[str, Any]) -> str:
    """The line under a number: its label, else its Arabic unit (Counter itself only takes Latin units like % or km²)."""
    label = str(num.get("label") or "").strip()
    suf = str(num.get("suffix") or "").strip()
    return label or (suf if re.search(r"[؀-ۿ]", suf) else "")


def _label_line(num: Dict[str, Any], words) -> str:
    lab = _unit_label(num)
    return (f"\n        <ArText size={{44}} weight={{700}} delay={{{_at(words, num.get('at'), 0.3) + 0.4}}} maxWidth={{900}}>{{{_js(lab)}}}</ArText>"
            if lab else "")


def _counter(num: Dict[str, Any], words, size: int, color: str = "") -> str:
    v = float(num["value"])
    year = bool(num.get("year")) or (v.is_integer() and 100 <= v <= 2100 and not num.get("suffix"))
    dec = 0 if v.is_integer() else min(2, len(str(v).split(".")[1]))
    attrs = f"to={{{int(v) if v.is_integer() else v}}} size={{{size}}} delay={{{_at(words, num.get('at'), 0.3)}}} decimals={{{dec}}}"
    if year:
        attrs += " year"
    if num.get("suffix") and not re.search(r"[؀-ۿ]", str(num["suffix"])):  # Arabic units go to the label (ArText)
        attrs += f" suffix={{{_js(' ' + str(num['suffix']))}}}"
    if color:
        attrs += f" color={{{_js(color)}}}"
    f0 = round(_at(words, num.get('at'), 0.3) * FPS)
    attrs += f" style={{{{opacity: interpolate(k.frame, [{max(0, f0 - 4)}, {f0 + 2}], [0, 1], {{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}})}}}}"
    return f"<Counter {attrs} />"


HEADER = """import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, ArText, Counter, Filter, Flow, Hub, Icon, KeyLine, LAYOUT, Level, MapLayer, Pinned, Ribbon, Ring, SceneProps, Shrink, Stack, Steps, Tally, Timeline, interpolate, useIdle, useKit, useSpr, enter} from '../kit';
"""

HERO_ICON = """
const HeroIcon: React.FC<{name: string; delay: number; y: number}> = ({name, delay, y}) => {
  const k = useKit();
  const p = useSpr(delay, 'bouncy');
  const bob = useIdle(8, 3.2, 0);
  return (
    <Abs x={LAYOUT.cx - 270} y={y + bob} w={540} h={540} style={{...enter(p, 'pop', 0), display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <div data-hero="icon" style={{position: 'absolute', inset: 0, borderRadius: 270, border: `8px solid ${k.c('accent', 0.85)}`, background: k.c('accent', 0.08)}} />
      <div style={{position: 'absolute', inset: -36, borderRadius: 306, border: `2px solid ${k.c('accent', 0.25)}`}} />
      <Icon name={name} size={300} color={k.c('accent')} />
    </Abs>
  );
};
"""

SIDE = """
const Side: React.FC<{x: number; label: string; icon: string; delay: number; children?: React.ReactNode}> = ({x, label, icon, delay, children}) => {
  const k = useKit();
  const p = useSpr(delay, 'snappy');
  return (
    <Abs x={x} y={LAYOUT.beat.top + 330} w={400} style={{...enter(p, 'rise', 60), display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 22}}>
      <div style={{width: 230, height: 230, borderRadius: 115, border: `5px solid ${k.c('accent', 0.8)}`, display: 'flex', alignItems: 'center', justifyContent: 'center', background: k.c('accent', 0.07)}}>
        <Icon name={icon} size={130} color={k.c('accent')} />
      </div>
      <ArText size={50} weight={800} maxWidth={390} reveal="none">{label}</ArText>
      {children}
    </Abs>
  );
};
"""


def compile_shot(shot: Dict[str, Any], ctx: Dict[str, Any], ds: Dict[str, Any]) -> str:
    """Shot spec -> one TSX scene against ../kit. Positions are fixed per device (tested against the gates), timing comes
    from the anchor words. No creative decision is made here."""
    words, dev = ctx["words"], shot["device"]
    _CAP["s"] = HERO_CAP * ctx["dur"] / FPS
    ribbon = f"      <Ribbon variant={{{int(ds['motif']['ribbon_variant'])}}} />"
    top = "LAYOUT.beat.top + 10"
    helpers, body = "", []
    if dev in MECHANISMS:
        m = shot["mech"]
        dur_s = ctx["dur"] / FPS
        enter_s = _at(words, shot.get("mech_at") or shot.get("keyword_at"), 0.2)
        ch = _at(words, m.get("change_at"), enter_s + 0.7, hero=False) if m.get("change_at") else enter_s + 0.7
        ch = round(min(max(ch, enter_s + 0.4), max(enter_s + 0.4, dur_s - 2.0)), 2)  # the change finishes inside the scene
        t = lambda k: _js(str(m.get(k) or "").strip())
        if dev == "level":
            el = f"<Level from={{{float(m['from'])}}} to={{{float(m['to'])}}} fromLabel={{{t('from_label')}}} toLabel={{{t('to_label')}}} delay={{{enter_s}}} change={{{ch}}} />"
        elif dev == "flow":
            br = [{"label": str(b["label"]).strip(), **({"share": float(b["share"])} if b.get("share") is not None else {}),
                   **({"icon": b["icon"]} if b.get("icon") and icon_ok(b.get("icon")) else {})} for b in m["branches"][:4]]
            el = f"<Flow source={{{t('source')}}} branches={{{_js(br)}}} keep={{{int(m['keep']) if isinstance(m.get('keep'), int) else -1}}} delay={{{enter_s}}} change={{{ch}}} />"
        elif dev == "filter":
            ic = f" icon={{{_js(m['icon'])}}}" if m.get("icon") and icon_ok(m.get("icon")) else ""
            el = f"<Filter from={{{float(m['from'])}}} to={{{float(m['to'])}}}{ic} fromLabel={{{t('from_label')}}} toLabel={{{t('to_label')}}} delay={{{enter_s}}} change={{{ch}}} />"
        elif dev == "tally":
            sd = [{"label": str(x["label"]).strip(), "value": float(x["value"]), "icon": x["icon"]} for x in m["sides"][:2]]
            el = f"<Tally sides={{{_js(sd)}}} delay={{{enter_s}}} change={{{ch}}} />"
        elif dev == "timeline":
            evs = [{"year": int(_num(x["year"])), "label": str(x["label"]).strip()} for x in m["events"][:5]]
            times, last = [], enter_s
            for i, x in enumerate(m["events"][:5]):  # each event on its word; never before the previous one; inside the scene
                tt = _at(words, x.get("at"), last + 0.8, hero=(i == 0)) if x.get("at") else last + (0.4 if i == 0 else 0.8)
                tt = round(min(max(tt, last + (0 if i == 0 else 0.5)), dur_s - 0.8), 2)
                times.append(tt)
                last = tt
            el = f"<Timeline events={{{_js(evs)}}} times={{{_js(times)}}} delay={{{enter_s}}} />"
        else:
            el = f"<Shrink from={{{float(m['from'])}}} to={{{float(m['to'])}}} unit={{{t('unit')}}} fromLabel={{{t('from_label')}}} toLabel={{{t('to_label')}}} delay={{{enter_s}}} change={{{ch}}} />"
        body = [_keyline(shot, words, top, 92), "      " + el]
    elif dev == "statement":
        helpers = HERO_ICON
        body = [f"      <HeroIcon name={{{_js(shot['hero_icon'])}}} delay={{{_at(words, shot.get('hero_at'), 0.0)}}} y={{LAYOUT.beat.top + 50}} />",
                _keyline(shot, words, "LAYOUT.beat.top + 660", 0)]
    elif dev == "number":
        shown = len(f"{float(shot['number']['value']):,.0f}")
        if shown <= 5:  # fits the ring
            hero = f"""      <Abs x={{LAYOUT.cx - 280}} y={{LAYOUT.beat.top + 320}} w={{560}} h={{560}}>
        <Ring value={{1}} size={{560}} delay={{{_at(words, shot['number'].get('at'), 0.3)}}}>{_counter(shot['number'], words, 170)}</Ring>
      </Abs>"""
        else:  # a long number gets the full width and an underline instead of the ring; its label sits right under it
            size = min(150, int(900 / (0.62 * shown)))
            hero = f"""      <Abs x={{90}} y={{LAYOUT.beat.top + 470}} w={{900}} style={{{{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 24}}}}>
        {_counter(shot['number'], words, size)}
        <div style={{{{width: 520, height: 10, borderRadius: 5, background: k.c('accent', 0.85)}}}} />{_label_line(shot['number'], words)}
      </Abs>"""
        body = [_keyline(shot, words, top, 96), hero]
        if shown <= 5 and _unit_label(shot["number"]):
            body.append(f"""      <Abs x={{90}} y={{LAYOUT.beat.top + 910}} w={{900}} style={{{{display: 'flex', justifyContent: 'center'}}}}>
        <ArText size={{44}} weight={{700}} delay={{{_at(words, shot['number'].get('at'), 0.3) + 0.4}}} maxWidth={{900}}>{{{_js(_unit_label(shot['number']))}}}</ArText>
      </Abs>""")
    elif dev == "pinned":
        num = shot.get("number") if isinstance(shot.get("number"), dict) else None
        inner = _counter(num, words, 110, "#141210") if num else f"<Icon name={{{_js(shot['hero_icon'])}}} size={{260}} color=\"#141210\" />"
        label = _unit_label(num) if num else ""
        lab = f"\n            <ArText size={{38}} weight={{700}} color=\"#141210\" maxWidth={{380}} reveal=\"fade\">{{{_js(label)}}}</ArText>" if label else ""
        delay = _at(words, (num or {}).get("at") or shot.get("hero_at"), 0.2)
        body = [_keyline(shot, words, top, 96),
                f"""      <Pinned x={{LAYOUT.cx - 270}} y={{LAYOUT.beat.top + 340}} w={{540}} h={{540}} rotate={{-2}} delay={{{delay}}}>
        <div style={{{{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 56}}}}>
            {inner}{lab}
        </div>
      </Pinned>"""]
    elif dev == "hub":
        items = [{"icon": it["icon"], "label": str(it["text"]).strip()} for it in shot["items"]][:6]
        first = _at(words, shot["items"][0].get("at"), 0.4) - 0.35
        body = [_keyline(shot, words, top, 92),
                f"""      <Hub cy={{LAYOUT.beat.center_y + 110}} radius={{250}} delay={{{round(max(0.0, first), 2)}}} items={{{_js(items)}}}
           center={{<Icon name={_js(shot.get('hero_icon') if icon_ok(shot.get('hero_icon')) and shot.get('hero_icon') else items[0]['icon'])} size={{130}} color={{k.c('accent')}} />}} />"""]
    elif dev == "steps":
        labels = [str(it["text"]).strip() for it in shot["items"]][:5]
        body = [_keyline(shot, words, top, 92),
                f"      <Steps items={{{_js(labels)}}} delay={{{_at(words, shot['items'][0].get('at'), 0.3)}}} />"]
    elif dev == "stack":
        items = [{"text": str(it["text"]).strip(), "icon": it["icon"]} for it in shot["items"]][:5]
        ats = [_at(words, it.get("at"), -1, hero=(i == 0)) for i, it in enumerate(shot["items"][:5])]
        known = [a for a in ats if a >= 0]
        step = round(min(1.2, max(0.25, (known[-1] - known[0]) / (len(known) - 1))), 2) if len(known) >= 2 else 0.5
        body = [_keyline(shot, words, top, 92),
                f"      <Stack top={{LAYOUT.beat.top + 300}} step={{{step}}} delay={{{known[0] if known else 0.3}}} items={{{_js(items)}}} focus />"]
    elif dev == "versus":
        helpers = SIDE
        sides = shot["sides"][:2]
        xs = ("LAYOUT.cx + 40", "LAYOUT.cx - 440")  # first side on the right (Arabic)
        body = [_keyline(shot, words, top, 92)]
        for x, s in zip(xs, sides):
            d = _at(words, s.get("at"), 0.3)
            kid = _counter({"value": s["value"], "at": s.get("at")}, words, 90) if s.get("value") is not None else ""
            body.append(f"      <Side x={{{x}}} label={{{_js(str(s['label']).strip())}}} icon={{{_js(s['icon'])}}} delay={{{d}}}>{kid}</Side>")
        body.append("""      <Abs x={LAYOUT.cx - 3} y={LAYOUT.beat.top + 340} w={6} h={420} style={{background: k.c('accent', 0.35), borderRadius: 3}} />""")
    elif dev == "map":
        body = ["      <MapLayer overlay={data.map_overlay} mode=\"split-bottom\" />", _keyline(shot, words, top, 92)]
        num = shot.get("number") if isinstance(shot.get("number"), dict) else None
        if num:
            lab = _unit_label(num)
            lab_el = (f"<ArText size={{40}} weight={{700}} delay={{{_at(words, num.get('at'), 0.3) + 0.4}}} maxWidth={{420}}>{{{_js(lab)}}}</ArText>" if lab else "")
            body.append(f"""      <Abs x={{90}} y={{LAYOUT.beat.top + 270}} w={{900}} style={{{{display: 'flex', flexDirection: 'row-reverse', alignItems: 'center', justifyContent: 'center', gap: 28}}}}>
        {_counter(num, words, min(110, int(700 / (0.62 * len(f"{float(num['value']):,.0f}")))))}{lab_el}
      </Abs>""")
    return (HEADER + helpers + f"""
// studio shot ({dev}): {str(shot.get('why') or '').replace(chr(10), ' ')[:160]}
export default function Scene({{dur, data}}: SceneProps) {{
  const k = useKit();
  // virtual camera: slow push-in + gentle bob on the content; the ribbon stays outside it (slower layer = parallax)
  const cam = interpolate(k.frame, [0, Math.max(1, dur)], [1, {CAMERA_PUSH}], {{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}});
  const bob = useIdle({CAMERA_BOB}, 4.5, 0);
  return (
    <AbsoluteFill>
{ribbon}
      <AbsoluteFill style={{{{transform: `translateY(${{bob}}px) scale(${{cam}})`, transformOrigin: '50% 45%'}}}}>
{chr(10).join(body)}
      </AbsoluteFill>
    </AbsoluteFill>
  );
}}
""")
