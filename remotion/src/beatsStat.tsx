// Split from beats.tsx (re-exported there).
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {clamp01, enterStyle, EnterKind, Pop, useFont, useIdle, useProgress, useSpring} from './hooks';
import {AccentShapes, isAlt, useFont2} from './photo';
import {rgba, useTheme} from './theme';
import {BEAT_ZONE} from './layout';
import {Beat, RGB} from './types';
import {cueSecOf} from './beats';

// ------------------------------------------------------------------ أرقام

export const parseNum = (s: string) => {

  const m = s.match(/\d[\d,\.]*/);

  if (!m || m.index === undefined) return null;

  const raw = m[0].replace(/[.,]+$/, '');

  const clean = raw.replace(/,/g, '');

  const val = parseFloat(clean);

  if (isNaN(val)) return null;

  return {pre: s.slice(0, m.index), val, dec: clean.includes('.') ? clean.split('.')[1].length : 0, commas: raw.includes(','), suf: s.slice(m.index + raw.length)};

};

export const StatBeat: React.FC<{beat: Beat}> = ({beat}) => {

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

          <div style={{position: 'absolute', left: 0, right: 0, top: cy - 80 - 85, textAlign: 'center', ...enterStyle(a, 'pop'), ...num(Math.min(170, Math.floor(500 / (0.62 * Math.max(3, s.length)))), th.p.accent)}}>{show}</div>

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

export const TextWord: React.FC<{w: string; i: number; n: number; layout: string; size: number; color: string; kind: EnterKind}> = ({w, i, n, layout, size: size0, color: color0, kind}) => {

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

export const BigTextBeat: React.FC<{beat: Beat}> = ({beat}) => {

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
