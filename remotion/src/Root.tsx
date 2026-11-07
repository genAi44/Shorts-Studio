import React from 'react';
import {AbsoluteFill, Composition} from 'remotion';
import {Short} from './Short';
import {demoSpec} from './demo';
import {ElevationProfileBeat} from './beats';
import {
  AnimatedRouteBeat,
  BalanceMeterBeat,
  DeepTimeSliderBeat,
  DotMatrixPopulationBeat,
  FrontlineClashBeat,
  MacroZoomGlobeBeat,
  MoneyWaterfallBeat,
  StackPyramidBeat,
  SubsurfaceMineBeat,
  VersusBattleBeat,
} from './visualStoryBeats';
import {GenerativeCanvasBeat} from './generativeCanvas';
import {MotionCtx, ThemeCtx, makeTheme} from './theme';
import {Icon} from './icons';
import {Emoji} from './emoji';
import {Flag} from './flag';
import {LottieVisual} from './lottie';
import {BarChart, LineChart, NumberCounter, PieDonutChart, ProgressRing, Timeline} from './charts';
import {
  AnimatedHeadline,
  BulletListReveal,
  LowerThird,
  QuoteCard,
  StatCallout,
  StyledCaption,
  TitleCard,
} from './typography';
import {getTransitionPresentation, linearTiming, NoiseShapesLayer, TransitionSeries} from './transitions';
import type {Spec} from './types';

export const ComponentShowcase: React.FC<{mode?: string}> = ({mode = 'all'}) => {
  const sampleData = [
    {label: 'مصر', value: 114, year: '١٩٥٢'},
    {label: 'السعودية', value: 92, year: '١٩٣٢'},
    {label: 'بوليفيا', value: 68, year: '١٨٢٥'},
    {label: 'المغرب', value: 78, year: '١٩٥٦'},
  ];

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #090e17 0%, #030508 100%)',
        color: '#f8fafc',
        padding: 48,
        direction: 'rtl',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 32,
      }}
    >
      <NoiseShapesLayer seed={42} />
      {mode === 'icon' && <Icon name="lucide:landmark" size={240} color="#f5c542" animation="draw" />}
      {mode === 'emoji' && <Emoji char="🏛️" size={240} animation="pop" />}
      {mode === 'flag' && (
        <div style={{display: 'flex', gap: 40}}>
          <Flag code="EG" shape="rect" size={180} animation="pop" />
          <Flag code="بوليفيا" shape="round" size={180} animation="float" />
        </div>
      )}
      {mode === 'lottie' && <LottieVisual name="checkmark" size={280} />}
      {mode === 'bar_rtl' && (
        <BarChart
          data={sampleData}
          style={{title: 'مقارنة المؤشرات الاقتصادية (RTL)', rtl: true, arabicNumerals: true, unit: '%'}}
        />
      )}
      {mode === 'line_rtl' && (
        <LineChart
          data={sampleData}
          style={{title: 'تطور النمو عبر العقود', rtl: true, arabicNumerals: true}}
        />
      )}
      {mode === 'donut_rtl' && (
        <PieDonutChart
          data={sampleData}
          style={{title: 'توزيع الحصص الإقليمية', rtl: true, arabicNumerals: true}}
        />
      )}
      {mode === 'counter_ring' && (
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 40}}>
          <NumberCounter value={3650} label="متراً فوق سطح البحر — لاباز" arabicNumerals={true} rtl={true} />
          <ProgressRing value={86} label="نسبة التحضر" arabicNumerals={true} />
        </div>
      )}
      {mode === 'timeline_rtl' && (
        <Timeline
          data={sampleData}
          style={{title: 'الخط الزمني للأحداث التاريخية', rtl: true, arabicNumerals: true}}
        />
      )}
      {mode === 'elevation_capital' && (
        <ThemeCtx.Provider value={makeTheme(demoSpec.style)}>
          <MotionCtx.Provider value={{speed: 1, settled: false}}>
            <ElevationProfileBeat
              beat={{
                kind: 'elevation_profile',
                from: 0,
                dur: 90,
                title: 'العاصمة لاباز — بوليفيا',
                capital: 'العاصمة لاباز',
                country: 'BO',
                height: '3,650',
                unit: 'م',
                sea_label: 'مستوى سطح البحر',
              }}
            />
          </MotionCtx.Provider>
        </ThemeCtx.Provider>
      )}
      {mode === 'versus_battle' && (
        <ThemeCtx.Provider value={makeTheme(demoSpec.style)}>
          <MotionCtx.Provider value={{speed: 1, settled: false}}>
            <VersusBattleBeat beat={{kind: 'versus_battle', from: 0, dur: 90, title: 'سباق القوة الاقتصادية'}} />
          </MotionCtx.Provider>
        </ThemeCtx.Provider>
      )}
      {mode === 'animated_route' && (
        <ThemeCtx.Provider value={makeTheme(demoSpec.style)}>
          <MotionCtx.Provider value={{speed: 1, settled: false}}>
            <AnimatedRouteBeat beat={{kind: 'animated_route', from: 0, dur: 90, title: 'مسار الانتقال إلى لاباز'}} />
          </MotionCtx.Provider>
        </ThemeCtx.Provider>
      )}
      {mode === 'balance_meter' && (
        <ThemeCtx.Provider value={makeTheme(demoSpec.style)}>
          <MotionCtx.Provider value={{speed: 1, settled: false}}>
            <BalanceMeterBeat beat={{kind: 'balance_meter', from: 0, dur: 90, title: 'ميزان السيطرة السياسية'}} />
          </MotionCtx.Provider>
        </ThemeCtx.Provider>
      )}
      {mode === 'deep_time_slider' && (
        <ThemeCtx.Provider value={makeTheme(demoSpec.style)}>
          <MotionCtx.Provider value={{speed: 1, settled: false}}>
            <DeepTimeSliderBeat beat={{kind: 'deep_time_slider', from: 0, dur: 90, title: 'قفزة عبر القرون والتاريخ'}} />
          </MotionCtx.Provider>
        </ThemeCtx.Provider>
      )}
      {mode === 'stack_pyramid' && (
        <ThemeCtx.Provider value={makeTheme(demoSpec.style)}>
          <MotionCtx.Provider value={{speed: 1, settled: false}}>
            <StackPyramidBeat beat={{kind: 'stack_pyramid', from: 0, dur: 90, title: 'هيكل السلطة الدستورية'}} />
          </MotionCtx.Provider>
        </ThemeCtx.Provider>
      )}
      {mode === 'macro_zoom_globe' && (
        <ThemeCtx.Provider value={makeTheme(demoSpec.style)}>
          <MotionCtx.Provider value={{speed: 1, settled: false}}>
            <MacroZoomGlobeBeat beat={{kind: 'macro_zoom_globe', from: 0, dur: 90, title: 'في قلب أمريكا الجنوبية'}} />
          </MotionCtx.Provider>
        </ThemeCtx.Provider>
      )}
      {mode === 'subsurface_mine' && (
        <ThemeCtx.Provider value={makeTheme(demoSpec.style)}>
          <MotionCtx.Provider value={{speed: 1, settled: false}}>
            <SubsurfaceMineBeat beat={{kind: 'subsurface_mine', from: 0, dur: 90, title: 'مناجم الفضة في باطن الأرض'}} />
          </MotionCtx.Provider>
        </ThemeCtx.Provider>
      )}
      {mode === 'dot_matrix_population' && (
        <ThemeCtx.Provider value={makeTheme(demoSpec.style)}>
          <MotionCtx.Provider value={{speed: 1, settled: false}}>
            <DotMatrixPopulationBeat beat={{kind: 'dot_matrix_population', from: 0, dur: 90, title: 'التوزيع السكاني الحي'}} />
          </MotionCtx.Provider>
        </ThemeCtx.Provider>
      )}
      {mode === 'money_waterfall' && (
        <ThemeCtx.Provider value={makeTheme(demoSpec.style)}>
          <MotionCtx.Provider value={{speed: 1, settled: false}}>
            <MoneyWaterfallBeat beat={{kind: 'money_waterfall', from: 0, dur: 90, title: 'شلال التدفقات المالية'}} />
          </MotionCtx.Provider>
        </ThemeCtx.Provider>
      )}
      {mode === 'frontline_clash' && (
        <ThemeCtx.Provider value={makeTheme(demoSpec.style)}>
          <MotionCtx.Provider value={{speed: 1, settled: false}}>
            <FrontlineClashBeat beat={{kind: 'frontline_clash', from: 0, dur: 90, title: 'اشتعال خطوط المواجهة العسكرية'}} />
          </MotionCtx.Provider>
        </ThemeCtx.Provider>
      )}
      {mode === 'generative_canvas' && (
        <ThemeCtx.Provider value={makeTheme(demoSpec.style)}>
          <MotionCtx.Provider value={{speed: 1, settled: false}}>
            <GenerativeCanvasBeat
              beat={{
                kind: 'generative_canvas',
                from: 0,
                dur: 90,
                title: 'انفجار بركاني مفاجئ وحمم منصهرة',
                subtitle: 'تم تأليفه تلقائياً من عناصر ليغو الحركية',
                accent: '#ef4444',
                grid: 'dots',
                elements: [
                  {
                    type: 'shape',
                    shape: 'triangle',
                    x: 540,
                    y: 1100,
                    w: 680,
                    h: 460,
                    fill: '#1c1917',
                    stroke: '#78350f',
                    strokeWidth: 4,
                    motion: 'rise',
                    delay: 0,
                  },
                  {
                    type: 'path',
                    curve: 'mountain',
                    from: [200, 1300],
                    to: [880, 1300],
                    stroke: '#f97316',
                    strokeWidth: 6,
                    motion: 'draw',
                    delay: 5,
                  },
                  {
                    type: 'shape',
                    shape: 'circle',
                    x: 540,
                    y: 860,
                    w: 90,
                    h: 90,
                    fill: '#ef4444',
                    stroke: '#fca5a5',
                    strokeWidth: 3,
                    motion: 'pop',
                    loop: 'pulse',
                    delay: 10,
                  },
                  {
                    type: 'counter',
                    x: 540,
                    y: 600,
                    to: 1200,
                    unit: '°م',
                    label: 'حرارة الحمم البركانية',
                    color: '#ef4444',
                    fontSize: 72,
                    motion: 'pop',
                    delay: 15,
                  },
                  {
                    type: 'badge',
                    x: 540,
                    y: 430,
                    text: 'تحذير جيولوجي عالي الخطورة',
                    icon: 'lucide:flame',
                    size: 'lg',
                    bg: 'rgba(69, 10, 10, 0.92)',
                    borderColor: '#ef4444',
                    textColor: '#fef2f2',
                    motion: 'drop',
                    delay: 20,
                  },
                  {
                    type: 'gauge',
                    x: 540,
                    y: 1420,
                    value: 86,
                    label: 'نسبة انتشار الرماد في الغلاف الجوي',
                    unit: '%',
                    color: '#f97316',
                    width: 720,
                    motion: 'rise',
                    delay: 25,
                  },
                ],
              }}
            />
          </MotionCtx.Provider>
        </ThemeCtx.Provider>
      )}
      {mode === 'typography_rtl' && (
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 28, width: '100%'}}>
          <TitleCard title="لماذا تملك بوليفيا عاصمتين رسميتين؟" subtitle="قصة سوكري ولاباز عبر التاريخ" rtl={true} />
          <LowerThird title="مدينة لاباز — بوليفيا" subtitle="أعلى مقر حكومي في العالم (٣٬٦٥٠ م)" rtl={true} />
          <QuoteCard quote="التاريخ يكتبه الجغرافيا وتصنعه الشعوب" author="ابن خلدون" rtl={true} />
          <BulletListReveal title="الحقائق الثلاث الحاسمة" items={['سوكري العاصمة الدستورية منذ ١٨٢٥', 'لاباز مقر الحكومة والبرلمان منذ ١٨٩٩', 'دستور ٢٠٠٩ ثبّت التسوية التاريخية']} rtl={true} />
          <StatCallout value="3650" label="ارتفاع لاباز فوق سطح البحر" unit="م" arabicNumerals={true} rtl={true} />
          <StyledCaption text="اكتشف سر العاصمتين في ستين ثانية" mode="word-highlight" rtl={true} />
        </div>
      )}
      {mode === 'all' && (
        <>
          <AnimatedHeadline text="طبقة العناصر البصرية والرسوم المتحركة" rtl={true} />
          <div style={{display: 'flex', gap: 36, alignItems: 'center'}}>
            <Icon name="lucide:landmark" size={120} color="#f5c542" animation="pop" />
            <Emoji char="🏛️" size={120} animation="bounce" />
            <Flag code="EG" shape="rect" size={110} animation="pop" />
            <Flag code="BO" shape="round" size={110} animation="float" />
            <LottieVisual name="checkmark" size={140} />
          </div>
          <BarChart
            data={sampleData}
            style={{title: 'مقارنة المؤشرات بالأرقام العربية', rtl: true, arabicNumerals: true, width: 880, height: 520}}
          />
          <LowerThird title="استوديو Shorts" subtitle="يعمل بالكامل دون اتصال بالإنترنت" rtl={true} />
        </>
      )}
    </AbsoluteFill>
  );
};

/**
 * 5-second (150 frames @ 30fps) smoke test combining:
 * Icon + Emoji + Flag + Animated Chart + Scene Transition (`@remotion/transitions`).
 */
export const SmokeScene5s: React.FC = () => {
  const chartData = [
    {label: 'لاباز', value: 3650},
    {label: 'سوكري', value: 2790},
    {label: 'كيتو', value: 2850},
  ];

  return (
    <AbsoluteFill style={{background: '#070b14', direction: 'rtl'}}>
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={85}>
          <AbsoluteFill
            style={{
              background: 'radial-gradient(circle at 50% 35%, #162440 0%, #060a12 100%)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 36,
              padding: 48,
            }}
          >
            <NoiseShapesLayer seed={11} />
            <AnimatedHeadline text="لغز عاصمتي بوليفيا: سوكري ولاباز" rtl={true} />
            <div style={{display: 'flex', gap: 42, alignItems: 'center'}}>
              <Icon name="lucide:landmark" size={136} color="#f5c542" animation="draw" />
              <Emoji char="🏛️" size={136} animation="pop" />
              <Flag code="BO" shape="rect" size={126} animation="pop" />
            </div>
            <LowerThird title="الجمهورية البوليفية" subtitle="عاصمتان في دولة واحدة منذ عام ١٨٩٩" rtl={true} />
          </AbsoluteFill>
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={getTransitionPresentation({
            type: 'wipe',
            direction: 'from-right',
            durationInFrames: 15,
            sfx: 'none',
          })}
          timing={linearTiming({durationInFrames: 15})}
        />
        <TransitionSeries.Sequence durationInFrames={80}>
          <AbsoluteFill
            style={{
              background: 'radial-gradient(circle at 50% 45%, #132238 0%, #050811 100%)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 32,
              padding: 48,
            }}
          >
            <NoiseShapesLayer seed={22} />
            <div style={{display: 'flex', gap: 32, alignItems: 'center'}}>
              <Flag code="EG" shape="round" size={100} animation="pop" />
              <LottieVisual name="checkmark" size={130} />
              <Icon name="lucide:mountain" size={110} color="#38bdf8" animation="float" />
            </div>
            <BarChart
              data={chartData}
              style={{
                title: 'ارتفاع العواصم فوق سطح البحر (متر)',
                rtl: true,
                arabicNumerals: true,
                unit: 'م',
                width: 900,
                height: 580,
              }}
            />
          </AbsoluteFill>
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Short"
      component={Short}
      durationInFrames={150}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{spec: demoSpec}}
      calculateMetadata={({props}: {props: {spec?: Spec} & Partial<Spec>}) => {
        const s = (props.spec ?? (props as unknown as Spec)) || demoSpec;
        return {
          durationInFrames: Math.max(1, s.total || 240),
          fps: s.fps || 30,
          width: s.width || 1080,
          height: s.height || 1920,
        };
      }}
    />
    <Composition
      id="ComponentShowcase"
      component={ComponentShowcase}
      durationInFrames={90}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{mode: 'all'}}
    />
    <Composition
      id="SmokeScene5s"
      component={SmokeScene5s}
      durationInFrames={150}
      fps={30}
      width={1080}
      height={1920}
    />
  </>
);
