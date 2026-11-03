import React from 'react';
import {Composition} from 'remotion';
import {Short} from './Short';
import {demoSpec} from './demo';
import type {Spec} from './types';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Short"
    component={Short}
    durationInFrames={150}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={{spec: demoSpec}}
    calculateMetadata={({props}: {props: {spec: Spec}}) => ({
      durationInFrames: Math.max(1, props.spec.total),
      fps: props.spec.fps,
      width: props.spec.width,
      height: props.spec.height,
    })}
  />
);
