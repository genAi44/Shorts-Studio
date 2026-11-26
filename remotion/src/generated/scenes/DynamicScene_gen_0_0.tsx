/* AUTO-GENERATED ORIGINAL TSX SCENE BY AI VIDEO ARCHITECT */
import React from 'react';
import {AbsoluteFill, interpolate, interpolateColors, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

// ---- scene ----
/* @llm_verified:DynamicScene_gen_0_0:07f80849a2d0 */
export const DynamicScene_gen_0_0: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
  const currentFrame = useCurrentFrame();
  const {fps: videoFps} = useVideoConfig();
  const frame = props.frame ?? currentFrame;
  const fps = props.fps ?? videoFps;
  const dur = Math.max(1, props.dur ?? 150);
  const p = Math.min(1, Math.max(0, frame / dur));

  const headerOpacity = interpolate(frame, [0, 8], [0.85, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const heroScale = spring({frame, fps, config: {damping: 14, stiffness: 110, mass: 0.8}});
  const heroOpacity = interpolate(frame, [0, 8], [0.85, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Phase 2: isolation wall / barbed wire + "منعزلة" bar
  const p2 = interpolate(p, [0.35, 0.7], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const p2Op = interpolate(p, [0.35, 0.42], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Phase 3: takeaway card
  const p3 = interpolate(p, [0.7, 0.78], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // decorative flag wave
  const wave = Math.sin(frame / 12) * 6;

  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden', background: 'linear-gradient(180deg, #061018 0%, #0a1a22 45%, #04141a 100%)'}}>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920">
        <defs>
          <radialGradient id="bgGlow" cx="50%" cy="38%" r="65%">
            <stop offset="0%" stopColor="#2dd4bf" stopOpacity="0.22" />
            <stop offset="55%" stopColor="#0a2a2f" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#000000" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="groundGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0e3a34" />
            <stop offset="100%" stopColor="#04120f" />
          </linearGradient>
          <linearGradient id="domeGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#4ade80" />
            <stop offset="100%" stopColor="#166534" />
          </linearGradient>
          <linearGradient id="wallGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2dd4bf" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#0f766e" stopOpacity="0.85" />
          </linearGradient>
          <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#4ade80" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#4ade80" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Atmospheric backdrop */}
        <rect x={0} y={0} width={1080} height={1920} fill="url(#bgGlow)" />
        {/* depth lines */}
        {[0, 1, 2, 3, 4, 5, 6].map((i) => (
          <line key={i} x1={0} y1={1420 + i * 18} x2={1080} y2={1420 + i * 18} stroke="#0f766e" strokeOpacity={0.06} strokeWidth={2} />
        ))}
        {/* light beams */}
        <path d="M 200 200 L 320 200 L 240 900 L 120 900 Z" fill="url(#beam)" opacity={0.35} />
        <path d="M 780 200 L 900 200 L 960 900 L 840 900 Z" fill="url(#beam)" opacity={0.28} />

        {/* Top Header Banner */}
        <g opacity={headerOpacity}>
          <rect x={60} y={110} width={960} height={130} rx={22} fill="rgba(6,12,24,0.94)" stroke="#4ade80" strokeWidth={2} />
          <rect x={60} y={110} width={10} height={130} rx={4} fill="#4ade80" />
          <foreignObject x={80} y={118} width={920} height={118}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start', paddingRight: 14}}>
              <div style={{fontSize: 44, fontWeight: 900, color: '#fde047', lineHeight: 1.15, letterSpacing: 0.3}}>دولة شبه شيوعية منعزلة بفخر</div>
              <div style={{fontSize: 26, fontWeight: 700, color: '#a7f3d0', marginTop: 6}}>خمس كيانات سياسية غامضة • الجزء ٣</div>
            </div>
          </foreignObject>
        </g>

        {/* SLOT A (right side, opposite HUD) — top mini metric card */}
        <g opacity={heroOpacity} transform={`translate(0, ${(1 - heroScale) * 20})`}>
          <rect x={612} y={270} width={408} height={300} rx={22} fill="rgba(6,12,24,0.94)" stroke="#2dd4bf" strokeWidth={2} />
          <foreignObject x={628} y={282} width={380} height={276}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}>
              <div style={{fontSize: 30, fontWeight: 900, color: '#fde047', lineHeight: 1.2}}>نظام شبه شيوعي</div>
              <div style={{fontSize: 24, fontWeight: 700, color: '#ffffff', lineHeight: 1.35}}>سيطرة حزبية واحدة على الدولة والمجتمع</div>
              <div style={{display: 'flex', gap: 10, justifyContent: 'flex-end'}}>
                <div style={{fontSize: 22, fontWeight: 800, color: '#4ade80', background: 'rgba(74,222,128,0.14)', border: '1.5px solid #4ade80', borderRadius: 10, padding: '4px 12px'}}>حزب واحد</div>
                <div style={{fontSize: 22, fontWeight: 800, color: '#2dd4bf', background: 'rgba(45,212,191,0.14)', border: '1.5px solid #2dd4bf', borderRadius: 10, padding: '4px 12px'}}>اقتصاد موجه</div>
              </div>
            </div>
          </foreignObject>
        </g>

        {/* SLOT B — Architectural Monument Illustration on solid ground */}
        <g opacity={heroOpacity}>
          {/* ground plateau */}
          <ellipse cx={540} cy={1060} rx={470} ry={38} fill="#0f766e" opacity={0.22} />
          <rect x={90} y={1030} width={900} height={30} rx={8} fill="url(#groundGrad)" />
          {/* main dome building */}
          {/* base */}
          <rect x={280} y={860} width={520} height={170} rx={6} fill="#0b2b28" stroke="#2dd4bf" strokeWidth={2} />
          {/* columns */}
          {[320, 380, 440, 500, 560, 620, 680, 740].map((x, i) => (
            <rect key={i} x={x} y={880} width={22} height={140} rx={3} fill="#134e4a" stroke="#2dd4bf" strokeOpacity={0.7} strokeWidth={1.5} />
          ))}
          {/* arch window */}
          <path d="M 500 940 Q 540 900 580 940 L 580 1020 L 500 1020 Z" fill="#04120f" stroke="#4ade80" strokeWidth={2} />
          {/* drum */}
          <rect x={380} y={800} width={320} height={62} rx={4} fill="#0e3a34" stroke="#2dd4bf" strokeWidth={2} />
          {/* dome */}
          <path d="M 380 800 Q 540 620 700 800 Z" fill="url(#domeGrad)" stroke="#a7f3d0" strokeWidth={2.5} />
          {/* dome ribs */}
          {[-0.6, -0.3, 0, 0.3, 0.6].map((t, i) => (
            <path key={i} d={`M 540 800 Q ${540 + t * 300} ${680 + Math.abs(t) * 40} ${540 + t * 320} 800`} fill="none" stroke="#a7f3d0" strokeOpacity={0.35} strokeWidth={1.5} />
          ))}
          {/* spire */}
          <rect x={534} y={620} width={12} height={40} fill="#4ade80" />
          <circle cx={540} cy={616} r={10} fill="#fde047" stroke="#4ade80" strokeWidth={2} />
          {/* flag on top */}
          <line x1={540} y1={616} x2={540} y2={560} stroke="#a7f3d0" strokeWidth={3} />
          <path d={`M 540 ${560 + wave * 0.1} Q ${590} ${548 + wave} 640 560 L 640 600 Q 590 ${588 + wave} 540 600 Z`} fill="#4ade80" stroke="#a7f3d0" strokeWidth={2} />
          {/* side towers */}
          <rect x={230} y={820} width={70} height={210} rx={4} fill="#0b2b28" stroke="#2dd4bf" strokeWidth={2} />
          <rect x={780} y={820} width={70} height={210} rx={4} fill="#0b2b28" stroke="#2dd4bf" strokeWidth={2} />
          <path d="M 230 820 L 265 780 L 300 820 Z" fill="#166534" stroke="#2dd4bf" strokeWidth={2} />
          <path d="M 780 820 L 815 780 L 850 820 Z" fill="#166534" stroke="#2dd4bf" strokeWidth={2} />
          {/* windows in towers */}
          {[860, 910, 960].map((y, i) => (
            <g key={i}>
              <rect x={250} y={y} width={30} height={28} rx={3} fill="#fde047" opacity={0.55} />
              <rect x={800} y={y} width={30} height={28} rx={3} fill="#fde047" opacity={0.55} />
            </g>
          ))}
        </g>

        {/* Phase 2 overlay: isolation wall + barbed wire (foreground, below monument) */}
        <g opacity={p2Op}>
          {/* perimeter wall */}
          <rect x={130} y={1040} width={820} height={22} rx={4} fill="url(#wallGrad)" opacity={0.9} />
          {/* barbed wire loops */}
          {Array.from({length: 20}).map((_, i) => {
            const x = 140 + i * 40;
            return (
              <g key={i}>
                <circle cx={x} cy={1030} r={9} fill="none" stroke="#4ade80" strokeWidth={2} opacity={0.85} />
                <line x1={x - 12} y1={1030} x2={x + 12} y2={1030} stroke="#4ade80" strokeWidth={1.5} opacity={0.7} />
              </g>
            );
          })}
          {/* watchtower */}
          <rect x={880} y={940} width={60} height={100} fill="#0b2b28" stroke="#2dd4bf" strokeWidth={2} />
          <path d="M 870 940 L 910 900 L 950 940 Z" fill="#166534" stroke="#2dd4bf" strokeWidth={2} />
          <rect x={895} y={960} width={30} height={24} fill="#fde047" opacity={0.6} />
          {/* isolation label */}
          <foreignObject x={330} y={1072} width={420} height={44}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center'}}>
              <div style={{fontSize: 26, fontWeight: 900, color: '#fde047', background: 'rgba(6,12,24,0.94)', border: '1.5px solid #4ade80', borderRadius: 12, padding: '6px 18px'}}>حدود مغلقة ورقابة صارمة</div>
            </div>
          </foreignObject>
        </g>

        {/* SLOT C — Phase 3 takeaway card */}
        <g opacity={p3} transform={`translate(0, ${(1 - p3) * 24})`}>
          <rect x={60} y={1140} width={960} height={280} rx={22} fill="rgba(6,12,24,0.94)" stroke="#fde047" strokeWidth={2} />
          <rect x={60} y={1140} width={960} height={10} rx={4} fill="#fde047" />
          <foreignObject x={84} y={1160} width={912} height={250}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}>
              <div style={{fontSize: 32, fontWeight: 900, color: '#fde047', lineHeight: 1.2}}>منعزلة بفخر عن العالم</div>
              <div style={{fontSize: 26, fontWeight: 700, color: '#ffffff', lineHeight: 1.4}}>
                ترفض التأثير الخارجي وتغلق أبوابها أمام الإعلام والزوار الأجانب
              </div>
              <div style={{display: 'flex', gap: 12, justifyContent: 'flex-end', flexWrap: 'wrap'}}>
                <div style={{fontSize: 24, fontWeight: 800, color: '#4ade80', background: 'rgba(74,222,128,0.14)', border: '1.5px solid #4ade80', borderRadius: 12, padding: '6px 14px'}}>إعلام مُقيَّد</div>
                <div style={{fontSize: 24, fontWeight: 800, color: '#2dd4bf', background: 'rgba(45,212,191,0.14)', border: '1.5px solid #2dd4bf', borderRadius: 12, padding: '6px 14px'}}>تأشيرات نادرة</div>
                <div style={{fontSize: 24, fontWeight: 800, color: '#fde047', background: 'rgba(253,224,71,0.14)', border: '1.5px solid #fde047', borderRadius: 12, padding: '6px 14px'}}>حدود مُحصَّنة</div>
              </div>
            </div>
          </foreignObject>
        </g>
      </svg>
    </AbsoluteFill>
  );
};
