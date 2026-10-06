#!/usr/bin/env python3
# Copyright (C) 2026 Lenik <identicon@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import colorsys
import math
import random
from typing import Callable

from PIL import Image, ImageDraw

TYPES = ("identicon", "wavatar", "monsterid", "retro", "robo")
ALIASES = {
    "robohash": "robo",
    "monster": "monsterid",
}

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


def _retro_hair(g: Pix, n: int, bits: BitPump, hair: tuple[int, int, int, int], level: int) -> None:
    style = bits.take(3)
    scalp = n // 7
    cx = n // 2
    face_l = n // 6
    face_r = n - face_l
    width = face_r - face_l
    if style == 0:
        for i in range(scalp + n // 10):
            shrink = i // 3
            g.fill(face_l + shrink, i, max(2, width - 2 * shrink), 1, hair)
    elif style == 1:
        for x in range(face_l, cx):
            h = scalp + ((x * 3) % max(2, n // 8)) + n // 14
            g.fill(x, 0, 1, h, hair, mirror=True)
    elif style == 2:
        g.fill(face_l, 0, width, scalp, hair)
        g.fill(cx - n // 8, 0, n // 4, scalp + n // 8, hair)
        g.fill(face_l - n // 16, scalp // 2, n // 8, n // 8, hair, mirror=True)
    elif style == 3:
        g.fill(face_l + n // 12, 0, width - n // 6, scalp + n // 12, hair)
        g.fill(face_l, scalp, n // 10, n // 8, hair, mirror=True)
    elif style == 4:
        g.fill(face_l + n // 10, 0, width - n // 5, scalp, hair)
        if level >= 16:
            g.fill(face_l + n // 8, scalp, n // 10, n // 9, hair, mirror=True)
    elif style == 5:
        g.disc(cx, scalp + n // 16, n // 5, hair)
        g.fill(cx - n // 6, 0, n // 3, scalp + n // 10, hair)
    else:
        g.fill(face_l + n // 14, 0, width - n // 7, scalp, hair)
        if level >= 24:
            for i in range(4):
                g.fill(face_l + n // 10 + i * n // 14, 0, max(1, n // 22), scalp + n // 10, hair, mirror=True)


def _retro_face_features(
    g: Pix,
    n: int,
    bits: BitPump,
    rng: random.Random,
    skin: tuple[int, int, int, int],
    hair: tuple[int, int, int, int],
    outline: tuple[int, int, int, int],
    eye: tuple[int, int, int, int],
    pupil: tuple[int, int, int, int],
    mouth_c: tuple[int, int, int, int],
    shirt: tuple[int, int, int, int],
    level: int,
) -> None:
    face_l = n // 6
    face_t = n // 7
    face_w = n - 2 * face_l
    face_h = n * 4 // 7
    if n >= 16:
        g.disc(n // 2, face_t + face_h // 2, face_w // 2, skin)
        g.fill(face_l + face_w // 8, face_t + face_h // 3, face_w * 3 // 4, face_h // 2, skin)
    else:
        g.fill(face_l, face_t, face_w, face_h, skin)
    if bits.take(1) and level >= 16:
        ear_h = max(2, n // 8)
        ear_w = max(1, n // 16)
        g.fill(face_l - ear_w, face_t + face_h // 3, ear_w, ear_h, skin, mirror=True)

    eye_y = face_t + face_h * 5 // 16
    eye_x = face_l + face_w // 5
    ew = max(1, n // 10 if level >= 16 else 1)
    eh = max(1, n // 12 if level >= 16 else 1)
    g.fill(eye_x, eye_y, ew, eh, eye, mirror=True)
    pw = max(1, ew // 2)
    g.fill(eye_x + ew - pw, eye_y + eh // 4, pw, max(1, eh // 2), pupil, mirror=True)
    if level >= 24 and bits.take(1):
        g.fill(eye_x, eye_y - max(1, n // 20), ew + 1, max(1, n // 24), hair, mirror=True)
    if level >= 32 and bits.take(1):
        g.fill(eye_x - 1, eye_y, ew + 2, 1, outline, mirror=True)
        g.fill(eye_x - 1, eye_y + eh, ew + 2, 1, outline, mirror=True)

    if level >= 16 and bits.take(1):
        g.put(n // 2, eye_y + eh + max(1, n // 20), outline)

    mouth_y = face_t + face_h * 3 // 4
    mw = max(2, face_w // 3)
    mx = n // 2 - mw // 2
    expr = bits.take(3)
    if expr == 0:
        g.fill(mx, mouth_y, mw, max(1, n // 24), mouth_c)
    elif expr == 1:
        g.fill(mx, mouth_y, mw, max(1, n // 20), mouth_c)
        if level >= 16:
            g.fill(mx, mouth_y, 1, max(1, n // 16), mouth_c, mirror=True)
    elif expr == 2:
        g.fill(mx + mw // 4, mouth_y, mw // 2, max(1, n // 16), mouth_c)
    elif expr == 3:
        g.fill(mx, mouth_y, mw, max(1, n // 12), mouth_c)
        if level >= 24:
            for i in range(mx, mx + mw, max(1, n // 16)):
                g.put(i, mouth_y, (255, 255, 255, 255))
    elif expr == 4:
        g.fill(mx, mouth_y - 1, mw, 1, mouth_c)
        g.fill(mx, mouth_y, 1, max(1, n // 16), mouth_c, mirror=True)
    else:
        g.fill(mx + 1, mouth_y, mw - 2, max(1, n // 20), mouth_c)
        if level >= 32:
            g.put(n // 2, mouth_y + 1, (220, 80, 90, 255))

    if level >= 24 and bits.take(1):
        blush = (240, 140, 140, 255)
        g.fill(face_l + 1, eye_y + eh + 1, max(1, n // 12), max(1, n // 20), blush, mirror=True)

    if level >= 32 and bits.take(1):
        gy = eye_y - 1
        g.fill(eye_x - 2, gy, n // 2 - (eye_x - 2) + ew, max(1, n // 18), outline)

    neck_y = face_t + face_h
    if level >= 16:
        g.fill(n // 2 - n // 10, neck_y, n // 5, max(1, n // 16), skin)
        shirt_y = neck_y + max(1, n // 16)
        g.fill(n // 4, shirt_y, n // 2, max(1, n - shirt_y), shirt)
        if level >= 32 and bits.take(1):
            g.fill(n // 2 - 1, neck_y + n // 10, 2, max(2, n // 8), hair)


def render_retro(
    digest: bytes,
    size: int,
    back: tuple[int, int, int, int] | None,
) -> Image.Image:
    bits = BitPump(digest)
    rng = _rng(digest)
    n = _lod_n(size)
    bg = back if back is not None else hsl(rng.randrange(360), 40, 82)
    skin = (*rng.choice(NES[1:12]), 255)
    hair = (*rng.choice(NES), 255)
    outline = (24, 24, 32, 255)
    eye = (248, 248, 248, 255)
    pupil = (24, 24, 40, 255)
    mouth_c = (168, 40, 40, 255)
    shirt = hsl(rng.randrange(360), 55, 48)
    g = Pix(n, bg)
    _retro_hair(g, n, bits, hair, n)
    _retro_face_features(g, n, bits, rng, skin, hair, outline, eye, pupil, mouth_c, shirt, n)
    if n >= 32 and bits.take(1):
        hat = hsl(rng.randrange(360), 60, 42)
        g.fill(n // 6, 0, n * 2 // 3, max(2, n // 10), hat)
        g.fill(n // 8, max(1, n // 12), n * 3 // 4, max(1, n // 16), hat)
    return g.image(size)


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


_RENDERERS: dict[str, Callable[..., Image.Image]] = {
    "identicon": render_identicon,
    "wavatar": render_wavatar,
    "monsterid": render_monsterid,
    "retro": render_retro,
    "robo": render_robo,
}
