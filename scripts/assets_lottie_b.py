"""Split from `scripts/build_assets.py` (re-exported there); see that module."""
from __future__ import annotations
from assets_lottie_a import _kf_scalar, _kf_vec2


def make_lottie_loader() -> dict:
    """Animated spinning golden ring loader."""
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": 60,
        "w": 256,
        "h": 256,
        "nm": "loader-ring",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "Spinner",
                "sr": 1,
                "ks": {
                    "o": {"a": 0, "k": 100},
                    "r": _kf_scalar(0, 0, 60, 360),
                    "p": {"a": 0, "k": [128, 128, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {"a": 0, "k": [100, 100, 100]},
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            {"ty": "el", "p": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [176, 176]}},
                            {"ty": "tm", "s": {"a": 0, "k": 10}, "e": {"a": 0, "k": 80}, "o": {"a": 0, "k": 0}, "m": 1},
                            {"ty": "st", "c": {"a": 0, "k": [0.96, 0.78, 0.26, 1]}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": 16}, "lc": 2, "lj": 2},
                            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                        ],
                    }
                ],
                "ip": 0,
                "op": 60,
                "st": 0,
            }
        ],
    }


def make_lottie_sparkles() -> dict:
    """Animated 4-point golden sparkle stars pulsing."""
    star_verts = [[0, -68], [18, -18], [68, 0], [18, 18], [0, 68], [-18, 18], [-68, 0], [-18, -18]]
    zeros = [[0, 0]] * len(star_verts)
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": 60,
        "w": 256,
        "h": 256,
        "nm": "sparkles-gold",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "MainStar",
                "sr": 1,
                "ks": {
                    "o": _kf_scalar(0, 60, 30, 100, 60, 75),
                    "r": _kf_scalar(0, -12, 30, 12, 60, -12),
                    "p": {"a": 0, "k": [128, 128, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": _kf_vec2(0, [50, 50, 100], 25, [112, 112, 100], 60, [85, 85, 100]),
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            {"ty": "sh", "ks": {"a": 0, "k": {"i": zeros, "o": zeros, "v": star_verts, "c": True}}},
                            {"ty": "fl", "c": {"a": 0, "k": [1.0, 0.84, 0.32, 1]}, "o": {"a": 0, "k": 100}},
                            {"ty": "st", "c": {"a": 0, "k": [1.0, 0.95, 0.75, 1]}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": 4}, "lc": 2, "lj": 2},
                            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                        ],
                    }
                ],
                "ip": 0,
                "op": 60,
                "st": 0,
            }
        ],
    }


def make_lottie_confetti() -> dict:
    """Festive radial burst particles."""
    layers = []
    colors = [
        [0.98, 0.80, 0.22, 1],
        [0.24, 0.82, 0.56, 1],
        [0.22, 0.68, 0.96, 1],
        [0.96, 0.38, 0.44, 1],
        [0.72, 0.46, 0.98, 1],
        [1.0, 0.62, 0.20, 1],
    ]
    import math
    for idx in range(6):
        ang = idx * (math.pi * 2 / 6)
        tx = round(128 + math.cos(ang) * 88, 1)
        ty = round(128 + math.sin(ang) * 88, 1)
        layers.append({
            "ddd": 0,
            "ind": idx + 1,
            "ty": 4,
            "nm": f"Particle_{idx}",
            "sr": 1,
            "ks": {
                "o": _kf_scalar(0, 100, 45, 100, 60, 0),
                "r": _kf_scalar(0, 0, 60, 180),
                "p": _kf_vec2(0, [128, 128, 0], 35, [tx, ty, 0], 60, [tx, ty + 16, 0]),
                "a": {"a": 0, "k": [0, 0, 0]},
                "s": _kf_vec2(0, [20, 20, 100], 20, [110, 110, 100], 60, [60, 60, 100]),
            },
            "ao": 0,
            "shapes": [
                {
                    "ty": "gr",
                    "it": [
                        {"ty": "el", "p": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [26, 26]}},
                        {"ty": "fl", "c": {"a": 0, "k": colors[idx]}, "o": {"a": 0, "k": 100}},
                        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                    ],
                }
            ],
            "ip": 0,
            "op": 60,
            "st": 0,
        })
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": 60,
        "w": 256,
        "h": 256,
        "nm": "confetti-burst",
        "ddd": 0,
        "assets": [],
        "layers": layers,
    }


def make_lottie_transition() -> dict:
    """Expanding concentric geometric ring transition wipe."""
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": 45,
        "w": 256,
        "h": 256,
        "nm": "transition-sweep",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "RingWave",
                "sr": 1,
                "ks": {
                    "o": _kf_scalar(0, 95, 30, 85, 45, 0),
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [128, 128, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": _kf_vec2(0, [10, 10, 100], 45, [220, 220, 100]),
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            {"ty": "el", "p": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [160, 160]}},
                            {"ty": "st", "c": {"a": 0, "k": [0.96, 0.78, 0.25, 1]}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": 18}, "lc": 2, "lj": 2},
                            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                        ],
                    }
                ],
                "ip": 0,
                "op": 45,
                "st": 0,
            }
        ],
    }


def make_lottie_pulse_target() -> dict:
    """Radar/location pulse target ring."""
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": 60,
        "w": 256,
        "h": 256,
        "nm": "pulse-target",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "OuterPulse",
                "sr": 1,
                "ks": {
                    "o": _kf_scalar(0, 90, 55, 0),
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [128, 128, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": _kf_vec2(0, [35, 35, 100], 55, [125, 125, 100]),
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            {"ty": "el", "p": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [160, 160]}},
                            {"ty": "st", "c": {"a": 0, "k": [0.96, 0.35, 0.32, 1]}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": 12}, "lc": 2, "lj": 2},
                            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                        ],
                    }
                ],
                "ip": 0,
                "op": 60,
                "st": 0,
            },
            {
                "ddd": 0,
                "ind": 2,
                "ty": 4,
                "nm": "CoreDot",
                "sr": 1,
                "ks": {
                    "o": {"a": 0, "k": 100},
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [128, 128, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": _kf_vec2(0, [90, 90, 100], 30, [115, 115, 100], 60, [90, 90, 100]),
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            {"ty": "el", "p": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [48, 48]}},
                            {"ty": "fl", "c": {"a": 0, "k": [0.98, 0.80, 0.25, 1]}, "o": {"a": 0, "k": 100}},
                            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                        ],
                    }
                ],
                "ip": 0,
                "op": 60,
                "st": 0,
            },
        ],
    }
