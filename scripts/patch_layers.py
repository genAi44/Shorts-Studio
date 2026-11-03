from pathlib import Path

TARGET = Path("remotion/src/layers.tsx")
content = TARGET.read_text(encoding="utf-8").replace("\r\n", "\n")

# 1. Update imports
old_imp = """import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {rgba, useTheme} from './theme';
import {RGB} from './types';"""

new_imp = """import React, {useMemo} from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {rgba, useTheme} from './theme';
import {RGB, Spec} from './types';
import {FireSparks} from './fx';"""

if old_imp in content:
    content = content.replace(old_imp, new_imp, 1)

# 2. Add detectMapRegion and replace Background component
old_bg = """// الطبقة 1: خلفية متحركة (لا خلفية مسطّحة أبداً). تتغير حسب ستايل الفيديو.
export const Background: React.FC = () => {
  const th = useTheme();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {palette: p, bg} = th.st;
  const s = bg.motion ? frame / fps : 0;
  const k = bg.intensity;
  const pat = th.dark ? mixc(p.text, p.accent2, 0.5) : p.accent2;
  const base = `linear-gradient(${bg.angle}deg, ${rgba(p.c1)}, ${rgba(p.c2)})`;
  const blobs = (
    <>
      <div style={{position: 'absolute', inset: 0, background: `radial-gradient(520px 520px at ${50 + 22 * Math.sin(s * 0.45)}% ${30 + 10 * Math.cos(s * 0.4)}%, ${rgba(p.accent2, 0.16 * k)}, transparent 70%)`}} />
      <div style={{position: 'absolute', inset: 0, background: `radial-gradient(640px 640px at ${50 + 26 * Math.cos(s * 0.35)}% ${72 + 9 * Math.sin(s * 0.5)}%, ${rgba(p.accent, 0.12 * k)}, transparent 70%)`}} />
    </>
  );
  let layer: React.ReactNode = null;
  const t = bg.type;
  if (t === 'grid') {
    layer = <div style={{position: 'absolute', inset: -100, backgroundImage: `linear-gradient(${rgba(pat, 0.13 * k)} 3px, transparent 3px), linear-gradient(90deg, ${rgba(pat, 0.13 * k)} 3px, transparent 3px)`, backgroundSize: '96px 96px', backgroundPosition: `${(s * 26) % 96}px ${(s * 20) % 96}px`}} />;
  } else if (t === 'dots') {
    layer = <div style={{position: 'absolute', inset: -100, backgroundImage: `radial-gradient(circle, ${rgba(pat, 0.22 * k)} 4.5px, transparent 5.5px)`, backgroundSize: '72px 72px', backgroundPosition: `${(s * 24) % 72}px ${(s * 18) % 72}px`}} />;
  } else if (t === 'stripes') {
    layer = <div style={{position: 'absolute', inset: -300, backgroundImage: `repeating-linear-gradient(45deg, ${rgba(pat, 0.09 * k)} 0 44px, transparent 44px 130px)`, backgroundPosition: `${(s * 30) % 184}px 0`}} />;
  } else if (t === 'waves') {
    layer = <Waves color={rgba(pat, 0.2 * k)} s={s} />;
  } else if (t === 'radial') {
    layer = <div style={{position: 'absolute', inset: 0, background: `radial-gradient(900px 900px at 50% 45%, ${rgba(p.accent2, (0.2 + 0.05 * Math.sin(s * 1.3)) * k)}, transparent 70%)`}} />;
  } else if (t === 'rays') {
    layer = <div style={{position: 'absolute', inset: 0, background: `repeating-conic-gradient(from ${s * 14}deg at 50% 45%, ${rgba(p.accent, 0.15 * k)} 0deg 6deg, transparent 6deg 13deg)`, WebkitMaskImage: 'radial-gradient(circle at 50% 45%, black 5%, transparent 75%)'}} />;
  } else if (t === 'aurora') {
    layer = (
      <>
        {[p.accent, p.accent2, mixc(p.accent, p.accent2, 0.5)].map((c, i) => (
          <div key={i} style={{position: 'absolute', inset: 0, background: `radial-gradient(${520 - i * 60}px ${300 + i * 40}px at ${50 + 36 * Math.sin(s * 0.5 + i * 2.1)}% ${50 + 32 * Math.cos(s * 0.4 + i * 1.7)}%, ${rgba(c, 0.34 * k)}, transparent 70%)`}} />
        ))}
      </>
    );
  } else if (t === 'paper') {
    layer = <div style={{position: 'absolute', inset: 0, background: `radial-gradient(circle at 50% 50%, transparent 55%, ${rgba(p.c2, 0.55)} 130%)`}} />;
  }
  return <AbsoluteFill style={{background: base}}>{blobs}{layer}</AbsoluteFill>;
};"""

new_bg = """const detectMapRegion = (spec?: Spec): string => {
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
          <Img src={mapSrc} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
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
              height: 440,
              background:
                'linear-gradient(to bottom, rgba(0,0,0,0.88) 0%, rgba(0,0,0,0.4) 55%, transparent 100%)',
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
              height: 500,
              background:
                'linear-gradient(to top, rgba(0,0,0,0.94) 0%, rgba(0,0,0,0.55) 55%, transparent 100%)',
              pointerEvents: 'none',
              zIndex: 4,
            }}
          />
        </>
      ) : null}
    </AbsoluteFill>
  );
};"""

if old_bg in content:
    content = content.replace(old_bg, new_bg, 1)
    TARGET.write_text(content, encoding="utf-8")
    print("remotion/src/layers.tsx updated successfully!")
else:
    print("Could not match old_bg in remotion/src/layers.tsx")

