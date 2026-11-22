import React from 'react';
import {useCurrentFrame, interpolate, staticFile} from 'remotion';
import {SafeImg} from './SafeImg';
import {useTheme, rgba} from './theme';

/**
 * Deterministic pseudo-random helper based on index/seed
 */
const pseudo = (seed: number) => {
  const x = Math.sin(seed * 9999) * 10000;
  return x - Math.floor(x);
};

/**
 * 1. Particles: SVG circles that drift up and fade. Pure math, zero libraries.
 */
export const Particles: React.FC<{
  n?: number;
  color?: [number, number, number];
  speed?: number;
}> = ({n = 20, color, speed = 1}) => {
  const frame = useCurrentFrame();
  const theme = useTheme();
  const baseColor = color ?? theme.p.accent;

  const items = Array.from({length: n}).map((_, i) => {
    const seed = i + 1;
    const xBase = pseudo(seed * 11) * 1080;
    const yStart = 1920 + pseudo(seed * 17) * 200;
    const dur = 90 + pseudo(seed * 23) * 60;
    const size = 3 + pseudo(seed * 29) * 7;
    const swayAmp = 20 + pseudo(seed * 31) * 40;
    const swaySpeed = 0.05 + pseudo(seed * 37) * 0.05;

    // Progress looped across duration
    const localFrame = (frame * speed + seed * 30) % dur;
    const progress = localFrame / dur;

    const y = interpolate(progress, [0, 1], [yStart, yStart - 1800]);
    const x = xBase + Math.sin(frame * swaySpeed + seed) * swayAmp;
    const opacity = interpolate(
      progress,
      [0, 0.2, 0.7, 1],
      [0, 0.8, 0.6, 0]
    );

    return (
      <circle
        key={i}
        cx={x}
        cy={y}
        r={size}
        fill={rgba(baseColor, opacity)}
        filter="drop-shadow(0 0 6px rgba(255, 200, 50, 0.6))"
      />
    );
  });

  return (
    <svg
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: 1080,
        height: 1920,
        pointerEvents: 'none',
        zIndex: 10,
      }}
    >
      {items}
    </svg>
  );
};

/**
 * 2. FireSparks: Cinematic ember particles matching the reference image.
 * Floating upwards with horizontal sine sway, flickering opacity and golden/orange fire glow.
 */
export const FireSparks: React.FC<{
  n?: number;
  zIndex?: number;
}> = ({n = 28, zIndex = 12}) => {
  const frame = useCurrentFrame();

  const embers = Array.from({length: n}).map((_, i) => {
    const s = i + 101;
    const xBase = pseudo(s * 13) * 1080;
    const dur = 75 + pseudo(s * 19) * 45;
    const size = 2 + pseudo(s * 23) * 5;
    const swayAmp = 30 + pseudo(s * 29) * 35;
    const swayFreq = 0.04 + pseudo(s * 31) * 0.04;

    const localFrame = (frame + s * 25) % dur;
    const p = localFrame / dur;

    const y = interpolate(p, [0, 1], [1950, -50]);
    const x = xBase + Math.sin(frame * swayFreq + s) * swayAmp;

    // Golden / amber spark colors
    const colors = [
      '#FFD700', // Gold
      '#FFA500', // Amber
      '#FF8C00', // Dark orange
      '#FFE4B5', // Soft warm white
    ];
    const emberColor = colors[i % colors.length];
    const flicker = 0.5 + 0.5 * Math.sin(frame * 0.4 + s);
    const alpha = interpolate(p, [0, 0.15, 0.8, 1], [0, 0.9, 0.8, 0]) * flicker;

    return (
      <circle
        key={i}
        cx={x}
        cy={y}
        r={size}
        fill={emberColor}
        opacity={alpha}
        style={{
          filter: `drop-shadow(0 0 ${size * 2}px ${emberColor})`,
        }}
      />
    );
  });

  return (
    <svg
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: 1080,
        height: 1920,
        pointerEvents: 'none',
        zIndex,
      }}
    >
      {embers}
    </svg>
  );
};

/**
 * 3. GlowText: Arabic bold text with 3D gold gradient and ambient radial glow.
 * Exactly matches the hook aesthetic from the reference image.
 */
export const GlowText: React.FC<{
  children: React.ReactNode;
  fontSize?: number;
  color?: string;
  gold?: boolean;
  style?: React.CSSProperties;
}> = ({children, fontSize = 64, color, gold = true, style}) => {
  const theme = useTheme();

  const goldGradient =
    'linear-gradient(180deg, #FFF6D1 0%, #F5C542 25%, #D4AF37 55%, #8B6508 100%)';
  const normalGradient = `linear-gradient(180deg, #FFFFFF 0%, ${rgba(theme.p.text, 0.9)} 100%)`;

  return (
    <div
      style={{
        position: 'relative',
        display: 'inline-block',
        textAlign: 'center',
        ...style,
      }}
    >
      {/* Ambient radial glow backdrop */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '120%',
          height: '140%',
          background: gold
            ? 'radial-gradient(ellipse at center, rgba(212, 175, 55, 0.28) 0%, rgba(212, 175, 55, 0) 70%)'
            : `radial-gradient(ellipse at center, ${rgba(theme.p.accent, 0.25)} 0%, transparent 70%)`,
          filter: 'blur(24px)',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      {/* Main Text with vibrant high-contrast gold styling & deep shadow */}
      <div
        style={{
          position: 'relative',
          zIndex: 1,
          fontFamily: `${theme.family}, 'Noto Kufi Arabic', 'Cairo', sans-serif`,
          fontWeight: 900,
          fontSize,
          lineHeight: 1.18,
          letterSpacing: '-0.01em',
          color: color || '#FFFFFF',
          textShadow: gold
            ? '0 0 24px rgba(255, 215, 0, 0.85), 0 0 48px rgba(212, 175, 55, 0.5), 0 4px 14px rgba(0, 0, 0, 0.95)'
            : '0 4px 14px rgba(0, 0, 0, 0.95)',
          filter: gold ? 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.8))' : undefined,
        }}
      >
        {children}
      </div>
    </div>
  );
};

/**
 * 4. ArrowFlow: Animated SVG curved or straight arrow connecting two coordinates.
 * Uses strokeDashoffset to draw the arrow dynamically with an animated arrowhead.
 */
export const ArrowFlow: React.FC<{
  from: {x: number; y: number};
  to: {x: number; y: number};
  color?: string;
  curvature?: number; // offset perpendicular to line
  delay?: number;
  duration?: number;
}> = ({
  from,
  to,
  color = '#38bdf8',
  curvature = 0,
  delay = 0,
  duration = 24,
}) => {
  const frame = useCurrentFrame();

  const progress = interpolate(frame - delay, [0, duration], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const midX = (from.x + to.x) / 2;
  const midY = (from.y + to.y) / 2;
  // Perpendicular vector for curved arc
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const len = Math.hypot(dx, dy) || 1;
  const nx = -dy / len;
  const ny = dx / len;
  const cx = midX + nx * curvature;
  const cy = midY + ny * curvature;

  const pathD = `M ${from.x} ${from.y} Q ${cx} ${cy} ${to.x} ${to.y}`;
  const totalLength = Math.hypot(to.x - from.x, to.y - from.y) * 1.15;
  const strokeDashoffset = interpolate(progress, [0, 1], [totalLength, 0]);

  // Arrowhead angle at target
  const angle = Math.atan2(to.y - cy, to.x - cx) * (180 / Math.PI);

  return (
    <svg
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: 1080,
        height: 1920,
        pointerEvents: 'none',
        zIndex: 5,
      }}
    >
      <defs>
        <filter id={`arrowGlow_${from.x}_${to.x}`}>
          <feDropShadow dx="0" dy="0" stdDeviation="6" flood-color={color} flood-opacity="0.8" />
        </filter>
      </defs>
      {/* Path line */}
      <path
        d={pathD}
        fill="none"
        stroke={color}
        strokeWidth={5}
        strokeLinecap="round"
        strokeDasharray={totalLength}
        strokeDashoffset={strokeDashoffset}
        filter={`url(#arrowGlow_${from.x}_${to.x})`}
      />
      {/* Arrowhead at target when progress > 0.85 */}
      {progress > 0.85 && (
        <polygon
          points={`${to.x},${to.y} ${to.x - 16},${to.y - 10} ${to.x - 10},${to.y} ${to.x - 16},${to.y + 10}`}
          fill={color}
          transform={`rotate(${angle} ${to.x} ${to.y})`}
          opacity={interpolate(progress, [0.85, 1], [0, 1])}
        />
      )}
    </svg>
  );
};

/**
 * 5. FloatBadge: Glassmorphic badge with SVG icon, spring entrance, and bobbing.
 */
import {spring, useVideoConfig} from 'remotion';

export const FloatBadge: React.FC<{
  icon: string;
  label?: string;
  x: number;
  y: number;
  size?: number;
  borderColor?: string;
  delay?: number;
}> = ({
  icon,
  label,
  x,
  y,
  size = 140,
  borderColor = '#D4AF37',
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const theme = useTheme();

  // Spring pop-in (bouncy) instead of linear interpolate
  const pop = spring({
    frame: frame - delay,
    fps,
    config: {stiffness: 150, damping: 11, mass: 0.8},
  });

  // Bobbing float motion
  const bob = Math.sin((frame + delay * 5) * 0.08) * 8;

  const iconSrc = icon.startsWith('http') || icon.startsWith('/') ? icon : staticFile(icon);

  return (
    <div
      style={{
        position: 'absolute',
        left: x - size / 2,
        top: y - size / 2 + bob,
        width: size,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        transform: `scale(${pop})`,
        zIndex: 6,
      }}
    >
      {/* Glassmorphic Badge Container */}
      <div
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          background:
            'radial-gradient(circle at 32% 30%, rgba(255,255,255,0.08) 0%, rgba(10,15,30,0.88) 70%)',
          border: `2.5px solid ${borderColor}`,
          boxShadow: `0 8px 32px rgba(0,0,0,0.65), 0 0 20px ${borderColor}55, inset 0 1px 0 rgba(255,255,255,0.12)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backdropFilter: 'blur(16px)',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <SafeImg
          src={iconSrc}
          fallbackSrc={staticFile('icons/history/monument.svg')}
          style={{
            width: size * 0.56,
            height: size * 0.56,
            objectFit: 'contain',
            filter: 'brightness(0) invert(1) drop-shadow(0 2px 8px rgba(212,175,55,0.65))',
          }}
        />
      </div>

      {/* Label Capsule Below */}
      {label && label.trim() !== '' && (
        <div
          dir="rtl"
          style={{
            marginTop: 8,
            padding: '5px 18px',
            borderRadius: 16,
            background: 'rgba(10, 15, 25, 0.92)',
            border: `1.5px solid ${borderColor}88`,
            fontFamily: theme.family,
            fontSize: 25,
            fontWeight: 800,
            color: '#FFFFFF',
            whiteSpace: 'nowrap',
            boxShadow: '0 4px 12px rgba(0,0,0,0.65)',
            letterSpacing: '0.01em',
          }}
        >
          {label}
        </div>
      )}
    </div>
  );
};

/**
 * 6a. CaptionScrim: Semi-transparent gradient behind the caption zone.
 * Guarantees WCAG AA legibility of captions over complex maps/backgrounds.
 * Place this BELOW <Captions> in z-order.
 */
export const CaptionScrim: React.FC<{
  captionY?: number; // top of caption zone (matches theme.capY - fontSize)
  height?: number;
  opacity?: number;
}> = ({captionY = 1380, height = 540, opacity = 1}) => {
  const th = useTheme();
  // plain grounds: fade into the ground colour itself (a black scrim turned paper/colour backgrounds muddy grey)
  const plain = th.st.bg.type !== 'cinematic' && th.st.bg.type !== 'waves';
  const c = th.st.palette.c1;
  const bg = plain
    ? `linear-gradient(to bottom, rgba(${c[0]},${c[1]},${c[2]},0) 0%, rgba(${c[0]},${c[1]},${c[2]},0.9) 35%, rgba(${c[0]},${c[1]},${c[2]},0.97) 100%)`
    : 'linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.72) 35%, rgba(0,0,0,0.88) 100%)';
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        top: captionY,
        height,
        background: bg,
        pointerEvents: 'none',
        opacity,
        zIndex: 18,
      }}
    />
  );
};

/**
 * 6b. MapOverlay: Dark vignette and subtle background texture layer for map compositions.
 */
export const MapOverlay: React.FC<{
  opacity?: number;
}> = ({opacity = 0.85}) => {
  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: 1080,
        height: 1920,
        background:
          'radial-gradient(circle at 50% 50%, rgba(10, 15, 26, 0.4) 0%, rgba(7, 10, 18, 0.92) 80%, rgba(4, 6, 12, 0.98) 100%)',
        mixBlendMode: 'multiply',
        pointerEvents: 'none',
        opacity,
        zIndex: 2,
      }}
    />
  );
};

