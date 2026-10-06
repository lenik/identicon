#!/usr/bin/env python3
# Copyright (C) 2026 Lenik <identicon@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import math

from PIL import Image, ImageDraw

from pixgrid import _rng, hsl

def render_wavatar(
    digest: bytes,
    size: int,
    back: tuple[int, int, int, int] | None,
) -> Image.Image:
    rng = _rng(digest)
    work = min(1024, max(size * 4, 256))
    bg = back if back is not None else hsl(rng.randrange(360), 55, 78)
    img = Image.new("RGBA", (work, work), bg)
    d = ImageDraw.Draw(img)
    cx = cy = work / 2
    head_r = work * rng.uniform(0.32, 0.38)
    skin = hsl(rng.choice((12, 24, 28, 36, 40)), rng.uniform(35, 55), rng.uniform(62, 82))
    hair_c = hsl(rng.randrange(360), rng.uniform(40, 80), rng.uniform(18, 45))
    eye_white = (250, 250, 250, 255)
    iris = hsl(rng.choice((200, 220, 140, 30, 280)), 55, 40)
    line = hsl(20, 40, 22)

    hair_style = rng.randrange(5)
    if hair_style == 0:
        d.ellipse(
            [cx - head_r * 1.15, cy - head_r * 1.45, cx + head_r * 1.15, cy - head_r * 0.1],
            fill=hair_c,
        )
    elif hair_style == 1:
        d.ellipse(
            [cx - head_r * 1.05, cy - head_r * 1.25, cx + head_r * 1.05, cy + head_r * 0.2],
            fill=hair_c,
        )
    elif hair_style == 2:
        for side in (-1, 1):
            d.ellipse(
                [
                    cx + side * head_r * 0.85 - head_r * 0.28,
                    cy - head_r * 1.05,
                    cx + side * head_r * 0.85 + head_r * 0.28,
                    cy - head_r * 0.45,
                ],
                fill=hair_c,
            )
    elif hair_style == 3:
        for i in range(7):
            ang = -80 + i * 26
            px = cx + math.sin(ang * math.pi / 180) * head_r * 0.95
            py = cy - math.cos(ang * math.pi / 180) * head_r * 1.05
            spike = work * 0.07
            d.polygon(
                [(cx, cy - head_r * 0.2), (px - spike, py), (px + spike, py)],
                fill=hair_c,
            )

    if rng.random() < 0.55:
        ear_w = head_r * 0.22
        ear_h = head_r * 0.28
        for side in (-1, 1):
            d.ellipse(
                [
                    cx + side * head_r - ear_w,
                    cy - ear_h,
                    cx + side * head_r + ear_w,
                    cy + ear_h,
                ],
                fill=skin,
            )

    d.ellipse([cx - head_r, cy - head_r, cx + head_r, cy + head_r], fill=skin)

    eye_y = cy - head_r * 0.12
    eye_dx = head_r * rng.uniform(0.32, 0.42)
    eye_rx = head_r * rng.uniform(0.12, 0.18)
    eye_ry = eye_rx * rng.uniform(0.85, 1.25)
    wink = rng.randrange(8)
    for i, side in enumerate((-1, 1)):
        ex = cx + side * eye_dx
        closed = (wink == 1 and i == 0) or (wink == 2 and i == 1) or wink == 3
        if closed:
            d.arc(
                [ex - eye_rx, eye_y - eye_ry / 2, ex + eye_rx, eye_y + eye_ry],
                200,
                340,
                fill=line,
                width=max(2, work // 80),
            )
        else:
            d.ellipse([ex - eye_rx, eye_y - eye_ry, ex + eye_rx, eye_y + eye_ry], fill=eye_white, outline=line)
            pr = eye_rx * 0.45
            d.ellipse([ex - pr, eye_y - pr, ex + pr, eye_y + pr], fill=iris)
            hl = pr * 0.35
            d.ellipse([ex - hl * 0.2, eye_y - pr * 0.5, ex + hl, eye_y - pr * 0.05], fill=(255, 255, 255, 255))

    if rng.random() < 0.7:
        brow_y = eye_y - eye_ry * 1.6
        w = max(2, work // 90)
        for side in (-1, 1):
            tilt = rng.uniform(-8, 12)
            x0 = cx + side * (eye_dx - eye_rx)
            x1 = cx + side * (eye_dx + eye_rx)
            d.line([(x0, brow_y + tilt), (x1, brow_y - tilt * 0.3)], fill=hair_c, width=w)

    mouth_y = cy + head_r * 0.38
    mw = head_r * rng.uniform(0.28, 0.45)
    mouth = rng.randrange(6)
    w = max(2, work // 70)
    if mouth == 0:
        d.arc([cx - mw, mouth_y - mw * 0.4, cx + mw, mouth_y + mw * 0.7], 20, 160, fill=line, width=w)
    elif mouth == 1:
        d.arc([cx - mw, mouth_y - mw * 0.5, cx + mw, mouth_y + mw * 0.4], 200, 340, fill=line, width=w)
    elif mouth == 2:
        d.line([(cx - mw, mouth_y), (cx + mw, mouth_y)], fill=line, width=w)
    elif mouth == 3:
        d.ellipse([cx - mw * 0.35, mouth_y - mw * 0.25, cx + mw * 0.35, mouth_y + mw * 0.35], fill=line)
    elif mouth == 4:
        d.arc([cx - mw, mouth_y - mw * 0.1, cx + mw, mouth_y + mw * 0.9], 10, 170, fill=line, width=w)
        d.chord([cx - mw * 0.7, mouth_y, cx + mw * 0.7, mouth_y + mw * 0.7], 0, 180, fill=(220, 80, 90, 255))
    else:
        d.polygon(
            [(cx - mw, mouth_y), (cx + mw * 0.1, mouth_y - mw * 0.15), (cx + mw, mouth_y + mw * 0.1)],
            outline=line,
        )

    if rng.random() < 0.25:
        d.arc(
            [cx - head_r * 0.55, cy - head_r * 0.05, cx + head_r * 0.55, cy + head_r * 0.55],
            200,
            340,
            fill=(40, 40, 40, 255),
            width=max(2, work // 70),
        )
        for side in (-1, 1):
            d.ellipse(
                [
                    cx + side * head_r * 0.55 - head_r * 0.08,
                    cy - head_r * 0.02,
                    cx + side * head_r * 0.55 + head_r * 0.08,
                    cy + head_r * 0.14,
                ],
                fill=(40, 40, 40, 255),
            )

    if work != size:
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    return img

