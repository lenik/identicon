#!/usr/bin/env python3
# Copyright (C) 2026 Lenik <identicon@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

from PIL import Image, ImageDraw

from pixgrid import BitPump, hsl

def _identicon_map(
    pts: list[tuple[float, float]],
    box: tuple[float, float, float, float],
) -> list[tuple[float, float]]:
    x0, y0, x1, y1 = box
    return [(x0 + u * (x1 - x0), y0 + v * (y1 - y0)) for u, v in pts]


def _identicon_rot(
    pts: list[tuple[float, float]],
    turns: int,
) -> list[tuple[float, float]]:
    out = pts
    for _ in range(turns % 4):
        out = [(1.0 - v, u) for u, v in out]
    return out


def _draw_identicon_patch(
    d: ImageDraw.ImageDraw,
    box: tuple[float, float, float, float],
    kind: int,
    turns: int,
    color: tuple[int, int, int, int],
) -> None:
    if kind == 0:
        return
    x0, y0, x1, y1 = box
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2

    def poly(pts: list[tuple[float, float]]) -> None:
        d.polygon(_identicon_map(_identicon_rot(pts, turns), box), fill=color)

    if kind == 1:
        poly([(0, 0), (1, 0), (1, 1), (0, 1)])
    elif kind == 2:
        poly([(0, 1), (1, 1), (0.5, 0)])
    elif kind == 3:
        poly([(0, 0), (1, 0), (0, 1)])
    elif kind == 4:
        poly([(0, 0), (1, 0), (1, 1)])
    elif kind == 5:
        poly([(0.5, 0), (1, 0.5), (0.5, 1), (0, 0.5)])
    elif kind == 6:
        d.ellipse([x0, y0, x1, y1], fill=color)
    elif kind == 7:
        start = (turns % 4) * 90
        d.pieslice([x0, y0, x1, y1], start, start + 90, fill=color)
    elif kind == 8:
        poly([(0, 0), (1, 0), (0.5, 0.45), (1, 1), (0, 1), (0.5, 0.55)])
    elif kind == 9:
        poly([(0, 0.25), (1, 0), (1, 0.75), (0, 1)])
    elif kind == 10:
        poly([(0.18, 0), (0.82, 0), (1, 1), (0, 1)])
    elif kind == 11:
        if turns % 2 == 0:
            d.rectangle([x0, y0, x1, my], fill=color)
        else:
            d.rectangle([x0, y0, mx, y1], fill=color)
    elif kind == 12:
        t = max(1.0, (x1 - x0) * 0.22)
        d.rectangle([mx - t, y0, mx + t, y1], fill=color)
        d.rectangle([x0, my - t, x1, my + t], fill=color)
    elif kind == 13:
        poly([(0, 0), (1, 0.35), (1, 1), (0, 0.65)])
    elif kind == 14:
        poly([(0, 0), (1, 0), (0.35, 0.5), (1, 1), (0, 1)])
    else:
        d.chord([x0, y0, x1, y1], (turns % 4) * 90, (turns % 4) * 90 + 180, fill=color)


def render_identicon(
    digest: bytes,
    size: int,
    back: tuple[int, int, int, int] | None,
) -> Image.Image:
    bits = BitPump(digest)
    bg = back if back is not None else (255, 255, 255, 255)
    hue = bits.take(8) * 360 / 256
    fg1 = hsl(hue, 58 + bits.take(4), 40 + bits.take(3))
    fg2 = hsl(hue + 28 + bits.take(6), 50 + bits.take(4), 58 + bits.take(3))
    work = size * 2 if size < 512 else size
    img = Image.new("RGBA", (work, work), bg)
    d = ImageDraw.Draw(img)
    cols = 5
    pad = work * 0.07
    inner = work - 2 * pad
    cell = inner / cols
    inset = cell * 0.04
    # Left-right mirror of the left half (center column drawn once).
    for row in range(cols):
        for col in range((cols + 1) // 2):
            kind = 1 + bits.take(4) % 15
            if bits.take(4) == 0:
                continue
            turns = bits.take(2)
            color = fg1 if bits.take(1) == 0 else fg2
            boxes = [(col, row)]
            mirror_col = cols - 1 - col
            if mirror_col != col:
                boxes.append((mirror_col, row))
            for c, r in boxes:
                x0 = pad + c * cell + inset
                y0 = pad + r * cell + inset
                x1 = pad + (c + 1) * cell - inset
                y1 = pad + (r + 1) * cell - inset
                _draw_identicon_patch(d, (x0, y0, x1, y1), kind, turns, color)
    if work != size:
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    return img

