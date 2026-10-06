#!/usr/bin/env python3
# Copyright (C) 2026 Lenik <identicon@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

from PIL import Image

from pixgrid import _rng, _scale_cells, hsl

def render_monsterid(
    digest: bytes,
    size: int,
    back: tuple[int, int, int, int] | None,
) -> Image.Image:
    rng = _rng(digest)
    n = 24
    bg = back if back is not None else (255, 255, 255, 255)
    cells = [[bg for _ in range(n)] for _ in range(n)]
    body = hsl(rng.randrange(360), rng.uniform(50, 85), rng.uniform(38, 62))
    dark = hsl(rng.randrange(360), 40, 18)
    accent = hsl(rng.randrange(360), 70, 55)
    eye_c = hsl(rng.randrange(360), 20, 92)

    def rect(x: int, y: int, w: int, h: int, c: tuple[int, int, int, int]) -> None:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if 0 <= xx < n and 0 <= yy < n:
                    cells[yy][xx] = c

    body_w = rng.randint(8, 12)
    body_h = rng.randint(8, 12)
    bx = (n - body_w) // 2
    by = n - body_h - 5
    rect(bx, by, body_w, body_h, body)

    leg_w = rng.randint(2, 3)
    for side in (0, 1):
        lx = bx + 1 + side * (body_w - leg_w - 2)
        rect(lx, by + body_h - 1, leg_w, 5, dark)
        rect(lx - 1, n - 2, leg_w + 2, 2, dark)

    arm_y = by + rng.randint(1, 3)
    arm_h = rng.randint(3, 6)
    rect(bx - 3, arm_y, 3, arm_h, body)
    rect(bx + body_w, arm_y, 3, arm_h, body)
    if rng.random() < 0.5:
        rect(bx - 3, arm_y + arm_h - 1, 3, 2, accent)
        rect(bx + body_w, arm_y + arm_h - 1, 3, 2, accent)

    head_w = rng.randint(body_w - 2, body_w + 2)
    head_h = rng.randint(6, 9)
    hx = (n - head_w) // 2
    hy = by - head_h + 2
    rect(hx, hy, head_w, head_h, body)

    horn = rng.randrange(4)
    if horn == 1:
        rect(hx + 1, hy - 3, 2, 4, accent)
        rect(hx + head_w - 3, hy - 3, 2, 4, accent)
    elif horn == 2:
        rect(hx + head_w // 2 - 1, hy - 4, 2, 5, dark)
    elif horn == 3:
        for i in range(head_w):
            if i % 2 == 0:
                rect(hx + i, hy - 2, 1, 2, accent)

    eyes = rng.choice((1, 2, 2, 2, 3))
    ey = hy + rng.randint(2, 3)
    if eyes == 1:
        xs = [hx + head_w // 2]
    elif eyes == 2:
        xs = [hx + 2, hx + head_w - 4]
    else:
        xs = [hx + 1, hx + head_w // 2 - 1, hx + head_w - 3]
    for x in xs:
        rect(x, ey, 3, 3, eye_c)
        rect(x + 1, ey + 1, 1, 1, dark)

    my = hy + head_h - 3
    mw = rng.randint(3, max(3, head_w - 4))
    mx = hx + (head_w - mw) // 2
    rect(mx, my, mw, 2, dark)
    if rng.random() < 0.6:
        for i in range(mx, mx + mw):
            if i % 2 == 0:
                rect(i, my, 1, 1, (255, 255, 255, 255))

    if rng.random() < 0.4:
        rect(bx + body_w // 2 - 1, by + 2, 2, 3, accent)

    return _scale_cells(cells, size)

