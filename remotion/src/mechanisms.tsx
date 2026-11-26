/**
 * Mechanism recipes: the picture IS the explanation. Each one draws a physical thing that changes state on a spoken
 * word (`change` seconds): a level that drops or overflows, a stream that splits, many that become few, quantities you
 * can count, an area that shrinks. Big by contract: the drawing is marked [data-hero] and the render gate measures it.
 * All deterministic (frame-driven), RTL labels through ArText, colours from the video theme.
 */
import React from 'react';
import {interpolate} from 'remotion';
import {BEAT_ZONE} from './layout';
import {clamp01, useIdle, useProgress, useSpring as useSpr} from './hooks';
import {Icon} from './icons';
import {Abs, ArText, useKit} from './kit';  // render-time only (kit re-exports this file)

const STAGE = {x: 80, y: BEAT_ZONE.top + 290, w: 920, h: BEAT_ZONE.bottom - BEAT_ZONE.top - 300};  // y 570..1370
const fmt = (v: number) => (Number.isInteger(v) ? v : Math.round(v * 100) / 100).toLocaleString('en-US');

/** Stage box under the key line; children are positioned in its local px. */
const Stage: React.FC<{delay: number; children: React.ReactNode}> = ({delay, children}) => {
  const p = useSpr(delay, 'snappy');
  return (
    <Abs x={STAGE.x} y={STAGE.y} w={STAGE.w} h={STAGE.h} style={{opacity: clamp01(p * 1.4), transform: `translateY(${(1 - p) * 50}px)`}}>
      {children}
    </Abs>
  );
};

const Label: React.FC<{x: number; y: number; w: number; text: string; size?: number; color?: string; align?: 'center' | 'right' | 'left'; delay: number; weight?: number}> = ({x, y, w, text, size = 40, color, align = 'center', delay, weight = 800}) => (
  <Abs x={x} y={y} w={w} style={{display: 'flex', justifyContent: align === 'center' ? 'center' : align === 'right' ? 'flex-end' : 'flex-start'}}>
    <ArText size={size} weight={weight} color={color} align={align} delay={delay} reveal="fade" maxWidth={w}>{text}</ArText>
  </Abs>
);

// ------------------------------------------------------------------ Level: a tank whose level moves (drops, rises, overflows)
/** from/to: fill 0..1.2 (above 1 = overflow). The old level stays as a dashed ghost line with its label. */
export const Level: React.FC<{from: number; to: number; fromLabel?: string; toLabel?: string; delay?: number; change?: number; dur?: number}> = ({from, to, fromLabel = '', toLabel = '', delay = 0.2, change, dur = 1.6}) => {
  const k = useKit();
  const ch = change ?? delay + 0.7;
  const q = useProgress(ch, dur);
  const W = STAGE.w, tx = 330, tw = 520, ty = 60, th = 640;  // tank box in stage px; labels on the left, ruler on the right
  const f = Math.min(1.12, from + (to - from) * q);
  const lvl = (v: number) => ty + th - Math.min(1, v) * th;
  const y = lvl(f);
  const pts = Array.from({length: 25}, (_, i) => {
    const x = tx + (i / 24) * tw;
    return `${x},${y + Math.sin(i * 0.9 + k.t * 3) * 7}`;
  });
  const water = `M ${tx},${ty + th} L ${pts.join(' L ')} L ${tx + tw},${ty + th} Z`;
  const over = f > 1;
  const ghostY = lvl(from);
  const labelGap = Math.abs(ghostY - y) < 80 ? 80 * Math.sign(y - ghostY || 1) : 0;
  return (
    <Stage delay={delay}>
      <svg width={W} height={STAGE.h} data-hero="level" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
        {Array.from({length: 11}, (_, i) => (
          <line key={i} x1={tx + tw + 10} x2={tx + tw + (i % 5 === 0 ? 46 : 28)} y1={ty + th - (i / 10) * th} y2={ty + th - (i / 10) * th} stroke={k.c('text', 0.45)} strokeWidth={i % 5 === 0 ? 5 : 3} />
        ))}
        <path d={water} fill={k.c('accent2', 0.75)} />
        <path d={`M ${pts.join(' L ')}`} fill="none" stroke={k.c('accent2')} strokeWidth={6} />
        {over ? [0, 1].map((s) => (
          <rect key={s} x={s ? tx + tw - 4 : tx - 14} y={ty} width={18} height={interpolate(f, [1, 1.12], [0, th * 0.8], {extrapolateRight: 'clamp'})} rx={9} fill={k.c('accent2', 0.75)} />
        )) : null}
        <rect x={tx} y={ty} width={tw} height={th} rx={26} fill="none" stroke={over ? k.c('accent') : k.c('text', 0.85)} strokeWidth={10} />
        {q > 0.02 && Math.abs(to - from) > 0.03 ? (
          <line x1={tx - 40} x2={tx + tw + 20} y1={ghostY} y2={ghostY} stroke={k.c('text', 0.55)} strokeWidth={5} strokeDasharray="18 14" opacity={clamp01(q * 3)} />
        ) : null}
      </svg>
      {fromLabel ? <Label x={0} y={ghostY - 32} w={tx - 50} text={fromLabel} size={42} color={k.c('text', 0.7)} align="left" delay={ch} weight={700} /> : null}
      {toLabel ? <Label x={0} y={y - 36 + labelGap} w={tx - 50} text={toLabel} size={52} color={k.c('accent')} align="left" delay={ch + dur * 0.6} /> : null}
    </Stage>
  );
};

// ------------------------------------------------------------------ Flow: one stream that splits into shares
/** branches: share in % (shown when given) or equal widths; `keep` = the branch the sentence is about (highlighted). */
export const Flow: React.FC<{source: string; branches: {label: string; share?: number; icon?: string}[]; keep?: number; delay?: number; change?: number; dur?: number}> = ({source, branches, keep = -1, delay = 0.2, change, dur = 1.4}) => {
  const k = useKit();
  const ch = change ?? delay + 0.6;
  const q = useProgress(ch, dur);
  const n = Math.max(2, Math.min(4, branches.length));
  const W = STAGE.w, cx = W / 2, top = 80 + 150 / 2, splitY = 270, endY = 540, MAXW = 150;
  const total = branches.slice(0, n).reduce((a, b) => a + (b.share ?? 100 / n), 0) || 1;
  const xs = Array.from({length: n}, (_, i) => W - 130 - (i * (W - 260)) / (n - 1));  // right -> left (Arabic order)
  const dash = -k.frame * 5;
  return (
    <Stage delay={delay}>
      <svg width={W} height={STAGE.h} data-hero="flow" style={{position: 'absolute', left: 0, top: 0}}>
        <line x1={cx} x2={cx} y1={top} y2={splitY} stroke={k.c('accent2', 0.85)} strokeWidth={MAXW} strokeLinecap="round" />
        <line x1={cx} x2={cx} y1={top} y2={splitY} stroke={k.c('text', 0.35)} strokeWidth={10} strokeDasharray="26 20" strokeDashoffset={dash} />
        {branches.slice(0, n).map((b, i) => {
          const w = Math.max(10, (MAXW * (b.share ?? 100 / n)) / total);
          const d = `M ${cx} ${splitY} C ${cx} ${splitY + 170}, ${xs[i]} ${splitY + 120}, ${xs[i]} ${endY}`;
          const on = keep < 0 || keep === i;
          const len = 700;
          return (
            <g key={i}>
              <path d={d} fill="none" stroke={k.c('text', 0.12)} strokeWidth={w} strokeLinecap="round" />
              <path d={d} fill="none" stroke={on ? k.c('accent', 0.9) : k.c('text', 0.3)} strokeWidth={w} strokeLinecap="round" strokeDasharray={len} strokeDashoffset={len * (1 - q)} />
              {q > 0.6 ? <path d={d} fill="none" stroke={k.c('ground', 0.6)} strokeWidth={Math.min(8, w / 3)} strokeDasharray="22 22" strokeDashoffset={dash} opacity={clamp01((q - 0.6) * 3)} /> : null}
            </g>
          );
        })}
      </svg>
      <Label x={cx - 300} y={0} w={600} text={source} size={48} delay={delay} />
      {branches.slice(0, n).map((b, i) => {
        const on = keep < 0 || keep === i;
        const d = ch + dur * 0.7 + i * 0.12;
        return (
          <React.Fragment key={i}>
            {b.icon ? <Abs x={xs[i] - 45} y={endY + 20} w={90} h={90} style={{opacity: clamp01((q - 0.7) * 4)}}><Icon name={b.icon} size={90} color={on ? k.c('accent') : k.c('text', 0.5)} /></Abs> : null}
            <Label x={xs[i] - 150} y={endY + (b.icon ? 118 : 30)} w={300} text={b.share != null ? `${fmt(b.share)}% ${b.label}` : b.label} size={on ? 54 : 42} color={on ? k.c('accent') : k.c('text', 0.7)} delay={d} />
          </React.Fragment>
        );
      })}
    </Stage>
  );
};

// ------------------------------------------------------------------ Filter: many become few
/** A grid of `from` things (max 40 drawn, proportional above that); on the change word all but `to` fade away. */
export const Filter: React.FC<{from: number; to: number; icon?: string; fromLabel?: string; toLabel?: string; delay?: number; change?: number; dur?: number}> = ({from, to, icon, fromLabel = '', toLabel = '', delay = 0.2, change, dur = 1.0}) => {
  const k = useKit();
  const ch = change ?? delay + 0.9;
  const q = useProgress(ch, dur);
  const n = Math.max(2, Math.min(40, Math.round(from)));
  const kk = to <= 0 ? 0 : Math.max(1, Math.min(n - 1, Math.round((to / from) * n)));  // to 0: every one fades
  const kept = new Set(Array.from({length: kk}, (_, j) => Math.round(((j + 0.5) * n) / kk - 0.5)));
  const cols = n <= 9 ? 3 : n <= 16 ? 4 : n <= 30 ? 6 : 8;
  const rows = Math.ceil(n / cols);
  const cell = Math.min(820 / cols, 560 / rows);
  const gx = (STAGE.w - cols * cell) / 2;
  return (
    <Stage delay={delay}>
      <div data-hero="filter" style={{position: 'absolute', left: gx, top: 20, width: cols * cell, height: rows * cell}}>
        {Array.from({length: n}, (_, i) => {
          const on = kept.has(i);
          const r = Math.floor(i / cols), c = cols - 1 - (i % cols);  // fill right -> left
          const pop = useSpr(delay + i * 0.025, 'snappy');
          const sc = on ? 1 + 0.18 * q : 1 - 0.3 * q;
          return (
            <div key={i} style={{position: 'absolute', left: c * cell, top: r * cell, width: cell, height: cell, display: 'flex', alignItems: 'center', justifyContent: 'center',
              opacity: pop * (on ? 1 : 1 - 0.85 * q), transform: `scale(${pop * sc})`}}>
              {icon ? <Icon name={icon} size={cell * 0.66} color={on && q > 0.1 ? k.c('accent') : k.c('text', 0.8)} />
                : <div style={{width: cell * 0.56, height: cell * 0.56, borderRadius: cell, background: on && q > 0.1 ? k.c('accent') : k.c('text', 0.75)}} />}
            </div>
          );
        })}
      </div>
      <Label x={0} y={rows * cell + 60} w={STAGE.w / 2 - 20} text={`${fmt(to)} ${toLabel}`.trim()} size={52} color={k.c('accent')} delay={ch + dur * 0.5} />
      <Label x={STAGE.w / 2 + 20} y={rows * cell + 66} w={STAGE.w / 2 - 20} text={`${fmt(from)} ${fromLabel}`.trim()} size={40} color={k.c('text', 0.7)} delay={delay + 0.3} weight={700} />
    </Stage>
  );
};

// ------------------------------------------------------------------ Tally: two quantities you can count
/** Two columns of icons in proportion (one icon = `unit`, max 30 per column); the bigger side is the accent. */
export const Tally: React.FC<{sides: {label: string; value: number; icon: string}[]; delay?: number; change?: number}> = ({sides, delay = 0.2, change}) => {
  const k = useKit();
  const ch = change ?? delay + 0.4;
  const s2 = sides.slice(0, 2);
  const max = Math.max(...s2.map((s) => s.value), 1);
  const unit = Math.max(1, Math.ceil(max / 30));
  const colW = 400, cols = 5, cell = 72;
  const big = s2[0].value >= (s2[1]?.value ?? 0) ? 0 : 1;
  return (
    <Stage delay={delay}>
      <div data-hero="tally" style={{position: 'absolute', left: 30, top: 0, width: STAGE.w - 60, height: 500}}>
        {s2.map((s, si) => {
          const cnt = Math.max(1, Math.round(s.value / unit));
          const left = si === 0 ? STAGE.w - 60 - colW : 0;  // first side on the right (Arabic)
          return Array.from({length: cnt}, (_, i) => {
            const p = useSpr(ch + si * 0.5 + i * 0.04, 'snappy');
            const r = Math.floor(i / cols), c = cols - 1 - (i % cols);
            return (
              <div key={`${si}-${i}`} style={{position: 'absolute', left: left + c * (colW / cols) + (colW / cols - cell) / 2, top: 480 - (r + 1) * (cell + 8), opacity: p, transform: `scale(${p})`}}>
                <Icon name={s.icon} size={cell} color={si === big ? k.c('accent') : k.c('text', 0.6)} />
              </div>
            );
          });
        })}
      </div>
      {s2.map((s, si) => (
        <Label key={si} x={si === 0 ? STAGE.w - 30 - colW : 30} y={520} w={colW} text={`${fmt(s.value)} ${s.label}`} size={50} color={si === big ? k.c('accent') : k.c('text', 0.8)} delay={ch + si * 0.5 + 0.3} />
      ))}
      <Abs x={STAGE.w / 2 - 3} y={60} w={6} h={440} style={{background: k.c('text', 0.2), borderRadius: 3}} />
    </Stage>
  );
};

// ------------------------------------------------------------------ Shrink: an area that shrinks (or grows)
const blob = (cx: number, cy: number, R: number) => {
  const pts = Array.from({length: 60}, (_, i) => {
    const a = (i / 60) * Math.PI * 2;
    const r = R * (1 + 0.09 * Math.sin(3 * a + 1) + 0.05 * Math.sin(5 * a + 2) + 0.03 * Math.cos(7 * a));
    return `${(cx + Math.cos(a) * r * 1.05).toFixed(1)},${(cy + Math.sin(a) * r * 0.86).toFixed(1)}`;
  });
  return `M ${pts.join(' L ')} Z`;
};

/** Area from -> to (scale = sqrt of the ratio, so the AREA is true); the old outline stays dashed with its label. */
export const Shrink: React.FC<{from: number; to: number; unit?: string; fromLabel?: string; toLabel?: string; delay?: number; change?: number; dur?: number}> = ({from, to, unit = '', fromLabel = '', toLabel = '', delay = 0.2, change, dur = 1.8}) => {
  const k = useKit();
  const ch = change ?? delay + 0.7;
  const q = useProgress(ch, dur);
  const breathe = useIdle(4, 3.6, 0);
  const max = Math.max(from, to, 1e-9);
  const R = 330, cx = STAGE.w / 2, cy = 330;
  const s = (v: number) => Math.sqrt(v / max);
  const cur = s(from) + (s(to) - s(from)) * q;
  return (
    <Stage delay={delay}>
      <svg width={STAGE.w} height={STAGE.h} data-hero="shrink" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
        <path d={blob(cx, cy, R * s(from))} fill="none" stroke={k.c('text', 0.5)} strokeWidth={6} strokeDasharray="20 14" />
        <path d={blob(cx, cy, R * cur + breathe)} fill={k.c('accent2', 0.7)} stroke={k.c('accent2')} strokeWidth={6} />
        {[0.72, 0.45].map((f) => <path key={f} d={blob(cx, cy, R * cur * f)} fill="none" stroke={k.c('ground', 0.35)} strokeWidth={4} />)}
      </svg>
      <Label x={cx - 300} y={cy - 40} w={600} text={`${fmt(Number.isInteger(from) && Number.isInteger(to) ? Math.round(from + (to - from) * q) : from + (to - from) * q)} ${unit}`.trim()} size={64} delay={delay + 0.2} />
      {toLabel ? <Label x={cx - 300} y={cy + 40} w={600} text={toLabel} size={38} color={k.c('text', 0.85)} delay={ch + dur * 0.7} weight={700} /> : null}
      {fromLabel ? <Label x={cx - 300} y={cy + R * s(from) * 0.86 + 24} w={600} text={`${fromLabel} ${fmt(from)} ${unit}`.trim()} size={36} color={k.c('text', 0.65)} delay={ch} weight={700} /> : null}
    </Stage>
  );
};

// ------------------------------------------------------------------ Timeline: years on a vertical axis, a marker that travels
/** events: 2-5 {year, label}; `times` = second at which each event is reached (its spoken word). Earlier events recede. */
export const Timeline: React.FC<{events: {year: number; label: string}[]; times: number[]; delay?: number}> = ({events, times, delay = 0.2}) => {
  const k = useKit();
  const ev = events.slice(0, 5);
  const n = Math.max(2, ev.length);
  const ax = 700, y0 = 50, y1 = 650;  // axis on the right part (Arabic reads from the right): years right of it, labels left
  const yOf = (i: number) => y0 + (i * (y1 - y0)) / (n - 1);
  const ts = ev.map((_, i) => times[i] ?? delay + 0.6 + i * 0.8);
  // marker position: piecewise between the events it has reached
  let pos = 0;
  ts.forEach((t, i) => { if (i > 0) pos += clamp01((k.t - (t - 0.35)) / 0.35); });
  const cur = Math.min(ev.length - 1, Math.floor(pos + 1e-6));
  const my = yOf(0) + pos * ((y1 - y0) / (n - 1));
  return (
    <Stage delay={delay}>
      <svg width={STAGE.w} height={STAGE.h} data-hero="timeline" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
        <line x1={ax} x2={ax} y1={y0} y2={y1} stroke={k.c('text', 0.25)} strokeWidth={10} strokeLinecap="round" />
        <line x1={ax} x2={ax} y1={y0} y2={my} stroke={k.c('accent')} strokeWidth={10} strokeLinecap="round" />
        {ev.map((_, i) => <circle key={i} cx={ax} cy={yOf(i)} r={16} fill={i <= cur ? k.c('accent') : k.c('ground')} stroke={k.c('accent')} strokeWidth={6} />)}
        <circle cx={ax} cy={my} r={30 + Math.sin(k.t * 4) * 3} fill="none" stroke={k.c('accent', 0.6)} strokeWidth={6} />
      </svg>
      {ev.map((e, i) => {
        const shown = clamp01((k.t - (ts[i] - 0.3)) / 0.3);
        const op = shown * (i === cur ? 1 : 0.45);
        return (
          <React.Fragment key={i}>
            <Abs x={ax + 40} y={yOf(i) - 36} w={STAGE.w - ax - 40} style={{opacity: op}}>
              <div style={{fontFamily: k.font, fontWeight: 900, fontSize: i === cur ? 66 : 52, color: k.c('accent'), direction: 'ltr', lineHeight: 1.1}}>{String(e.year)}</div>
            </Abs>
            <Abs x={ax - 50 - 560} y={yOf(i) - 38} w={560} style={{opacity: op}}>
              <ArText size={i === cur ? 56 : 46} weight={800} align="right" reveal="none" maxWidth={560} style={{width: 560}}>{e.label}</ArText>
            </Abs>
          </React.Fragment>
        );
      })}
    </Stage>
  );
};
