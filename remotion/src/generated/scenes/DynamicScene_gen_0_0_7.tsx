/* AUTO-GENERATED ORIGINAL TSX SCENE BY AI VIDEO ARCHITECT */
import React from 'react';
import {AbsoluteFill, interpolate, interpolateColors, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

// ---- scene ----
/* @llm_verified:DynamicScene_gen_0_0_7:4a559434ecfb */
export const DynamicScene_gen_0_0_7: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
  const currentFrame = useCurrentFrame();
  const {fps: videoFps} = useVideoConfig();
  const frame = props.frame ?? currentFrame;
  const fps = props.fps ?? videoFps;
  const dur = Math.max(1, props.dur ?? 180);
  const p = Math.min(1, Math.max(0, frame / dur));

  const primary = '#22d3ee';
  const secondary = '#3b82f6';

  // Entrance animations
  const headerOpacity = interpolate(frame, [0, 6], [0.85, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const heroScale = spring({frame, fps, config: {damping: 14, mass: 0.6}, from: 0.85, to: 1});

  // Phase 2: Iberian peninsula comparison
  const ph2Opacity = interpolate(p, [0.30, 0.38], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const ph2Y = interpolate(p, [0.30, 0.40], [30, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Phase 3: takeaway card
  const ph3Opacity = interpolate(p, [0.66, 0.74], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const ph3Y = interpolate(p, [0.66, 0.76], [40, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Pulse for emblem
  const pulse = 0.85 + 0.15 * Math.sin(frame / 8);

  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden', background: 'linear-gradient(180deg, #041018 0%, #071a2a 40%, #04101c 100%)'}}>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920">
        <defs>
          <radialGradient id="s8-glow" cx="50%" cy="35%" r="55%">
            <stop offset="0%" stopColor={primary} stopOpacity={0.28} />
            <stop offset="55%" stopColor={secondary} stopOpacity={0.10} />
            <stop offset="100%" stopColor="#000000" stopOpacity={0} />
          </radialGradient>
          <linearGradient id="s8-beam" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={primary} stopOpacity={0.35} />
            <stop offset="100%" stopColor={primary} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="s8-spain" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#b45309" />
          </linearGradient>
          <linearGradient id="s8-portugal" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#22c55e" />
            <stop offset="100%" stopColor="#15803d" />
          </linearGradient>
          <linearGradient id="s8-emblem" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={primary} stopOpacity={0.9} />
            <stop offset="100%" stopColor={secondary} stopOpacity={0.6} />
          </linearGradient>
        </defs>

        {/* Atmospheric backdrop */}
        <rect x={0} y={0} width={1080} height={1920} fill="url(#s8-glow)" />
        <path d="M0 1400 Q 540 1300 1080 1400 L 1080 1920 L 0 1920 Z" fill="#03121f" opacity={0.9} />
        <path d="M0 1520 Q 540 1450 1080 1520" stroke={primary} strokeOpacity={0.15} strokeWidth={2} fill="none" />
        <path d="M0 1620 Q 540 1560 1080 1620" stroke={primary} strokeOpacity={0.10} strokeWidth={2} fill="none" />

        {/* Light beams */}
        <polygon points="380,0 460,0 620,900 300,900" fill="url(#s8-beam)" opacity={0.35} />
        <polygon points="640,0 700,0 800,900 560,900" fill="url(#s8-beam)" opacity={0.22} />

        {/* Top Headline Banner */}
        <g opacity={headerOpacity}>
          <rect x={60} y={110} width={960} height={120} rx={20} fill="rgba(6, 12, 24, 0.94)" stroke={primary} strokeWidth={2} />
          <rect x={60} y={110} width={8} height={120} fill={primary} />
        </g>
        <foreignObject x={80} y={122} width={920} height={100}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-end', paddingLeft: 20, paddingRight: 20}}>
            <div style={{fontSize: 44, fontWeight: 800, color: '#fde047', lineHeight: 1.15}}>جيرانها الإسبان والبرتغاليين تماماً</div>
            <div style={{fontSize: 26, color: '#93c5fd', marginTop: 4}}>شبه الجزيرة الأيبيرية · الحدود الجغرافية</div>
          </div>
        </foreignObject>

        {/* Slot A (left side, right side reserved for HUD): emblem badge */}
        <g opacity={headerOpacity}>
          <circle cx={280} cy={420} r={110} fill="rgba(6, 12, 24, 0.9)" stroke={primary} strokeWidth={3} opacity={pulse} />
          <circle cx={280} cy={420} r={80} fill="none" stroke={primary} strokeWidth={2} opacity={0.5} />
          <circle cx={280} cy={420} r={130} fill="none" stroke={primary} strokeWidth={1} opacity={0.25} />
          {/* Iberian peninsula silhouette simplified */}
          <path d="M230 380 L 330 380 L 340 440 L 320 470 L 250 470 L 220 440 Z" fill="url(#s8-emblem)" opacity={0.9} />
          <text x={280} y={440} textAnchor="middle" fontSize={28} fontWeight={800} fill="#04101c">IB</text>
        </g>

        {/* Slot B: Iberian Peninsula comparison stage */}
        <g transform={`translate(0, ${ph2Y})`} opacity={ph2Opacity}>
          <rect x={60} y={620} width={960} height={420} rx={22} fill="rgba(6, 12, 24, 0.94)" stroke={secondary} strokeWidth={2} />
          {/* Title inside card */}
          <foreignObject x={80} y={640} width={920} height={60}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", fontSize: 30, fontWeight: 700, color: '#fde047', textAlign: 'right'}}>جارتان في شبه الجزيرة الأيبيرية</div>
          </foreignObject>

          {/* Map-like peninsula illustration */}
          <g transform="translate(540, 880)">
            {/* Sea context */}
            <ellipse cx={0} cy={0} rx={420} ry={160} fill="#0a2540" opacity={0.6} />
            {/* Spain shape */}
            <path d="M-260 -80 L -60 -100 L 60 -90 L 160 -60 L 220 -10 L 200 60 L 120 100 L 0 110 L -140 100 L -240 60 L -280 -10 Z" fill="url(#s8-spain)" opacity={0.9} stroke="#fbbf24" strokeWidth={2} />
            {/* Portugal shape */}
            <path d="M-300 40 L -280 -20 L -260 -60 L -240 -40 L -230 40 L -260 90 L -290 80 Z" fill="url(#s8-portugal)" opacity={0.95} stroke="#4ade80" strokeWidth={2} />
            {/* Border line */}
            <path d="M-230 -40 L -225 40 L -240 90" stroke="#ffffff" strokeWidth={3} strokeDasharray="8 5" opacity={0.85} />
            {/* Labels */}
            <text x={40} y={0} textAnchor="middle" fontSize={32} fontWeight={800} fill="#04101c">إسبانيا</text>
            <text x={-265} y={20} textAnchor="middle" fontSize={20} fontWeight={800} fill="#ffffff" transform="rotate(-90 -265 20)">البرتغال</text>
            {/* Compass rose */}
            <g transform="translate(320, -100)">
              <circle r={28} fill="rgba(6,12,24,0.9)" stroke={primary} strokeWidth={2} />
              <polygon points="0,-20 6,0 0,20 -6,0" fill={primary} />
            </g>
          </g>

          {/* Bottom labels */}
          <foreignObject x={80} y={980} width={440} height={50}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", fontSize: 26, fontWeight: 700, color: '#fbbf24', background: 'rgba(180,83,9,0.25)', borderRadius: 10, padding: '6px 14px', textAlign: 'center'}}>المملكة الإسبانية</div>
          </foreignObject>
          <foreignObject x={560} y={980} width={440} height={50}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", fontSize: 26, fontWeight: 700, color: '#4ade80', background: 'rgba(21,128,61,0.25)', borderRadius: 10, padding: '6px 14px', textAlign: 'center'}}>الجمهورية البرتغالية</div>
          </foreignObject>
        </g>

        {/* Slot C: Takeaway card */}
        <g transform={`translate(0, ${ph3Y})`} opacity={ph3Opacity}>
          <rect x={60} y={1090} width={960} height={340} rx={22} fill="rgba(6, 12, 24, 0.96)" stroke={primary} strokeWidth={2.5} />
          <rect x={60} y={1090} width={10} height={340} fill={primary} />

          {/* Emblem icon */}
          <g transform="translate(150, 1180)">
            <circle r={48} fill="rgba(34,211,238,0.15)" stroke={primary} strokeWidth={2} />
            <path d="M-18 -20 L 18 -20 L 22 0 L 12 18 L -12 18 L -22 0 Z" fill={primary} opacity={0.85} />
            <circle cx={0} cy={0} r={6} fill="#04101c" />
          </g>

          <foreignObject x={220} y={1120} width={780} height={280}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", color: '#ffffff', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 10}}>
              <div style={{fontSize: 34, fontWeight: 800, color: '#fde047', lineHeight: 1.25}}>جارتان تلامسان حدودها تماماً</div>
              <div style={{fontSize: 28, color: '#e2e8f0', lineHeight: 1.4}}>إسبانيا والبرتغال تشتركان معها في شبه الجزيرة الأيبيرية</div>
              <div style={{display: 'flex', gap: 12, marginTop: 6, flexWrap: 'wrap'}}>
                <div style={{fontSize: 24, fontWeight: 700, color: primary, background: 'rgba(34,211,238,0.15)', border: '1px solid rgba(34,211,238,0.5)', borderRadius: 10, padding: '4px 12px'}}>حدود مشتركة</div>
                <div style={{fontSize: 24, fontWeight: 700, color: '#fbbf24', background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.5)', borderRadius: 10, padding: '4px 12px'}}>شبه الجزيرة الأيبيرية</div>
              </div>
            </div>
          </foreignObject>
        </g>

        {/* HUD corner (top-right) — small map context dots */}
        <g opacity={headerOpacity}>
          <rect x={700} y={280} width={320} height={300} rx={18} fill="rgba(6, 12, 24, 0.88)" stroke={secondary} strokeWidth={1.5} />
          <circle cx={860} cy={430} r={110} fill="none" stroke={primary} strokeWidth={1} opacity={0.35} />
          <circle cx={860} cy={430} r={75} fill="none" stroke={secondary} strokeWidth={1} opacity={0.4} />
          <circle cx={860} cy={430} r={40} fill="none" stroke={primary} strokeWidth={1.5} opacity={0.6} />
          <circle cx={860} cy={430} r={5} fill={primary} />
          <circle cx={860} cy={355} r={4} fill="#fbbf24" />
          <circle cx={925} cy={470} r={4} fill="#4ade80" />
          <line x1={860} y1={430} x2={860} y2={355} stroke="#fbbf24" strokeWidth={1.5} strokeDasharray="4 4" />
          <line x1={860} y1={430} x2={925} y2={470} stroke="#4ade80" strokeWidth={1.5} strokeDasharray="4 4" />
        </g>
        <foreignObject x={710} y={300} width={300} height={60}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", fontSize: 24, fontWeight: 700, color: '#fde047', textAlign: 'center', paddingTop: 6}}>الجوار الأيبيري</div>
        </foreignObject>
        <foreignObject x={710} y={520} width={300} height={40}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", fontSize: 22, color: '#93c5fd', textAlign: 'center'}}>إسبانيا · البرتغال</div>
        </foreignObject>
      </svg>
    </AbsoluteFill>
  );
};
