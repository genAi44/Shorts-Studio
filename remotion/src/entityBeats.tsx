/**
 * entityBeats.tsx - visuals for entity types that had no component: years / eras (YearCounterBeat) and
 * historical persons (PersonCardBeat). Pure SVG/CSS + spring/interpolate; colours come from the video theme so
 * they sit on any ground (paper, kraft, solid, ink ...).
 */
import React, {useContext} from 'react';
import {AbsoluteFill, interpolate, staticFile} from 'remotion';
import {Easing} from 'remotion';
import {MapLayoutCtx, rgba, useTheme} from './theme';
import {enterStyle, useFont, useProgress, useSpring} from './hooks';
import {BEAT_ZONE} from './layout';
import type {Beat} from './types';
import {SafeImg} from './SafeImg';

const fmtYear = (y: number) => (y < 0 ? `${Math.abs(y)} ق.م` : String(y));

/** Year / century / era: a counter that rolls to the spoken year over a timeline axis (two years = before / after). */
export const YearCounterBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const {splitBottom} = useContext(MapLayoutCtx); // a map stage fills the lower half: stack the counter above it
  const year = Number(beat.year);
  const to = beat.to_year !== undefined && beat.to_year !== null ? Number(beat.to_year) : null;
  const p = useProgress(0.1, 1.2);
  const lbl = useSpring(0.35, 'snappy');
  const span = Math.max(60, Math.round(Math.abs((to ?? year) - year) * 1.6) || (Math.abs(year) > 1000 ? 140 : 60));
  const a0 = year - span * 0.45, a1 = (to ?? year) + span * 0.55;
  const cur = Math.round(interpolate(p, [0, 1], [a0, to ?? year], {easing: Easing.bezier(0.22, 1, 0.36, 1)}));
  const X0 = 150, X1 = 930, AY = splitBottom ? BEAT_ZONE.top + 355 : BEAT_ZONE.center_y + 190;
  const bigTop = splitBottom ? BEAT_ZONE.top + 60 : BEAT_ZONE.center_y - 330, labelTop = splitBottom ? BEAT_ZONE.top + 250 : BEAT_ZONE.center_y - 60;
  const xOf = (v: number) => X0 + ((v - a0) / (a1 - a0)) * (X1 - X0);
  const ticks = Array.from({length: 5}, (_, i) => Math.round(a0 + ((a1 - a0) * i) / 4));
  const text = rgba(th.p.text), acc = rgba(th.p.accent), acc2 = rgba(th.p.accent2);
  const showTo = to !== null;
  const bigSize = splitBottom ? (showTo ? 110 : 150) : showTo ? 150 : 210;
  return (
    <AbsoluteFill>
      {beat.title ? (
        <div dir="rtl" style={{position: 'absolute', left: BEAT_ZONE.left, right: BEAT_ZONE.right, top: splitBottom ? BEAT_ZONE.top - 40 : BEAT_ZONE.title_top + 40, textAlign: 'center', ...font, fontSize: splitBottom ? 44 : 56, fontWeight: 800, color: text, ...enterStyle(lbl, 'rise', 30)}}>{beat.title}</div>
      ) : null}
      <div style={{position: 'absolute', left: 0, right: 0, top: bigTop, textAlign: 'center', direction: 'ltr', ...font, fontSize: bigSize, fontWeight: 900, lineHeight: 1.1, color: acc, fontVariantNumeric: 'tabular-nums', textShadow: th.shadow}}>
        {showTo ? `${fmtYear(year)} ← ${fmtYear(Math.round(interpolate(p, [0, 1], [year, to as number])))}` : fmtYear(cur)}
      </div>
      {beat.label ? (
        <div dir="rtl" style={{position: 'absolute', left: BEAT_ZONE.left, right: BEAT_ZONE.right, top: labelTop, textAlign: 'center', ...font, fontSize: splitBottom ? 40 : 52, fontWeight: 700, color: text, ...enterStyle(lbl, 'rise', 36)}}>{beat.label}</div>
      ) : null}
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <line x1={X0} y1={AY} x2={X1} y2={AY} stroke={rgba(th.p.text, 0.35)} strokeWidth={5} strokeLinecap="round" />
        {showTo && <rect x={xOf(year)} y={AY - 14} width={Math.max(0, (xOf(to as number) - xOf(year)) * p)} height={28} rx={14} fill={acc2} opacity={0.85} />}
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={xOf(t)} y1={AY - 14} x2={xOf(t)} y2={AY + 14} stroke={rgba(th.p.text, 0.5)} strokeWidth={3} />
            <text x={xOf(t)} y={AY + 58} textAnchor="middle" fontSize={32} fill={rgba(th.p.text, 0.7)} fontFamily={th.family}>{fmtYear(t)}</text>
          </g>
        ))}
        <circle cx={xOf(showTo ? interpolate(p, [0, 1], [year, to as number]) : cur)} cy={AY} r={24} fill={acc} stroke={rgba(th.p.c1)} strokeWidth={6} />
      </svg>
    </AbsoluteFill>
  );
};

/** Historical person: name + years + role on a card; licensed photo when one exists, else a symbolic silhouette. */
export const PersonCardBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const pop = useSpring(0.1, 'snappy');
  const rise = useSpring(0.35, 'smooth');
  const W = 780, H = 1000;
  const left = (1080 - W) / 2, top = BEAT_ZONE.center_y - H / 2;
  const card = th.dark ? rgba(th.p.c2, 0.92) : 'rgba(255,255,255,0.92)';
  const text = rgba(th.p.text), acc = rgba(th.p.accent), acc2 = rgba(th.p.accent2);
  const initials = String(beat.name || '').split(/\s+/).filter(Boolean).slice(0, 2).map((w: string) => w[0]).join('');
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left, top, width: W, height: H, borderRadius: 40, background: card, border: `4px solid ${acc}`, boxShadow: `0 30px 70px rgba(0,0,0,0.35)`, overflow: 'hidden', ...enterStyle(pop, 'rise', 70)}}>
        <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: 560, background: `linear-gradient(160deg, ${rgba(th.p.accent, 0.35)}, ${rgba(th.p.accent2, 0.35)})`}}>
          {beat.img ? (
            <SafeImg src={staticFile(beat.img)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          ) : (
            <svg width={W} height={560} viewBox={`0 0 ${W} 560`}>
              <circle cx={W / 2} cy={230} r={118} fill={rgba(th.p.text, 0.22)} />
              <path d={`M ${W / 2 - 250} 560 C ${W / 2 - 250} 400 ${W / 2 - 150} 350 ${W / 2} 350 C ${W / 2 + 150} 350 ${W / 2 + 250} 400 ${W / 2 + 250} 560 Z`} fill={rgba(th.p.text, 0.22)} />
              <text x={W / 2} y={262} textAnchor="middle" fontSize={120} fontWeight={900} fill={rgba(th.p.c1)} fontFamily={th.family}>{initials}</text>
            </svg>
          )}
        </div>
        <div dir="rtl" style={{position: 'absolute', left: 40, right: 40, top: 600, textAlign: 'center', ...font, fontSize: 84, fontWeight: 900, lineHeight: 1.2, color: text, ...enterStyle(rise, 'rise', 40)}}>{beat.name}</div>
        {beat.years ? (
          <div style={{position: 'absolute', left: 0, right: 0, top: 740, textAlign: 'center', direction: 'ltr', ...font, fontSize: 60, fontWeight: 800, color: acc, ...enterStyle(rise, 'rise', 40)}}>{beat.years}</div>
        ) : null}
        {beat.role ? (
          <div dir="rtl" style={{position: 'absolute', left: 60, right: 60, top: 840, textAlign: 'center', ...font, fontSize: 46, fontWeight: 600, lineHeight: 1.3, color: rgba(th.p.text, 0.85), ...enterStyle(rise, 'rise', 40)}}>
            <span style={{borderBottom: `5px solid ${acc2}`}}>{beat.role}</span>
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
