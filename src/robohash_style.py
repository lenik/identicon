#!/usr/bin/env python3
# Copyright (C) 2026 Lenik <identicon@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import importlib.util
import os
import re
import sys
import types
from functools import lru_cache
from pathlib import Path

from PIL import Image

ROBOHASH_SETS = ("set1", "set2", "set3", "set4", "set5", "set6")


class MissingRobohashError(RuntimeError):
    """Raised when Robohash sprite assets or assembler cannot be loaded."""


def _ensure_natsort() -> None:
    try:
        import natsort  # noqa: F401
        return
    except ImportError:
        pass

    def natsorted(seq, key=None, reverse=False):
        def parts(item):
            text = str(item if key is None else key(item))
            return [
                int(tok) if tok.isdigit() else tok.lower()
                for tok in re.split(r"(\d+)", text)
            ]

        return sorted(seq, key=parts, reverse=reverse)

    stub = types.ModuleType("natsort")
    stub.natsorted = natsorted  # type: ignore[attr-defined]
    sys.modules["natsort"] = stub


def _candidate_dirs() -> list[Path]:
    here = Path(__file__).resolve().parent
    env = os.environ.get("IDENTICON_ROBOHASH_DIR")
    out: list[Path] = []
    if env:
        out.append(Path(env))
    out.extend(
        [
            Path(sys.prefix) / "share" / "identicon" / "robohash",
            here.parent / "share" / "identicon" / "robohash",
            here / "robohash",
        ]
    )
    for parent in (here, *here.parents):
        out.append(parent / "third_party" / "robohash")
    seen: set[Path] = set()
    uniq: list[Path] = []
    for p in out:
        rp = p.resolve() if p.exists() else p
        if rp in seen:
            continue
        seen.add(rp)
        uniq.append(p)
    return uniq


def robohash_resource_dir() -> Path:
    for cand in _candidate_dirs():
        if (cand / "sets" / "set1").is_dir() and (cand / "robohash.py").is_file():
            return cand
        if (cand / "sets" / "set1").is_dir() and (cand / "robohash" / "robohash.py").is_file():
            return cand / "robohash"
    tried = ", ".join(str(p) for p in _candidate_dirs())
    raise MissingRobohashError(
        f"Robohash assets not found (tried: {tried})"
    )


@lru_cache(maxsize=1)
def _robohash_class():
    _ensure_natsort()
    root = robohash_resource_dir()
    path = root / "robohash.py"
    spec = importlib.util.spec_from_file_location("_identicon_robohash", path)
    if spec is None or spec.loader is None:
        raise MissingRobohashError(f"cannot load Robohash assembler from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls = getattr(mod, "Robohash", None)
    if cls is None:
        raise MissingRobohashError(f"Robohash class missing in {path}")
    return cls


def render_robohash(
    digest: bytes,
    size: int,
    back: tuple[int, int, int, int] | None,
    roboset: str,
) -> Image.Image:
    Robohash = _robohash_class()
    rh = Robohash(digest.hex(), ignoreext=False)
    available = tuple(rh.sets)
    if roboset not in available:
        raise MissingRobohashError(
            f"Robohash {roboset} is not available (have {', '.join(available) or 'none'})"
        )
    rh.assemble(roboset=roboset, format="png", sizex=size, sizey=size)
    img = rh.img.convert("RGBA")
    if back is None:
        return img
    canvas = Image.new("RGBA", (size, size), back)
    canvas.alpha_composite(img)
    return canvas
