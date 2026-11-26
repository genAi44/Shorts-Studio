/* AUTO-GENERATED ORIGINAL TSX SCENE BY AI VIDEO ARCHITECT */
import React from 'react';
import {AbsoluteFill, interpolate, interpolateColors, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

// ---- scene ----
/* @llm_verified:DynamicScene_open_loop2_0_5:8f9687c185c9 */
export const DynamicScene_open_loop2_0_5: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
  const currentFrame = useCurrentFrame();
  const {fps: videoFps} = useVideoConfig();
  const frame = props.frame ?? currentFrame;
  const fps = props.fps ?? videoFps;
  const dur = Math.max(1, props.dur ?? 150);
  const p = Math.min(1, Math.max(0, frame / dur));

  const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

  // Entrances
  const bgGlow = interpolate(frame, [0, 10], [0.85, 1], clamp);
  const headerOp = interpolate(frame, [0, 6], [0.85, 1], clamp);
  const heroOp = interpolate(frame, [0, 8], [0.85, 1], clamp);
  const heroScale = interpolate(frame, [0, 12], [0.94, 1], clamp);

  // Scale beam balance (Phase 1) tilting
  const tilt = Math.sin(frame / 14) * 6 * (1 - p * 0.4);

  // Phase 1 -> fade out at 0.46..0.52
  const p1Op = interpolate(p, [0.44, 0.5], [1, 0], clamp);
  const p2Op = interpolate(p, [0.5, 0.56], [0, 1], clamp);

  // Phase 3 takeaway
  const p3Op = interpolate(p, [0.72, 0.78], [0, 1], clamp);
  const p3Scale = interpolate(frame, [Math.floor(dur * 0.72), Math.floor(dur * 0.72) + 10], [0.9, 1], clamp);

  // Seal pulse
  const sealPulse = 0.5 + Math.abs(Math.sin(frame / 16)) * 0.5;

  // Balance needle angle for hero
  const needle = Math.sin(frame / 18) * 10;

  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden', background: 'linear-gradient(180deg, #050914 0%, #0a1428 45%, #030712 100%)'}}>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920">
        <defs>
          <radialGradient id="sc9glow" cx="50%" cy="35%" r="70%">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.35" />
            <stop offset="55%" stopColor="#818cf8" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#030712" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="sc9spot" cx="50%" cy="30%" r="55%">
            <stop offset="0%" stopColor="#60a5fa" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#060c18" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="sc9beam" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#93c5fd" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#818cf8" stopOpacity="0.9" />
          </linearGradient>
          <linearGradient id="sc9paper" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#f8fafc" />
            <stop offset="100%" stopColor="#cbd5e1" />
          </linearGradient>
          <linearGradient id="sc9seal" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#64748b" />
            <stop offset="100%" stopColor="#1e293b" />
          </linearGradient>
          <linearGradient id="sc9ground" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0f1e38" stopOpacity="0" />
            <stop offset="100%" stopColor="#0b1526" stopOpacity="0.9" />
          </linearGradient>
          <filter id="sc9soft"><feGaussianBlur stdDeviation="6" /></filter>
        </defs>

        {/* Atmospheric backdrop */}
        <rect x={0} y={0} width={1080} height={1920} fill="url(#sc9glow)" opacity={bgGlow} />
        <rect x={0} y={0} width={1080} height={1000} fill="url(#sc9spot)" opacity={bgGlow} />

        {/* Light beams */}
        <g opacity={0.22}>
          <polygon points="540,180 300,900 420,900" fill="url(#sc9beam)" />
          <polygon points="540,180 660,900 780,900" fill="url(#sc9beam)" />
        </g>

        {/* Horizon / ground plane */}
        <path d="M0,1380 C260,1330 820,1330 1080,1380 L1080,1500 L0,1500 Z" fill="url(#sc9ground)" />
        <line x1={0} y1={1380} x2={1080} y2={1380} stroke="#38bdf8" strokeOpacity={0.25} strokeWidth={1.5} />

        {/* Subtle wireframe meridians top */}
        <g stroke="#38bdf8" strokeOpacity={0.12} fill="none" strokeWidth={1}>
          <ellipse cx={540} cy={420} rx={520} ry={180} />
          <ellipse cx={540} cy={420} rx={380} ry={130} />
          <ellipse cx={540} cy={420} rx={240} ry={80} />
        </g>

        {/* ================= HEADER BANNER ================= */}
        <g opacity={headerOp}>
          <rect x={60} y={110} width={960} height={130} rx={22} fill="rgba(6,12,24,0.95)" stroke="#38bdf8" strokeWidth={2} />
          <rect x={60} y={110} width={10} height={130} fill="#38bdf8" />
          <rect x={1010} y={110} width={10} height={130} fill="#818cf8" />
        </g>
        <foreignObject x={80} y={116} width={920} height={120}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center'}}>
            <div style={{fontSize: 46, fontWeight: 900, color: '#fde047', lineHeight: 1.1, textShadow: '0 2px 10px rgba(0,0,0,0.6)'}}>دولة بلا اعتراف</div>
            <div style={{fontSize: 26, fontWeight: 700, color: '#7dd3fc', marginTop: 8}}>هل هي حقيقية؟</div>
          </div>
        </foreignObject>

        {/* ================= PHASE 1: SCALE / BALANCE (Slot A/B) ================= */}
        <g opacity={p1Op * heroOp} transform={`translate(540, 700) scale(${heroScale})`}>
          {/* Base pillar */}
          <rect x={-14} y={-40} width={28} height={280} fill="#1e293b" stroke="#38bdf8" strokeWidth={2} />
          <ellipse cx={0} cy={250} rx={140} ry={26} fill="#0b1526" stroke="#38bdf8" strokeWidth={2} />
          <rect x={-60} y={240} width={120} height={16} rx={6} fill="#38bdf8" opacity={0.5} />
          {/* Fulcrum */}
          <circle cx={0} cy={-40} r={16} fill="#fde047" stroke="#0b1526" strokeWidth={3} />

          {/* Beam */}
          <g transform={`rotate(${tilt} 0 -40)`}>
            <rect x={-260} y={-52} width={520} height={24} rx={10} fill="url(#sc9beam)" stroke="#e0f2fe" strokeWidth={2} />
            <circle cx={0} cy={-40} r={8} fill="#0b1526" />

            {/* Left pan: official independence document */}
            <line x1={-240} y1={-40} x2={-240} y2={60} stroke="#93c5fd" strokeWidth={3} />
            <g transform="translate(-240, 60)">
              <g transform={`rotate(${-tilt * 0.5})`}>
                <rect x={-95} y={-10} width={190} height={170} rx={10} fill="url(#sc9paper)" stroke="#94a3b8" strokeWidth={2} />
                <rect x={-70} y={16} width={140} height={10} rx={4} fill="#64748b" />
                <rect x={-70} y={40} width={120} height={8} rx={4} fill="#94a3b8" />
                <rect x={-70} y={58} width={130} height={8} rx={4} fill="#94a3b8" />
                <rect x={-70} y={76} width={100} height={8} rx={4} fill="#94a3b8" />
                {/* Stamp circle on document */}
                <circle cx={55} cy={120} r={26} fill="none" stroke="#dc2626" strokeWidth={4} />
                <path d="M45,120 L52,128 L68,110" stroke="#dc2626" strokeWidth={4} fill="none" strokeLinecap="round" />
              </g>
            </g>

            {/* Right pan: empty government seal */}
            <line x1={240} y1={-40} x2={240} y2={60} stroke="#93c5fd" strokeWidth={3} />
            <g transform="translate(240, 60)">
              <g transform={`rotate(${-tilt * 0.5})`} opacity={sealPulse > 0.5 ? 1 : 0.85}>
                <circle cx={0} cy={60} r={78} fill="url(#sc9seal)" stroke="#475569" strokeWidth={4} />
                <circle cx={0} cy={60} r={58} fill="none" stroke="#94a3b8" strokeWidth={2} strokeDasharray="4 6" />
                {/* Empty interior: dashed question */}
                <text x={0} y={80} textAnchor="middle" fontSize={60} fontWeight={900} fill="#cbd5e1" fontFamily="Arial" opacity={0.9}>?</text>
                {/* Cracked / empty mark */}
                <path d="M-30,30 L-8,50 L-22,70 L0,90" stroke="#ef4444" strokeWidth={3} fill="none" opacity={0.7} />
              </g>
            </g>
          </g>
        </g>

        {/* Phase 1 caption card (Slot C) */}
        <g opacity={p1Op}>
          <rect x={60} y={1120} width={960} height={280} rx={24} fill="rgba(6,12,24,0.94)" stroke="#38bdf8" strokeWidth={2} />
        </g>
        <foreignObject x={80} y={1136} width={920} height={250} opacity={p1Op}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '10px 20px', boxSizing: 'border-box'}}>
            <div style={{fontSize: 30, fontWeight: 800, color: '#7dd3fc', marginBottom: 12}}>والآن… ميزان الفيزياء</div>
            <div style={{fontSize: 34, fontWeight: 900, color: '#ffffff', lineHeight: 1.4}}>وثيقة استقلال رسمية <span style={{color: '#fde047'}}>مقابل</span> ختم حكومي فارغ</div>
            <div style={{fontSize: 26, fontWeight: 700, color: '#94a3b8', marginTop: 10}}>لا يعترف به أي حكوم في العالم</div>
          </div>
        </foreignObject>

        {/* ================= PHASE 2: REVEAL / QUESTION (Slot A/B) ================= */}
        <g opacity={p2Op}>
          {/* Slot A: big emblem - unrecognized state symbol */}
          <g transform="translate(540, 430)">
            {/* outer ring */}
            <circle cx={0} cy={0} r={150} fill="rgba(6,12,24,0.9)" stroke="#818cf8" strokeWidth={3} />
            <circle cx={0} cy={0} r={120} fill="none" stroke="#38bdf8" strokeWidth={2} strokeDasharray="8 10" opacity={0.7} />
            {/* flag pole */}
            <rect x={-6} y={-110} width={12} height={220} rx={4} fill="#cbd5e1" />
            {/* flag rectangle (unknown flag) */}
            <g transform="translate(6, -110)">
              <rect x={0} y={0} width={130} height={80} rx={6} fill="#0f172a" stroke="#94a3b8" strokeWidth={2} />
              <text x={65} y={54} textAnchor="middle" fontSize={48} fontWeight={900} fill="#fde047" fontFamily="Arial">؟</text>
            </g>
            {/* broken recognition seals around */}
            <g opacity={0.85}>
              {[0, 60, 120, 180, 240, 300].map((deg, i) => (
                <g key={i} transform={`rotate(${deg}) translate(0,-150)`}>
                  <circle cx={0} cy={0} r={12} fill="#1e293b" stroke="#ef4444" strokeWidth={2} />
                  <line x1={-6} y1={-6} x2={6} y2={6} stroke="#ef4444" strokeWidth={2} />
                  <line x1={6} y1={-6} x2={-6} y2={6} stroke="#ef4444" strokeWidth={2} />
                </g>
              ))}
            </g>
          </g>

          {/* Slot B: recognition meter / comparison bars */}
          <g transform="translate(60, 660)">
            <rect x={0} y={0} width={960} height={400} rx={24} fill="rgba(6,12,24,0.94)" stroke="#818cf8" strokeWidth={2} />
            {/* Title inside */}
          </g>
        </g>
        <foreignObject x={80} y={676} width={920} height={380} opacity={p2Op}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '22px 26px', boxSizing: 'border-box'}}>
            <div style={{fontSize: 30, fontWeight: 900, color: '#fde047', textAlign: 'center'}}>مؤشر الاعتراف الدولي</div>

            {/* Row 1: claim of sovereignty */}
            <div style={{display: 'flex', flexDirection: 'row', alignItems: 'center', gap: 14}}>
              <div style={{fontSize: 26, fontWeight: 800, color: '#e2e8f0', width: 220, textAlign: 'right'}}>ادّعاء السيادة</div>
              <div style={{flex: 1, height: 34, background: 'rgba(56,189,248,0.12)', borderRadius: 10, overflow: 'hidden', border: '1px solid rgba(56,189,248,0.4)'}}>
                <div style={{width: '100%', height: '100%', background: 'linear-gradient(90deg,#38bdf8,#818cf8)', borderRadius: 10}} />
              </div>
              <div style={{fontSize: 26, fontWeight: 900, color: '#38bdf8', width: 80, textAlign: 'left'}}>كامل</div>
            </div>

            {/* Row 2: international recognition */}
            <div style={{display: 'flex', flexDirection: 'row', alignItems: 'center', gap: 14}}>
              <div style={{fontSize: 26, fontWeight: 800, color: '#e2e8f0', width: 220, textAlign: 'right'}}>الاعتراف الدولي</div>
              <div style={{flex: 1, height: 34, background: 'rgba(239,68,68,0.12)', borderRadius: 10, overflow: 'hidden', border: '1px solid rgba(239,68,68,0.4)'}}>
                <div style={{width: '6%', height: '100%', background: 'linear-gradient(90deg,#ef4444,#f97316)', borderRadius: 10}} />
              </div>
              <div style={{fontSize: 26, fontWeight: 900, color: '#f87171', width: 80, textAlign: 'left'}}>صفر</div>
            </div>

            {/* Row 3: sovereign state status */}
            <div style={{display: 'flex', flexDirection: 'row', alignItems: 'center', gap: 14}}>
              <div style={{fontSize: 26, fontWeight: 800, color: '#e2e8f0', width: 220, textAlign: 'right'}}>عضوية الأمم المتحدة</div>
              <div style={{flex: 1, height: 34, background: 'rgba(148,163,184,0.12)', borderRadius: 10, overflow: 'hidden', border: '1px solid rgba(148,163,184,0.4)'}}>
                <div style={{width: '4%', height: '100%', background: 'linear-gradient(90deg,#94a3b8,#64748b)', borderRadius: 10}} />
              </div>
              <div style={{fontSize: 26, fontWeight: 900, color: '#cbd5e1', width: 80, textAlign: 'left'}}>غائب</div>
            </div>

            <div style={{fontSize: 25, fontWeight: 700, color: '#94a3b8', textAlign: 'center', marginTop: 4}}>دولة مجهرية تعتبر نفسها مستقلة… بلا اعتراف</div>
          </div>
        </foreignObject>

        {/* ================= PHASE 3: TAKEAWAY CALLOUT (Slot C) ================= */}
        <g opacity={p3Op} transform={`translate(540, 1260) scale(${p3Scale}) translate(-540,-1260)`}>
          <rect x={60} y={1090} width={960} height={330} rx={26} fill="rgba(6,12,24,0.96)" stroke="#fde047" strokeWidth={2.5} />
          <rect x={60} y={1090} width={960} height={12} rx={6} fill="#fde047" />
          {/* Animated question emblem */}
          <g transform="translate(880, 1255)">
            <circle cx={0} cy={0} r={70} fill="rgba(56,189,248,0.15)" stroke="#38bdf8" strokeWidth={3} />
            <circle cx={0} cy={0} r={52} fill="none" stroke="#818cf8" strokeWidth={2} strokeDasharray="6 8" />
            <text x={0} y={30} textAnchor="middle" fontSize={72} fontWeight={900} fill="#fde047" fontFamily="Arial">؟</text>
          </g>
        </g>
        <foreignObject x={80} y={1106} width={760} height={300} opacity={p3Op}>
          <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start', textAlign: 'right', padding: '10px 14px', boxSizing: 'border-box'}}>
            <div style={{fontSize: 30, fontWeight: 900, color: '#fde047', marginBottom: 14}}>هل تصدّق؟</div>
            <div style={{fontSize: 34, fontWeight: 900, color: '#ffffff', lineHeight: 1.35}}>هناك دولة لا يقرّها أي حكوم في العالم</div>
            <div style={{display: 'flex', flexDirection: 'row', gap: 10, marginTop: 16}}>
              <div style={{fontSize: 24, fontWeight: 800, color: '#7dd3fc', padding: '8px 14px', background: 'rgba(56,189,248,0.15)', border: '1.5px solid #38bdf8', borderRadius: 12}}>بلا اعتراف</div>
              <div style={{fontSize: 24, fontWeight: 800, color: '#a5b4fc', padding: '8px 14px', background: 'rgba(129,140,248,0.15)', border: '1.5px solid #818cf8', borderRadius: 12}}>مجهرية</div>
              <div style={{fontSize: 24, fontWeight: 800, color: '#fde047', padding: '8px 14px', background: 'rgba(253,224,71,0.15)', border: '1.5px solid #fde047', borderRadius: 12}}>غير حقيقية؟</div>
            </div>
          </div>
        </foreignObject>

        {/* Balance needle spark on ground */}
        <g opacity={p2Op}>
          <circle cx={540} cy={1380} r={6} fill="#38bdf8" />
          <line x1={540} y1={1380} x2={540 + Math.sin(needle * 3.14 / 180) * 90} y2={1380 - 60} stroke="#38bdf8" strokeWidth={3} strokeLinecap="round" />
        </g>
      </svg>
    </AbsoluteFill>
  );
};
