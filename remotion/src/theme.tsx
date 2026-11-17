import {createContext, useContext} from 'react';
import {Easing} from 'remotion';
import type {RGB, Style} from './types';

const lum = (c: RGB) => 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2];
export const rgba = (c: RGB, a = 1) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;
export const on = (c: RGB) => (lum(c) > 150 ? 'rgb(22,18,14)' : 'rgb(255,255,255)');

export const FONT_FILES: Record<string, string> = {
  kufi: 'NotoKufi.ttf', cairo: 'Cairo.ttf', changa: 'Changa.ttf', messiri: 'ElMessiri.ttf', reem: 'ReemKufi.ttf',
  markazi: 'Markazi.ttf', amiri: 'Amiri-Bold.ttf', lalezar: 'Lalezar.ttf', tajawal: 'Tajawal-ExtraBold.ttf',
};

// الثيم الوحيد للمشروع: كل الألوان والمنحنيات والخطوط تأتي من هنا (من ستايل الفيديو).
export const makeTheme = (st: Style) => {
  const p = st.palette;
  const tok = (name: string | undefined): RGB => {
    switch (name) {
      case 'accent2': return p.accent2;
      case 'text': return p.text;
      case 'c1': return p.c1;
      case 'c2': return p.c2;
      case 'ctx': return p.ctx;
      default:
        if (name && /^hl\d$/.test(name)) return p.hl[Number(name[2]) % p.hl.length];
        return p.accent;
    }
  };
  // Cinematic lighting presets per scene mood
  const lighting = {
    keyLight: st.dark ? `rgba(255,220,180,0.12)` : `rgba(255,255,240,0.15)`,
    fillLight: st.dark ? `rgba(100,140,200,0.08)` : `rgba(200,220,255,0.10)`,
    rimLight: st.dark ? `rgba(255,200,100,0.20)` : `rgba(255,255,255,0.25)`,
    ambientOcclusion: st.dark ? 'rgba(0,0,0,0.35)' : 'rgba(0,0,0,0.15)',
  };
  return {
    st, p, dark: st.dark, family: `F_${st.font}`, family2: `F2_${st.font2}`, weight: st.weight, pace: st.pace, tok,
    zoneCy: ({top: 870, center: 870, upper: 920, lower: 650} as Record<string, number>)[st.headline.pos] ?? 870,
    headY: ({top: 250, center: 250, upper: 340, lower: 1130} as Record<string, number>)[st.headline.pos] ?? 250,
    // Caption always stays in the bottom 25% safe zone (y >= 1440 on 1920px canvas)
    capY: Math.max(1440, st.headline.pos === 'lower' ? Math.max(st.caption.y, 1440) : st.caption.y),
    ease: {
      out: Easing.bezier(0.16, 1, 0.3, 1),
      in: Easing.bezier(0.7, 0, 0.84, 0.35),
      inOut: Easing.bezier(0.65, 0, 0.35, 1),
    },
    shadow: st.dark ? '0 4px 20px rgba(0,0,0,0.6)' : '0 3px 12px rgba(255,255,255,0.6)',
    // Cinematic lighting
    lighting,
    // Vignette for cinematic depth
    vignette: st.dark 
      ? 'radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.55) 100%)'
      : 'radial-gradient(ellipse at center, transparent 40%, rgba(30,25,20,0.35) 100%)',
    // Film grain overlay
    grainIntensity: 0.06,
  };
};
export type Theme = ReturnType<typeof makeTheme>;
export const ThemeCtx = createContext<Theme>(null as unknown as Theme);
export const useTheme = () => useContext(ThemeCtx);

// سرعة الحركة للمشهد (الـ HOOK أسرع) وحالة «الثبات» لمشهد الـ LOOP.
export const MotionCtx = createContext({speed: 1, settled: false});

// تخطيط الشاشة المقسمة: صورة في الأعلى وخريطة تفاعلية عريضة في الأسفل
export const MapLayoutCtx = createContext({splitBottom: false});
