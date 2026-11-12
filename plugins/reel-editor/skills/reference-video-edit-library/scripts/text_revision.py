#!/usr/bin/env python3
"""Prepare a text-only revision plus complete glyphs, preserving cut/audio timing.

The caller applies this revision using current ChatCut tools. This script never
uses Transcript delete, which may remove video/audio as well as words.
"""
import argparse
import copy
import json
from pathlib import Path
import sys
from glyphs import extract, MissingGlyphsError
from timeline_plan import caption_line_limit


def prepare(plan, cue_key, text, font_path, font_number=0):
    if not isinstance(font_number, int) or isinstance(font_number, bool) or font_number < 0:
        raise ValueError("--font-number must be a nonnegative integer")
    revised = copy.deepcopy(plan)
    matches = [cue for cue in revised["cues"] if cue["key"] == cue_key]
    if len(matches) != 1:
        raise ValueError("Expected exactly one matching cue")
    if not text.strip():
        raise ValueError("Empty text is not a text replacement; explicitly request cue removal")
    cue = matches[0]
    if (plan.get("executionRoute") == "patient_vlog_with_sourced_cast"
            or plan.get("pattern", plan.get("id")) == "A07"):
        raise ValueError("A07 text revision must preserve clock/story cards and source labels; "
                         "follow references/a07.md")
    if (plan.get("executionRoute") == "speech_summary_design"
            or plan.get("pattern", plan.get("id")) == "A06"):
        raise ValueError("A06 text revision must retain grounded summary cards and original speech; "
                         "follow references/a06.md")
    if (plan.get("executionRoute") == "before_after_comparison"
            or plan.get("pattern", plan.get("id")) == "A05"):
        raise ValueError("A05 text revision must retain comparison stages, clinic palette and face mosaic; "
                         "follow references/a05.md")
    if (plan.get("executionRoute") == "speech_cleanup_then_overlays"
            or plan.get("pattern", plan.get("id")) == "A04"):
        raise ValueError("A04 text revision must retain speech timing and per-line backgrounds; "
                         "follow references/a04.md")
    if (plan.get("executionRoute") == "native_independent_overlays"
            or plan.get("pattern", plan.get("id")) == "A03"
            or cue.get("writingMode", "").startswith("vertical")):
        raise ValueError("Vertical/mixed caption layers require the A03 text revision workflow; "
                         "horizontal glyph widths cannot validate this layout")
    original_text = cue["text"]
    # Extract every character from this revision; do not reuse a partial old dictionary.
    font_key = "introPostscriptName" if cue["style"] == "intro_handwritten" else "bodyPostscriptName"
    expected = cue.get("postscriptName") or revised["typography"].get(font_key)
    if not expected:
        raise ValueError("Cue has no verified font identity; identify it or record a user-approved substitute")
    glyph_data = extract(font_path, text, compact=True, font_number=font_number,
                         expected_postscript_name=expected)
    text = glyph_data["text"]
    if not text.strip():
        raise ValueError("Empty text after newline/BOM normalization")
    metrics = cue["metrics"]
    line_widths = [sum(glyph_data["glyphs"][ch]["a"] for ch in line) *
                   metrics["fontSize"] / glyph_data["upem"] for line in text.split("\n")]
    max_width = metrics.get("maxLineAdvance", revised["typography"].get("maxLineAdvance"))
    if not isinstance(max_width, (int, float)) or isinstance(max_width, bool) or max_width <= 0:
        raise ValueError("Cue needs a positive measured maxLineAdvance for width review")
    cue["text"] = text
    cue["revision"] = {"previousText": original_text,
                       "timingPreserved": True, "glyphsRegenerated": True}
    max_lines = caption_line_limit(revised)
    layout_review = {}
    if max_lines is not None:
        exceeds = len(line_widths) > max_lines
        warnings = []
        if exceeds:
            warnings.append(cue_key + ": " + str(len(line_widths)) + " lines exceed maxLines=" +
                            str(max_lines) + "; regroup at natural speech boundaries without dropping words or changing audio")
        layout_review = {"maxLines": max_lines, "exceedsMaxLines": exceeds, "warnings": warnings}
        revised["warnings"] = [warning for warning in revised.get("warnings", [])
                               if not (warning.startswith(cue_key + ": ") and
                                       " lines exceed maxLines=" in warning)] + warnings
        cue["needsLayoutReview"] = (exceeds or max(map(len, text.split("\n"))) > 12 or
                                    max(line_widths) > max_width)
    revised["verification"].update({"chatcutApplied": False, "composedFramesVerified": False,
                                     "exportVerified": False})
    return {"schemaVersion": 1, "cueKey": cue_key, "plan": revised,
            "glyphs": glyph_data,
            "layout": {"lineWidthsAtReferenceSize": line_widths,
                       "maxLineAdvance": max_width,
                       "suggestedScale": min(1, max_width / max(line_widths)) if max(line_widths) else 1,
                       "lineCount": len(line_widths),
                       "needsCompositionReview": True, **layout_review},
            "apply": {"operation": "replace-cue-text-and-glyphs",
                      "keepCutAndAudioTiming": True,
                      "doNotUseTranscriptDeletion": True}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--cue", required=True)
    parser.add_argument("--text", required=True, type=Path)
    parser.add_argument("--font", required=True, type=Path)
    parser.add_argument("--font-number", type=int, default=0,
                        help="Zero-based TTC/OTC face index; defaults to 0")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.output.resolve() in (args.plan.resolve(), args.text.resolve(), args.font.resolve()):
            raise ValueError("Output must differ from every input")
        result = prepare(json.loads(args.plan.read_text(encoding="utf-8-sig")), args.cue,
                         args.text.read_text(encoding="utf-8-sig"), args.font,
                         font_number=args.font_number)
        args.output.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
        return 0
    except MissingGlyphsError as error:
        print(str(error), file=sys.stderr)
        return 3
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        print("text_revision.py: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
