import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "remotion" / "src" / "beats.tsx"

content = TARGET.read_text(encoding="utf-8")

# 1. Update imports
old_import = "import {AbsoluteFill, Audio, Easing, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';"
new_import = (
    "import {AbsoluteFill, Audio, Easing, Img, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';\n"
    "import {ArrowFlow, FireSparks, FloatBadge, GlowText, MapOverlay, Particles} from './fx';\n"
    "import {IconSceneBeat} from './iconScene';"
)
if old_import in content:
    content = content.replace(old_import, new_import)

# 2. Add components before BeatView
new_components = """
// ------------------------------------------------------------------ مقاطع SVG الحديثة
const MapPinBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const region = beat.region || 'egypt';
  const points = beat.points || [
    {name: 'القاهرة', x: 540, y: 780},
    {name: 'الإسكندرية', x: 420, y: 560},
    {name: 'الأقصر', x: 620, y: 1180},
  ];
  const mapSrc = staticFile(`maps/${region}.svg`);

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <div style={{position: 'absolute', inset: 0, opacity: 0.35, filter: 'contrast(1.2) brightness(0.7)'}}>
        <Img src={mapSrc} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
      </div>
      <MapOverlay opacity={0.8} />
      <FireSparks n={20} />

      {beat.title && (
        <div style={{position: 'absolute', left: 60, right: 60, top: 240, textAlign: 'center', zIndex: 10}}>
          <GlowText fontSize={64} gold>{beat.title}</GlowText>
        </div>
      )}

      {points.length > 1 && points.slice(1).map((pt: any, i: number) => (
        <ArrowFlow
          key={i}
          from={{x: points[i].x, y: points[i].y}}
          to={{x: pt.x, y: pt.y}}
          color="#38bdf8"
          curvature={25}
          delay={10 + i * 8}
        />
      ))}

      {points.map((pt: any, i: number) => {
        const pinPop = useSpring(0.1 + i * 0.15, 'bouncy');
        const iconPath = pt.icon || 'icons/map/map_pin.svg';
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: pt.x - 70,
              top: pt.y - 70,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              transform: `scale(${pinPop})`,
              zIndex: 7,
            }}
          >
            <div
              style={{
                width: 90,
                height: 90,
                borderRadius: '50%',
                background: 'radial-gradient(circle at 35% 35%, rgba(45, 55, 72, 0.9), rgba(15, 23, 42, 0.95))',
                border: '3px solid #D4AF37',
                boxShadow: '0 0 20px rgba(212, 175, 55, 0.6), 0 8px 18px rgba(0,0,0,0.6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Img src={staticFile(iconPath)} style={{width: 50, height: 50, objectFit: 'contain'}} />
            </div>
            {pt.name && (
              <div
                style={{
                  marginTop: 6,
                  padding: '4px 14px',
                  borderRadius: 14,
                  background: 'rgba(10, 15, 25, 0.9)',
                  border: '1px solid rgba(212, 175, 55, 0.6)',
                  fontFamily: th.family,
                  fontSize: 24,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  whiteSpace: 'nowrap',
                }}
              >
                {pt.name}
              </div>
            )}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const TimelineCardBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const items: any[] = (beat.items || [
    {year: '٦٤١ م', label: 'الفتح وتأسيس الفسطاط', icon: 'icons/history/castle.svg'},
    {year: '٩٦٩ م', label: 'بناء القاهرة المعزية', icon: 'icons/building/mosque.svg'},
    {year: '١٨٠٥ م', label: 'عصر محمد علي وتحديث العاصمة', icon: 'icons/crown/crown.svg'},
  ]).slice(0, 4);

  const lineProgress = useProgress(0.1, 1.2);
  const totalH = items.length * 200;
  const startY = th.zoneCy - totalH / 2 + 60;

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <MapOverlay opacity={0.6} />
      <FireSparks n={18} />

      {beat.title && (
        <div style={{position: 'absolute', left: 60, right: 60, top: 220, textAlign: 'center', zIndex: 10}}>
          <GlowText fontSize={62} gold>{beat.title}</GlowText>
        </div>
      )}

      <svg
        width={1080}
        height={1920}
        style={{position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 4}}
      >
        <line
          x1={220}
          y1={startY}
          x2={220}
          y2={startY + totalH}
          stroke="rgba(212, 175, 55, 0.3)"
          strokeWidth={6}
          strokeLinecap="round"
        />
        <line
          x1={220}
          y1={startY}
          x2={220}
          y2={startY + totalH * lineProgress}
          stroke="#D4AF37"
          strokeWidth={6}
          strokeLinecap="round"
          filter="drop-shadow(0 0 10px #D4AF37)"
        />
        <circle
          cx={220}
          cy={startY + totalH * lineProgress}
          r={10}
          fill="#FFF3C4"
          filter="drop-shadow(0 0 12px #FFD700)"
        />
      </svg>

      <div style={{position: 'absolute', inset: 0, zIndex: 6}}>
        {items.map((it, i) => {
          const itemY = startY + i * 200;
          const pop = useSpring(0.15 + i * 0.18, 'bouncy');
          const iconSrc = staticFile(it.icon || 'icons/time/history_clock.svg');
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: 170,
                top: itemY - 45,
                display: 'flex',
                alignItems: 'center',
                gap: 28,
                transform: `scale(${pop})`,
              }}
            >
              <div
                style={{
                  width: 96,
                  height: 96,
                  borderRadius: '50%',
                  background: 'radial-gradient(circle at 35% 35%, #2a3342, #0f172a)',
                  border: '3px solid #D4AF37',
                  boxShadow: '0 0 20px rgba(212, 175, 55, 0.4), 0 8px 18px rgba(0,0,0,0.6)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <Img src={iconSrc} style={{width: 52, height: 52, objectFit: 'contain'}} />
              </div>

              <div
                dir="rtl"
                style={{
                  padding: '14px 28px',
                  borderRadius: 24,
                  background: 'rgba(15, 23, 42, 0.88)',
                  border: '1.5px solid rgba(212, 175, 55, 0.4)',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                  minWidth: 460,
                  maxWidth: 700,
                  backdropFilter: 'blur(14px)',
                }}
              >
                {it.year && (
                  <div
                    style={{
                      fontFamily: th.family,
                      fontSize: 34,
                      fontWeight: 900,
                      color: '#FFD700',
                      marginBottom: 4,
                      letterSpacing: '0.02em',
                      textShadow: '0 2px 8px rgba(212, 175, 55, 0.5)',
                    }}
                  >
                    {it.year}
                  </div>
                )}
                <div
                  style={{
                    fontFamily: th.family2 || th.family,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  {it.label || it.text || ''}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const StatRingV2Beat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const p = useProgress(0.12, 1.4);
  const a = useSpring(0.08, 'bouncy');
  const cy = th.zoneCy - 60;
  const s = String(beat.number ?? '');
  const pn = parseNum(s);
  const show = pn ? pn.pre + (pn.commas ? (pn.val * p).toLocaleString('en-US', {minimumFractionDigits: pn.dec, maximumFractionDigits: pn.dec}) : (pn.val * p).toFixed(pn.dec)) + pn.suf : s;

  const R = 230;
  const C = 2 * Math.PI * R;
  const iconPath = beat.icon || 'icons/coin/gold_bars.svg';
  const iconSrc = staticFile(iconPath);

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <MapOverlay opacity={0.6} />
      <FireSparks n={20} />

      <svg
        width={1080}
        height={1920}
        style={{position: 'absolute', inset: 0, opacity: clamp01(a * 1.5)}}
      >
        <defs>
          <linearGradient id="ringGradV2" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFF3C4" />
            <stop offset="50%" stopColor="#D4AF37" />
            <stop offset="100%" stopColor="#8B6508" />
          </linearGradient>
          <filter id="ringGlowV2" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="16" floodColor="#D4AF37" floodOpacity="0.8" />
          </filter>
        </defs>
        <circle cx={540} cy={cy - 120} r={R} fill="none" stroke="rgba(255, 255, 255, 0.12)" strokeWidth={16} />
        <circle
          cx={540}
          cy={cy - 120}
          r={R}
          fill="none"
          stroke="url(#ringGradV2)"
          strokeWidth={18}
          strokeLinecap="round"
          strokeDasharray={C}
          strokeDashoffset={C * (1 - p)}
          transform={`rotate(-90 540 ${cy - 120})`}
          filter="url(#ringGlowV2)"
        />
      </svg>

      <div
        style={{
          position: 'absolute',
          left: 540 - 100,
          top: cy - 120 - 100,
          width: 200,
          height: 200,
          borderRadius: '50%',
          background: 'radial-gradient(circle at 35% 35%, rgba(45, 55, 72, 0.7), rgba(15, 23, 42, 0.85))',
          border: '2px solid rgba(212, 175, 55, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backdropFilter: 'blur(10px)',
          ...enterStyle(a, 'pop'),
        }}
      >
        <Img src={iconSrc} style={{width: 120, height: 120, objectFit: 'contain'}} />
      </div>

      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: cy + 150,
          textAlign: 'center',
          ...enterStyle(a, 'rise', 40),
        }}
      >
        <GlowText fontSize={130} gold>
          {show}
        </GlowText>
      </div>

      {beat.label && (
        <div
          dir="rtl"
          style={{
            position: 'absolute',
            left: 90,
            right: 90,
            top: cy + 320,
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              padding: '12px 36px',
              borderRadius: 30,
              background: 'rgba(15, 23, 42, 0.85)',
              border: '1.5px solid rgba(212, 175, 55, 0.5)',
              fontFamily: th.family,
              fontSize: 48,
              fontWeight: 700,
              color: '#FFFFFF',
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              textShadow: th.shadow,
            }}
          >
            {beat.label}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
"""

target_marker = "// ------------------------------------------------------------------ توزيع\nexport const BeatView"
if target_marker in content:
    content = content.replace(target_marker, new_components + "\n" + target_marker)

old_switch = """  switch (beat.kind) {
    case 'map': body = <MapBeat beat={beat} />; break;"""

new_switch = """  switch (beat.kind) {
    case 'icon_scene': body = <IconSceneBeat beat={beat} />; break;
    case 'map_pin': body = <MapPinBeat beat={beat} />; break;
    case 'timeline_card': body = <TimelineCardBeat beat={beat} />; break;
    case 'stat_ring_v2': body = <StatRingV2Beat beat={beat} />; break;
    case 'map': body = <MapBeat beat={beat} />; break;"""

if old_switch in content:
    content = content.replace(old_switch, new_switch)

TARGET.write_text(content, encoding="utf-8")
print("remotion/src/beats.tsx updated successfully!")

