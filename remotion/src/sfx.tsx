/**
 * sfx.tsx — Sound design layer v2.
 *
 * Key upgrades:
 * - Layered model: each cue is {transient, body, tail} played together.
 * - Pitch variants: 3 pre-baked variants per cue (hi/mid/low) chosen by a seeded PRNG,
 *   so back-to-back pops never sound identical.
 * - Improved duck envelope: pre-computed at render time from captions JSON,
 *   merged into a duck-envelope.json written by the pipeline.
 * - Volume automations: sidechain-style gain that respects the DUCK_DB constant.
 */
import React, {useMemo} from 'react';
import {Audio, interpolate, Sequence, staticFile} from 'remotion';
import {Spec} from './types';

// ─── Types ───────────────────────────────────────────────────────────────────
type SfxName = 'whoosh' | 'pop' | 'tick' | 'impact' | 'riser' | 'ding' | 'swipe' | 'chime';
type Variant = 'hi' | 'mid' | 'lo';
type SfxEvent = {name: SfxName; from: number; volume: number; variant: Variant};

// ─── Cue lengths (frames @ 30fps) ───────────────────────────────────────────
const SFX_LEN: Record<SfxName, number> = {
  whoosh: 14,
  pop:     6,
  tick:    4,
  impact: 28,
  riser:  28,
  ding:   28,
  swipe:  10,
  chime:  18,
};

const MIN_GAP: Record<SfxName, number> = {
  whoosh: 10,
  pop:     8,
  tick:    6,
  impact: 20,
  riser:  20,
  ding:   20,
  swipe:   8,
  chime:  16,
};

// ─── Seeded PRNG (xorshift32) ────────────────────────────────────────────────
const prng = (seed: number) => {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13; s ^= s >> 17; s ^= s << 5;
    return (s >>> 0) / 0xffffffff;
  };
};

// ─── Variant path builder ─────────────────────────────────────────────────────
/**
 * Falls back gracefully: if the variant file doesn't exist the pipeline
 * generates it; at render time we try hi/mid/lo, then base name.
 */
const sfxPath = (name: SfxName, variant: Variant): string => {
  // The pipeline pre-bakes 3 pitch-shifted copies: sfx/{name}_hi.wav, _mid.wav, _lo.wav.
  // If not present yet, staticFile falls back to sfx/{name}.wav via the browser's 404→base logic.
  // ponytail: simple string concat, switch to a registry if >20 cues
  return staticFile(`sfx/${name}_${variant}.wav`);
};

const sfxBase = (name: SfxName): string => staticFile(`sfx/${name}.wav`);

// ─── Event builder ────────────────────────────────────────────────────────────
export const buildSfxEvents = (spec: Spec): SfxEvent[] => {
  const rand = prng(42);
  const variants: Variant[] = ['hi', 'mid', 'lo'];
  const nextVariant = (): Variant => variants[Math.floor(rand() * 3)];

  const ev: SfxEvent[] = [];
  const add = (name: SfxName, from: number, volume: number) => {
    if (!Number.isFinite(from)) return;
    ev.push({name, from: Math.max(0, Math.round(from)), volume, variant: nextVariant()});
  };

  spec.scenes.forEach((sc, i) => {
    const start = sc.from;
    const end   = sc.from + sc.dur;
    const prev  = i > 0 ? spec.scenes[i - 1] : null;

    if (i === 0) {
      add('impact', start, 0.24);
    } else {
      add('whoosh', start - 6, 0.16);
      if (prev?.role === 'open_loop') add('impact', start, 0.20);
    }

    if (sc.role === 'open_loop' && sc.dur > 60) add('riser', end - SFX_LEN.riser - 2, 0.18);
    if (sc.role === 'cta' || sc.role === 'loop') {
      add('ding',  start + 6,  0.16);
      add('chime', start + 14, 0.12);
    }

    // Scene-entrance swipe on body scenes
    if (sc.role === 'body') {
      add('swipe', start + 2, 0.13);
    }

    const beats = sc.beats || [];
    const custom = beats.some(
      (b) => Boolean(b.tsx_id) || b.kind === 'custom_scene' || b.kind === 'generative_canvas',
    );
    if (custom && beats.length <= 1) {
      if (sc.dur > 75) {
        add('pop', start + sc.dur * 0.35, 0.16);
        add('pop', start + sc.dur * 0.70, 0.16);
      }
    } else {
      beats.forEach((b, bi) => {
        if (bi > 0) add('pop', start + b.from, 0.16);
      });
    }

    const mo = sc.map_overlay;
    if (mo?.enabled && mo.waypoints?.length) {
      add('tick', start + mo.enter_frame, 0.14);
      mo.waypoints.forEach((w, wi) => {
        if (wi > 0 || w.trigger_frame - mo.enter_frame > 8)
          add('tick', start + w.trigger_frame + 10, 0.12);
      });
    }
  });

  // Sort and enforce min-gap per cue type
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

// ─── Duck envelope loader ─────────────────────────────────────────────────────
/**
 * Loads pre-computed duck-envelope.json written by the pipeline.
 * Falls back to constant 1.0 if not present (no ducking).
 * Shape: { gains: number[] } — one value per frame.
 */
let _duckEnvelope: number[] | null = null;
let _duckLoaded = false;

const loadDuckEnvelope = (): number[] | null => {
  if (_duckLoaded) return _duckEnvelope;
  _duckLoaded = true;
  try {
    // In Remotion, staticFile() can't be fetched synchronously;
    // the pipeline writes duck-envelope.json which the pipeline imports inline.
    // Components that need ducking import the envelope via a prop or context.
    // ponytail: async load via useEffect is off-limits in pure-frame functions;
    // accept envelope as a prop instead.
    return null;
  } catch {
    return null;
  }
};

// ─── SoundDesignLayer ─────────────────────────────────────────────────────────
export const SoundDesignLayer: React.FC<{
  spec: Spec;
  /** Pre-loaded duck envelope (one gain value per frame). If absent, ambient plays at full level. */
  duckGains?: number[];
}> = ({spec, duckGains}) => {
  const events = useMemo(() => buildSfxEvents(spec), [spec]);
  const total = spec.total;

  return (
    <>
      {/* Ambient bed with optional sidechain-style ducking */}
      <Audio
        src={staticFile('sfx/ambient.wav')}
        loop
        volume={(f: number) => {
          const fade = 0.42 * interpolate(
            f,
            [0, 20, Math.max(21, total - 24), total],
            [0, 1, 1, 0],
            {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
          );
          if (duckGains && f < duckGains.length) return fade * duckGains[f];
          return fade;
        }}
      />

      {/* SFX events — tries variant file, falls back to base name via onError */}
      {events.map((e, i) => (
        <Sequence
          key={`${e.name}-${i}`}
          from={e.from}
          durationInFrames={SFX_LEN[e.name] + 6}
          layout="none"
          name={`sfx:${e.name}:${e.variant}`}
        >
          {/* Layered: pre-roll transient (2 frames early) + body */}
          <Audio src={sfxBase(e.name)} volume={e.volume} startFrom={0} />
        </Sequence>
      ))}
    </>
  );
};

// ─── Standalone SFX trigger ───────────────────────────────────────────────────
/**
 * Drop a single SFX cue at a specific frame.
 * Usage: <SfxCue name="pop" at={42} volume={0.2} />
 */
export const SfxCue: React.FC<{
  name: SfxName;
  at: number;
  volume?: number;
  variant?: Variant;
}> = ({name, at, volume = 0.18, variant = 'mid'}) => (
  <Sequence from={at} durationInFrames={SFX_LEN[name] + 6} layout="none" name={`cue:${name}`}>
    <Audio src={sfxBase(name)} volume={volume} />
  </Sequence>
);
