import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, ArText, Icon, KeyLine, LAYOUT, Pinned, Ribbon, SceneProps, Stack, useKit} from '../kit';

// Recipe: a pinned card on the left of a cumulative list.
export default function Scene({data}: SceneProps) {
  const k = useKit();
  return (
    <AbsoluteFill>
      <Ribbon variant={2} />
      <Abs x={90} y={LAYOUT.beat.top + 10} w={900} style={{display: 'flex', justifyContent: 'center'}}>
        <KeyLine keyword="ما الذي يحدث؟" size={96} />
      </Abs>
      <Stack
        top={LAYOUT.beat.top + 220}
        items={[
          {text: 'ترتفع الطلبات', icon: 'lucide:trending-up'},
          {text: 'تتسع الموانئ', icon: 'lucide:ship'},
          {text: 'تنمو المدن', icon: 'lucide:building-2'},
          {text: 'تتغير الأسواق', icon: 'lucide:store'},
        ]}
      />
    </AbsoluteFill>
  );
}
