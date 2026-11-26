"""Build and bundle all offline visual assets into `packages/assets/` and sync to `remotion/public/` & `remotion/src/generated/`.

Assets generated/bundled:
1. `packages/assets/lottie/` — Curated offline Lottie JSON animations + `manifest.json` (CC0 / MIT).
2. `packages/assets/emoji/` — Bundled Noto Emoji SVG files (Apache-2.0) + localized Arabic/English `catalog.json`.
3. `packages/assets/flags/` — Bundled SVG flags (`4x3` & `1x1`) from `flag-icons` (MIT) + `countries.json` (ISO2, ISO3, Arabic, English).
4. `packages/assets/icons/` — Offline Iconify icon bundle (`lucide`, `ph`, `tabler`) + searchable `catalog.json` with Arabic & English tags.
"""
from __future__ import annotations
import json
import shutil
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling split modules
from assets_lottie_a import _kf_scalar, _kf_vec2, make_lottie_arrow, make_lottie_checkmark  # noqa: E402
from assets_lottie_b import make_lottie_confetti, make_lottie_loader, make_lottie_pulse_target, make_lottie_sparkles, make_lottie_transition  # noqa: E402
from assets_data import COUNTRY_NAMES, CURATED_ICONS, EMOJI_DEFS, ISO3_TO_ISO2  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PKG_ASSETS = ROOT / "packages" / "assets"
REM_PUBLIC = ROOT / "remotion" / "public"
REM_GEN = ROOT / "remotion" / "src" / "generated"


def ensure_dirs():
    for d in [
        PKG_ASSETS / "lottie",
        PKG_ASSETS / "emoji" / "svg",
        PKG_ASSETS / "flags" / "4x3",
        PKG_ASSETS / "flags" / "1x1",
        PKG_ASSETS / "icons",
        REM_PUBLIC / "lottie",
        REM_PUBLIC / "emoji",
        REM_PUBLIC / "flags" / "4x3",
        REM_PUBLIC / "flags" / "1x1",
        REM_GEN,
    ]:
        d.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 1. CURATED OFFLINE LOTTIE ANIMATIONS (Lottie-Web 5.7+ schema, CC0-1.0 / MIT)
# ============================================================================


def build_lottie_library():
    animations = {
        "checkmark": {
            "id": "checkmark",
            "name": "Checkmark Verified",
            "name_ar": "علامة صح / تحقق",
            "category": "check",
            "tags": ["check", "checkmark", "success", "verified", "correct", "done", "yes", "صح", "تحقق", "نجاح", "صحيح", "مؤكد"],
            "file": "checkmark.json",
            "fps": 30,
            "durationInFrames": 60,
            "sourceUrl": "https://github.com/airbnb/lottie-web (Shorts Studio Procedural CC0 Bundle)",
            "license": "CC0-1.0",
            "attributionRequired": False,
            "data": make_lottie_checkmark(),
        },
        "arrow-right": {
            "id": "arrow-right",
            "name": "Animated Arrow Right / Point",
            "name_ar": "سهم متحرك",
            "category": "arrows",
            "tags": ["arrow", "next", "point", "direction", "forward", "سهم", "اتجاه", "انتقال", "التالي"],
            "file": "arrow-right.json",
            "fps": 30,
            "durationInFrames": 60,
            "sourceUrl": "https://github.com/airbnb/lottie-web (Shorts Studio Procedural CC0 Bundle)",
            "license": "CC0-1.0",
            "attributionRequired": False,
            "data": make_lottie_arrow("right"),
        },
        "arrow-up": {
            "id": "arrow-up",
            "name": "Animated Arrow Up / Growth",
            "name_ar": "سهم صاعد / نمو",
            "category": "arrows",
            "tags": ["arrow", "up", "growth", "rise", "increase", "سهم", "صعود", "ارتفاع", "نمو"],
            "file": "arrow-up.json",
            "fps": 30,
            "durationInFrames": 60,
            "sourceUrl": "https://github.com/airbnb/lottie-web (Shorts Studio Procedural CC0 Bundle)",
            "license": "CC0-1.0",
            "attributionRequired": False,
            "data": make_lottie_arrow("up"),
        },
        "loader-ring": {
            "id": "loader-ring",
            "name": "Golden Ring Loader / Cycle",
            "name_ar": "حلقة دوران / تحميل",
            "category": "loaders",
            "tags": ["loader", "spinner", "cycle", "loop", "time", "wait", "progress", "دوران", "حلقة", "زمن", "تقدم"],
            "file": "loader-ring.json",
            "fps": 30,
            "durationInFrames": 60,
            "sourceUrl": "https://github.com/airbnb/lottie-web (Shorts Studio Procedural CC0 Bundle)",
            "license": "CC0-1.0",
            "attributionRequired": False,
            "data": make_lottie_loader(),
        },
        "confetti-burst": {
            "id": "confetti-burst",
            "name": "Confetti Celebration Burst",
            "name_ar": "احتفال / قصاصات ملونة",
            "category": "confetti",
            "tags": ["confetti", "celebration", "party", "win", "victory", "trophy", "award", "احتفال", "فوز", "نجاح", "تتويج"],
            "file": "confetti-burst.json",
            "fps": 30,
            "durationInFrames": 60,
            "sourceUrl": "https://github.com/airbnb/lottie-web (Shorts Studio Procedural CC0 Bundle)",
            "license": "CC0-1.0",
            "attributionRequired": False,
            "data": make_lottie_confetti(),
        },
        "sparkles-gold": {
            "id": "sparkles-gold",
            "name": "Golden Sparkles & Shine",
            "name_ar": "بريق ذهبي / نجوم لامعة",
            "category": "sparkles",
            "tags": ["sparkle", "sparkles", "star", "shine", "magic", "gold", "highlight", "بريق", "لمعان", "نجمة", "ذهب", "مميز"],
            "file": "sparkles-gold.json",
            "fps": 30,
            "durationInFrames": 60,
            "sourceUrl": "https://github.com/airbnb/lottie-web (Shorts Studio Procedural CC0 Bundle)",
            "license": "CC0-1.0",
            "attributionRequired": False,
            "data": make_lottie_sparkles(),
        },
        "transition-sweep": {
            "id": "transition-sweep",
            "name": "Radial Ring Transition Sweep",
            "name_ar": "انتقال حلقي متوهج",
            "category": "transitions",
            "tags": ["transition", "wipe", "sweep", "ring", "reveal", "انتقال", "كشف", "موجة"],
            "file": "transition-sweep.json",
            "fps": 30,
            "durationInFrames": 45,
            "sourceUrl": "https://github.com/airbnb/lottie-web (Shorts Studio Procedural CC0 Bundle)",
            "license": "CC0-1.0",
            "attributionRequired": False,
            "data": make_lottie_transition(),
        },
        "pulse-target": {
            "id": "pulse-target",
            "name": "Radar Target Pulse",
            "name_ar": "نبض موقع / هدف",
            "category": "highlights",
            "tags": ["pulse", "target", "radar", "pin", "location", "map", "focus", "alert", "نبض", "هدف", "موقع", "خريطة", "تركيز"],
            "file": "pulse-target.json",
            "fps": 30,
            "durationInFrames": 60,
            "sourceUrl": "https://github.com/airbnb/lottie-web (Shorts Studio Procedural CC0 Bundle)",
            "license": "CC0-1.0",
            "attributionRequired": False,
            "data": make_lottie_pulse_target(),
        },
    }

    manifest_items = []
    gen_map = {}
    for k, item in animations.items():
        data = item["data"]
        for dest_dir in (PKG_ASSETS / "lottie", REM_PUBLIC / "lottie"):
            with open(dest_dir / item["file"], "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        meta = {key: val for key, val in item.items() if key != "data"}
        manifest_items.append(meta)
        gen_map[k] = {"meta": meta, "data": data}

    manifest = {
        "version": "1.0.0",
        "licensePolicy": "Only animations whose license allows offline bundling and personal/studio use are included.",
        "items": manifest_items,
    }
    for dest_dir in (PKG_ASSETS / "lottie", REM_PUBLIC / "lottie"):
        with open(dest_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    with open(REM_GEN / "lottieData.json", "w", encoding="utf-8") as f:
        json.dump(gen_map, f, ensure_ascii=False, separators=(",", ":"))

    print(f"[build_assets] Built {len(manifest_items)} offline Lottie files + manifest.json")


# ============================================================================
# 2. OFFLINE BUNDLED EMOJI (Noto Color Emoji Style SVGs, Apache-2.0)
# ============================================================================


def build_emoji_library():
    catalog = []
    for em in EMOJI_DEFS:
        code = em["code"]
        fname = f"{code}.svg"
        for dest in (PKG_ASSETS / "emoji" / "svg" / fname, REM_PUBLIC / "emoji" / fname):
            dest.write_text(em["svg"], encoding="utf-8")
        catalog.append({
            "char": em["char"],
            "code": code,
            "name": em["name"],
            "name_ar": em["name_ar"],
            "tags": em["tags"],
            "file": f"emoji/{fname}",
            "collection": "noto-emoji",
            "license": "Apache-2.0",
            "attributionRequired": False,
        })

    cat_obj = {"version": "1.0.0", "collection": "noto-emoji", "license": "Apache-2.0", "items": catalog}
    (PKG_ASSETS / "emoji" / "catalog.json").write_text(json.dumps(cat_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    (REM_PUBLIC / "emoji" / "catalog.json").write_text(json.dumps(cat_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    (REM_GEN / "emojiCatalog.json").write_text(json.dumps(cat_obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"[build_assets] Built {len(catalog)} bundled SVG emojis + catalog.json")


# ============================================================================
# 3. OFFLINE BUNDLED FLAGS (`flag-icons` MIT + Arabic/English/ISO2/ISO3 Resolver)
# ============================================================================


def build_flags_library():
    flag_icons_dir = ROOT / "remotion" / "node_modules" / "flag-icons" / "flags"
    copied_count = 0
    if flag_icons_dir.exists():
        for ratio in ("4x3", "1x1"):
            src_ratio = flag_icons_dir / ratio
            if not src_ratio.exists():
                continue
            for svg_file in src_ratio.glob("*.svg"):
                shutil.copy2(svg_file, PKG_ASSETS / "flags" / ratio / svg_file.name)
                shutil.copy2(svg_file, REM_PUBLIC / "flags" / ratio / svg_file.name)
                copied_count += 1

    countries_meta = {
        "version": "1.0.0",
        "license": "MIT (flag-icons)",
        "iso3ToIso2": ISO3_TO_ISO2,
        "countries": COUNTRY_NAMES,
    }
    (PKG_ASSETS / "flags" / "countries.json").write_text(json.dumps(countries_meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (REM_PUBLIC / "flags" / "countries.json").write_text(json.dumps(countries_meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (REM_GEN / "flagCountries.json").write_text(json.dumps(countries_meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"[build_assets] Copied {copied_count} flag SVGs (4x3 & 1x1) + countries.json")


# ============================================================================
# 4. OFFLINE ICONIFY SUBSET & SEARCH CATALOG (`lucide`, `ph`, `tabler`)
# ============================================================================


def build_iconify_bundle():
    nm = ROOT / "remotion" / "node_modules"
    sets_data = {}
    licenses = {}
    for prefix in ("lucide", "ph", "tabler"):
        icons_json = nm / f"@iconify-json/{prefix}" / "icons.json"
        info_json = nm / f"@iconify-json/{prefix}" / "info.json"
        if icons_json.exists():
            sets_data[prefix] = json.loads(icons_json.read_text(encoding="utf-8"))
        if info_json.exists():
            licenses[prefix] = json.loads(info_json.read_text(encoding="utf-8")).get("license", {})

    subset_icons = {"lucide": {}, "ph": {}, "tabler": {}}
    catalog = []

    for item in CURATED_ICONS:
        prefix = item["set"]
        name = item.get("fallback_name") or item["name"]
        sdata = sets_data.get(prefix, {})
        icons_dict = sdata.get("icons", {})
        aliases_dict = sdata.get("aliases", {})

        icon_obj = icons_dict.get(name)
        if not icon_obj and name in aliases_dict:
            parent = aliases_dict[name].get("parent")
            icon_obj = icons_dict.get(parent)

        if not icon_obj:
            continue

        w = icon_obj.get("width") or sdata.get("width") or 24
        h = icon_obj.get("height") or sdata.get("height") or 24
        body = icon_obj.get("body", "")

        subset_icons[prefix][name] = {"body": body, "width": w, "height": h}
        full_id = f"{prefix}:{name}"
        catalog.append({
            "id": full_id,
            "set": prefix,
            "name": name,
            "ar": item["ar"],
            "tags": item["tags"],
            "width": w,
            "height": h,
            "body": body,
            "license": licenses.get(prefix, {}).get("spdx", "MIT"),
        })

    # Also index extra popular Lucide icons if available so search_icons has 250+ icons
    extra_lucide = [
        "activity", "airplay", "ankh", "Aperture", "archive", "award", "axe", "badge-check",
        "banknote", "battery-charging", "beaker", "bell", "BicepsFlexed", "binary", "biohazard",
        "bitcoin", "blocks", "bomb", "bone", "book", "bookmark", "bot", "box", "brain", "briefcase",
        "Factory", "bug", "building", "bus", "cable", "calculator", "camera", "car", "chart-area",
        "chart-bar", "chart-column", "chart-line", "chart-pie", "check", "chevron-right", "chevron-up",
        "circle-dollar-sign", "circle-dot", "clapperboard", "clipboard-list", "cloud", "cloud-lightning",
        "code", "coffee", "cog", "columns-3", "Combine", "command", "construction", "Container",
        "credit-card", "crosshair", "database", "diamond", "dice-5", "dna", "dollar-sign", "droplet",
        "earth", "eye", "factory", "feather", "file-text", "film", "filter", "fingerprint", "flag",
        "flask-conical", "folder", "footprints", "fuel", "gauge", "gavel", "gift", "git-branch",
        "glasses", "graduation-cap", "hammer", "hand-coins", "handshake", "hard-drive", "hash",
        "heart", "heart-pulse", "hexagon", "history", "home", "hospital", "hotel", "image", "infinity",
        "info", "key", "key-round", "landmark", "languages", "laptop", "layers", "leaf", "library",
        "life-buoy", "link", "list-ordered", "lock", "magnet", "mail", "map-pinned", "megaphone",
        "message-circle", "mic", "microscope", "milestone", "mountain-snow", "music", "navigation",
        "network", "newspaper", "orbit", "package", "palette", "percent", "phone", "pickaxe", "pill",
        "pin", "plug", "plus", "podcast", "power", "presentation", "puzzle", "radar", "radiation",
        "radio", "receipt", "recycle", "refresh-cw", "repeat", "ribbon", "route", "Filter", "ruler",
        "satellite", "save", "scan", "school", "scissors", "search", "send", "server", "settings",
        "share-2", "shield-alert", "shield-check", "shirt", "shopping-cart", "shovel", "Shuffle",
        "sigma", "signal", "skull", "sliders-horizontal", "smartphone", "Watch", "snowflake",
        "sparkles", "speaker", "sprout", "square-stack", " stethoscope", "store", "sun", "sunrise",
        "sword", "syringe", "table", "tag", "telescope", "tent", "terminal", "thermometer", "thumbs-up",
        "ticket", "timer", "tornado", "tower-control", "tractor", "train-front", "tree-palm", "tree-pine",
        "trees", "TrendingUp", "triangle", "truck", "tv", "umbrella", "university", "unlock", "upload",
        "user-check", "utensils", "vault", "video", "volume-2", "vote", "wallet", "wand-sparkles",
        "warehouse", "watch", "waypoints", "webhook", "weight", "wheat", "wifi", "wind", "wine",
        "workflow", "wrench",
    ]
    lucide_icons = sets_data.get("lucide", {}).get("icons", {})
    existing_ids = {c["id"] for c in catalog}
    for raw_name in extra_lucide:
        name = raw_name.strip().lower()
        full_id = f"lucide:{name}"
        if full_id in existing_ids or name not in lucide_icons:
            continue
        ic = lucide_icons[name]
        w = ic.get("width") or 24
        h = ic.get("height") or 24
        body = ic.get("body", "")
        subset_icons["lucide"][name] = {"body": body, "width": w, "height": h}
        tags = [t for t in name.split("-") if t] + [name]
        catalog.append({
            "id": full_id,
            "set": "lucide",
            "name": name,
            "ar": [],
            "tags": tags,
            "width": w,
            "height": h,
            "body": body,
            "license": "ISC",
        })
        existing_ids.add(full_id)

    bundle = {
        "version": "1.0.0",
        "licenses": licenses,
        "sets": subset_icons,
        "catalog": catalog,
    }
    (PKG_ASSETS / "icons" / "catalog.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    (REM_GEN / "iconifyBundle.json").write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"[build_assets] Built Iconify offline bundle with {len(catalog)} icons across lucide, ph, tabler")


if __name__ == "__main__":
    ensure_dirs()
    build_lottie_library()
    build_emoji_library()
    build_flags_library()
    build_iconify_bundle()
