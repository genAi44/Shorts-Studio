import React from 'react';
import {AbsoluteFill} from 'remotion';
import {AUTHORED} from './authored/registry';
import type {Beat} from './types';

class SceneBoundary extends React.Component<{id: string; children: React.ReactNode}, {failed: boolean}> {
  state = {failed: false};
  static getDerivedStateFromError() { return {failed: true}; }
  componentDidCatch(e: unknown) { console.warn('[authored-scene] runtime error in', this.props.id, e); }
  render() { return this.state.failed ? null : this.props.children; }
}

/** Renders an authored scene by id. The same component serves preview and final render. */
export const AuthoredBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const Scene = AUTHORED[String(beat.scene_id)];
  if (!Scene) {
    console.warn('[authored-scene] missing scene', beat.scene_id);
    return null;
  }
  return (
    <AbsoluteFill>
      <SceneBoundary id={String(beat.scene_id)}><Scene dur={beat.dur || 150} data={beat.data || {}} /></SceneBoundary>
    </AbsoluteFill>
  );
};
