#!/usr/bin/env python3
# Copyright (C) 2026 Lenik <identicon@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

from PIL import Image

from pixgrid import Pix, _lod_n, _rng, hsl

def _robo_line(
    g: Pix,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int, int],
    thick: int,
) -> None:
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(steps + 1):
        x = int(x0 + (x1 - x0) * i / steps)
        y = int(y0 + (y1 - y0) * i / steps)
        g.fill(x - thick // 2, y - thick // 2, max(1, thick), max(1, thick), color)


def _robo_hand(
    g: Pix,
    x: int,
    y: int,
    style: int,
    facing: int,
    metal: tuple[int, int, int, int],
    dark: tuple[int, int, int, int],
    glow: tuple[int, int, int, int],
    s: int,
) -> None:
    if style == 0:
        g.disc(x, y, max(1, s), metal)
        g.put(x, y, glow)
    elif style == 1:
        g.fill(x - s, y - s // 2, s * 2, s, metal)
        g.fill(x + facing * s, y - s, 1, s * 2, dark)
    elif style == 2:
        g.fill(x - s, y - s, s * 2, s * 2, metal)
        g.fill(x + facing * (s - 1), y, s, 1, dark)
        g.fill(x + facing * (s - 1), y + s // 2, s, 1, dark)
    else:
        g.fill(x - s, y - s // 2, s * 2 + 1, s, metal)
        g.fill(x + facing * s, y - s, max(1, s // 2), s * 2, glow)


def _robo_foot(
    g: Pix,
    x: int,
    y: int,
    style: int,
    metal: tuple[int, int, int, int],
    dark: tuple[int, int, int, int],
    s: int,
) -> None:
    if style == 0:
        g.fill(x - s, y, s * 2 + 1, max(1, s), dark)
    elif style == 1:
        g.disc(x, y, s, metal)
        g.fill(x - s, y + s // 2, s * 2 + 1, max(1, s // 2), dark)
    elif style == 2:
        g.fill(x - s - 1, y - 1, s * 2 + 3, s + 1, metal)
        g.fill(x - s, y, s * 2 + 1, s, dark)
    else:
        g.fill(x - s // 2, y - s, s + 1, s * 2, metal)
        g.fill(x - s, y + s // 2, s * 2 + 1, max(1, s // 2), dark)


def _robo_eyes(
    g: Pix,
    hx: int,
    hy: int,
    hw: int,
    hh: int,
    style: int,
    glow: tuple[int, int, int, int],
    dark: tuple[int, int, int, int],
    visor: tuple[int, int, int, int],
    n: int,
) -> None:
    ey = hy + max(1, hh // 3)
    if style == 0:
        gap = max(2, hw // 4)
        er = max(1, n // 24)
        g.disc(hx + hw // 2 - gap, ey, er, glow)
        g.disc(hx + hw // 2 + gap, ey, er, glow)
    elif style == 1:
        g.fill(hx + 2, ey - 1, hw - 4, max(2, hh // 5), visor)
        g.fill(hx + 3, ey, max(1, hw // 6), max(1, hh // 8), glow)
        g.fill(hx + hw - 3 - hw // 6, ey, max(1, hw // 6), max(1, hh // 8), glow)
    elif style == 2:
        g.disc(hx + hw // 2, ey, max(2, n // 16), glow)
        g.put(hx + hw // 2, ey, dark)
    elif style == 3:
        s = max(1, n // 20)
        for dx in (-1, 1):
            cx = hx + hw // 2 + dx * hw // 5
            g.fill(cx - s, ey, s * 2 + 1, 1, glow)
            g.fill(cx, ey - s, 1, s * 2 + 1, glow)
    elif style == 4:
        for dx in (-1, 1):
            cx = hx + hw // 2 + dx * hw // 5
            g.fill(cx - 2, ey, 4, 1, dark)
    elif style == 5:
        for i, dx in enumerate((-1, 0, 1)):
            g.disc(hx + hw // 2 + dx * hw // 5, ey, max(1, n // 28), glow)
    else:
        g.fill(hx + 2, ey - max(1, hh // 8), hw - 4, max(2, hh // 4), visor)
        g.fill(hx + hw // 4, ey - 1, max(2, hw // 6), max(2, hh // 6), glow)
        g.fill(hx + hw - hw // 4 - hw // 6, ey - 1, max(2, hw // 6), max(2, hh // 6), glow)


def _robo_mouth(
    g: Pix,
    hx: int,
    hy: int,
    hw: int,
    hh: int,
    expr: int,
    dark: tuple[int, int, int, int],
    glow: tuple[int, int, int, int],
    n: int,
) -> None:
    my = hy + hh * 2 // 3
    mw = max(2, hw // 3)
    mx = hx + (hw - mw) // 2
    if expr == 0:
        g.fill(mx, my, mw, 1, dark)
        g.put(mx, my - 1, dark)
        g.put(mx + mw - 1, my - 1, dark)
    elif expr == 1:
        g.fill(mx, my, mw, 1, dark)
        g.put(mx, my + 1, dark)
        g.put(mx + mw - 1, my + 1, dark)
    elif expr == 2:
        g.fill(mx + mw // 4, my, max(2, mw // 2), max(2, n // 20), dark)
    elif expr == 3:
        g.fill(mx, my, mw, max(2, n // 16), dark)
        for i in range(mx, mx + mw, max(1, n // 20)):
            g.put(i, my, glow)
    elif expr == 4:
        g.fill(mx, my, mw, 1, dark)
    elif expr == 5:
        g.fill(mx, my, mw, 1, dark)
        g.fill(mx + mw // 2, my, 1, max(1, n // 16), dark)
        g.fill(mx + mw // 2, my + max(1, n // 16), mw // 3, 1, glow)
    elif expr == 6:
        g.fill(mx, my, 1, 2, dark)
        g.fill(mx + mw - 1, my, 1, 2, dark)
        g.fill(mx, my + 2, mw, 1, dark)
    else:
        g.fill(mx, my, mw, max(1, n // 18), glow)
        g.fill(mx, my, mw, 1, dark)


def render_robo(
    digest: bytes,
    size: int,
    back: tuple[int, int, int, int] | None,
) -> Image.Image:
    rng = _rng(digest)
    n = _lod_n(size, min_n=16)
    bg = back if back is not None else hsl(rng.randrange(360), 42, 84)
    body_c = hsl(rng.randrange(360), rng.uniform(40, 80), rng.uniform(42, 64))
    dark = hsl(rng.randrange(360), 25, 18)
    visor = hsl(rng.choice((190, 210, 130, 280)), 55, 28)
    glow = hsl(rng.choice((50, 180, 110, 0, 300)), 80, 58)
    accent = hsl(rng.randrange(360), 70, 50)
    g = Pix(n, bg)

    hw = max(6, int(n * rng.choice((0.38, 0.44, 0.50, 0.56, 0.62))))
    hh = max(5, int(n * rng.choice((0.26, 0.30, 0.34, 0.40))))
    hx = (n - hw) // 2
    hy = max(int(n * 0.22), 4)
    bw = max(6, int(n * rng.choice((0.32, 0.40, 0.48, 0.56))))
    bh = max(5, int(n * rng.choice((0.22, 0.28, 0.34))))
    bx = (n - bw) // 2
    by = hy + hh - max(2, n // 14)
    if by + bh > n - 3:
        bh = max(4, n - 3 - by)

    limb_c = accent if rng.random() < 0.45 else body_c

    inner = (bx + 2, by + 2, bx + bw - 2, by + bh - 2)
    shoulder_y = by + max(1, bh // 6)
    arm_thick = 2 if n < 24 else 3 if n < 40 else 4
    arm_pose = rng.randrange(4)
    hand_style = rng.randrange(4)
    foot_style = rng.randrange(4)
    leg_style = rng.randrange(4)
    hip_y = by + bh - 1
    foot_y = n - 2

    for k, side in enumerate((-1, 1)):
        lx = n // 2 + side * max(2, bw // 4)
        if leg_style == 0:
            _robo_line(g, lx, hip_y, lx, foot_y - 1, limb_c, arm_thick)
        elif leg_style == 1:
            _robo_line(g, lx, hip_y, lx + side, foot_y - 1, limb_c, arm_thick + 1)
        elif leg_style == 2:
            g.fill(lx - 1, hip_y, 3, foot_y - hip_y, dark)
        else:
            _robo_line(g, lx, hip_y, lx, hip_y + (foot_y - hip_y) // 2, limb_c, arm_thick)
            g.disc(lx, foot_y - 1, max(2, n // 16), dark)
            if k == 0 and rng.random() < 0.08:
                break
            continue
        _robo_foot(g, lx, foot_y - 1, foot_style, limb_c, dark, max(1, n // 18))
        if k == 0 and rng.random() < 0.08:
            break

    for side in (-1, 1):
        sx = bx if side < 0 else bx + bw - 1
        if arm_pose == 0:
            hx_ = sx + side * (n // 6)
            hy_ = by + bh - 2
            _robo_line(g, sx, shoulder_y, hx_, hy_, limb_c, arm_thick)
        elif arm_pose == 1:
            hx_ = sx + side * (n // 5)
            hy_ = shoulder_y + 1
            _robo_line(g, sx, shoulder_y, hx_, hy_, limb_c, arm_thick)
        elif arm_pose == 2:
            hx_ = sx + side * (n // 8)
            hy_ = hy + hh // 3
            _robo_line(g, sx, shoulder_y, hx_, hy_, limb_c, arm_thick)
        else:
            hx_ = sx + side * (n // 6)
            hy_ = by + bh // 2
            _robo_line(g, sx, shoulder_y, hx_, shoulder_y + 1, limb_c, arm_thick)
            _robo_line(g, hx_, shoulder_y + 1, hx_, hy_, limb_c, arm_thick)
        _robo_hand(g, hx_, hy_, hand_style, side, limb_c, dark, glow, max(1, n // 20))

    body_shape = rng.randrange(4)
    if body_shape == 0:
        g.fill(bx, by, bw, bh, body_c)
    elif body_shape == 1:
        g.fill(bx + 1, by, bw - 2, bh, body_c)
        g.fill(bx, by + 1, bw, bh - 2, body_c)
    elif body_shape == 2:
        for i in range(bh):
            inset = i * (bw // 6) // max(1, bh)
            g.fill(bx + inset, by + i, max(2, bw - 2 * inset), 1, body_c)
    else:
        g.fill(bx, by, bw, bh, body_c)
        g.fill(bx - 1, by + bh // 3, bw + 2, bh // 3, body_c)

    neck_w = max(2, min(hw, bw) // 3)
    g.fill(n // 2 - neck_w // 2, hy + hh - 1, neck_w, max(2, by - (hy + hh) + 3), body_c)

    nbtn = rng.randrange(4)
    btn_space = max(1, inner[3] - inner[1])
    if nbtn and btn_space >= 3:
        for i in range(nbtn):
            byy = inner[1] + 1 + i * max(2, btn_space // (nbtn + 1))
            g.fill(n // 2 - 1, byy, 2, min(2, inner[3] - byy), glow, clip=inner)

    if n >= 24 and rng.random() < 0.45:
        panel_h = max(1, min(bh // 5, inner[3] - inner[1] - 1))
        g.fill(bx + 2, by + 2, bw - 4, panel_h, visor, clip=inner)

    head_shape = rng.randrange(4)
    if head_shape == 0:
        g.fill(hx, hy, hw, hh, body_c)
    elif head_shape == 1:
        g.fill(hx + 1, hy, hw - 2, hh, body_c)
        g.fill(hx, hy + 1, hw, hh - 2, body_c)
    elif head_shape == 2:
        g.disc(hx + hw // 2, hy + hh // 2, min(hw, hh) // 2, body_c)
        g.fill(hx + 2, hy + hh // 3, hw - 4, hh // 2, body_c)
    else:
        g.fill(hx, hy + 2, hw, hh - 2, body_c)
        g.fill(hx + 2, hy, hw - 4, 3, body_c)

    _robo_eyes(g, hx, hy, hw, hh, rng.randrange(7), glow, dark, visor, n)
    _robo_mouth(g, hx, hy, hw, hh, rng.randrange(8), dark, glow, n)

    n_ant = rng.choice((0, 1, 1, 2, 2, 3))
    tip = rng.randrange(3)
    if n_ant == 0:
        xs = []
    elif n_ant == 1:
        xs = [hx + hw // 2]
    elif n_ant == 2:
        xs = [hx + hw // 4, hx + 3 * hw // 4]
    else:
        xs = [hx + 2, hx + hw // 2, hx + hw - 3]
    max_ah = max(2, hy - 1)
    for ax in xs:
        ah = rng.randint(2, max_ah)
        g.fill(ax, hy - ah, 1, ah + 1, dark)
        ty = hy - ah
        if tip == 0:
            g.disc(ax, ty, max(1, n // 24), glow)
        elif tip == 1:
            g.fill(ax - 1, ty - 1, 3, 2, accent)
        else:
            g.put(ax, max(0, ty - 1), glow)

    return g.image(size)

