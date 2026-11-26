/* AUTO-GENERATED ORIGINAL TSX SCENE BY AI VIDEO ARCHITECT */
import React from 'react';
import {AbsoluteFill, interpolate, interpolateColors, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

// ---- scene ----
/* @llm_verified:DynamicScene_gen_5_5:976519f71b24 */
export const DynamicScene_gen_5_5: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
  const currentFrame = useCurrentFrame();
  const {fps: videoFps} = useVideoConfig();
  const frame = props.frame ?? currentFrame;
  const fps = props.fps ?? videoFps;
  const dur = Math.max(1, props.dur ?? 150);
  const p = Math.min(1, Math.max(0, frame / dur));

  const headlineIn = interpolate(frame, [0, 8], [0.85, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const heroIn = spring({frame: Math.min(frame, 20), fps, config: {damping: 18, stiffness: 110}});

  // Phase timings
  const ph2 = interpolate(p, [0.32, 0.42], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const ph3 = interpolate(p, [0.66, 0.76], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const pulse = (Math.sin(frame / 8) + 1) / 2;

  // Node positions for the system flow diagram (language -> official status)
  const nodeA = {x: 260, y: 730};
  const nodeB = {x: 540, y: 730};
  const nodeC = {x: 820, y: 730};

  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden', background: 'radial-gradient(circle at 50% 40%, #1a0b2e 0%, #0a0618 55%, #040208 100%)'}}>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920">
        <defs>
          <radialGradient id="spot" cx="50%" cy="38%" r="55%">
            <stop offset="0%" stopColor="#a855f7" stopOpacity="0.28"/>
            <stop offset="60%" stopColor="#ec4899" stopOpacity="0.08"/>
            <stop offset="100%" stopColor="#040208" stopOpacity="0"/>
          </radialGradient>
          <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ec4899" stopOpacity="0.22"/>
            <stop offset="100%" stopColor="#ec4899" stopOpacity="0"/>
          </linearGradient>
          <linearGradient id="nodeG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#a855f7" stopOpacity="0.9"/>
            <stop offset="100%" stopColor="#7c3aed" stopOpacity="0.9"/>
          </linearGradient>
          <linearGradient id="nodeG2" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ec4899" stopOpacity="0.9"/>
            <stop offset="100%" stopColor="#be185d" stopOpacity="0.9"/>
          </linearGradient>
          <linearGradient id="nodeG3" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fde047" stopOpacity="0.95"/>
            <stop offset="100%" stopColor="#d97706" stopOpacity="0.95"/>
          </linearGradient>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="10" result="b"/>
            <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        {/* Atmospheric backdrop */}
        <rect x={0} y={0} width={1080} height={1920} fill="url(#spot)"/>
        <rect x={120} y={0} width={160} height={1500} fill="url(#beam)" opacity={0.5}/>
        <rect x={800} y={0} width={160} height={1500} fill="url(#beam)" opacity={0.35}/>
        {/* ground/horizon lines */}
        {[0, 1, 2, 3].map((i) => (
          <line key={i} x1={0} y1={1300 + i * 40} x2={1080} y2={1300 + i * 40} stroke="#a855f7" strokeOpacity={0.10 - i * 0.02} strokeWidth={1.5}/>
        ))}

        {/* Top Headline Banner */}
        <g opacity={headlineIn}>
          <rect x={60} y={110} width={960} height={130} rx={20} fill="rgba(6,12,24,0.94)" stroke="#a855f7" strokeWidth={2}/>
          <foreignObject x={60} y={110} width={960} height={130}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '10px 18px', boxSizing: 'border-box'}}>
              <div style={{color: '#ffffff', fontSize: 44, fontWeight: 800, lineHeight: 1.1, textAlign: 'center'}}>التي يتحدث فيها الهولندية كلسان</div>
              <div style={{color: '#fde047', fontSize: 26, fontWeight: 700, marginTop: 6}}>رسمي — لغة الدولة في أمريكا الجنوبية</div>
            </div>
          </foreignObject>
        </g>

        {/* SLOT A (left side, avoid top-right HUD) : language emblem card */}
        <g opacity={heroIn}>
          <rect x={60} y={278} width={520} height={300} rx={22} fill="rgba(6,12,24,0.94)" stroke="#ec4899" strokeWidth={2}/>
          {/* Speech bubble emblem representing Dutch language */}
          <g transform="translate(200, 340)">
            <rect x={0} y={0} width={240} height={150} rx={26} fill="url(#nodeG2)" filter="url(#glow)" opacity={0.95}/>
            <polygon points="60,148 100,148 70,185" fill="#be185d"/>
            <circle cx={70} cy={75} r={12} fill="#ffffff"/>
            <circle cx={120} cy={75} r={12} fill="#ffffff"/>
            <circle cx={170} cy={75} r={12} fill="#ffffff"/>
          </g>
          <foreignObject x={70} y={470} width={500} height={100}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fde047', fontSize: 34, fontWeight: 800, textAlign: 'center'}}>
              اللغة الهولندية
            </div>
          </foreignObject>
        </g>

        {/* SLOT B : System flow diagram (Phase 1 base + Phase 2 pulses) */}
        <g opacity={interpolate(p, [0, 0.05], [0.9, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}>
          {/* connection lines */}
          <line x1={nodeA.x + 90} y1={nodeA.y} x2={nodeB.x - 90} y2={nodeB.y} stroke="#a855f7" strokeWidth={5} strokeOpacity={0.7}/>
          <line x1={nodeB.x + 90} y1={nodeB.y} x2={nodeC.x - 90} y2={nodeC.y} stroke="#ec4899" strokeWidth={5} strokeOpacity={0.7}/>

          {/* Node A : arrow into country */}
          <g>
            <circle cx={nodeA.x} cy={nodeA.y} r={90} fill="url(#nodeG)" filter="url(#glow)"/>
            <foreignObject x={nodeA.x - 85} y={nodeA.y - 40} width={170} height={80}>
              <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ffffff', fontSize: 30, fontWeight: 800, textAlign: 'center'}}>
                الدولة
              </div>
            </foreignObject>
          </g>

          {/* Node B : language promoted */}
          <g>
            <circle cx={nodeB.x} cy={nodeB.y} r={90} fill="url(#nodeG2)" filter="url(#glow)"/>
            <foreignObject x={nodeB.x - 85} y={nodeB.y - 40} width={170} height={80}>
              <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ffffff', fontSize: 28, fontWeight: 800, textAlign: 'center'}}>
                الهولندية
              </div>
            </foreignObject>
          </g>

          {/* Node C : official status */}
          <g>
            <circle cx={nodeC.x} cy={nodeC.y} r={90} fill="url(#nodeG3)" filter="url(#glow)"/>
            <foreignObject x={nodeC.x - 85} y={nodeC.y - 40} width={170} height={80}>
              <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#1a0b2e', fontSize: 28, fontWeight: 800, textAlign: 'center'}}>
                لسان رسمي
              </div>
            </foreignObject>
          </g>

          {/* Animated signal pulses travelling the flow (Phase 2) */}
          <g opacity={ph2}>
            <circle cx={nodeA.x + 90 + (nodeB.x - nodeA.x - 180) * ((frame % 60) / 60)} cy={nodeA.y} r={9} fill="#fde047" filter="url(#glow)" opacity={0.95}/>
            <circle cx={nodeB.x + 90 + (nodeC.x - nodeB.x - 180) * (((frame + 30) % 60) / 60)} cy={nodeB.y} r={9} fill="#ffffff" filter="url(#glow)" opacity={0.95}/>
          </g>
        </g>

        {/* SLOT B lower / Slot C : Phase 3 takeaway card */}
        <g opacity={ph3}>
          <rect x={60} y={1085} width={960} height={340} rx={22} fill="rgba(6,12,24,0.94)" stroke="#fde047" strokeWidth={2.5}/>
          <foreignObject x={80} y={1100} width={920} height={310}>
            <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 18, padding: '10px 20px', boxSizing: 'border-box'}}>
              <div style={{color: '#fde047', fontSize: 42, fontWeight: 800, textAlign: 'center', lineHeight: 1.15}}>الهولندية لسان رسمي</div>
              <div style={{display: 'flex', gap: 14, flexWrap: 'wrap', justifyContent: 'center'}}>
                <div style={{background: 'rgba(168,85,247,0.25)', border: '1.5px solid #a855f7', borderRadius: 14, padding: '12px 22px', color: '#ffffff', fontSize: 30, fontWeight: 700}}>لغة الدولة</div>
                <div style={{background: 'rgba(236,72,153,0.25)', border: '1.5px solid #ec4899', borderRadius: 14, padding: '12px 22px', color: '#ffffff', fontSize: 30, fontWeight: 700}}>في أمريكا الجنوبية</div>
              </div>
              <div style={{color: '#e9d5ff', fontSize: 28, fontWeight: 600, textAlign: 'center', marginTop: 4}}>تحدثها الدولة كلسان رسمي</div>
            </div>
          </foreignObject>
        </g>

        {/* Phase 1 fading node labels refined by pulse glow */}
        <g opacity={0.5 + pulse * 0.5}>
          <circle cx={nodeA.x} cy={nodeA.y} r={96} fill="none" stroke="#a855f7" strokeWidth={2} strokeOpacity={0.5}/>
        </g>
      </svg>
    </AbsoluteFill>
  );
};
