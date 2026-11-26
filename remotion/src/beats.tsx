import React, {useContext, useId} from 'react';

import {AbsoluteFill, Audio, Easing, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {SafeImg} from './SafeImg';
import {ArrowFlow, CaptionScrim, FireSparks, FloatBadge, GlowText, MapOverlay, Particles} from './fx';
import {CameraRig, ParallaxLayer, SvgZoomIn, useCameraShake} from './camera';
import {AnimatedMetric} from './metrics';

import {Icon} from './icons';
import {Flag} from './flag';
import {SceneVisualsLayer} from './visualLayer';
import {SlotContainer} from './layoutEngine';
import {ChartVisual} from './charts';
import {TypographyVisual} from './typography';
import {
  AnimatedRouteBeat,
  BalanceMeterBeat,
  DeepTimeSliderBeat,
  DotMatrixPopulationBeat,
  FrontlineClashBeat,
  MacroZoomGlobeBeat,
  MoneyWaterfallBeat,
  StackPyramidBeat,
  SubsurfaceMineBeat,
  VersusBattleBeat,
} from './visualStoryBeats';
import {GenerativeCanvasBeat} from './generativeCanvas';
import {AreaMapBeat} from './areaMap';
import {DYNAMIC_SCENE_REGISTRY} from './generated/DynamicScenes';

import {clamp01, enterStyle, EnterKind, Pop, useFont, useIdle, useProgress, useSpring} from './hooks';

import {Headline} from './text';

import {AccentShapes, PhotoBeat, isAlt, useFont2} from './photo';
import {CitySceneBeat, ArchitectureBeat, MysterySceneBeat} from './sceneBeats';
import {YearCounterBeat, PersonCardBeat} from './entityBeats';
import {AuthoredBeat} from './authoredBeat';

import {MapLayoutCtx, MotionCtx, on, rgba, useTheme} from './theme';
import {BEAT_ZONE, CAPTION_ZONE, HEADLINE_ZONE, SAFE_BOTTOM, SAFE_TOP, SCENE_FIT} from './layout';
import {Beat, RGB} from './types';
import {LineChartBeat, PieChartBeat} from './beatsChartsB';
import {ElevationProfileBeat, StatRingV2Beat} from './beatsChartsA';
import {MapPinBeat, TimelineCardBeat} from './beatsMapPin';
import {CanvasBeat, CardStackBeat, SplitBeat, TickerBeat} from './beatsCanvas';
import {BarsBeat, IconsBeat, ListBeat, TimelineBeat, VersusBeat} from './beatsBasic';
import {BigTextBeat, StatBeat} from './beatsStat';
import {MapBeat} from './beatsMap';
export {HlCountry} from './beatsMap';
export {parseNum} from './beatsStat';
export {ElevationProfileBeat} from './beatsChartsA';



export const shade = (c: RGB, k: number): string => `rgb(${c.map((v) => Math.max(0, Math.min(255, Math.round(v * k)))).join(',')})`;

/** Read a cue frame from beat.cues by type (returns seconds). */
export const cueSecOf = (beat: Beat, type: string, fallback = 0): number => {
  const fps = 30;
  const cue = (beat.cues as Array<{frame: number; type: string}> | undefined)?.find(c => c.type === type);
  return cue ? cue.frame / fps : fallback;
};



// ------------------------------------------------------------------ غلاف المقطع: خروج + كاميرا (push-in/pan/parallax/fly-to/static مع micro-drift)

export const BeatShell: React.FC<{beat: Beat; children: React.ReactNode}> = ({beat, children}) => {

  const frame = useCurrentFrame();

  const {fps} = useVideoConfig();

  const th = useTheme();

  const ex = beat.settled ? 0 : Math.round(0.26 * fps);

  const exit = ex

    ? interpolate(frame, [beat.dur - ex, beat.dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: th.ease.in})

    : 0;

  const prog = beat.dur > 1 ? frame / (beat.dur - 1) : 0;

  const cam = beat.camera as string | undefined;

  // impact shake — triggered at metric_punch cue (frame -99 = no-op when no cue)
  const punchF = (beat.cues as Array<{frame: number; type: string}> | undefined)
    ?.find(c => c.type === 'metric_punch')?.frame ?? -99;
  const sh = useCameraShake(punchF, 12, 0.85);

  // حركة الكاميرا الديناميكية السينمائية

  let camScale = 1;

  let camX = sh.x;   // shake is always baked in

  let camY = sh.y;

  let camRot = sh.rot;



  if (cam === 'zoom-in' || cam === 'push-in') {

    camScale = 1 + 0.12 * prog;

  } else if (cam === 'zoom-out') {

    camScale = 1.14 - 0.14 * prog;

  } else if (cam === 'pan-left' || cam === 'pan') {

    camX += -60 * prog;

  } else if (cam === 'pan-right') {

    camX += 60 * prog;

  } else if (cam === 'tilt-up') {

    camY += 40 - 70 * prog;

  } else if (cam === 'tilt-down') {

    camY += -30 + 70 * prog;

  } else if (cam === 'parallax') {

    // Ken Burns full strength — matches CameraRig("ken-burns") values
    camScale = 1 + 0.08 * prog;

    camX += -20 + 40 * prog;

  } else if (cam === 'handheld') {

    camScale = 1.03 + 0.02 * Math.sin((frame / fps) * 2.5);

    camX += Math.sin((frame / fps) * 1.8) * 12;

    camY += Math.cos((frame / fps) * 2.1) * 9;

    camRot += Math.sin((frame / fps) * 1.5) * 0.8;

  }



  // إجراء ثانٍ إلزامي لأي مقطع أطول من 2.5 ثانية (> 75 إطاراً): تقريب إضافي للكاميرا وتوهج ديناميكي

  const isLong = beat.dur > Math.round(2.5 * fps) && !beat.settled;

  const secondActionStart = Math.round(2.0 * fps);

  const secondProg = isLong

    ? interpolate(frame, [secondActionStart, beat.dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: th.ease.inOut})

    : 0;

  const secondPushScale = 1 + 0.075 * secondProg;

  const totalScale = camScale * secondPushScale;



  // micro-drift on static so no frame is truly frozen (4px sine bob)

  const drift = (!cam || cam === 'static') && !beat.settled ? Math.sin(frame / fps * 1.4) * 4 : 0;



  return (

    <AbsoluteFill>

      <AbsoluteFill style={{

        opacity: 1 - exit,

        translate: `${camX + drift * 0.25}px ${camY + -36 * exit + drift}px`,

        scale: String((1 - 0.035 * exit) * totalScale),

        rotate: camRot ? `${camRot}deg` : undefined

      }}>

        {children}

      </AbsoluteFill>

      {/* إشارة بصرية حركية كإجراء ثانٍ عند المقطع الطويل */}

      {!beat.tsx_id && isLong && frame >= secondActionStart ? (

        <div style={{

          position: 'absolute', inset: 0, pointerEvents: 'none',

          boxShadow: `inset 0 0 ${Math.round(90 * secondProg)}px ${rgba(th.p.accent, 0.28 * (1 - secondProg))}`,

          opacity: clamp01(secondProg * 2)

        }}>

          <div style={{

            position: 'absolute', left: 540 - 220 * secondProg, width: 440 * secondProg,

            top: th.zoneCy + 440, height: 6, borderRadius: 3,

            background: `linear-gradient(90deg, transparent, ${rgba(th.p.accent)}, transparent)`,

            opacity: 1 - secondProg * 0.4

          }} />

        </div>

      ) : null}

      {!beat.tsx_id && beat.title && ![
        'icon_scene', 'map_pin', 'timeline_card', 'bigtext', 'custom_scene',
        'generative_canvas', 'versus_battle', 'balance_meter', 'stack_pyramid',
        'deep_time_slider', 'macro_zoom_globe', 'subsurface_mine', 'dot_matrix_population',
        'money_waterfall', 'frontline_clash', 'animated_route', 'bars', 'line_chart', 'pie_chart',
        'city_skyline', 'architecture', 'year_counter', 'person_card', 'authored' // these draw their own title: a second headline would stack on it
      ].includes(beat.kind) ? <div style={{opacity: 1 - exit}}><Headline text={beat.title} /></div> : null}

    </AbsoluteFill>

  );

};

// One broken LLM scene (runtime throw) must not abort the whole render: show nothing for that beat instead.
class SceneBoundary extends React.Component<{children: React.ReactNode}, {failed: boolean}> {
  state = {failed: false};
  static getDerivedStateFromError() { return {failed: true}; }
  componentDidCatch(e: unknown) { console.warn('[scene-boundary] dynamic scene failed:', e); }
  render() { return this.state.failed ? null : this.props.children; }
}

const TSX_SCENE_CSS = '.tsx-scene > div { background: none !important; } .tsx-scene svg rect[width="1080"][height="1920"] { display: none; }';

export const BeatView: React.FC<{beat: Beat}> = ({beat}) => {
  const {hudMap} = useContext(MapLayoutCtx);
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // If this beat has its own AI-generated bespoke TSX component, render it inside a clipped slot above captions
  const DynamicComp = beat.tsx_id ? DYNAMIC_SCENE_REGISTRY[beat.tsx_id] : undefined;
  if (DynamicComp) {
    // LLM scenes are top-heavy (content ends ~y=1050..1190). With a HUD map, compress them above the map band;
    // without one, shift down and enlarge slightly so the beat zone is used.
    return (
      <SlotContainer slot="FULL_STAGE" fullCanvas clip>
        {/* LLM scenes paint their own opaque dark background. Make the scene transparent so the video's ground
            (paper / kraft / solid / ink ...) shows through: scene root background off, full-canvas glow rects hidden. */}
        <style>{TSX_SCENE_CSS}</style>
        <div className="tsx-scene" style={{position: 'absolute', inset: 0, transformOrigin: `50% ${SCENE_FIT.origin_y_pct}%`, transform: hudMap ? `scale(${SCENE_FIT.compress_pct / 100})` : `translateY(${SCENE_FIT.plain_shift_px}px) scale(${SCENE_FIT.plain_scale_pct / 100})`}}>
          <SceneBoundary><DynamicComp frame={frame} fps={fps} dur={beat.dur || 90} /></SceneBoundary>
        </div>
      </SlotContainer>
    );
  }

  let body: React.ReactNode;

  switch (beat.kind) {
    case 'area_map': body = <AreaMapBeat beat={beat} />; break;
    case 'map_pin': body = <MapPinBeat beat={beat} />; break;
    case 'timeline_card': body = <TimelineCardBeat beat={beat} />; break;
    case 'stat_ring_v2': body = <StatRingV2Beat beat={beat} />; break;
    case 'elevation_profile': body = <ElevationProfileBeat beat={beat} />; break;
    case 'versus_battle': body = <VersusBattleBeat beat={beat} />; break;
    case 'animated_route': body = <AnimatedRouteBeat beat={beat} />; break;
    case 'balance_meter': body = <BalanceMeterBeat beat={beat} />; break;
    case 'deep_time_slider': body = <DeepTimeSliderBeat beat={beat} />; break;
    case 'stack_pyramid': body = <StackPyramidBeat beat={beat} />; break;
    case 'macro_zoom_globe': body = <MacroZoomGlobeBeat beat={beat} />; break;
    case 'subsurface_mine': body = <SubsurfaceMineBeat beat={beat} />; break;
    case 'dot_matrix_population': body = <DotMatrixPopulationBeat beat={beat} />; break;
    case 'money_waterfall': body = <MoneyWaterfallBeat beat={beat} />; break;
    case 'frontline_clash': body = <FrontlineClashBeat beat={beat} />; break;
    case 'generative_canvas': body = <GenerativeCanvasBeat beat={beat} />; break;
    case 'custom_scene': body = <GenerativeCanvasBeat beat={beat} />; break;
    case 'cinematic_dramatic':
    case 'architectural_blueprint':
    case 'celestial_constellation':
    case 'kinetic_wave_field':
    case 'radial_light_cathedral':
    case 'topographic_contour':
      body = <GenerativeCanvasBeat beat={beat} />; break;
    case 'chart': body = beat.spec ? <AbsoluteFill style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}><ChartVisual spec={beat.spec} /></AbsoluteFill> : <BarsBeat beat={beat} />; break;
    case 'typography': body = beat.spec ? <AbsoluteFill style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}><TypographyVisual spec={beat.spec} /></AbsoluteFill> : <BigTextBeat beat={beat} />; break;
    case 'visuals': body = <SceneVisualsLayer visuals={beat.visuals} />; break;
    case 'line_chart': body = <LineChartBeat beat={beat} />; break;
    case 'pie_chart': body = <PieChartBeat beat={beat} />; break;

    case 'map': body = <MapBeat beat={beat} />; break;

    case 'stat': body = <StatBeat beat={beat} />; break;

    case 'bars': body = <BarsBeat beat={beat} />; break;

    case 'timeline': body = <TimelineBeat beat={beat} />; break;

    case 'versus': body = <VersusBeat beat={beat} />; break;

    case 'list': body = <ListBeat beat={beat} />; break;

    case 'icons': body = <IconsBeat beat={beat} />; break;

    case 'canvas': body = <CanvasBeat beat={beat} />; break;

    case 'photo': body = <PhotoBeat beat={beat} />; break;

    case 'city_skyline': body = <CitySceneBeat beat={beat} />; break;

    case 'architecture': body = <ArchitectureBeat beat={beat} />; break;

    case 'mystery_scene': body = <MysterySceneBeat beat={beat} />; break;
    case 'authored': body = <AuthoredBeat beat={beat} />; break;
    case 'year_counter': body = <YearCounterBeat beat={beat} />; break;
    case 'person_card': body = <PersonCardBeat beat={beat} />; break;

    case 'split': body = <SplitBeat beat={beat} />; break;

    case 'ticker': body = <TickerBeat beat={beat} />; break;

    case 'cardstack': body = <CardStackBeat beat={beat} />; break;

    default: body = <BigTextBeat beat={beat} />;

  }

  return (
    <BeatShell beat={beat}>
      {body}
      {beat.kind !== 'visuals' && beat.visuals && beat.visuals.length > 0 ? (
        <SceneVisualsLayer visuals={beat.visuals} />
      ) : null}
    </BeatShell>
  );

};

