import React, {useMemo} from 'react';
import {interpolate, spring} from 'remotion';
import {rgba} from './theme';
import {MAP_LENS} from './layout';
import type {MapCountryShape, MapFeature, MapWaypoint} from './mapOverlay';

/**
 * Vector map engine (SVG, offline, deterministic).
 * Layers: sea gradient + parallax topographic contours + graticule -> context land (hatched) -> target land
 * (gradient, coastal glow, procedural terrain texture) -> city halo -> animated route (curved arc, arrowhead,
 * travelling dot) -> pins that drop with a spring -> magnifier lens for tiny places.
 * A city/capital subject highlights a halo around the city and only dims-in its country, never floods the whole country.
 */

export type MapCam = {tx: number; ty: number; z: number};

type Colors = {accent: string; accent2: string; text: string; sea0: string; sea1: string; ctxFill: string; ctxStroke: string};

export type MapViewportProps = {
  frame: number;
  fps: number;
  vw: number;
  vh: number;
  height: number;
  ctxPath: string;
  countries: MapCountryShape[];
  waypoints: MapWaypoint[];
  activeIdx: number;
  prevWp: {x: number; y: number; name_ar?: string} | null;
  camTransition: number;
  features: MapFeature[];
  main: MapCam;
  lens: MapCam | null; // zoomed view shown in the magnifier when the place is tiny
  lensC: {cx: number; cy: number}; // lens centre inside the VISIBLE part of the viewBox
  colors: Colors;
  font: string;
  uid: string;
};

const CITY_KINDS = new Set(['capital', 'city', 'landmark']);

const hash = (s: string) => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return Math.abs(h) % 1000;
};

const bez = (p0: number, c: number, p1: number, t: number) => (1 - t) * (1 - t) * p0 + 2 * (1 - t) * t * c + t * t * p1;

/** Teardrop marker, tip at (0,0). */
const PIN_PATH = 'M0 0 C-9 -12 -15 -20 -15 -28 A15 15 0 1 1 15 -28 C15 -20 9 -12 0 0 Z';

const Defs: React.FC<{uid: string; c: Colors; seed: number}> = ({uid, c, seed}) => (
  <defs>
    <radialGradient id={`${uid}sea`} cx="50%" cy="48%" r="75%">
      <stop offset="0%" stopColor={c.sea0} />
      <stop offset="100%" stopColor={c.sea1} />
    </radialGradient>
    <linearGradient id={`${uid}land`} x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stopColor={c.accent} stopOpacity={0.62} />
      <stop offset="100%" stopColor={c.accent2} stopOpacity={0.3} />
    </linearGradient>
    <radialGradient id={`${uid}halo`} cx="50%" cy="50%" r="50%">
      <stop offset="0%" stopColor={c.accent} stopOpacity={0.55} />
      <stop offset="60%" stopColor={c.accent} stopOpacity={0.16} />
      <stop offset="100%" stopColor={c.accent} stopOpacity={0} />
    </radialGradient>
    <pattern id={`${uid}hatch`} width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">
      <line x1="0" y1="0" x2="0" y2="9" stroke={c.ctxStroke} strokeOpacity={0.5} strokeWidth="1.4" />
    </pattern>
    <filter id={`${uid}glow`} x="-25%" y="-25%" width="150%" height="150%">
      <feGaussianBlur stdDeviation="4" result="b" />
      <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
    </filter>
    <filter id={`${uid}soft`} x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="9" />
    </filter>
    <filter id={`${uid}terrain`} x="0%" y="0%" width="100%" height="100%" filterUnits="objectBoundingBox">
      <feTurbulence type="fractalNoise" baseFrequency="0.022 0.03" numOctaves="3" seed={seed} result="n" />
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0.9 0.9 0.9 0 -1.15" />
    </filter>
    <filter id={`${uid}shadow`} x="-50%" y="-50%" width="200%" height="200%">
      <feDropShadow dx="0" dy="2" stdDeviation="2.4" floodColor="#000" floodOpacity="0.7" />
    </filter>
  </defs>
);

const Sea: React.FC<{p: MapViewportProps; cam: MapCam; waves: string[]}> = ({p, cam, waves}) => (
  <>
    <rect width={p.vw} height={p.vh} fill={`url(#${p.uid}sea)`} />
    {/* parallax topographic contours: move at 35% of the camera so the land feels in front of the sea */}
    <g transform={`translate(${(cam.tx * 0.35).toFixed(1)} ${(cam.ty * 0.35).toFixed(1)})`} opacity={0.5}>
      {waves.map((d, i) => <path key={i} d={d} fill="none" stroke={rgba([120, 190, 255] as any, 0.09)} strokeWidth={1.4} />)}
    </g>
    <g opacity={0.12}>
      {[0.25, 0.5, 0.75].map((r) => <line key={`gy${r}`} x1={0} y1={p.vh * r} x2={p.vw} y2={p.vh * r} stroke={p.colors.accent} strokeWidth={1.1} strokeDasharray="6 8" />)}
      {[0.2, 0.4, 0.6, 0.8].map((r) => <line key={`gx${r}`} x1={p.vw * r} y1={0} x2={p.vw * r} y2={p.vh} stroke={p.colors.accent} strokeWidth={1.1} strokeDasharray="6 8" />)}
    </g>
  </>
);

const World: React.FC<{p: MapViewportProps; cam: MapCam; seed: number; isLens?: boolean}> = ({p, cam, seed, isLens}) => {
  const {frame, fps, uid, colors, activeIdx, waypoints, countries, ctxPath, prevWp, camTransition} = p;
  const active = waypoints[activeIdx];
  const z = cam.z;
  const cityFocus = CITY_KINDS.has(active.kind);
  const regionFocus = active.kind === 'continent';
  const local = Math.max(0, frame - active.trigger_frame);

  // visible region in map coordinates (terrain texture is only generated for what is on screen)
  const vx = -cam.tx / z, vy = -cam.ty / z, vwz = p.vw / z, vhz = p.vh / z;

  // route: curved arc from the previous waypoint to the active one
  const route = (() => {
    if (!prevWp) return null;
    const dx = active.x - prevWp.x, dy = active.y - prevWp.y;
    const len = Math.hypot(dx, dy);
    if (len < 8) return null;
    const nx = -dy / len, ny = dx / len;
    let lift = Math.min(70, len * 0.28);
    if (ny * lift > 0) lift = -lift; // always bulge upward on screen
    const cx = (prevWp.x + active.x) / 2 + nx * lift;
    const cy = (prevWp.y + active.y) / 2 + ny * lift;
    const t = Math.min(1, camTransition);
    const px = bez(prevWp.x, cx, active.x, t), py = bez(prevWp.y, cy, active.y, t);
    const tx = 2 * (1 - t) * (cx - prevWp.x) + 2 * t * (active.x - cx);
    const ty = 2 * (1 - t) * (cy - prevWp.y) + 2 * t * (active.y - cy);
    return {d: `M${prevWp.x.toFixed(1)} ${prevWp.y.toFixed(1)} Q${cx.toFixed(1)} ${cy.toFixed(1)} ${active.x.toFixed(1)} ${active.y.toFixed(1)}`, px, py, ang: (Math.atan2(ty, tx) * 180) / Math.PI, t};
  })();

  // unique pins (a country + its capital share one pin)
  const pins: {wp: MapWaypoint; idx: number}[] = [];
  for (let i = 0; i <= activeIdx && i < waypoints.length; i++) {
    const w = waypoints[i];
    const at = pins.findIndex((u) => Math.hypot(u.wp.x - w.x, u.wp.y - w.y) < 4);
    if (at >= 0) pins[at] = {wp: CITY_KINDS.has(pins[at].wp.kind) ? pins[at].wp : w, idx: i};
    else pins.push({wp: w, idx: i});
  }

  const pulse = ((frame - active.trigger_frame) % 40) / 40;
  const routeColor = (active as any).arrow === 'attack' ? '#ef4444' : colors.accent2;

  return (
    <g transform={`translate(${cam.tx.toFixed(1)} ${cam.ty.toFixed(1)}) scale(${z.toFixed(3)})`}>
      {ctxPath ? (
        <>
          <path d={ctxPath} fill={colors.ctxFill} stroke={colors.ctxStroke} strokeWidth={1.1 / z} />
          <path d={ctxPath} fill={`url(#${uid}hatch)`} stroke="none" />
        </>
      ) : null}

      {countries.map((c, ci) => {
        if (!c.d) return null;
        const target = regionFocus || !active.iso3 || c.iso3 === active.iso3;
        const fillOp = target ? (cityFocus ? 0.62 : 1) : 0.3;
        return (
          <g key={`${c.iso3}_${ci}`}>
            {target && <path d={c.d} fill="none" stroke={colors.accent} strokeWidth={9 / z} strokeOpacity={0.22} filter={`url(#${uid}soft)`} />}
            <path d={c.d} fill={`url(#${uid}land)`} fillOpacity={fillOp} stroke={colors.accent} strokeOpacity={target ? 1 : 0.4} strokeWidth={(target ? 2.6 : 1.3) / z} strokeLinejoin="round" filter={target ? `url(#${uid}glow)` : undefined} />
          </g>
        );
      })}

      {/* procedural terrain texture on the highlighted land only (noise clipped by the country outlines) */}
      <clipPath id={`${uid}clip${isLens ? 'L' : 'M'}`}>
        {countries.filter((c) => c.d && (regionFocus || !active.iso3 || c.iso3 === active.iso3)).map((c, i) => <path key={i} d={c.d} />)}
      </clipPath>
      <g clipPath={`url(#${uid}clip${isLens ? 'L' : 'M'})`} opacity={0.34} style={{mixBlendMode: 'overlay'}}>
        <rect x={vx} y={vy} width={vwz} height={vhz} filter={`url(#${uid}terrain)`} />
      </g>

      {/* terrain / sea / region features: rivers draw themselves, lakes fill, areas are marked ellipses */}
      {p.features.map((f) => {
        const lp = Math.max(0, frame - f.trigger_frame);
        const fin = Math.min(1, lp / 14);
        if (frame < f.trigger_frame - 2) return null;
        const draw = Math.min(1, lp / 42);
        return (
          <g key={f.id} opacity={fin}>
            {f.shape === 'river' && f.d && (
              <>
                <path d={f.d} fill="none" stroke={colors.accent2} strokeWidth={9 / z} strokeOpacity={0.2} strokeLinecap="round" strokeLinejoin="round" filter={`url(#${uid}soft)`} />
                <path d={f.d} fill="none" stroke={colors.accent2} strokeWidth={3.4 / z} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - draw} filter={`url(#${uid}glow)`} />
              </>
            )}
            {f.shape === 'lake' && f.d && <path d={f.d} fill={colors.accent2} fillOpacity={0.55} stroke={colors.accent2} strokeWidth={2 / z} filter={`url(#${uid}glow)`} />}
            {f.shape === 'area' && f.rx > 0 && (
              <>
                <ellipse cx={f.cx} cy={f.cy} rx={f.rx * (0.6 + 0.4 * draw)} ry={f.ry * (0.6 + 0.4 * draw)} fill={colors.accent} fillOpacity={0.14} stroke={colors.accent2} strokeWidth={2.4 / z} strokeDasharray={`${9 / z} ${8 / z}`} strokeDashoffset={-(frame * 0.6) / z} />
                {f.approx && <text x={f.cx} y={f.cy + f.ry + 22 / z} textAnchor="middle" fontSize={14 / z} fill={colors.text} opacity={0.75} fontFamily={p.font}>حدود تقريبية</text>}
              </>
            )}
            {f.shape === 'mountain' && (
              <g transform={`translate(${f.cx} ${f.cy}) scale(${(1 / z).toFixed(3)})`} filter={`url(#${uid}shadow)`}>
                <path d="M-26 0 L0 -46 L26 0 Z" fill={colors.accent} stroke="#040914" strokeWidth={2.4} />
                <path d="M-8 -26 L0 -46 L8 -26 L0 -30 Z" fill="#fff" opacity={0.9} />
              </g>
            )}
          </g>
        );
      })}

      {/* city halo: the subject is the city, not the whole country */}
      {cityFocus && (
        <g>
          <circle cx={active.x} cy={active.y} r={(52 + 6 * Math.sin(frame / 9)) / z} fill={`url(#${uid}halo)`} />
          <circle cx={active.x} cy={active.y} r={30 / z} fill="none" stroke={colors.accent} strokeWidth={1.6 / z} strokeDasharray={`${5 / z} ${7 / z}`} strokeOpacity={0.8} transform={`rotate(${(frame * 1.6) % 360} ${active.x} ${active.y})`} />
        </g>
      )}

      {route && (
        <g>
          <path d={route.d} fill="none" stroke={routeColor} strokeWidth={9 / z} strokeOpacity={0.18} strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - route.t} filter={`url(#${uid}soft)`} />
          <path d={route.d} fill="none" stroke={routeColor} strokeWidth={3.2 / z} strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - route.t} filter={`url(#${uid}glow)`} />
          <path d={route.d} fill="none" stroke="#fff" strokeWidth={1.1 / z} strokeLinecap="round" pathLength={1} strokeDasharray={`0.012 0.03`} strokeDashoffset={-(frame * 0.012)} opacity={0.85} />
          <g transform={`translate(${route.px.toFixed(1)} ${route.py.toFixed(1)}) rotate(${route.ang.toFixed(1)}) scale(${(1 / z).toFixed(3)})`}>
            <path d="M0 0 L-11 -6 L-11 6 Z" fill="#fff" opacity={route.t < 1 ? 1 : 0.0} />
          </g>
          <circle cx={prevWp!.x} cy={prevWp!.y} r={5 / z} fill="#e2e8f0" stroke={colors.accent2} strokeWidth={2 / z} />
        </g>
      )}

      {pins.map(({wp, idx}) => {
        const current = idx === activeIdx || Math.hypot(wp.x - active.x, wp.y - active.y) < 4;
        const lp = Math.max(0, frame - wp.trigger_frame);
        const drop = spring({frame: lp, fps, config: {damping: 9, stiffness: 150, mass: 0.6}});
        const lift = (1 - Math.min(1.15, drop)) * 80;
        const s = (current ? 1 : 0.7) / z;
        const badgeW = 150 / z, badgeH = 34 / z;
        const above = wp.y > p.vh * 0.45;
        const labelX = Math.max(-cam.tx / z + 8 / z, Math.min(-cam.tx / z + p.vw / z - badgeW - 8 / z, wp.x - badgeW / 2));
        const labelY = above ? wp.y - 62 / z - badgeH : wp.y + 14 / z;
        return (
          <g key={wp.id}>
            {current && lp > 6 && (
              <>
                <circle cx={wp.x} cy={wp.y} r={(10 + 34 * pulse) / z} fill="none" stroke="#fde047" strokeWidth={2.2 / z} opacity={(1 - pulse) * 0.85} />
                <circle cx={wp.x} cy={wp.y} r={(10 + 34 * ((pulse + 0.5) % 1)) / z} fill="none" stroke="#fde047" strokeWidth={1.6 / z} opacity={(1 - ((pulse + 0.5) % 1)) * 0.5} />
              </>
            )}
            <ellipse cx={wp.x} cy={wp.y} rx={9 * s * Math.min(1, drop)} ry={3.4 * s * Math.min(1, drop)} fill="#000" opacity={0.5} />
            <g transform={`translate(${wp.x} ${(wp.y - lift / z).toFixed(1)}) scale(${s.toFixed(3)})`} filter={`url(#${uid}shadow)`} opacity={Math.min(1, lp / 3)}>
              <path d={PIN_PATH} fill={current ? '#fde047' : '#cbd5e1'} stroke="#040914" strokeWidth={2.2} />
              <circle cx={0} cy={-28} r={6} fill="#040914" />
            </g>
            {current && !isLens && lp > 8 && (
              <foreignObject x={labelX} y={labelY} width={badgeW} height={badgeH} opacity={Math.min(1, (lp - 8) / 6)}>
                <div dir="rtl" lang="ar" style={{width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(4,10,24,0.92)', border: `1.5px solid ${colors.accent}`, borderRadius: 999, color: '#fde047', fontSize: Math.round(17 / z), fontWeight: 900, fontFamily: p.font, boxShadow: '0 4px 12px rgba(0,0,0,0.65)', whiteSpace: 'nowrap', padding: '0 8px'}}>
                  {wp.name_ar}
                </div>
              </foreignObject>
            )}
          </g>
        );
      })}
    </g>
  );
};

export const MapViewport: React.FC<MapViewportProps> = (p) => {
  const seed = useMemo(() => hash(p.waypoints[0]?.id || 'map'), [p.waypoints]);
  const waves = useMemo(() => {
    const out: string[] = [];
    for (let row = -3; row < 9; row++) {
      let d = '';
      for (let x = -p.vw; x <= p.vw * 2; x += 40) {
        const y = row * 90 + 22 * Math.sin((x / 380) * Math.PI * 2 + row * 0.7);
        d += `${x === -p.vw ? 'M' : 'L'}${x} ${y.toFixed(1)} `;
      }
      out.push(d);
    }
    return out;
  }, [p.vw]);

  const lens = p.lens;
  // lens fades/scales in with the camera move; connector links the lens to the pin on the main map
  const lensIn = Math.min(1, p.camTransition * 1.4);
  const active = p.waypoints[p.activeIdx];
  const pinX = p.main.tx + active.x * p.main.z;
  const pinY = p.main.ty + active.y * p.main.z;
  const L = {cx: p.lensC.cx, cy: p.lensC.cy, r: MAP_LENS.r};
  const ang = Math.atan2(pinY - L.cy, pinX - L.cx);
  const edgeX = L.cx + Math.cos(ang) * L.r, edgeY = L.cy + Math.sin(ang) * L.r;

  return (
    <svg width="100%" height={p.height} viewBox={`0 0 ${p.vw} ${p.vh}`} preserveAspectRatio="xMidYMid slice" style={{display: 'block'}}>
      <Defs uid={p.uid} c={p.colors} seed={seed} />
      <Sea p={p} cam={p.main} waves={waves} />
      <World p={p} cam={p.main} seed={seed} />
      {lens && (
        <g opacity={lensIn}>
          <line x1={edgeX} y1={edgeY} x2={pinX} y2={pinY} stroke={p.colors.accent} strokeWidth={1.8} strokeDasharray="5 5" opacity={0.85} />
          <circle cx={pinX} cy={pinY} r={14} fill="none" stroke={p.colors.accent} strokeWidth={1.8} opacity={0.9} />
          <clipPath id={`${p.uid}lens`}><circle cx={L.cx} cy={L.cy} r={L.r} /></clipPath>
          <circle cx={L.cx} cy={L.cy} r={L.r + 6} fill="rgba(4,10,24,0.85)" />
          <g clipPath={`url(#${p.uid}lens)`}>
            <rect x={L.cx - L.r} y={L.cy - L.r} width={L.r * 2} height={L.r * 2} fill={`url(#${p.uid}sea)`} />
            <World p={p} cam={lens} seed={seed} isLens />
          </g>
          <circle cx={L.cx} cy={L.cy} r={L.r} fill="none" stroke={p.colors.accent} strokeWidth={4} />
          <circle cx={L.cx} cy={L.cy} r={L.r + 8} fill="none" stroke={p.colors.accent} strokeWidth={1.2} opacity={0.45} />
        </g>
      )}
    </svg>
  );
};
