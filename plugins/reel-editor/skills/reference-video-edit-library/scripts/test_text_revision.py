"""A text change must preserve timing/audio and include newly introduced glyphs."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import text_revision
from test_timeline_plan import reference_request
from timeline_plan import build_plan

FONT = Path(__file__).resolve().parent.parent / "assets/fonts/NotoSerifCJKjp-Black.otf"


class TextRevisionTests(unittest.TestCase):
    def test_a07_text_change_preserves_story_cards_not_speech_cues(self):
        before = self.plan()
        before["pattern"] = "A07"
        with patch("text_revision.extract") as extract:
            with self.assertRaisesRegex(ValueError, "A07 text revision"):
                text_revision.prepare(before, "text5", "来院・相談", FONT)
            extract.assert_not_called()

    def test_a06_text_change_requires_summary_card_workflow(self):
        before = self.plan()
        before["pattern"] = "A06"
        with patch("text_revision.extract") as extract:
            with self.assertRaisesRegex(ValueError, "A06 text revision"):
                text_revision.prepare(before, "text5", "ゴルフの近況", FONT)
            extract.assert_not_called()

    def test_a05_text_change_requires_comparison_layout_workflow(self):
        before = self.plan()
        before["pattern"] = "A05"
        with patch("text_revision.extract") as extract:
            with self.assertRaisesRegex(ValueError, "A05 text revision"):
                text_revision.prepare(before, "text5", "施術後", FONT)
            extract.assert_not_called()

    def test_a04_revision_requires_speech_timing_and_background_layout(self):
        before = self.plan()
        before["pattern"] = "A04"
        with patch("text_revision.extract") as extract:
            with self.assertRaisesRegex(ValueError, "A04 text revision"):
                text_revision.prepare(before, "text5", "本人の発言を修正", FONT)
            extract.assert_not_called()

    def test_vertical_layout_does_not_report_horizontal_width_validation(self):
        before = self.plan()
        before["pattern"] = "A03"
        with patch("text_revision.extract") as extract:
            with self.assertRaisesRegex(ValueError, "A03 text revision workflow"):
                text_revision.prepare(before, "text5", "東京都\n初回料金", FONT)
            extract.assert_not_called()

    def plan(self):
        request = reference_request()
        request.update({"typographyFallback": "noto", "fontFallbackApprovedByUser": True})
        return build_plan(request)

    def test_replacement_keeps_timing_and_adds_new_glyphs(self):
        before = self.plan()
        after = text_revision.prepare(before, "text5", "東京都渋谷区\n初回3,980円", FONT)
        revised = after["plan"]
        self.assertEqual(revised["cuts"], before["cuts"])
        self.assertEqual(revised["audio"], before["audio"])
        self.assertEqual([(c["key"],c["start"],c["end"]) for c in revised["cues"]],
                         [(c["key"],c["start"],c["end"]) for c in before["cues"]])
        self.assertEqual(before["cues"][1]["text"], "青空整体院")
        for char in "東京都渋谷区初回3,980円":
            self.assertIn(char, after["glyphs"]["glyphs"])
        self.assertEqual(after["layout"]["lineCount"], 2)
        self.assertFalse(revised["verification"]["composedFramesVerified"])

    def test_windows_newlines_and_bom_use_extracted_text_for_layout(self):
        result = text_revision.prepare(self.plan(), "text5", "\ufeff青空整体院\r\n初回3,980円\r受付中", FONT)
        expected = "青空整体院\n初回3,980円\n受付中"
        self.assertEqual(result["glyphs"]["text"], expected)
        self.assertEqual(result["plan"]["cues"][1]["text"], expected)
        self.assertNotIn("\r", result["glyphs"]["glyphs"])
        self.assertEqual(result["layout"]["lineCount"], 3)

    def test_strict_font_rejects_noto_even_when_characters_exist(self):
        strict = build_plan(reference_request())
        with self.assertRaisesRegex(ValueError, "Font identity mismatch"):
            text_revision.prepare(strict, "text5", "青空整体院", FONT)

    def test_long_replacement_reports_scale_without_changing_timing(self):
        result = text_revision.prepare(self.plan(), "text5", "あ"*30, FONT)
        self.assertLess(result["layout"]["suggestedScale"], .5)
        self.assertTrue(result["layout"]["needsCompositionReview"])

    def test_a02_line_limit_survives_revision_without_automatic_reflow(self):
        before = self.plan()
        before["pattern"] = "A02"
        before["productionProfile"] = {"id": "accepted-test", "layout": {"maxLines": 2}}
        replacement = "一行目\n二行目\n三行目"
        result = text_revision.prepare(before, "text5", replacement, FONT)
        revised = result["plan"]
        cue = next(c for c in revised["cues"] if c["key"] == "text5")
        self.assertEqual(cue["text"], replacement)
        self.assertEqual(result["layout"]["maxLines"], 2)
        self.assertTrue(result["layout"]["exceedsMaxLines"])
        self.assertTrue(cue["needsLayoutReview"])
        self.assertTrue(any("3 lines exceed maxLines=2" in w for w in result["layout"]["warnings"]))
        self.assertIn(result["layout"]["warnings"][0], revised["warnings"])
        self.assertEqual(revised["cuts"], before["cuts"])
        self.assertEqual(revised["audio"], before["audio"])
        self.assertEqual([(c["start"], c["end"]) for c in revised["cues"]],
                         [(c["start"], c["end"]) for c in before["cues"]])
        revised["productionProfile"]["layout"]["maxLines"] = 4
        self.assertEqual(before["productionProfile"]["layout"]["maxLines"], 2)

    def test_a02_two_line_revision_clears_its_previous_line_limit_warning(self):
        plan = self.plan()
        plan["pattern"] = "A02"
        plan = text_revision.prepare(plan, "text5", "一行目\n二行目\n三行目", FONT)["plan"]
        result = text_revision.prepare(plan, "text5", "一行目\n二行目", FONT)
        self.assertEqual(result["layout"]["maxLines"], 2)
        self.assertFalse(result["layout"]["exceedsMaxLines"])
        self.assertEqual(result["layout"]["warnings"], [])
        cue = next(c for c in result["plan"]["cues"] if c["key"] == "text5")
        self.assertFalse(cue["needsLayoutReview"])
        self.assertFalse(any("text5: 3 lines exceed maxLines=" in w for w in result["plan"]["warnings"]))

    def test_a01_revision_retains_existing_layout_contract(self):
        result = text_revision.prepare(self.plan(), "text5", "一行目\n二行目\n三行目", FONT)
        self.assertEqual(result["layout"]["lineCount"], 3)
        self.assertNotIn("maxLines", result["layout"])
        self.assertNotIn("exceedsMaxLines", result["layout"])
        self.assertNotIn("warnings", result["layout"])

    def test_fallback_requires_real_approval_record(self):
        request = reference_request()
        request["typographyFallback"] = "noto"
        with self.assertRaisesRegex(ValueError, "explicit user approval"):
            build_plan(request)

    def test_per_cue_font_and_width_override_pattern_body_defaults(self):
        plan = self.plan()
        cue = next(c for c in plan["cues"] if c["key"] == "text5")
        cue["postscriptName"] = "NotoSerifCJKjp-Black"
        cue["metrics"]["maxLineAdvance"] = 240
        plan["typography"]["bodyPostscriptName"] = "Different-Body-Font"
        result = text_revision.prepare(plan, "text5", "青空整体院", FONT)
        self.assertEqual(result["layout"]["maxLineAdvance"], 240)
        self.assertLess(result["layout"]["suggestedScale"], 1)
        cue["postscriptName"] = "Different-Cue-Font"
        with self.assertRaisesRegex(ValueError, "Font identity mismatch"):
            text_revision.prepare(plan, "text5", "青空整体院", FONT)

    def test_unidentified_font_is_not_silently_substituted(self):
        plan = self.plan()
        plan["typography"].pop("bodyPostscriptName")
        with self.assertRaisesRegex(ValueError, "no verified font identity"):
            text_revision.prepare(plan, "text5", "青空整体院", FONT)

    def test_nonzero_collection_face_is_forwarded_with_expected_identity(self):
        plan = self.plan()
        cue = next(c for c in plan["cues"] if c["key"] == "text5")
        cue["postscriptName"] = "HiraMinProN-W6"
        collection = Path("example-font.ttc")
        glyph_data = {"text": "院", "upem": 1000, "glyphs": {"院": {"a": 1000}}}
        with patch.object(text_revision, "extract", return_value=glyph_data) as extract:
            result = text_revision.prepare(plan, "text5", "院", collection, font_number=2)
        extract.assert_called_once_with(collection, "院", compact=True, font_number=2,
                                        expected_postscript_name="HiraMinProN-W6")
        self.assertEqual(result["glyphs"], glyph_data)
        self.assertEqual(result["layout"]["lineWidthsAtReferenceSize"], [cue["metrics"]["fontSize"]])

    def test_cli_forwards_collection_face_and_rejects_negative_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            plan_path, text_path, output_path = [Path(directory, name) for name in
                                                ("plan.json", "text.txt", "revision.json")]
            plan = self.plan()
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            text_path.write_text("院", encoding="utf-8")
            args = ["--plan", str(plan_path), "--cue", "text5", "--text", str(text_path),
                    "--font", str(FONT), "--output", str(output_path), "--font-number"]
            with patch.object(text_revision, "prepare", return_value={"prepared": True}) as prepare:
                self.assertEqual(text_revision.main(args + ["2"]), 0)
            prepare.assert_called_once_with(plan, "text5", "院", FONT, font_number=2)
            saved = output_path.read_text(encoding="utf-8")
            with patch.object(text_revision, "extract") as extract, patch("sys.stderr") as stderr:
                self.assertEqual(text_revision.main(args + ["-1"]), 2)
            extract.assert_not_called()
            self.assertTrue(any("nonnegative integer" in str(call) for call in stderr.write.call_args_list))
            self.assertEqual(output_path.read_text(encoding="utf-8"), saved)


if __name__ == "__main__":
    unittest.main()
