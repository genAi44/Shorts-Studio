import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import * as CairoFont from '@remotion/google-fonts/Cairo';
import * as NotoKufiArabicFont from '@remotion/google-fonts/NotoKufiArabic';
import * as TajawalFont from '@remotion/google-fonts/Tajawal';
import * as AmiriFont from '@remotion/google-fonts/Amiri';
import * as InterFont from '@remotion/google-fonts/Inter';
import * as MontserratFont from '@remotion/google-fonts/Montserrat';
import {formatChartNumber} from './charts';
import type {TypographyComponentSpec} from './schema';
export {BulletListReveal, StatCallout, StyledCaption, TypographyVisual} from './typographyMore';

// Curated Arabic + English Font Pairings (`@remotion/google-fonts` metadata + local fallback families)
export const FONT_PAIRINGS = {
  cairo_inter: {
    id: 'cairo_inter',
    name: 'Cairo + Inter (Modern Editorial)',
    arabicFamily: `"${CairoFont.fontFamily}", "F_cairo", "Cairo", sans-serif`,
    englishFamily: `"${InterFont.fontFamily}", "Inter", sans-serif`,
    headingWeight: 800,
    bodyWeight: 600,
  },
  kufi_montserrat: {
    id: 'kufi_montserrat',
    name: 'Noto Kufi Arabic + Montserrat (Geometric Broadcast)',
    arabicFamily: `"${NotoKufiArabicFont.fontFamily}", "F_kufi", "Noto Kufi Arabic", sans-serif`,
    englishFamily: `"${MontserratFont.fontFamily}", "Montserrat", sans-serif`,
    headingWeight: 800,
    bodyWeight: 600,
  },
  tajawal_inter: {
    id: 'tajawal_inter',
    name: 'Tajawal + Inter (Clean Documentary)',
    arabicFamily: `"${TajawalFont.fontFamily}", "F_tajawal", "Tajawal", sans-serif`,
    englishFamily: `"${InterFont.fontFamily}", "Inter", sans-serif`,
    headingWeight: 800,
    bodyWeight: 500,
  },
  amiri_classic: {
    id: 'amiri_classic',
    name: 'Amiri + Montserrat (Historical / Heritage)',
    arabicFamily: `"${AmiriFont.fontFamily}", "F_amiri", "Amiri", serif`,
    englishFamily: `"${MontserratFont.fontFamily}", "Montserrat", sans-serif`,
    headingWeight: 700,
    bodyWeight: 600,
  },
} as const;

export type FontPairingKey = keyof typeof FONT_PAIRINGS;

/**
 * Splits text strictly by words (whitespace), NEVER by characters/letters.
 * Essential for Arabic shaping so cursive ligatures are never broken.
 */
export const splitIntoWordsOnly = (text: string): string[] => {
  return (text || '').trim().split(/\s+/).filter(Boolean);
};

// 1. <AnimatedHeadline /> — Strictly per-word animation (NEVER per-letter for Arabic)
export const AnimatedHeadline: React.FC<{
  text: string;
  rtl?: boolean;
  fontPairing?: FontPairingKey;
  color?: string;
  accentColor?: string;
  size?: number;
}> = ({
  text,
  rtl = true,
  fontPairing = 'cairo_inter',
  color = '#f8fafc',
  accentColor = '#f5c542',
  size = 58,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pairing = FONT_PAIRINGS[fontPairing] ?? FONT_PAIRINGS.cairo_inter;
  const words = splitIntoWordsOnly(text);

  return (
    <div
      dir={rtl ? 'rtl' : 'ltr'}
      lang={rtl ? 'ar' : 'en'}
      data-component="animated_headline"
      data-granularity="word"
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        columnGap: 16,
        rowGap: 10,
        fontFamily: rtl ? pairing.arabicFamily : pairing.englishFamily,
        fontWeight: pairing.headingWeight,
        fontSize: size,
        lineHeight: 1.32,
        color,
        padding: '18px 36px',
      }}
    >
      {words.map((word, idx) => {
        const sp = spring({
          frame: Math.max(0, frame - idx * 3),
          fps,
          config: {damping: 13, stiffness: 170, mass: 0.75},
        });
        const y = interpolate(sp, [0, 1], [28, 0]);
        const isHighlight = idx === 0 || /\d|[٠-٩]/.test(word);
        return (
          <span
            key={idx}
            data-word-index={idx}
            style={{
              display: 'inline-block',
              opacity: Math.min(1, sp * 1.5),
              transform: `translateY(${y.toFixed(1)}px) scale(${(0.88 + 0.12 * sp).toFixed(3)})`,
              color: isHighlight ? accentColor : color,
              textShadow: '0 4px 18px rgba(0,0,0,0.55)',
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};

// 2. <LowerThird /> — Broadcast lower-third banner
export const LowerThird: React.FC<{
  title: string;
  subtitle?: string;
  rtl?: boolean;
  fontPairing?: FontPairingKey;
  accentColor?: string;
}> = ({
  title,
  subtitle = '',
  rtl = true,
  fontPairing = 'cairo_inter',
  accentColor = '#f5c542',
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pairing = FONT_PAIRINGS[fontPairing] ?? FONT_PAIRINGS.cairo_inter;
  const sp = spring({frame, fps, config: {damping: 15, stiffness: 150}});
  const slideX = interpolate(sp, [0, 1], [rtl ? 120 : -120, 0]);

  return (
    <div
      dir={rtl ? 'rtl' : 'ltr'}
      data-component="lower_third"
      style={{
        display: 'inline-flex',
        alignItems: ' stretch',
        background: 'rgba(11, 18, 32, 0.92)',
        borderRadius: 20,
        overflow: 'hidden',
        boxShadow: '0 14px 38px rgba(0,0,0,0.55)',
        border: '1.5px solid rgba(255,255,255,0.14)',
        opacity: Math.min(1, sp * 1.4),
        transform: `translateX(${slideX.toFixed(1)}px)`,
        fontFamily: rtl ? pairing.arabicFamily : pairing.englishFamily,
      }}
    >
      <div style={{width: 12, background: accentColor}} />
      <div style={{padding: '18px 32px', display: 'flex', flexDirection: 'column', gap: 4}}>
        <div style={{fontSize: 36, fontWeight: 800, color: '#ffffff', lineHeight: 1.25}}>
          {title}
        </div>
        {subtitle && (
          <div style={{fontSize: 24, fontWeight: 600, color: accentColor, lineHeight: 1.25}}>
            {subtitle}
          </div>
        )}
      </div>
    </div>
  );
};

// 3. <TitleCard /> — Full-impact centered scene title card
export const TitleCard: React.FC<{
  title: string;
  subtitle?: string;
  rtl?: boolean;
  fontPairing?: FontPairingKey;
  accentColor?: string;
}> = ({
  title,
  subtitle = '',
  rtl = true,
  fontPairing = 'cairo_inter',
  accentColor = '#f5c542',
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pairing = FONT_PAIRINGS[fontPairing] ?? FONT_PAIRINGS.cairo_inter;
  const sp = spring({frame, fps, config: {damping: 14, stiffness: 140}});

  return (
    <div
      dir={rtl ? 'rtl' : 'ltr'}
      data-component="title_card"
      style={{
        padding: '44px 56px',
        borderRadius: 32,
        background: 'linear-gradient(145deg, rgba(15, 23, 42, 0.94), rgba(8, 12, 24, 0.96))',
        border: `2.5px solid ${accentColor}`,
        boxShadow: '0 24px 60px rgba(0,0,0,0.65)',
        textAlign: 'center',
        maxWidth: 900,
        opacity: Math.min(1, sp * 1.4),
        transform: `scale(${(0.88 + 0.12 * sp).toFixed(3)})`,
        fontFamily: rtl ? pairing.arabicFamily : pairing.englishFamily,
      }}
    >
      <AnimatedHeadline
        text={title}
        rtl={rtl}
        fontPairing={fontPairing}
        accentColor={accentColor}
        size={56}
      />
      {subtitle && (
        <div
          style={{
            marginTop: 14,
            fontSize: 30,
            fontWeight: 600,
            color: '#cbd5e1',
          }}
        >
          {subtitle}
        </div>
      )}
    </div>
  );
};

// 4. <QuoteCard /> — Styled historical/editorial quotation card
export const QuoteCard: React.FC<{
  quote: string;
  author?: string;
  rtl?: boolean;
  fontPairing?: FontPairingKey;
  accentColor?: string;
}> = ({
  quote,
  author = '',
  rtl = true,
  fontPairing = 'amiri_classic',
  accentColor = '#f5c542',
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pairing = FONT_PAIRINGS[fontPairing] ?? FONT_PAIRINGS.amiri_classic;
  const sp = spring({frame, fps, config: {damping: 15, stiffness: 140}});
  const words = splitIntoWordsOnly(quote);

  return (
    <div
      dir={rtl ? 'rtl' : 'ltr'}
      data-component="quote_card"
      style={{
        padding: '42px 52px',
        borderRadius: 28,
        background: 'rgba(11, 18, 32, 0.92)',
        borderRight: rtl ? `8px solid ${accentColor}` : undefined,
        borderLeft: !rtl ? `8px solid ${accentColor}` : undefined,
        boxShadow: '0 20px 50px rgba(0,0,0,0.55)',
        maxWidth: 880,
        opacity: Math.min(1, sp * 1.4),
        fontFamily: rtl ? pairing.arabicFamily : pairing.englishFamily,
      }}
    >
      <div style={{fontSize: 64, lineHeight: 0.7, color: accentColor, marginBottom: 12}}>
        {rtl ? '«' : '“'}
      </div>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          columnGap: 12,
          rowGap: 8,
          fontSize: 42,
          fontWeight: 700,
          color: '#f8fafc',
          lineHeight: 1.45,
        }}
      >
        {words.map((w, i) => {
          const wsp = spring({
            frame: Math.max(0, frame - i * 2),
            fps,
            config: {damping: 14, stiffness: 160},
          });
          return (
            <span key={i} style={{opacity: Math.min(1, wsp * 1.5)}}>
              {w}
            </span>
          );
        })}
      </div>
      {author && (
        <div
          style={{
            marginTop: 22,
            fontSize: 28,
            fontWeight: 700,
            color: accentColor,
          }}
        >
          — {author}
        </div>
      )}
    </div>
  );
};

