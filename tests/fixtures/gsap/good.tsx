import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ArText, HeroPhoto, LAYOUT, SceneProps, useGsapTimeline} from '../kit';

export default function Scene({data}: SceneProps) {
  const scope = useGsapTimeline<HTMLDivElement>(({timeline: tl, selector: q}) => {
    tl.from(q('.card'), {y: 80, opacity: 0, duration: 0.6, ease: 'back.out(1.6)'}, 0.2);
    tl.fromTo(q('.route'), {strokeDashoffset: 1}, {strokeDashoffset: 0, duration: 2.4, ease: 'power2.inOut'}, 0.8);
    tl.to(q('.card'), {y: -12, duration: 6, ease: 'none'}, 0.8);
  });
  return (
    <AbsoluteFill>
      <style>{`.card{position:absolute;left:140px;top:420px;width:800px;height:520px;border-radius:32px;background:#fff8ef;box-shadow:0 20px 50px rgba(0,0,0,.15)}`}</style>
      <div ref={scope} style={{position: 'absolute', inset: 0}}>
        <div className="card">
          <svg width={800} height={520}><path className="route" d="M60 460 C 300 80, 520 80, 740 400" pathLength={1} strokeDasharray={1} fill="none" stroke="#B22656" strokeWidth={10} /></svg>
        </div>
      </div>
      <HeroPhoto data={data} x={200} y={LAYOUT.beat.top} w={680} h={360} />
      <ArText size={96}>{data.sentences?.[0] ?? ''}</ArText>
    </AbsoluteFill>
  );
}
