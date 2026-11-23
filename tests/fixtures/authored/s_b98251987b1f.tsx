import React from 'react';
import {Abs, Card, ArText, Counter, Ring, useKit, enter, useSpr, useProgress, SceneProps, LAYOUT} from '../kit';

export default function Scene({dur, data}: SceneProps) {
  const k = useKit();
  const progress = useProgress(0, dur / k.fps);
  const p = useSpr(0.1, 'snappy');
  return (
    <Abs x={0} y={0} w={LAYOUT.W} h={LAYOUT.H} style={{background: 'transparent'}}>
      <Abs x={450} y={800} w={300} h={300} style={{background: 'transparent'}}>
        <Ring
          size={300}
          value={progress}
          stroke={2}
          color={k.c('accent2', 0.2)}
          delay={0.5}
        />
      </Abs>
      <Abs
        x={90}
        y={LAYOUT.beat.center_y - 220}
        w={900}
        style={enter(p, 'rise', 60)}
      >
        <Card
          style={{
            padding: 40,
            background: data.theme.card_bg,
            border: data.theme.card_border,
          }}
        >
          <ArText
            size={80}
            color={data.theme.text}
            align="center"
          >
            {data.sentence}
          </ArText>
          <Counter
            to={1300000}
            size={150}
            delay={0.3}
          />
        </Card>
      </Abs>
    </Abs>
  );
}
