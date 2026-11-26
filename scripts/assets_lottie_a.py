"""Split from `scripts/build_assets.py` (re-exported there); see that module."""
from __future__ import annotations


def _kf_scalar(t0: int, v0: float, t1: int, v1: float, t2: int | None = None, v2: float | None = None):
    kfs = [
        {
            "i": {"x": [0.4], "y": [1]},
            "o": {"x": [0.2], "y": [0]},
            "t": t0,
            "s": [v0],
        },
        {
            "i": {"x": [0.4], "y": [1]},
            "o": {"x": [0.2], "y": [0]},
            "t": t1,
            "s": [v1],
        },
    ]
    if t2 is not None and v2 is not None:
        kfs.append({"t": t2, "s": [v2]})
    return {"a": 1, "k": kfs}


def _kf_vec2(t0: int, v0: list[float], t1: int, v1: list[float], t2: int | None = None, v2: list[float] | None = None):
    kfs = [
        {
            "i": {"x": [0.3, 0.3], "y": [1, 1]},
            "o": {"x": [0.2, 0.2], "y": [0, 0]},
            "t": t0,
            "s": v0,
        },
        {
            "i": {"x": [0.3, 0.3], "y": [1, 1]},
            "o": {"x": [0.2, 0.2], "y": [0, 0]},
            "t": t1,
            "s": v1,
        },
    ]
    if t2 is not None and v2 is not None:
        kfs.append({"t": t2, "s": v2})
    return {"a": 1, "k": kfs}


def make_lottie_checkmark() -> dict:
    """Animated golden/green circle + checkmark draw-on."""
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": 60,
        "w": 256,
        "h": 256,
        "nm": "checkmark",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "CheckStroke",
                "sr": 1,
                "ks": {
                    "o": {"a": 0, "k": 100},
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [128, 128, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": _kf_vec2(0, [60, 60, 100], 24, [104, 104, 100], 36, [100, 100, 100]),
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            {
                                "ty": "sh",
                                "ks": {
                                    "a": 0,
                                    "k": {
                                        "i": [[0, 0], [0, 0], [0, 0]],
                                        "o": [[0, 0], [0, 0], [0, 0]],
                                        "v": [[-44, 4], [-14, 34], [48, -32]],
                                        "c": False,
                                    },
                                },
                            },
                            {
                                "ty": "tm",
                                "s": {"a": 0, "k": 0},
                                "e": _kf_scalar(6, 0, 32, 100),
                                "o": {"a": 0, "k": 0},
                                "m": 1,
                            },
                            {
                                "ty": "st",
                                "c": {"a": 0, "k": [0.247, 0.85, 0.54, 1]},
                                "o": {"a": 0, "k": 100},
                                "w": {"a": 0, "k": 18},
                                "lc": 2,
                                "lj": 2,
                            },
                            {
                                "ty": "tr",
                                "p": {"a": 0, "k": [0, 0]},
                                "a": {"a": 0, "k": [0, 0]},
                                "s": {"a": 0, "k": [100, 100]},
                                "r": {"a": 0, "k": 0},
                                "o": {"a": 0, "k": 100},
                            },
                        ],
                    },
                    {
                        "ty": "gr",
                        "it": [
                            {
                                "ty": "el",
                                "p": {"a": 0, "k": [0, 0]},
                                "s": {"a": 0, "k": [196, 196]},
                            },
                            {
                                "ty": "tm",
                                "s": {"a": 0, "k": 0},
                                "e": _kf_scalar(0, 0, 22, 100),
                                "o": {"a": 0, "k": 0},
                                "m": 1,
                            },
                            {
                                "ty": "st",
                                "c": {"a": 0, "k": [0.95, 0.78, 0.28, 1]},
                                "o": {"a": 0, "k": 100},
                                "w": {"a": 0, "k": 12},
                                "lc": 2,
                                "lj": 2,
                            },
                            {
                                "ty": "fl",
                                "c": {"a": 0, "k": [0.12, 0.28, 0.22, 1]},
                                "o": {"a": 0, "k": 28},
                            },
                            {
                                "ty": "tr",
                                "p": {"a": 0, "k": [0, 0]},
                                "a": {"a": 0, "k": [0, 0]},
                                "s": {"a": 0, "k": [100, 100]},
                                "r": {"a": 0, "k": 0},
                                "o": {"a": 0, "k": 100},
                            },
                        ],
                    },
                ],
                "ip": 0,
                "op": 60,
                "st": 0,
            }
        ],
    }


def make_lottie_arrow(direction: str = "right") -> dict:
    """Animated directional arrow with smooth slide & draw-on."""
    rot = 0 if direction == "right" else (-90 if direction == "up" else 180)
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": 60,
        "w": 256,
        "h": 256,
        "nm": f"arrow-{direction}",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "ArrowGroup",
                "sr": 1,
                "ks": {
                    "o": {"a": 0, "k": 100},
                    "r": {"a": 0, "k": rot},
                    "p": _kf_vec2(0, [112, 128, 0], 30, [136, 128, 0], 60, [124, 128, 0]),
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {"a": 0, "k": [100, 100, 100]},
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            {
                                "ty": "sh",
                                "ks": {
                                    "a": 0,
                                    "k": {
                                        "i": [[0, 0], [0, 0]],
                                        "o": [[0, 0], [0, 0]],
                                        "v": [[-70, 0], [56, 0]],
                                        "c": False,
                                    },
                                },
                            },
                            {
                                "ty": "sh",
                                "ks": {
                                    "a": 0,
                                    "k": {
                                        "i": [[0, 0], [0, 0], [0, 0]],
                                        "o": [[0, 0], [0, 0], [0, 0]],
                                        "v": [[14, -42], [60, 0], [14, 42]],
                                        "c": False,
                                    },
                                },
                            },
                            {
                                "ty": "tm",
                                "s": {"a": 0, "k": 0},
                                "e": _kf_scalar(0, 0, 24, 100),
                                "o": {"a": 0, "k": 0},
                                "m": 1,
                            },
                            {
                                "ty": "st",
                                "c": {"a": 0, "k": [0.98, 0.80, 0.25, 1]},
                                "o": {"a": 0, "k": 100},
                                "w": {"a": 0, "k": 18},
                                "lc": 2,
                                "lj": 2,
                            },
                            {
                                "ty": "tr",
                                "p": {"a": 0, "k": [0, 0]},
                                "a": {"a": 0, "k": [0, 0]},
                                "s": {"a": 0, "k": [100, 100]},
                                "r": {"a": 0, "k": 0},
                                "o": {"a": 0, "k": 100},
                            },
                        ],
                    }
                ],
                "ip": 0,
                "op": 60,
                "st": 0,
            }
        ],
    }
