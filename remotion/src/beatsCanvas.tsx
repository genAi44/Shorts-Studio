// Split from beats.tsx (re-exported there).
import React, {useContext} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {Icon} from './icons';
import {clamp01, enterStyle, EnterKind, useFont, useProgress, useSpring} from './hooks';
import {AccentShapes} from './photo';
import {MotionCtx, rgba, useTheme} from './theme';
import {BEAT_ZONE} from './layout';
import {Beat, RGB} from './types';

// ------------------------------------------------------------------ كانفس حر: عناصر يرسمها المخرج البصري بالكود

export const CanvasEl: React.FC<{el: any; idx: number}> = ({el, idx}) => {

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

export const CanvasBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const els = (beat.elements || []).slice(0, 14);

  return <AbsoluteFill>{els.map((el: any, i: number) => <CanvasEl key={i} el={el} idx={i} />)}</AbsoluteFill>;

};

// ------------------------------------------------------------------ مقارنة عمودية (لوحتان)

export const SplitPanel: React.FC<{data: any; side: 'screen-right' | 'screen-left'; col: RGB}> = ({data, side, col}) => {

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

export const SplitBeat: React.FC<{beat: Beat}> = ({beat}) => {

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

export const TickerBeat: React.FC<{beat: Beat}> = ({beat}) => {

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

      <div data-audit-ignore style={{position: 'absolute', top: th.zoneCy - 50, left: 0, right: 0, height: 156, overflow: 'hidden', borderTop: `3px solid ${rgba(th.p.accent, 0.5)}`, borderBottom: `3px solid ${rgba(th.p.accent, 0.5)}`}}>

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

// Stacked cards must never overlap: height shrinks with the count so they all fit the beat zone.
export const CARD_GAP = 24;

export const CARD_H = (n: number) => Math.min(196, Math.floor((BEAT_ZONE.bottom - BEAT_ZONE.top - 40 - (n - 1) * CARD_GAP) / Math.max(1, n)));

export const CardItem: React.FC<{item: any; i: number; n: number}> = ({item, i, n}) => {

  const th = useTheme();

  const font = useFont();

  const p = useSpring(0.1 + i * 0.28, 'bouncy');

  const col = th.tok(`hl${i}`);

  return (

    <div style={{position: 'absolute', left: 80, right: 80, top: th.zoneCy - (n * CARD_H(n) + (n - 1) * CARD_GAP) / 2 + i * (CARD_H(n) + CARD_GAP), height: CARD_H(n), borderRadius: 32, background: rgba(th.p.c1, Math.max(0.35, 0.82 - i * 0.1)), border: `3px solid ${rgba(col, 0.8)}`, display: 'flex', alignItems: 'center', gap: 28, padding: '0 36px', zIndex: n - i, ...enterStyle(p, 'rise', 40 + i * 18)}}>

      {item.icon ? <div style={{flex: '0 0 auto'}}><Icon name={item.icon} size={78} color={rgba(col)} /></div> : null}

      <div dir="rtl" style={{...font, fontSize: 52, lineHeight: 1.3, color: rgba(th.p.text), flex: 1, textShadow: th.shadow}}>{item.text || ''}</div>

      {item.value ? <div style={{...font, fontSize: 70, color: rgba(col), direction: 'ltr', flex: '0 0 auto'}}>{item.value}</div> : null}

    </div>

  );

};

export const CardStackBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const items: any[] = (beat.items || []).slice(0, 4);

  return <AbsoluteFill>{items.map((it, i) => <CardItem key={i} item={it} i={i} n={items.length} />)}</AbsoluteFill>;

};
