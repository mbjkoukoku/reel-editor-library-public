#!/usr/bin/env python3
"""Portable CLI regression tests. Run: python3 -m unittest discover -s scripts."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import glyphs


HERE = Path(__file__).resolve().parent
FONT = HERE.parent / "assets" / "fonts" / "NotoSerifCJKjp-Black.otf"


class GlyphTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.text = Path(self.temporary.name) / "text.txt"

    def run_cli(self, text, *options):
        self.text.write_bytes(text if isinstance(text, bytes) else text.encode("utf-8"))
        return subprocess.run(
            [sys.executable, str(HERE / "glyphs.py"), "--font", str(FONT),
             "--text", str(self.text), *options],
            capture_output=True, text=True, encoding="utf-8", env=os.environ.copy(),
        )

    def test_japanese_digits_spaces_and_line_endings(self):
        result = self.run_cli("\ufeff青空整体院\r\n初回 3,500円　予約受付中\r\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["text"], "青空整体院\n初回 3,500円　予約受付中\n")
        self.assertEqual(data["upem"], 1000)
        self.assertNotIn("\n", data["glyphs"])
        for char in (" ", "　"):
            self.assertEqual(data["glyphs"][char]["d"], "")
            self.assertIsNone(data["glyphs"][char]["b"])
            self.assertGreater(data["glyphs"][char]["a"], 0)
        for char in "青空整体院350":
            self.assertTrue(data["glyphs"][char]["d"])
            self.assertEqual(len(data["glyphs"][char]["b"]), 4)
        self.assertEqual(data["glyphs"]["青"]["a"], 1000)

    def test_compact_roundtrip_preserves_commands_and_metrics(self):
        normal = json.loads(self.run_cli("青空整体院 3,500円").stdout)
        compact = json.loads(self.run_cli("青空整体院 3,500円", "--compact").stdout)
        self.assertEqual(compact["pathEncoding"], "base36-int-v1")
        for char, source in normal["glyphs"].items():
            encoded = compact["glyphs"][char]
            decoded = re.sub(r"-?[0-9a-z]+", lambda match: str(int(match[0], 36)), encoded["d"])
            expected = [token.upper() if token in "MLHVQCZz" else str(glyphs.round_coordinate(token))
                        for token in glyphs.PATH_TOKEN.findall(source["d"])]
            self.assertEqual(glyphs.PATH_TOKEN.findall(decoded), expected)
            self.assertEqual(encoded["a"], source["a"])
            self.assertEqual(encoded["b"], source["b"])
        self.assertLess(len(json.dumps(compact)), len(json.dumps(normal)))

    def test_fractional_coordinates_and_base36_letters(self):
        self.assertEqual(glyphs.compact_path("M35.5 -35.5Q1e2 0 0.49 -0.49z"), "M10,-10Q2s,0,0,0Z")
        self.assertEqual(glyphs.compact_path("M10 11H35V36z"), "Ma,bHzV10Z")

    def test_missing_glyphs_fail_without_replacing_output(self):
        destination = Path(self.temporary.name) / "result.json"
        destination.write_text("previous result", encoding="utf-8")
        result = self.run_cli("青空整体院\U0001fae0\U0010ffff", "--output", str(destination))
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn("U+1FAE0", result.stderr)
        self.assertIn("U+10FFFF", result.stderr)
        self.assertEqual(destination.read_text(encoding="utf-8"), "previous result")

    def test_wrong_font_identity_is_rejected_without_fallback(self):
        result = self.run_cli("青空整体院", "--expected-postscript-name", "VDL-V7Mincho-Ultra")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Font identity mismatch", result.stderr)
        self.assertEqual(result.stdout, "")
        result = self.run_cli("青空整体院", "--expected-postscript-name", "NotoSerifCJKjp-Black")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["fontIdentity"]["postscriptName"], "NotoSerifCJKjp-Black")

    def test_invalid_utf8_fails(self):
        result = self.run_cli(b"\xff")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
