/* AUTO-GENERATED ORIGINAL TSX SCENE BY AI VIDEO ARCHITECT */
import React from 'react';
import {AbsoluteFill, interpolate, interpolateColors, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

// ---- scene ----
/* @llm_verified:DynamicScene_lead_0_1:72ef52719f18 */
export const DynamicScene_lead_0_1: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
  const currentFrame = useCurrentFrame();
  const {fps: videoFps} = useVideoConfig();
  const frame = props.frame ?? currentFrame;
  const fps = props.fps ?? videoFps;
  const dur = Math.max(1, props.dur ?? 150);
  const p = Math.min(1, Math.max(0, frame / dur));

  // Phase timings
  const ph1 = interpolate(p, [0.0, 0.05], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const ph2 = interpolate(p, [0.33, 0.40], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const ph3 = interpolate(p, [0.67, 0.74], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Header entrance
  const headerIn = spring({frame, fps, config: {damping: 14, stiffness: 120}});

  // Hero ring rotation
  const ringRot = interpolate(p, [0, 1], [0, 40], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Slot A: counter 5 nodes glow
  const nodeGlow = (i: number) => {
    const start = 0.06 + i * 0.045;
    return interpolate(p, [start, start + 0.06], [0.15, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  };

  // Slot B: comparison bars
  const barLeft = interpolate(p, [0.36, 0.60], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const barRight = interpolate(p, [0.42, 0.66], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});

  // Slot C: ghost card fade
  const ghostIn = interpolate(p, [0.70, 0.78], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Node positions on the ring (5 nodes)
  const cx = 540;
  const cy = 445;
  const R = 175;
  const nodes = [0, 1, 2, 3, 4].map((i) => {
    const ang = (i / 5) * Math.PI * 2 - Math.PI / 2 + (ringRot * Math.PI) / 180;
    return {x: cx + Math.cos(ang) * R, y: cy + Math.sin(ang) * R, ang};
  });

  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden', background: 'radial-gradient(circle at 50% 30%, #0b1f3a 0%, #050b16 55%, #02060d 100%)'}}>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920">
        <defs>
          <radialGradient id="spot" cx="50%" cy="28%" r="60%">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.35" />
            <stop offset="55%" stopColor="#3b82f6" stopOpacity="0.10" />
            <stop offset="100%" stopColor="#02060d" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="100%" stopColor="#3b82f6" />
          </linearGradient>
          <linearGradient id="barL" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="100%" stopColor="#0ea5b7" />
          </linearGradient>
          <linearGradient id="barR" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#1e40af" />
          </linearGradient>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Ambient spotlight */}
        <rect x={0} y={0} width={1080} height={1920} fill="url(#spot)" opacity={0.9} />

        {/* Topographic depth lines (bottom background) */}
        <g opacity={0.14} stroke="#22d3ee" strokeWidth={1.2} fill="none">
          <path d="M0 1300 Q 270 1240 540 1290 T 1080 1260" />
          <path d="M0 1360 Q 270 1310 540 1350 T 1080 1330" />
          <path d="M0 1420 Q 270 1380 540 1410 T 1080 1395" />
          <path d="M0 1180 Q 270 1130 540 1170 T 1080 1150" />
        </g>

        {/* ============ TOP HEADER BANNER ============ */}
        <g opacity={headerIn}>
          <rect x={60} y={110} width={960} height={130} rx={20} fill="rgba(6, 12, 24, 0.94)" stroke="#22d3ee" strokeWidth={2} />
          <rect x={60} y={110} width={10} height={130} rx={5} fill="#22d3ee" />
          <line x1={90} y1={218} x2={990} y2={218} stroke="#22d3ee" strokeOpacity={0.35} strokeWidth={1.5} />
        </g>
        <foreignObject x={80} y={120} width={920} height={120}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-end', paddingRight: 20, opacity: headerIn}}>
            <div style={{fontSize: 48, fontWeight: 900, color: '#ffffff', lineHeight: 1.1}}>
              5 كيانات غامضة
            </div>
            <div style={{fontSize: 26, fontWeight: 700, color: '#fde047', marginTop: 6}}>
              هل هي حقيقية؟
            </div>
          </div>
        </foreignObject>

        {/* ============ SLOT A: HERO RING (y: 265..590) ============ */}
        <g opacity={ph1}>
          {/* Orbital rings */}
          <circle cx={cx} cy={cy} r={R + 40} fill="none" stroke="#22d3ee" strokeOpacity={0.15} strokeWidth={1.5} strokeDasharray="4 8" />
          <circle cx={cx} cy={cy} r={R} fill="none" stroke="url(#ringGrad)" strokeWidth={3} opacity={0.85} />
          <circle cx={cx} cy={cy} r={R - 55} fill="none" stroke="#3b82f6" strokeOpacity={0.4} strokeWidth={2} strokeDasharray="2 6" />

          {/* Center emblem: number 5 */}
          <circle cx={cx} cy={cy} r={78} fill="rgba(6, 12, 24, 0.95)" stroke="#22d3ee" strokeWidth={3} filter="url(#glow)" />
          <circle cx={cx} cy={cy} r={64} fill="none" stroke="#3b82f6" strokeWidth={1.5} opacity={0.6} />

          {/* 5 glowing nodes */}
          {nodes.map((n, i) => {
            const g = nodeGlow(i);
            return (
              <g key={i} opacity={g}>
                <circle cx={n.x} cy={n.y} r={26} fill="rgba(6, 12, 24, 0.95)" stroke="#22d3ee" strokeWidth={2.5} filter="url(#glow)" />
                <circle cx={n.x} cy={n.y} r={12} fill="#22d3ee" opacity={0.9} />
                <circle cx={n.x} cy={n.y} r={18} fill="none" stroke="#fde047" strokeWidth={1.5} opacity={0.7} />
              </g>
            );
          })}
        </g>

        {/* Center counter "5" */}
        <foreignObject x={cx - 78} y={cy - 62} width={156} height={130}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', direction: 'ltr', opacity: ph1}}>
            <span style={{fontSize: 92, fontWeight: 900, color: '#fde047', lineHeight: 1, textShadow: '0 0 18px rgba(253,224,71,0.7)'}}>5</span>
          </div>
        </foreignObject>

        {/* Slot A left caption (opposite HUD corner) */}
        <foreignObject x={60} y={505} width={480} height={80}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", background: 'rgba(6, 12, 24, 0.94)', border: '1.5px solid #22d3ee', borderRadius: 16, padding: '10px 18px', color: '#ffffff', fontSize: 28, fontWeight: 800, opacity: ph1}}>
            خلال ثوانٍ قليلة…
          </div>
        </foreignObject>

        {/* ============ SLOT B: SPLIT COMPARATIVE STAGE (y: 615..1060) ============ */}
        <g opacity={ph2}>
          {/* Divider */}
          <line x1={540} y1={640} x2={540} y2={1040} stroke="#22d3ee" strokeOpacity={0.35} strokeWidth={2} strokeDasharray="6 8" />

          {/* Left panel: معزول بشدة */}
          <rect x={70} y={640} width={440} height={400} rx={20} fill="rgba(6, 12, 24, 0.94)" stroke="#22d3ee" strokeWidth={2} />
          <circle cx={290} cy={720} r={44} fill="rgba(34, 211, 238, 0.15)" stroke="#22d3ee" strokeWidth={2.5} />
          {/* Isolated icon: lock + wall */}
          <g transform="translate(290, 720)">
            <rect x={-16} y={-4} width={32} height={22} rx={3} fill="none" stroke="#22d3ee" strokeWidth={3} />
            <path d="M -10 -4 V -12 A 10 10 0 0 1 10 -12 V -4" fill="none" stroke="#22d3ee" strokeWidth={3} />
            <circle cx={0} cy={7} r={3} fill="#22d3ee" />
          </g>

          {/* Wall segments */}
          <g stroke="#22d3ee" strokeWidth={2} opacity={0.5}>
            <line x1={100} y1={790} x2={480} y2={790} strokeDasharray="10 6" />
          </g>

          {/* Proportional bar: معزول */}
          <rect x={100} y={820} width={380} height={26} rx={13} fill="rgba(34, 211, 238, 0.12)" stroke="#22d3ee" strokeOpacity={0.4} strokeWidth={1.5} />
          <rect x={100} y={820} width={380 * barLeft} height={26} rx={13} fill="url(#barL)" />

          {/* Right panel: وهم قانوني */}
          <rect x={570} y={640} width={440} height={400} rx={20} fill="rgba(6, 12, 24, 0.94)" stroke="#3b82f6" strokeWidth={2} />
          <circle cx={790} cy={720} r={44} fill="rgba(59, 130, 246, 0.15)" stroke="#3b82f6" strokeWidth={2.5} />
          {/* Ghost icon: dashed document */}
          <g transform="translate(790, 720)">
            <rect x={-14} y={-18} width={28} height={34} rx={3} fill="none" stroke="#3b82f6" strokeWidth={2.5} strokeDasharray="4 3" />
            <line x1={-8} y1={-8} x2={8} y2={-8} stroke="#3b82f6" strokeWidth={2} opacity={0.7} />
            <line x1={-8} y1={0} x2={8} y2={0} stroke="#3b82f6" strokeWidth={2} opacity={0.7} />
            <line x1={-8} y1={8} x2={2} y2={8} stroke="#3b82f6" strokeWidth={2} opacity={0.7} />
          </g>

          <g stroke="#3b82f6" strokeWidth={2} opacity={0.5}>
            <line x1={600} y1={790} x2={980} y2={790} strokeDasharray="10 6" />
          </g>

          {/* Proportional bar: وهم */}
          <rect x={600} y={820} width={380} height={26} rx={13} fill="rgba(59, 130, 246, 0.12)" stroke="#3b82f6" strokeOpacity={0.4} strokeWidth={1.5} />
          <rect x={600} y={820} width={380 * barRight} height={26} rx={13} fill="url(#barR)" />

          {/* Panel labels */}
        </g>

        <foreignObject x={90} y={930} width={400} height={90}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', opacity: ph2}}>
            <div style={{fontSize: 30, fontWeight: 900, color: '#ffffff'}}>معزول بشدة</div>
            <div style={{fontSize: 24, fontWeight: 700, color: '#22d3ee', marginTop: 4}}>حدود مغلقة</div>
          </div>
        </foreignObject>

        <foreignObject x={590} y={930} width={400} height={90}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', opacity: ph2}}>
            <div style={{fontSize: 30, fontWeight: 900, color: '#ffffff'}}>وهم قانوني</div>
            <div style={{fontSize: 24, fontWeight: 700, color: '#3b82f6', marginTop: 4}}>لا يراه أحد</div>
          </div>
        </foreignObject>

        {/* ============ SLOT C: PHASE 3 TAKEAWAY (y: 1085..1435) ============ */}
        <g opacity={ph3}>
          <rect x={60} y={1085} width={960} height={340} rx={22} fill="rgba(6, 12, 24, 0.94)" stroke="#fde047" strokeWidth={2} />
          <rect x={60} y={1085} width={960} height={10} rx={5} fill="#fde047" />
        </g>

        {/* Recap chips */}
        <foreignObject x={80} y={1115} width={920} height={90}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12, opacity: ph3}}>
            <div style={{flex: 1, background: 'rgba(34, 211, 238, 0.18)', border: '1.5px solid #22d3ee', borderRadius: 14, padding: '10px 8px', textAlign: 'center', color: '#ffffff', fontSize: 26, fontWeight: 800}}>
              معزول
            </div>
            <div style={{flex: 1, background: 'rgba(59, 130, 246, 0.18)', border: '1.5px solid #3b82f6', borderRadius: 14, padding: '10px 8px', textAlign: 'center', color: '#ffffff', fontSize: 26, fontWeight: 800}}>
              وهمي
            </div>
            <div style={{flex: 1, background: 'rgba(253, 224, 71, 0.18)', border: '1.5px solid #fde047', borderRadius: 14, padding: '10px 8px', textAlign: 'center', color: '#ffffff', fontSize: 26, fontWeight: 800}}>
              غامض
            </div>
          </div>
        </foreignObject>

        {/* Main takeaway text */}
        <foreignObject x={80} y={1221} width={920} height={190}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', opacity: ph3}}>
            <div style={{fontSize: 34, fontWeight: 900, color: '#ffffff', textAlign: 'center', lineHeight: 1.35}}>
              بعضها معزول بشدة، وبعضها مجرد وهم قانوني
            </div>
            <div style={{fontSize: 28, fontWeight: 800, color: '#fde047', marginTop: 10, opacity: ghostIn}}>
              لا يراه أحد
            </div>
          </div>
        </foreignObject>

        {/* Small animated callout emblem in Slot C corner */}
        <g opacity={ph3} transform="translate(960, 1395)">
          <circle r={22} fill="rgba(253, 224, 71, 0.2)" stroke="#fde047" strokeWidth={2} />
          <text x={0} y={8} textAnchor="middle" fontSize={22} fontWeight={900} fill="#fde047">?</text>
        </g>
      </svg>
    </AbsoluteFill>
  );
};
