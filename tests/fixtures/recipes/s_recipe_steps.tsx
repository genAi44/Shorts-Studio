import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, KeyLine, LAYOUT, Ribbon, SceneProps, Steps} from '../kit';

// Recipe: three rising steps with a two-tone headline above them.
export default function Scene({data}: SceneProps) {
  return (
    <AbsoluteFill>
      <Ribbon variant={1} />
      <Abs x={90} y={LAYOUT.beat.top + 10} w={900} style={{display: 'flex', justifyContent: 'center'}}>
        <KeyLine lead="ثلاث خطوات للنمو" keyword="الوضوح أولاً" size={104} />
      </Abs>
      <Steps items={['وضوح', 'هيكل', 'نتائج']} />
    </AbsoluteFill>
  );
}
