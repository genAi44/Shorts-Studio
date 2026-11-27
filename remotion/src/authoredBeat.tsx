import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {AUTHORED} from './authored/registry';
import type {Beat} from './types';

class SceneBoundary extends React.Component<{id: string; children: React.ReactNode}, {failed: boolean}> {
  state = {failed: false};
  static getDerivedStateFromError() { return {failed: true}; }
  componentDidCatch(e: unknown) { console.warn('[authored-scene] runtime error in', this.props.id, e); }
  render() { return this.state.failed ? null : this.props.children; }
}

/** Motion floor for every authored scene: a slow continuous push-in (100 % -> 105 %) with a gentle drift, so no frame of a
 *  drawn scene is ever frozen (measured: authored scenes were frozen 26-67 % of the time, photo/map scenes 2-11 %).
 *  Pure function of the frame; the sandbox audit renders through it, so the gates measure the moved layout. */
export const CAMERA_PUSH = 0.05;
const CameraFloor: React.FC<{dur: number; children: React.ReactNode}> = ({dur, children}) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [0, Math.max(1, dur)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.sin)});
  const scale = 1 + CAMERA_PUSH * t;
  const dx = Math.sin((frame / Math.max(30, dur)) * Math.PI * 2) * 10;
  const dy = -14 * t;
  return (
    <AbsoluteFill style={{transform: `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px) scale(${scale.toFixed(4)})`, transformOrigin: '50% 45%'}}>
      {children}
    </AbsoluteFill>
  );
};

/** Renders an authored scene by id. The same component serves preview and final render. */
export const AuthoredBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const Scene = AUTHORED[String(beat.scene_id)];
  if (!Scene) {
    console.warn('[authored-scene] missing scene', beat.scene_id);
    return null;
  }
  return (
    <CameraFloor dur={beat.dur || 150}>
      <SceneBoundary id={String(beat.scene_id)}><Scene dur={beat.dur || 150} data={beat.data || {}} /></SceneBoundary>
    </CameraFloor>
  );
};
