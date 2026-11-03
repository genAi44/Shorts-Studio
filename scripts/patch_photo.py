import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "remotion" / "src" / "photo.tsx"

content = TARGET.read_text(encoding="utf-8")

# 1. Update imports
old_import = "import {Beat, RGB} from './types';"
new_import = (
    "import {Beat, RGB} from './types';\n"
    "import {IconSceneBeat} from './iconScene';\n"
    "import {FireSparks, FloatBadge, MapOverlay} from './fx';"
)
if old_import in content:
    content = content.replace(old_import, new_import)

# 2. Add fallback to IconSceneBeat at start of PhotoBeat
old_photobeat_start = "export const PhotoBeat: React.FC<{beat: Beat}> = ({beat}) => {\n  const th = useTheme();"
new_photobeat_start = (
    "export const PhotoBeat: React.FC<{beat: Beat}> = ({beat}) => {\n"
    "  if (!beat.img) {\n"
    "    return <IconSceneBeat beat={beat} />;\n"
    "  }\n"
    "  const th = useTheme();"
)
if old_photobeat_start in content:
    content = content.replace(old_photobeat_start, new_photobeat_start)

# 3. Add source badge and accent icons in PhotoBeat return
old_return = """  return (
    <AbsoluteFill>
      <AccentShapes seed={beat.from + 7} count={cut || ed.photo !== 'bleed' ? 3 : 2} />
      {media}"""

new_return = """  // Accent icons and corner source badge
  const sourceIcon = beat.source === 'pexels' ? 'icons/star/sparkle.svg' : 'icons/monument/monument.svg';
  const accent1 = beat.accent_icon || 'icons/star/star.svg';

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <AccentShapes seed={beat.from + 7} count={cut || ed.photo !== 'bleed' ? 3 : 2} />
      {media}
      {/* Dark vignette gradient overlay for cinematic contrast */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none',
        background: 'radial-gradient(circle at 50% 50%, transparent 40%, rgba(0,0,0,0.65) 100%)',
        zIndex: 4,
      }} />
      {/* Corner source badge */}
      <FloatBadge
        icon={sourceIcon}
        label={beat.source || 'وثائقي'}
        x={140}
        y={cy - (hasNum ? 280 : 360)}
        size={90}
        borderColor=\"#D4AF37\"
        delay={10}
      />
      {/* Accent icon in opposite corner */}
      <FloatBadge
        icon={accent1}
        x={940}
        y={cy - (hasNum ? 270 : 340)}
        size={84}
        borderColor=\"#38bdf8\"
        delay={16}
      />"""

if old_return in content:
    content = content.replace(old_return, new_return)

TARGET.write_text(content, encoding="utf-8")
print("remotion/src/photo.tsx updated successfully!")

