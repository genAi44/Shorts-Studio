import iconifyBundle from './generated/iconifyBundle.json';
import emojiCatalog from './generated/emojiCatalog.json';
import lottieDataBundle from './generated/lottieData.json';
import {resolveCountryIso2} from './flag';
import {DrawChartInput, DrawChartSchema} from './schema';
import {pickSceneTransitions} from './transitions';

export interface SearchIconsArgs {
  query: string;
  set?: 'lucide' | 'ph' | 'tabler';
  limit?: number;
}

export interface IconMatch {
  id: string;
  set: string;
  name: string;
  score: number;
  tags: string[];
  ar: string[];
  license: string;
}

const SEMANTIC_SYNONYMS: Record<string, string[]> = {
  pyramid: ['lucide:pyramid', 'lucide:landmark', 'tabler:building-monument'],
  هرم: ['lucide:pyramid', 'lucide:landmark'],
  أهرامات: ['lucide:pyramid', 'lucide:landmark'],
  capital: ['lucide:landmark', 'lucide:building-2', 'tabler:map-pin-filled'],
  عاصمة: ['lucide:landmark', 'lucide:building-2', 'lucide:crown'],
  war: ['lucide:swords', 'lucide:shield', 'ph:sword'],
  حرب: ['lucide:swords', 'lucide:shield', 'ph:sword'],
  معركة: ['lucide:swords', 'ph:sword'],
  money: ['lucide:coins', 'lucide:banknote', 'ph:treasure-chest'],
  مال: ['lucide:coins', 'lucide:banknote'],
  اقتصاد: ['lucide:trending-up', 'lucide:coins', 'lucide:bar-chart-3'],
  map: ['lucide:map', 'lucide:globe', 'lucide:map-pin'],
  خريطة: ['lucide:map', 'lucide:globe', 'lucide:map-pin'],
  law: ['lucide:scale', 'lucide:scroll-text', 'lucide:gavel'],
  دستور: ['lucide:scroll-text', 'lucide:scale', 'ph:scroll'],
  قانون: ['lucide:scale', 'lucide:gavel'],
  people: ['lucide:users', 'lucide:user-round'],
  سكان: ['lucide:users', 'lucide:user-round'],
  time: ['lucide:clock', 'lucide:hourglass', 'tabler:timeline'],
  زمن: ['lucide:hourglass', 'lucide:clock', 'tabler:timeline'],
  تاريخ: ['lucide:scroll-text', 'lucide:hourglass', 'lucide:landmark'],
};

/**
 * 1. `search_icons({ query, set? })`
 * Searches offline Iconify catalog (`lucide`, `ph`, `tabler`) by exact name, Arabic/English tags,
 * and semantic synonym mapping so agents never invent icon names.
 */
export const search_icons = ({query, set, limit = 5}: SearchIconsArgs): IconMatch[] => {
  const q = (query || '').trim().toLowerCase();
  const tokens = q.split(/[\s,_-]+/).filter(Boolean);
  const catalog: any[] = (iconifyBundle as any).catalog || [];
  const filtered = set ? catalog.filter((c) => c.set === set) : catalog;

  const synonymHits = new Set<string>();
  for (const [k, ids] of Object.entries(SEMANTIC_SYNONYMS)) {
    if (q.includes(k) || k.includes(q)) {
      ids.forEach((id) => synonymHits.add(id));
    }
  }

  const scored = filtered.map((item) => {
    let score = 0;
    const itemName = item.name.toLowerCase();
    const itemId = item.id.toLowerCase();
    const tags: string[] = (item.tags || []).map((t: string) => t.toLowerCase());
    const arTags: string[] = item.ar || [];

    if (itemId === q || itemName === q) score += 100;
    if (synonymHits.has(item.id)) score += 75;
    if (itemName.includes(q) && q.length >= 2) score += 50;
    for (const ar of arTags) {
      if (ar === q) score += 90;
      else if (q.includes(ar) || ar.includes(q)) score += 60;
    }
    for (const tag of tags) {
      if (tag === q) score += 70;
      else if (tokens.some((tk) => tag.includes(tk) || tk.includes(tag))) score += 30;
    }
    return {
      id: item.id,
      set: item.set,
      name: item.name,
      score,
      tags: item.tags || [],
      ar: arTags,
      license: item.license || 'MIT',
    };
  });

  scored.sort((a, b) => b.score - a.score);
  const positive = scored.filter((s) => s.score > 0);
  if (positive.length > 0) return positive.slice(0, limit);
  return scored.slice(0, limit);
};

/**
 * 2. `search_emoji({ query })`
 * Searches offline bundled Noto Emoji catalog using localized Arabic & English names/tags.
 */
export const search_emoji = ({query, limit = 5}: {query: string; limit?: number}) => {
  const q = (query || '').trim().toLowerCase();
  const items: any[] = (emojiCatalog as any).items || [];
  const scored = items.map((em) => {
    let score = 0;
    if (em.char === query.trim() || em.code === q) score += 120;
    if (em.name.toLowerCase().includes(q) && q) score += 80;
    if (em.name_ar.includes(query.trim()) && query.trim()) score += 90;
    for (const t of em.tags || []) {
      const tl = String(t).toLowerCase();
      if (tl === q) score += 75;
      else if (q && (tl.includes(q) || q.includes(tl))) score += 40;
    }
    return {...em, score};
  });
  scored.sort((a, b) => b.score - a.score);
  const positive = scored.filter((s) => s.score > 0);
  return (positive.length ? positive : scored).slice(0, limit);
};

/**
 * 3. `resolve_flag(query)`
 * Resolves Arabic/English country names or ISO2/ISO3 codes to `{ code, fileRect, fileRound }`.
 */
export const resolve_flag = (query: string) => {
  const iso2 = resolveCountryIso2(query);
  return {
    code: iso2.toUpperCase(),
    iso2,
    fileRect: `flags/4x3/${iso2}.svg`,
    fileRound: `flags/1x1/${iso2}.svg`,
  };
};

/**
 * 4. `search_lottie({ query })`
 * Searches the curated local Lottie manifest in `packages/assets/lottie/manifest.json`.
 */
export const search_lottie = ({query, limit = 4}: {query: string; limit?: number}) => {
  const q = (query || '').trim().toLowerCase();
  const entries = Object.values(lottieDataBundle as Record<string, {meta: any}>).map((e) => e.meta);
  const scored = entries.map((m) => {
    let score = 0;
    if (m.id.toLowerCase() === q || m.category.toLowerCase() === q) score += 100;
    if (m.name.toLowerCase().includes(q) && q) score += 65;
    if ((m.name_ar || '').includes(query.trim()) && query.trim()) score += 80;
    for (const t of m.tags || []) {
      const tl = String(t).toLowerCase();
      if (tl === q) score += 75;
      else if (q && (tl.includes(q) || q.includes(tl))) score += 40;
    }
    return {...m, score};
  });
  scored.sort((a, b) => b.score - a.score);
  const positive = scored.filter((s) => s.score > 0);
  return (positive.length ? positive : scored).slice(0, limit);
};

/**
 * 5. `draw_chart(input)`
 * Validates chart configuration with Zod (`DrawChartSchema`) and returns a ready-to-render visual spec.
 */
export const draw_chart = (input: unknown): {kind: 'chart'; spec: DrawChartInput} => {
  const parsed = DrawChartSchema.parse(input);
  return {
    kind: 'chart',
    spec: parsed,
  };
};

export {pickSceneTransitions};

