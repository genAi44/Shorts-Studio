import React, {useMemo} from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {evolvePath} from '@remotion/paths';
import {iconToSVG, replaceIDs} from '@iconify/utils';
import iconifyBundle from './generated/iconifyBundle.json';
import type {IconAnimationPreset} from './schema';

// Legacy short-name path fallback for existing beats
export const ICON_PATHS: Record<string, string[]> = {
  star: ['M50 8 L61 38 L93 38 L67 57 L77 88 L50 69 L23 88 L33 57 L7 38 L39 38 Z'],
  question: [
    'M50 10 A40 40 0 1 0 50 90 A40 40 0 1 0 50 10 Z',
    'M38 38 C38 26 62 26 62 38 C62 46 50 48 50 58',
    'M50 70 A3 3 0 1 0 50 76 A3 3 0 1 0 50 70 Z',
  ],
  check: ['M18 52 L42 76 L84 26'],
  x: ['M22 22 L78 78', 'M78 22 L22 78'],
  bolt: ['M56 8 L22 56 L50 56 L42 92 L78 44 L50 44 Z'],
  crown: ['M12 76 L20 28 L50 52 L80 28 L88 76 Z', 'M12 84 L88 84'],
  fire: ['M50 10 C70 32 82 52 76 72 C72 86 60 92 50 92 C40 92 28 86 24 72 C20 56 32 42 40 34 C42 46 50 46 50 10 Z'],
  heart: ['M50 86 C20 64 12 44 18 28 C24 14 40 14 50 28 C60 14 76 14 82 28 C88 44 80 64 50 86 Z'],
  globe: ['M50 10 A40 40 0 1 0 50 90 A40 40 0 1 0 50 10 Z', 'M10 50 L90 50', 'M50 10 C32 30 32 70 50 90', 'M50 10 C68 30 68 70 50 90'],
  clock: ['M50 10 A40 40 0 1 0 50 90 A40 40 0 1 0 50 10 Z', 'M50 26 L50 52 L68 62'],
  pin: ['M50 10 C32 10 20 24 20 40 C20 62 50 90 50 90 C50 90 80 62 80 40 C80 24 68 10 50 10 Z', 'M50 32 A8 8 0 1 0 50 48 A8 8 0 1 0 50 32 Z'],
  book: ['M14 20 L48 26 L48 84 L14 78 Z', 'M86 20 L52 26 L52 84 L86 78 Z'],
  shield: ['M50 10 L86 24 L86 52 C86 72 68 84 50 92 C32 84 14 72 14 52 L14 24 Z'],
  arrow_up: ['M50 86 L50 16', 'M24 42 L50 16 L76 42'],
  arrow_down: ['M50 14 L50 84', 'M24 58 L50 84 L76 58'],
  scale: ['M50 16 L50 86', 'M20 32 L80 32', 'M20 32 L10 58 L30 58 Z', 'M80 32 L70 58 L90 58 Z', 'M32 86 L68 86'],
  mountain: ['M8 84 L44 20 L66 56 L76 40 L92 84 Z'],
  wave: ['M8 40 Q28 20 50 40 T92 40', 'M8 64 Q28 44 50 64 T92 64'],
  sun: ['M50 28 A22 22 0 1 0 50 72 A22 22 0 1 0 50 28 Z', 'M50 8 L50 18', 'M50 82 L50 92', 'M8 50 L18 50', 'M82 50 L92 50'],
  lock: ['M24 46 L76 46 L76 88 L24 88 Z', 'M34 46 L34 32 A16 16 0 0 1 66 32 L66 46'],
  user: ['M50 18 A16 16 0 1 0 50 50 A16 16 0 1 0 50 18 Z', 'M18 88 C18 66 82 66 82 88'],
  trophy: ['M28 16 L72 16 L72 46 C72 62 62 70 50 70 C38 70 28 62 28 46 Z', 'M50 70 L50 86', 'M32 86 L68 86', 'M28 24 L14 24 L14 40 C14 50 22 52 28 52', 'M72 24 L86 24 L86 40 C86 50 78 52 72 52'],
  coin: ['M50 12 A38 38 0 1 0 50 88 A38 38 0 1 0 50 12 Z', 'M50 28 L50 72', 'M38 38 C38 30 62 30 62 40 C62 50 38 50 38 60 C38 70 62 70 62 62'],
  eye: ['M8 50 C24 24 76 24 92 50 C76 76 24 76 8 50 Z', 'M50 36 A14 14 0 1 0 50 64 A14 14 0 1 0 50 36 Z'],
  warning: ['M50 12 L92 86 L8 86 Z', 'M50 38 L50 62', 'M50 74 L50 76'],
  sparkle: ['M50 8 L58 42 L92 50 L58 58 L50 92 L42 58 L8 50 L42 42 Z'],
  sword: ['M18 82 L78 22 L86 14 L78 22', 'M62 22 L78 38', 'M14 86 L28 72', 'M22 66 L34 78'],
  ship: ['M16 62 L84 62 L74 80 L26 80 Z', 'M50 20 L50 62', 'M50 22 L76 54 L50 54 Z'],
  skull: ['M50 14 C26 14 18 32 18 50 C18 62 24 70 32 74 L32 86 L68 86 L68 74 C76 70 82 62 82 50 C82 32 74 14 50 14 Z', 'M38 48 A6 6 0 1 0 38 60 A6 6 0 1 0 38 48 Z', 'M62 48 A6 6 0 1 0 62 60 A6 6 0 1 0 62 48 Z'],
  scroll: ['M24 20 L76 20 L76 80 L24 80 Z', 'M18 20 A6 6 0 1 0 24 26', 'M82 80 A6 6 0 1 0 76 74', 'M34 38 L66 38', 'M34 52 L66 52', 'M34 66 L54 66'],
  plane: ['M12 54 L88 20 L66 84 L50 60 L34 72 L38 54 Z'],
  oil: ['M50 14 C50 14 24 48 24 68 C24 82 36 90 50 90 C64 90 76 82 76 68 C76 48 50 14 50 14 Z'],
  wheat: ['M50 88 L50 20', 'M50 32 C36 28 32 18 44 16 C48 22 50 28 50 32', 'M50 48 C64 44 68 34 56 32 C52 38 50 44 50 48', 'M50 64 C36 60 32 50 44 48 C48 54 50 60 50 64'],
  factory: ['M12 86 L12 44 L38 58 L38 44 L64 58 L64 30 L88 30 L88 86 Z', 'M70 14 C74 20 78 20 82 14'],
  anchor: ['M50 24 A8 8 0 1 0 50 8 A8 8 0 1 0 50 24 Z', 'M50 24 L50 86', 'M32 40 L68 40', 'M18 62 C18 82 36 88 50 88 C64 88 82 82 82 62'],
  gavel: ['M30 42 L58 14 L72 28 L44 56 Z', 'M52 48 L84 80', 'M14 84 L46 84'],
  key: ['M34 32 A18 18 0 1 0 34 68 A18 18 0 1 0 34 32 Z', 'M52 50 L88 50 L88 64', 'M74 50 L74 62'],
  bulb: ['M50 14 C32 14 22 28 22 44 C22 56 32 64 36 72 L64 72 C68 64 78 56 78 44 C78 28 68 14 50 14 Z', 'M38 80 L62 80', 'M42 88 L58 88'],
  atom: ['M50 50 m-6 0 a6 6 0 1 0 12 0 a6 6 0 1 0 -12 0', 'M14 50 A36 14 0 1 0 86 50 A36 14 0 1 0 14 50 Z', 'M32 19 A14 36 30 1 0 68 81 A14 36 30 1 0 32 19 Z', 'M68 19 A36 14 60 1 0 32 81 A36 14 60 1 0 68 19 Z'],
  dna: ['M26 12 C26 38 74 38 74 64 C74 78 58 88 26 88', 'M74 12 C74 38 26 38 26 64 C26 78 42 88 74 88', 'M32 26 L68 26', 'M32 50 L68 50', 'M32 74 L68 74'],
  chart: ['M14 84 L88 84', 'M18 72 L38 50 L56 60 L82 24', 'M68 24 L82 24 L82 38'],
  hand: ['M24 60 L44 44 L64 56 L84 40', 'M12 46 L28 30 L44 44', 'M88 46 L72 30 L56 44'],
};

const SHORT_TO_ICONIFY: Record<string, string> = {
  landmark: 'lucide:landmark',
  capital: 'lucide:landmark',
  parliament: 'lucide:landmark',
  government: 'lucide:landmark',
  building: 'lucide:building',
  city: 'lucide:building-2',
  question: 'lucide:help-circle',
  help: 'lucide:help-circle',
  'help-circle': 'lucide:help-circle',
  mystery: 'lucide:help-circle',
  info: 'lucide:info',
  history: 'lucide:history',
  pyramid: 'lucide:pyramid',
  castle: 'lucide:castle',
  crown: 'lucide:crown',
  star: 'lucide:star',
  check: 'lucide:check-circle-2',
  bolt: 'lucide:zap',
  zap: 'lucide:zap',
  fire: 'lucide:flame',
  flame: 'lucide:flame',
  heart: 'lucide:heart',
  globe: 'lucide:globe',
  world: 'lucide:globe',
  earth: 'lucide:globe',
  clock: 'lucide:clock',
  hourglass: 'lucide:hourglass',
  pin: 'lucide:map-pin',
  'map-pin': 'lucide:map-pin',
  map: 'lucide:map',
  compass: 'lucide:compass',
  book: 'lucide:book-open',
  shield: 'lucide:shield',
  arrow_up: 'lucide:trending-up',
  'trending-up': 'lucide:trending-up',
  arrow_down: 'lucide:trending-down',
  scale: 'lucide:scale',
  justice: 'lucide:scale',
  mountain: 'lucide:mountain',
  wave: 'lucide:waves',
  sun: 'lucide:sun',
  lock: 'lucide:lock',
  user: 'lucide:user-round',
  users: 'lucide:users',
  people: 'lucide:users',
  population: 'lucide:users',
  trophy: 'lucide:trophy',
  medal: 'lucide:medal',
  coin: 'lucide:coins',
  coins: 'lucide:coins',
  money: 'lucide:coins',
  eye: 'lucide:eye',
  warning: 'lucide:alert-triangle',
  sparkle: 'lucide:sparkles',
  sparkles: 'lucide:sparkles',
  sword: 'lucide:swords',
  swords: 'lucide:swords',
  ship: 'lucide:ship',
  scroll: 'lucide:scroll-text',
  plane: 'lucide:plane',
  oil: 'lucide:droplet',
  wheat: 'lucide:wheat',
  factory: 'lucide:factory',
  anchor: 'lucide:anchor',
  gavel: 'lucide:gavel',
  key: 'lucide:key',
  bulb: 'lucide:lightbulb',
  lightbulb: 'lucide:lightbulb',
  atom: 'lucide:atom',
  dna: 'lucide:dna',
  chart: 'lucide:bar-chart-3',
  mosque: 'ph:mosque',
  monument: 'tabler:building-monument',
  timeline: 'tabler:timeline',
};

type CachedIconData = {
  viewBox: string;
  paths: string[];
  rawBody: string;
};

// Module-level cache for 4K rendering performance (zero per-frame SVG parsing)
const ICON_CACHE = new Map<string, CachedIconData>();

const extractPathsFromBody = (body: string): string[] => {
  const paths: string[] = [];
  const dRegex = /<path[^>]*\bd="([^"]+)"[^>]*\/?>/gi;
  let match: RegExpExecArray | null;
  while ((match = dRegex.exec(body)) !== null) {
    paths.push(match[1]);
  }
  const circleRegex = /<circle[^>]*\bcx="([^"]+)"[^>]*\bcy="([^"]+)"[^>]*\br="([^"]+)"[^>]*\/?>/gi;
  while ((match = circleRegex.exec(body)) !== null) {
    const cx = parseFloat(match[1]);
    const cy = parseFloat(match[2]);
    const r = parseFloat(match[3]);
    if (!Number.isNaN(cx) && !Number.isNaN(cy) && !Number.isNaN(r)) {
      paths.push(`M ${cx - r} ${cy} a ${r} ${r} 0 1 0 ${r * 2} 0 a ${r} ${r} 0 1 0 ${-r * 2} 0`);
    }
  }
  const rectRegex = /<rect[^>]*\bx="([^"]+)"[^>]*\by="([^"]+)"[^>]*\bwidth="([^"]+)"[^>]*\bheight="([^"]+)"[^>]*\/?>/gi;
  while ((match = rectRegex.exec(body)) !== null) {
    const x = parseFloat(match[1]);
    const y = parseFloat(match[2]);
    const w = parseFloat(match[3]);
    const h = parseFloat(match[4]);
    if (!Number.isNaN(x) && !Number.isNaN(y) && !Number.isNaN(w) && !Number.isNaN(h)) {
      paths.push(`M ${x} ${y} H ${x + w} V ${y + h} H ${x} Z`);
    }
  }
  const polyRegex = /<(?:polyline|polygon)[^>]*\bpoints="([^"]+)"[^>]*\/?>/gi;
  while ((match = polyRegex.exec(body)) !== null) {
    const pts = match[1].trim().split(/[\s,]+/);
    if (pts.length >= 4) {
      let d = `M ${pts[0]} ${pts[1]}`;
      for (let i = 2; i < pts.length - 1; i += 2) {
        d += ` L ${pts[i]} ${pts[i + 1]}`;
      }
      if (match[0].toLowerCase().startsWith('<polygon')) d += ' Z';
      paths.push(d);
    }
  }
  const lineRegex = /<line[^>]*\bx1="([^"]+)"[^>]*\by1="([^"]+)"[^>]*\bx2="([^"]+)"[^>]*\by2="([^"]+)"[^>]*\/?>/gi;
  while ((match = lineRegex.exec(body)) !== null) {
    paths.push(`M ${match[1]} ${match[2]} L ${match[3]} ${match[4]}`);
  }
  return paths;
};

export const resolveIconData = (rawName: string): CachedIconData => {
  const key = (rawName || 'lucide:star').trim().toLowerCase();
  const cached = ICON_CACHE.get(key);
  if (cached) return cached;

  const normalized = SHORT_TO_ICONIFY[key] ?? key;
  const sets = (iconifyBundle as any).sets || {};

  if (normalized.includes(':')) {
    const [prefix, iconName] = normalized.split(':');
    const setDict = sets[prefix];
    const iconObj = setDict?.[iconName];
    if (iconObj) {
      const rendered = iconToSVG(iconObj);
      const vb = rendered.attributes.viewBox || `0 0 ${iconObj.width || 24} ${iconObj.height || 24}`;
      const paths = extractPathsFromBody(rendered.body);
      const data: CachedIconData = {
        viewBox: vb,
        paths,
        rawBody: replaceIDs(rendered.body),
      };
      ICON_CACHE.set(key, data);
      return data;
    }
  }

  // Fallback to searching across sets if no prefix was given
  for (const prefix of ['lucide', 'ph', 'tabler']) {
    const iconObj = sets[prefix]?.[normalized];
    if (iconObj) {
      const rendered = iconToSVG(iconObj);
      const vb = rendered.attributes.viewBox || `0 0 ${iconObj.width || 24} ${iconObj.height || 24}`;
      const paths = extractPathsFromBody(rendered.body);
      const data: CachedIconData = {
        viewBox: vb,
        paths,
        rawBody: replaceIDs(rendered.body),
      };
      ICON_CACHE.set(key, data);
      return data;
    }
  }

  // Legacy 100x100 paths
  const legacyPaths = ICON_PATHS[key] ?? ICON_PATHS.star;
  const fallback: CachedIconData = {
    viewBox: '0 0 100 100',
    paths: legacyPaths,
    rawBody: legacyPaths.map((d) => `<path d="${d}" fill="none" stroke="currentColor" />`).join(''),
  };
  ICON_CACHE.set(key, fallback);
  return fallback;
};

export interface IconProps {
  name: string;
  size?: number;
  color?: string;
  strokeWidth?: number;
  stroke?: number;
  draw?: number;
  animation?: IconAnimationPreset;
  delayFrames?: number;
  style?: React.CSSProperties;
}

export const Icon: React.FC<IconProps> = ({
  name,
  size = 96,
  color = 'currentColor',
  strokeWidth,
  stroke,
  draw,
  animation = 'none',
  delayFrames = 0,
  style,
}) => {
  const resolvedStrokeWidth = strokeWidth ?? stroke ?? 2.2;
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const localFrame = Math.max(0, frame - delayFrames);
  const data = useMemo(() => resolveIconData(name), [name]);

  // Compute Remotion frame-driven animation transform & stroke evolution
  let drawProgress = draw ?? 1;
  let scale = 1;
  let translateY = 0;
  let rotateDeg = 0;
  let opacity = 1;

  if (animation === 'draw' && draw === undefined) {
    drawProgress = interpolate(localFrame, [0, Math.round(fps * 0.75)], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    opacity = interpolate(localFrame, [0, 4], [0, 1], {extrapolateRight: 'clamp'});
  } else if (animation === 'pop') {
    const sp = spring({
      frame: localFrame,
      fps,
      config: {damping: 12, stiffness: 180, mass: 0.7},
    });
    scale = interpolate(sp, [0, 1], [0.25, 1]);
    opacity = Math.min(1, sp * 1.5);
  } else if (animation === 'float') {
    const enter = spring({frame: localFrame, fps, config: {damping: 16, stiffness: 140}});
    scale = interpolate(enter, [0, 1], [0.85, 1]);
    translateY = Math.sin((localFrame / fps) * Math.PI * 1.6) * 8;
    opacity = Math.min(1, enter * 1.5);
  } else if (animation === 'pulse') {
    const enter = spring({frame: localFrame, fps, config: {damping: 14, stiffness: 150}});
    scale = enter * (1 + 0.08 * Math.sin((localFrame / fps) * Math.PI * 2.5));
    opacity = Math.min(1, enter * 1.5);
  } else if (animation === 'rotate') {
    const enter = spring({frame: localFrame, fps, config: {damping: 15, stiffness: 140}});
    scale = enter;
    rotateDeg = (localFrame / fps) * 60;
    opacity = Math.min(1, enter * 1.5);
  }

  const isLegacy100 = data.viewBox === '0 0 100 100';
  const effectiveStrokeWidth = isLegacy100 ? Math.max(5, resolvedStrokeWidth) : Math.min(4, resolvedStrokeWidth);

  return (
    <svg
      data-audit-icon="1"
      width={size}
      height={size}
      viewBox={data.viewBox}
      style={{
        overflow: 'visible',
        color,
        opacity,
        transform: `translateY(${translateY.toFixed(2)}px) scale(${scale.toFixed(3)}) rotate(${rotateDeg.toFixed(2)}deg)`,
        transformOrigin: 'center center',
        ...style,
      }}
    >
      {data.paths.length > 0 ? (
        data.paths.map((d, idx) => {
          const prog = Math.max(0.001, Math.min(1, drawProgress));
          let evo: {strokeDasharray?: string; strokeDashoffset?: number} = {};
          if (prog < 0.999) {
            try {
              evo = evolvePath(prog, d);
            } catch {
              evo = {};
            }
          }
          return (
            <path
              key={idx}
              d={d}
              fill="none"
              stroke={color}
              strokeWidth={effectiveStrokeWidth}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray={evo.strokeDasharray}
              strokeDashoffset={evo.strokeDashoffset}
            />
          );
        })
      ) : (
        <g dangerouslySetInnerHTML={{__html: data.rawBody}} />
      )}
    </svg>
  );
};
