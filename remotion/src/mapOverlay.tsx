import React from 'react';
import {AbsoluteFill, Easing, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {SafeImg} from './SafeImg';
import {rgba, useTheme} from './theme';

export type MapWaypoint = {
  id: string;
  kind: 'capital' | 'city' | 'country' | string;
  kind_label: string;
  name_ar: string;
  name_en?: string;
  country_ar?: string;
  iso3?: string;
  iso2?: string;
  lat: number;
  lon: number;
  coords: string;
  x: number;
  y: number;
  trigger_frame: number;
  end_frame: number;
  zoom: number;
};

export type MapCountryShape = {
  iso3: string;
  name_ar: string;
  d: string;
  cx: number;
  cy: number;
};

export type MapOverlaySpec = {
  enabled: boolean;
  placement?: 'top-left' | 'top-right' | 'bottom-left' | string;
  enter_frame: number;
  exit_frame: number;
  viewport: {w: number; h: number};
  ctx_path: string;
  countries: MapCountryShape[];
  waypoints: MapWaypoint[];
  prev_waypoint?: {name_ar: string; x: number; y: number} | null;
  zoom_hierarchy?: string[];
  map_style?: 'historical' | 'modern' | string;
};

export const MapOverlayLayer: React.FC<{overlay?: MapOverlaySpec | null; splitBottom?: boolean; mode?: 'hud' | 'split-bottom' | 'full-stage'}> = ({overlay, splitBottom = false, mode}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const th = useTheme();

  if (!overlay || !overlay.enabled || !overlay.waypoints || overlay.waypoints.length === 0) {
    return null;
  }

  const {enter_frame, exit_frame, viewport, ctx_path, countries, waypoints, prev_waypoint} = overlay;
  if (frame < enter_frame - 2 || frame > exit_frame + 6) {
    return null;
  }

  const vw = viewport?.w || 420;
  const vh = viewport?.h || 260;
  const cx0 = vw / 2;
  const cy0 = vh / 2;

  // Entrance & exit envelope synced to voiceover timing
  const enterSpring = spring({
    frame: Math.max(0, frame - enter_frame),
    fps,
    config: {damping: 16, stiffness: 120, mass: 0.85},
  });
  const exitFade = interpolate(
    frame,
    [Math.max(enter_frame + 12, exit_frame - 14), Math.max(enter_frame + 16, exit_frame)],
    [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );
  const visibility = enterSpring * exitFade;

  // Determine active waypoint based on current frame
  let activeIdx = 0;
  for (let i = 0; i < waypoints.length; i++) {
    if (frame >= waypoints[i].trigger_frame) {
      activeIdx = i;
    }
  }
  const activeWp = waypoints[activeIdx];
  const prevWp = activeIdx > 0 ? waypoints[activeIdx - 1] : prev_waypoint || null;

  // If the current waypoint is a country mention but the same scene also mentions its capital/city,
  // display the unified "Capital — عاصمة Country" label so the title never flips or confuses the viewer.
  const pairedCityWp =
    activeWp.kind === 'country' && activeWp.iso3
      ? waypoints.find((w) => w.iso3 === activeWp.iso3 && (w.kind === 'capital' || w.kind === 'city')) || activeWp
      : activeWp;

  const headerTitle = (() => {
    const w = pairedCityWp;
    if (w.kind === 'capital' && w.country_ar && w.country_ar !== w.name_ar) {
      return `${w.name_ar} — عاصمة ${w.country_ar}`;
    }
    if (w.kind === 'city' && w.country_ar && w.country_ar !== w.name_ar) {
      return `${w.name_ar} — ${w.country_ar}`;
    }
    if (w.kind === 'landmark' && w.country_ar && w.country_ar !== w.name_ar) {
      return `${w.name_ar} — ${w.country_ar}`;
    }
    if (w.kind === 'continent') {
      return `قارة ${w.name_ar}`;
    }
    if (w.kind === 'country') {
      return `دولة ${w.name_ar}`;
    }
    return w.name_ar;
  })();

  const iso2Lower = (pairedCityWp.iso2 || activeWp.iso2 || '').trim().toLowerCase();

  // Smooth multi-stage camera transition (Continent/World -> Country -> City) with strict border-preserving clamp
  const localFrame = Math.max(0, frame - activeWp.trigger_frame);
  const useHierarchy = activeIdx === 0 && (overlay.zoom_hierarchy?.length ?? 0) >= 3 && activeWp.zoom > 1.08;
  const camTransition = useHierarchy
    ? interpolate(localFrame, [0, 9, 26], [0, 0.28, 1], {
        easing: Easing.bezier(0.22, 1, 0.36, 1),
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : interpolate(localFrame, [0, 24], [0, 1], {
        easing: Easing.bezier(0.22, 1, 0.36, 1),
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });

  const startX = prevWp ? prevWp.x : cx0;
  const startY = prevWp ? prevWp.y : cy0;
  const startZoom = activeIdx > 0 ? waypoints[activeIdx - 1].zoom : 1.0;

  const camX = interpolate(camTransition, [0, 1], [startX, activeWp.x]);
  const camY = interpolate(camTransition, [0, 1], [startY, activeWp.y]);
  const camZoom = Math.max(1.0, interpolate(camTransition, [0, 1], [startZoom, activeWp.zoom]));

  const rawTx = cx0 - camX * camZoom;
  const rawTy = cy0 - camY * camZoom;
  const minTx = vw * (1 - camZoom);
  const minTy = vh * (1 - camZoom);
  const tx = Math.max(minTx, Math.min(0, rawTx));
  const ty = Math.max(minTy, Math.min(0, rawTy));

  // Sonar pulse around active pin
  const pulsePhase = ((frame - activeWp.trigger_frame) % 36) / 36;
  const pulseRadius = interpolate(pulsePhase, [0, 1], [9, 36]);
  const pulseAlpha = interpolate(pulsePhase, [0, 1], [0.88, 0]);

  // Placement: panoramic split-bottom stage below photo, full-stage map, or corner HUD
  const effectiveMode = mode || (splitBottom ? 'split-bottom' : 'hud');
  const isWide = effectiveMode === 'split-bottom' || effectiveMode === 'full-stage';
  const placement = overlay.placement === 'top-right' ? 'top-right' : 'top-left';
  const cardWidth = isWide ? 984 : Math.min(520, vw);
  const svgRenderHeight = effectiveMode === 'full-stage' ? 980 : effectiveMode === 'split-bottom' ? 620 : Math.min(340, vh);
  const slotName = effectiveMode === 'split-bottom' ? 'STAGE_B' : effectiveMode === 'full-stage' ? 'FULL_STAGE' : 'HUD';
  const posStyle: React.CSSProperties =
    effectiveMode === 'full-stage'
      ? {left: 48, top: 200}
      : effectiveMode === 'split-bottom'
      ? {left: 48, top: 710}
      : placement === 'top-right'
      ? {right: 48, top: 290}
      : {left: 48, top: 290};

  const slideOffsetX = isWide ? 0 : placement === 'top-right' ? (1 - enterSpring) * 65 : -(1 - enterSpring) * 65;
  const slideOffsetY = isWide ? (1 - enterSpring) * 44 : (1 - enterSpring) * 24;

  const accentSolid = rgba(th.p.accent, 1);
  const accent2Solid = rgba(th.p.accent2, 1);
  const accentGlow = rgba(th.p.accent, 0.42);
  const surfaceBg = rgba(th.p.c1, 0.94);
  const surfaceBg2 = rgba(th.p.c2, 0.97);
  const arabicFont = `'Cairo', 'Noto Kufi Arabic', ${th.family2 || th.family}`;

  // Deduplicate waypoints by (x, y) when rendering pins so a country+capital pair doesn't stack two identical dots
  const uniquePinWaypoints: {wp: MapWaypoint; idx: number}[] = [];
  for (let i = 0; i <= activeIdx && i < waypoints.length; i++) {
    const candidate = waypoints[i];
    const existingIdx = uniquePinWaypoints.findIndex(
      (u) => Math.hypot(u.wp.x - candidate.x, u.wp.y - candidate.y) < 4
    );
    if (existingIdx >= 0) {
      // Prefer the capital/city metadata or the latest active index
      const prevEntry = uniquePinWaypoints[existingIdx];
      const mergedWp =
        prevEntry.wp.kind === 'capital' || prevEntry.wp.kind === 'city' ? prevEntry.wp : candidate;
      uniquePinWaypoints[existingIdx] = {wp: mergedWp, idx: i};
    } else {
      uniquePinWaypoints.push({wp: candidate, idx: i});
    }
  }

  return (
    <AbsoluteFill style={{pointerEvents: 'none', zIndex: 24}}>
      <div
        dir="rtl"
        lang="ar"
        data-slot={slotName}
        style={{
          position: 'absolute',
          ...posStyle,
          width: cardWidth,
          borderRadius: 24,
          overflow: 'hidden',
          background: `linear-gradient(155deg, ${surfaceBg} 0%, ${surfaceBg2} 100%)`,
          border: `2px solid ${rgba(th.st.palette.accent, 0.62)}`,
          boxShadow: `0 20px 48px rgba(0, 0, 0, 0.72), 0 0 28px ${accentGlow}`,
          backdropFilter: 'blur(14px)',
          opacity: visibility,
          transform: `translate3d(${slideOffsetX.toFixed(1)}px, ${slideOffsetY.toFixed(1)}px, 0) scale(${(0.92 + 0.08 * enterSpring).toFixed(3)})`,
          fontFamily: arabicFont,
        }}
      >
        {/* Top Cinematic Header Bar with Official Country Flag & Clear Arabic Title */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '11px 16px',
            background: 'rgba(4, 10, 24, 0.78)',
            borderBottom: `1.5px solid ${rgba(th.st.palette.accent, 0.32)}`,
            gap: 10,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 11, minWidth: 0}}>
            {iso2Lower && iso2Lower.length === 2 ? (
              <div
                style={{
                  width: 34,
                  height: 25,
                  borderRadius: 6,
                  overflow: 'hidden',
                  border: '1.5px solid rgba(255, 255, 255, 0.35)',
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.45)',
                  flexShrink: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: '#0f172a',
                }}
              >
                <SafeImg
                  data-flag-iso2={iso2Lower}
                  src={staticFile(`flags/4x3/${iso2Lower}.svg`)}
                  style={{width: '100%', height: '100%', objectFit: 'cover'}}
                />
              </div>
            ) : (
              <span
                style={{
                  width: 11,
                  height: 11,
                  borderRadius: '50%',
                  background: accentSolid,
                  boxShadow: `0 0 12px ${accentSolid}`,
                  display: 'inline-block',
                  flexShrink: 0,
                }}
              />
            )}
            <span
              style={{
                fontSize: 20,
                fontWeight: 900,
                color: '#ffffff',
                lineHeight: 1.25,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {headerTitle}
            </span>
          </div>
        </div>

        {/* Unobstructed Interactive Vector Map Viewport */}
        <div style={{position: 'relative', width: cardWidth, height: svgRenderHeight, overflow: 'hidden'}}>
          <svg width="100%" height={svgRenderHeight} viewBox={`0 0 ${vw} ${vh}`} preserveAspectRatio="xMidYMid slice" style={{display: 'block'}}>
            <defs>
              <radialGradient id="mapOverlayBg" cx="50%" cy="50%" r="70%">
                <stop offset="0%" stopColor={rgba(th.st.palette.c2, 0.95)} />
                <stop offset="100%" stopColor="#040914" />
              </radialGradient>
              <linearGradient id="mapOverlayPoly" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor={accentSolid} stopOpacity={0.46} />
                <stop offset="100%" stopColor={accent2Solid} stopOpacity={0.22} />
              </linearGradient>
              <filter id="mapOverlayGlow" x="-25%" y="-25%" width="150%" height="150%">
                <feGaussianBlur stdDeviation="3.5" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            <rect width={vw} height={vh} fill="url(#mapOverlayBg)" />

            {/* Subtle Topographic Graticule Grid */}
            <g opacity={0.14}>
              {[0.25, 0.5, 0.75].map((ry) => (
                <line key={`gy_${ry}`} x1={0} y1={vh * ry} x2={vw} y2={vh * ry} stroke={accentSolid} strokeWidth={1.2} strokeDasharray="6 8" />
              ))}
              {[0.2, 0.4, 0.6, 0.8].map((rx) => (
                <line key={`gx_${rx}`} x1={vw * rx} y1={0} x2={vw * rx} y2={vh} stroke={accentSolid} strokeWidth={1.2} strokeDasharray="6 8" />
              ))}
            </g>

            {/* Camera Transform Group */}
            <g transform={`translate(${tx.toFixed(1)}, ${ty.toFixed(1)}) scale(${camZoom.toFixed(3)})`}>
              {/* Neighboring Countries Context */}
              {ctx_path ? (
                <path
                  d={ctx_path}
                  fill="rgba(255, 255, 255, 0.045)"
                  stroke="rgba(255, 255, 255, 0.18)"
                  strokeWidth={1.1 / camZoom}
                />
              ) : null}

              {/* Highlighted Target Country Polygons (active country glows, others dim) */}
              {countries.map((c, ci) => {
                const isActiveCountry = !activeWp.iso3 || c.iso3 === activeWp.iso3;
                return c.d ? (
                  <path
                    key={`c_${c.iso3}_${ci}`}
                    d={c.d}
                    fill="url(#mapOverlayPoly)"
                    fillOpacity={isActiveCountry ? 1 : 0.35}
                    stroke={accentSolid}
                    strokeOpacity={isActiveCountry ? 1 : 0.45}
                    strokeWidth={(isActiveCountry ? 3.2 : 1.6) / camZoom}
                    filter={isActiveCountry ? 'url(#mapOverlayGlow)' : undefined}
                  />
                ) : null;
              })}

              {/* Animated Zigzag / Trajectory Arc Between Distinct Previous Location and Active Location */}
              {prevWp && Math.hypot(activeWp.x - prevWp.x, activeWp.y - prevWp.y) > 8 ? (() => {
                const dx = activeWp.x - prevWp.x;
                const dy = activeWp.y - prevWp.y;
                const len = Math.max(1, Math.hypot(dx, dy));
                const nx = -dy / len;
                const ny = dx / len;
                const zigAmp = Math.min(14, len * 0.14);
                const p1x = prevWp.x + dx * 0.25 + nx * zigAmp;
                const p1y = prevWp.y + dy * 0.25 + ny * zigAmp;
                const p2x = prevWp.x + dx * 0.50 - nx * zigAmp;
                const p2y = prevWp.y + dy * 0.50 - ny * zigAmp;
                const p3x = prevWp.x + dx * 0.75 + nx * zigAmp * 0.85;
                const p3y = prevWp.y + dy * 0.75 + ny * zigAmp * 0.85;
                const zigD = `M ${prevWp.x.toFixed(1)} ${prevWp.y.toFixed(1)} L ${p1x.toFixed(1)} ${p1y.toFixed(1)} L ${p2x.toFixed(1)} ${p2y.toFixed(1)} L ${p3x.toFixed(1)} ${p3y.toFixed(1)} L ${activeWp.x.toFixed(1)} ${activeWp.y.toFixed(1)}`;
                return (
                  <g>
                    <path
                      d={zigD}
                      fill="none"
                      stroke={accent2Solid}
                      strokeWidth={3.2 / camZoom}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      pathLength={1}
                      strokeDasharray="1"
                      strokeDashoffset={1 - camTransition}
                      opacity={0.95}
                      filter="url(#mapOverlayGlow)"
                    />
                    <circle
                      cx={prevWp.x}
                      cy={prevWp.y}
                      r={5.5 / camZoom}
                      fill="#e2e8f0"
                      stroke={accent2Solid}
                      strokeWidth={2 / camZoom}
                    />
                  </g>
                );
              })() : null}

              {/* Render Deduplicated Waypoints + Direct Pin Callout Label */}
              {uniquePinWaypoints.map(({wp, idx}) => {
                const isCurrent = idx === activeIdx || Math.hypot(wp.x - activeWp.x, wp.y - activeWp.y) < 4;
                const placeLabel = wp.name_ar;
                const badgeW = 136 / camZoom;
                const badgeH = 32 / camZoom;
                const placeAbove = wp.y > vh * 0.42;
                const rawBx = wp.x - badgeW / 2;
                const bx = Math.max(8 / camZoom, Math.min(vw - badgeW - 8 / camZoom, rawBx));
                const by = placeAbove ? wp.y - badgeH - 12 / camZoom : wp.y + 12 / camZoom;

                return (
                  <g key={wp.id}>
                    {isCurrent && (
                      <>
                        <circle
                          cx={wp.x}
                          cy={wp.y}
                          r={pulseRadius / camZoom}
                          fill="none"
                          stroke="#fde047"
                          strokeWidth={2.2 / camZoom}
                          opacity={pulseAlpha}
                        />
                        <circle
                          cx={wp.x}
                          cy={wp.y}
                          r={14 / camZoom}
                          fill="rgba(253, 224, 71, 0.25)"
                        />
                      </>
                    )}
                    <circle
                      cx={wp.x}
                      cy={wp.y}
                      r={(isCurrent ? 7.0 : 5.0) / camZoom}
                      fill={isCurrent ? '#fde047' : '#cbd5e1'}
                      stroke="#040914"
                      strokeWidth={2.2 / camZoom}
                    />
                    {isCurrent && (
                      <foreignObject x={bx} y={by} width={badgeW} height={badgeH}>
                        <div
                          dir="rtl"
                          lang="ar"
                          style={{
                            width: '100%',
                            height: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            background: 'rgba(4, 10, 24, 0.92)',
                            border: `1.5px solid ${accentSolid}`,
                            borderRadius: 999,
                            color: '#fde047',
                            fontSize: Math.round(15 / camZoom),
                            fontWeight: 900,
                            fontFamily: arabicFont,
                            boxShadow: '0 4px 12px rgba(0,0,0,0.65)',
                            whiteSpace: 'nowrap',
                            padding: '0 8px',
                          }}
                        >
                          {placeLabel}
                        </div>
                      </foreignObject>
                    )}
                  </g>
                );
              })}
            </g>
          </svg>
        </div>

        {/* Clean Bottom Footer Bar (Outside Map Viewport so Zero Polygon Obstruction) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 16px',
            background: 'rgba(4, 10, 24, 0.88)',
            borderTop: `1px solid ${rgba(th.st.palette.accent, 0.28)}`,
          }}
        >
          <span style={{fontSize: 16, fontWeight: 800, color: '#e2e8f0'}}>
            {pairedCityWp.kind === 'continent'
              ? `القارة: ${pairedCityWp.name_ar}`
              : pairedCityWp.country_ar
              ? `الدولة: ${pairedCityWp.country_ar}`
              : `الموقع: ${pairedCityWp.name_ar}`}
          </span>
          <span
            style={{
              fontSize: 15,
              fontWeight: 800,
              padding: '2px 10px',
              borderRadius: 999,
              background: rgba(th.st.palette.accent, 0.18),
              border: `1px solid ${rgba(th.st.palette.accent, 0.45)}`,
              color: '#fde047',
              direction: 'ltr',
            }}
          >
            {pairedCityWp.coords}
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
