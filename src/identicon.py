#!/usr/bin/env python3
# Copyright (C) 2026 Lenik <identicon@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import getopt
import os
import sys
from typing import TextIO

from runtime import (
    digest_for,
    format_from_path,
    init_i18n,
    normalize_format,
    parse_color,
    program_version,
    save_image,
)
from styles import TYPES, normalize_type, render

DEFAULT_SIZE = 256
DEFAULT_FORMAT = "PNG"
DEFAULT_TYPE = "identicon"


def usage(out: TextIO) -> None:
    out.write(
        _("Usage: identicon [OPTION]... ID\n"
          "Generate a deterministic avatar image from ID.\n")
    )
    out.write("\n")
    out.write("  -s, --salt SALT    ")
    out.write(_("mix SALT into the hash (UTF-8)\n"))
    out.write("  -o, --out FILE     ")
    out.write(_("write the image to FILE; format follows the extension (default: stdout)\n"))
    out.write("  -t, --type TYPE    ")
    out.write(_("avatar style (default: identicon)\n"))
    out.write("                      identicon   ")
    out.write(_("kaleidoscopic pixel pattern\n"))
    out.write("                      wavatar     ")
    out.write(_("cartoon faces with varying expressions and background colors\n"))
    out.write("                      monsterid   ")
    out.write(_("colorful pixel monsters with distinctive looks\n"))
    out.write("                      retro       ")
    out.write(_("8-bit NES-era pixel faces\n"))
    out.write("                      robo        ")
    out.write(_("cute little robots\n"))
    out.write("  -F, --format FMT   ")
    out.write(_("image format: jpg, gif, png, bmp, ... (default: png)\n"))
    out.write("  -S, --size PIXELS  ")
    out.write(_("size in pixels (default: 256)\n"))
    out.write("  -b, --backcolor C  ")
    out.write(_("background color: name, #rgb, #rrggbb, or rgb/hsl[a](...)\n"))
    out.write("  -f, --force        ")
    out.write(_("overwrite FILE if it already exists\n"))
    out.write("  -v, --verbose      ")
    out.write(_("repeat for more verbose loggings\n"))
    out.write("  -q, --quiet        ")
    out.write(_("show less logging messages\n"))
    out.write("  -h, --help         ")
    out.write(_("display this help and exit\n"))
    out.write("      --version      ")
    out.write(_("output version information and exit\n"))
    out.write("\n")
    out.write(_("ID and SALT are UTF-8 encoded.\n"))
    out.write(_("Report bugs to: <{email}>\n").format(email="identicon@bodz.net"))


def version(out: TextIO) -> None:
    out.write(f"identicon {program_version()}\n")
    out.write(_("Copyright (C) {year} {author}\n").format(year=2026, author="Lenik"))
    out.write(_("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n"))
    out.write(_("This is free software: you are free to change and redistribute it.\n"))
    out.write(_("This project opposes AI exploitation and AI hegemony.\n"))
    out.write(
        _(
            "This project rejects mindless MIT-style licensing and politically naive "
            "BSD-style licensing.\n"
        )
    )
    out.write(_("There is NO WARRANTY, to the extent permitted by law.\n"))


def _error(program: str, message: str) -> int:
    print(f"{program}: {message}", file=sys.stderr)
    return 1


def main(argv: list[str]) -> int:
    init_i18n(argv[0])
    program = os.path.basename(argv[0]) or "identicon"

    try:
        opts, extra = getopt.gnu_getopt(
            argv[1:],
            "s:o:t:F:S:b:fvqh",
            [
                "salt=",
                "out=",
                "type=",
                "format=",
                "size=",
                "backcolor=",
                "force",
                "verbose",
                "quiet",
                "help",
                "version",
            ],
        )
    except getopt.GetoptError as e:
        return _error(program, str(e))

    salt: str | None = None
    out_path: str | None = None
    kind = DEFAULT_TYPE
    fmt_opt: str | None = None
    size = DEFAULT_SIZE
    back_text: str | None = None
    force = False
    verbose = 0

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(sys.stdout)
            return 0
        if opt == "--version":
            version(sys.stdout)
            return 0
        if opt in ("-v", "--verbose"):
            verbose += 1
        elif opt in ("-q", "--quiet"):
            verbose = -1
        elif opt in ("-s", "--salt"):
            salt = arg
        elif opt in ("-o", "--out"):
            out_path = arg
        elif opt in ("-t", "--type"):
            kind = arg
        elif opt in ("-F", "--format"):
            fmt_opt = arg
        elif opt in ("-S", "--size"):
            try:
                size = int(arg, 10)
            except ValueError:
                return _error(program, _("invalid size {value!r}").format(value=arg))
        elif opt in ("-b", "--backcolor"):
            back_text = arg
        elif opt in ("-f", "--force"):
            force = True

    if not extra:
        return _error(program, _("missing ID"))
    if len(extra) > 1:
        return _error(program, _("extra argument: {arg}").format(arg=extra[1]))
    ident = extra[0]

    try:
        kind = normalize_type(kind)
    except ValueError:
        return _error(
            program,
            _("unknown type {value!r} (expected {types})").format(
                value=kind,
                types=", ".join(TYPES),
            ),
        )

    if size < 1 or size > 4096:
        return _error(program, _("invalid size {value!r}").format(value=size))

    back = None
    if back_text is not None:
        try:
            back = parse_color(back_text)
        except ValueError as e:
            return _error(
                program,
                _("invalid color {value!r}: {err}").format(value=back_text, err=e),
            )

    fmt_name: str | None = None
    if fmt_opt is not None:
        try:
            fmt_name = normalize_format(fmt_opt)
        except ValueError:
            return _error(program, _("unknown format {value!r}").format(value=fmt_opt))
    elif out_path and out_path != "-":
        fmt_name = format_from_path(out_path)
    if fmt_name is None:
        fmt_name = DEFAULT_FORMAT

    dest_path = None if (not out_path or out_path == "-") else out_path
    if dest_path and os.path.exists(dest_path) and not force:
        return _error(
            program,
            _("{path} exists (use --force to overwrite)").format(path=dest_path),
        )

    digest = digest_for(ident, salt)
    img = render(kind, digest, size, back)

    if verbose > 0:
        dest_label = dest_path if dest_path else "-"
        print(
            f"{program}: type={kind} size={size} format={fmt_name.lower()} out={dest_label}",
            file=sys.stderr,
        )
        if verbose > 1:
            print(f"{program}: sha256={digest.hex()}", file=sys.stderr)

    try:
        if dest_path:
            with open(dest_path, "wb") as fh:
                save_image(img, fh, fmt_name)
        else:
            save_image(img, sys.stdout.buffer, fmt_name)
            sys.stdout.buffer.flush()
    except OSError as e:
        return _error(program, str(e))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
