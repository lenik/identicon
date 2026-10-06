from __future__ import annotations

import io
import os
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from runtime import digest_for, parse_color, save_image
from identicon import main
from robohash_style import MissingRobohashError, robohash_resource_dir
from styles import BUILTIN_TYPES, normalize_type, render


class ColorTests(unittest.TestCase):
    def test_named_and_hex(self) -> None:
        self.assertEqual(parse_color("red")[:3], (255, 0, 0))
        self.assertEqual(parse_color("#ff0000")[:3], (255, 0, 0))
        self.assertEqual(parse_color("#f00")[:3], (255, 0, 0))

    def test_rgb_hsl(self) -> None:
        self.assertEqual(parse_color("rgb(255, 0, 0)")[:3], (255, 0, 0))
        r, g, b, a = parse_color("hsl(0, 100%, 50%)")
        self.assertEqual((r, g, b, a), (255, 0, 0, 255))

    def test_transparent(self) -> None:
        self.assertEqual(parse_color("transparent"), (0, 0, 0, 0))


class RenderTests(unittest.TestCase):
    def test_all_types_size_and_determinism(self) -> None:
        d = digest_for("alice@example.com", "pepper")
        d2 = digest_for("alice@example.com", "other")
        for kind in BUILTIN_TYPES:
            a = render(kind, d, 64, None)
            b = render(kind, d, 64, None)
            c = render(kind, d2, 64, None)
            self.assertEqual(a.size, (64, 64))
            self.assertEqual(a.tobytes(), b.tobytes(), kind)
            self.assertNotEqual(a.tobytes(), c.tobytes(), kind)

    def test_utf8_salt_changes_digest(self) -> None:
        a = digest_for("名字", None)
        b = digest_for("名字", "盐")
        self.assertNotEqual(a, b)
        self.assertEqual(len(a), 32)

    def test_backcolor_fills_robo_corners(self) -> None:
        d = digest_for("bg", None)
        img = render("robo", d, 32, parse_color("#00ff00"))
        self.assertEqual(img.getpixel((0, 0))[:3], (0, 255, 0))

    def test_identicon_uses_geometry_not_fat_pixels(self) -> None:
        img = render("identicon", digest_for("geo", None), 128, None)
        colors = {img.getpixel((x, y)) for x in range(0, 128, 2) for y in range(0, 128, 2)}
        self.assertGreater(len(colors), 8)

    def test_retro_lod_adds_detail(self) -> None:
        d = digest_for("lod-face", None)
        small = render("retro", d, 16, None).resize((256, 256), Image.Resampling.NEAREST)
        large = render("retro", d, 256, None)
        self.assertNotEqual(small.tobytes(), large.tobytes())

    def test_robo_variants_differ(self) -> None:
        seen = set()
        for i in range(8):
            img = render("robo", digest_for(f"bot-{i}", None), 64, None)
            seen.add(img.tobytes())
        self.assertEqual(len(seen), 8)


def _robohash_available() -> bool:
    try:
        robohash_resource_dir()
        return True
    except MissingRobohashError:
        return False


class RobohashTests(unittest.TestCase):
    def test_numeric_aliases(self) -> None:
        for i in range(1, 7):
            self.assertEqual(normalize_type(str(i)), f"set{i}")
            self.assertEqual(normalize_type(f"set{i}"), f"set{i}")

    @unittest.skipUnless(_robohash_available(), "Robohash sprite sets not vendored")
    def test_set1_and_alias_match(self) -> None:
        d = digest_for("robohash-user", "salt")
        a = render("set1", d, 32, None)
        b = render("1", d, 32, None)
        self.assertEqual(a.size, (32, 32))
        self.assertEqual(a.tobytes(), b.tobytes())

    @unittest.skipUnless(_robohash_available(), "Robohash sprite sets not vendored")
    def test_sets_determinism_and_salt(self) -> None:
        d = digest_for("alice@example.com", "pepper")
        d2 = digest_for("alice@example.com", "other")
        for kind in ("set1", "set6"):
            a = render(kind, d, 32, None)
            b = render(kind, d, 32, None)
            c = render(kind, d2, 32, None)
            self.assertEqual(a.tobytes(), b.tobytes(), kind)
            self.assertNotEqual(a.tobytes(), c.tobytes(), kind)

    @unittest.skipUnless(_robohash_available(), "Robohash sprite sets not vendored")
    def test_backcolor_under_transparency(self) -> None:
        img = render("set1", digest_for("bg-rh", None), 32, parse_color("#00ff00"))
        self.assertEqual(img.getpixel((0, 0))[:3], (0, 255, 0))


class CliTests(unittest.TestCase):
    def test_help_and_version(self) -> None:
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            self.assertEqual(main(["identicon", "-h"]), 0)
        self.assertIn("Usage:", buf.getvalue())
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            self.assertEqual(main(["identicon", "--version"]), 0)
        self.assertIn("identicon", buf.getvalue())

    def test_missing_id(self) -> None:
        err = io.StringIO()
        with patch("sys.stderr", err):
            self.assertEqual(main(["identicon"]), 1)
        self.assertIn("missing ID", err.getvalue())

    def test_write_png_and_force(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "out.png")
            self.assertEqual(main(["identicon", "-S", "48", "-o", path, "user"]), 0)
            with Image.open(path) as im:
                self.assertEqual(im.size, (48, 48))
            err = io.StringIO()
            with patch("sys.stderr", err):
                self.assertEqual(main(["identicon", "-o", path, "user"]), 1)
            self.assertIn("exists", err.getvalue())
            self.assertEqual(main(["identicon", "-f", "-o", path, "user"]), 0)

    def test_format_from_extension(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "face.jpg")
            self.assertEqual(
                main(["identicon", "-t", "retro", "-S", "32", "-o", path, "id"]),
                0,
            )
            with Image.open(path) as im:
                self.assertEqual(im.format, "JPEG")

    def test_stdout_png(self) -> None:
        buf = io.BytesIO()

        class _Stdout:
            buffer = buf

        with patch("sys.stdout", _Stdout()):
            self.assertEqual(main(["identicon", "-S", "16", "x"]), 0)
        img = Image.open(io.BytesIO(buf.getvalue()))
        self.assertEqual(img.format, "PNG")
        self.assertEqual(img.size, (16, 16))


class SaveTests(unittest.TestCase):
    def test_jpeg_from_rgba(self) -> None:
        img = render("robo", digest_for("r", None), 24, None)
        buf = io.BytesIO()
        save_image(img, buf, "JPEG")
        out = Image.open(io.BytesIO(buf.getvalue()))
        self.assertEqual(out.format, "JPEG")


if __name__ == "__main__":
    unittest.main()
