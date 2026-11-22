import React from 'react';
import {AbsoluteFill, Easing, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {SafeImg} from './SafeImg';
import {rgba, useTheme} from './theme';
import {HUD_MAP_ZONE, MAP_LENS, MAP_STAGE_ZONE} from './layout';
import {MapViewport} from './mapEngine';

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

export type MapFeature = {
  id: string;
  shape: 'river' | 'lake' | 'area' | 'mountain' | string;
  label: string;
  kind_label: string;
  d: string;
  cx: number;
  cy: number;
  rx: number;
  ry: number;
  approx: boolean;
  trigger_frame: number;
};

export type MapOverlaySpec = {
  features?: MapFeature[];
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
      return `${w.kind_label || 'قارة'} ${w.name_ar}`;
    }
    if (w.kind === 'country') {
      return `دولة ${w.name_ar}`;
    }
    if (['ocean', 'globe', 'terrain', 'empire', 'region'].includes(w.kind)) {
      return w.name_ar;
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

  // Placement: panoramic split-bottom stage below photo, full-stage map, or corner HUD
  const effectiveMode = mode || (splitBottom ? 'split-bottom' : 'hud');
  const isWide = effectiveMode === 'split-bottom' || effectiveMode === 'full-stage';
  const cardWidth = isWide ? MAP_STAGE_ZONE.width : HUD_MAP_ZONE.width;
  const svgRenderHeight = effectiveMode === 'full-stage' ? MAP_STAGE_ZONE.full_svg_height : effectiveMode === 'split-bottom' ? MAP_STAGE_ZONE.split_svg_height : HUD_MAP_ZONE.svg_height;

  // tiny places: the main map stays at a readable regional zoom and a magnifier lens shows the close-up
  const useLens = activeWp.zoom * 100 >= MAP_LENS.min_zoom_pct;
  const mainZoom = useLens ? Math.min(camZoom, MAP_LENS.main_cap_pct / 100) : camZoom;
  const rawTx = cx0 - camX * mainZoom;
  const rawTy = cy0 - camY * mainZoom;
  const minTx = vw * (1 - mainZoom);
  const minTy = vh * (1 - mainZoom);
  const tx = Math.max(minTx, Math.min(0, rawTx));
  const ty = Math.max(minTy, Math.min(0, rawTy));
  // slice-fit crops the viewBox sides: keep the lens inside what is actually visible
  const fit = Math.max(cardWidth / vw, svgRenderHeight / vh);
  const visX0 = (vw - cardWidth / fit) / 2, visY0 = (vh - svgRenderHeight / fit) / 2;
  const lensC = {cx: visX0 + MAP_LENS.margin + MAP_LENS.r, cy: visY0 + MAP_LENS.margin + MAP_LENS.r};
  const lensCam = {tx: lensC.cx - camX * camZoom, ty: lensC.cy - camY * camZoom, z: camZoom};

  // Sonar pulse around active pin
  const pulsePhase = ((frame - activeWp.trigger_frame) % 36) / 36;
  const pulseRadius = interpolate(pulsePhase, [0, 1], [9, 36]);
  const pulseAlpha = interpolate(pulsePhase, [0, 1], [0.88, 0]);

  const slotName = effectiveMode === 'split-bottom' ? 'STAGE_B' : effectiveMode === 'full-stage' ? 'FULL_STAGE' : 'HUD';
  const posStyle: React.CSSProperties =
    effectiveMode === 'full-stage'
      ? {left: 48, top: MAP_STAGE_ZONE.full_top}
      : effectiveMode === 'split-bottom'
      ? {left: 48, top: MAP_STAGE_ZONE.split_top}
      : {left: HUD_MAP_ZONE.left, top: HUD_MAP_ZONE.top}; // bottom band above CAPTION_ZONE: never covers scene content

  const slideOffsetX = 0;
  const slideOffsetY = (1 - enterSpring) * 44;

  const accentSolid = rgba(th.p.accent, 1);
  const accent2Solid = rgba(th.p.accent2, 1);
  const accentGlow = rgba(th.p.accent, 0.42);
  const surfaceBg = rgba(th.p.c1, 0.94);
  const surfaceBg2 = rgba(th.p.c2, 0.97);
  const arabicFont = `'Cairo', 'Noto Kufi Arabic', ${th.family2 || th.family}`;

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
          <MapViewport
            frame={frame} fps={fps} vw={vw} vh={vh} height={svgRenderHeight}
            ctxPath={ctx_path} countries={countries} waypoints={waypoints} activeIdx={activeIdx}
            prevWp={prevWp} camTransition={camTransition} features={overlay.features || []}
            main={{tx, ty, z: mainZoom}} lens={useLens ? lensCam : null} lensC={lensC}
            colors={{accent: accentSolid, accent2: accent2Solid, text: '#e2e8f0', ctxFill: rgba(th.p.text, 0.09), ctxStroke: rgba(th.p.text, 0.34), sea0: rgba(th.st.palette.c2, 0.95), sea1: th.dark ? '#040914' : rgba(th.st.palette.c2, 1)}}
            font={arabicFont} uid="mp"
          />
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
              ? (pairedCityWp.kind_label === 'منطقة' ? `المنطقة: ${pairedCityWp.name_ar}` : `القارة: ${pairedCityWp.name_ar}`)
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
