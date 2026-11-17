import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {SafeImg} from './SafeImg';
import {rgba, useTheme} from './theme';
import {RGB, Spec} from './types';
import {FireSparks} from './fx';

const mixc = (a: RGB, b: RGB, t: number): RGB => [0, 1, 2].map((i) => Math.round(a[i] + (b[i] - a[i]) * t)) as RGB;

// الطبقة 1: خلفية سينمائية مع إضاءة محيطية وتظليل داكن للأطراف وشرارات صاعدة
export const Background: React.FC<{spec?: Spec}> = ({spec}) => {
  const th = useTheme();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {palette: p, bg} = th.st;
  const s = bg.motion ? frame / fps : 0;
  const k = bg.intensity;

  const darkBase = `linear-gradient(${bg.angle}deg, ${rgba(mixc(p.c1, [16, 28, 52], 0.45))} 0%, ${rgba(mixc(p.c2, [10, 18, 36], 0.5))} 55%, #070d19 100%)`;
  const base = th.dark ? darkBase : `linear-gradient(${bg.angle}deg, ${rgba(p.c1)}, ${rgba(p.c2)})`;

  return (
    <AbsoluteFill style={{background: base, overflow: 'hidden'}}>
      {/* 1. مسحة لونية غنية وديناميكية من باليتة الستايل */}
      {th.dark && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(ellipse 90% 65% at 50% 32%, ${rgba(p.accent, 0.24)} 0%, ${rgba(p.c1, 0.55)} 52%, ${rgba(p.c2, 0.75)} 85%, transparent 100%)`,
            mixBlendMode: 'screen',
          }}
        />
      )}

      {/* 2. أمواج متجهة متحركة تملأ الفراغ البصري */}
      <Waves color={rgba(p.accent, th.dark ? 0.14 : 0.18)} s={s} />

      {/* 3. شبكة إحداثيات هندسية للعمق البصري */}
      {th.dark && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: `linear-gradient(${rgba(p.accent, 0.08)} 1px, transparent 1px), linear-gradient(90deg, ${rgba(p.accent2, 0.08)} 1px, transparent 1px)`,
            backgroundSize: '110px 110px',
            backgroundPosition: `${(s * 12) % 110}px ${(s * 9) % 110}px`,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* 4. توهج سبوت لايت محيطي متعدد الطبقات */}
      {th.dark && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(circle at 50% 44%, ${rgba(p.accent, 0.22)} 0%, ${rgba(p.accent2, 0.12)} 48%, transparent 78%)`,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* 5. شرارات وجمرات ذهبية متصاعدة */}
      {th.dark && <FireSparks n={28} zIndex={3} />}

      {/* 6. تأطير سينمائي متوازن يحافظ على إضاءة المشهد */}
      {th.dark ? (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 50%, transparent 55%, rgba(0,0,0,0.35) 85%, rgba(0,0,0,0.62) 100%)',
            pointerEvents: 'none',
            zIndex: 4,
          }}
        />
      ) : null}
    </AbsoluteFill>
  );
};

const Waves: React.FC<{color: string; s: number}> = ({color, s}) => {
  const d = useMemo(() => {
    const out: string[] = [];
    for (let row = -2; row < 14; row++) {
      const y0 = row * 170;
      let path = '';
      for (let x = 0; x <= 1080; x += 30) {
        const y = y0 + 34 * Math.sin((x / 720) * Math.PI * 2);
        path += `${x === 0 ? 'M' : 'L'}${x} ${y.toFixed(1)} `;
      }
      out.push(path);
    }
    return out;
  }, []);
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
      <g style={{translate: `${(s * 40) % 720}px ${(s * 20) % 170}px`}}>
        {d.map((p, i) => <path key={i} d={p} fill="none" stroke={color} strokeWidth={3} transform="translate(-720 0)" />)}
        {d.map((p, i) => <path key={'b' + i} d={p} fill="none" stroke={color} strokeWidth={3} transform="translate(0 0)" />)}
      </g>
    </svg>
  );
};

// الطبقات 4 و5: تدرّج لوني + حبيبات + فينيت (فوق كل شيء).
export const Finish: React.FC = () => {
  const th = useTheme();
  const frame = useCurrentFrame();
  const {palette: p} = th.st;
  const gx = (frame * 97) % 512;
  const gy = (frame * 61) % 512;
  return (
    <>
      <AbsoluteFill style={{background: `linear-gradient(160deg, ${rgba(p.accent, 0.14)}, ${rgba(p.accent2, 0.14)})`, mixBlendMode: th.dark ? 'soft-light' : 'multiply', pointerEvents: 'none'}} />
      <AbsoluteFill style={{backgroundImage: `url(${staticFile('grain.png')})`, backgroundSize: '512px 512px', backgroundPosition: `${gx}px ${gy}px`, opacity: th.dark ? 0.1 : 0.07, mixBlendMode: 'overlay', pointerEvents: 'none'}} />
      <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 48%, transparent 58%, rgba(0,0,0,${th.dark ? 0.5 : 0.22}) 125%)`, pointerEvents: 'none'}} />
    </>
  );
};

// زخارف الإطار وشريط التقدم (زمن عام للفيديو كله).
export const Deco: React.FC<{total: number}> = ({total}) => {
  const th = useTheme();
  const frame = useCurrentFrame();
  const {palette: p, deco} = th.st;
  const f = Math.min(1, frame / Math.max(total - 1, 1));
  const a = rgba(p.accent, 0.9);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {deco.frame === 'corners' && (
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          {[[50, 50, 1, 1], [1030, 50, -1, 1], [50, 1870, 1, -1], [1030, 1870, -1, -1]].map(([x, y, sx, sy], i) => (
            <polyline key={i} points={`${x},${y + 90 * sy} ${x},${y} ${x + 90 * sx},${y}`} fill="none" stroke={a} strokeWidth={7} strokeLinecap="round" />
          ))}
        </svg>
      )}
      {deco.frame === 'border' && <div style={{position: 'absolute', inset: 28, border: `4px solid ${rgba(p.accent, 0.55)}`, borderRadius: 18}} />}
      {deco.frame === 'ticks' && (
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          {Array.from({length: 29}).map((_, i) => {
            const y = 120 + i * 60;
            const l = i % 4 === 0 ? 34 : 18;
            return <g key={i} stroke={rgba(p.text, 0.4)} strokeWidth={3}><line x1={30} y1={y} x2={30 + l} y2={y} /><line x1={1050} y1={y} x2={1050 - l} y2={y} /></g>;
          })}
        </svg>
      )}
      {deco.progress === 'top' && <div style={{position: 'absolute', left: 0, top: 0, height: 12, width: `${f * 100}%`, background: rgba(p.accent)}} />}
      {deco.progress === 'bottom' && <div style={{position: 'absolute', left: 0, bottom: 0, height: 12, width: `${f * 100}%`, background: rgba(p.accent)}} />}
      {deco.progress === 'side' && <div style={{position: 'absolute', right: 0, top: 0, width: 12, height: `${f * 100}%`, background: rgba(p.accent)}} />}
    </AbsoluteFill>
  );
};

// انتقال حقيقي بين المشاهد (slide, wipe, shape wipe) بدون وميض لون مصمت كامل
export const SceneWipe: React.FC<{index: number}> = ({index}) => {
  const th = useTheme();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const n = Math.round(0.38 * fps);
  if (index === 0 || frame > n) return null;
  const p = interpolate(frame, [0, n], [0, 1], {extrapolateRight: 'clamp', easing: th.ease.inOut});
  const kind = (th.st.seed + index) % 3;
  const col = rgba(index % 2 ? th.p.accent : th.p.accent2);
  const col2 = rgba(index % 2 ? th.p.accent2 : th.p.text);

  // 1. Slide: شريط انزلاقي حركي بحافة متوهجة يتحرك عبر الشاشة
  if (kind === 0) {
    const x = interpolate(p, [0, 1], [-120, 1200]);
    return (
      <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden'}}>
        <div style={{
          position: 'absolute', top: 0, bottom: 0, left: x - 40, width: 80,
          background: `linear-gradient(90deg, transparent, ${col}, ${col2}, transparent)`,
          filter: 'blur(4px)', opacity: (1 - p) * 0.95
        }} />
        <div style={{
          position: 'absolute', top: 0, bottom: 0, left: x - 8, width: 16,
          background: col, boxShadow: `0 0 32px ${col}`, opacity: (1 - p)
        }} />
      </AbsoluteFill>
    );
  }

  // 2. Wipe: مسح تدريجي قطري متحرك مع خط فاصل أنيق
  if (kind === 1) {
    const pos = interpolate(p, [0, 1], [0, 120]);
    return (
      <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden'}}>
        <div style={{
          position: 'absolute', inset: 0,
          clipPath: `polygon(${pos}% 0%, ${pos + 12}% 0%, ${pos - 18}% 100%, ${pos - 30}% 100%)`,
          background: `linear-gradient(135deg, ${col}, ${col2})`,
          opacity: (1 - p) * 0.9,
          boxShadow: '0 0 40px rgba(0,0,0,0.4)'
        }} />
      </AbsoluteFill>
    );
  }

  // 3. Shape Wipe: شكل هندسي (ماس/دائرة) متسع بحافة مضيئة يكشف المشهد
  const r = interpolate(p, [0, 1], [0, 140]);
  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden'}}>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <defs>
          <radialGradient id={`sw_g_${index}`} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={col} stopOpacity="0" />
            <stop offset="85%" stopColor={col} stopOpacity={(1 - p) * 0.7} />
            <stop offset="100%" stopColor={col2} stopOpacity={(1 - p) * 0.95} />
          </radialGradient>
        </defs>
        <circle cx={540} cy={960} r={`${r}%`} fill="none" stroke={`url(#sw_g_${index})`} strokeWidth={36 * (1 - p)} opacity={1 - p} />
      </svg>
    </AbsoluteFill>
  );
};
