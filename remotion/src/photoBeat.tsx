// Split from photo.tsx (re-exported there).
import React, {useContext} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {clamp01, enterStyle, useIdle, useProgress, useSpring} from './hooks';
import {MapLayoutCtx, MotionCtx, rgba, useTheme} from './theme';
import {BEAT_ZONE} from './layout';
import {Beat} from './types';
import {CountNum, Framed, MixedText, Pic} from './photo';

// ------------------------------------------------------------------ مقطع الصورة

export const PhotoBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const th = useTheme();

  const ed = th.st.edit;

  const {settled} = useContext(MotionCtx);

  const {splitBottom} = useContext(MapLayoutCtx);

  const pop = useSpring(0.05, 'bouncy');

  const sm = useSpring(0.05, 'smooth');

  const ring = useProgress(0.1, 0.9);

  const idle = useIdle(9, 3.8);

  const frame = useCurrentFrame();

  const {fps} = useVideoConfig();

  const hasNum = !!beat.number;

  const cy = splitBottom ? 400 : th.zoneCy - (hasNum ? 230 : 110);

  const textY = th.zoneCy + (hasNum ? 170 : 330);

  const capSize = Math.max(48, Math.round(th.st.text.size * 0.62));

  const spin = settled ? 0 : (frame / fps) * 8;

  const cut = !!beat.cut;

  const S = splitBottom ? 450 : (hasNum ? 540 : 620);



  let media: React.ReactNode;

  if (cut) {

    const R = S + 90;

    const C = 2 * Math.PI * (R / 2 - 3);

    media = (

      <>

        {ed.cutout === 'glow' && <div style={{position: 'absolute', left: 540 - R * 0.8, top: cy - R * 0.8, width: R * 1.6, height: R * 1.6, borderRadius: '50%', background: `radial-gradient(circle, ${rgba(th.p.accent, 0.5)}, transparent 68%)`, opacity: sm}} />}

        {ed.cutout === 'blob' && <div style={{position: 'absolute', left: 540 - S * 0.52, top: cy - S * 0.5, width: S * 1.04, height: S, background: rgba(th.p.accent, 0.92), borderRadius: '58% 42% 55% 45% / 48% 56% 44% 52%', rotate: `${spin * 2 - 8}deg`, scale: 0.6 + 0.4 * pop, opacity: clamp01(pop * 1.6)}} />}

        {ed.cutout === 'ring' && (

          <svg width={R} height={R} viewBox={`0 0 ${R} ${R}`} style={{position: 'absolute', left: 540 - R / 2, top: cy - R / 2, rotate: `${spin}deg`, overflow: 'visible'}}>

            <circle cx={R / 2} cy={R / 2} r={R / 2 - 3} fill="none" stroke={rgba(th.p.text, 0.8)} strokeWidth={4} strokeLinecap="round" strokeDasharray={`3 14`} strokeDashoffset={C * (1 - ring)} opacity={ring} />

            <circle cx={R / 2} cy={R / 2} r={R / 2 - 3} fill="none" stroke={rgba(th.p.accent, 0.9)} strokeWidth={5} strokeLinecap="round" pathLength={1} strokeDasharray={`0.18 1`} strokeDashoffset={-ring * 0.9} />

          </svg>

        )}

        <Pic beat={beat} fit="contain" style={{position: 'absolute', left: 540 - S / 2, top: cy - S / 2 + idle, width: S, height: S, filter: 'drop-shadow(0 26px 28px rgba(0,0,0,0.38))', ...enterStyle(pop, 'pop')}} />

      </>

    );

  } else if (ed.photo === 'bleed') {

    const H = splitBottom ? 680 : (hasNum ? 1200 : 1400);

    media = (

      <div style={{position: 'absolute', left: 0, right: 0, top: splitBottom ? 80 : cy - H / 2, opacity: clamp01(sm * 1.5), translate: `0 ${(1 - sm) * 50}px`, WebkitMaskImage: 'linear-gradient(to bottom, transparent, #000 14%, #000 84%, transparent)', maskImage: 'linear-gradient(to bottom, transparent, #000 14%, #000 84%, transparent)'}}>

        <Framed beat={beat} w={1080} h={H} />

      </div>

    );

  } else if (ed.photo === 'free') {

    // frameless: no border, no card; the photo dissolves into the background through a soft elliptical mask
    const w = splitBottom ? 960 : (hasNum ? 940 : 1000), h = splitBottom ? 540 : (hasNum ? 680 : 800);
    const fade = 'radial-gradient(ellipse 50% 50% at 50% 50%, #000 58%, transparent 100%)';

    media = (

      <div style={{position: 'absolute', left: 540 - w / 2, top: cy - h / 2 + idle * 0.5, opacity: clamp01(sm * 1.5) * (beat.img ? 1 : 0.28), scale: 0.94 + 0.06 * sm, WebkitMaskImage: fade, maskImage: fade}}>

        <Framed beat={beat} w={w} h={h} />

      </div>

    );

  } else if (ed.photo === 'circle') {

    // frameless: a round crop with only a soft shadow (no border line)
    const D = splitBottom ? 470 : (hasNum ? 600 : 700);

    media = (

      <div style={{position: 'absolute', left: 540 - D / 2, top: cy - D / 2 + idle * 0.5, filter: beat.img ? 'drop-shadow(0 26px 30px rgba(0,0,0,0.38))' : 'none', opacity: beat.img ? 1 : 0.35, ...enterStyle(pop, 'pop')}}>

        <Framed beat={beat} w={D} h={D} style={{borderRadius: '50%'}} />

      </div>

    );

  } else if (ed.photo === 'polaroid') {

    const w = splitBottom ? 920 : (hasNum ? 820 : 920);

    const h = splitBottom ? 520 : (hasNum ? 620 : 760);

    media = (

      <div style={{position: 'absolute', left: 540 - w / 2, top: cy - h / 2 + idle * 0.5, padding: 10, background: 'rgba(255,255,255,0.08)', backdropFilter: 'blur(16px)', border: '1px solid rgba(255,255,255,0.18)', borderRadius: 28, boxShadow: '0 30px 60px rgba(0,0,0,0.45)', ...enterStyle(pop, 'rise', 60)}}>

        <Framed beat={beat} w={w} h={h} style={{borderRadius: 20}} />

      </div>

    );

  } else if (ed.photo === 'arch') {

    const w = splitBottom ? 920 : (hasNum ? 820 : 920), h = splitBottom ? 520 : (hasNum ? 660 : 820);

    media = (

      <div style={{position: 'absolute', left: 540 - w / 2, top: cy - h / 2 + idle * 0.5, borderRadius: 28, overflow: 'hidden', border: `2.5px solid ${rgba(th.p.accent, 0.72)}`, boxShadow: `0 28px 54px rgba(0,0,0,0.45), 0 0 36px ${rgba(th.p.accent, 0.22)}`, ...enterStyle(pop, 'rise', 60)}}>

        <Framed beat={beat} w={w} h={h} />

      </div>

    );

  } else if (ed.photo === 'tilt') {

    const w = splitBottom ? 900 : (hasNum ? 800 : 900), h = splitBottom ? 500 : (hasNum ? 600 : 720);

    media = (

      <div style={{position: 'absolute', left: 540 - w / 2, top: cy - h / 2 + idle * 0.5, rotate: `${1.5 - 1.5 * (1 - pop)}deg`, ...enterStyle(pop, 'left', 40)}}>

        <div style={{position: 'absolute', left: 18, top: 18, width: w, height: h, borderRadius: 28, background: rgba(th.p.accent, 0.85)}} />

        <Framed beat={beat} w={w} h={h} style={{borderRadius: 28, boxShadow: '0 26px 44px rgba(0,0,0,0.35)'}} />

      </div>

    );

  } else {

    const w = splitBottom ? 920 : (hasNum ? 820 : 920), h = splitBottom ? 520 : (hasNum ? 640 : 780);

    media = (

      <div style={{position: 'absolute', left: 540 - w / 2, top: cy - h / 2 + idle * 0.5, borderRadius: 28, overflow: 'hidden', border: `2.5px solid ${rgba(th.p.accent, 0.7)}`, boxShadow: '0 24px 48px rgba(0,0,0,0.4)', ...enterStyle(pop, 'pop')}}>

        <Framed beat={beat} w={w} h={h} />

      </div>

    );

  }



  return (

    <AbsoluteFill>

      {media}

      {hasNum ? <CountNum text={String(beat.number)} size={150} y={textY - 20} /> : null}

      {!splitBottom && beat.text && beat.text.trim().length > 0 && !(beat.narration && beat.narration.includes(beat.text.trim())) ? (

        <div style={{

          position: 'absolute', left: 60, right: 60, top: Math.min(hasNum ? textY + 120 : textY, BEAT_ZONE.bottom - 180),

          padding: '16px 28px', borderRadius: 28,

          background: rgba(th.dark ? th.p.c2 : th.p.c1, 0.72),

          backdropFilter: 'blur(20px)',

          WebkitBackdropFilter: 'blur(20px)',

          boxShadow: `0 14px 34px rgba(0,0,0,0.32), inset 0 0 0 1.5px ${rgba(th.p.accent, 0.35)}`,

          display: 'flex', justifyContent: 'center'

        }}>

          <MixedText text={beat.text} size={Math.max(48, hasNum ? Math.round(capSize * 0.82) : capSize)} delay={0} />

        </div>

      ) : null}

    </AbsoluteFill>

  );

};
