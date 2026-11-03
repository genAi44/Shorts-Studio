import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {SafeImg} from './SafeImg';
import {rgba, useTheme} from './theme';
import {RGB, Spec} from './types';
import {FireSparks} from './fx';

const mixc = (a: RGB, b: RGB, t: number): RGB => [0, 1, 2].map((i) => Math.round(a[i] + (b[i] - a[i]) * t)) as RGB;

const detectMapRegion = (spec?: Spec): string => {
  if (!spec) return 'middle_east';
  const allText = (spec.scenes || [])
    .map((s) => (s.words || []).map((w) => w.t).join(' '))
    .join(' ')
    .toLowerCase();

  if (allText.includes('سعودية') || allText.includes('رياض') || allText.includes('جدة') || allText.includes('مكة') || allText.includes('درعية')) {
    return 'saudi_arabia';
  }
  if (allText.includes('مصر') || allText.includes('قاهرة') || allText.includes('إسكندرية') || allText.includes('نيل') || allText.includes('أهرام')) {
    return 'egypt';
  }
  if (allText.includes('بوليفيا') || allText.includes('سوكري') || allText.includes('لاباز') || allText.includes('أويوني')) {
    return 'bolivia';
  }
  return 'middle_east';
};

// الطبقة 1: خلفية سينمائية ثلاثية الأبعاد مع خريطة متجهة وشرارات لهب متصاعدة وتظليل سينمائي
export const Background: React.FC<{spec?: Spec}> = ({spec}) => {
  const th = useTheme();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {palette: p, bg} = th.st;
  const s = bg.motion ? frame / fps : 0;
  const k = bg.intensity;

  // اختيار الخريطة الإقليمية المناسبة
  const region = useMemo(() => detectMapRegion(spec), [spec]);
  const mapSrc = staticFile(`maps/${region}.svg`);

  // حركة كاميرا انسيابية بطيئة على نسيج الخريطة (Ken Burns)
  const mapScale = 1.06 + 0.04 * Math.sin(s * 0.12);
  const mapX = Math.sin(s * 0.08) * 22;
  const mapY = Math.cos(s * 0.1) * 16;

  const darkBase = 'linear-gradient(180deg, #090e17 0%, #030508 55%, #010204 100%)';
  const base = th.dark ? darkBase : `linear-gradient(${bg.angle}deg, ${rgba(p.c1)}, ${rgba(p.c2)})`;

  return (
    <AbsoluteFill style={{background: base, overflow: 'hidden'}}>
      {/* 1. مسحة لونية خفيفة من باليتة الستايل */}
      {th.dark && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(ellipse at 50% 30%, ${rgba(p.c1, 0.45)} 0%, ${rgba(p.c2, 0.7)} 70%, transparent 100%)`,
            mixBlendMode: 'screen',
          }}
        />
      )}

      {/* 2. طبقة نسيج الخريطة الإقليمية المرجعية */}
      {th.dark && (
        <div
          style={{
            position: 'absolute',
            inset: -90,
            opacity: 0.24,
            transform: `scale(${mapScale}) translate(${mapX}px, ${mapY}px)`,
            filter: 'contrast(1.35) brightness(0.68) drop-shadow(0 0 24px rgba(212, 175, 55, 0.3))',
            pointerEvents: 'none',
            mixBlendMode: 'screen',
          }}
        >
          <SafeImg src={mapSrc} fallbackSrc={staticFile('maps/middle_east.svg')} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
        </div>
      )}

      {/* 3. شبكة إحداثيات خطية خافتة للعمق البصري */}
      {th.dark && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: `linear-gradient(rgba(212, 175, 55, 0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(212, 175, 55, 0.04) 1px, transparent 1px)`,
            backgroundSize: '120px 120px',
            backgroundPosition: `${(s * 10) % 120}px ${(s * 8) % 120}px`,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* 4. توهج سبوت لايت ذهبي في المركز */}
      {th.dark && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 45%, rgba(212, 175, 55, 0.16) 0%, rgba(212, 175, 55, 0.04) 45%, transparent 68%)',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* 5. شرارات وجمرات لهب ذهبية متصاعدة مستمرة طوال الفيديو */}
      {th.dark && <FireSparks n={28} zIndex={3} />}

      {/* 6. تأطير سينمائي وتظليل داكن للأطراف (Vignette) */}
      {th.dark ? (
        <>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background:
                'radial-gradient(circle at 50% 50%, transparent 32%, rgba(0,0,0,0.65) 75%, rgba(0,0,0,0.96) 100%)',
              pointerEvents: 'none',
              zIndex: 4,
            }}
          />
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: 220,
              background:
                'linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, transparent 100%)',
              pointerEvents: 'none',
              zIndex: 4,
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: 260,
              background:
                'linear-gradient(to top, rgba(0,0,0,0.75) 0%, transparent 100%)',
              pointerEvents: 'none',
              zIndex: 4,
            }}
          />
        </>
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
