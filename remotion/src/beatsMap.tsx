// Split from beats.tsx (re-exported there).
import React, {useContext} from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {ParallaxLayer, SvgZoomIn} from './camera';
import {clamp01, enterStyle, useFont, useSpring} from './hooks';
import {MotionCtx, rgba, useTheme} from './theme';
import {BEAT_ZONE} from './layout';
import {Beat, RGB} from './types';
import {shade} from './beats';

// ------------------------------------------------------------------ الخريطة

export const Marker: React.FC<{kind: string; col: RGB; ring: RGB; p: number}> = ({kind, col, ring, p}) => {

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

export const HlCountry: React.FC<{h: any; i: number}> = ({h, i}) => {

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

export const MapPoint: React.FC<{pt: any; j: number}> = ({pt, j}) => {

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

export const SmallMagnifier: React.FC<{h: any; ctx: string}> = ({h, ctx}) => {

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

export const MapBeat: React.FC<{beat: Beat}> = ({beat}) => {

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
