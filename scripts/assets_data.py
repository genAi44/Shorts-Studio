"""Split from `scripts/build_assets.py` (re-exported there); see that module."""
from __future__ import annotations


EMOJI_DEFS = [
    {
        "char": "🏛️", "code": "1f3db", "name": "classical building", "name_ar": "مبنى كلاسيكي / معلم تاريخي",
        "tags": ["history", "monument", "museum", "parliament", "capital", "state", "empire", "تاريخ", "معلم", "متحف", "برلمان", "عاصمة", "دولة", "حضارة"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><polygon points="64,12 12,42 116,42" fill="#e2c07d" stroke="#b08d44" stroke-width="4"/><rect x="16" y="42" width="96" height="10" rx="2" fill="#d4af37"/><rect x="24" y="52" width="12" height="50" fill="#f4e8c1"/><rect x="46" y="52" width="12" height="50" fill="#f4e8c1"/><rect x="70" y="52" width="12" height="50" fill="#f4e8c1"/><rect x="92" y="52" width="12" height="50" fill="#f4e8c1"/><rect x="14" y="102" width="100" height="12" rx="3" fill="#c5a059"/></svg>'
    },
    {
        "char": "🕌", "code": "1f54c", "name": "mosque", "name_ar": "مسجد / جامع",
        "tags": ["mosque", "islam", "dome", "minaret", "arab", "heritage", "مسجد", "جامع", "إسلام", "قبة", "مئذنة", "تراث"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><path d="M36 68 C36 36, 92 36, 92 68 Z" fill="#f5c542"/><rect x="28" y="68" width="72" height="44" rx="4" fill="#f4e8c1"/><rect x="54" y="84" width="20" height="28" rx="10" fill="#2c3e50"/><rect x="14" y="28" width="12" height="84" rx="3" fill="#e2c07d"/><polygon points="20,14 12,28 28,28" fill="#f5c542"/><circle cx="64" cy="28" r="5" fill="#f5c542"/></svg>'
    },
    {
        "char": "👑", "code": "1f451", "name": "crown", "name_ar": "تاج ملكي",
        "tags": ["crown", "king", "queen", "empire", "rule", "power", "royal", "throne", "تاج", "ملك", "إمبراطورية", "حكم", "سلطة", "عرش"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><polygon points="16,96 24,36 48,64 64,24 80,64 104,36 112,96" fill="#ffd700" stroke="#d49b00" stroke-width="4" stroke-linejoin="round"/><rect x="16" y="96" width="96" height="14" rx="5" fill="#e6a800"/><circle cx="64" cy="20" r="7" fill="#ff4d4d"/><circle cx="24" cy="32" r="6" fill="#33ccff"/><circle cx="104" cy="32" r="6" fill="#33ccff"/></svg>'
    },
    {
        "char": "⚔️", "code": "2694", "name": "crossed swords", "name_ar": "سيفان متقاطعان / معركة",
        "tags": ["war", "battle", "sword", "conflict", "army", "military", "fight", "حرب", "معركة", "سيف", "صراع", "جيش", "نزاع"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><g stroke-linecap="round"><line x1="22" y1="106" x2="104" y2="24" stroke="#d8e2ef" stroke-width="12"/><line x1="106" y1="106" x2="24" y2="24" stroke="#b8c7d9" stroke-width="12"/><line x1="20" y1="84" x2="44" y2="108" stroke="#f5c542" stroke-width="8"/><line x1="84" y1="108" x2="108" y2="84" stroke="#f5c542" stroke-width="8"/></g></svg>'
    },
    {
        "char": "🌍", "code": "1f30d", "name": "globe europe-africa", "name_ar": "الكرة الأرضية / العالم",
        "tags": ["world", "earth", "globe", "planet", "global", "geography", "عالم", "الأرض", "كوكب", "جغرافيا", "دولي"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><circle cx="64" cy="64" r="52" fill="#2b7de9"/><path d="M46,24 C62,22 78,32 82,46 C86,60 74,78 66,96 C58,104 44,90 42,74 C40,58 34,34 46,24 Z" fill="#47b86e"/><path d="M84,28 C96,36 106,52 102,68 C94,66 88,54 84,28 Z" fill="#47b86e"/></svg>'
    },
    {
        "char": "🗺️", "code": "1f5fa", "name": "world map", "name_ar": "خريطة العالم",
        "tags": ["map", "atlas", "borders", "region", "country", "location", "خريطة", "حدود", "منطقة", "دولة", "أطلس"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><polygon points="14,26 46,18 82,28 114,20 114,102 82,110 46,100 14,108" fill="#f2deb8" stroke="#b59257" stroke-width="4"/><line x1="46" y1="18" x2="46" y2="100" stroke="#c8a870" stroke-width="3"/><line x1="82" y1="28" x2="82" y2="110" stroke="#c8a870" stroke-width="3"/><circle cx="34" cy="56" r="10" fill="#47b86e"/><path d="M56,42 L74,48 L70,78 L54,70 Z" fill="#47b86e"/><circle cx="96" cy="64" r="11" fill="#47b86e"/></svg>'
    },
    {
        "char": "📍", "code": "1f4cd", "name": "round pushpin", "name_ar": "دبوس موقع",
        "tags": ["pin", "location", "point", "city", "capital", "place", "here", "موقع", "نقطة", "مدينة", "عاصمة", "مكان"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><path d="M64,14 C38,14 22,32 22,54 C22,82 64,116 64,116 C64,116 106,82 106,54 C106,32 90,14 64,14 Z" fill="#e53935"/><circle cx="64" cy="52" r="18" fill="#ffffff"/></svg>'
    },
    {
        "char": "📊", "code": "1f4ca", "name": "bar chart", "name_ar": "مخطط بياني / إحصائيات",
        "tags": ["chart", "stats", "statistics", "data", "numbers", "economy", "ranking", "إحصائيات", "بيانات", "أرقام", "مخطط", "ترتيب"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect x="18" y="64" width="22" height="46" rx="4" fill="#3b82f6"/><rect x="53" y="36" width="22" height="74" rx="4" fill="#10b981"/><rect x="88" y="18" width="22" height="92" rx="4" fill="#f59e0b"/><line x1="10" y1="112" x2="118" y2="112" stroke="#cbd5e1" stroke-width="6" stroke-linecap="round"/></svg>'
    },
    {
        "char": "📈", "code": "1f4c8", "name": "chart increasing", "name_ar": "نمو صاعد / ارتفاع",
        "tags": ["growth", "trend", "increase", "rise", "economy", "profit", "نمو", "ارتفاع", "صعود", "اقتصاد", "تطور"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect x="14" y="14" width="100" height="100" rx="12" fill="#1e293b" stroke="#475569" stroke-width="4"/><polyline points="26,92 52,66 72,76 102,34" fill="none" stroke="#22c55e" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/><polyline points="82,34 102,34 102,54" fill="none" stroke="#22c55e" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    },
    {
        "char": "💰", "code": "1f4b0", "name": "money bag", "name_ar": "ثروة / أموال",
        "tags": ["money", "wealth", "gold", "economy", "trade", "budget", "billion", "مال", "ثروة", "ذهب", "اقتصاد", "تجارة", "مليار"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><path d="M46,34 L82,34 L98,64 C108,88 94,114 64,114 C34,114 20,88 30,64 Z" fill="#eab308" stroke="#ca8a04" stroke-width="4"/><polygon points="48,16 80,16 74,34 54,34" fill="#facc15"/><text x="64" y="88" font-size="42" font-family="sans-serif" font-weight="bold" fill="#713f12" text-anchor="middle">$</text></svg>'
    },
    {
        "char": "🏆", "code": "1f3c6", "name": "trophy", "name_ar": "كأس البطولة / المركز الأول",
        "tags": ["trophy", "winner", "first", "champion", "award", "top", "record", "كأس", "بطل", "الأول", "صدارة", "جائزة", "قياسي"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><path d="M36,20 H92 V56 C92,76 78,88 64,88 C50,88 36,76 36,56 Z" fill="#fbbf24" stroke="#d97706" stroke-width="4"/><path d="M36,28 H20 V48 C20,60 28,66 36,66" fill="none" stroke="#fbbf24" stroke-width="8"/><path d="M92,28 H108 V48 C108,60 100,66 92,66" fill="none" stroke="#fbbf24" stroke-width="8"/><rect x="54" y="88" width="20" height="18" fill="#d97706"/><rect x="38" y="106" width="52" height="12" rx="4" fill="#92400e"/></svg>'
    },
    {
        "char": "⚡", "code": "26a1", "name": "high voltage", "name_ar": "صاعقة / طاقة / سرعة",
        "tags": ["lightning", "energy", "power", "shock", "fast", "electric", "tension", "برق", "طاقة", "قوة", "صدمة", "سرعة", "مفاجأة"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><polygon points="74,10 26,72 62,72 52,118 102,54 66,54" fill="#facc15" stroke="#eab308" stroke-width="4" stroke-linejoin="round"/></svg>'
    },
    {
        "char": "🔥", "code": "1f525", "name": "fire", "name_ar": "نار / شعلة",
        "tags": ["fire", "flame", "hot", "spark", "energy", "crisis", "نار", "لهب", "شعلة", "حرارة", "أزمة"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><path d="M66,12 C88,36 104,58 100,84 C96,106 80,118 64,118 C46,118 28,104 28,80 C28,58 46,44 52,32 C56,46 64,46 66,12 Z" fill="#f97316"/><path d="M64,54 C76,68 82,80 78,96 C74,108 68,114 64,114 C54,114 46,104 48,90 C50,78 58,68 64,54 Z" fill="#facc15"/></svg>'
    },
    {
        "char": "⭐", "code": "2b50", "name": "star", "name_ar": "نجمة",
        "tags": ["star", "rating", "highlight", "featured", "special", "نجمة", "مميز", "تقييم", "تألق"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><polygon points="64,12 79,46 116,50 88,75 96,112 64,93 32,112 40,75 12,50 49,46" fill="#fbbf24" stroke="#d97706" stroke-width="4" stroke-linejoin="round"/></svg>'
    },
    {
        "char": "⏳", "code": "23f3", "name": "hourglass", "name_ar": "ساعة رملية / زمن",
        "tags": ["time", "history", "century", "era", "year", "ancient", "wait", "زمن", "وقت", "قرن", "عصر", "تاريخ", "سنة"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect x="28" y="14" width="72" height="10" rx="4" fill="#b45309"/><rect x="28" y="104" width="72" height="10" rx="4" fill="#b45309"/><path d="M36,24 L92,24 L68,64 L92,104 L36,104 L60,64 Z" fill="#fef3c7" stroke="#d97706" stroke-width="4"/><polygon points="44,98 84,98 64,74" fill="#f59e0b"/></svg>'
    },
    {
        "char": "📜", "code": "1f4dc", "name": "scroll", "name_ar": "مخطوطة تاريخية / وثيقة",
        "tags": ["scroll", "constitution", "law", "treaty", "document", "history", "text", "مخطوطة", "دستور", "معاهدة", "وثيقة", "قانون", "تاريخ"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect x="28" y="20" width="72" height="88" rx="6" fill="#fde68a" stroke="#b45309" stroke-width="4"/><rect x="20" y="14" width="88" height="14" rx="7" fill="#d97706"/><rect x="20" y="100" width="88" height="14" rx="7" fill="#d97706"/><line x1="42" y1="46" x2="86" y2="46" stroke="#92400e" stroke-width="5" stroke-linecap="round"/><line x1="42" y1="64" x2="86" y2="64" stroke="#92400e" stroke-width="5" stroke-linecap="round"/><line x1="42" y1="82" x2="72" y2="82" stroke="#92400e" stroke-width="5" stroke-linecap="round"/></svg>'
    },
    {
        "char": "⚖️", "code": "2696", "name": "balance scale", "name_ar": "ميزان العدالة / القضاء",
        "tags": ["justice", "law", "court", "constitution", "balance", "compare", "عدالة", "قضاء", "قانون", "محكمة", "دستور", "ميزان"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><line x1="64" y1="20" x2="64" y2="108" stroke="#fbbf24" stroke-width="8"/><line x1="24" y1="40" x2="104" y2="40" stroke="#fbbf24" stroke-width="7"/><polygon points="14,76 42,76 28,40" fill="none" stroke="#fde68a" stroke-width="4"/><polygon points="86,76 114,76 100,40" fill="none" stroke="#fde68a" stroke-width="4"/><path d="M12,76 Q28,92 44,76 Z" fill="#f59e0b"/><path d="M84,76 Q100,92 116,76 Z" fill="#f59e0b"/><rect x="42" y="104" width="44" height="10" rx="4" fill="#d97706"/></svg>'
    },
    {
        "char": "💡", "code": "1f4a1", "name": "light bulb", "name_ar": "فكرة / اكتشاف",
        "tags": ["idea", "fact", "secret", "discovery", "knowledge", "smart", "فكرة", "حقيقة", "سر", "اكتشاف", "معرفة", "ذكاء"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><path d="M64,16 C40,16 26,34 26,54 C26,68 36,78 44,88 H84 C92,78 102,68 102,54 C102,34 88,16 64,16 Z" fill="#fde047" stroke="#eab308" stroke-width="4"/><rect x="46" y="90" width="36" height="12" rx="4" fill="#94a3b8"/><rect x="52" y="104" width="24" height="10" rx="4" fill="#64748b"/></svg>'
    },
    {
        "char": "🔬", "code": "1f52c", "name": "microscope", "name_ar": "مجهر / بحث علمي",
        "tags": ["science", "research", "lab", "biology", "medicine", "study", "علم", "بحث", "مختبر", "طب", "دراسة"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect x="24" y="104" width="80" height="12" rx="4" fill="#475569"/><path d="M72,32 C94,44 96,76 74,92" fill="none" stroke="#94a3b8" stroke-width="10" stroke-linecap="round"/><rect x="46" y="20" width="18" height="48" rx="4" transform="rotate(-25 55 44)" fill="#38bdf8"/><line x1="36" y1="78" x2="78" y2="78" stroke="#cbd5e1" stroke-width="8" stroke-linecap="round"/></svg>'
    },
    {
        "char": "🚀", "code": "1f680", "name": "rocket", "name_ar": "صاروخ / فضاء / انطلاق",
        "tags": ["space", "rocket", "launch", "future", "technology", "speed", "فضاء", "صاروخ", "انطلاق", "مستقبل", "تكنولوجيا"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><path d="M64,12 C84,32 90,62 86,88 H42 C38,62 44,32 64,12 Z" fill="#f8fafc" stroke="#64748b" stroke-width="4"/><circle cx="64" cy="54" r="12" fill="#38bdf8"/><polygon points="42,72 22,94 42,92" fill="#ef4444"/><polygon points="86,72 106,94 86,92" fill="#ef4444"/><polygon points="52,90 64,118 76,90" fill="#f97316"/></svg>'
    },
    {
        "char": "🏔️", "code": "1f3d4", "name": "snow-capped mountain", "name_ar": "جبل / قمة",
        "tags": ["mountain", "peak", "altitude", "andes", "geography", "nature", "جبل", "قمة", "ارتفاع", "جغرافيا", "طبيعة"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><polygon points="64,18 12,108 116,108" fill="#64748b"/><polygon points="64,18 42,56 56,62 64,50 74,62 86,56" fill="#f8fafc"/></svg>'
    },
    {
        "char": "🛡️", "code": "1f6e1", "name": "shield", "name_ar": "درع حماية / دفاع",
        "tags": ["shield", "defense", "security", "protection", "army", "fortress", "درع", "دفاع", "حماية", "أمن", "حصن"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><path d="M64,14 L106,30 V62 C106,90 86,108 64,116 C42,108 22,90 22,62 V30 Z" fill="#3b82f6" stroke="#fbbf24" stroke-width="6"/><path d="M64,22 V108 C82,100 98,84 98,62 V35 Z" fill="#2563eb"/></svg>'
    },
    {
        "char": "🎯", "code": "1f3af", "name": "bullseye target", "name_ar": "هدف دقيق",
        "tags": ["target", "goal", "focus", "point", "accuracy", "mission", "هدف", "تركيز", "دقة", "غاية"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><circle cx="64" cy="64" r="50" fill="#ef4444"/><circle cx="64" cy="64" r="34" fill="#ffffff"/><circle cx="64" cy="64" r="20" fill="#ef4444"/><circle cx="64" cy="64" r="8" fill="#fbbf24"/></svg>'
    },
    {
        "char": "👥", "code": "1f465", "name": "busts in silhouette", "name_ar": "سكان / مجتمع / شعب",
        "tags": ["people", "population", "society", "citizens", "crowd", "nation", "سكان", "شعب", "مجتمع", "بشر", "مواطنين", "مليون"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><circle cx="48" cy="44" r="18" fill="#60a5fa"/><path d="M18,104 C18,80 78,80 78,104 Z" fill="#3b82f6"/><circle cx="84" cy="48" r="15" fill="#93c5fd"/><path d="M62,104 C62,84 110,84 110,104 Z" fill="#60a5fa"/></svg>'
    },
    {
        "char": "💎", "code": "1f48e", "name": "gem stone", "name_ar": "جوهرة / معدن ثمين",
        "tags": ["diamond", "gem", "treasure", "rare", "value", "luxury", "ألماس", "جوهرة", "كنز", "ثمين", "نادر"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><polygon points="36,22 92,22 114,52 64,112 14,52" fill="#38bdf8" stroke="#0284c7" stroke-width="4"/><polyline points="14,52 114,52" stroke="#bae6fd" stroke-width="4"/><polyline points="36,22 50,52 64,112 78,52 92,22" fill="none" stroke="#7dd3fc" stroke-width="3"/></svg>'
    },
    {
        "char": "🧭", "code": "1f9ed", "name": "compass", "name_ar": "بوصلة / اتجاهات",
        "tags": ["compass", "navigation", "north", "south", "direction", "explore", "بوصلة", "اتجاه", "شمال", "جنوب", "استكشاف"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><circle cx="64" cy="64" r="50" fill="#1e293b" stroke="#fbbf24" stroke-width="6"/><polygon points="64,24 76,64 64,56 52,64" fill="#ef4444"/><polygon points="64,104 76,64 64,72 52,64" fill="#e2e8f0"/></svg>'
    },
    {
        "char": "✅", "code": "2705", "name": "check mark button", "name_ar": "علامة صح",
        "tags": ["check", "yes", "true", "correct", "verified", "صح", "صحيح", "نعم", "مؤكد"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect x="14" y="14" width="100" height="100" rx="22" fill="#22c55e"/><polyline points="34,66 56,88 94,42" fill="none" stroke="#ffffff" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    },
    {
        "char": "⚠️", "code": "26a0", "name": "warning", "name_ar": "تحذير / تنبيه",
        "tags": ["warning", "danger", "alert", "caution", "risk", "تحذير", "خطر", "تنبيه", "انتبه"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><polygon points="64,14 116,108 12,108" fill="#facc15" stroke="#ca8a04" stroke-width="5" stroke-linejoin="round"/><rect x="58" y="44" width="12" height="34" rx="6" fill="#1e293b"/><circle cx="64" cy="92" r="7" fill="#1e293b"/></svg>'
    },
    {
        "char": "❓", "code": "2753", "name": "question mark", "name_ar": "علامة استفهام / لغز",
        "tags": ["question", "mystery", "why", "how", "puzzle", "riddle", "سؤال", "لغز", "لماذا", "كيف", "غموض", "سر"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><circle cx="64" cy="64" r="52" fill="#f59e0b"/><text x="64" y="92" font-size="82" font-family="sans-serif" font-weight="bold" fill="#ffffff" text-anchor="middle">?</text></svg>'
    },
    {
        "char": "⚓", "code": "2693", "name": "anchor", "name_ar": "مرساة بحرية / ميناء",
        "tags": ["sea", "ocean", "port", "navy", "ship", "trade", "maritime", "بحر", "ميناء", "أسطول", "سفينة", "ملاحة"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><circle cx="64" cy="26" r="10" fill="none" stroke="#94a3b8" stroke-width="8"/><line x1="64" y1="36" x2="64" y2="108" stroke="#94a3b8" stroke-width="10"/><line x1="40" y1="54" x2="88" y2="54" stroke="#94a3b8" stroke-width="8" stroke-linecap="round"/><path d="M26,76 C26,102 50,110 64,110 C78,110 102,102 102,76" fill="none" stroke="#94a3b8" stroke-width="10" stroke-linecap="round"/></svg>'
    },
    {
        "char": "🛢️", "code": "1f6e2", "name": "oil drum", "name_ar": "برميل نفط / طاقة",
        "tags": ["oil", "gas", "petroleum", "energy", "barrel", "resources", "نفط", "بترول", "غاز", "طاقة", "موارد"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect x="30" y="18" width="68" height="92" rx="8" fill="#ef4444" stroke="#991b1b" stroke-width="4"/><line x1="26" y1="48" x2="102" y2="48" stroke="#fca5a5" stroke-width="6"/><line x1="26" y1="80" x2="102" y2="80" stroke="#fca5a5" stroke-width="6"/></svg>'
    },
    {
        "char": "🏰", "code": "1f3f0", "name": "castle", "name_ar": "قلعة / حصن تاريخي",
        "tags": ["castle", "fortress", "citadel", "palace", "walls", "history", "قلعة", "حصن", "قصر", "أسوار", "تاريخ"],
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect x="20" y="42" width="24" height="68" fill="#d6d3d1"/><rect x="84" y="42" width="24" height="68" fill="#d6d3d1"/><rect x="44" y="56" width="40" height="54" fill="#e7e5e4"/><polygon points="20,42 32,20 44,42" fill="#ef4444"/><polygon points="84,42 96,20 108,42" fill="#ef4444"/><rect x="54" y="80" width="20" height="30" rx="10" fill="#44403c"/></svg>'
    },
]


ISO3_TO_ISO2 = {
    "EGY": "eg", "SAU": "sa", "ARE": "ae", "QAT": "qa", "KWT": "kw", "BHR": "bh", "OMN": "om", "YEM": "ye",
    "IRQ": "iq", "SYR": "sy", "JOR": "jo", "LBN": "lb", "PSE": "ps", "SDN": "sd", "LBY": "ly", "TUN": "tn",
    "DZA": "dz", "MAR": "ma", "MRT": "mr", "SOM": "so", "DJI": "dj", "COM": "km",
    "TUR": "tr", "IRN": "ir", "PAK": "pk", "AFG": "af", "IND": "in", "CHN": "cn", "JPN": "jp", "KOR": "kr",
    "RUS": "ru", "DEU": "de", "FRA": "fr", "GBR": "gb", "ITA": "it", "ESP": "es", "PRT": "pt", "GRC": "gr",
    "NLD": "nl", "BEL": "be", "CHE": "ch", "AUT": "at", "POL": "pl", "UKR": "ua", "SWE": "se", "NOR": "no",
    "USA": "us", "CAN": "ca", "MEX": "mx", "BRA": "br", "ARG": "ar", "BOL": "bo", "CHL": "cl", "PER": "pe",
    "COL": "co", "VEN": "ve", "ECU": "ec", "PRY": "py", "URY": "uy",
    "ZAF": "za", "NGA": "ng", "ETH": "et", "KEN": "ke", "TZA": "tz", "GHA": "gh", "SEN": "sn", "MLI": "ml",
    "IDN": "id", "MYS": "my", "SGP": "sg", "THA": "th", "VNM": "vn", "PHL": "ph", "AUS": "au", "NZL": "nz",
    "KAZ": "kz", "UZB": "uz", "AZE": "az", "GEO": "ge", "ARM": "am",
}


COUNTRY_NAMES = [
    {"iso2": "EG", "iso3": "EGY", "ar": ["مصر", "القاهرة", "المصرية"], "en": ["egypt", "cairo"]},
    {"iso2": "SA", "iso3": "SAU", "ar": ["السعودية", "المملكة العربية السعودية", "الرياض"], "en": ["saudi arabia", "saudi", "riyadh"]},
    {"iso2": "AE", "iso3": "ARE", "ar": ["الإمارات", "ابوظبي", "أبوظبي", "دبي"], "en": ["united arab emirates", "uae", "dubai", "abu dhabi"]},
    {"iso2": "QA", "iso3": "QAT", "ar": ["قطر", "الدوحة"], "en": ["qatar", "doha"]},
    {"iso2": "KW", "iso3": "KWT", "ar": ["الكويت"], "en": ["kuwait"]},
    {"iso2": "BH", "iso3": "BHR", "ar": ["البحرين", "المنامة"], "en": ["bahrain", "manama"]},
    {"iso2": "OM", "iso3": "OMN", "ar": ["عمان", "سلطنة عمان", "مسقط"], "en": ["oman", "muscat"]},
    {"iso2": "YE", "iso3": "YEM", "ar": ["اليمن", "صنعاء"], "en": ["yemen", "sanaa"]},
    {"iso2": "IQ", "iso3": "IRQ", "ar": ["العراق", "بغداد"], "en": ["iraq", "baghdad"]},
    {"iso2": "SY", "iso3": "SYR", "ar": ["سوريا", "دمشق"], "en": ["syria", "damascus"]},
    {"iso2": "JO", "iso3": "JOR", "ar": ["الأردن", "الاردن", "عمان"], "en": ["jordan", "amman"]},
    {"iso2": "LB", "iso3": "LBN", "ar": ["لبنان", "بيروت"], "en": ["lebanon", "beirut"]},
    {"iso2": "PS", "iso3": "PSE", "ar": ["فلسطين", "القدس", "غزة"], "en": ["palestine", "jerusalem"]},
    {"iso2": "SD", "iso3": "SDN", "ar": ["السودان", "الخرطوم"], "en": ["sudan", "khartoum"]},
    {"iso2": "LY", "iso3": "LBY", "ar": ["ليبيا", "طرابلس"], "en": ["libya", "tripoli"]},
    {"iso2": "TN", "iso3": "TUN", "ar": ["تونس"], "en": ["tunisia", "tunis"]},
    {"iso2": "DZ", "iso3": "DZA", "ar": ["الجزائر"], "en": ["algeria", "algiers"]},
    {"iso2": "MA", "iso3": "MAR", "ar": ["المغرب", "الرباط"], "en": ["morocco", "rabat"]},
    {"iso2": "MR", "iso3": "MRT", "ar": ["موريتانيا", "نواكشوط"], "en": ["mauritania"]},
    {"iso2": "BO", "iso3": "BOL", "ar": ["بوليفيا", "لاباز", "سوكري"], "en": ["bolivia", "la paz", "sucre"]},
    {"iso2": "TR", "iso3": "TUR", "ar": ["تركيا", "أنقرة", "إسطنبول"], "en": ["turkey", "turkiye", "ankara", "istanbul"]},
    {"iso2": "IR", "iso3": "IRN", "ar": ["إيران", "ايران", "طهران"], "en": ["iran", "tehran"]},
    {"iso2": "US", "iso3": "USA", "ar": ["أمريكا", "امريكا", "الولايات المتحدة", "واشنطن"], "en": ["united states", "usa", "america", "us"]},
    {"iso2": "GB", "iso3": "GBR", "ar": ["بريطانيا", "المملكة المتحدة", "إنجلترا", "لندن"], "en": ["united kingdom", "uk", "britain", "england", "london"]},
    {"iso2": "FR", "iso3": "FRA", "ar": ["فرنسا", "باريس"], "en": ["france", "paris"]},
    {"iso2": "DE", "iso3": "DEU", "ar": ["ألمانيا", "المانيا", "برلين"], "en": ["germany", "berlin"]},
    {"iso2": "IT", "iso3": "ITA", "ar": ["إيطاليا", "ايطاليا", "روما"], "en": ["italy", "rome"]},
    {"iso2": "ES", "iso3": "ESP", "ar": ["إسبانيا", "اسبانيا", "مدريد", "الأندلس"], "en": ["spain", "madrid"]},
    {"iso2": "RU", "iso3": "RUS", "ar": ["روسيا", "موسكو"], "en": ["russia", "moscow"]},
    {"iso2": "CN", "iso3": "CHN", "ar": ["الصين", "بكين"], "en": ["china", "beijing"]},
    {"iso2": "JP", "iso3": "JPN", "ar": ["اليابان", "طوكيو"], "en": ["japan", "tokyo"]},
    {"iso2": "IN", "iso3": "IND", "ar": ["الهند", "نيودلهي"], "en": ["india", "new delhi"]},
    {"iso2": "BR", "iso3": "BRA", "ar": ["البرازيل"], "en": ["brazil"]},
    {"iso2": "AR", "iso3": "ARG", "ar": ["الأرجنتين", "الارجنتين"], "en": ["argentina"]},
    {"iso2": "ZA", "iso3": "ZAF", "ar": ["جنوب أفريقيا", "جنوب افريقيا"], "en": ["south africa"]},
    {"iso2": "ID", "iso3": "IDN", "ar": ["إندونيسيا", "اندونيسيا"], "en": ["indonesia"]},
    {"iso2": "MY", "iso3": "MYS", "ar": ["ماليزيا"], "en": ["malaysia"]},
    {"iso2": "PK", "iso3": "PAK", "ar": ["باكستان"], "en": ["pakistan"]},
    {"iso2": "CA", "iso3": "CAN", "ar": ["كندا"], "en": ["canada"]},
    {"iso2": "AU", "iso3": "AUS", "ar": ["أستراليا", "استراليا"], "en": ["australia"]},
    {"iso2": "MX", "iso3": "MEX", "ar": ["المكسيك"], "en": ["mexico"]},
    {"iso2": "KR", "iso3": "KOR", "ar": ["كوريا الجنوبية", "كوريا", "سيول"], "en": ["south korea", "korea", "seoul"]},
    {"iso2": "GR", "iso3": "GRC", "ar": ["اليونان", "أثينا"], "en": ["greece", "athens"]},
    {"iso2": "PT", "iso3": "PRT", "ar": ["البرتغال", "لشبونة"], "en": ["portugal", "lisbon"]},
    {"iso2": "NL", "iso3": "NLD", "ar": ["هولندا", "أمستردام"], "en": ["netherlands", "amsterdam"]},
    {"iso2": "CH", "iso3": "CHE", "ar": ["سويسرا"], "en": ["switzerland"]},
    {"iso2": "SE", "iso3": "SWE", "ar": ["السويد"], "en": ["sweden"]},
    {"iso2": "NO", "iso3": "NOR", "ar": ["النرويج"], "en": ["norway"]},
    {"iso2": "UA", "iso3": "UKR", "ar": ["أوكرانيا", "اوكرانيا"], "en": ["ukraine"]},
    {"iso2": "PL", "iso3": "POL", "ar": ["بولندا"], "en": ["poland"]},
    {"iso2": "ET", "iso3": "ETH", "ar": ["إثيوبيا", "اثيوبيا"], "en": ["ethiopia"]},
    {"iso2": "NG", "iso3": "NGA", "ar": ["نيجيريا"], "en": ["nigeria"]},
    {"iso2": "CL", "iso3": "CHL", "ar": ["تشيلي"], "en": ["chile"]},
    {"iso2": "PE", "iso3": "PER", "ar": ["بيرو"], "en": ["peru"]},
    {"iso2": "CO", "iso3": "COL", "ar": ["كولومبيا"], "en": ["colombia"]},
]


CURATED_ICONS = [
    # History, Landmarks, State, Politics
    {"set": "lucide", "name": "landmark", "ar": ["معلم", "برلمان", "عاصمة", "حكومة", "مبنى تاريخي", "محكمة"], "tags": ["landmark", "capital", "government", "parliament", "building", "history", "museum", "court"]},
    {"set": "lucide", "name": "crown", "ar": ["تاج", "ملك", "مملكة", "إمبراطورية", "سلطة", "عرش"], "tags": ["crown", "king", "royal", "empire", "monarchy", "power", "rule"]},
    {"set": "lucide", "name": "castle", "ar": ["قلعة", "حصن", "قصر", "تراث", "أسوار"], "tags": ["castle", "fortress", "palace", "citadel", "medieval", "history"]},
    {"set": "lucide", "name": "pyramid", "ar": ["هرم", "أهرامات", "فرعون", "مصر", "آثار"], "tags": ["pyramid", "egypt", "ancient", "monument", "pharaoh", "geometry"]},
    {"set": "lucide", "name": "scroll-text", "ar": ["مخطوطة", "دستور", "وثيقة", "معاهدة", "تاريخ"], "tags": ["scroll", "document", "constitution", "treaty", "history", "law", "script"]},
    {"set": "lucide", "name": "scale", "ar": ["ميزان", "عدالة", "قضاء", "قانون", "مقارنة"], "tags": ["scale", "justice", "law", "court", "balance", "compare"]},
    {"set": "lucide", "name": "swords", "ar": ["سيوف", "معركة", "حرب", "صراع", "جيش", "تمرد"], "tags": ["swords", "war", "battle", "conflict", "military", "fight", "rebellion"]},
    {"set": "lucide", "name": "shield", "ar": ["درع", "حماية", "دفاع", "أمن", "جيش"], "tags": ["shield", "defense", "security", "protect", "guard", "armor"]},
    {"set": "lucide", "name": "building-2", "ar": ["مدينة", "مبنى", "عاصمة", "برج", "حضر"], "tags": ["building", "city", "urban", "office", "capital", "skyscraper"]},
    # Geography, Maps, Navigation
    {"set": "lucide", "name": "globe", "ar": ["عالم", "الأرض", "كوكب", "دولي", "جغرافيا"], "tags": ["globe", "world", "earth", "planet", "global", "international"]},
    {"set": "lucide", "name": "map", "ar": ["خريطة", "أطلس", "إقليم", "حدود", "منطقة"], "tags": ["map", "geography", "region", "territory", "borders", "atlas"]},
    {"set": "lucide", "name": "map-pin", "ar": ["موقع", "دبوس", "نقطة", "مكان", "مدينة"], "tags": ["map-pin", "pin", "location", "place", "marker", "point", "spot"]},
    {"set": "lucide", "name": "compass", "ar": ["بوصلة", "اتجاه", "شمال", "جنوب", "ملاحة"], "tags": ["compass", "navigation", "direction", "north", "explore", "guide"]},
    {"set": "lucide", "name": "mountain", "ar": ["جبل", "قمة", "ارتفاع", "تضاريس", "هضبة"], "tags": ["mountain", "peak", "altitude", "nature", "terrain", "andes"]},
    {"set": "lucide", "name": "waves", "ar": ["بحر", "محيط", "نهر", "موج", "مياه", "مضيق"], "tags": ["waves", "sea", "ocean", "water", "river", "strait", "maritime"]},
    {"set": "lucide", "name": "anchor", "ar": ["مرساة", "ميناء", "أسطول", "سفينة", "بحرية"], "tags": ["anchor", "port", "harbor", "ship", "navy", "maritime"]},
    {"set": "lucide", "name": "plane", "ar": ["طائرة", "طيران", "سفر", "مطار"], "tags": ["plane", "flight", "travel", "aviation", "airport"]},
    {"set": "lucide", "name": "ship", "ar": ["سفينة", "بحر", "تجارة بحرية", "أسطول"], "tags": ["ship", "boat", "vessel", "trade", "cargo", "sea"]},
    # Economy, Charts, Numbers, Rankings
    {"set": "lucide", "name": "trending-up", "ar": ["نمو", "ارتفاع", "صعود", "تطور", "اقتصاد"], "tags": ["trending-up", "growth", "increase", "rise", "chart", "economy", "profit"]},
    {"set": "lucide", "name": "trending-down", "ar": ["هبوط", "انخفاض", "أزمة", "تراجع", "خسارة"], "tags": ["trending-down", "decline", "drop", "crisis", "fall", "loss"]},
    {"set": "lucide", "name": "bar-chart-3", "ar": ["إحصائيات", "مخطط أعمدة", "بيانات", "أرقام"], "tags": ["bar-chart", "chart", "stats", "statistics", "data", "analytics"]},
    {"set": "lucide", "name": "pie-chart", "ar": ["مخطط دائري", "نسبة", "حصة", "توزيع"], "tags": ["pie-chart", "donut", "share", "percentage", "distribution"]},
    {"set": "lucide", "name": "coins", "ar": ["أموال", "عملة", "ذهب", "ثروة", "اقتصاد", "ميزانية"], "tags": ["coins", "money", "wealth", "gold", "currency", "economy", "finance"]},
    {"set": "lucide", "name": "banknote", "ar": ["نقد", "دولار", "مال", "تمويل", "مليار"], "tags": ["banknote", "cash", "money", "dollar", "billion", "budget"]},
    {"set": "lucide", "name": "gem", "ar": ["جوهرة", "ألماس", "كنز", "موارد", "ثمين"], "tags": ["gem", "diamond", "treasure", "mineral", "valuable", "luxury"]},
    {"set": "lucide", "name": "trophy", "ar": ["كأس", "بطولة", "المركز الأول", "فوز", "صدارة"], "tags": ["trophy", "winner", "champion", "first", "award", "top", "record"]},
    {"set": "lucide", "name": "medal", "ar": ["ميدالية", "جائزة", "مرتبة", "تصنيف", "تكريم"], "tags": ["medal", "award", "rank", "prize", "honor", "badge"]},
    # People, Society, Science, Energy, Time
    {"set": "lucide", "name": "users", "ar": ["سكان", "شعب", "مجتمع", "بشر", "مواطنين", "جمهور"], "tags": ["users", "people", "population", "crowd", "society", "citizens", "community"]},
    {"set": "lucide", "name": "user-round", "ar": ["شخص", "فرد", "قائد", "مواطن", "إنسان"], "tags": ["user", "person", "individual", "leader", "profile", "human"]},
    {"set": "lucide", "name": "clock", "ar": ["ساعة", "وقت", "زمن", "تاريخ", "مدة", "عصر"], "tags": ["clock", "time", "duration", "hour", "history", "schedule"]},
    {"set": "lucide", "name": "hourglass", "ar": ["ساعة رملية", "قرن", "حقبة", "انتظار", "مرور الزمن"], "tags": ["hourglass", "timer", "era", "century", "ancient", "countdown"]},
    {"set": "lucide", "name": "calendar", "ar": ["تقويم", "سنة", "عام", "تاريخ", "يوم"], "tags": ["calendar", "year", "date", "event", "anniversary"]},
    {"set": "lucide", "name": "flame", "ar": ["نار", "شعلة", "لهب", "طاقة", "ثورة", "حماس"], "tags": ["flame", "fire", "hot", "spark", "energy", "burn"]},
    {"set": "lucide", "name": "zap", "ar": ["برق", "صاعقة", "طاقة", "كهرباء", "سرعة", "مفاجأة"], "tags": ["zap", "lightning", "bolt", "power", "electricity", "fast", "shock"]},
    {"set": "lucide", "name": "lightbulb", "ar": ["فكرة", "ابتكار", "سر", "حقيقة", "اكتشاف", "ذكاء"], "tags": ["lightbulb", "bulb", "idea", "fact", "discovery", "innovation", "insight"]},
    {"set": "lucide", "name": "atom", "ar": ["ذرة", "علم", "فيزياء", "تكنولوجيا", "أبحاث"], "tags": ["atom", "science", "physics", "nuclear", "research", "technology"]},
    {"set": "lucide", "name": "cpu", "ar": ["معالج", "ذكاء اصطناعي", "حاسوب", "رقائق", "تقنية"], "tags": ["cpu", "chip", "processor", "ai", "computer", "tech", "hardware"]},
    {"set": "lucide", "name": "rocket", "ar": ["صاروخ", "فضاء", "انطلاق", "مستقبل", "تقدم"], "tags": ["rocket", "space", "launch", "future", "startup", "boost"]},
    {"set": "lucide", "name": "book-open", "ar": ["كتاب", "معرفة", "تعليم", "قراءة", "دراسة", "ثقافة"], "tags": ["book", "knowledge", "education", "study", "library", "history"]},
    {"set": "lucide", "name": "star", "ar": ["نجمة", "تألق", "مميز", "تقييم", "نجاح"], "tags": ["star", "favorite", "rating", "highlight", "special"]},
    {"set": "lucide", "name": "sparkles", "ar": ["بريق", "لمعان", "سحر", "إبداع", "مميز"], "tags": ["sparkles", "magic", "shine", "glitter", "new", "special"]},
    {"set": "lucide", "name": "target", "ar": ["هدف", "تركيز", "دقة", "نقطة محورية"], "tags": ["target", "goal", "bullseye", "focus", "aim"]},
    {"set": "lucide", "name": "check-circle-2", "ar": ["صح", "تحقق", "صحيح", "مؤكد", "مكتمل"], "tags": ["check", "verified", "correct", "success", "done", "true"]},
    {"set": "lucide", "name": "alert-triangle", "ar": ["تحذير", "خطر", "تنبيه", "أزمة", "مشكلة"], "tags": ["warning", "alert", "danger", "risk", "caution", "error"]},
    {"set": "lucide", "name": "help-circle", "ar": ["سؤال", "لغز", "استفهام", "غموض", "لماذا"], "tags": ["question", "help", "mystery", "why", "riddle", "unknown"]},
    {"set": "lucide", "name": "arrow-right", "ar": ["سهم يمين", "انتقال", "التالي"], "tags": ["arrow-right", "next", "forward", "direction"]},
    {"set": "lucide", "name": "arrow-left", "ar": ["سهم يسار", "اتجاه", "عودة"], "tags": ["arrow-left", "back", "rtl", "direction"]},
    {"set": "lucide", "name": "arrow-up-right", "ar": ["سهم صاعد", "نمو", "تقدم"], "tags": ["arrow-up-right", "growth", "outward", "increase"]},
    # Phosphor (ph) icons
    {"set": "ph", "name": "mosque", "ar": ["مسجد", "جامع", "إسلام", "عمارة إسلامية", "مئذنة"], "tags": ["mosque", "islam", "religion", "dome", "heritage", "arab"]},
    {"set": "ph", "name": "globe-hemisphere-east", "ar": ["الشرق الأوسط", "الكرة الأرضية", "قارات", "عالم"], "tags": ["globe", "east", "middle-east", "world", "continents"]},
    {"set": "ph", "name": "bank", "ar": ["بنك", "مصرف", "خزينة", "دولة", "مؤسسة"], "tags": ["bank", "finance", "institution", "state", "treasury"]},
    {"set": "ph", "name": "columns", "ar": ["أعمدة", "حضارة", "آثار", "معبد", "تاريخ"], "tags": ["columns", "pillars", "classical", "temple", "history", "antiquity"]},
    {"set": "ph", "name": "scroll", "ar": ["وثيقة", "فرمان", "معاهدة", "مخطوطة"], "tags": ["scroll", "manuscript", "decree", "history", "ancient"]},
    {"set": "ph", "name": "sword", "ar": ["سيف", "فتح", "معركة", "قوة"], "tags": ["sword", "blade", "warrior", "battle", "conquest"]},
    {"set": "ph", "name": "crown-simple", "ar": ["تاج", "سيادة", "حكم", "مملكة"], "tags": ["crown", "sovereignty", "royalty", "kingdom"]},
    {"set": "ph", "name": "treasure-chest", "ar": ["كنز", "ثروة", "ذهب", "اكتشاف"], "tags": ["treasure", "chest", "wealth", "gold", "loot"]},
    {"set": "ph", "name": "Drop", "fallback_name": "drop", "ar": ["نفط", "ماء", "قطرة", "موارد"], "tags": ["drop", "oil", "water", "liquid", "resource"]},
    {"set": "ph", "name": "brain", "ar": ["عقل", "ذكاء", "تفكير", "علم النفس", "عبقرية"], "tags": ["brain", "mind", "intelligence", "psychology", "thinking"]},
    {"set": "ph", "name": "handshake", "ar": ["اتفاق", "سلام", "تحالف", "تعاون", "معاهدة"], "tags": ["handshake", "peace", "treaty", "alliance", "deal", "agreement"]},
    # Tabler icons
    {"set": "tabler", "name": "building-mosque", "ar": ["مسجد", "جامع", "قبة", "تراث إسلامي"], "tags": ["mosque", "islamic", "building", "dome", "minaret"]},
    {"set": "tabler", "name": "building-monument", "ar": ["نصب تذكاري", "مسلة", "معلم تاريخي"], "tags": ["monument", "obelisk", "memorial", "heritage"]},
    {"set": "tabler", "name": "world", "ar": ["عالم", "شبكة عالمية", "دولي"], "tags": ["world", "global", "earth", "international"]},
    {"set": "tabler", "name": "map-pin-filled", "ar": ["دبوس خريطة", "نقطة رئيسية", "عاصمة"], "tags": ["map-pin", "location", "capital", "point"]},
    {"set": "tabler", "name": "chart-arcs", "ar": ["مخطط حلقي", "نسب", "إحصائيات"], "tags": ["chart", "ring", "donut", "progress", "metrics"]},
    {"set": "tabler", "name": "timeline", "ar": ["خط زمني", "تسلسل أحداث", "تاريخ"], "tags": ["timeline", "chronology", "history", "sequence"]},
    {"set": "tabler", "name": "award", "ar": ["وسام", "جائزة", "شرف", "المركز الأول"], "tags": ["award", "ribbon", "prize", "excellence"]},
    {"set": "tabler", "name": "scale", "ar": ["ميزان", "عدل", "حكم", "مقارنة"], "tags": ["scale", "justice", "balance", "law"]},
]
