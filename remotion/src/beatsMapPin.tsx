// Split from beats.tsx (re-exported there).
import React from 'react';
import {AbsoluteFill, staticFile, useCurrentFrame} from 'remotion';
import {SafeImg} from './SafeImg';
import {ArrowFlow, FireSparks, GlowText, MapOverlay} from './fx';
import {useFont, useProgress, useSpring} from './hooks';
import {rgba, useTheme} from './theme';
import {BEAT_ZONE} from './layout';
import {Beat} from './types';
import {HlCountry} from './beats';

// ------------------------------------------------------------------ توزيع


// ------------------------------------------------------------------ مقاطع SVG الحديثة
/** Animated ripple ring around a map pin */
export const PinRipple: React.FC<{x: number; y: number; color: string; delay?: number}> = ({x, y, color, delay = 0}) => {
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

export const MapPinBeat: React.FC<{beat: Beat}> = ({beat}) => {
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

export const TimelineCardBeat: React.FC<{beat: Beat}> = ({beat}) => {
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
