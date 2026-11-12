#!/usr/bin/env python3
"""Export per-character font outlines and metrics from a UTF-8 text file.

Requires Python 3.9+ and fontTools. This extracts cmap glyphs, not shaped text.
See ../references/fonts.md for the JSON schema, layout and compact decoding.
"""

import argparse
import json
import math
from pathlib import Path
import re
import sys
import unicodedata


NUMBER = r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?"
PATH_TOKEN = re.compile(NUMBER + r"|[A-Za-z]")
BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"


class MissingGlyphsError(ValueError):
    """One or more input characters have no mapped glyph in the chosen font."""


def base36(value):
    """Encode an integer; a minus sign is kept outside the base-36 digits."""
    if value == 0:
        return "0"
    sign = "-" if value < 0 else ""
    value = abs(value)
    digits = []
    while value:
        value, remainder = divmod(value, 36)
        digits.append(BASE36[remainder])
    return sign + "".join(reversed(digits))


def round_coordinate(value):
    """Round half away from zero, independently of Python's tie-to-even round."""
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Non-finite outline coordinate")
    return math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5)


def compact_path(path):
    """Uppercase SVG commands + comma-separated signed lowercase base-36 ints."""
    groups = []
    command = None
    operands = []
    for token in PATH_TOKEN.findall(path):
        if token in ("M", "L", "H", "V", "Q", "C", "Z", "z"):
            if command is not None:
                groups.append(command + ",".join(operands))
            command = token.upper()
            operands = []
        else:
            if command is None:
                raise ValueError("Outline does not start with an SVG command")
            operands.append(base36(round_coordinate(token)))
    if command is not None:
        groups.append(command + ",".join(operands))
    return "".join(groups)


def extract(font_path, text, compact=False, font_number=None, expected_postscript_name=None):
    # Public callers as well as the CLI use the same newline/BOM normalization.
    text = text.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    # Import lazily so --help remains available before installing the dependency.
    try:
        from fontTools.pens.boundsPen import BoundsPen
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.ttLib import TTFont
    except ImportError as error:
        raise RuntimeError(
            "fontTools is required in this Python environment. "
            "See the skill's references/fonts.md for virtual environment setup."
        ) from error

    options = {} if font_number is None else {"fontNumber": font_number}
    with TTFont(str(font_path), **options) as font:
        names = font["name"]
        postscript_name = names.getDebugName(6)
        if expected_postscript_name and postscript_name != expected_postscript_name:
            raise ValueError("Font identity mismatch: expected " + expected_postscript_name +
                             ", received " + str(postscript_name) + "; no fallback was used")
        font_identity = {"postscriptName": postscript_name,
                         "family": names.getDebugName(1), "fullName": names.getDebugName(4)}
        cmap = font.getBestCmap() or {}
        # Keep input order, deduplicate characters, preserve every space.
        characters = list(dict.fromkeys(char for char in text if char != "\n"))
        missing = [char for char in characters if cmap.get(ord(char)) in (None, ".notdef")]
        if missing:
            details = "\n".join(
                f"  U+{ord(char):04X} {json.dumps(char, ensure_ascii=False)} "
                f"({unicodedata.name(char, 'UNNAMED')})"
                for char in missing
            )
            raise MissingGlyphsError("Missing glyphs; no fallback was used:\n" + details)

        glyph_set = font.getGlyphSet()
        output = {}
        for char in characters:
            glyph = glyph_set[cmap[ord(char)]]
            path_pen = SVGPathPen(glyph_set)
            bounds_pen = BoundsPen(glyph_set)
            glyph.draw(path_pen)
            glyph.draw(bounds_pen)
            path = path_pen.getCommands()
            output[char] = {
                "d": compact_path(path) if compact else path,
                "a": glyph.width,
                "b": list(bounds_pen.bounds) if bounds_pen.bounds is not None else None,
            }

        return {
            "schemaVersion": 1,
            "fontIdentity": font_identity,
            "upem": font["head"].unitsPerEm,
            "pathEncoding": "base36-int-v1" if compact else "svg",
            "text": text,
            "glyphs": output,
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", required=True, type=Path, help="OTF/TTF font file (or TTC/OTC with --font-number)")
    parser.add_argument("--text", required=True, type=Path, help="UTF-8 text file; CRLF/CR become LF, optional BOM is removed")
    parser.add_argument("--output", type=Path, help="JSON destination; default: stdout. Written only after successful extraction.")
    parser.add_argument("--expected-postscript-name", help="Reject a different font instead of silently approximating")
    parser.add_argument("--compact", action="store_true", help="Round outline coordinates to integers and encode them in base 36")
    parser.add_argument("--font-number", type=int, help="Zero-based face index for a TTC/OTC collection")
    args = parser.parse_args(argv)
    try:
        if args.font_number is not None and args.font_number < 0:
            raise ValueError("--font-number must be nonnegative")
        if args.output and args.output.resolve() in (args.text.resolve(), args.font.resolve()):
            raise ValueError("Output must differ from the input text and font files")
        text = args.text.read_text(encoding="utf-8-sig")
        document = extract(args.font, text, args.compact, args.font_number, args.expected_postscript_name)
        data = json.dumps(
            document, ensure_ascii=False,
            indent=None if args.compact else 2,
            separators=(",", ":") if args.compact else None,
            allow_nan=False,
        ) + "\n"
        if args.output:
            args.output.write_text(data, encoding="utf-8")
        else:
            sys.stdout.write(data)
        return 0
    except MissingGlyphsError as error:
        print(str(error), file=sys.stderr)
        return 3
    except (OSError, UnicodeError, ValueError, KeyError, RuntimeError) as error:
        print(f"glyphs.py: {error}", file=sys.stderr)
        return 2
    except Exception as error:
        # fontTools may raise format-specific exceptions for unsupported files.
        print(f"glyphs.py: font extraction failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
