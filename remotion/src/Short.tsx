import React, {useEffect, useMemo, useState} from 'react';
import {AbsoluteFill, Sequence, continueRender, delayRender, staticFile, useCurrentFrame} from 'remotion';
import {Audio} from '@remotion/media';
import {loadFont} from '@remotion/fonts';
import {BeatView} from './beats';
import {Background, Deco, Finish, SceneWipe} from './layers';
import {Captions} from './text';
import {FONT_FILES, MotionCtx, ThemeCtx, makeTheme, useTheme} from './theme';
import {SceneSpec, Spec} from './types';

const Scene: React.FC<{scene: SceneSpec; index: number}> = ({scene, index}) => {
  const th = useTheme();
  const frame = useCurrentFrame();
  const speed = th.pace * (scene.role === 'hook' ? 2.2 : 1);
  const activeBeatKind = useMemo(() => {
    let kind = scene.beats[0]?.kind ?? '';
    for (const b of scene.beats) { if (b.from <= frame) kind = b.kind; }
    return kind;
  }, [frame, scene.beats]);
  const suppressCaptions = activeBeatKind === 'bigtext';
  return (
    <AbsoluteFill>
      {scene.beats.map((b, i) => (
        <Sequence key={i} from={b.from} durationInFrames={b.dur} layout="none" name={`${scene.id}:${b.kind}`}>
          <MotionCtx.Provider value={{speed, settled: !!b.settled}}>
            <BeatView beat={b} />
          </MotionCtx.Provider>
        </Sequence>
      ))}
      {!suppressCaptions && <Captions words={scene.words} />}
      <SceneWipe index={index} />
    </AbsoluteFill>
  );
};

export const Short: React.FC<{spec: Spec}> = ({spec}) => {
  const theme = useMemo(() => makeTheme(spec.style), [spec.style]);
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    const f = (family: string, key: string) => loadFont({family, url: staticFile(`fonts/${FONT_FILES[key] ?? 'NotoKufi.ttf'}`), weight: '100 900'});
    Promise.all([f(theme.family, spec.style.font), f(theme.family2, spec.style.font2)])
      .then(() => continueRender(handle))
      .catch((e) => { console.error(e); continueRender(handle); });
  }, [handle, theme.family, theme.family2, spec.style.font, spec.style.font2]);
  return (
    <ThemeCtx.Provider value={theme}>
      <AbsoluteFill style={{direction: 'rtl'}}>
        <Background spec={spec} />
        {spec.scenes.map((sc, i) => (
          <Sequence key={sc.id} from={sc.from} durationInFrames={sc.dur} name={sc.id}>
            <Scene scene={sc} index={i} />
          </Sequence>
        ))}
        <Deco total={spec.total} />
        <Finish />
        {spec.audio ? <Audio src={staticFile(spec.audio)} /> : null}
      </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
