---
name: typography-components
description: Reusable Arabic/English typography and layout components (<LowerThird />, <TitleCard />, <QuoteCard />, <BulletListReveal />, <StatCallout />, <StyledCaption />, <AnimatedHeadline />) with @remotion/google-fonts pairings and strict RTL word-level animation.
---

# Typography & Layout Components (`typography-components`)

## Mandatory Arabic Typography Rule
- **Animate per word, NEVER per letter for Arabic**: Splitting Arabic strings into individual characters breaks cursive glyph joining (`ب + ي + ت` vs `بيت`). Always use `splitIntoWordsOnly(text)` (`text.trim().split(/\s+/)`) so every word remains a single intact DOM text node.

## Curated Font Pairings (`FONT_PAIRINGS`)
- `cairo_inter` — **Cairo + Inter** (Modern Editorial, default)
- `kufi_montserrat` — **Noto Kufi Arabic + Montserrat** (Geometric Broadcast)
- `tajawal_inter` — **Tajawal + Inter** (Clean Documentary)
- `amiri_classic` — **Amiri + Montserrat** (Historical / Heritage Quotations)

---

## Worked Examples

### 1. Per-Word Animated Headline (`<AnimatedHeadline />`)

```tsx
import {AnimatedHeadline} from './typography';

<AnimatedHeadline
  text="لماذا تملك بوليفيا عاصمتين رسميتين؟"
  rtl={true}
  fontPairing="cairo_inter"
  accentColor="#f5c542"
/>
```

### 2. Lower Third, Quote Card, Bullet List & Stat Callout

```tsx
import {LowerThird, QuoteCard, BulletListReveal, StatCallout, StyledCaption} from './typography';

<LowerThird title="مدينة لاباز — بوليفيا" subtitle="أعلى مقر حكومي في العالم (٣٬٦٥٠ م)" rtl={true} />

<QuoteCard quote="الجغرافيا هي القدر الذي يصنع التاريخ" author="وثائق التاريخ المعاصر" rtl={true} fontPairing="amiri_classic" />

<BulletListReveal
  title="الحقائق الثلاث الحاسمة"
  items={['سوكري العاصمة الدستورية منذ ١٨٢٥', 'لاباز مقر الحكومة والبرلمان منذ ١٨٩٩', 'دستور ٢٠٠٩ ثبّت التسوية التاريخية']}
  rtl={true}
/>

<StatCallout value="3650" label="ارتفاع لاباز فوق سطح البحر" unit="م" arabicNumerals={true} rtl={true} />

<StyledCaption text="اكتشف سر العاصمتين في ستين ثانية" mode="word-highlight" rtl={true} />
```

