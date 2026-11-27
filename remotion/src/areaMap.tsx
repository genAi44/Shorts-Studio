import React from 'react';
import {AbsoluteFill, Easing, useCurrentFrame} from 'remotion';
import {clamp01, useFont, useProgress, useSpring} from './hooks';
import {rgba, useTheme} from './theme';
import {Beat} from './types';

/**
 * area_map: the narration states the AREA of a place -> its real outline, filled, with an animated area counter.
 * All geometry arrives pre-projected in canvas px (pipeline/areamap.py build_view); this file only animates it.
 * Motion = spring + bezier only (the pulse is a bezier-eased triangle wave, no raw sin).
 */
const UNIT_AR: Record<string, string> = {km2: 'كم²', mi2: 'ميل²', ha: 'هكتار', m2: 'م²'};
const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩';

const decOf = (v: number) => {
  const s = String(v);
  const i = s.indexOf('.');
  return i < 0 ? 0 : Math.min(2, s.length - i - 1);
};
export const fmtNum = (v: number, arabic: boolean, dec: number) => {
  const s = v.toLocaleString('en-US', {minimumFractionDigits: dec, maximumFractionDigits: dec});
  return arabic ? s.replace(/\d/g, (d) => AR_DIGITS[+d]).replace(/,/g, '٬').replace(/\./g, '٫') : s;
};

const PULSE = Easing.bezier(0.4, 0, 0.2, 1);
/** 0→1→0 every `period` frames, bezier-eased. */
const usePulse = (period = 48, delay = 20) => {
  const f = Math.max(0, useCurrentFrame() - delay);
  const ph = (f % period) / period;
  return PULSE(ph < 0.5 ? ph * 2 : (1 - ph) * 2);
};

// counter block position per layout (the map box is placed on the other side by pipeline/areamap.py BOX)
const COUNTER: Record<string, {top: number; card: boolean}> = {
  top: {top: 300, card: false},
  bottom: {top: 1130, card: false},
  overlay: {top: 1200, card: true},
};

export const AreaMapBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const frame = useCurrentFrame();
  const v = beat.view;
  const a = beat.area ?? {};
  const boxP = useSpring(0, 'smooth');
  const drawP = useProgress(0.15, 0.9);
  const fillP = useProgress(0.7, 0.7);
  const cntP = useProgress(0.35, 1.5);
  const popP = useSpring(1.1, 'bouncy');
  const insetP = useSpring(0.9, 'snappy');
  const pulse = usePulse();
  if (!v) return null;

  const arabic = a.digits === 'arabic';
  const value: number = a.value ?? a.data_km2 ?? 0;
  const dec = decOf(value);
  const finalStr = fmtNum(value, arabic, dec);
  const numSize = Math.min(150, Math.floor(900 / (finalStr.length * 0.62)));
  const unit = UNIT_AR[a.unit] ?? 'كم²';
  const lay = COUNTER[v.layout] ?? COUNTER.top;
  const box = v.box;
  const accent = th.p.accent;
  const accent2 = th.p.accent2;
    const ratio: number | null = v.ratio;

  const hlFill = (role: string) => rgba(role === 'main' ? accent : accent2, 0.78 * fillP);
  const hlColor = (role: string) => rgba(role === 'main' ? accent : accent2, 1);

  const ctxNodes = (
    v.ctx ? (
          <>
            <path d={v.ctx} fillRule="evenodd" fill={rgba(th.p.ctx, th.st.map.ctx_alpha * clamp01(boxP))} />
            <path d={v.ctx} fillRule="evenodd" fill="none" stroke={rgba(th.p.ctx_edge, 0.7)} strokeWidth={1.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - clamp01(boxP)} />
          </>
        ) : null
  );
  const hlNodes = (
    <>
        {v.hl.map((h: any, i: number) => (
          <g key={i}>
            {h.d ? (
              <>
                <path d={h.d} fillRule="evenodd" fill={hlFill(h.role)} />
                <path d={h.d} fillRule="evenodd" fill="none" stroke={hlColor(h.role)} strokeWidth={5} strokeLinejoin="round"
                  pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - drawP} />
                <path d={h.d} fillRule="evenodd" fill="none" stroke={hlColor(h.role)} strokeWidth={6 + 16 * pulse} strokeLinejoin="round"
                  opacity={fillP * 0.5 * (1 - pulse)} />
              </>
            ) : null}
            {h.tiny ? (
              <>
                <circle cx={h.cx} cy={h.cy} r={9} fill={hlColor(h.role)} opacity={drawP} />
                <circle cx={h.cx} cy={h.cy} r={14 + 34 * pulse} fill="none" stroke={hlColor(h.role)} strokeWidth={4} opacity={drawP * (1 - pulse)} />
              </>
            ) : null}
          </g>
        ))}
    </>
  );

  return (
    <AbsoluteFill>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <defs>
          <radialGradient id="am-globe" cx="40%" cy="35%" r="75%">
            <stop offset="0%" stopColor={rgba(th.p.c2, 0.55)} />
            <stop offset="100%" stopColor={rgba(th.p.c1, 0.9)} />
          </radialGradient>
          <clipPath id="am-box">
            <rect x={box.cx - box.w / 2} y={box.cy - box.h / 2} width={box.w} height={box.h} rx={40} />
          </clipPath>
          {v.inset ? (
            <clipPath id="am-inset">
              <circle cx={v.inset.cx} cy={v.inset.cy} r={v.inset.r - 4} />
            </clipPath>
          ) : null}
        </defs>

        {/* map card */}
        <rect
          x={box.cx - box.w / 2} y={box.cy - box.h / 2} width={box.w} height={box.h} rx={40}
          fill={rgba(th.p.c1, 0.42 * boxP)} stroke={rgba(th.p.ctx_edge, 0.5 * boxP)} strokeWidth={2}
        />

        {v.globe ? (
          <circle cx={v.globe.cx} cy={v.globe.cy} r={v.globe.r * (0.9 + 0.1 * boxP)} fill="url(#am-globe)" stroke={rgba(th.p.ctx_edge, 0.8)} strokeWidth={3} />
        ) : null}

        <g clipPath="url(#am-box)">{v.under ? <>{hlNodes}{ctxNodes}</> : <>{ctxNodes}{hlNodes}</>}</g>

        {/* compare: names under each shape */}
        {v.mode === 'compare'
          ? v.hl.map((h: any, i: number) => (
              <text key={`t${i}`} x={h.lx} y={h.ly} textAnchor="middle" fontSize={44} fill={rgba(th.p.text, 1)}
                style={{...font, opacity: popP}}>{h.label}</text>
            ))
          : null}

        {/* magnifier: link + inset lens */}
        {v.inset ? (
          <g>
            <line x1={v.link[0]} y1={v.link[1]} x2={v.link[2]} y2={v.link[3]} stroke={rgba(accent, 0.9)} strokeWidth={4}
              strokeDasharray="14 10" opacity={insetP} />
            <g transform={`translate(${v.inset.cx} ${v.inset.cy}) scale(${0.4 + 0.6 * insetP}) translate(${-v.inset.cx} ${-v.inset.cy})`} opacity={clamp01(insetP * 1.4)}>
              <circle cx={v.inset.cx} cy={v.inset.cy} r={v.inset.r} fill={rgba(th.p.c1, 0.97)} />
              <g clipPath="url(#am-inset)">
                <path d={v.inset.d} fillRule="evenodd" fill={rgba(accent, 0.8)} stroke={rgba(accent, 1)} strokeWidth={3} />
              </g>
              <circle cx={v.inset.cx} cy={v.inset.cy} r={v.inset.r} fill="none" stroke={rgba(accent, 1)} strokeWidth={6 + 8 * pulse} />
            </g>
          </g>
        ) : null}
      </svg>

      {/* tags: approximate shape / fallback — visible, never silent */}
      <div style={{position: 'absolute', top: box.cy - box.h / 2 + 18, left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: 12, direction: 'rtl'}}>
        {v.synthetic ? <Tag text="شكل تقريبي" /> : null}
        {beat._fallback ? <Tag text="عرض احتياطي" /> : null}
      </div>

      {/* comparison ratio badge */}
      {ratio ? (
        <div style={{position: 'absolute', top: box.cy - box.h / 2 + 70, left: 0, right: 0, display: 'flex', justifyContent: 'center', direction: 'rtl'}}>
          <div style={{...font, transform: `scale(${0.6 + 0.4 * popP})`, opacity: clamp01(popP * 1.5), background: accent2 ? rgba(accent2, 1) : '#000', color: '#fff',
            borderRadius: 999, padding: '10px 34px', fontSize: 64, textShadow: 'none'}}>
            {`${fmtNum(ratio, arabic, decOf(ratio))} ضعف`}
          </div>
        </div>
      ) : null}

      {/* animated area counter */}
      <div style={{position: 'absolute', top: lay.top, left: 60, right: 60, display: 'flex', flexDirection: 'column', alignItems: 'center', direction: 'rtl', ...font,
        ...(lay.card ? {background: rgba(th.p.c1, 0.82), border: `3px solid ${rgba(accent, 0.8)}`, borderRadius: 36, padding: '14px 20px', height: 160, justifyContent: 'center'} : {})}}>
        <div style={{display: 'flex', alignItems: 'baseline', gap: 20, direction: 'rtl'}}>
          <span style={{fontSize: lay.card ? Math.min(numSize, 104) : numSize, color: rgba(accent, 1), lineHeight: 1.1, fontVariantNumeric: 'tabular-nums', direction: 'ltr'}}>
            {fmtNum(value * cntP, arabic, dec)}
          </span>
          <span style={{fontSize: lay.card ? 48 : 60, color: rgba(th.p.text, 1)}}>{unit}</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Tag: React.FC<{text: string}> = ({text}) => {
  const th = useTheme();
  const font = useFont();
  return (
    <div style={{...font, fontSize: 30, padding: '4px 20px', borderRadius: 999, color: rgba(th.p.text, 1), background: rgba(th.p.c1, 0.9), border: `2px solid ${rgba(th.p.ctx_edge, 0.9)}`}}>
      {text}
    </div>
  );
};
