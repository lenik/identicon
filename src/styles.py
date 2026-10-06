#!/usr/bin/env python3
# Copyright (C) 2026 Lenik <identicon@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

from typing import Callable

from PIL import Image

from ident_style import render_identicon
from monster_style import render_monsterid
from retro_style import render_retro
from robo_style import render_robo
from robohash_style import ROBOHASH_SETS, render_robohash
from wavatar_style import render_wavatar

BUILTIN_TYPES = ("identicon", "wavatar", "monsterid", "retro", "robo")
TYPES = BUILTIN_TYPES + ROBOHASH_SETS
ALIASES = {
    "robohash": "robo",
    "monster": "monsterid",
    **{str(i): f"set{i}" for i in range(1, 7)},
}

TYPE_CHOICES = (
    "identicon, wavatar, monsterid, retro, robo, "
    "set1..set6 (or 1..6)"
)


def normalize_type(name: str) -> str:
    key = name.strip().lower()
    key = ALIASES.get(key, key)
    if key not in TYPES:
        raise ValueError(key)
    return key


def render(
    kind: str,
    digest: bytes,
    size: int,
    back: tuple[int, int, int, int] | None,
) -> Image.Image:
    kind = normalize_type(kind)
    fn = _RENDERERS[kind]
    return fn(digest, size, back)


def _rh(roboset: str) -> Callable[..., Image.Image]:
    def _render(
        digest: bytes,
        size: int,
        back: tuple[int, int, int, int] | None,
    ) -> Image.Image:
        return render_robohash(digest, size, back, roboset)

    _render.__name__ = f"render_{roboset}"
    return _render


_RENDERERS: dict[str, Callable[..., Image.Image]] = {
    "identicon": render_identicon,
    "wavatar": render_wavatar,
    "monsterid": render_monsterid,
    "retro": render_retro,
    "robo": render_robo,
    **{name: _rh(name) for name in ROBOHASH_SETS},
}
