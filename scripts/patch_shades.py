from pathlib import Path

TARGET = Path("remotion/src/layers.tsx")
content = TARGET.read_text(encoding="utf-8").replace("\r\n", "\n")

old_shades = """          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: 440,
              background:
                'linear-gradient(to bottom, rgba(0,0,0,0.88) 0%, rgba(0,0,0,0.4) 55%, transparent 100%)',
              pointerEvents: 'none',
              zIndex: 4,
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: 500,
              background:
                'linear-gradient(to top, rgba(0,0,0,0.94) 0%, rgba(0,0,0,0.55) 55%, transparent 100%)',
              pointerEvents: 'none',
              zIndex: 4,
            }}
          />"""

new_shades = """          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: 220,
              background:
                'linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, transparent 100%)',
              pointerEvents: 'none',
              zIndex: 4,
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: 260,
              background:
                'linear-gradient(to top, rgba(0,0,0,0.75) 0%, transparent 100%)',
              pointerEvents: 'none',
              zIndex: 4,
            }}
          />"""

if old_shades in content:
    content = content.replace(old_shades, new_shades, 1)
    TARGET.write_text(content, encoding="utf-8")
    print("Patched shades in layers.tsx")
else:
    print("Could not match old_shades")

