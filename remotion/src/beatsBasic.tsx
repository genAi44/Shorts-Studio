// Split from beats.tsx (re-exported there).
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Icon} from './icons';
import {clamp01, enterStyle, useFont, useIdle, useProgress, useSpring} from './hooks';
import {on, rgba, useTheme} from './theme';
import {BEAT_ZONE} from './layout';
import {Beat, RGB} from './types';

// ------------------------------------------------------------------ أعمدة

export const BarRow: React.FC<{item: any; i: number; max: number; top: number}> = ({item, i, max, top}) => {

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

export const BarsBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const th = useTheme();

  const items = (beat.items || []).slice(0, 6);

  const max = Math.max(...items.map((x: any) => Number(x.value) || 0), 1);

  const rowH = 170;

  const top0 = th.zoneCy - (items.length * rowH) / 2 + 20;

  return <AbsoluteFill>{items.map((it: any, i: number) => <BarRow key={i} item={it} i={i} max={max} top={top0 + i * rowH} />)}</AbsoluteFill>;

};

// ------------------------------------------------------------------ خط زمني

export const TimelineRow: React.FC<{item: any; i: number; y: number}> = ({item, i, y}) => {

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

export const TimelineBeat: React.FC<{beat: Beat}> = ({beat}) => {

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

export const VsCard: React.FC<{item: any; side: 'right' | 'left'; col: RGB}> = ({item, side, col}) => {

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

export const VersusBeat: React.FC<{beat: Beat}> = ({beat}) => {

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

export const ListRow: React.FC<{item: any; i: number; y: number; height: number}> = ({item, i, y, height}) => {

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

export const ListBeat: React.FC<{beat: Beat}> = ({beat}) => {

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

export const IconCell: React.FC<{item: any; i: number; x: number; y: number}> = ({item, i, x, y}) => {

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

export const IconsBeat: React.FC<{beat: Beat}> = ({beat}) => {

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
