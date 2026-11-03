import React from 'react';
import {AbsoluteFill, staticFile, useCurrentFrame} from 'remotion';
import {SafeImg} from './SafeImg';
import {ArrowFlow, FloatBadge, GlowText} from './fx';
import {enterStyle, useFont, useSpring} from './hooks';
import {rgba, useTheme} from './theme';
import type {Beat} from './types';

/**
 * Full-screen composition matching the cinematic dark gold target aesthetic:
 * - Large hero SVG icon with scale spring + glow pulse in center
 * - Arabic bold RTL headline with 3D gold gradient at top
 * - 2-4 smaller accent icons orbiting or staggered around it with connecting arrows
 * - Fire embers / sparks and regional map are rendered by Background
 */
export const IconSceneBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const frame = useCurrentFrame();
  const heroPop = useSpring(0.1, 'bouncy');
  const heroPulse = 1 + 0.04 * Math.sin(frame * 0.1);
  const textPop = useSpring(0.18, 'smooth');

  // Hero icon from beat or auto-matched
  const heroIcon = beat.hero_icon || beat.icon || 'icons/building/city.svg';
  const heroSrc = heroIcon.startsWith('http') || heroIcon.startsWith('/') ? heroIcon : staticFile(heroIcon);

  const DEFAULT_POSITIONS = [
    {x: 230, y: 720},
    {x: 850, y: 740},
    {x: 220, y: 1360},
    {x: 860, y: 1390},
  ];

  // Staggered badges around hero — always assign default corner positions when x/y are null/undefined
  const rawBadges: Array<{icon: string; label?: string; x?: number | null; y?: number | null}> =
    beat.badges ||
    (beat.items && beat.items.length > 0
      ? beat.items.slice(0, 4).map((it: any) => ({
          icon: it.icon || 'icons/history/pyramid.svg',
          label: it.text || it.label || '',
          x: it.x,
          y: it.y,
        }))
      : [
          {icon: 'icons/history/pyramid.svg', label: 'منف'},
          {icon: 'icons/monument/lighthouse.svg', label: 'الإسكندرية'},
          {icon: 'icons/monument/obelisk.svg', label: 'طيبة'},
          {icon: 'icons/monument/mosque.svg', label: 'الفسطاط'},
        ]);

  const badges = rawBadges.map((b, i) => ({
    ...b,
    x: b.x != null ? b.x : DEFAULT_POSITIONS[i % 4].x,
    y: b.y != null ? b.y : DEFAULT_POSITIONS[i % 4].y,
  }));

  const heroX = 540;
  const heroY = 1040;
  const heroSize = 250;
  const titleText = beat.title || beat.text || 'عبر التاريخ';

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      {/* Top Arabic Bold Headline with 3D Gold Gradient */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 360,
          textAlign: 'center',
          zIndex: 10,
          ...enterStyle(textPop, 'drop', 30),
        }}
      >
        <GlowText fontSize={titleText.length > 25 ? 54 : 68} gold>
          {titleText}
        </GlowText>
        {beat.sub ? (
          <div
            dir="rtl"
            style={{
              marginTop: 14,
              ...font,
              fontSize: 36,
              color: rgba(th.p.text, 0.9),
              textShadow: th.shadow,
            }}
          >
            {beat.sub}
          </div>
        ) : null}
      </div>

      {/* Radiating Animated Arrows from Center to Badges */}
      {badges.map((b, i) => (
        <ArrowFlow
          key={i}
          from={{x: heroX, y: heroY - 30}}
          to={{x: b.x, y: b.y + 30}}
          color={i % 2 === 0 ? '#38bdf8' : '#D4AF37'}
          curvature={i % 2 === 0 ? -28 : 28}
          delay={12 + i * 4}
          duration={20}
        />
      ))}

      {/* Center 3D Hero Landmark */}
      <div
        style={{
          position: 'absolute',
          left: heroX - heroSize / 2,
          top: heroY - heroSize / 2,
          width: heroSize,
          height: heroSize,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          transform: `scale(${heroPop * heroPulse})`,
          zIndex: 8,
        }}
      >
        <div
          style={{
            width: heroSize,
            height: heroSize,
            borderRadius: '50%',
            background:
              'radial-gradient(circle at 35% 35%, rgba(212, 175, 55, 0.25) 0%, rgba(15, 23, 42, 0.95) 75%)',
            border: '4px solid #D4AF37',
            boxShadow:
              '0 0 42px rgba(212, 175, 55, 0.45), 0 16px 36px rgba(0, 0, 0, 0.85)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backdropFilter: 'blur(16px)',
          }}
        >
          <SafeImg
            src={heroSrc}
            fallbackSrc={staticFile('icons/history/monument.svg')}
            style={{
              width: heroSize * 0.65,
              height: heroSize * 0.65,
              objectFit: 'contain',
              filter:
                'drop-shadow(0 0 18px rgba(212, 175, 55, 0.8)) drop-shadow(0 8px 16px rgba(0,0,0,0.8))',
            }}
          />
        </div>

        {/* Center label */}
        <div
          style={{
            marginTop: 12,
            padding: '6px 26px',
            borderRadius: 20,
            background: 'linear-gradient(180deg, #D4AF37 0%, #8B6508 100%)',
            border: '2px solid #FFF3C4',
            fontFamily: th.family,
            fontSize: 32,
            fontWeight: 900,
            color: '#1A1202',
            boxShadow: '0 8px 20px rgba(0,0,0,0.7)',
            letterSpacing: '0.02em',
          }}
        >
          {beat.center_label || beat.label || 'المركز'}
        </div>
      </div>

      {/* Floating Corner Badges */}
      {badges.map((b, i) => (
        <FloatBadge
          key={i}
          icon={b.icon}
          label={b.label}
          x={b.x}
          y={b.y}
          size={140}
          borderColor={i % 2 === 0 ? '#38bdf8' : '#D4AF37'}
          delay={15 + i * 5}
        />
      ))}
    </AbsoluteFill>
  );
};
