import React, {useId} from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Icon} from './icons';
import {Flag} from './flag';
import {useFont, useProgress, useSpring} from './hooks';
import {on, rgba, useTheme} from './theme';
import {Beat} from './types';

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

// ============================================================================
// 6. <MacroZoomGlobeBeat /> — الزوم التلسكوبي من العالم إلى الدولة
// ============================================================================
export const MacroZoomGlobeBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();

  const title = String(beat.title || 'في قلب المنطقة الجغرافية');
  const targetCountry = String(beat.country || (beat as any).region || 'المنطقة المستهدفة');
  const targetCode = String(beat.code || (beat as any).iso || '');

  const prog = useProgress(0.1, 1.3);
  const zoomScale = 1 + prog * 1.8;

  return (
    <AbsoluteFill style={{direction: 'rtl', padding: 48, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <div style={{marginTop: 340, ...font, fontSize: 52, fontWeight: 900, color: '#f8fafc', textAlign: 'center'}}>
        {title}
      </div>

      {/* Target Focus Ring */}
      <div style={{marginTop: 90, position: 'relative', width: 500, height: 500, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        {/* Globe representation */}
        <div style={{width: 440, height: 440, borderRadius: '50%', background: 'radial-gradient(circle at 35% 35%, #1e3a8a 0%, #030712 90%)', border: '4px solid #38bdf8', boxShadow: '0 0 60px rgba(56,189,248,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${zoomScale.toFixed(2)})`, transformOrigin: 'center center'}}>
          <Icon name="lucide:globe" size={260} color="#38bdf8" />
        </div>

        {/* Pulsing targeting reticle */}
        <div style={{position: 'absolute', inset: 30, borderRadius: '50%', border: '3px dashed #f5c542', animation: 'spin 12s linear infinite', pointerEvents: 'none'}} />

        {/* Target Country Tag Reveal */}
        {prog > 0.6 && (
          <div style={{position: 'absolute', bottom: -50, display: 'flex', alignItems: 'center', gap: 14, padding: '14px 34px', borderRadius: 28, background: 'rgba(8,12,24,0.96)', border: '3px solid #f5c542', boxShadow: '0 0 35px rgba(245,197,66,0.5)', opacity: Math.min(1, (prog - 0.6) * 3)}}>
            {targetCode ? <Flag code={targetCode} shape="round" size={54} /> : <Icon name="lucide:map-pin" size={48} color="#f5c542" />}
            <span style={{...font, fontSize: 40, fontWeight: 900, color: '#f8fafc'}}>{targetCountry}</span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// 7. <SubsurfaceMineBeat /> — تشريح باطن الأرض والتعدين
// ============================================================================
export const SubsurfaceMineBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();

  const title = String(beat.title || 'ثروات وأسرار باطن الأرض');
  const targetDepth = Number(beat.depth_m || 1200);
  const resourceName = String(beat.resource || 'المعادن والموارد الطبيعية');

  const prog = useProgress(0.2, 1.3);
  const curDepth = Math.round(targetDepth * Math.min(1, prog));
  const panY = interpolate(prog, [0, 1], [0, -320]);

  return (
    <AbsoluteFill style={{direction: 'rtl', padding: 48, overflow: 'hidden'}}>
      <div style={{marginTop: 340, ...font, fontSize: 52, fontWeight: 900, color: '#f8fafc', textAlign: 'center'}}>
        {title}
      </div>

      {/* Earth Layers Canvas Pan */}
      <div style={{marginTop: 40, position: 'relative', width: '100%', height: 900, transform: `translateY(${panY.toFixed(1)}px)`}}>
        {/* Surface Grass/Rock */}
        <div style={{width: '100%', height: 160, borderRadius: 24, background: 'linear-gradient(180deg, #15803d, #78350f)', border: '2px solid rgba(255,255,255,0.2)', padding: 18, display: 'flex', alignItems: 'center', gap: 14}}>
          <Icon name="lucide:building" size={48} color="#f8fafc" />
          <span style={{fontSize: 28, fontWeight: 800, color: '#f8fafc'}}>سطح الأرض والمدينة القديمة</span>
        </div>

        {/* Underground Deep Rock / Shaft */}
        <div style={{width: '100%', height: 750, marginTop: 12, borderRadius: 28, background: 'linear-gradient(180deg, #292524 0%, #0c0a09 100%)', border: '3px solid #f5c542', padding: 28, position: 'relative'}}>
          {/* Vertical Mine Shaft Line */}
          <div style={{position: 'absolute', right: 120, top: 0, bottom: 0, width: 8, background: 'dashed #f5c542', borderRight: '4px dashed #f5c542'}} />

          {/* Depth Counter Badge */}
          <div style={{position: 'absolute', right: 150, top: 220, padding: '16px 28px', borderRadius: 24, background: 'rgba(8,12,24,0.95)', border: '2.5px solid #f5c542', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4}}>
            <span style={{fontSize: 22, color: '#94a3b8', fontWeight: 700}}>العمق تحت الأرض</span>
            <span style={{fontSize: 64, fontWeight: 900, color: '#f5c542', direction: 'ltr'}}>-{curDepth} م</span>
          </div>

          {/* Treasure Mineral Ore Vein */}
          <div style={{position: 'absolute', left: 80, bottom: 80, display: 'flex', alignItems: 'center', gap: 18, padding: '20px 32px', borderRadius: 24, background: 'rgba(245,197,66,0.15)', border: '2px solid #f5c542', boxShadow: '0 0 35px rgba(245,197,66,0.4)'}}>
            <Icon name="lucide:gem" size={64} color="#f5c542" />
            <div style={{display: 'flex', flexDirection: 'column'}}>
              <span style={{...font, fontSize: 34, fontWeight: 900, color: '#f8fafc'}}>{resourceName}</span>
              <span style={{fontSize: 24, color: '#f5c542', marginTop: 4}}>مليارات الأونصات المستخرجة</span>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// 8. <DotMatrixPopulationBeat /> — مصفوفة الكثافة السكانية الحية
// ============================================================================
export const DotMatrixPopulationBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();

  const title = String(beat.title || 'التوزيع السكاني والديموغرافي');
  const totalLabel = String(beat.total_label || '١٢ مليون نسمة');
  const highlightPct = Number(beat.highlight_pct || 70); // Percentage highlighted

  const prog = useProgress(0.2, 1.2);
  const totalDots = 60; // 6 rows x 10 cols
  const activeCount = Math.round((totalDots * (highlightPct / 100)) * Math.min(1, prog));

  return (
    <AbsoluteFill style={{direction: 'rtl', padding: 48, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <div style={{marginTop: 340, ...font, fontSize: 52, fontWeight: 900, color: '#f8fafc', textAlign: 'center'}}>
        {title}
      </div>

      <div style={{marginTop: 20, fontSize: 32, fontWeight: 700, color: '#f5c542'}}>
        إجمالي السكان: {totalLabel}
      </div>

      {/* Grid of Dots / Avatars */}
      <div style={{marginTop: 40, display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gap: 14, padding: 32, borderRadius: 32, background: 'rgba(11,18,32,0.92)', border: '2px solid rgba(255,255,255,0.18)'}}>
        {Array.from({length: totalDots}).map((_, idx) => {
          const isLit = idx < activeCount;
          return (
            <div
              key={idx}
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                background: isLit ? '#f5c542' : 'rgba(255,255,255,0.12)',
                boxShadow: isLit ? '0 0 16px rgba(245,197,66,0.6)' : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'background 0.2s',
              }}
            >
              <Icon name="lucide:user-round" size={26} color={isLit ? '#090e17' : 'rgba(255,255,255,0.3)'} />
            </div>
          );
        })}
      </div>

      {/* Percentage Callout */}
      <div style={{marginTop: 36, padding: '12px 32px', borderRadius: 20, background: 'rgba(245,197,66,0.2)', border: '2px solid #f5c542', color: '#f8fafc', fontWeight: 800, fontSize: 30}}>
        {Math.round(highlightPct * Math.min(1, prog))}% يتركزون في المراكز الحضرية
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// 9. <MoneyWaterfallBeat /> — تدفق العملات وميزانية الدولة
// ============================================================================
export const MoneyWaterfallBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const frame = useCurrentFrame();

  const title = String(beat.title || 'مسار التدفقات المالية والميزانية');
  const mainBudget = String(beat.total || '١٠٠ مليار $');
  const streams = beat.streams || [
    {name: 'تطوير البنية والمدن', pct: '٤٥%', color: '#f5c542'},
    {name: 'الخدمات والصحة', pct: '٣٠%', color: '#38bdf8'},
    {name: 'الاحتياطي السيادي', pct: '٢٥%', color: '#34d399'},
  ];

  const prog = useProgress(0.2, 1.3);

  return (
    <AbsoluteFill style={{direction: 'rtl', padding: 48, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <div style={{marginTop: 340, ...font, fontSize: 52, fontWeight: 900, color: '#f8fafc', textAlign: 'center'}}>
        {title}
      </div>

      {/* Main Budget Reservoir */}
      <div style={{marginTop: 40, width: 680, padding: '24px 36px', borderRadius: 28, background: 'rgba(11,18,32,0.96)', border: '3.5px solid #f5c542', boxShadow: '0 0 35px rgba(245,197,66,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
          <Icon name="lucide:coins" size={54} color="#f5c542" />
          <span style={{...font, fontSize: 32, fontWeight: 800, color: '#f8fafc'}}>الميزانية العامة</span>
        </div>
        <span style={{fontSize: 48, fontWeight: 900, color: '#f5c542'}}>{mainBudget}</span>
      </div>

      {/* Animated Pipes Flow Lines */}
      <svg width={680} height={120} style={{margin: '10px 0'}}>
        <line x1={340} y1={0} x2={160} y2={120} stroke="#f5c542" strokeWidth={6} strokeDasharray="12 8" strokeDashoffset={-frame * 3} />
        <line x1={340} y1={0} x2={340} y2={120} stroke="#38bdf8" strokeWidth={6} strokeDasharray="12 8" strokeDashoffset={-frame * 3} />
        <line x1={340} y1={0} x2={520} y2={120} stroke="#34d399" strokeWidth={6} strokeDasharray="12 8" strokeDashoffset={-frame * 3} />
      </svg>

      {/* Destination Buckets */}
      <div style={{display: 'flex', gap: 18, width: 880, justifyContent: 'center'}}>
        {streams.map((s: any, idx: number) => {
          return (
            <div
              key={idx}
              style={{
                flex: 1,
                padding: '24px 20px',
                borderRadius: 24,
                background: 'rgba(15,23,42,0.92)',
                border: `2.5px solid ${s.color}`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 8,
                transform: `scale(${0.8 + 0.2 * Math.min(1, prog)})`,
              }}
            >
              <span style={{fontSize: 42, fontWeight: 900, color: s.color}}>{s.pct}</span>
              <span style={{...font, fontSize: 24, fontWeight: 700, color: '#f8fafc', textAlign: 'center'}}>
                {s.name}
              </span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// 10. <FrontlineClashBeat /> — خط المواجهة وحصار المعارك
// ============================================================================
export const FrontlineClashBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();

  const title = String(beat.title || 'اشتعال خطوط المواجهة والنزاع');
  const sideAName = String(beat.side_a || (beat as any).sideA || (beat as any).left || 'القوة الأولى');
  const sideBName = String(beat.side_b || (beat as any).sideB || (beat as any).right || 'القوة المقابلة');

  const prog = useProgress(0.2, 1.3);
  const clashOffset = (prog - 0.5) * 140;

  return (
    <AbsoluteFill style={{direction: 'rtl', padding: 48, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <div style={{marginTop: 340, ...font, fontSize: 52, fontWeight: 900, color: '#f8fafc', textAlign: 'center'}}>
        {title}
      </div>

      {/* War Frontline Map Simulator */}
      <div style={{marginTop: 60, width: 880, height: 560, borderRadius: 32, background: 'radial-gradient(circle at 50% 50%, #1e1b4b 0%, #030712 100%)', border: '3px solid rgba(255,255,255,0.2)', position: 'relative', overflow: 'hidden', display: 'flex'}}>
        {/* Left Faction (Red territory) */}
        <div style={{flex: 1, background: 'rgba(239,68,68,0.2)', padding: 32, display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <Icon name="lucide:shield" size={38} color="#ef4444" />
            <span style={{...font, fontSize: 32, fontWeight: 900, color: '#fca5a5'}}>{sideAName}</span>
          </div>
          <span style={{fontSize: 24, color: '#fca5a5'}}>منطقة الدفاع</span>
        </div>

        {/* Right Faction (Blue territory) */}
        <div style={{flex: 1, background: 'rgba(56,189,248,0.2)', padding: 32, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', alignItems: 'flex-end'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <span style={{...font, fontSize: 32, fontWeight: 900, color: '#7dd3fc'}}>{sideBName}</span>
            <Icon name="lucide:shield" size={38} color="#38bdf8" />
          </div>
          <span style={{fontSize: 24, color: '#7dd3fc'}}>محور التقدم</span>
        </div>

        {/* Pulsing Clashing Frontline */}
        <div style={{position: 'absolute', top: 0, bottom: 0, left: 440 + clashOffset, width: 8, background: '#f5c542', boxShadow: '0 0 35px #f5c542'}}>
          {/* Crossed Swords explosion marker at center of clash */}
          <div style={{position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%, -50%)', padding: 18, borderRadius: '50%', background: '#090e17', border: '3px solid #f5c542', boxShadow: '0 0 25px rgba(245,197,66,0.7)'}}>
            <Icon name="lucide:swords" size={54} color="#f5c542" animation="pop" />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
