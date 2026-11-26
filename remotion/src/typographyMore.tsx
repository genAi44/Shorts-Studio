// Split from typography.tsx (re-exported there).
import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {formatChartNumber} from './charts';
import type {TypographyComponentSpec} from './schema';
import {AnimatedHeadline, FONT_PAIRINGS, LowerThird, QuoteCard, TitleCard, splitIntoWordsOnly} from './typography';
import type {FontPairingKey} from './typography';

// 5. <BulletListReveal /> — Staggered bullet list reveal
export const BulletListReveal: React.FC<{
  title?: string;
  items: string[];
  rtl?: boolean;
  fontPairing?: FontPairingKey;
  accentColor?: string;
}> = ({
  title,
  items,
  rtl = true,
  fontPairing = 'cairo_inter',
  accentColor = '#f5c542',
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pairing = FONT_PAIRINGS[fontPairing] ?? FONT_PAIRINGS.cairo_inter;

  return (
    <div
      dir={rtl ? 'rtl' : 'ltr'}
      data-component="bullet_list"
      style={{
        padding: '36px 46px',
        borderRadius: 28,
        background: 'rgba(11, 18, 32, 0.90)',
        border: '2px solid rgba(245, 197, 66, 0.3)',
        maxWidth: 880,
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: 18,
        fontFamily: rtl ? pairing.arabicFamily : pairing.englishFamily,
      }}
    >
      {title && (
        <div style={{fontSize: 38, fontWeight: 800, color: accentColor, marginBottom: 6}}>
          {title}
        </div>
      )}
      {items.map((item, idx) => {
        const sp = spring({
          frame: Math.max(0, frame - idx * 6),
          fps,
          config: {damping: 14, stiffness: 150},
        });
        const dx = interpolate(sp, [0, 1], [rtl ? 50 : -50, 0]);
        return (
          <div
            key={idx}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 18,
              opacity: Math.min(1, sp * 1.4),
              transform: `translateX(${dx.toFixed(1)}px)`,
            }}
          >
            <div
              style={{
                width: 18,
                height: 18,
                borderRadius: '50%',
                background: accentColor,
                flexShrink: 0,
              }}
            />
            <div style={{fontSize: 32, fontWeight: 700, color: '#f8fafc', lineHeight: 1.35}}>
              {item}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// 6. <StatCallout /> — Bold numeric callout card
export const StatCallout: React.FC<{
  value: string;
  label: string;
  unit?: string;
  rtl?: boolean;
  arabicNumerals?: boolean;
  fontPairing?: FontPairingKey;
  accentColor?: string;
}> = ({
  value,
  label,
  unit = '',
  rtl = true,
  arabicNumerals = false,
  fontPairing = 'cairo_inter',
  accentColor = '#f5c542',
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pairing = FONT_PAIRINGS[fontPairing] ?? FONT_PAIRINGS.cairo_inter;
  const sp = spring({frame, fps, config: {damping: 13, stiffness: 160}});
  const formattedVal = formatChartNumber(value, arabicNumerals, unit);
  const fSize = formattedVal.length > 10 ? 68 : formattedVal.length > 7 ? 84 : 102;

  return (
    <div
      dir={rtl ? 'rtl' : 'ltr'}
      data-component="stat_callout"
      style={{
        padding: '38px 56px',
        borderRadius: 32,
        background: 'rgba(11, 18, 32, 0.92)',
        border: `3px solid ${accentColor}`,
        boxShadow: '0 20px 52px rgba(0,0,0,0.58)',
        textAlign: 'center',
        opacity: Math.min(1, sp * 1.5),
        transform: `scale(${(0.84 + 0.16 * sp).toFixed(3)})`,
        fontFamily: rtl ? pairing.arabicFamily : pairing.englishFamily,
      }}
    >
      <div style={{fontSize: fSize, fontWeight: 900, color: accentColor, lineHeight: 1.08}}>
        {formattedVal}
      </div>
      <div style={{marginTop: 12, fontSize: 34, fontWeight: 700, color: '#f8fafc'}}>
        {label}
      </div>
    </div>
  );
};

// 7. <StyledCaption /> — Word-highlight, Karaoke, and Pop caption styles (per-word only)
export const StyledCaption: React.FC<{
  text: string;
  mode?: 'word-highlight' | 'karaoke' | 'pop';
  rtl?: boolean;
  fontPairing?: FontPairingKey;
  accentColor?: string;
}> = ({
  text,
  mode = 'word-highlight',
  rtl = true,
  fontPairing = 'cairo_inter',
  accentColor = '#f5c542',
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pairing = FONT_PAIRINGS[fontPairing] ?? FONT_PAIRINGS.cairo_inter;
  const words = splitIntoWordsOnly(text);
  const activeIdx = words.length > 0 ? Math.min(words.length - 1, Math.floor((frame / (fps * 0.35)))) : 0;

  return (
    <div
      dir={rtl ? 'rtl' : 'ltr'}
      data-component="caption_style"
      data-caption-mode={mode}
      style={{
        padding: '16px 38px',
        borderRadius: 999,
        background: 'rgba(11, 18, 32, 0.88)',
        display: 'inline-flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        columnGap: 16,
        rowGap: 8,
        fontFamily: rtl ? pairing.arabicFamily : pairing.englishFamily,
        fontSize: 48,
        fontWeight: 800,
      }}
    >
      {words.map((word, idx) => {
        const isActive = idx === activeIdx;
        const isPassed = idx <= activeIdx;
        const sp = spring({
          frame: Math.max(0, frame - idx * 4),
          fps,
          config: {damping: 11, stiffness: 190},
        });
        if (mode === 'karaoke') {
          return (
            <span
              key={idx}
              style={{
                color: isPassed ? accentColor : 'rgba(255,255,255,0.42)',
                transform: isActive ? 'scale(1.08)' : 'scale(1)',
                display: 'inline-block',
              }}
            >
              {word}
            </span>
          );
        }
        if (mode === 'pop') {
          return (
            <span
              key={idx}
              style={{
                color: isActive ? accentColor : '#ffffff',
                opacity: Math.min(1, sp * 1.6),
                transform: `scale(${(0.5 + 0.5 * sp).toFixed(2)})`,
                display: 'inline-block',
              }}
            >
              {word}
            </span>
          );
        }
        // word-highlight
        return (
          <span
            key={idx}
            style={{
              padding: isActive ? '2px 16px' : '2px 4px',
              borderRadius: 14,
              background: isActive ? accentColor : 'transparent',
              color: isActive ? '#0b1220' : '#ffffff',
              display: 'inline-block',
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};

// Unified dispatcher for TypographyComponentSpec
export const TypographyVisual: React.FC<{spec: TypographyComponentSpec}> = ({spec}) => {
  switch (spec.component) {
    case 'lower_third':
      return (
        <LowerThird
          title={spec.title || ''}
          subtitle={spec.subtitle}
          rtl={spec.rtl}
          fontPairing={spec.fontPairing}
        />
      );
    case 'title_card':
      return (
        <TitleCard
          title={spec.title || ''}
          subtitle={spec.subtitle}
          rtl={spec.rtl}
          fontPairing={spec.fontPairing}
        />
      );
    case 'quote_card':
      return (
        <QuoteCard
          quote={spec.quote || spec.title || ''}
          author={spec.author || spec.subtitle}
          rtl={spec.rtl}
          fontPairing={spec.fontPairing}
        />
      );
    case 'bullet_list':
      return (
        <BulletListReveal
          title={spec.title}
          items={spec.items || []}
          rtl={spec.rtl}
          fontPairing={spec.fontPairing}
        />
      );
    case 'stat_callout':
      return (
        <StatCallout
          value={spec.value || '100'}
          label={spec.title || spec.subtitle || ''}
          unit={spec.unit}
          rtl={spec.rtl}
          arabicNumerals={spec.arabicNumerals}
          fontPairing={spec.fontPairing}
        />
      );
    case 'caption_style':
      return (
        <StyledCaption
          text={spec.title || ''}
          mode={spec.captionMode || 'word-highlight'}
          rtl={spec.rtl}
          fontPairing={spec.fontPairing}
        />
      );
    case 'animated_headline':
    default:
      return (
        <AnimatedHeadline
          text={spec.title || ''}
          rtl={spec.rtl}
          fontPairing={spec.fontPairing}
        />
      );
  }
};
