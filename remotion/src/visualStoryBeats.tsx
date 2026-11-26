import React, {useId} from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Icon} from './icons';
import {Flag} from './flag';
import {useFont, useProgress, useSpring} from './hooks';
import {on, rgba, useTheme} from './theme';
import {Beat} from './types';
export {DotMatrixPopulationBeat, FrontlineClashBeat, MacroZoomGlobeBeat, MoneyWaterfallBeat, SubsurfaceMineBeat} from './visualStoryBeatsMore';

// ============================================================================
// 1. <VersusBattleBeat /> — سباق المقارنة المباشر وميزان القوى
// ============================================================================
export const VersusBattleBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const title = String(beat.title || 'مقارنة القوى');
  const rawLeft = (beat.left || {}) as any;
  const rawRight = (beat.right || {}) as any;

  const leftName = String(rawLeft.name || rawLeft.title || rawLeft.label || 'الطرف الأول');
  const rightName = String(rawRight.name || rawRight.title || rawRight.label || 'الطرف الثاني');
  const leftSub = String(rawLeft.subtitle || rawLeft.badge || rawLeft.unit || '');
  const rightSub = String(rawRight.subtitle || rawRight.badge || rawRight.unit || '');

  const hasExplicitValues = (rawLeft.value !== undefined && rawRight.value !== undefined && !isNaN(Number(rawLeft.value)) && !isNaN(Number(rawRight.value)));
  const leftTarget = hasExplicitValues ? Number(rawLeft.value) : 100;
  const rightTarget = hasExplicitValues ? Number(rawRight.value) : 100;
  const maxVal = Math.max(leftTarget, rightTarget, 1);

  const prog = useProgress(0.2, 1.2);
  const leftCur = Math.round(leftTarget * Math.min(1, prog));
  const rightCur = Math.round(rightTarget * Math.min(1, prog));

  // Bar height progress
  const leftBarH = Math.round((leftTarget / maxVal) * 520 * Math.min(1, prog));
  const rightBarH = Math.round((rightTarget / maxVal) * 520 * Math.min(1, prog));

  const winner = rightTarget > leftTarget ? 'right' : leftTarget > rightTarget ? 'left' : 'tie';
  const showWinner = hasExplicitValues && winner !== 'tie' && prog > 0.85;

  return (
    <AbsoluteFill style={{direction: 'rtl', padding: 48, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      {/* Title */}
      <div style={{marginTop: 340, ...font, fontSize: 52, fontWeight: 900, color: '#f8fafc', textShadow: th.shadow, textAlign: 'center'}}>
        {title}
      </div>

      {/* Versus Badge */}
      <div style={{marginTop: 18, padding: '8px 24px', borderRadius: 999, background: 'rgba(239, 68, 68, 0.2)', border: '2px solid #ef4444', color: '#f87171', fontWeight: 900, fontSize: 28}}>
        VS
      </div>

      {/* Split Bars Arena */}
      <div style={{width: '100%', maxWidth: 900, marginTop: 40, display: 'flex', justifyContent: 'space-around', alignItems: 'flex-end', height: 600, paddingBottom: 40, borderBottom: '3px solid rgba(255,255,255,0.15)'}}>
        {/* Right side (Side A) */}
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, width: 340}}>
          {showWinner && winner === 'right' && (
            <div style={{display: 'flex', alignItems: 'center', gap: 6, padding: '6px 18px', borderRadius: 20, background: '#f5c542', color: '#090e17', fontWeight: 900, fontSize: 24}}>
              <Icon name="lucide:trophy" size={26} color="#090e17" />
              <span>المتصدر</span>
            </div>
          )}
          {hasExplicitValues ? (
            <div style={{...font, fontSize: 54, fontWeight: 900, color: '#f5c542', direction: 'ltr'}}>
              {rightCur.toLocaleString('en-US')} {rawRight.unit || ''}
            </div>
          ) : (
            rightSub ? (
              <div style={{padding: '6px 16px', borderRadius: 999, background: 'rgba(245,197,66,0.15)', border: '1.5px solid #f5c542', color: '#f5c542', fontSize: 22, fontWeight: 700}}>
                {rightSub}
              </div>
            ) : null
          )}
          <div style={{width: 140, height: hasExplicitValues ? Math.max(24, rightBarH) : 260, borderRadius: 24, background: 'linear-gradient(180deg, #f5c542, #b45309)', boxShadow: '0 0 32px rgba(245, 197, 66, 0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            {!hasExplicitValues && <Icon name="lucide:shield" size={64} color="#090e17" />}
          </div>
          <div style={{display: 'flex', alignItems: 'center', gap: 10, marginTop: 6}}>
            {rawRight.code && <Flag code={rawRight.code} shape="round" size={44} />}
            <span style={{...font, fontSize: 32, fontWeight: 800, color: '#f8fafc', textAlign: 'center'}}>{rightName}</span>
          </div>
        </div>

        {/* Left side (Side B) */}
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, width: 340}}>
          {showWinner && winner === 'left' && (
            <div style={{display: 'flex', alignItems: 'center', gap: 6, padding: '6px 18px', borderRadius: 20, background: '#38bdf8', color: '#090e17', fontWeight: 900, fontSize: 24}}>
              <Icon name="lucide:trophy" size={26} color="#090e17" />
              <span>المتصدر</span>
            </div>
          )}
          {hasExplicitValues ? (
            <div style={{...font, fontSize: 54, fontWeight: 900, color: '#38bdf8', direction: 'ltr'}}>
              {leftCur.toLocaleString('en-US')} {rawLeft.unit || ''}
            </div>
          ) : (
            leftSub ? (
              <div style={{padding: '6px 16px', borderRadius: 999, background: 'rgba(56,189,248,0.15)', border: '1.5px solid #38bdf8', color: '#38bdf8', fontSize: 22, fontWeight: 700}}>
                {leftSub}
              </div>
            ) : null
          )}
          <div style={{width: 140, height: hasExplicitValues ? Math.max(24, leftBarH) : 260, borderRadius: 24, background: 'linear-gradient(180deg, #38bdf8, #0369a1)', boxShadow: '0 0 32px rgba(56, 189, 248, 0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            {!hasExplicitValues && <Icon name="lucide:shield" size={64} color="#090e17" />}
          </div>
          <div style={{display: 'flex', alignItems: 'center', gap: 10, marginTop: 6}}>
            {rawLeft.code && <Flag code={rawLeft.code} shape="round" size={44} />}
            <span style={{...font, fontSize: 32, fontWeight: 800, color: '#f8fafc', textAlign: 'center'}}>{leftName}</span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// 2. <AnimatedRouteBeat /> — مسار القصة والرحلة الجغرافية
// ============================================================================
export const AnimatedRouteBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const title = String(beat.title || 'مسار الانتقال التاريخي');
  const fromCity = String(beat.from_city || 'سوكري');
  const toCity = String(beat.to_city || 'لاباز');
  const distanceKm = Number(beat.distance_km || 560);

  const prog = useProgress(0.2, 1.4);
  const curKm = Math.round(distanceKm * Math.min(1, prog));

  // Curved trajectory from City A (bottom right) to City B (top left)
  const P0 = {x: 820, y: 1140};
  const C1 = {x: 620, y: 720};
  const P1 = {x: 260, y: 560};

  // Quadratic bezier point calculation
  const t = Math.min(1, Math.max(0, prog));
  const curX = Math.round((1 - t) * (1 - t) * P0.x + 2 * (1 - t) * t * C1.x + t * t * P1.x);
  const curY = Math.round((1 - t) * (1 - t) * P0.y + 2 * (1 - t) * t * C1.y + t * t * P1.y);

  return (
    <AbsoluteFill style={{direction: 'rtl', padding: 48}}>
      <div style={{marginTop: 340, ...font, fontSize: 52, fontWeight: 900, color: '#f8fafc', textAlign: 'center'}}>
        {title}
      </div>

      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, pointerEvents: 'none'}}>
        {/* Track path background */}
        <path d={`M ${P0.x} ${P0.y} Q ${C1.x} ${C1.y} ${P1.x} ${P1.y}`} fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth={10} strokeDasharray="16 12" />
        {/* Animated active path */}
        <path d={`M ${P0.x} ${P0.y} Q ${C1.x} ${C1.y} ${P1.x} ${P1.y}`} fill="none" stroke="#f5c542" strokeWidth={10} strokeDasharray={1200} strokeDashoffset={1200 * (1 - t)} strokeLinecap="round" />
        {/* Moving traveler icon node */}
        <circle cx={curX} cy={curY} r={22} fill="#090e17" stroke="#f5c542" strokeWidth={6} />
      </svg>

      {/* Start City Node */}
      <div style={{position: 'absolute', left: P0.x - 120, top: P0.y + 36, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
        <div style={{padding: '10px 24px', borderRadius: 20, background: 'rgba(11,18,32,0.92)', border: '2px solid #38bdf8', color: '#f8fafc', fontWeight: 800, fontSize: 32}}>
          📍 {fromCity}
        </div>
        <span style={{fontSize: 22, color: '#94a3b8', marginTop: 4}}>نقطة الانطلاق (0 كم)</span>
      </div>

      {/* Destination City Node */}
      <div style={{position: 'absolute', left: P1.x - 120, top: P1.y - 110, display: 'flex', flexDirection: 'column', alignItems: 'center', opacity: prog > 0.4 ? 1 : 0.4}}>
        <div style={{padding: '10px 24px', borderRadius: 20, background: 'rgba(11,18,32,0.92)', border: '2px solid #f5c542', color: '#f8fafc', fontWeight: 800, fontSize: 32}}>
          🏛️ {toCity}
        </div>
        <span style={{fontSize: 22, color: '#f5c542', marginTop: 4}}>المقر الجديد ({distanceKm} كم)</span>
      </div>

      {/* Moving Distance HUD Counter */}
      <div style={{position: 'absolute', left: curX + 32, top: curY - 50, padding: '8px 20px', borderRadius: 18, background: 'rgba(8,12,24,0.95)', border: '2px solid #f5c542', boxShadow: '0 0 24px rgba(245,197,66,0.5)', display: 'inline-flex', alignItems: 'baseline', gap: 6, direction: 'ltr'}}>
        <span style={{...font, fontSize: 44, fontWeight: 900, color: '#f5c542'}}>{curKm.toLocaleString('en-US')}</span>
        <span style={{fontSize: 24, fontWeight: 700, color: '#cbd5e1'}}>كم</span>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// 3. <BalanceMeterBeat /> — ميزان القوى والاستفتاء (Gauge & Tug-of-War)
// ============================================================================
export const BalanceMeterBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();

  const title = String(beat.title || 'ميزان القوى والخيارات');
  const labelA = String(beat.label_a || (beat as any).leftLabel || (beat as any).left?.title || (beat as any).left?.name || 'الطرف الأول');
  const labelB = String(beat.label_b || (beat as any).rightLabel || (beat as any).right?.title || (beat as any).right?.name || 'الطرف الثاني');
  const targetPct = Number(beat.pct || (beat as any).leftWeight || 50); // Percent skew to side A

  const prog = useProgress(0.2, 1.3);
  const curPct = Math.round(50 + (targetPct - 50) * Math.min(1, prog));
  const tiltDeg = (curPct - 50) * 0.9;

  return (
    <AbsoluteFill style={{direction: 'rtl', padding: 48, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <div style={{marginTop: 340, ...font, fontSize: 52, fontWeight: 900, color: '#f8fafc', textAlign: 'center'}}>
        {title}
      </div>

      {/* Gauge Arc / Balance Beam */}
      <div style={{marginTop: 90, width: 860, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
        {/* Scale Beam */}
        <div style={{width: 760, height: 18, borderRadius: 9, background: 'rgba(255,255,255,0.25)', position: 'relative', transform: `rotate(${tiltDeg.toFixed(1)}deg)`, transformOrigin: 'center center', transition: 'transform 0.1s'}}>
          {/* Center fulcrum */}
          <div style={{position: 'absolute', left: '50%', top: -20, width: 40, height: 40, transform: 'translate(-50%, 0)', background: '#f5c542', borderRadius: '50%', boxShadow: '0 0 24px #f5c542'}} />
        </div>

        {/* Two Pans hanging */}
        <div style={{width: 860, display: 'flex', justifyContent: 'space-between', marginTop: 30}}>
          {/* Side A Pan */}
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, padding: '24px 36px', borderRadius: 28, background: 'rgba(11,18,32,0.92)', border: '3px solid #f5c542', width: 380}}>
            <Icon name="lucide:scale" size={48} color="#f5c542" />
            <span style={{...font, fontSize: 34, fontWeight: 900, color: '#f8fafc', textAlign: 'center'}}>{labelA}</span>
            <span style={{fontSize: 68, fontWeight: 900, color: '#f5c542'}}>{curPct}%</span>
          </div>

          {/* Side B Pan */}
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, padding: '24px 36px', borderRadius: 28, background: 'rgba(11,18,32,0.92)', border: '3px solid #38bdf8', width: 380}}>
            <Icon name="lucide:scale" size={48} color="#38bdf8" />
            <span style={{...font, fontSize: 34, fontWeight: 900, color: '#f8fafc', textAlign: 'center'}}>{labelB}</span>
            <span style={{fontSize: 68, fontWeight: 900, color: '#38bdf8'}}>{100 - curPct}%</span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// 4. <DeepTimeSliderBeat /> — شريط القرون والزمن المتسارع
// ============================================================================
export const DeepTimeSliderBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();

  const title = String(beat.title || 'قفزة عبر القرون والتاريخ');
  const rawEras = (beat as any).eras || [];
  const startYear = Number(beat.start_year || (rawEras[0]?.year ? String(rawEras[0].year).replace(/\D/g, '') : 1000) || 1000);
  const endYear = Number(beat.end_year || (rawEras.length ? String(rawEras[rawEras.length - 1].year).replace(/\D/g, '') : 2000) || 2024);
  const eventLabel = String(beat.event_label || rawEras[0]?.name || beat.title || 'محطة تاريخية بارزة');

  const prog = useProgress(0.2, 1.4);
  const curYear = Math.round(startYear + (endYear - startYear) * Math.min(1, prog));

  return (
    <AbsoluteFill style={{direction: 'rtl', padding: 48, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <div style={{marginTop: 340, ...font, fontSize: 52, fontWeight: 900, color: '#f8fafc', textAlign: 'center'}}>
        {title}
      </div>

      {/* Speedometer Odometer Year Display */}
      <div style={{marginTop: 70, padding: '24px 60px', borderRadius: 36, background: 'rgba(8,12,24,0.94)', border: '3.5px solid #f5c542', boxShadow: '0 0 45px rgba(245,197,66,0.4)', display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
        <span style={{fontSize: 26, color: '#94a3b8', fontWeight: 700}}>السنة الحاسمة</span>
        <span style={{fontSize: 124, fontWeight: 900, color: '#f5c542', direction: 'ltr', lineHeight: 1.05}}>
          {curYear}
        </span>
      </div>

      {/* Event Reveal Card at the end of the time leap */}
      {prog > 0.65 && (
        <div style={{marginTop: 48, maxWidth: 840, padding: '24px 36px', borderRadius: 28, background: 'rgba(15,23,42,0.92)', border: '2px solid rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', gap: 20, opacity: Math.min(1, (prog - 0.65) * 3)}}>
          <Icon name="lucide:scroll-text" size={60} color="#f5c542" />
          <div style={{display: 'flex', flexDirection: 'column'}}>
            <span style={{...font, fontSize: 36, fontWeight: 800, color: '#f8fafc'}}>{eventLabel}</span>
            <span style={{fontSize: 24, color: '#38bdf8', marginTop: 4}}>تاريخ محفور في الذاكرة الوطنية</span>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// ============================================================================
// 5. <StackPyramidBeat /> — الهرم الطبقي وتشريح السلطة
// ============================================================================
export const StackPyramidBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();

  const title = String(beat.title || 'هيكل وتوزيع المراحل');
  const rawLayers = (beat as any).tiers || beat.layers || (beat as any).items || [];
  const layers = rawLayers.length ? rawLayers.map((l: any, idx: number) => {
    const total = rawLayers.length;
    const w = 340 + Math.round((idx / Math.max(1, total - 1)) * 460);
    const colors = ['#f5c542', '#38bdf8', '#34d399', '#a78bfa', '#f87171'];
    return {
      name: String(l.label || l.name || l.title || `المستوى ${idx + 1}`),
      value: l.value !== undefined ? String(l.value) : '',
      width: l.width || w,
      color: l.color || colors[idx % colors.length],
    };
  }) : [
    {name: 'القمة والقيادة', value: 'المستوى الأول', width: 360, color: '#f5c542'},
    {name: 'المرحلة المركزية', value: 'المستوى الثاني', width: 560, color: '#38bdf8'},
    {name: 'القاعدة والأساس', value: 'المستوى الثالث', width: 780, color: '#34d399'},
  ];

  const prog = useProgress(0.2, 1.2);

  return (
    <AbsoluteFill style={{direction: 'rtl', padding: 48, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <div style={{marginTop: 340, ...font, fontSize: 52, fontWeight: 900, color: '#f8fafc', textAlign: 'center'}}>
        {title}
      </div>

      {/* Stack Layers (From top to bottom) */}
      <div style={{marginTop: 80, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20}}>
        {layers.map((l: any, idx: number) => {
          const delay = idx * 0.25;
          const layerProg = Math.max(0, Math.min(1, (prog - delay) * 2.5));
          if (layerProg <= 0.01) return null;
          return (
            <div
              key={idx}
              style={{
                width: l.width,
                padding: '24px 30px',
                borderRadius: 22,
                background: `linear-gradient(90deg, rgba(11,18,32,0.95), ${rgba(th.p.c1, 0.9)})`,
                border: `3px solid ${l.color}`,
                boxShadow: `0 8px 30px ${l.color}33`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: layerProg,
                transform: `scale(${0.7 + 0.3 * layerProg}) translateY(${(1 - layerProg) * -30}px)`,
              }}
            >
              <span style={{...font, fontSize: 32, fontWeight: 800, color: '#f8fafc', textAlign: 'center'}}>
                {l.name}
              </span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
