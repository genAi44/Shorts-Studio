import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, ArText, Card, Counter, useKit, useSpr, enter, SceneProps, LAYOUT, useIdle, ease} from '../kit';

export default function Scene({dur, data}: SceneProps) {
  const k = useKit();
  const p = useSpr(0.1, 'snappy');
  const shapeOffset = useIdle(8, 10, 0);

  return (
    <AbsoluteFill>
      <Abs
        x={500}
        y={660 + shapeOffset}
        style={{
          width: 180,
          height: 180,
          borderRadius: 90,
          background: k.c('ground2', 0.15),
        }}
      />

      <Abs
        x={90}
        y={640}
        w={900}
        style={enter(p, 'rise', 60)}
      >
        <Card style={{padding: 40}}>
          <ArText
            size={80}
            reveal="words"
            align="center"
            color={k.c('text')}
          >
            {data.sentence}
          </ArText>
          <Counter
            year
            to={1037}
            from={980}
            size={150}
            delay={0.3}
            dur={dur}
            color={k.c('accent')}
          />
        </Card>
      </Abs>
    </AbsoluteFill>
  );
}
