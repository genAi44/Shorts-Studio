# Entity → visual system

**Rule:** every entity named in the narration gets a visual that suits its type, in the scene of its sentence.
Geography is the strongest case: any place, from a village to the whole Earth, gets a map.

Code: [`pipeline/entities.py`](../pipeline/entities.py) (registry, extraction, validation, enforcement) ·
map overlay: [`pipeline/geo_overlay.py`](../pipeline/geo_overlay.py) + [`remotion/src/mapEngine.tsx`](../remotion/src/mapEngine.tsx) ·
new beats: [`remotion/src/entityBeats.tsx`](../remotion/src/entityBeats.tsx).

## Flow

1. **Extract** – `entities.extract_script(script)`: ONE llm call returns typed entities per sentence (JSON). No regex on Arabic.
   Cached in `data/entity_cache.json` by hash of the sentences. If the call fails, a visible warning is recorded and only
   the legacy dictionary matcher runs.
2. **Validate locally** – places against `data/geodata.db` (Natural Earth countries/rivers/lakes, GeoNames cities);
   unknown places go to Nominatim (1 req/s, cached in `data/nominatim_cache.json`) **with a visible warning**;
   the entity text must be a whole-word span of its sentence (`find_span`), otherwise it is dropped (warning).
3. **Plan check** – `direct.apply_beats` adds `entities.plan_errors` to the director's errors; one retry.
4. **Enforce** – `rem.build_spec` calls `entities.ensure_visuals`: a required beat-channel entity with no suitable beat on
   screen when it is spoken gets an **inserted fallback shot** (the beat under it is hidden for the shot). Places, terrain,
   routes, conflicts and empires go to the map overlay through `entities.geo_mentions`.
5. **Gate** – `entities.spec_gaps(spec)` re-checks the finished spec; `visual_qa.audit_spec` fails on any gap
   (`entity_gaps` in `qa_report.json`). `tests/test_entities.py` fails the same way.

Every fallback is recorded (`config.record_fallback`), marked `_fallback: true` in the spec, listed in
`qa_report.json`, returned by the API (`/api/job/<id>` → `warnings`, and in the result) and shown in the UI.

## The registry

`ENTITY_REGISTRY[id] = EntityType(id, label, llm_hint, channel, kinds, required, fallback, scales)`

| field | meaning |
|---|---|
| `llm_hint` | what the extractor should look for (the JSON shape lives in `EXTRACT_SYSTEM`) |
| `channel` | `overlay` = drawn by the map overlay, `beat` = needs a beat whose kind is in `kinds` |
| `required` | the gate fails when the visual is missing |
| `fallback(entity, sentence)` | returns the beat to insert when the plan missed it |

Built-in types: `place` (village/town/city/capital/region/country/continent/ocean/globe), `terrain`, `conflict`, `route`,
`time`, `quantity`, `person`, `nature`, `empire`, `flag` (derived from country places, never extracted).

## Adding a new type (one entry)

```python
from pipeline.entities import EntityType, register
register(EntityType("recipe", "وصفة", "a food recipe (name_ar, name_en)", channel="beat",
                    kinds=("photo", "icons"),
                    fallback=lambda e, s: {"kind": "photo", "query": e["name_en"], "text": e["name_ar"]}))
```

Then add the JSON shape of the new type to `EXTRACT_SYSTEM`. If it needs a new component: add the beat kind in
`direct.KINDS` + `normalize_beat` + `BEAT_RULES`, in `spec_schema.json` (then `python scripts/generate_schema.py`),
a React component in `remotion/src/` and a `case` in `BeatView`. `tests/test_contracts.py` fails if one of those is missing.

## Honest limits

- Terrain: rivers and lakes come from Natural Earth; mountains, deserts, straits and islands are marked from the model's
  coordinates and labelled approximate. Historical empires are an approximate marked area (no historical borders data).
- Photos for people / nature need the licensed-photo resolver; without one the card shows a symbolic silhouette / icon.
