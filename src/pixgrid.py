#!/usr/bin/env python3
# Copyright (C) 2026 Lenik <identicon@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import colorsys
import random

from PIL import Image

NES = (
    (252, 252, 252),
    (248, 56, 0),
    (252, 160, 68),
    (248, 216, 120),
    (0, 168, 0),
    (88, 216, 84),
    (0, 88, 248),
    (60, 188, 252),
    (104, 68, 252),
    (216, 40, 0),
    (200, 184, 248),
    (184, 248, 184),
    (248, 120, 88),
    (172, 124, 0),
    (228, 92, 16),
    (136, 136, 136),
)


class BitPump:
    def __init__(self, data: bytes) -> None:
        self.data = data if data else b"\x00"
        self.i = 0

    def take(self, n: int) -> int:
        v = 0
        for _ in range(n):
            byte = self.data[(self.i // 8) % len(self.data)]
            v = (v << 1) | ((byte >> (7 - (self.i % 8))) & 1)
            self.i += 1
        return v


def hsl(h: float, s: float, l: float, a: int = 255) -> tuple[int, int, int, int]:
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360.0, l / 100.0, s / 100.0)
    return (int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5), a)


def _rng(digest: bytes) -> random.Random:
    return random.Random(int.from_bytes(digest, "big"))


def _scale_cells(
    cells: list[list[tuple[int, int, int, int]]],
    size: int,
) -> Image.Image:
    h = len(cells)
    w = len(cells[0])
    img = Image.new("RGBA", (w, h))
    pix = img.load()
    assert pix is not None
    for y in range(h):
        for x in range(w):
            pix[x, y] = cells[y][x]
    return img.resize((size, size), Image.Resampling.NEAREST)


def _lod_n(size: int, *, min_n: int = 8) -> int:
    if size <= 16:
        n = 8
    elif size <= 32:
        n = 16
    elif size <= 64:
        n = 24
    elif size <= 128:
        n = 32
    else:
        n = 48
    return max(min_n, n)


class Pix:
    def __init__(self, n: int, bg: tuple[int, int, int, int]) -> None:
        self.n = n
        self.c = [[bg for _ in range(n)] for _ in range(n)]

    def put(self, x: int, y: int, color: tuple[int, int, int, int], mirror: bool = False) -> None:
        n = self.n
        if 0 <= x < n and 0 <= y < n:
            self.c[y][x] = color
        if mirror:
            mx = n - 1 - x
            if 0 <= mx < n and 0 <= y < n:
                self.c[y][mx] = color

    def fill(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        color: tuple[int, int, int, int],
        *,
        mirror: bool = False,
        clip: tuple[int, int, int, int] | None = None,
    ) -> None:
        x0, y0, x1, y1 = x, y, x + w, y + h
        if clip is not None:
            x0 = max(x0, clip[0])
            y0 = max(y0, clip[1])
            x1 = min(x1, clip[2])
            y1 = min(y1, clip[3])
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                self.put(xx, yy, color, mirror)

    def disc(self, cx: int, cy: int, r: int, color: tuple[int, int, int, int]) -> None:
        rr = r * r
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= rr:
                    self.put(x, y, color)

    def image(self, size: int) -> Image.Image:
        return _scale_cells(self.c, size)
