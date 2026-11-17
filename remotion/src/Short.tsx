import React, { useEffect, useMemo, useState } from 'react';
import { AbsoluteFill, Easing, Sequence, continueRender, delayRender, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { Audio } from '@remotion/media';
import { loadFont } from '@remotion/fonts';
import { BeatView } from './beats';
import { Background, Deco, Finish, SceneWipe } from './layers';
import { Captions } from './text';
import { FONT_FILES, MapLayoutCtx, MotionCtx, ThemeCtx, makeTheme, rgba, useTheme } from './theme';
import { NoiseShapesLayer, SceneTransitionEffect, pickSceneTransitions } from './transitions';
import { SceneVisualsLayer } from './visualLayer';
import { MapOverlayLayer } from './mapOverlay';
import { SoundDesignLayer } from './sfx';
import { CANVAS_HEIGHT, CANVAS_WIDTH, SAFE_TOP, SAFE_BOTTOM, HEADLINE_ZONE, BEAT_ZONE, CAPTION_ZONE } from './layout';
import { SceneSpec, Spec } from './types';

const Scene: React.FC<{ scene: SceneSpec; index: number; fallbackTransition?: any }> = ({
  scene,
  index,
  fallbackTransition,
}) => {
  const th = useTheme();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const speed = th.pace * (scene.role === 'hook' ? 2.2 : 1);
  const activeBeat = useMemo(() => {
    let cur = scene.beats[0];
    for (const b of scene.beats) {
      if (b.from <= frame) cur = b;
    }
    return cur;
  }, [frame, scene.beats]);
  const activeBeatKind = activeBeat?.kind ?? '';
  const suppressCaptions = activeBeatKind === 'bigtext';
  const hasCustomTsx = Boolean(activeBeat?.tsx_id);
  const isLegacyFullMap = !hasCustomTsx && (activeBeatKind === 'map' || activeBeatKind === 'map_pin');
  const transition = scene.transition ?? fallbackTransition;
  const dur = Math.max(1, scene.dur);

  // حركة كاميرا سينمائية متنوعة لكل مشهد (دفع، سحب، انزياح أفقي/عمودي سلس)
  const camMode = index % 4;
  const camProgress = interpolate(frame, [0, dur], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.sin),
  });
  const baseScale =
    camMode === 0
      ? interpolate(camProgress, [0, 1], [1.0, 1.055])
      : camMode === 1
        ? interpolate(camProgress, [0, 1], [1.05, 1.005])
        : camMode === 2
          ? interpolate(camProgress, [0, 1], [1.01, 1.045])
          : interpolate(camProgress, [0, 1], [1.02, 1.05]);
  const panX =
    camMode === 2
      ? interpolate(camProgress, [0, 1], [-12, 12])
      : camMode === 3
        ? interpolate(camProgress, [0, 1], [10, -10])
        : 0;
  const panY =
    camMode === 1
      ? interpolate(camProgress, [0, 1], [8, -8])
      : camMode === 3
        ? interpolate(camProgress, [0, 1], [-8, 10])
        : 0;

  // دخول وخروج سينمائي ناعم عند حدود المشاهد (بدل القطع الحاد)
  const enterSpr = index === 0 ? 1 : spring({ frame, fps, config: { damping: 16, stiffness: 180, mass: 0.7 } });
  const enterScale = index === 0 ? 1 : interpolate(enterSpr, [0, 1], [1.06, 1.0]);
  const enterY = index === 0 ? 0 : interpolate(enterSpr, [0, 1], [index % 2 === 0 ? 28 : -24, 0]);
  const enterOp = index === 0 ? 1 : interpolate(frame, [0, 7], [0.25, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const exitOp = dur > 10 ? interpolate(frame, [dur - 6, dur], [1, 0.72], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) : 1;
  const camScale = baseScale * enterScale;
  const sceneOpacity = Math.min(enterOp, exitOp);

  const hasMapOverlay = Boolean(scene.map_overlay);
  const isMapFocusedMode = scene.visual_mode === 'map_zoom' || scene.visual_mode === 'battle_map';
  const mapMode: 'hud' | 'split-bottom' | 'full-stage' = (isLegacyFullMap || (!hasCustomTsx && isMapFocusedMode && activeBeatKind !== 'photo'))
    ? 'full-stage'
    : !hasCustomTsx
      ? 'split-bottom'
      : 'hud';
  const hasSplitMap = hasMapOverlay && mapMode === 'split-bottom';

  return (
    <AbsoluteFill style={{ opacity: sceneOpacity }}>
      <MapLayoutCtx.Provider value={{ splitBottom: hasSplitMap }}>
        <AbsoluteFill
          style={{
            transform: `translate3d(${panX.toFixed(1)}px, ${(panY + enterY).toFixed(1)}px, 0) scale(${camScale.toFixed(4)})`,
            transformOrigin: '50% 45%',
          }}
        >
          {!hasCustomTsx && <NoiseShapesLayer seed={th.st.seed + index} />}
          {!(isLegacyFullMap && hasMapOverlay) && scene.beats.map((b, i) => (
            <Sequence key={i} from={b.from} durationInFrames={b.dur} layout="none" name={`${scene.id}:${b.kind}`}>
              <MotionCtx.Provider value={{ speed, settled: !!b.settled }}>
                <BeatView beat={b} />
              </MotionCtx.Provider>
            </Sequence>
          ))}
          {!hasCustomTsx && (
            <SceneVisualsLayer
              visuals={hasMapOverlay ? (scene.visuals || []).filter((v) => v.kind !== 'flag') : scene.visuals}
            />
          )}
        </AbsoluteFill>
      </MapLayoutCtx.Provider>
      {hasMapOverlay && <MapOverlayLayer overlay={scene.map_overlay} mode={mapMode} />}
      {!suppressCaptions && <Captions words={scene.words} />}
      <SceneWipe index={index} />
      <SceneTransitionEffect transition={transition} index={index} />
    </AbsoluteFill>
  );
};

export const Short: React.FC<{ spec?: Spec } & Partial<Spec>> = (props) => {
  const spec = (props.spec ?? (props as unknown as Spec))!;
  const theme = useMemo(() => makeTheme(spec.style), [spec.style]);
  const transitions = useMemo(
    () => pickSceneTransitions(spec.scenes.length, spec.style.seed),
    [spec.scenes.length, spec.style.seed]
  );
  const anyCustomTsx = useMemo(
    () => spec.scenes.some((sc) => sc.beats.some((b) => Boolean(b.tsx_id))),
    [spec.scenes]
  );
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    const f = (family: string, key: string) =>
      loadFont({
        family,
        url: staticFile(`fonts/${FONT_FILES[key] ?? 'NotoKufi.ttf'}`),
        weight: '100 900',
      });
    Promise.all([f(theme.family, spec.style.font), f(theme.family2, spec.style.font2)])
      .then(() => continueRender(handle))
      .catch((e) => {
        console.error(e);
        continueRender(handle);
      });
  }, [handle, theme.family, theme.family2, spec.style.font, spec.style.font2]);
  return (
    <ThemeCtx.Provider value={theme}>
      <AbsoluteFill style={{ direction: 'rtl', width: CANVAS_WIDTH, height: CANVAS_HEIGHT, background: '#050b16' }} data-safe-top={SAFE_TOP} data-safe-bottom={SAFE_BOTTOM} data-headline-top={HEADLINE_ZONE.top} data-beat-top={BEAT_ZONE.top} data-caption-top={CAPTION_ZONE.top}>
        <Background spec={spec} />
        {spec.scenes.map((sc, i) => (
          <Sequence key={sc.id} from={sc.from} durationInFrames={sc.dur} name={sc.id}>
            <Scene scene={sc} index={i} fallbackTransition={transitions[i]} />
          </Sequence>
        ))}
        {!anyCustomTsx && <Deco total={spec.total} />}
        <TopProgressBar total={spec.total} />
        <Finish />
        {spec.audio ? <Audio src={staticFile(spec.audio)} volume={0.78} /> : null}
        {spec.audio ? <SoundDesignLayer spec={spec} /> : null}
      </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};

const TopProgressBar: React.FC<{ total: number }> = ({ total }) => {
  const frame = useCurrentFrame();
  const th = useTheme();
  const pct = Math.min(100, Math.max(0, (frame / Math.max(1, total)) * 100));
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, insetBlockStart: 0, height: 8, background: 'rgba(255,255,255,0.08)', zIndex: 40, pointerEvents: 'none' }}>
      <div style={{ height: '100%', width: `${pct.toFixed(2)}%`, background: `linear-gradient(90deg, ${rgba(th.p.accent)}, ${rgba(th.p.accent2)})` }} />
    </div>
  );
};
