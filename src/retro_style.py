#!/usr/bin/env python3
# Copyright (C) 2026 Lenik <identicon@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import random

from PIL import Image

from pixgrid import NES, BitPump, Pix, _lod_n, _rng, hsl

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

