#!/usr/bin/env python3
# Copyright (C) 2026 Lenik <identicon@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import gettext
import hashlib
import hmac
import io
import locale
import os
from pathlib import Path
from typing import BinaryIO

from PIL import Image, ImageColor

TEXT_DOMAIN = "identicon"

TRANSPARENT = (0, 0, 0, 0)

_FORMAT_ALIASES = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "tif": "TIFF",
    "tiff": "TIFF",
    "png": "PNG",
    "gif": "GIF",
    "bmp": "BMP",
    "webp": "WEBP",
    "ico": "ICO",
}


def init_i18n(argv0: str) -> gettext.NullTranslations:
    locale.setlocale(locale.LC_ALL, "")

    localedir = os.environ.get("IDENTICON_LOCALEDIR")
    if not localedir and "/" in argv0:
        build_po = Path(argv0).resolve().parent / "po"
        if build_po.is_dir():
            localedir = str(build_po)

    trans = gettext.translation(TEXT_DOMAIN, localedir=localedir, fallback=True)
    trans.install()
    return trans


def program_version() -> str:
    env = os.environ.get("IDENTICON_VERSION")
    if env:
        return env.strip().lstrip("v")
    here = Path(__file__).resolve().parent
    for candidate in (here / "VERSION", here.parent / "VERSION"):
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").splitlines()[0].strip().lstrip("v")
    return "dev"


def digest_for(ident: str, salt: str | None) -> bytes:
    ident_b = ident.encode("utf-8")
    if salt:
        return hmac.new(salt.encode("utf-8"), ident_b, hashlib.sha256).digest()
    return hashlib.sha256(ident_b).digest()


def parse_color(text: str) -> tuple[int, int, int, int]:
    raw = text.strip()
    if raw.lower() in ("transparent", "none"):
        return TRANSPARENT
    try:
        rgb = ImageColor.getrgb(raw)
    except ValueError as e:
        raise ValueError(str(e)) from e
    if len(rgb) == 4:
        return (int(rgb[0]), int(rgb[1]), int(rgb[2]), int(rgb[3]))
    return (int(rgb[0]), int(rgb[1]), int(rgb[2]), 255)


def normalize_format(name: str) -> str:
    key = name.strip().lstrip(".").lower()
    if not key:
        raise ValueError("empty format")
    mapped = _FORMAT_ALIASES.get(key, key.upper())
    Image.init()
    if mapped not in Image.SAVE:
        raise ValueError(mapped)
    return mapped


def format_from_path(path: str) -> str | None:
    suffix = Path(path).suffix
    if not suffix:
        return None
    try:
        return normalize_format(suffix)
    except ValueError:
        return None


def image_for_save(img: Image.Image, fmt: str) -> Image.Image:
    needs_rgb = fmt in ("JPEG", "BMP")
    if fmt == "GIF" and img.mode == "RGBA":
        alpha = img.getchannel("A")
        if alpha.getextrema()[0] < 255:
            needs_rgb = False
            converted = img.convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
            return converted
        needs_rgb = True
    if needs_rgb and img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        return bg
    return img


def save_image(img: Image.Image, dest: BinaryIO, fmt: str) -> None:
    payload = image_for_save(img, fmt)
    kwargs: dict[str, object] = {"format": fmt}
    if fmt == "JPEG":
        kwargs["quality"] = 95
        kwargs["optimize"] = True
    if fmt == "PNG":
        kwargs["optimize"] = True
    payload.save(dest, **kwargs)


def image_bytes(img: Image.Image, fmt: str) -> bytes:
    buf = io.BytesIO()
    save_image(img, buf, fmt)
    return buf.getvalue()
