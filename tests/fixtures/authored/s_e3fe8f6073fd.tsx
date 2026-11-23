import React from 'react';
import {AbsoluteFill} from 'remotion';
import {SceneProps, LAYOUT, useKit, Abs, Card, ArText, Counter, Icon, useSpr, enter, useIdle} from '../kit';

export default function Scene({dur, data}: SceneProps) {
  const k = useKit();
  const p = useSpr(0.1, 'snappy');
  const idle = useIdle(5, 4, 0);

  const cardW = 860;
  const cardX = LAYOUT.cx - cardW / 2;
  const cardY = LAYOUT.beat.top + 60;

  return (
    <AbsoluteFill>
      <Abs x={cardX + cardW / 2} y={cardY + 120} style={{transform: `translate(${idle}px,${idle}px)`}}>
        <Icon name="lucide:landmark" size={260} color={k.c('accent2', 0.1)} strokeWidth={1} />
      </Abs>

      <Abs x={cardX} y={cardY} w={cardW} style={enter(p, 'rise', 60)}>
        <Card style={{padding: 40}}>
          <ArText
            size={68}
            weight={700}
            color={k.c('text')}
            align="center"
            maxWidth={cardW - 80}
            reveal="words"
          >
            {data.sentence}
          </ArText>
          <ArText
            size={38}
            weight={400}
            color={k.c('accent')}
            align="center"
            style={{marginTop: 24}}
            maxWidth={cardW - 80}
          >
            {data.entities[0].label_ar}
          </ArText>
          <Counter
            to={data.entities[0].to}
            from={data.entities[0].value}
            size={120}
            delay={0.3}
            color={k.c('accent')}
            style={{marginTop: 28}}
          />
        </Card>
      </Abs>
    </AbsoluteFill>
  );
}
