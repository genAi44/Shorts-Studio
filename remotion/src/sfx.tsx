import React, {useMemo} from 'react';
import {Sequence, interpolate, staticFile} from 'remotion';
import {Audio} from '@remotion/media';
import {Spec} from './types';

/**
 * طبقة التصميم الصوتي (Sound Design):
 * - ambient bed هادئ يملأ فجوات الصمت بين المشاهد.
 * - impact في بداية الـ hook وبعد كل open loop (لحظة الكشف).
 * - whoosh يعبر كل قطع بين مشهدين.
 * - riser قبل نهاية كل open loop.
 * - pop مع مراحل ظهور البطاقات (0.35 / 0.70 من المشهد) أو بداية كل beat.
 * - tick مع ظهور الخريطة وكل دبوس جغرافي.
 * - ding في الـ CTA.
 * كل الملفات محلية (public/sfx/*.wav) يولّدها pipeline/sfx.py — لا اعتماد على الشبكة.
 */
type SfxName = 'whoosh' | 'pop' | 'tick' | 'impact' | 'riser' | 'ding';
type SfxEvent = {name: SfxName; from: number; volume: number};

const SFX_LEN: Record<SfxName, number> = {
  whoosh: 14,
  pop: 6,
  tick: 4,
  impact: 28,
  riser: 28,
  ding: 28,
};

const MIN_GAP: Record<SfxName, number> = {
  whoosh: 10,
  pop: 8,
  tick: 6,
  impact: 20,
  riser: 20,
  ding: 20,
};

export const buildSfxEvents = (spec: Spec): SfxEvent[] => {
  const ev: SfxEvent[] = [];
  const add = (name: SfxName, from: number, volume: number) => {
    if (!Number.isFinite(from)) return;
    ev.push({name, from: Math.max(0, Math.round(from)), volume});
  };
  spec.scenes.forEach((sc, i) => {
    const start = sc.from;
    const end = sc.from + sc.dur;
    const prev = i > 0 ? spec.scenes[i - 1] : null;
    if (i === 0) {
      add('impact', start, 0.24);
    } else {
      add('whoosh', start - 6, 0.16);
      if (prev && prev.role === 'open_loop') add('impact', start, 0.20);
    }
    if (sc.role === 'open_loop' && sc.dur > 60) add('riser', end - SFX_LEN.riser - 2, 0.18);
    if (sc.role === 'cta' || sc.role === 'loop') add('ding', start + 6, 0.16);

    const beats = sc.beats || [];
    const custom = beats.some((b) => Boolean(b.tsx_id) || b.kind === 'custom_scene' || b.kind === 'generative_canvas');
    if (custom && beats.length <= 1) {
      // تتزامن مع مراحل الكشف الثلاث المطلوبة من مولّد المشاهد
      if (sc.dur > 75) {
        add('pop', start + sc.dur * 0.35, 0.16);
        add('pop', start + sc.dur * 0.7, 0.16);
      }
    } else {
      beats.forEach((b, bi) => {
        if (bi > 0) add('pop', start + b.from, 0.16);
      });
    }

    const mo = sc.map_overlay;
    if (mo && mo.enabled && mo.waypoints && mo.waypoints.length) {
      add('tick', start + mo.enter_frame, 0.14);
      mo.waypoints.forEach((w, wi) => {
        if (wi > 0 || w.trigger_frame - mo.enter_frame > 8) add('tick', start + w.trigger_frame + 10, 0.12);
      });
    }
  });

  ev.sort((a, b) => a.from - b.from);
  const last: Partial<Record<SfxName, number>> = {};
  return ev.filter((e) => {
    const l = last[e.name];
    if (l !== undefined && e.from - l < MIN_GAP[e.name]) return false;
    if (e.from >= spec.total) return false;
    last[e.name] = e.from;
    return true;
  });
};

export const SoundDesignLayer: React.FC<{spec: Spec}> = ({spec}) => {
  const events = useMemo(() => buildSfxEvents(spec), [spec]);
  const total = spec.total;
  return (
    <>
      <Audio
        src={staticFile('sfx/ambient.wav')}
        loop
        volume={(f: number) =>
          0.42 *
          interpolate(f, [0, 20, Math.max(21, total - 24), total], [0, 1, 1, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })
        }
      />
      {events.map((e, i) => (
        <Sequence key={`${e.name}-${i}`} from={e.from} durationInFrames={SFX_LEN[e.name] + 6} layout="none" name={`sfx:${e.name}`}>
          <Audio src={staticFile(`sfx/${e.name}.wav`)} volume={e.volume} />
        </Sequence>
      ))}
    </>
  );
};
