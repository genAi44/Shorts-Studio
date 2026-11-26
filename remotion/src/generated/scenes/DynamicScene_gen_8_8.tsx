/* AUTO-GENERATED ORIGINAL TSX SCENE BY AI VIDEO ARCHITECT */
import React from 'react';
import {AbsoluteFill, interpolate, interpolateColors, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

// ---- scene ----
/* @llm_verified:DynamicScene_gen_8_8:e35642a092f3 */
export const DynamicScene_gen_8_8: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
  const currentFrame = useCurrentFrame();
  const {fps: videoFps} = useVideoConfig();
  const frame = props.frame ?? currentFrame;
  const fps = props.fps ?? videoFps;
  const dur = Math.max(1, props.dur ?? 150);

  const p = Math.min(1, Math.max(0, frame / dur));

  // Phase timings
  const ph1 = interpolate(p, [0, 0.08], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const ph2 = interpolate(p, [0.32, 0.42], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const ph3 = interpolate(p, [0.68, 0.78], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Header entrance
  const headerOp = interpolate(frame, [0, 6], [0.85, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Timeline conduit wave animation
  const wavePhase = (frame / 18) % (Math.PI * 2);

  // Timeline milestones: 3 dated checkpoints representing tight surveillance of tourists
  const milestones = [
    {x: 190, label: 'نقطة التفتيش', sub: 'فحص الجوازات', delay: 0.12},
    {x: 540, label: 'مرشد إجباري', sub: 'مرافقة دائمة', delay: 0.30},
    {x: 890, label: 'مناطق محظورة', sub: 'تصوير ممنوع', delay: 0.48},
  ];

  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden', background: 'linear-gradient(180deg, #0a0612 0%, #150a1e 45%, #1a0d24 100%)'}}>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920">
        <defs>
          <radialGradient id="s4-glow" cx="50%" cy="42%" r="60%">
            <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.32" />
            <stop offset="55%" stopColor="#7c1d3d" stopOpacity="0.14" />
            <stop offset="100%" stopColor="#0a0612" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="s4-line" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.15" />
            <stop offset="50%" stopColor="#f97316" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.15" />
          </linearGradient>
          <linearGradient id="s4-bar" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#f43f5e" />
            <stop offset="100%" stopColor="#f97316" />
          </linearGradient>
          <linearGradient id="s4-tower" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f97316" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#7c1d3d" stopOpacity="0.5" />
          </linearGradient>
          <pattern id="s4-grid" width="60" height="60" patternUnits="userSpaceOnUse">
            <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#f43f5e" strokeOpacity="0.06" strokeWidth="1" />
          </pattern>
        </defs>

        {/* Atmospheric backdrop */}
        <rect x={0} y={0} width={1080} height={1920} fill="url(#s4-grid)" />
        <rect x={0} y={0} width={1080} height={1920} fill="url(#s4-glow)" />

        {/* Horizon ground plane */}
        <path d="M 0 1400 Q 540 1320 1080 1400 L 1080 1920 L 0 1920 Z" fill="#0a0612" opacity="0.85" />
        <line x1={0} y1={1400} x2={1080} y2={1400} stroke="#f43f5e" strokeOpacity="0.25" strokeWidth={2} />

        {/* ===== TOP HEADLINE BANNER ===== */}
        <g opacity={headerOp}>
          <rect x={60} y={110} width={960} height={130} rx={20} fill="rgba(6,12,24,0.94)" stroke="#f43f5e" strokeWidth={2} />
          <rect x={60} y={110} width={8} height={130} rx={4} fill="#f97316" />
          <foreignObject x={80} y={118} width={920} height={114}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-end', paddingRight: 12}}>
              <div style={{fontSize: 44, fontWeight: 900, color: '#ffffff', lineHeight: 1.15, textAlign: 'right'}}>
                السائحين الغربيين لزيارة أراضيها المراقبة
              </div>
              <div style={{fontSize: 26, fontWeight: 700, color: '#fde047', marginTop: 6, textAlign: 'right'}}>
                مراقبة بدقة شديدة على طول الطريق
              </div>
            </div>
          </foreignObject>
        </g>

        {/* ===== SLOT A: HUD side (right) reserved + left side metric card ===== */}
        <g opacity={ph1}>
          <rect x={60} y={272} width={520} height={310} rx={22} fill="rgba(6,12,24,0.94)" stroke="#f97316" strokeWidth={2} />
          <foreignObject x={80} y={290} width={480} height={280}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', alignItems: 'flex-end'}}>
              <div style={{fontSize: 30, fontWeight: 800, color: '#fde047', textAlign: 'right'}}>جواز سفر تحت الرقابة</div>
              <div style={{fontSize: 26, color: '#e2e8f0', lineHeight: 1.5, textAlign: 'right', marginTop: 8}}>
                كل تحرك للسائح يُسجَّل، وكل زيارة تخضع لتصريح مسبق قبل الوصول.
              </div>
              <div style={{display: 'flex', gap: 10, marginTop: 12, justifyContent: 'flex-end'}}>
                <div style={{background: '#f43f5e', color: '#fff', padding: '6px 14px', borderRadius: 10, fontSize: 24, fontWeight: 800}}>تفتيش</div>
                <div style={{background: '#f97316', color: '#fff', padding: '6px 14px', borderRadius: 10, fontSize: 24, fontWeight: 800}}>تصريح</div>
                <div style={{background: '#7c1d3d', color: '#fff', padding: '6px 14px', borderRadius: 10, fontSize: 24, fontWeight: 800}}>مرافقة</div>
              </div>
            </div>
          </foreignObject>
        </g>

        {/* Reserved HUD corner icon marker on right (visual only, kept clear of text) */}
        <g opacity={0.9}>
          <circle cx={822} cy={430} r={150} fill="none" stroke="#f43f5e" strokeOpacity={0.5} strokeWidth={2} strokeDasharray="6 10" />
          <circle cx={822} cy={430} r={110} fill="rgba(244,63,94,0.10)" stroke="#f97316" strokeOpacity={0.7} strokeWidth={2} />
          <circle cx={822} cy={430} r={70} fill="rgba(6,12,24,0.85)" stroke="#fde047" strokeOpacity={0.8} strokeWidth={2} />
          {/* Eye of surveillance icon */}
          <path d="M 772 430 Q 822 388 872 430 Q 822 472 772 430 Z" fill="none" stroke="#fde047" strokeWidth={3} />
          <circle cx={822} cy={430} r={14} fill="#f43f5e" />
          <circle cx={822} cy={430} r={20} fill="none" stroke="#f97316" strokeWidth={2} opacity={0.7} />
        </g>

        {/* ===== SLOT B: Historical Chronicle Timeline conduit ===== */}
        <g opacity={ph1}>
          <rect x={60} y={620} width={960} height={440} rx={24} fill="rgba(6,12,24,0.94)" stroke="#f43f5e" strokeWidth={2} />
          <foreignObject x={80} y={636} width={920} height={70}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", display: 'flex', justifyContent: 'flex-end', alignItems: 'center', width: '100%', height: '100%'}}>
              <div style={{fontSize: 30, fontWeight: 800, color: '#fde047'}}>مسار الزيارة المراقب — محطات إجبارية</div>
            </div>
          </foreignObject>

          {/* Timeline conduit */}
          <line x1={140} y1={860} x2={940} y2={860} stroke="url(#s4-line)" strokeWidth={6} strokeLinecap="round" />

          {/* Animated wave pulse along conduit */}
          <circle cx={140 + (Math.sin(wavePhase) * 0.5 + 0.5) * 800} cy={860} r={10} fill="#fde047" opacity={0.9} />
          <circle cx={140 + (Math.sin(wavePhase) * 0.5 + 0.5) * 800} cy={860} r={22} fill="none" stroke="#f97316" strokeWidth={2} opacity={0.6} />

          {/* Milestones */}
          {milestones.map((m, i) => {
            const show = interpolate(p, [m.delay, m.delay + 0.10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
            return (
              <g key={i} opacity={show}>
                <circle cx={m.x} cy={860} r={26} fill="#0a0612" stroke="#f97316" strokeWidth={3} />
                <circle cx={m.x} cy={860} r={12} fill="#f43f5e" />
                <rect x={m.x - 110} y={890} width={220} height={140} rx={14} fill="rgba(10,6,18,0.96)" stroke="#f43f5e" strokeWidth={1.5} />
                <foreignObject x={m.x - 100} y={900} width={200} height={120}>
                  <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center'}}>
                    <div style={{fontSize: 26, fontWeight: 900, color: '#fde047', lineHeight: 1.2}}>{m.label}</div>
                    <div style={{fontSize: 24, color: '#e2e8f0', marginTop: 6}}>{m.sub}</div>
                  </div>
                </foreignObject>
              </g>
            );
          })}

          {/* Small numbered badges above milestones */}
          {milestones.map((m, i) => (
            <g key={`n${i}`} opacity={interpolate(p, [m.delay, m.delay + 0.10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}>
              <circle cx={m.x} cy={800} r={22} fill="#f97316" />
              <text x={m.x} y={809} textAnchor="middle" fontSize={24} fontWeight={900} fill="#ffffff" fontFamily="Arial">{i + 1}</text>
            </g>
          ))}
        </g>

        {/* ===== SLOT C: Phase 3 takeaway callout ===== */}
        <g opacity={ph3}>
          <rect x={60} y={1090} width={960} height={330} rx={24} fill="rgba(6,12,24,0.94)" stroke="#fde047" strokeWidth={2} />
          <foreignObject x={80} y={1104} width={920} height={302}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}>
              <div style={{display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 12}}>
                <div style={{fontSize: 28, color: '#fde047', fontWeight: 900}}>الخلاصة</div>
                <div style={{width: 10, height: 32, background: '#f97316', borderRadius: 4}} />
              </div>
              <div style={{fontSize: 30, color: '#ffffff', fontWeight: 800, lineHeight: 1.35, textAlign: 'right', marginTop: 8}}>
                السائح الغربي يزور الأراضي المسموح بها فقط، تحت مراقبة دقيقة ومرافقة دائمة
              </div>
              <div style={{display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: 12}}>
                <div style={{background: 'rgba(244,63,94,0.22)', border: '1.5px solid #f43f5e', color: '#fecdd3', padding: '8px 16px', borderRadius: 12, fontSize: 24, fontWeight: 800}}>تصريح مسبق</div>
                <div style={{background: 'rgba(249,115,22,0.22)', border: '1.5px solid #f97316', color: '#fed7aa', padding: '8px 16px', borderRadius: 12, fontSize: 24, fontWeight: 800}}>مرشد إجباري</div>
                <div style={{background: 'rgba(253,224,71,0.18)', border: '1.5px solid #fde047', color: '#fef08a', padding: '8px 16px', borderRadius: 12, fontSize: 24, fontWeight: 800}}>مناطق محظورة</div>
              </div>
            </div>
          </foreignObject>
        </g>

        {/* Bottom safe zone remains empty (y >= 1465) */}
      </svg>
    </AbsoluteFill>
  );
};
