// Split from generativeCanvas.tsx (re-exported there).
import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {useTheme, rgba} from './theme';
import {BEAT_ZONE, CANVAS_FIT_BOX} from './layout';
import {useFont} from './hooks';
import {DYNAMIC_SCENE_REGISTRY} from './generated/DynamicScenes';
import {CanvasMoodBackground, CustomSvgIllustrationLayer, GenerativeElementView} from './generativeCanvas';
import type {GenerativeCanvasSpec} from './generativeCanvas';

// ------------------------------------------------------------------ Generative Canvas Beat Main
// Templates place small fixed-size primitives around the canvas centre, leaving most of the 9:16 frame dark.
// Measure the content bbox (rough per-type size estimates) and scale it up to fill the beat zone.
export const FIT_BOX = {w: CANVAS_FIT_BOX.w, h: CANVAS_FIT_BOX.h, cx: CANVAS_FIT_BOX.cx, cy: CANVAS_FIT_BOX.cy, max: CANVAS_FIT_BOX.max_pct / 100};

export const computeFit = (els: any[]): {k: number; cx: number; cy: number} => {
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const el of els) {
    const rx = Number(el.x ?? 540), ry = Number(el.y ?? 960);
    if (!Number.isFinite(rx) || !Number.isFinite(ry)) continue;
    const x = Math.max(200, Math.min(880, rx)), y = Math.max(360, Math.min(1550, ry));
    let w = 0, h = 0;
    switch (el.type) {
      case 'badge': { const fs = el.size === 'lg' ? 30 : el.size === 'sm' ? 22 : 26; w = String(el.text || '').length * fs * 0.6 + 110; h = fs * (el.sub ? 3.2 : 2.4); break; }
      case 'icon': case 'emoji': w = h = el.size ?? 120; break;
      case 'flag': w = el.size ?? 130; h = w * 0.75; break;
      case 'lottie': w = h = el.size ?? 220; break;
      case 'counter': { const fs = el.fontSize ?? 64; const dg = String(el.to ?? '').length; w = (dg + Math.floor((dg - 1) / 3)) * fs * 0.62 + 160; h = fs * 2.2; break; }
      case 'gauge': w = el.kind === 'ring' ? 160 : (el.width ?? 400); h = el.kind === 'ring' ? 160 : 80; break;
      case 'text': { const fs = el.size ?? 38; w = Math.min(el.maxWidth ?? 800, String(el.text || '').length * fs * 0.55); h = fs * 1.5; break; }
      default: continue; // shapes/paths/connectors are decor: they scale with the group but don't size it
    }
    x0 = Math.min(x0, x - w / 2); x1 = Math.max(x1, x + w / 2);
    y0 = Math.min(y0, y - h / 2); y1 = Math.max(y1, y + h / 2);
  }
  if (!Number.isFinite(x0)) return {k: 1, cx: FIT_BOX.cx, cy: FIT_BOX.cy};
  const k = Math.max(1, Math.min(FIT_BOX.max, FIT_BOX.w / Math.max(1, x1 - x0), FIT_BOX.h / Math.max(1, y1 - y0)));
  return {k, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2};
};

export const GenerativeCanvasBeat: React.FC<{ beat: any }> = ({ beat }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const th = useTheme();
  const font = useFont();

  const defaultAccent = th?.p?.accent ? rgba(th.p.accent) : '#f59e0b';
  const defaultSec = th?.p?.accent2 ? rgba(th.p.accent2) : '#38bdf8';

  const sceneSpec = (beat.scene_spec && typeof beat.scene_spec === 'object') ? beat.scene_spec : {};
  const cinematicMode = sceneSpec.cinematic || (beat.kind === 'custom_scene' ? '' : '');
  const cinematicLighting = sceneSpec.lighting || '';

  const spec: GenerativeCanvasSpec = {
    title: beat.title || '',
    subtitle: beat.subtitle || '',
    background: beat.background,
    accent: beat.accent || defaultAccent,
    grid: beat.grid ?? 'dots',
    elements: beat.elements || [],
  };

  const fit = React.useMemo(() => computeFit(spec.elements as any[]), [spec.elements]);
  const accentColor = spec.accent || defaultAccent;
  const secondaryAccent = beat.secondary_accent || defaultSec;
  const cinematicIntensity = cinematicMode ? 1 : 0;
  const DynamicTsxComp = beat.tsx_id ? DYNAMIC_SCENE_REGISTRY[beat.tsx_id] : undefined;

  return (
    <AbsoluteFill
      style={{
        background:
          spec.background ||
          `radial-gradient(circle at 50% 38%, #132347 0%, #0b1938 55%, #050b1a 100%)`,
        overflow: 'hidden',
      }}
    >
      <CanvasMoodBackground
        mode={spec.grid}
        environment={beat.environment}
        accent={accentColor}
        secondaryAccent={secondaryAccent}
        frame={frame}
        fps={fps}
      />

      {/* Custom SVG Vector Illustrations from Scene Specification (Section C) */}
      <CustomSvgIllustrationLayer
        layers={beat.svg_layers}
        frame={frame}
        fps={fps}
        accent={accentColor}
        secondaryAccent={secondaryAccent}
      />

      {/* Executable React/TSX Component generated specifically for this segment */}
      {DynamicTsxComp ? (
        <DynamicTsxComp frame={frame} fps={fps} dur={beat.dur || 90} />
      ) : null}

      {/* Header title if specified */}
      {spec.title && (
        <div
          dir="rtl"
          style={{
            position: 'absolute',
            top: BEAT_ZONE.title_top,
            left: '50%',
            transform: 'translateX(-50%)',
            textAlign: 'center',
            zIndex: 30,
            width: 920,
          }}
        >
          <div
            style={{
              ...font,
              fontSize: 52,
              fontWeight: 800,
              color: '#ffffff',
              textShadow: `0 4px 24px rgba(0,0,0,0.85), 0 0 28px ${accentColor}55`,
              lineHeight: 1.25,
            }}
          >
            {spec.title}
          </div>
          {spec.subtitle && (
            <div
              style={{
                fontSize: 27,
                color: accentColor,
                fontWeight: 700,
                marginTop: 8,
                textShadow: '0 2px 12px rgba(0,0,0,0.8)',
              }}
            >
              {spec.subtitle}
            </div>
          )}
        </div>
      )}

      {/* Render all generative elements */}
      <div style={{position: 'absolute', inset: 0, transformOrigin: `${fit.cx}px ${fit.cy}px`, transform: `translate(${FIT_BOX.cx - fit.cx}px, ${FIT_BOX.cy - fit.cy}px) scale(${fit.k.toFixed(3)})`}}>
      {spec.elements.map((el, idx) => (
        <GenerativeElementView
          key={el.id || `gen_el_${idx}`}
          el={el}
          frame={frame}
          fps={fps}
          accent={accentColor}
          settled={Boolean(beat.settled)}
        />
      ))}
      </div>

      {/* Cinematic lighting + vignette + grain layer driven from scene_spec.cinematic / lighting */}
      {cinematicIntensity > 0 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            pointerEvents: 'none',
            background:
              cinematicLighting === 'dramatic'
                ? 'radial-gradient(ellipse 80% 60% at 50% 42%, rgba(244,63,94,0.34) 0%, rgba(0,0,0,0.55) 70%)'
                : cinematicLighting === 'deep-space'
                ? 'radial-gradient(ellipse 80% 60% at 50% 42%, rgba(56,189,248,0.22) 0%, rgba(8,12,30,0.7) 78%)'
                : cinematicLighting === 'radial-core'
                ? 'radial-gradient(ellipse 90% 70% at 50% 38%, rgba(251,191,36,0.32) 0%, rgba(12,8,30,0.68) 90%)'
                : cinematicLighting === 'cool-flow'
                ? 'radial-gradient(ellipse 80% 60% at 50% 42%, rgba(56,189,248,0.26) 0%, rgba(6,20,38,0.66) 80%)'
                : cinematicLighting === 'earth-tones'
                ? 'radial-gradient(ellipse 80% 60% at 50% 42%, rgba(180,120,60,0.28) 0%, rgba(20,14,8,0.72) 82%)'
                : cinematicLighting === 'soft-top'
                ? 'radial-gradient(ellipse 90% 50% at 50% 18%, rgba(233,244,255,0.28) 0%, rgba(8,12,22,0.66) 82%)'
                : 'radial-gradient(ellipse 80% 60% at 50% 38%, rgba(212,175,55,0.26) 0%, rgba(6,8,18,0.7) 82%)',
            boxShadow: 'inset 0 0 140px rgba(0,0,0,0.72)',
            mixBlendMode: 'multiply',
            opacity: 0.9 + 0.1 * Math.sin(frame / 3),
          }}
        />
      )}

    </AbsoluteFill>
  );
};
