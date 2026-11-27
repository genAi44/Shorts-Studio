"""What the designer receives from upstream: the director's binding decision, and whether a scene keeps a native visual."""
from typing import Any, Dict, List


def director_decision(scene: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The beat director's decision for this scene (step 3 of the app), handed to the designer as binding input."""
    out = []
    for b in scene.get("beats") or []:
        if isinstance(b, dict) and (b.get("concept") or b.get("title")):
            out.append({k: b[k] for k in ("kind", "title", "concept", "camera") if b.get(k)})
    return out


NATIVE_KINDS = ("map", "map_pin", "area_map")


def has_native_visual(scene: Dict[str, Any]) -> bool:
    """A scene whose director beats show a real map or a found licensed photo: those render with the native
    components, an authored TSX scene would replace them with a drawing (seen: 0 photos on screen from 9 found)."""
    return any(isinstance(b, dict) and (b.get("kind") in NATIVE_KINDS or (b.get("kind") == "photo" and b.get("img")))
               for b in scene.get("beats") or [])
