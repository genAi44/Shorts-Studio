/* AUTO-GENERATED ORIGINAL TSX SCENE BY AI VIDEO ARCHITECT */
import React from 'react';
import {AbsoluteFill, interpolate, interpolateColors, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

// ---- scene ----
/* @llm_verified:DynamicScene_cta_0_7:a3718f1c8a03 */
export const DynamicScene_cta_0_7: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
  const currentFrame = useCurrentFrame();
  const {fps: videoFps} = useVideoConfig();
  const frame = props.frame ?? currentFrame;
  const fps = props.fps ?? videoFps;
  const dur = Math.max(1, props.dur ?? 180);
  const p = Math.min(1, Math.max(0, frame / dur));

  // Phase timings
  const ph1In = interpolate(p, [0.0, 0.05], [0.85, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const ph2In = interpolate(p, [0.50, 0.58], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Continuous subtle motion
  const glowPulse = 0.75 + 0.25 * Math.sin(frame / 12);
  const floatY = Math.sin(frame / 20) * 6;
  const beamShift = Math.sin(frame / 30) * 20;

  // Chip stagger for slot B row
  const chip1 = interpolate(p, [0.06, 0.14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const chip2 = interpolate(p, [0.14, 0.22], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const chip3 = interpolate(p, [0.22, 0.30], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // CTA card scale bounce
  const ctaScale = interpolate(p, [0.50, 0.62], [0.85, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const ctaGlow = interpolate(p, [0.50, 0.70], [0.2, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Comment bubble pop
  const bubblePop = interpolate(p, [0.55, 0.68], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden', background: 'radial-gradient(ellipse at 50% 35%, #0a2233 0%, #061420 55%, #030a12 100%)'}}>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920" style={{position: 'absolute', inset: 0}}>
        <defs>
          <radialGradient id="ctaSpot" cx="50%" cy="32%" r="60%">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.42 * glowPulse} />
            <stop offset="55%" stopColor="#0e7490" stopOpacity={0.16 * glowPulse} />
            <stop offset="100%" stopColor="#030a12" stopOpacity={0} />
          </radialGradient>
          <linearGradient id="ctaBeam" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#34d399" stopOpacity="0.0" />
            <stop offset="50%" stopColor="#34d399" stopOpacity="0.14" />
            <stop offset="100%" stopColor="#34d399" stopOpacity="0.0" />
          </linearGradient>
          <linearGradient id="ctaPlate" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#0f766e" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#064e3b" stopOpacity="0.95" />
          </linearGradient>
          <linearGradient id="ctaDome" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.85" />
            <stop offset="100%" stopColor="#0e7490" stopOpacity="0.55" />
          </linearGradient>
          <linearGradient id="ctaColumn" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#0e7490" stopOpacity="0.6" />
            <stop offset="50%" stopColor="#67e8f9" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#0e7490" stopOpacity="0.6" />
          </linearGradient>
        </defs>

        {/* Atmospheric backdrop */}
        <rect x={0} y={0} width={1080} height={1920} fill="url(#ctaSpot)" />

        {/* Light beams */}
        <g opacity={0.8}>
          <polygon points={`${300 + beamShift},0 ${420 + beamShift},0 260,1450 120,1450`} fill="url(#ctaBeam)" />
          <polygon points={`${700 - beamShift},0 ${820 - beamShift},0 960,1450 820,1450`} fill="url(#ctaBeam)" />
        </g>

        {/* Horizon ground plane */}
        <line x1={0} y1={1445} x2={1080} y2={1445} stroke="#0e7490" strokeWidth={2} opacity={0.5} />
        <rect x={0} y={1445} width={1080} height={20} fill="#020609" opacity={0.9} />

        {/* ================= TOP HEADER BANNER ================= */}
        <g opacity={ph1In}>
          <rect x={60} y={110} width={960} height={130} rx={22} fill="rgba(6, 12, 24, 0.94)" stroke="#06b6d4" strokeWidth={2.5} />
          <rect x={60} y={110} width={960} height={130} rx={22} fill="none" stroke="#34d399" strokeWidth={1} opacity={0.4} />
        </g>
        <foreignObject x={70} y={118} width={940} height={120}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', opacity: ph1In}}>
            <div style={{color: '#fde047', fontSize: 44, fontWeight: 800, lineHeight: 1.15, textAlign: 'center', textShadow: '0 2px 8px rgba(0,0,0,0.8)'}}>اكتب دولتك المفضلة</div>
            <div style={{color: '#a5f3fc', fontSize: 26, fontWeight: 600, marginTop: 4}}>أغرب 5 دول في العالم — ختام الرحلة</div>
          </div>
        </foreignObject>

        {/* ================= SLOT A (y 255..600): decorative emblem right side ================= */}
        <g opacity={ph1In} transform={`translate(0, ${floatY})`}>
          {/* Left HUD zone (48..468, 256..600) kept empty for MapOverlayLayer */}
          {/* Right side emblem: globe + question mark badge */}
          <circle cx={800} cy={400} r={128} fill="none" stroke="#06b6d4" strokeWidth={2} opacity={0.35} />
          <circle cx={800} cy={400} r={104} fill="none" stroke="#34d399" strokeWidth={1.5} opacity={0.5} />
          <ellipse cx={800} cy={400} rx={104} ry={40} fill="none" stroke="#22d3ee" strokeWidth={1.2} opacity={0.4} />
          <ellipse cx={800} cy={400} rx={40} ry={104} fill="none" stroke="#22d3ee" strokeWidth={1.2} opacity={0.4} />
          <line x1={696} y1={400} x2={904} y2={400} stroke="#22d3ee" strokeWidth={1} opacity={0.3} />
          <line x1={800} y1={296} x2={800} y2={504} stroke="#22d3ee" strokeWidth={1} opacity={0.3} />
          {/* emblem center */}
          <circle cx={800} cy={400} r={54} fill="rgba(6,12,24,0.95)" stroke="#fde047" strokeWidth={2.5} />
          <foreignObject x={760} y={362} width={80} height={80}>
            <div dir="ltr" style={{fontFamily: "'Cairo', sans-serif", width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fde047', fontSize: 56, fontWeight: 900}}>?</div>
          </foreignObject>
        </g>

        {/* ================= SLOT B (y 615..1060): Two mystery countries + chips ================= */}
        <g opacity={ph1In}>
          <rect x={60} y={615} width={960} height={440} rx={24} fill="rgba(6, 12, 24, 0.94)" stroke="#06b6d4" strokeWidth={2} />
          {/* Section title */}
          <foreignObject x={80} y={628} width={920} height={60}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', color: '#a5f3fc', fontSize: 30, fontWeight: 700}}>
              دولتان أخريان غامضتان في الطريق
            </div>
          </foreignObject>

          {/* Two artifact icons: dome (left) + question tower (right) */}
          {/* Left: mystery dome */}
          <g transform="translate(240, 800)">
            <ellipse cx={0} cy={130} rx={130} ry={18} fill="#020609" opacity={0.9} />
            <rect x={-110} y={105} width={220} height={25} rx={4} fill="url(#ctaPlate)" />
            <rect x={-95} y={70} width={190} height={40} rx={4} fill="#0e7490" opacity={0.85} />
            <path d="M -80 70 Q 0 -60 80 70 Z" fill="url(#ctaDome)" stroke="#22d3ee" strokeWidth={2} />
            <circle cx={0} cy={-2} r={8} fill="#fde047" />
            <line x1={0} y1={-10} x2={0} y2={-46} stroke="#fde047" strokeWidth={3} />
            <g opacity={chip1}>
              <foreignObject x={-140} y={254} width={280} height={48}>
                <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', sans-serif", width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(6,12,24,0.95)', border: '1.5px solid #34d399', borderRadius: 12, color: '#ffffff', fontSize: 26, fontWeight: 700}}>دولة مجهرية</div>
              </foreignObject>
            </g>
          </g>

          {/* Right: mystery tower */}
          <g transform="translate(800, 800)">
            <ellipse cx={0} cy={130} rx={130} ry={18} fill="#020609" opacity={0.9} />
            <rect x={-110} y={105} width={220} height={25} rx={4} fill="url(#ctaPlate)" />
            <rect x={-60} y={-40} width={120} height={145} rx={6} fill="#0e7490" opacity={0.85} />
            {[ -20, 10, 40 ].map((yy, i) => (
              <rect key={i} x={-40} y={yy} width={80} height={14} rx={3} fill="#67e8f9" opacity={0.7} />
            ))}
            <path d="M -60 -40 L 0 -95 L 60 -40 Z" fill="url(#ctaDome)" stroke="#22d3ee" strokeWidth={2} />
            <circle cx={0} cy={-58} r={7} fill="#fde047" />
            <g opacity={chip2}>
              <foreignObject x={-140} y={318} width={280} height={48}>
                <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', sans-serif", width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(6,12,24,0.95)', border: '1.5px solid #06b6d4', borderRadius: 12, color: '#ffffff', fontSize: 26, fontWeight: 700}}>بلا اعتراف دولي</div>
              </foreignObject>
            </g>
          </g>

          {/* Center label chip3 */}
          <g opacity={chip3}>
            <foreignObject x={400} y={1000} width={280} height={48}>
              <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', sans-serif", width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(6,12,24,0.95)', border: '1.5px solid #fde047', borderRadius: 12, color: '#fde047', fontSize: 26, fontWeight: 800}}>تابعنا للمزيد</div>
            </foreignObject>
          </g>
        </g>

        {/* ================= SLOT C (y 1085..1435): CTA comment card ================= */}
        <g opacity={ph2In} transform={`translate(540, 1260) scale(${ctaScale}) translate(-540, -1260)`}>
          <rect x={60} y={1085} width={960} height={350} rx={26} fill="rgba(6, 12, 24, 0.96)" stroke="#34d399" strokeWidth={2.5} />
          <rect x={60} y={1085} width={960} height={350} rx={26} fill="none" stroke="#06b6d4" strokeWidth={1} opacity={0.6 * ctaGlow} />

          {/* Comment bubble icon (right side) */}
          <g opacity={bubblePop} transform={`translate(${880}, ${1200 + (1 - bubblePop) * 30})`}>
            <rect x={-70} y={-55} width={140} height={110} rx={22} fill="url(#ctaColumn)" opacity={0.9} stroke="#22d3ee" strokeWidth={2} />
            <polygon points="-24,55 24,55 0,88" fill="#0e7490" stroke="#22d3ee" strokeWidth={2} />
            <circle cx={-30} cy={0} r={8} fill="#04070d" />
            <circle cx={0} cy={0} r={8} fill="#04070d" />
            <circle cx={30} cy={0} r={8} fill="#04070d" />
          </g>

          {/* Text content */}
          <foreignObject x={110} y={1110} width={640} height={300}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 14}}>
              <div style={{color: '#fde047', fontSize: 40, fontWeight: 900, lineHeight: 1.2}}>اكتب في التعليقات</div>
              <div style={{color: '#ffffff', fontSize: 30, fontWeight: 700, lineHeight: 1.35}}>أي دولة تعتقد أنك لن تستطيع زيارتها؟</div>
              <div style={{display: 'flex', flexDirection: 'row-reverse', gap: 10, marginTop: 6}}>
                <div style={{background: 'rgba(52,211,153,0.16)', border: '1.5px solid #34d399', borderRadius: 12, padding: '6px 14px', color: '#a7f3d0', fontSize: 24, fontWeight: 700}}>إعجاب</div>
                <div style={{background: 'rgba(6,182,212,0.16)', border: '1.5px solid #06b6d4', borderRadius: 12, padding: '6px 14px', color: '#a5f3fc', fontSize: 24, fontWeight: 700}}>متابعة</div>
                <div style={{background: 'rgba(253,224,71,0.14)', border: '1.5px solid #fde047', borderRadius: 12, padding: '6px 14px', color: '#fde047', fontSize: 24, fontWeight: 700}}>تعليق</div>
              </div>
            </div>
          </foreignObject>
        </g>

        {/* Bottom safe zone y >= 1465 left empty for captions */}
      </svg>
    </AbsoluteFill>
  );
};
