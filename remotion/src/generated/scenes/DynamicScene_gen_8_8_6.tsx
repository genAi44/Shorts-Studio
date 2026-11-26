/* AUTO-GENERATED ORIGINAL TSX SCENE BY AI VIDEO ARCHITECT */
import React from 'react';
import {AbsoluteFill, interpolate, interpolateColors, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

// ---- scene ----
/* @llm_verified:DynamicScene_gen_8_8_6:c2ce7972621f */
export const DynamicScene_gen_8_8_6: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
  const currentFrame = useCurrentFrame();
  const {fps: videoFps} = useVideoConfig();
  const frame = props.frame ?? currentFrame;
  const fps = props.fps ?? videoFps;
  const dur = Math.max(1, props.dur ?? 150);
  const p = Math.min(1, Math.max(0, frame / dur));

  const appear = interpolate(p, [0, 0.08], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const ph2 = interpolate(p, [0.32, 0.44], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const ph3 = interpolate(p, [0.66, 0.78], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  const pulse = 0.5 + 0.5 * Math.sin(frame / 14);

  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden', background: 'linear-gradient(180deg, #050b16 0%, #0a1424 55%, #060d18 100%)'}}>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920">
        <defs>
          <radialGradient id="s7glow" cx="50%" cy="35%" r="70%">
            <stop offset="0%" stopColor="#1e3a8a" stopOpacity="0.55" />
            <stop offset="55%" stopColor="#0b1a33" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#050b16" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="s7barA" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="100%" stopColor="#0ea5e9" />
          </linearGradient>
          <linearGradient id="s7barB" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#818cf8" />
            <stop offset="100%" stopColor="#6366f1" />
          </linearGradient>
          <linearGradient id="s7line" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#818cf8" stopOpacity="0.9" />
          </linearGradient>
          <radialGradient id="s7node" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0.2" />
          </radialGradient>
        </defs>

        <rect x={0} y={0} width={1080} height={1920} fill="url(#s7glow)" />

        {/* Depth grid lines */}
        <g opacity={0.16}>
          {Array.from({length: 12}).map((_, i) => (
            <line key={`h${i}`} x1={0} y1={300 + i * 90} x2={1080} y2={300 + i * 90} stroke="#38bdf8" strokeWidth={1} />
          ))}
          {Array.from({length: 12}).map((_, i) => (
            <line key={`v${i}`} x1={60 + i * 90} y1={260} x2={60 + i * 90} y2={1440} stroke="#818cf8" strokeWidth={0.6} />
          ))}
        </g>

        {/* Ground horizon */}
        <line x1={0} y1={1440} x2={1080} y2={1440} stroke="#38bdf8" strokeOpacity={0.35} strokeWidth={2} />

        {/* Top headline banner */}
        <foreignObject x={60} y={110} width={960} height={130}>
          <div dir="rtl" lang="ar" style={{
            fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif",
            width: '100%', height: '100%',
            background: 'rgba(6, 12, 24, 0.94)',
            border: '1.5px solid rgba(56, 189, 248, 0.6)',
            borderRadius: 18,
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 8px 30px rgba(0,0,0,0.55)',
            opacity: appear,
            transform: `translateY(${(1 - appear) * -14}px)`
          }}>
            <div style={{fontSize: 46, fontWeight: 800, color: '#fde047', lineHeight: 1.15, letterSpacing: 0}}>
              قاطعة صلتها اللغوية عن
            </div>
            <div style={{fontSize: 26, fontWeight: 600, color: '#93c5fd', marginTop: 6}}>
              فجوة التواصل بين اللسان والجوار
            </div>
          </div>
        </foreignObject>

        {/* Slot A: Right-side metric panel (avoid left HUD corner) */}
        <foreignObject x={604} y={270} width={416} height={310}>
          <div dir="rtl" lang="ar" style={{
            fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif",
            width: '100%', height: '100%',
            background: 'rgba(6, 12, 24, 0.94)',
            border: '1.5px solid rgba(129, 140, 248, 0.6)',
            borderRadius: 18,
            padding: '18px 20px',
            display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
            boxShadow: '0 10px 34px rgba(0,0,0,0.55)',
            opacity: appear
          }}>
            <div style={{fontSize: 26, fontWeight: 700, color: '#fde047'}}>الانقطاع اللغوي</div>
            <div style={{fontSize: 28, fontWeight: 700, color: '#ffffff', lineHeight: 1.5, marginTop: 4}}>
              لسانٌ منفصل عن محيطه اللغوي
            </div>
            <div style={{display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 10, marginTop: 6}}>
              <div style={{fontSize: 26, color: '#93c5fd', fontWeight: 600}}>فاصل التواصل</div>
              <div style={{width: 14, height: 14, borderRadius: 7, background: '#38bdf8', boxShadow: `0 0 ${8 + pulse * 10}px #38bdf8`}} />
            </div>
          </div>
        </foreignObject>

        {/* Slot B: Broken language bridge diagram */}
        <g opacity={appear}>
          {/* Left node: Dutch language */}
          <circle cx={230} cy={820} r={72} fill="rgba(56, 189, 248, 0.14)" stroke="#38bdf8" strokeWidth={2.5} />
          <circle cx={230} cy={820} r={44} fill="url(#s7node)" opacity={0.85} />
          <text x={230} y={835} textAnchor="middle" fontSize={40} fill="#e0f2fe" fontFamily="Cairo, sans-serif" fontWeight={800}>NL</text>

          {/* Right node: Spanish/Portuguese */}
          <circle cx={850} cy={820} r={72} fill="rgba(129, 140, 248, 0.14)" stroke="#818cf8" strokeWidth={2.5} />
          <circle cx={850} cy={820} r={44} fill="#818cf8" opacity={0.85} />
          <text x={850} y={835} textAnchor="middle" fontSize={40} fill="#eef2ff" fontFamily="Cairo, sans-serif" fontWeight={800}>ES/PT</text>

          {/* Broken bridge line */}
          <line x1={302} y1={820} x2={480} y2={820} stroke="url(#s7line)" strokeWidth={5} strokeDasharray="14 10" opacity={0.85} />
          <line x1={600} y1={820} x2={778} y2={820} stroke="url(#s7line)" strokeWidth={5} strokeDasharray="14 10" opacity={0.85} />

          {/* Broken gap marker */}
          <g opacity={ph2}>
            <rect x={480} y={770} width={120} height={100} rx={14} fill="rgba(239, 68, 68, 0.14)" stroke="#ef4444" strokeWidth={2.5} />
            <line x1={505} y1={795} x2={575} y2={845} stroke="#ef4444" strokeWidth={5} strokeLinecap="round" />
            <line x1={575} y1={795} x2={505} y2={845} stroke="#ef4444" strokeWidth={5} strokeLinecap="round" />
          </g>

          {/* Slot B bottom label */}
          <foreignObject x={60} y={920} width={960} height={130}>
            <div dir="rtl" lang="ar" style={{
              fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif",
              width: '100%', height: '100%',
              background: 'rgba(6, 12, 24, 0.94)',
              border: '1.5px solid rgba(239, 68, 68, 0.55)',
              borderRadius: 18,
              padding: '16px 24px',
              display: 'flex', flexDirection: 'column', justifyContent: 'center',
              boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
              opacity: ph2
            }}>
              <div style={{fontSize: 28, color: '#fca5a5', fontWeight: 700}}>فجوة لغوية</div>
              <div style={{fontSize: 30, color: '#ffffff', fontWeight: 800, marginTop: 4, lineHeight: 1.4}}>
                الجسر المقطوع بين الهولندية ولغات الجيران
              </div>
            </div>
          </foreignObject>
        </g>

        {/* Slot C: Phase 3 takeaway with comparison bars */}
        <foreignObject x={60} y={1090} width={960} height={345}>
          <div dir="rtl" lang="ar" style={{
            fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif",
            width: '100%', height: '100%',
            background: 'rgba(6, 12, 24, 0.94)',
            border: '1.5px solid rgba(56, 189, 248, 0.6)',
            borderRadius: 20,
            padding: '20px 26px',
            display: 'flex', flexDirection: 'column', gap: 14,
            boxShadow: '0 12px 36px rgba(0,0,0,0.6)',
            opacity: ph3
          }}>
            <div style={{fontSize: 30, fontWeight: 800, color: '#fde047'}}>
              قاطعة صلتها اللغوية عن جيرانها
            </div>

            {/* Bar 1 - Dutch */}
            <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <div style={{fontSize: 26, color: '#93c5fd', fontWeight: 700}}>الهولندية</div>
                <div style={{fontSize: 26, color: '#e0f2fe', fontWeight: 700}}>لسان مستقل</div>
              </div>
              <div style={{height: 20, background: 'rgba(56,189,248,0.15)', borderRadius: 10, overflow: 'hidden'}}>
                <div style={{
                  height: '100%',
                  width: `${Math.round(interpolate(p, [0.68, 0.95], [15, 92], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}))}%`,
                  background: 'url(#s7barA)',
                  backgroundColor: '#38bdf8',
                  borderRadius: 10
                }} />
              </div>
            </div>

            {/* Bar 2 - Neighbors */}
            <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <div style={{fontSize: 26, color: '#c7d2fe', fontWeight: 700}}>الإسبانية والبرتغالية</div>
                <div style={{fontSize: 26, color: '#e0e7ff', fontWeight: 700}}>جوار لغوي مختلف</div>
              </div>
              <div style={{height: 20, background: 'rgba(129,140,248,0.15)', borderRadius: 10, overflow: 'hidden'}}>
                <div style={{
                  height: '100%',
                  width: `${Math.round(interpolate(p, [0.72, 0.98], [12, 78], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}))}%`,
                  background: 'url(#s7barB)',
                  backgroundColor: '#818cf8',
                  borderRadius: 10
                }} />
              </div>
            </div>

            <div style={{fontSize: 26, color: '#fca5a5', fontWeight: 700, marginTop: 4, textAlign: 'center'}}>
              قاطعة صلتها اللغوية عن
            </div>
          </div>
        </foreignObject>
      </svg>
    </AbsoluteFill>
  );
};
