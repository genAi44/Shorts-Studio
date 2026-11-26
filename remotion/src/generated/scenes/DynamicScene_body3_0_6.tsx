/* AUTO-GENERATED ORIGINAL TSX SCENE BY AI VIDEO ARCHITECT */
import React from 'react';
import {AbsoluteFill, interpolate, interpolateColors, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

// ---- scene ----
/* @llm_verified:DynamicScene_body3_0_6:d578e7c1f195 */
export const DynamicScene_body3_0_6: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
  const currentFrame = useCurrentFrame();
  const {fps: videoFps} = useVideoConfig();
  const frame = props.frame ?? currentFrame;
  const fps = props.fps ?? videoFps;
  const dur = Math.max(1, props.dur ?? 150);
  const p = Math.min(1, Math.max(0, frame / dur));

  const clampOpts = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

  // Header entrance
  const headerOp = interpolate(frame, [0, 8], [0.85, 1], clampOpts);

  // Phase timings
  const ph1 = interpolate(p, [0.0, 0.06], [0, 1], clampOpts);
  const ph2 = interpolate(p, [0.33, 0.40], [0, 1], clampOpts);
  const ph3 = interpolate(p, [0.67, 0.74], [0, 1], clampOpts);

  // Hero ring rotation
  const ringRot = interpolate(p, [0, 1], [0, 40], clampOpts);

  // Zero counter: starts near target, small wobble
  const zeroScale = spring({frame: frame - 4, fps, config: {damping: 12, stiffness: 90}});

  // Comparison bars in Slot B (Phase 2)
  // "دولة مجهرية" tiny vs "عالم" big — conceptual, no fake numbers
  const barBig = interpolate(ph2, [0, 1], [0, 1], clampOpts);
  const barSmall = interpolate(ph2, [0, 1], [0, 1], clampOpts);

  // Phase 3 stamp
  const stampScale = interpolate(ph3, [0, 1], [0.5, 1], clampOpts);

  // Ambient glow pulse
  const glow = 0.6 + 0.4 * Math.sin(frame / 18);

  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden', background: 'linear-gradient(180deg, #05070f 0%, #0a1020 55%, #04060d 100%)'}}>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920">
        <defs>
          <radialGradient id="bgGlow" cx="50%" cy="38%" r="60%">
            <stop offset="0%" stopColor="#eab308" stopOpacity={0.22 * glow} />
            <stop offset="45%" stopColor="#22d3ee" stopOpacity={0.10} />
            <stop offset="100%" stopColor="#04060d" stopOpacity={0} />
          </radialGradient>
          <linearGradient id="ringGold" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#fde047" />
            <stop offset="50%" stopColor="#eab308" />
            <stop offset="100%" stopColor="#a16207" />
          </linearGradient>
          <linearGradient id="ringCyan" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#67e8f9" />
            <stop offset="100%" stopColor="#0891b2" />
          </linearGradient>
          <linearGradient id="barBigGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="100%" stopColor="#eab308" />
          </linearGradient>
          <linearGradient id="horizonGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0a1020" stopOpacity="0" />
            <stop offset="100%" stopColor="#0f1a2e" stopOpacity="0.9" />
          </linearGradient>
        </defs>

        {/* Ambient backdrop */}
        <rect x={0} y={0} width={1080} height={1920} fill="url(#bgGlow)" />
        {/* Ground horizon */}
        <rect x={0} y={1180} width={1080} height={260} fill="url(#horizonGrad)" />
        {/* Topographic depth lines */}
        {[0, 1, 2, 3].map((i) => (
          <path
            key={`topo-${i}`}
            d={`M -40 ${1260 + i * 55} Q 270 ${1210 + i * 55} 540 ${1260 + i * 55} T 1120 ${1260 + i * 55}`}
            stroke="#1e293b"
            strokeWidth={1.5}
            fill="none"
            opacity={0.5}
          />
        ))}

        {/* ── TOP HEADER BANNER ── */}
        <g opacity={headerOp}>
          <rect x={60} y={95} width={960} height={140} rx={22} fill="rgba(6,12,24,0.94)" stroke="#eab308" strokeWidth={2} />
          <rect x={60} y={95} width={960} height={6} rx={3} fill="url(#ringGold)" />
        </g>
        <foreignObject x={60} y={105} width={960} height={140}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', opacity: headerOp}}>
            <div style={{fontSize: 46, fontWeight: 800, color: '#fde047', lineHeight: 1.15}}>نييروي المجهرية</div>
            <div style={{fontSize: 26, fontWeight: 600, color: '#94e8f5', marginTop: 4}}>دولة صغيرة تعتبر نفسها ذات سيادة</div>
          </div>
        </foreignObject>

        {/* ── SLOT A (y 265..590) — LEFT SIDE HERO: STAT RING + GIANT ZERO ── */}
        <g opacity={ph1}>
          {/* Stat ring pedestal at left, avoiding right HUD map zone */}
          <circle cx={290} cy={430} r={155} fill="none" stroke="#1e293b" strokeWidth={3} opacity={0.7} />
          <g transform={`rotate(${ringRot} 290 430)`}>
            <circle cx={290} cy={430} r={155} fill="none" stroke="url(#ringGold)" strokeWidth={7} strokeDasharray="60 30" strokeLinecap="round" />
            <circle cx={290} cy={430} r={120} fill="none" stroke="url(#ringCyan)" strokeWidth={4} strokeDasharray="18 22" strokeLinecap="round" opacity={0.85} />
          </g>
          {/* Inner disc */}
          <circle cx={290} cy={430} r={95} fill="rgba(6,12,24,0.95)" stroke="#eab308" strokeWidth={2} />
        </g>
        <foreignObject x={190} y={355} width={200} height={150}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', opacity: ph1 * Math.min(1, zeroScale)}}>
            <div style={{fontSize: 96, fontWeight: 900, color: '#fde047', lineHeight: 1, direction: 'ltr', textShadow: '0 0 24px rgba(234,179,8,0.6)'}}>0</div>
            <div style={{fontSize: 24, fontWeight: 700, color: '#67e8f9', marginTop: 2}}>حكومات معترفة</div>
          </div>
        </foreignObject>

        {/* ── SLOT A right small caption card (below HUD map zone, x 612..1032 but y>610 not allowed here; keep small tag at y 520) ── */}
        <foreignObject x={600} y={500} width={420} height={90}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', opacity: ph1}}>
            <div style={{background: 'rgba(6,12,24,0.94)', border: '1.5px solid #22d3ee', borderRadius: 14, padding: '10px 18px', fontSize: 28, fontWeight: 700, color: '#ffffff', whiteSpace: 'nowrap'}}>
              نييروي — مثال للدول المجهرية
            </div>
          </div>
        </foreignObject>

        {/* ── SLOT B (y 615..1060) — COMPARATIVE STAGE ── */}
        {/* Left panel: Neyroy micro state */}
        <g opacity={ph2}>
          <rect x={60} y={620} width={450} height={430} rx={22} fill="rgba(6,12,24,0.94)" stroke="#eab308" strokeWidth={2} />
          <rect x={60} y={620} width={450} height={6} rx={3} fill="url(#ringGold)" />
          {/* tiny flag / micro state emblem */}
          <g transform="translate(285 780)">
            <circle r={70} fill="#0a1020" stroke="#eab308" strokeWidth={2} />
            <circle r={48} fill="none" stroke="#22d3ee" strokeWidth={3} strokeDasharray="6 6" />
            <circle r={14} fill="#fde047" />
            {/* tiny dotted sovereignty halo */}
            <circle r={90} fill="none" stroke="#334155" strokeWidth={1.5} strokeDasharray="3 6" />
          </g>
        </g>
        <foreignObject x={70} y={620} width={430} height={70}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', opacity: ph2}}>
            <div style={{fontSize: 32, fontWeight: 800, color: '#fde047'}}>دولة مجهرية</div>
          </div>
        </foreignObject>
        <foreignObject x={70} y={890} width={430} height={140}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', opacity: ph2}}>
            <div style={{fontSize: 26, fontWeight: 700, color: '#ffffff', lineHeight: 1.4}}>تعتبر نفسها مستقلة وذات سيادة كاملة</div>
          </div>
        </foreignObject>

        {/* Right panel: No recognition */}
        <g opacity={ph2}>
          <rect x={570} y={620} width={450} height={430} rx={22} fill="rgba(6,12,24,0.94)" stroke="#22d3ee" strokeWidth={2} />
          <rect x={570} y={620} width={450} height={6} rx={3} fill="url(#ringCyan)" />
          {/* crossed emblem: no recognition */}
          <g transform="translate(795 780)">
            <circle r={70} fill="#0a1020" stroke="#22d3ee" strokeWidth={2} />
            <circle r={48} fill="none" stroke="#ef4444" strokeWidth={4} />
            <line x1={-34} y1={-34} x2={34} y2={34} stroke="#ef4444" strokeWidth={6} strokeLinecap="round" />
            <line x1={34} y1={-34} x2={-34} y2={34} stroke="#ef4444" strokeWidth={6} strokeLinecap="round" />
          </g>
        </g>
        <foreignObject x={580} y={620} width={430} height={70}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', opacity: ph2}}>
            <div style={{fontSize: 32, fontWeight: 800, color: '#67e8f9'}}>بلا اعتراف</div>
          </div>
        </foreignObject>
        <foreignObject x={580} y={890} width={430} height={140}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', opacity: ph2}}>
            <div style={{fontSize: 26, fontWeight: 700, color: '#ffffff', lineHeight: 1.4}}>لا حكومات ولا منظمات دولية تمنحها الاعتراف</div>
          </div>
        </foreignObject>

        {/* Proportional conceptual bars under both panels (Phase 2 continuation) */}
        <g opacity={ph2}>
          {/* Big bar: world recognition (conceptual, not numeric) */}
          <rect x={60} y={1070} width={450 * barBig} height={22} rx={11} fill="url(#barBigGrad)" />
          <rect x={570} y={1070} width={450 * barSmall} height={22} rx={11} fill="#334155" />
        </g>

        {/* ── SLOT C (y 1085..1435) — PHASE 3 TAKEAWAY ── */}
        <g opacity={ph3}>
          <rect x={60} y={1100} width={960} height={320} rx={24} fill="rgba(6,12,24,0.95)" stroke="#eab308" strokeWidth={2.5} />
          <rect x={60} y={1100} width={960} height={7} rx={3} fill="url(#ringGold)" />
        </g>
        {/* Stamp emblem left of card */}
        <g opacity={ph3} transform={`translate(180 1260) scale(${stampScale})`}>
          <circle r={78} fill="none" stroke="#eab308" strokeWidth={3} strokeDasharray="8 8" />
          <circle r={54} fill="rgba(234,179,8,0.15)" stroke="#fde047" strokeWidth={2} />
          <text x={0} y={14} textAnchor="middle" fontSize={44} fontWeight={900} fill="#fde047" fontFamily="sans-serif">0</text>
        </g>
        <foreignObject x={290} y={1110} width={710} height={300}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start', textAlign: 'right', padding: '0 6px', opacity: ph3}}>
            <div style={{fontSize: 34, fontWeight: 800, color: '#fde047', marginBottom: 8}}>حتى اليوم</div>
            <div style={{fontSize: 28, fontWeight: 700, color: '#ffffff', lineHeight: 1.5}}>لا تحظى نييروي باعتراف أي حكومة أو منظمة دولية حول العالم.</div>
            <div style={{marginTop: 14, display: 'flex', gap: 10, flexDirection: 'row-reverse', flexWrap: 'wrap'}}>
              <span style={{background: 'rgba(34,211,238,0.18)', border: '1px solid #22d3ee', color: '#67e8f9', fontSize: 24, fontWeight: 700, padding: '6px 14px', borderRadius: 12}}>دولة مجهرية</span>
              <span style={{background: 'rgba(234,179,8,0.18)', border: '1px solid #eab308', color: '#fde047', fontSize: 24, fontWeight: 700, padding: '6px 14px', borderRadius: 12}}>ادعاء سيادة</span>
              <span style={{background: 'rgba(239,68,68,0.18)', border: '1px solid #ef4444', color: '#fca5a5', fontSize: 24, fontWeight: 700, padding: '6px 14px', borderRadius: 12}}>صفر اعتراف</span>
            </div>
          </div>
        </foreignObject>

        {/* Bottom safe zone y>=1465 stays empty */}
      </svg>
    </AbsoluteFill>
  );
};
