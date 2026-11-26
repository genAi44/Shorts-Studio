// Split from visualStoryBeats.tsx (re-exported there).
import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {Icon} from './icons';
import {Flag} from './flag';
import {useFont, useProgress} from './hooks';
import {useTheme} from './theme';
import {Beat} from './types';

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
