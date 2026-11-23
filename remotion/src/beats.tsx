import React, {useContext, useId} from 'react';

import {AbsoluteFill, Audio, Easing, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {SafeImg} from './SafeImg';
import {ArrowFlow, CaptionScrim, FireSparks, FloatBadge, GlowText, MapOverlay, Particles} from './fx';
import {CameraRig, ParallaxLayer, SvgZoomIn, useCameraShake} from './camera';
import {AnimatedMetric} from './metrics';

import {Icon} from './icons';
import {Flag} from './flag';
import {SceneVisualsLayer} from './visualLayer';
import {SlotContainer} from './layoutEngine';
import {ChartVisual} from './charts';
import {TypographyVisual} from './typography';
import {
  AnimatedRouteBeat,
  BalanceMeterBeat,
  DeepTimeSliderBeat,
  DotMatrixPopulationBeat,
  FrontlineClashBeat,
  MacroZoomGlobeBeat,
  MoneyWaterfallBeat,
  StackPyramidBeat,
  SubsurfaceMineBeat,
  VersusBattleBeat,
} from './visualStoryBeats';
import {GenerativeCanvasBeat} from './generativeCanvas';
import {AreaMapBeat} from './areaMap';
import {DYNAMIC_SCENE_REGISTRY} from './generated/DynamicScenes';

import {clamp01, enterStyle, EnterKind, Pop, useFont, useIdle, useProgress, useSpring} from './hooks';

import {Headline} from './text';

import {AccentShapes, PhotoBeat, isAlt, useFont2} from './photo';
import {CitySceneBeat, ArchitectureBeat, MysterySceneBeat} from './sceneBeats';

import {MotionCtx, on, rgba, useTheme} from './theme';
import {BEAT_ZONE, CAPTION_ZONE, HEADLINE_ZONE, SAFE_BOTTOM, SAFE_TOP} from './layout';
import {Beat, RGB} from './types';



const shade = (c: RGB, k: number): string => `rgb(${c.map((v) => Math.max(0, Math.min(255, Math.round(v * k)))).join(',')})`;

/** Read a cue frame from beat.cues by type (returns seconds). */
const cueSecOf = (beat: Beat, type: string, fallback = 0): number => {
  const fps = 30;
  const cue = (beat.cues as Array<{frame: number; type: string}> | undefined)?.find(c => c.type === type);
  return cue ? cue.frame / fps : fallback;
};



// ------------------------------------------------------------------ غلاف المقطع: خروج + كاميرا (push-in/pan/parallax/fly-to/static مع micro-drift)

export const BeatShell: React.FC<{beat: Beat; children: React.ReactNode}> = ({beat, children}) => {

  const frame = useCurrentFrame();

  const {fps} = useVideoConfig();

  const th = useTheme();

  const ex = beat.settled ? 0 : Math.round(0.26 * fps);

  const exit = ex

    ? interpolate(frame, [beat.dur - ex, beat.dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: th.ease.in})

    : 0;

  const prog = beat.dur > 1 ? frame / (beat.dur - 1) : 0;

  const cam = beat.camera as string | undefined;

  // impact shake — triggered at metric_punch cue (frame -99 = no-op when no cue)
  const punchF = (beat.cues as Array<{frame: number; type: string}> | undefined)
    ?.find(c => c.type === 'metric_punch')?.frame ?? -99;
  const sh = useCameraShake(punchF, 12, 0.85);

  // حركة الكاميرا الديناميكية السينمائية

  let camScale = 1;

  let camX = sh.x;   // shake is always baked in

  let camY = sh.y;

  let camRot = sh.rot;



  if (cam === 'zoom-in' || cam === 'push-in') {

    camScale = 1 + 0.12 * prog;

  } else if (cam === 'zoom-out') {

    camScale = 1.14 - 0.14 * prog;

  } else if (cam === 'pan-left' || cam === 'pan') {

    camX += -60 * prog;

  } else if (cam === 'pan-right') {

    camX += 60 * prog;

  } else if (cam === 'tilt-up') {

    camY += 40 - 70 * prog;

  } else if (cam === 'tilt-down') {

    camY += -30 + 70 * prog;

  } else if (cam === 'parallax') {

    // Ken Burns full strength — matches CameraRig("ken-burns") values
    camScale = 1 + 0.08 * prog;

    camX += -20 + 40 * prog;

  } else if (cam === 'handheld') {

    camScale = 1.03 + 0.02 * Math.sin((frame / fps) * 2.5);

    camX += Math.sin((frame / fps) * 1.8) * 12;

    camY += Math.cos((frame / fps) * 2.1) * 9;

    camRot += Math.sin((frame / fps) * 1.5) * 0.8;

  }



  // إجراء ثانٍ إلزامي لأي مقطع أطول من 2.5 ثانية (> 75 إطاراً): تقريب إضافي للكاميرا وتوهج ديناميكي

  const isLong = beat.dur > Math.round(2.5 * fps) && !beat.settled;

  const secondActionStart = Math.round(2.0 * fps);

  const secondProg = isLong

    ? interpolate(frame, [secondActionStart, beat.dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: th.ease.inOut})

    : 0;

  const secondPushScale = 1 + 0.075 * secondProg;

  const totalScale = camScale * secondPushScale;



  // micro-drift on static so no frame is truly frozen (4px sine bob)

  const drift = (!cam || cam === 'static') && !beat.settled ? Math.sin(frame / fps * 1.4) * 4 : 0;



  return (

    <AbsoluteFill>

      <AbsoluteFill style={{

        opacity: 1 - exit,

        translate: `${camX + drift * 0.25}px ${camY + -36 * exit + drift}px`,

        scale: String((1 - 0.035 * exit) * totalScale),

        rotate: camRot ? `${camRot}deg` : undefined

      }}>

        {children}

      </AbsoluteFill>

      {/* إشارة بصرية حركية كإجراء ثانٍ عند المقطع الطويل */}

      {!beat.tsx_id && isLong && frame >= secondActionStart ? (

        <div style={{

          position: 'absolute', inset: 0, pointerEvents: 'none',

          boxShadow: `inset 0 0 ${Math.round(90 * secondProg)}px ${rgba(th.p.accent, 0.28 * (1 - secondProg))}`,

          opacity: clamp01(secondProg * 2)

        }}>

          <div style={{

            position: 'absolute', left: 540 - 220 * secondProg, width: 440 * secondProg,

            top: th.zoneCy + 440, height: 6, borderRadius: 3,

            background: `linear-gradient(90deg, transparent, ${rgba(th.p.accent)}, transparent)`,

            opacity: 1 - secondProg * 0.4

          }} />

        </div>

      ) : null}

      {!beat.tsx_id && beat.title && ![
        'icon_scene', 'map_pin', 'timeline_card', 'bigtext', 'custom_scene',
        'generative_canvas', 'versus_battle', 'balance_meter', 'stack_pyramid',
        'deep_time_slider', 'macro_zoom_globe', 'subsurface_mine', 'dot_matrix_population',
        'money_waterfall', 'frontline_clash', 'animated_route', 'bars', 'line_chart', 'pie_chart'
      ].includes(beat.kind) ? <div style={{opacity: 1 - exit}}><Headline text={beat.title} /></div> : null}

    </AbsoluteFill>

  );

};



// ------------------------------------------------------------------ الخريطة

const Marker: React.FC<{kind: string; col: RGB; ring: RGB; p: number}> = ({kind, col, ring, p}) => {

  const s = 0.4 + 0.6 * p;

  const c = rgba(col);

  const r = rgba(ring);

  return (

    <svg width={140} height={140} viewBox="-70 -90 140 140" style={{overflow: 'visible', scale: s, opacity: clamp01(p * 2)}}>

      {kind === 'pin' ? (

        <g>

          <path d="M0 0C-6-14-20-26-20-42A20 20 0 0 1 20-42C20-26 6-14 0 0Z" fill={r} />

          <path d="M0-4C-5-15-16-26-16-42A16 16 0 0 1 16-42C16-26 5-15 0-4Z" fill={c} />

          <circle cx={0} cy={-42} r={6.5} fill={r} />

        </g>

      ) : kind === 'square' ? (

        <g><rect x={-19} y={-19} width={38} height={38} fill={r} /><rect x={-14} y={-14} width={28} height={28} fill={c} /></g>

      ) : kind === 'diamond' ? (

        <g><polygon points="0,-24 24,0 0,24 -24,0" fill={r} /><polygon points="0,-18 18,0 0,18 -18,0" fill={c} /></g>

      ) : (

        <g><circle r={17} fill={r} /><circle r={13} fill={c} /></g>

      )}

    </svg>

  );

};



const HlCountry: React.FC<{h: any; i: number}> = ({h, i}) => {

  const th = useTheme();

  const p = useSpring(0.25 + 0.4 * i, 'smooth');

  const e = useSpring(0.12 + 0.4 * i, 'smooth');

  const mp = th.st.map;

  const col = th.p.hl[i % th.p.hl.length];

  const fill = mp.fill === 'gradient' ? `url(#g${i})` : mp.fill === 'hatch' ? `url(#h${i})` : rgba(col);

  return (

    <g style={{transformOrigin: `${h.cx}px ${h.cy}px`, scale: 0.9 + 0.1 * Math.min(1, p), opacity: clamp01(p * 1.5)}}>

      <defs>

        <linearGradient id={`g${i}`} x1="0" y1="0" x2="0" y2="1">

          <stop offset="0" stopColor={shade(col, 1.18)} />

          <stop offset="1" stopColor={shade(col, 0.76)} />

        </linearGradient>

        <pattern id={`h${i}`} width={26} height={26} patternUnits="userSpaceOnUse" patternTransform="rotate(45)">

          <rect width={26} height={26} fill={shade(col, 0.92)} />

          <rect width={9} height={26} fill="rgba(255,255,255,0.2)" />

        </pattern>

      </defs>

      <path d={h.d} fillRule="evenodd" fill={fill} />

      <path d={h.d} fillRule="evenodd" fill="none" stroke={rgba(th.p.text, 0.92)} strokeWidth={mp.edge} strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - Math.min(1, e)} />

    </g>

  );

};



const MapPoint: React.FC<{pt: any; j: number}> = ({pt, j}) => {

  const th = useTheme();

  const font = useFont();

  const frame = useCurrentFrame();

  const {fps} = useVideoConfig();

  const {settled} = useContext(MotionCtx);

  const delay = 0.2 + 0.25 * j;

  const p = useSpring(delay, 'bouncy');

  const lp = useSpring(delay + 0.15, 'snappy');

  const kind = th.st.map.marker;

  const dot = pt.dot !== false;

  const ph = settled ? 0.4 : (((frame / fps - delay - 0.4) * 0.9) % 1 + 1) % 1;

  // إذا كانت النقطة قريبة من شريط العنوان العلوي (pt.y < 560)، نضع التسمية أسفل الدبوس لتفادي الاصطدام
  const ly = dot && kind === 'pin' ? (pt.y < 560 ? pt.y + 70 : pt.y - 118) : pt.ly;

  return (

    <>

      {dot && (

        <div style={{position: 'absolute', left: pt.x - 70, top: pt.y - 70, width: 140, height: 140, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>

          {kind !== 'pin' && p > 0.98 && (

            <div style={{position: 'absolute', left: 70 - (18 + 46 * ph), top: -(18 + 46 * ph) + 70, width: 2 * (18 + 46 * ph), height: 2 * (18 + 46 * ph), borderRadius: '50%', border: `5px solid ${rgba(th.p.accent, 0.85 * (1 - ph))}`}} />

          )}

          <div style={{position: 'absolute', left: 0, top: kind === 'pin' ? BEAT_ZONE.pin_offset : BEAT_ZONE.zero}}>

            <Marker kind={kind} col={th.p.accent} ring={th.p.text} p={p} />

          </div>

        </div>

      )}

      {pt.name ? (

        <div style={{position: 'absolute', left: pt.x, top: ly, translate: '-50% -50%'}}>

          <div style={{...font, ...enterStyle(lp, 'rise', 24), fontSize: 46, fontWeight: Math.max(500, th.weight - 150), color: rgba(th.p.text), background: rgba(th.p.c1, 0.82), padding: '8px 26px', borderRadius: 24, whiteSpace: 'nowrap', direction: 'rtl'}}>{pt.name}</div>

        </div>

      ) : null}

    </>

  );

};



// لوحة تكبير للدول الصغيرة جداً (الفاتيكان، سان مارينو...)

const SmallMagnifier: React.FC<{h: any; ctx: string}> = ({h, ctx}) => {

  const th = useTheme();

  const p = useSpring(0.6, 'snappy');

  const col = rgba(th.p.hl[0] || th.p.accent);

  const vz = (h.vz as number) || 60;

  const half = vz / 2;

  return (

    <div style={{position: 'absolute', right: 60, top: th.zoneCy - 360, width: 260, height: 260, borderRadius: '50%', overflow: 'hidden', border: `6px solid ${col}`, boxShadow: `0 0 40px ${rgba(th.p.accent, 0.55)}`, opacity: Math.min(1, p * 2), scale: String(0.85 + 0.15 * Math.min(1, p))}}>

      <svg width={260} height={260} viewBox={`${h.cx - half} ${h.cy - half} ${vz} ${vz}`} style={{position: 'absolute', inset: 0}}>

        <rect x={h.cx - half} y={h.cy - half} width={vz} height={vz} fill={rgba(th.p.c1)} />

        <path d={ctx} fillRule="evenodd" fill={rgba(th.p.ctx, 0.35)} />

        <path d={h.d} fillRule="evenodd" fill={col} />

      </svg>

      <div style={{position: 'absolute', bottom: BEAT_ZONE.magnifier_bottom, left: 0, right: 0, textAlign: 'center', color: rgba(th.p.text), fontSize: 20, fontWeight: 700}}>×{Math.round(260 / vz)}z</div>

    </div>

  );

};



const MapBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const th = useTheme();

  const frame = useCurrentFrame();

  const v = beat.view;

  const ctxP = useSpring(0, 'smooth');

  if (!v) return null;

  // fly-to: SvgZoomIn handles the animated zoom-in to city coords
  const flyTo = (beat.camera as string) === 'fly-to';
  const firstHl = v.hl && v.hl.length > 0 ? v.hl[0] : null;
  const firstPt = v.pts && v.pts.length > 0 ? v.pts[0] : null;
  // Zoom origin: prefer pin point, then highlighted country center
  const flyOx = firstPt ? firstPt.x : firstHl ? firstHl.cx : 540;
  const flyOy = firstPt ? firstPt.y : firstHl ? firstHl.cy : 870;
  // For non-fly-to: Ken Burns slow push
  const kb = interpolate(frame, [0, beat.dur], [1, 1.05], {extrapolateRight: 'clamp', easing: Easing.bezier(0.3, 0, 0.7, 1)});
  const dy = th.zoneCy - 870;
  const scale = flyTo ? undefined : beat.settled ? 1.05 : kb;
  const ox = 540;
  const oy = 870;

  const smallHls = v.hl.filter((h: any) => h.small);

  const mapContent = (
    <>
      {/* depth=1: خريطة الخلفية + الدول المضاءة (تتحرك بسرعة متوسطة) */}
      <ParallaxLayer depth={1}>
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          <path d={v.ctx} fillRule="evenodd" fill={rgba(th.p.ctx, th.st.map.ctx_alpha * clamp01(ctxP))} />
          <path d={v.ctx} fillRule="evenodd" fill="none" stroke={rgba(th.p.ctx_edge, 0.85)} strokeWidth={2} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - Math.min(1, ctxP)} />
          {v.hl.map((h: any, i: number) => <HlCountry key={h.iso} h={h} i={i} />)}
        </svg>
      </ParallaxLayer>
      {/* depth=2: الدبابيس والتسميات (تتحرك أسرع = إحساس العمق) */}
      <ParallaxLayer depth={2}>
        {v.pts.map((pt: any, j: number) => <MapPoint key={j} pt={pt} j={j} />)}
      </ParallaxLayer>
    </>
  );

  return (
    <AbsoluteFill>
      {flyTo ? (
        // SvgZoomIn: animated wide-to-city zoom via CameraRig's SvgZoomIn
        <SvgZoomIn
          originX={flyOx}
          originY={flyOy}
          fromScale={0.42}
          dur={Math.max(Math.round(beat.dur * 0.65), 20)}
        >
          <div style={{position: 'absolute', inset: 0, translate: `0 ${dy}px`}}>
            {mapContent}
          </div>
        </SvgZoomIn>
      ) : (
        <div style={{position: 'absolute', inset: 0, transformOrigin: `${ox}px ${oy}px`, translate: `0 ${dy}px`, scale: String(scale)}}>
          {mapContent}
        </div>
      )}
      {smallHls.map((h: any, i: number) => <SmallMagnifier key={i} h={h} ctx={v.ctx} />)}
    </AbsoluteFill>
  );

};



// ------------------------------------------------------------------ أرقام

const parseNum = (s: string) => {

  const m = s.match(/\d[\d,\.]*/);

  if (!m || m.index === undefined) return null;

  const raw = m[0].replace(/[.,]+$/, '');

  const clean = raw.replace(/,/g, '');

  const val = parseFloat(clean);

  if (isNaN(val)) return null;

  return {pre: s.slice(0, m.index), val, dec: clean.includes('.') ? clean.split('.')[1].length : 0, commas: raw.includes(','), suf: s.slice(m.index + raw.length)};

};



const StatBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const th = useTheme();

  const font = useFont();

  const idle = useIdle(5, 3.4);
  // Use cue timing when available; fall back to hardcoded 0.15s
  const metricDelay = cueSecOf(beat, 'metric_start', 0.15);
  const p = useProgress(metricDelay, 1.5);

  const a = useSpring(0, 'snappy');

  const lay = beat.layout || th.st.stat.layout;

  const s = String(beat.number ?? '');

  const pn = parseNum(s);

  const show = pn ? pn.pre + (pn.commas ? (pn.val * p).toLocaleString('en-US', {minimumFractionDigits: pn.dec, maximumFractionDigits: pn.dec}) : (pn.val * p).toFixed(pn.dec)) + pn.suf : s;

  const cy = th.zoneCy - (th.st.headline.pos === 'lower' ? 100 : 60);

  const label = String(beat.label ?? '');

  const lines = label.split(/\s+/).filter(Boolean);

  const half = Math.ceil(lines.length / 2);

  const rows = lines.length > 3 ? [lines.slice(0, half).join(' '), lines.slice(half).join(' ')] : [lines.join(' ')];

  const R = 280;

  const C = 2 * Math.PI * R;

  const num = (size: number, color: RGB): React.CSSProperties => ({...font, fontSize: size, lineHeight: 1, color: rgba(color), textShadow: th.shadow, direction: 'ltr', fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap'});

  const labelEl = (top: number, color = th.p.text) => (

    <div dir="rtl" style={{position: 'absolute', left: 90, right: 90, top, textAlign: 'center'}}>

      {rows.map((r, i) => (

        <Pop key={i} delay={0.45 + i * 0.12} kind="rise" dist={30}>

          <div style={{...font, fontWeight: Math.max(500, th.weight - 200), fontSize: 60, lineHeight: 1.35, color: rgba(color), textShadow: th.shadow}}>{r}</div>

        </Pop>

      ))}

    </div>

  );

  return (

    <AbsoluteFill style={{translate: `0 ${idle}px`}}>

      {lay === 'ring' && (

        <>

          <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, opacity: clamp01(a * 1.6)}}>

            <circle cx={540} cy={cy - 80} r={R} fill="none" stroke={rgba(th.p.text, 0.18)} strokeWidth={14} />

            <circle cx={540} cy={cy - 80} r={R} fill="none" stroke={rgba(th.p.accent)} strokeWidth={14} strokeLinecap="round" strokeDasharray={C} strokeDashoffset={C * (1 - p)} transform={`rotate(-90 540 ${cy - 80})`} />

          </svg>

          <div style={{position: 'absolute', left: 0, right: 0, top: cy - 80 - 85, textAlign: 'center', ...enterStyle(a, 'pop'), ...num(170, th.p.accent)}}>{show}</div>

          {labelEl(cy + 270)}

        </>

      )}

      {lay === 'bar' && (

        <>

          <div style={{position: 'absolute', left: 0, right: 0, top: cy - 250, textAlign: 'center', ...enterStyle(a, 'rise'), ...num(210, th.p.accent)}}>{show}</div>

          <div style={{position: 'absolute', left: 140, right: 140, top: cy + 20, height: 34, borderRadius: 17, background: rgba(th.p.text, 0.16)}}>

            <div style={{position: 'absolute', right: 0, top: BEAT_ZONE.zero, bottom: BEAT_ZONE.zero, width: `${p * 100}%`, borderRadius: 17, background: `linear-gradient(270deg, ${rgba(th.p.accent)}, ${rgba(th.p.accent2)})`}} />

          </div>

          {labelEl(cy + 120)}

        </>

      )}

      {lay === 'stack' && (

        <>

          <div dir="rtl" style={{position: 'absolute', left: 90, right: 90, top: cy - 330, textAlign: 'center'}}>

            {rows.map((r, i) => (

              <Pop key={i} delay={0.1 + i * 0.12} kind="drop" dist={30}>

                <div style={{...font, fontWeight: Math.max(500, th.weight - 200), fontSize: 60, color: rgba(th.p.accent2), textShadow: th.shadow}}>{r}</div>

              </Pop>

            ))}

          </div>

          <div style={{position: 'absolute', left: 0, right: 0, top: cy - 170, textAlign: 'center', ...enterStyle(a, 'pop'), ...num(250, th.p.text)}}>{show}</div>

          <div style={{position: 'absolute', left: 540 - 230 * p, width: 460 * p, top: cy + 120, height: 12, borderRadius: 6, background: rgba(th.p.accent)}} />

        </>

      )}

      {lay === 'plain' && (

        <>

          <div style={{position: 'absolute', left: 0, right: 0, top: cy - 160, textAlign: 'center', ...enterStyle(a, 'rise'), ...num(240, th.p.accent)}}>{show}</div>

          <div style={{position: 'absolute', left: 540 - 300 * p, width: 600 * p, top: cy + 130, height: 12, borderRadius: 6, background: rgba(th.p.accent2)}} />

          {labelEl(cy + 190)}

        </>

      )}

    </AbsoluteFill>

  );

};



// ------------------------------------------------------------------ نص كبير

const TextWord: React.FC<{w: string; i: number; n: number; layout: string; size: number; color: string; kind: EnterKind}> = ({w, i, n, layout, size: size0, color: color0, kind}) => {

  const f1 = useFont();

  const f2 = useFont2();

  const th = useTheme();

  const alt = isAlt(i, n, th.st.edit.mixpat);

  const font = alt ? f2 : f1;

  const size = alt ? size0 * 0.94 : size0;

  const color = alt ? rgba(th.p.text, 0.9) : color0;

  const p = useSpring(0.12 + i * 0.22, kind === 'pop' ? 'bouncy' : 'snappy');

  const idle = useIdle(4, 3.4, i * 0.8);

  return (

    <div style={{...font, ...enterStyle(p, kind, 70), filter: th.st.edit.blur && p < 0.98 ? `blur(${(1 - clamp01(p)) * 14}px)` : undefined, fontSize: size, lineHeight: 1.18, color, textShadow: th.shadow, marginTop: idle, display: layout === 'stack' ? 'block' : 'inline-block'}}>{w}</div>

  );

};



const BigTextBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const th = useTheme();

  const font = useFont();

  const layout = beat.layout || th.st.text.layout;

  const words = String(beat.text || beat.title || '').split(/\s+/).filter(Boolean).slice(0, 7);

  const chars = words.join(' ').length;

  let size = th.st.text.size * (words.length <= 2 ? 1.15 : chars > 26 ? 0.78 : 0.95);

  if (layout === 'stack') size = Math.min(size * 1.1, 1500 / Math.max(words.length, 1) / 1.3);

  const bar = useProgress(0.1, 0.7);

  const sub = useSpring(0.1 + words.length * 0.22 + 0.2, 'smooth');

  const justify = layout === 'left' ? 'flex-start' : 'center';

  return (

    <AbsoluteFill>

      <AccentShapes seed={beat.from + 3} count={2} />

      <div dir="rtl" lang="ar" style={{position: 'absolute', left: 90, right: layout === 'left' ? 130 : 90, top: th.zoneCy - 300, height: 600, display: layout === 'stack' ? 'block' : 'flex', flexWrap: 'wrap', alignContent: 'center', justifyContent: justify, columnGap: Math.round(size * 0.28), textAlign: layout === 'left' ? 'right' : 'center', rotate: layout === 'diag' ? '-6deg' : undefined}}>

        {words.map((w, i) => (

          <TextWord key={i} w={w} i={i} n={words.length} layout={layout} size={size}

            color={layout === 'stack' ? (i % 2 ? rgba(th.p.text) : rgba(th.p.accent)) : i === words.length - 1 ? rgba(th.p.accent) : rgba(th.p.text)}

            kind={layout === 'diag' ? 'pop' : layout === 'left' ? 'right' : 'rise'} />

        ))}

      </div>

      {layout === 'left' && <div style={{position: 'absolute', right: 80, top: th.zoneCy - 300 + 300 * (1 - bar), width: 14, height: 600 * bar, borderRadius: 7, background: rgba(th.p.accent)}} />}

      {beat.sub ? (

        <div dir="rtl" style={{...font, ...enterStyle(sub, 'rise', 24), position: 'absolute', left: 90, right: 90, top: th.zoneCy + 330, textAlign: 'center', fontSize: 52, fontWeight: Math.max(500, th.weight - 250), color: rgba(th.p.accent2), textShadow: th.shadow}}>{beat.sub}</div>

      ) : null}

    </AbsoluteFill>

  );

};



// ------------------------------------------------------------------ أعمدة

const BarRow: React.FC<{item: any; i: number; max: number; top: number}> = ({item, i, max, top}) => {

  const th = useTheme();

  const font = useFont();

  const p = useSpring(0.1 + i * 0.2, 'smooth');

  const grow = useProgress(0.2 + i * 0.2, 1.1);

  const isMax = Number(item.value) === max;

  const col = isMax ? th.p.accent : th.p.accent2;

  const v = Number(item.value) || 0;

  const shown = item.display ?? (v * grow).toLocaleString('en-US', {maximumFractionDigits: v % 1 ? 1 : 0});

  return (

    <div style={{position: 'absolute', left: 90, right: 90, top, ...enterStyle(p, 'right', 60)}}>

      <div dir="rtl" style={{...font, fontSize: 48, fontWeight: Math.max(500, th.weight - 200), color: rgba(th.p.text), textShadow: th.shadow, marginBottom: 12}}>{item.label}</div>

      <div style={{position: 'relative', height: 54, borderRadius: 27, background: rgba(th.p.text, 0.12)}}>

        <div style={{position: 'absolute', right: 0, top: BEAT_ZONE.zero, bottom: BEAT_ZONE.zero, width: `${Math.max(2, (v / max) * 100 * grow)}%`, borderRadius: 27, background: `linear-gradient(270deg, ${rgba(col)}, ${rgba(col, 0.7)})`}} />

        <div style={{...font, position: 'absolute', left: 22, top: BEAT_ZONE.zero, bottom: BEAT_ZONE.zero, display: 'flex', alignItems: 'center', fontSize: 48, direction: 'ltr', color: rgba(th.p.text), textShadow: th.shadow}}>{shown}</div>

      </div>

    </div>

  );

};



const BarsBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const th = useTheme();

  const items = (beat.items || []).slice(0, 6);

  const max = Math.max(...items.map((x: any) => Number(x.value) || 0), 1);

  const rowH = 170;

  const top0 = th.zoneCy - (items.length * rowH) / 2 + 20;

  return <AbsoluteFill>{items.map((it: any, i: number) => <BarRow key={i} item={it} i={i} max={max} top={top0 + i * rowH} />)}</AbsoluteFill>;

};



// ------------------------------------------------------------------ خط زمني

const TimelineRow: React.FC<{item: any; i: number; y: number}> = ({item, i, y}) => {

  const th = useTheme();

  const font = useFont();

  const p = useSpring(0.25 + i * 0.4, 'snappy');

  const dot = useSpring(0.2 + i * 0.4, 'bouncy');

  return (

    <>

      <div style={{position: 'absolute', left: 804 - 20, top: y - 20, width: 40, height: 40, borderRadius: '50%', background: rgba(th.p.accent), border: `6px solid ${rgba(th.p.c1)}`, boxShadow: `0 0 0 4px ${rgba(th.p.accent, 0.4)}`, scale: Math.min(1.2, dot), opacity: clamp01(dot * 2)}} />

      <div dir="rtl" style={{position: 'absolute', right: 1080 - 745, left: 80, top: y - 78, textAlign: 'right', ...enterStyle(p, 'left', 50)}}>

        <div style={{...font, fontSize: 84, lineHeight: 1.05, color: rgba(th.p.accent), textShadow: th.shadow}}>{item.year}</div>

        <div style={{...font, fontWeight: Math.max(500, th.weight - 200), fontSize: 48, lineHeight: 1.3, color: rgba(th.p.text), textShadow: th.shadow}}>{item.label}</div>

      </div>

    </>

  );

};



const TimelineBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const th = useTheme();

  const items = (beat.items || []).slice(0, 5);

  const gap = 200;

  const y0 = th.zoneCy - ((items.length - 1) * gap) / 2;

  const line = useProgress(0, 0.5 + items.length * 0.4);

  const h = (items.length - 1) * gap + 60;

  return (

    <AbsoluteFill>

      <div style={{position: 'absolute', left: 804 - 3, top: y0 - 30, width: 6, height: h * line, borderRadius: 3, background: rgba(th.p.accent2, 0.85)}} />

      {items.map((it: any, i: number) => <TimelineRow key={i} item={it} i={i} y={y0 + i * gap} />)}

    </AbsoluteFill>

  );

};



// ------------------------------------------------------------------ مقارنة

const VsCard: React.FC<{item: any; side: 'right' | 'left'; col: RGB}> = ({item, side, col}) => {

  const th = useTheme();

  const font = useFont();

  const p = useSpring(side === 'right' ? 0.1 : 0.3, 'snappy');

  const idle = useIdle(6, 3.6, side === 'right' ? 0 : 2);

  return (

    <div style={{position: 'absolute', top: th.zoneCy - 330 + idle, [side]: 50, width: 465, height: 660, borderRadius: 40, background: rgba(th.p.c1, 0.78), border: `5px solid ${rgba(col)}`, boxShadow: `0 20px 60px ${rgba(col, 0.25)}`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', rowGap: 18, padding: 30, ...enterStyle(p, side === 'right' ? 'right' : 'left', 60)} as React.CSSProperties}>

      {item.icon ? <Icon name={item.icon} size={150} color={rgba(col)} /> : null}

      <div dir="rtl" style={{...font, fontSize: 60, lineHeight: 1.2, textAlign: 'center', color: rgba(th.p.text)}}>{item.title}</div>

      {item.value ? <div style={{...font, fontSize: 110, lineHeight: 1, color: rgba(col), direction: 'ltr'}}>{item.value}</div> : null}

      {item.sub ? <div dir="rtl" style={{...font, fontWeight: Math.max(500, th.weight - 250), fontSize: 48, textAlign: 'center', color: rgba(th.p.text, 0.8)}}>{item.sub}</div> : null}

    </div>

  );

};



const VersusBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const th = useTheme();

  const font = useFont();

  const vs = useSpring(0.55, 'bouncy');

  return (

    <AbsoluteFill>

      <VsCard item={beat.left || {}} side="right" col={th.p.accent} />

      <VsCard item={beat.right || {}} side="left" col={th.p.accent2} />

      <div style={{position: 'absolute', left: 540 - 62, top: th.zoneCy - 62, width: 124, height: 124, borderRadius: '50%', background: rgba(th.p.text), color: rgba(th.p.c1), display: 'flex', alignItems: 'center', justifyContent: 'center', ...font, fontSize: 56, direction: 'ltr', scale: Math.min(1.15, vs), opacity: clamp01(vs * 2), rotate: `${(1 - vs) * -40}deg`, boxShadow: '0 10px 30px rgba(0,0,0,0.35)'}}>VS</div>

    </AbsoluteFill>

  );

};



// ------------------------------------------------------------------ قائمة

const ListRow: React.FC<{item: any; i: number; y: number; height: number}> = ({item, i, y, height}) => {

  const th = useTheme();

  const font = useFont();

  const p = useSpring(0.1 + i * 0.24, 'snappy');

  const chk = useProgress(0.28 + i * 0.24, 0.5);

  const iconBox = Math.min(84, height - 36);

  const iconSize = Math.max(48, iconBox - 28);

  return (

    <div style={{

      position: 'absolute', left: 80, right: 80, top: y, height,

      display: 'flex', alignItems: 'center', columnGap: 26, direction: 'rtl',

      background: rgba(th.p.c1, 0.72), border: `2px solid ${rgba(th.tok(`hl${i}`), 0.35)}`,

      borderRadius: 28, padding: '0 32px', boxShadow: '0 12px 30px rgba(0,0,0,0.25)',

      ...enterStyle(p, 'right', 60)

    }}>

      <div style={{

        width: iconBox, height: iconBox, borderRadius: '50%',

        background: rgba(th.tok(`hl${i}`)), display: 'flex', alignItems: 'center',

        justifyContent: 'center', flex: '0 0 auto', boxShadow: `0 6px 18px ${rgba(th.tok(`hl${i}`), 0.45)}`

      }}>

        <Icon name={item.icon || 'check'} size={iconSize} color={on(th.tok(`hl${i}`))} stroke={2.4} draw={chk} />

      </div>

      <div style={{

        ...font, fontWeight: Math.max(500, th.weight - 150),

        fontSize: 52, lineHeight: 1.25, color: rgba(th.p.text),

        textShadow: th.shadow, flex: 1, wordBreak: 'break-word'

      }}>{item.text}</div>

    </div>

  );

};



const ListBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const th = useTheme();

  const items = (beat.items || []).slice(0, 5);

  const n = Math.max(items.length, 1);

  const topBound = th.st.headline.pos === 'top' ? BEAT_ZONE.list_top_with_headline : BEAT_ZONE.list_top_no_headline;

  const bottomBound = th.capY - 140;

  const totalH = bottomBound - topBound;

  const gap = n <= 3 ? 36 : 24;

  const rowH = Math.min(180, Math.max(130, Math.floor((totalH - (n - 1) * gap) / n)));

  const contentH = n * rowH + (n - 1) * gap;

  const startY = topBound + Math.floor((totalH - contentH) / 2);



  return (

    <AbsoluteFill>

      {items.map((it: any, i: number) => (

        <ListRow key={i} item={it} i={i} y={startY + i * (rowH + gap)} height={rowH} />

      ))}

    </AbsoluteFill>

  );

};



// ------------------------------------------------------------------ أيقونات

const IconCell: React.FC<{item: any; i: number; x: number; y: number}> = ({item, i, x, y}) => {

  const th = useTheme();

  const font = useFont();

  const p = useSpring(0.1 + i * 0.25, 'bouncy');

  const idle = useIdle(9, 3.2, i * 1.3);

  const col = th.tok(`hl${i}`);

  return (

    <div style={{position: 'absolute', left: x - 230, top: y - 200 + idle, width: 460, height: 400, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', rowGap: 18, ...enterStyle(p, 'pop')}}>

      <div style={{width: 230, height: 230, borderRadius: '50%', background: rgba(th.p.c1, 0.6), border: `6px solid ${rgba(col)}`, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: `0 0 60px ${rgba(col, 0.35)}`}}>

        <Icon name={item.icon} size={130} color={rgba(col)} stroke={1.5} />

      </div>

      <div dir="rtl" style={{...font, fontSize: 52, lineHeight: 1.2, textAlign: 'center', color: rgba(th.p.text), textShadow: th.shadow}}>{item.label}</div>

    </div>

  );

};



const IconsBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const th = useTheme();

  const items = (beat.items || []).slice(0, 4);

  const n = items.length;

  const cy = th.zoneCy;

  const pos = (i: number): [number, number] => {

    if (n === 1) return [540, cy];

    if (n === 2) return [i === 0 ? 800 : 280, cy];

    if (n === 3) return [[800, cy - 215], [280, cy - 215], [540, cy + 215]][i] as [number, number];

    return [[800, cy - 215], [280, cy - 215], [800, cy + 215], [280, cy + 215]][i] as [number, number];

  };

  return <AbsoluteFill>{items.map((it: any, i: number) => <IconCell key={i} item={it} i={i} x={pos(i)[0]} y={pos(i)[1]} />)}</AbsoluteFill>;

};



// ------------------------------------------------------------------ كانفس حر: عناصر يرسمها المخرج البصري بالكود

const CanvasEl: React.FC<{el: any; idx: number}> = ({el, idx}) => {

  const th = useTheme();

  const font = useFont();

  const frame = useCurrentFrame();

  const {fps} = useVideoConfig();

  const {settled} = useContext(MotionCtx);

  const p = useSpring(Number(el.delay) || idx * 0.15, el.enter === 'pop' ? 'bouncy' : 'snappy');

  const draw = useProgress(Number(el.delay) || idx * 0.15, 0.8);

  const t = settled ? 0 : frame / fps;

  const col = th.tok(el.color);

  const c = rgba(col);

  const kind: EnterKind = el.enter === 'pop' ? 'pop' : el.enter === 'drop' ? 'drop' : el.enter === 'left' ? 'left' : el.enter === 'right' ? 'right' : el.enter === 'fade' ? 'fade' : 'rise';

  const x = el.x != null ? Number(el.x) : 540;

  const y = el.y != null ? Number(el.y) : 960;

  const loop = el.loop === 'float' ? {translate: `0 ${Math.sin(t * 2) * 12}px`} : el.loop === 'pulse' ? {scale: 1 + 0.06 * Math.sin(t * 3)} : el.loop === 'spin' ? {rotate: `${(t * 40) % 360}deg`} : {};

  const size = Number(el.size) || 80;

  const wrap = (child: React.ReactNode, w = 0, h = 0) => (

    <div style={{position: 'absolute', left: x, top: y, translate: '-50% -50%'}}>

      <div style={{...enterStyle(p, kind, 50)}}>

        <div style={{...loop, width: w || undefined, height: h || undefined}}>{child}</div>

      </div>

    </div>

  );

  const shape = el.shape;

  if (el.type === 'text') {

    const txtStr = String(el.text ?? '');
    const effSize = txtStr.length > 26 ? Math.min(size, 56) : size;
    return wrap(
      <div
        dir="rtl"
        style={{
          ...font,
          fontSize: effSize,
          lineHeight: 1.3,
          color: c,
          textShadow: th.shadow,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          maxWidth: 900,
          width: 'max-content',
          textAlign: 'center',
          fontWeight: Number(el.weight) || th.weight,
        }}
      >
        {txtStr}
      </div>
    );

  }

  if (el.type === 'icon') return wrap(<Icon name={String(el.name || 'star')} size={size} color={c} stroke={Number(el.stroke) || 1.6} />);

  if (el.type === 'line' || el.type === 'arrow') {

    const x2 = Number(el.x2) || x + 200;

    const y2 = Number(el.y2) || y;

    const ang = Math.atan2(y2 - y, x2 - x);

    const hx = (a: number) => x2 - Math.cos(ang + a) * 38;

    const hy = (a: number) => y2 - Math.sin(ang + a) * 38;

    return (

      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, overflow: 'visible'}}>

        <line x1={x} y1={y} x2={x2} y2={y2} stroke={c} strokeWidth={Number(el.stroke) || 10} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - draw} />

        {el.type === 'arrow' && (

          <g opacity={clamp01((draw - 0.7) * 3.4)}>

            <line x1={x2} y1={y2} x2={hx(0.5)} y2={hy(0.5)} stroke={c} strokeWidth={Number(el.stroke) || 10} strokeLinecap="round" />

            <line x1={x2} y1={y2} x2={hx(-0.5)} y2={hy(-0.5)} stroke={c} strokeWidth={Number(el.stroke) || 10} strokeLinecap="round" />

          </g>

        )}

      </svg>

    );

  }

  // أشكال

  const w = Number(el.w) || size;

  const h = Number(el.h) || size;

  let s: React.ReactNode = null;

  if (shape === 'rect') s = <div style={{width: w, height: h, borderRadius: Number(el.r) || 24, background: c}} />;

  else if (shape === 'ring') s = <div style={{width: w, height: w, borderRadius: '50%', border: `${Number(el.stroke) || 12}px solid ${c}`}} />;

  else if (shape === 'tri') s = <svg width={w} height={h} viewBox="0 0 100 100"><polygon points="50,6 96,92 4,92" fill={c} /></svg>;

  else if (shape === 'star') s = <svg width={w} height={w} viewBox="0 0 24 24"><path d="M12 2l3 7 7.5.6-5.7 4.9 1.8 7.3L12 17.8 5.4 21.8l1.8-7.3L1.5 9.6 9 9z" fill={c} /></svg>;

  else s = <div style={{width: w, height: w, borderRadius: '50%', background: c}} />;

  return wrap(s);

};



const CanvasBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const els = (beat.elements || []).slice(0, 14);

  return <AbsoluteFill>{els.map((el: any, i: number) => <CanvasEl key={i} el={el} idx={i} />)}</AbsoluteFill>;

};



// ------------------------------------------------------------------ مقارنة عمودية (لوحتان)

const SplitPanel: React.FC<{data: any; side: 'screen-right' | 'screen-left'; col: RGB}> = ({data, side, col}) => {

  const th = useTheme();

  const font = useFont();

  const p = useSpring(side === 'screen-right' ? 0.08 : 0.22, 'snappy');

  const W = 478;

  const x = side === 'screen-right' ? 1080 - 60 - W : 60;

  const enterDir: EnterKind = side === 'screen-right' ? 'left' : 'right';

  return (

    <div style={{position: 'absolute', top: th.zoneCy - 320, left: x, width: W, height: 640, borderRadius: 36, background: rgba(th.p.c1, 0.72), border: `4px solid ${rgba(col, 0.75)}`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 20, padding: 28, ...enterStyle(p, enterDir, 60)}}>

      {data.icon ? <Icon name={data.icon} size={110} color={rgba(col)} /> : null}

      <div dir="rtl" style={{...font, fontSize: 56, lineHeight: 1.2, color: rgba(th.p.text), textAlign: 'center', textShadow: th.shadow}}>{data.title || ''}</div>

      {data.value ? <div style={{...font, fontSize: 96, color: rgba(col), direction: 'ltr', lineHeight: 1}}>{data.value}</div> : null}

      {data.sub ? <div dir="rtl" style={{...font, fontSize: 48, color: rgba(th.p.text, 0.78), textAlign: 'center'}}>{data.sub}</div> : null}

    </div>

  );

};



const SplitBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const th = useTheme();

  // beat.left (Arabic first/semantic-left) appears on screen-right (RTL convention)

  return (

    <AbsoluteFill>

      <SplitPanel data={(beat.left as any) || {}} side="screen-right" col={th.p.accent} />

      <SplitPanel data={(beat.right as any) || {}} side="screen-left" col={th.p.accent2} />

      <div style={{position: 'absolute', left: 536, top: th.zoneCy - 50, width: 8, height: 100, borderRadius: 4, background: rgba(th.p.text, 0.28)}} />

    </AbsoluteFill>

  );

};



// ------------------------------------------------------------------ شريط أخبار متحرك

const TickerBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const th = useTheme();

  const font = useFont();

  const frame = useCurrentFrame();

  const items: any[] = (beat.items || []).slice(0, 8);

  const p = useSpring(0, 'smooth');

  if (!items.length) return null;

  const speed = 3.2; // بكسل/إطار

  const totalW = items.length * 580;

  const offset = (frame * speed) % (totalW + 20);

  return (

    <AbsoluteFill>

      <AccentShapes seed={beat.from + 5} count={2} />

      {beat.title ? (

        <div style={{position: 'absolute', left: 80, right: 80, top: th.zoneCy - 240, textAlign: 'center', ...enterStyle(p, 'rise', 36)}}>

          <div dir="rtl" style={{...font, fontSize: 64, fontWeight: th.weight, color: rgba(th.p.text), textShadow: th.shadow}}>{beat.title}</div>

        </div>

      ) : null}

      <div style={{position: 'absolute', top: th.zoneCy - 50, left: 0, right: 0, height: 156, overflow: 'hidden', borderTop: `3px solid ${rgba(th.p.accent, 0.5)}`, borderBottom: `3px solid ${rgba(th.p.accent, 0.5)}`}}>

        <div style={{position: 'absolute', top: BEAT_ZONE.zero, bottom: BEAT_ZONE.zero, display: 'flex', alignItems: 'center', gap: 32, transform: `translateX(-${offset}px)`}}>

          {[...items, ...items, ...items].map((it, i) => (

            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 18, background: rgba(th.p.c1, 0.7), borderRadius: 24, padding: '14px 32px', border: `2px solid ${rgba(th.p.accent2, 0.5)}`, flexShrink: 0}}>

              {it.icon ? <Icon name={it.icon} size={60} color={rgba(th.p.accent)} /> : null}

              <div dir="rtl" style={{...font, fontSize: 50, color: rgba(th.p.text), whiteSpace: 'nowrap', textShadow: th.shadow}}>{it.text || ''}</div>

            </div>

          ))}

        </div>

        <div style={{position: 'absolute', top: BEAT_ZONE.zero, bottom: BEAT_ZONE.zero, left: 0, width: 70, background: `linear-gradient(90deg, ${rgba(th.p.c1)}, transparent)`}} />

        <div style={{position: 'absolute', top: BEAT_ZONE.zero, bottom: BEAT_ZONE.zero, right: 0, width: 70, background: `linear-gradient(270deg, ${rgba(th.p.c1)}, transparent)`}} />

      </div>

    </AbsoluteFill>

  );

};



// ------------------------------------------------------------------ مكدّس بطاقات (card stack)

const CardItem: React.FC<{item: any; i: number; n: number}> = ({item, i, n}) => {

  const th = useTheme();

  const font = useFont();

  const p = useSpring(0.1 + i * 0.28, 'bouncy');

  const col = th.tok(`hl${i}`);

  return (

    <div style={{position: 'absolute', left: 80, right: 80, top: th.zoneCy - 300 + i * 58, height: 196, borderRadius: 32, background: rgba(th.p.c1, Math.max(0.35, 0.82 - i * 0.1)), border: `3px solid ${rgba(col, 0.8)}`, display: 'flex', alignItems: 'center', gap: 28, padding: '0 36px', zIndex: n - i, ...enterStyle(p, 'rise', 40 + i * 18)}}>

      {item.icon ? <div style={{flex: '0 0 auto'}}><Icon name={item.icon} size={78} color={rgba(col)} /></div> : null}

      <div dir="rtl" style={{...font, fontSize: 52, lineHeight: 1.3, color: rgba(th.p.text), flex: 1, textShadow: th.shadow}}>{item.text || ''}</div>

      {item.value ? <div style={{...font, fontSize: 70, color: rgba(col), direction: 'ltr', flex: '0 0 auto'}}>{item.value}</div> : null}

    </div>

  );

};



const CardStackBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const items: any[] = (beat.items || []).slice(0, 4);

  return <AbsoluteFill>{items.map((it, i) => <CardItem key={i} item={it} i={i} n={items.length} />)}</AbsoluteFill>;

};



// ------------------------------------------------------------------ توزيع


// ------------------------------------------------------------------ مقاطع SVG الحديثة
/** Animated ripple ring around a map pin */
const PinRipple: React.FC<{x: number; y: number; color: string; delay?: number}> = ({x, y, color, delay = 0}) => {
  const frame = useCurrentFrame();
  const t = Math.max(0, frame - delay);
  const cycle = t % 45;
  const prog = cycle / 45;
  const r = 28 + 60 * prog;
  const opacity = (1 - prog) * 0.55;
  return (
    <svg style={{position: 'absolute', inset: 0, width: 1080, height: 1920, pointerEvents: 'none', zIndex: 6}}>
      <circle cx={x} cy={y} r={r} fill="none" stroke={color} strokeWidth={3} opacity={opacity} />
    </svg>
  );
};

const MapPinBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const frame = useCurrentFrame();
  const region = beat.region || 'egypt';
  const points = (beat.points || [
    {name: 'المدينة', x: 540, y: 870},
  ]) as Array<{name?: string; x: number; y: number; icon?: string}>;

  // When Python has computed a real GeoJSON view, render real SVG country paths
  const view = beat.view as any;
  const hasRealMap = view && view.ctx && view.hl;

  const mapSrc = staticFile(`maps/${region}.svg`);

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      {hasRealMap ? (
        /* Real GeoJSON paths projected to SVG — same renderer as MapBeat */
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          {/* Context countries (neighbours, faded) */}
          <path d={view.ctx} fillRule="evenodd" fill={rgba(th.p.ctx, th.st.map.ctx_alpha * 0.7)} />
          <path d={view.ctx} fillRule="evenodd" fill="none" stroke={rgba(th.p.ctx_edge, 0.6)} strokeWidth={1.5} />
          {/* Highlighted countries */}
          {(view.hl as any[]).map((h: any, i: number) => (
            <HlCountry key={h.iso ?? i} h={h} i={i} />
          ))}
        </svg>
      ) : (
        /* Fallback: static pre-made SVG map */
        <div style={{position: 'absolute', inset: 0, opacity: 0.38, filter: 'contrast(1.2) brightness(0.65)'}}>
          <SafeImg src={mapSrc} fallbackSrc={staticFile('maps/world.svg')} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
        </div>
      )}

      <MapOverlay opacity={hasRealMap ? 0.55 : 0.78} />
      <FireSparks n={20} />

      {beat.title && (
        <div style={{position: 'absolute', left: 60, right: 60, top: BEAT_ZONE.title_top, textAlign: 'center', zIndex: 10}}>
          <GlowText fontSize={beat.title.length > 22 ? 58 : 68} gold={false}>{beat.title}</GlowText>
        </div>
      )}

      {/* Animated arrows between pins */}
      {points.length > 1 && points.slice(1).map((pt, i) => (
        <ArrowFlow
          key={i}
          from={{x: points[i].x, y: points[i].y}}
          to={{x: pt.x, y: pt.y}}
          color={rgba(th.p.accent2)}
          curvature={28}
          delay={10 + i * 8}
        />
      ))}

      {/* Ripple rings */}
      {points.map((pt, i) => (
        <PinRipple key={i} x={pt.x} y={pt.y} color={rgba(i % 2 === 0 ? th.p.accent : th.p.accent2)} delay={i * 6} />
      ))}

      {/* Pin badges */}
      {points.map((pt, i) => {
        const pinPop = useSpring(0.1 + i * 0.15, 'bouncy');
        const iconPath = pt.icon || 'icons/map/map_pin.svg';
        const pinCol = rgba(i % 2 === 0 ? th.p.accent : th.p.accent2);
        const pinColA65 = rgba(i % 2 === 0 ? th.p.accent : th.p.accent2, 0.65);
        const pinColA07 = rgba(i % 2 === 0 ? th.p.accent : th.p.accent2, 0.7);
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: pt.x - 52,
              top: pt.y - 52,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              transform: `scale(${pinPop})`,
              zIndex: 8,
            }}
          >
            <div
              style={{
                width: 104,
                height: 104,
                borderRadius: '50%',
                background: 'radial-gradient(circle at 35% 35%, rgba(45, 55, 72, 0.92), rgba(10, 14, 26, 0.97))',
                border: `3px solid ${pinCol}`,
                boxShadow: `0 0 22px ${pinColA65}, 0 8px 20px rgba(0,0,0,0.7)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <SafeImg src={staticFile(iconPath)} fallbackSrc={staticFile('icons/map/pin.svg')} style={{width: 58, height: 58, objectFit: 'contain'}} />
            </div>
            {pt.name && (
              <div
                style={{
                  marginTop: 8,
                  padding: '5px 18px',
                  borderRadius: 20,
                  background: 'rgba(8, 12, 22, 0.92)',
                  border: `1.5px solid ${pinColA07}`,
                  fontFamily: th.family,
                  fontSize: 26,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  whiteSpace: 'nowrap',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                }}
              >
                {pt.name}
              </div>
            )}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const TimelineCardBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const items: any[] = (beat.items || [
    {year: '٦٤١ م', label: 'الفتح وتأسيس الفسطاط', icon: 'icons/history/castle.svg'},
    {year: '٩٦٩ م', label: 'بناء القاهرة المعزية', icon: 'icons/building/mosque.svg'},
    {year: '١٨٠٥ م', label: 'عصر محمد علي وتحديث العاصمة', icon: 'icons/crown/crown.svg'},
  ]).slice(0, 4);

  const lineProgress = useProgress(0.1, 1.2);
  const totalH = items.length * 200;
  const startY = th.zoneCy - totalH / 2 + 60;

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <MapOverlay opacity={0.6} />
      <FireSparks n={18} />

      {beat.title && (
        <div style={{position: 'absolute', left: 60, right: 60, top: BEAT_ZONE.sub_title_top, textAlign: 'center', zIndex: 10}}>
          <GlowText fontSize={62} gold={false}>{beat.title}</GlowText>
        </div>
      )}

      <svg
        width={1080}
        height={1920}
        style={{position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 4}}
      >
        <line
          x1={220}
          y1={startY}
          x2={220}
          y2={startY + totalH}
          stroke={rgba(th.p.accent, 0.3)}
          strokeWidth={6}
          strokeLinecap="round"
        />
        <line
          x1={220}
          y1={startY}
          x2={220}
          y2={startY + totalH * lineProgress}
          stroke={rgba(th.p.accent)}
          strokeWidth={6}
          strokeLinecap="round"
          filter={`drop-shadow(0 0 10px ${rgba(th.p.accent)})`}
        />
        <circle
          cx={220}
          cy={startY + totalH * lineProgress}
          r={10}
          fill={rgba(th.p.accent, 0.8)}
          filter={`drop-shadow(0 0 12px ${rgba(th.p.accent)})`}
        />
      </svg>

      <div style={{position: 'absolute', inset: 0, zIndex: 6}}>
        {items.map((it, i) => {
          const itemY = startY + i * 200;
          const pop = useSpring(0.15 + i * 0.18, 'bouncy');
          const iconSrc = staticFile(it.icon || 'icons/time/history_clock.svg');
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: 170,
                top: itemY - 45,
                display: 'flex',
                alignItems: 'center',
                gap: 28,
                transform: `scale(${pop})`,
              }}
            >
              <div
                style={{
                  width: 96,
                  height: 96,
                  borderRadius: '50%',
                  background: 'radial-gradient(circle at 35% 35%, #2a3342, #0f172a)',
                  border: `3px solid ${rgba(th.p.accent)}`,
                  boxShadow: `0 0 20px ${rgba(th.p.accent, 0.4)}, 0 8px 18px rgba(0,0,0,0.6)`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <SafeImg src={iconSrc} fallbackSrc={staticFile('icons/time/clock.svg')} style={{width: 52, height: 52, objectFit: 'contain'}} />
              </div>

              <div
                dir="rtl"
                style={{
                  padding: '14px 28px',
                  borderRadius: 24,
                  background: 'rgba(15, 23, 42, 0.88)',
                  border: `1.5px solid ${rgba(th.p.accent, 0.4)}`,
                  boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                  minWidth: 460,
                  maxWidth: 700,
                  backdropFilter: 'blur(14px)',
                }}
              >
                {it.year && (
                  <div
                    style={{
                      fontFamily: th.family,
                      fontSize: 34,
                      fontWeight: 900,
                      color: rgba(th.p.accent),
                      marginBottom: 4,
                      letterSpacing: '0.02em',
                      textShadow: `0 2px 8px ${rgba(th.p.accent, 0.5)}`,
                    }}
                  >
                    {it.year}
                  </div>
                )}
                <div
                  style={{
                    fontFamily: th.family2 || th.family,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  {it.label || it.text || ''}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const StatRingV2Beat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const p = useProgress(0.12, 1.4);
  const a = useSpring(0.08, 'bouncy');
  const cy = th.zoneCy - 60;
  const s = String(beat.number ?? '');
  const pn = parseNum(s);
  const show = pn ? pn.pre + (pn.commas ? (pn.val * p).toLocaleString('en-US', {minimumFractionDigits: pn.dec, maximumFractionDigits: pn.dec}) : (pn.val * p).toFixed(pn.dec)) + pn.suf : s;

  const R = 230;
  const C = 2 * Math.PI * R;
  const iconPath = beat.icon || 'icons/coin/gold_bars.svg';
  const iconSrc = staticFile(iconPath);

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <MapOverlay opacity={0.6} />
      <FireSparks n={20} />

      <svg
        width={1080}
        height={1920}
        style={{position: 'absolute', inset: 0, opacity: clamp01(a * 1.5)}}
      >
        <defs>
          <linearGradient id="ringGradV2" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={rgba(th.p.accent, 0.6)} />
            <stop offset="50%" stopColor={rgba(th.p.accent)} />
            <stop offset="100%" stopColor={rgba(th.p.accent2)} />
          </linearGradient>
          <filter id="ringGlowV2" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="16" floodColor={rgba(th.p.accent)} floodOpacity="0.8" />
          </filter>
        </defs>
        <circle cx={540} cy={cy - 120} r={R} fill="none" stroke="rgba(255, 255, 255, 0.12)" strokeWidth={16} />
        <circle
          cx={540}
          cy={cy - 120}
          r={R}
          fill="none"
          stroke="url(#ringGradV2)"
          strokeWidth={18}
          strokeLinecap="round"
          strokeDasharray={C}
          strokeDashoffset={C * (1 - p)}
          transform={`rotate(-90 540 ${cy - 120})`}
          filter="url(#ringGlowV2)"
        />
      </svg>

      <div
        style={{
          position: 'absolute',
          left: 540 - 100,
          top: cy - 120 - 100,
          width: 200,
          height: 200,
          borderRadius: '50%',
          background: 'radial-gradient(circle at 35% 35%, rgba(45, 55, 72, 0.7), rgba(15, 23, 42, 0.85))',
          border: `2px solid ${rgba(th.p.accent, 0.5)}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backdropFilter: 'blur(10px)',
          ...enterStyle(a, 'pop'),
        }}
      >
        <SafeImg src={iconSrc} fallbackSrc={staticFile('icons/star/star.svg')} style={{width: 120, height: 120, objectFit: 'contain'}} />
      </div>

      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: cy + 150,
          textAlign: 'center',
          ...enterStyle(a, 'rise', 40),
        }}
      >
        <GlowText fontSize={130} gold={false}>
          {show}
        </GlowText>
      </div>

      {beat.label && (
        <div
          dir="rtl"
          style={{
            position: 'absolute',
            left: 90,
            right: 90,
            top: cy + 320,
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              padding: '12px 36px',
              borderRadius: 30,
              background: 'rgba(15, 23, 42, 0.85)',
              border: `1.5px solid ${rgba(th.p.accent, 0.5)}`,
              fontFamily: th.family,
              fontSize: 48,
              fontWeight: 700,
              color: '#FFFFFF',
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              textShadow: th.shadow,
            }}
          >
            {beat.label}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ مخطط الارتفاع (جبل فوق سطح البحر)

export const ElevationProfileBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const uid = useId().replace(/:/g, '');

  const SEA_Y = BEAT_ZONE.sea_y;
  const PEAK_Y = BEAT_ZONE.peak_y;
  const CX = 540;

  const mountainProg = useProgress(0, 0.65);
  const seaProg = useProgress(0.35, 0.4);
  const heightProg = useProgress(cueSecOf(beat, 'metric_start', 0.55), 1.1);

  const clipY = interpolate(mountainProg, [0, 1], [SEA_Y, PEAK_Y - 20], {extrapolateRight: 'clamp'});
  const lineY = interpolate(heightProg, [0, 1], [SEA_Y, PEAK_Y], {extrapolateRight: 'clamp'});

  const h_str = String(beat.height || '0');
  const pn = parseNum(h_str);
  const hVal = pn ? Math.round(pn.val * Math.min(1, heightProg)) : 0;
  const hShow = hVal.toLocaleString('en-US');

  const unit = String(beat.unit || 'م');
  const seaLabel = String(beat.sea_label || 'سطح البحر');

  const mPath = `M 160 ${SEA_Y} C 250 ${SEA_Y} 390 980 500 700 C 520 600 530 490 ${CX} ${PEAK_Y} C 550 490 560 600 580 700 C 690 980 830 ${SEA_Y} 920 ${SEA_Y} Z`;
  const accentC = rgba(th.p.accent);
  const accent2C = rgba(th.p.accent2);
  const textC = rgba(th.p.text);

  return (
    <AbsoluteFill>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <defs>
          <linearGradient id={`${uid}g`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={accentC} stopOpacity="0.85" />
            <stop offset="65%" stopColor={accent2C} stopOpacity="0.6" />
            <stop offset="100%" stopColor={accent2C} stopOpacity="0.2" />
          </linearGradient>
          <clipPath id={`${uid}c`}>
            <rect x={0} y={clipY} width={1080} height={SEA_Y - clipY + 60} />
          </clipPath>
          <filter id={`${uid}f`} x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="-6" stdDeviation="20" floodColor={accentC} floodOpacity="0.5" />
          </filter>
        </defs>

        {/* Mountain body */}
        <path d={mPath} fill={`url(#${uid}g)`} clipPath={`url(#${uid}c)`} filter={`url(#${uid}f)`} />
        <path d={mPath} fill="none" stroke={rgba(th.p.accent, 0.45)} strokeWidth={3} clipPath={`url(#${uid}c)`} />
        {/* Snow cap */}
        <ellipse cx={CX} cy={PEAK_Y + 24} rx={58} ry={22} fill="rgba(235,248,255,0.9)" clipPath={`url(#${uid}c)`} />

        {/* Sea level horizontal line */}
        <line x1={80} y1={SEA_Y} x2={1000} y2={SEA_Y}
          stroke={accent2C} strokeWidth={4} strokeLinecap="round"
          opacity={Math.min(1, seaProg * 2.5)} />

        {/* Dashed height indicator line rising from sea to peak */}
        {heightProg > 0.01 && (
          <line x1={CX} y1={SEA_Y} x2={CX} y2={lineY}
            stroke={textC} strokeWidth={3}
            strokeDasharray="14 10" strokeLinecap="round" opacity={0.7} />
        )}

        {/* Tick marks at 25%, 50%, 75% of height */}
        {([0.25, 0.5, 0.75] as number[]).map((frac, i) => {
          const tickY = SEA_Y - (SEA_Y - PEAK_Y) * frac;
          const op = Math.max(0, Math.min(0.5, (heightProg - frac) * 4));
          return op > 0 ? (
            <line key={i} x1={CX - 24} y1={tickY} x2={CX + 24} y2={tickY}
              stroke={textC} strokeWidth={2} opacity={op} />
          ) : null;
        })}

        {/* Sea level label */}
        {seaProg > 0.3 && (
          <text x={96} y={SEA_Y - 14} fontSize={34} fontWeight={700}
            fill={accent2C} opacity={Math.min(1, (seaProg - 0.3) * 4)}
            fontFamily={th.family} textAnchor="start">
            {seaLabel} = 0 م
          </text>
        )}
      </svg>

      {/* Peak name */}
      {beat.title && mountainProg > 0.72 && (
        <div style={{
          position: 'absolute', left: 80, right: 80, top: PEAK_Y - 90,
          textAlign: 'center', ...font, fontSize: 60, fontWeight: 900,
          color: textC, textShadow: th.shadow, direction: 'rtl',
          opacity: Math.min(1, (mountainProg - 0.72) * 4),
          translate: `0 ${(1 - Math.min(1, (mountainProg - 0.72) * 4)) * -20}px`,
        }}>
          {beat.title}
        </div>
      )}

      {/* Floating height counter badge alongside the dashed line */}
      {heightProg > 0.04 && (
        <div style={{
          position: 'absolute',
          left: CX + 28,
          top: lineY - 46,
          transform: `scale(${Math.min(1, heightProg * 2.5)})`,
          transformOrigin: 'left center',
        }}>
          <div style={{
            display: 'inline-flex', alignItems: 'baseline', gap: 8,
            padding: '8px 24px',
            borderRadius: 32,
            background: 'rgba(8, 12, 24, 0.9)',
            border: `2px solid ${accentC}`,
            boxShadow: `0 0 20px ${rgba(th.p.accent, 0.5)}`,
            whiteSpace: 'nowrap',
          }}>
            <span style={{...font, fontSize: 72, color: accentC, direction: 'ltr', lineHeight: 1}}>{hShow}</span>
            <span style={{...font, fontSize: 38, color: textC, lineHeight: 1}}>{unit}</span>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ مخطط خطي (سلسلة زمنية)

const LineChartBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const uid = useId().replace(/:/g, '');

  const points: {label: string; value: number}[] = Array.isArray(beat.points) ? beat.points : [];
  if (points.length < 2) return null as any;

  const maxVal = Math.max(...points.map(p => p.value));
  const minVal = Math.min(...points.map(p => p.value));
  const range = maxVal - minVal || 1;

  // Canvas area inside the full 1080×1920 frame
  const PAD_L = 120, PAD_R = 60, PAD_T = 580, PAD_B = 1300;
  const W = 1080 - PAD_L - PAD_R;  // 900
  const H = PAD_B - PAD_T;          // 720

  const nx = (i: number) => PAD_L + (i / (points.length - 1)) * W;
  const ny = (v: number) => PAD_B - ((v - minVal) / range) * H;

  const polyPts = points.map((p, i) => `${nx(i).toFixed(1)},${ny(p.value).toFixed(1)}`).join(' ');
  const areaPath = `M ${nx(0).toFixed(1)},${PAD_B} ` +
    points.map((p, i) => `L ${nx(i).toFixed(1)},${ny(p.value).toFixed(1)}`).join(' ') +
    ` L ${nx(points.length - 1).toFixed(1)},${PAD_B} Z`;

  const gridProg = useProgress(cueSecOf(beat, 'grid_enter', 0.4), 0.4);
  const lineProg = useProgress(cueSecOf(beat, 'line_draw', 0.65), 0.9);
  const dotsProg = useProgress(cueSecOf(beat, 'dots_pop', 0.9), 0.5);
  const titleProg = useSpring(0.1, 'smooth');

  const accentC = rgba(th.p.accent);
  const accent2C = rgba(th.p.accent2);
  const textC = rgba(th.p.text);
  const lineLen = lineProg;  // 0→1 drives stroke-dashoffset

  // Approximate total polyline length for dasharray
  const totalLen = points.reduce((sum, p, i) => {
    if (i === 0) return 0;
    const dx = nx(i) - nx(i - 1);
    const dy = ny(p.value) - ny(points[i - 1].value);
    return sum + Math.sqrt(dx * dx + dy * dy);
  }, 0) || 1000;

  return (
    <AbsoluteFill>
      {/* Title */}
      {beat.title && (
        <div style={{
          position: 'absolute', left: BEAT_ZONE.left, right: BEAT_ZONE.right, top: BEAT_ZONE.chart_title_top,
          textAlign: 'center', ...font, fontSize: 58, fontWeight: 900,
          color: textC, textShadow: th.shadow, direction: 'rtl',
          ...enterStyle(titleProg, 'rise', 40),
        }}>{beat.title}</div>
      )}

      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <defs>
          <linearGradient id={`${uid}ag`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={accentC} stopOpacity="0.35" />
            <stop offset="100%" stopColor={accentC} stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Horizontal grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((frac, gi) => {
          const gy = PAD_B - frac * H;
          const gVal = minVal + frac * range;
          const op = gridProg * 0.35;
          return op > 0.01 ? (
            <g key={gi} opacity={op}>
              <line x1={PAD_L} y1={gy} x2={PAD_L + W} y2={gy} stroke={textC} strokeWidth={1.5} />
              <text x={PAD_L - 10} y={gy + 6} fontSize={28} fill={textC} textAnchor="end" fontFamily={th.family}>
                {gVal % 1 === 0 ? gVal.toFixed(0) : gVal.toFixed(1)}
              </text>
            </g>
          ) : null;
        })}

        {/* Area fill */}
        {lineProg > 0.01 && (
          <path d={areaPath} fill={`url(#${uid}ag)`} opacity={lineProg * 0.8} />
        )}

        {/* Animated line */}
        <polyline
          points={polyPts}
          fill="none"
          stroke={accentC}
          strokeWidth={6}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={`${totalLen} ${totalLen}`}
          strokeDashoffset={totalLen * (1 - lineLen)}
        />

        {/* Data point dots + labels */}
        {points.map((p, i) => {
          const px = nx(i), py = ny(p.value);
          const delay = 0.1 + i * 0.08;
          const dp = Math.max(0, Math.min(1, (dotsProg - delay + 0.1) * 5));
          if (dp < 0.01) return null;
          const above = py > PAD_T + 80;
          return (
            <g key={i} opacity={dp}>
              <circle cx={px} cy={py} r={12 * dp} fill={accentC} />
              <circle cx={px} cy={py} r={6} fill="rgba(255,255,255,0.9)" />
              {/* X-axis label */}
              <text x={px} y={PAD_B + 40} fontSize={30} fill={textC} textAnchor="middle" fontFamily={th.family}>{p.label}</text>
              {/* Value label above/below dot */}
              <text x={px} y={above ? py - 20 : py + 48} fontSize={32} fontWeight={700} fill={accentC} textAnchor="middle" fontFamily={th.family}>
                {p.value % 1 === 0 ? p.value.toFixed(0) : p.value.toFixed(1)}
                {beat.y_label ? ` ${beat.y_label}` : ''}
              </text>
            </g>
          );
        })}

        {/* Y-axis line */}
        <line x1={PAD_L} y1={PAD_T - 20} x2={PAD_L} y2={PAD_B + 10} stroke={textC} strokeWidth={2} opacity={gridProg * 0.5} />
        {/* X-axis line */}
        <line x1={PAD_L - 10} y1={PAD_B} x2={PAD_L + W} y2={PAD_B} stroke={textC} strokeWidth={2} opacity={gridProg * 0.5} />
      </svg>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ مخطط دائري (توزيع نسبي)

const PieChartBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();

  const items: {label: string; value: number}[] = Array.isArray(beat.items) ? beat.items : [];
  if (items.length < 2) return null as any;

  const total = items.reduce((s, it) => s + it.value, 0) || 100;

  // 5 accent colors cycling: accent, accent2, hl0..hl2
  const COLORS_FN = (i: number) => {
    const palette = [th.p.accent, th.p.accent2, ...(th.p.hl || [])];
    return rgba(palette[i % palette.length]);
  };

  const CX = 540, CY = 900, R = 300, HOLE = 160;

  const segProg = useProgress(cueSecOf(beat, 'seg_enter', 0.3), 1.0);
  const labelProg = useProgress(cueSecOf(beat, 'labels_enter', 0.8), 0.6);
  const titleProg = useSpring(0.05, 'smooth');

  // Build arc paths
  let angle = -Math.PI / 2;  // start at top
  const segments = items.map((it, i) => {
    const frac = it.value / total;
    const startA = angle;
    const endA = angle + 2 * Math.PI * frac;
    angle = endA;
    const midA = (startA + endA) / 2;
    // arc path
    const x1 = CX + R * Math.cos(startA), y1 = CY + R * Math.sin(startA);
    const x2 = CX + R * Math.cos(endA), y2 = CY + R * Math.sin(endA);
    const hx1 = CX + HOLE * Math.cos(startA), hy1 = CY + HOLE * Math.sin(startA);
    const hx2 = CX + HOLE * Math.cos(endA), hy2 = CY + HOLE * Math.sin(endA);
    const large = frac > 0.5 ? 1 : 0;
    const path = `M ${hx1.toFixed(1)},${hy1.toFixed(1)} L ${x1.toFixed(1)},${y1.toFixed(1)} A ${R},${R} 0 ${large},1 ${x2.toFixed(1)},${y2.toFixed(1)} L ${hx2.toFixed(1)},${hy2.toFixed(1)} A ${HOLE},${HOLE} 0 ${large},0 ${hx1.toFixed(1)},${hy1.toFixed(1)} Z`;
    // label position outside pie
    const LR = R + 90;
    const lx = CX + LR * Math.cos(midA), ly = CY + LR * Math.sin(midA);
    return {path, color: COLORS_FN(i), lx, ly, midA, frac, label: it.label, value: it.value};
  });

  const textC = rgba(th.p.text);

  return (
    <AbsoluteFill>
      {/* Title */}
      {beat.title && (
        <div style={{
          position: 'absolute', left: BEAT_ZONE.left, right: BEAT_ZONE.right, top: BEAT_ZONE.chart_title_top,
          textAlign: 'center', ...font, fontSize: 58, fontWeight: 900,
          color: textC, textShadow: th.shadow, direction: 'rtl',
          ...enterStyle(titleProg, 'rise', 40),
        }}>{beat.title}</div>
      )}

      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        {segments.map((seg, i) => {
          const delay = i * (0.9 / items.length);
          const sp = Math.max(0, Math.min(1, (segProg - delay) * (items.length + 1)));
          const lp = Math.max(0, Math.min(1, (labelProg - i * 0.1) * 4));
          if (sp < 0.01) return null;

          // Animate segment scale from center
          const scale = 0.3 + 0.7 * sp;
          return (
            <g key={i} transform={`translate(${CX * (1 - scale)},${CY * (1 - scale)}) scale(${scale})`} opacity={sp}>
              <path d={seg.path} fill={seg.color} />
            </g>
          );
        })}

        {/* Labels with leader lines */}
        {segments.map((seg, i) => {
          const lp = Math.max(0, Math.min(1, (labelProg - i * 0.08) * 5));
          if (lp < 0.01) return null;
          // line from pie edge to label
          const edgeX = CX + (R + 20) * Math.cos(seg.midA);
          const edgeY = CY + (R + 20) * Math.sin(seg.midA);
          const anchor = seg.lx > CX ? 'start' : 'end';
          return (
            <g key={i} opacity={lp}>
              <line x1={edgeX.toFixed(1)} y1={edgeY.toFixed(1)} x2={seg.lx.toFixed(1)} y2={seg.ly.toFixed(1)}
                stroke={seg.color} strokeWidth={3} />
              <text x={(seg.lx + (seg.lx > CX ? 16 : -16)).toFixed(1)} y={(seg.ly + 6).toFixed(1)}
                fontSize={30} fontWeight={700} fill={seg.color} textAnchor={anchor} fontFamily={th.family}>
                {seg.label}
              </text>
              <text x={(seg.lx + (seg.lx > CX ? 16 : -16)).toFixed(1)} y={(seg.ly + 44).toFixed(1)}
                fontSize={26} fill={textC} textAnchor={anchor} fontFamily={th.family}>
                {seg.value.toFixed(1)}%
              </text>
            </g>
          );
        })}

        {/* Center donut label (biggest segment) */}
        {segProg > 0.6 && (() => {
          const biggest = items.reduce((m, it) => it.value > m.value ? it : m, items[0]);
          return (
            <g opacity={Math.min(1, (segProg - 0.6) * 3)}>
              <text x={CX} y={CY - 20} fontSize={34} fill={textC} textAnchor="middle" fontFamily={th.family}>{biggest.label}</text>
              <text x={CX} y={CY + 32} fontSize={52} fontWeight={900} fill={rgba(th.p.accent)} textAnchor="middle" fontFamily={th.family}>
                {biggest.value.toFixed(0)}%
              </text>
            </g>
          );
        })()}
      </svg>
    </AbsoluteFill>
  );
};

export const BeatView: React.FC<{beat: Beat}> = ({beat}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // If this beat has its own AI-generated bespoke TSX component, render it inside a clipped slot above captions
  const DynamicComp = beat.tsx_id ? DYNAMIC_SCENE_REGISTRY[beat.tsx_id] : undefined;
  if (DynamicComp) {
    return (
      <SlotContainer slot="FULL_STAGE" fullCanvas clip>
        <DynamicComp frame={frame} fps={fps} dur={beat.dur || 90} />
      </SlotContainer>
    );
  }

  let body: React.ReactNode;

  switch (beat.kind) {
    case 'area_map': body = <AreaMapBeat beat={beat} />; break;
    case 'map_pin': body = <MapPinBeat beat={beat} />; break;
    case 'timeline_card': body = <TimelineCardBeat beat={beat} />; break;
    case 'stat_ring_v2': body = <StatRingV2Beat beat={beat} />; break;
    case 'elevation_profile': body = <ElevationProfileBeat beat={beat} />; break;
    case 'versus_battle': body = <VersusBattleBeat beat={beat} />; break;
    case 'animated_route': body = <AnimatedRouteBeat beat={beat} />; break;
    case 'balance_meter': body = <BalanceMeterBeat beat={beat} />; break;
    case 'deep_time_slider': body = <DeepTimeSliderBeat beat={beat} />; break;
    case 'stack_pyramid': body = <StackPyramidBeat beat={beat} />; break;
    case 'macro_zoom_globe': body = <MacroZoomGlobeBeat beat={beat} />; break;
    case 'subsurface_mine': body = <SubsurfaceMineBeat beat={beat} />; break;
    case 'dot_matrix_population': body = <DotMatrixPopulationBeat beat={beat} />; break;
    case 'money_waterfall': body = <MoneyWaterfallBeat beat={beat} />; break;
    case 'frontline_clash': body = <FrontlineClashBeat beat={beat} />; break;
    case 'generative_canvas': body = <GenerativeCanvasBeat beat={beat} />; break;
    case 'custom_scene': body = <GenerativeCanvasBeat beat={beat} />; break;
    case 'cinematic_dramatic':
    case 'architectural_blueprint':
    case 'celestial_constellation':
    case 'kinetic_wave_field':
    case 'radial_light_cathedral':
    case 'topographic_contour':
      body = <GenerativeCanvasBeat beat={beat} />; break;
    case 'chart': body = beat.spec ? <AbsoluteFill style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}><ChartVisual spec={beat.spec} /></AbsoluteFill> : <BarsBeat beat={beat} />; break;
    case 'typography': body = beat.spec ? <AbsoluteFill style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}><TypographyVisual spec={beat.spec} /></AbsoluteFill> : <BigTextBeat beat={beat} />; break;
    case 'visuals': body = <SceneVisualsLayer visuals={beat.visuals} />; break;
    case 'line_chart': body = <LineChartBeat beat={beat} />; break;
    case 'pie_chart': body = <PieChartBeat beat={beat} />; break;

    case 'map': body = <MapBeat beat={beat} />; break;

    case 'stat': body = <StatBeat beat={beat} />; break;

    case 'bars': body = <BarsBeat beat={beat} />; break;

    case 'timeline': body = <TimelineBeat beat={beat} />; break;

    case 'versus': body = <VersusBeat beat={beat} />; break;

    case 'list': body = <ListBeat beat={beat} />; break;

    case 'icons': body = <IconsBeat beat={beat} />; break;

    case 'canvas': body = <CanvasBeat beat={beat} />; break;

    case 'photo': body = <PhotoBeat beat={beat} />; break;

    case 'city_skyline': body = <CitySceneBeat beat={beat} />; break;

    case 'architecture': body = <ArchitectureBeat beat={beat} />; break;

    case 'mystery_scene': body = <MysterySceneBeat beat={beat} />; break;

    case 'split': body = <SplitBeat beat={beat} />; break;

    case 'ticker': body = <TickerBeat beat={beat} />; break;

    case 'cardstack': body = <CardStackBeat beat={beat} />; break;

    default: body = <BigTextBeat beat={beat} />;

  }

  return (
    <BeatShell beat={beat}>
      {body}
      {beat.kind !== 'visuals' && beat.visuals && beat.visuals.length > 0 ? (
        <SceneVisualsLayer visuals={beat.visuals} />
      ) : null}
    </BeatShell>
  );

};

