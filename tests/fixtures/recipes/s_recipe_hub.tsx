import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, Hub, Icon, KeyLine, LAYOUT, Ribbon, SceneProps, useKit} from '../kit';

// Recipe: Ribbon behind, KeyLine on top (one key word), Hub of satellites below.
export default function Scene({data}: SceneProps) {
  const k = useKit();
  return (
    <AbsoluteFill>
      <Ribbon variant={0} />
      <Abs x={90} y={LAYOUT.beat.top + 10} w={900} style={{display: 'flex', justifyContent: 'center'}}>
        <KeyLine lead="مصدر الدخل" keyword="خمسة روافد" size={110} />
      </Abs>
      <Hub
        cy={LAYOUT.beat.center_y + 120}
        radius={300}
        center={<Icon name="lucide:wallet" size={130} color={k.c('accent')} />}
        items={[
          {icon: 'lucide:fuel', label: 'النفط'},
          {icon: 'lucide:landmark', label: 'الاستثمار'},
          {icon: 'lucide:ship', label: 'الموانئ'},
          {icon: 'lucide:plane', label: 'السياحة'},
          {icon: 'lucide:cpu', label: 'التقنية'},
        ]}
      />
    </AbsoluteFill>
  );
}
