import React from 'react';
import {AbsoluteFill} from 'remotion';
import {SceneProps, LAYOUT, useKit, Abs, Card, ArText, Counter, useSpr, enter} from '../kit';

export default function Scene({dur, data}: SceneProps) {
  const k = useKit();
  const p = useSpr(0.1, 'snappy');
  return (
    <AbsoluteFill>
      <Abs x={90} y={LAYOUT.beat.center_y - 220} w={900} style={enter(p, 'rise', 60)}>
        <Card style={{padding: 40}}>
          <ArText size={64} color={data.theme.text} align="center">
            {data.sentence}
          </ArText>
          <Counter to={17} from={0} delay={0.3} size={150} color={data.theme.accent} />
          <Counter to={10} from={0} delay={0.6} size={150} color={data.theme.accent} />
        </Card>
      </Abs>
    </AbsoluteFill>
  );
}
