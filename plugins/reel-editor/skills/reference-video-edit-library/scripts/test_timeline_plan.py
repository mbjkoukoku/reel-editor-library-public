"""Behavioral checks for variable duration, visual selection and speech retention."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import timeline_plan


def shot(index, start=0, end=4, source="treatment", occupied=True):
    return {"referenceCut": index, "sourceId": source, "sourceInSeconds": start,
            "sourceOutSeconds": end, "sourceDurationSeconds": 60,
            "visualReview": {"continuousChecked": True, "motionNote": "Practitioner treats shoulder throughout",
                             "samples": [{"sourceSeconds": start+(end-start)*part,
                                          "practitionerVisible": occupied, "treatmentVisible": occupied,
                                          "evidence": "Practitioner and hands visible"}
                                         for part in (0, .5, .95)]}}


def reference_request():
    return {"shots": [shot(i, end=3) for i in range(13)],
            "texts": {"text0": {"text": "肩の悩み", "source": "LP heading"},
                      "text5": {"text": "青空整体院", "source": "LP store name"},
                      "text22": {"text": "予約はこちら", "source": "LP reservation URL"}}}


def alternate_spec():
    """Synthetic pattern to exercise routing without inventing A02 measurements."""
    return {"id": "A99", "version": "test", "canvas": {"width": 1080, "height": 1920,
            "fps": 24, "durationFrames": 240},
            "cuts": [{"role": "entrance", "start": 0, "end": 48},
                     {"role": "treatment", "start": 48, "end": 144},
                     {"role": "introduction", "start": 144, "end": 240}],
            "cues": [{"key": "clinic", "start": 0, "end": 48, "style": "main",
                      "metrics": {"fontSize": 80, "centerY": 900}},
                     {"key": "body", "start": 48, "end": 240, "style": "outlined",
                      "postscriptName": "Example-Heavy", "metrics": {"fontSize": 72, "centerY": 1000},
                      "animation": {"type": "slide", "durationFrames": 12}},
                     {"key": "label", "start": 192, "end": 240, "style": "small",
                      "metrics": {"fontSize": 40, "centerY": 800}}],
            "typography": {"bodyPostscriptName": "Example-Heavy", "maxLineAdvance": 960},
            "visualSelection": {"unoccupiedAllowedRoles": ["entrance"],
                                "maxUnoccupiedShotSeconds": 1.5, "maxUnoccupiedRunSeconds": 2},
            "speechCaptionCueKey": "body",
            "decorations": {"logo": {"start": 0, "end": 48, "anchor": "top"}}}


def alternate_request():
    entrance = shot(0, end=1.5, occupied=False)
    entrance["emptyBridgeReason"] = "Show the entrance briefly"
    return {"pattern": "A99", "shots": [entrance, shot(1, end=3), shot(2, end=5)],
            "texts": {key: {"text": "確認済み原稿", "source": "Current clinic LP"}
                      for key in ("clinic", "body", "label")}}


class PlanTests(unittest.TestCase):
    def test_a07_does_not_turn_story_and_cast_into_fixed_speech_plan(self):
        spec = timeline_plan.load_spec("A07")
        self.assertEqual(spec["executionRoute"], "patient_vlog_with_sourced_cast")
        with self.assertRaisesRegex(ValueError, "A07 requires a reviewed Vlog"):
            timeline_plan.build_plan({"pattern": "A07", "mode": "verbatim_speech"}, spec)

    def test_a06_does_not_make_verbatim_captions_or_retime_summary_cards(self):
        spec = timeline_plan.load_spec("A06")
        self.assertEqual(spec["executionRoute"], "speech_summary_design")
        with self.assertRaisesRegex(ValueError, "A06 requires speech-grounded summary"):
            timeline_plan.build_plan({"pattern": "A06", "mode": "verbatim_speech"}, spec)

    def test_a05_does_not_flatten_comparison_and_mosaic_into_horizontal_plan(self):
        spec = timeline_plan.load_spec("A05")
        self.assertEqual(spec["executionRoute"], "before_after_comparison")
        with self.assertRaisesRegex(ValueError, "A05 requires paired comparison"):
            timeline_plan.build_plan({"pattern": "A05", "mode": "reference"}, spec)

    def test_a04_does_not_retime_reference_copy_as_a_new_speech_edit(self):
        spec = timeline_plan.load_spec("A04")
        self.assertEqual(spec["executionRoute"], "speech_cleanup_then_overlays")
        with self.assertRaisesRegex(ValueError, "A04 requires speech cleanup"):
            timeline_plan.build_plan({"pattern": "A04", "mode": "verbatim_speech"}, spec)

    def test_a03_preserves_reference_layers_but_rejects_horizontal_planner(self):
        spec = timeline_plan.load_spec("A03")
        timeline_plan.validate_spec(spec, "A03")
        self.assertEqual(spec["audio"]["muteSource"], True)
        self.assertEqual(spec["canvas"]["durationFrames"], 6498)
        self.assertEqual(len(spec["cues"]), 37)
        self.assertTrue(any(cue["writingMode"] == "vertical-rl" for cue in spec["cues"]))
        self.assertTrue(any(a["start"] < b["end"] and b["start"] < a["end"]
                            for i, a in enumerate(spec["cues"]) for b in spec["cues"][i+1:]))
        with self.assertRaisesRegex(ValueError, "independent caption layers"):
            timeline_plan.build_plan({"pattern": "A03", "mode": "reference"})

    def test_adaptive_duration_preserves_order_and_tail(self):
        plan = timeline_plan.build_plan(reference_request())
        self.assertEqual(plan["canvas"]["durationFrames"], 39*30)
        self.assertNotEqual(plan["canvas"]["durationFrames"], 1585)
        self.assertEqual([s["referenceCut"] for s in plan["cuts"]], list(range(13)))
        self.assertEqual(plan["cues"][-1]["end"], 39*30)
        self.assertTrue(all(c["start"] < c["end"] <= 39*30 for c in plan["cues"]))
        self.assertTrue(all(c["playbackRate"] == 1 for c in plan["cuts"]))
        self.assertFalse(plan["verification"]["chatcutApplied"])
        self.assertTrue(plan["audio"]["muteSource"])

    def test_missing_scene_collapses_timing_without_filler(self):
        request = reference_request()
        request["shots"] = [s for s in request["shots"] if s["referenceCut"] not in (2,3)]
        plan = timeline_plan.build_plan(request)
        self.assertEqual(plan["canvas"]["durationFrames"], 33*30)
        self.assertNotIn("text5", [c["key"] for c in plan["cues"]])
        self.assertTrue(any("text5" in warning for warning in plan["warnings"]))

    def test_empty_filler_and_unwatched_ranges_are_rejected(self):
        request = reference_request()
        request["shots"][0] = shot(0, occupied=False)
        with self.assertRaisesRegex(ValueError, "Unoccupied"):
            timeline_plan.build_plan(request)
        request = reference_request()
        request["shots"][0]["visualReview"]["continuousChecked"] = False
        with self.assertRaisesRegex(ValueError, "Watch"):
            timeline_plan.build_plan(request)

    def test_bridges_need_purpose_and_short_duration(self):
        request = reference_request()
        request["shots"][2] = shot(2, end=2, occupied=False)
        request["shots"][2]["emptyBridgeReason"] = "Introduce clinic entrance"
        self.assertEqual(timeline_plan.build_plan(request)["cuts"][2]["durationFrames"], 60)
        request["shots"][2]["sourceOutSeconds"] = 5
        request["shots"][2]["visualReview"]["samples"][-1]["sourceSeconds"] = 4.9
        with self.assertRaises(ValueError):
            timeline_plan.build_plan(request)

    def test_out_of_bounds_and_reordered_cuts_are_rejected(self):
        request = reference_request()
        request["shots"][0]["sourceDurationSeconds"] = 1
        with self.assertRaisesRegex(ValueError, "exceeds"):
            timeline_plan.build_plan(request)
        request = reference_request()
        request["shots"][0], request["shots"][1] = request["shots"][1], request["shots"][0]
        with self.assertRaisesRegex(ValueError, "reference order"):
            timeline_plan.build_plan(request)

    def test_verbatim_keeps_original_words_and_source_audio(self):
        request = {"mode": "verbatim_speech", "shots": [shot(0, start=1, end=4)],
                   "speechSegments": [{"sourceId": "treatment", "startSeconds": 0, "endSeconds": 4,
                                       "text": "今日は肩を確認します。",
                                       "words": [{"text": "今日は", "startSeconds": 0, "endSeconds": 1},
                                                 {"text": "肩を", "startSeconds": 1, "endSeconds": 2},
                                                 {"text": "確認します。", "startSeconds": 2, "endSeconds": 4}]}]}
        plan = timeline_plan.build_plan(request)
        self.assertEqual(plan["cues"][0]["text"], "肩を確認します。")
        self.assertEqual((plan["cues"][0]["start"], plan["cues"][0]["end"]), (0,90))
        self.assertFalse(plan["audio"]["muteSource"])
        self.assertTrue(plan["cues"][0]["verbatim"])

    def test_cut_through_utterance_requires_word_times(self):
        request = {"mode": "verbatim_speech", "shots": [shot(0, start=1, end=4)],
                   "speechSegments": [{"sourceId": "treatment", "startSeconds": 0, "endSeconds": 4,
                                       "text": "今日は肩を確認します。"}]}
        with self.assertRaisesRegex(ValueError, "spoken token"):
            timeline_plan.build_plan(request)

    def test_dense_speech_is_flagged_for_readability(self):
        request = {"mode": "verbatim_speech", "shots": [shot(0)],
                   "speechSegments": [{"sourceId": "treatment", "startSeconds": 0, "endSeconds": 4,
                                       "text": "肩の動きを確認します。" * 8}]}
        plan = timeline_plan.build_plan(request)
        self.assertTrue(plan["cues"][0]["needsLayoutReview"])
        self.assertTrue(any("dense speech" in warning for warning in plan["warnings"]))
        self.assertEqual(plan["cues"][0]["text"], request["speechSegments"][0]["text"])

    def test_caption_overlap_and_paraphrased_word_text_are_rejected(self):
        segment = {"sourceId": "treatment", "startSeconds": 0, "endSeconds": 2,
                   "text": "確認します。"}
        request = {"mode": "verbatim_speech", "shots": [shot(0)],
                   "speechSegments": [segment, copy.deepcopy(segment)]}
        with self.assertRaisesRegex(ValueError, "overlap"):
            timeline_plan.build_plan(request)
        request["speechSegments"] = [{**segment, "words": [{"text": "診断します。", "startSeconds": 0, "endSeconds": 2}]}]
        with self.assertRaisesRegex(ValueError, "exactly"):
            timeline_plan.build_plan(request)


class MultiPatternTests(unittest.TestCase):
    def test_a02_production_profile_and_effective_styles_survive_planning(self):
        spec = alternate_spec()
        spec["id"] = "A02"
        spec["productionProfile"] = {"id": "accepted-test", "layout": {"maxLines": 2}}
        spec["typography"]["styles"] = {"outlined": {"fill": "#ffff00"}}
        spec["cues"][1]["metrics"]["centerY"] = 1140
        request = alternate_request()
        request["pattern"] = "A02"
        request["texts"]["body"]["text"] = "一行目\n二行目\n三行目"
        plan = timeline_plan.build_plan(request, spec)
        cue = next(c for c in plan["cues"] if c["key"] == "body")
        self.assertTrue(cue["needsLayoutReview"])
        self.assertEqual(cue["text"], request["texts"]["body"]["text"])
        self.assertEqual(cue["metrics"]["centerY"], 1140)
        self.assertEqual(plan["typography"]["styles"]["outlined"]["fill"], "#ffff00")
        self.assertTrue(any("body: 3 lines exceed maxLines=2" in w for w in plan["warnings"]))
        self.assertEqual(plan["productionProfile"], spec["productionProfile"])
        plan["productionProfile"]["layout"]["maxLines"] = 9
        self.assertEqual(spec["productionProfile"]["layout"]["maxLines"], 2)

    def test_a02_two_lines_pass_and_legacy_plan_still_flags_three_lines(self):
        spec = alternate_spec()
        spec["id"] = "A02"
        request = alternate_request()
        request["pattern"] = "A02"
        request["texts"]["body"]["text"] = "一行目\n二行目"
        plan = timeline_plan.build_plan(request, spec)
        self.assertFalse(next(c for c in plan["cues"] if c["key"] == "body")["needsLayoutReview"])
        request["texts"]["body"]["text"] += "\n三行目"
        plan = timeline_plan.build_plan(request, spec)
        self.assertTrue(next(c for c in plan["cues"] if c["key"] == "body")["needsLayoutReview"])

    def test_a01_approved_profile_retains_three_line_behavior(self):
        request = reference_request()
        request["texts"]["text5"]["text"] = "一行目\n二行目\n三行目"
        plan = timeline_plan.build_plan(request)
        self.assertEqual(plan["productionProfile"]["id"], "a01-approved-2026-10-06")
        self.assertFalse(next(c for c in plan["cues"] if c["key"] == "text5")["needsLayoutReview"])

    def test_production_line_limit_rejects_invalid_values(self):
        for value in (0, -1, True, 2.5, "2"):
            with self.subTest(value=value):
                spec = alternate_spec()
                spec["productionProfile"] = {"layout": {"maxLines": value}}
                with self.assertRaisesRegex(ValueError, "maxLines must be a positive integer"):
                    timeline_plan.build_plan(alternate_request(), spec)

    def test_animation_speed_is_preserved_and_only_short_cues_are_clamped(self):
        spec = alternate_spec()
        raw = [{"type": "in", "name": "slide", "start": 0, "duration": 500_000},
               {"type": "out", "name": "fade", "start": 1_500_000, "duration": 500_000}]
        spec["cues"][0]["originalCapCut"] = {"animations": copy.deepcopy(raw)}
        plan = timeline_plan.build_plan(alternate_request(), spec)
        cue = plan["cues"][0]
        self.assertEqual(cue["originalCapCut"]["animations"], raw)
        self.assertEqual([(a["startFrame"], a["durationFrames"]) for a in cue["appliedAnimations"]], [(0,12),(24,12)])
        self.assertFalse(any(a["clamped"] for a in cue["appliedAnimations"]))
        request = alternate_request()
        request["shots"][0] = shot(0, end=.25, occupied=False)
        request["shots"][0]["emptyBridgeReason"] = "Short entrance"
        plan = timeline_plan.build_plan(request, spec)
        self.assertEqual([(a["startFrame"], a["durationFrames"]) for a in plan["cues"][0]["appliedAnimations"]], [(0,6),(0,6)])
        self.assertTrue(all(a["clamped"] for a in plan["cues"][0]["appliedAnimations"]))
        self.assertTrue(any("animation shortened" in warning for warning in plan["warnings"]))
        self.assertEqual(spec["cues"][0]["originalCapCut"]["animations"], raw)

    def test_normalized_animation_delays_outside_new_cue_are_omitted(self):
        spec = alternate_spec()
        spec["cues"][0]["animations"] = [{"type": "in", "startFrame": 48, "durationFrames": 12}]
        plan = timeline_plan.build_plan(alternate_request(), spec)
        self.assertEqual(plan["cues"][0]["appliedAnimations"], [])
        self.assertTrue(any("omitted pending motion review" in warning for warning in plan["warnings"]))

    def test_clamped_animation_keyframes_stay_inside_applied_duration(self):
        cue = {"key": "animated", "start": 100, "end": 106,
               "animations": [{"type": "in", "durationFrames": 15, "visibleOffsetFrames": 1,
                               "keyframeTargets": [{"frame": 0, "scale": 4},
                                                    {"frame": 5, "scale": 2},
                                                    {"frame": 15, "scale": 1}]}]}
        original = copy.deepcopy(cue["animations"])
        timeline_plan.fit_animations(cue, 30, [])
        applied = cue["appliedAnimations"][0]
        self.assertEqual([target["frame"] for target in applied["keyframeTargets"]], [0, 2, 6])
        self.assertEqual(applied["keyframeTargets"][-1]["scale"], 1)
        self.assertEqual(cue["animations"], original)

    def test_selected_pattern_uses_own_roles_fps_fonts_and_decorations(self):
        plan = timeline_plan.build_plan(alternate_request(), alternate_spec())
        self.assertEqual(plan["pattern"], "A99")
        self.assertEqual(plan["canvas"]["durationFrames"], 228)
        self.assertEqual([c["role"] for c in plan["cuts"]], ["entrance", "treatment", "introduction"])
        self.assertEqual([c["end"] for c in plan["cuts"]], [36, 108, 228])
        self.assertEqual(plan["cues"][1]["postscriptName"], "Example-Heavy")
        self.assertEqual(plan["cues"][1]["animation"]["durationFrames"], 12)
        self.assertEqual(plan["cues"][1]["end"], plan["cues"][2]["end"])
        self.assertEqual(plan["typography"]["maxLineAdvance"], 960)
        self.assertIsNone(plan["band"])
        self.assertEqual(set(plan["decorations"]), {"logo"})
        self.assertEqual(plan["decorations"]["logo"]["end"], 36)
        self.assertFalse(plan["decorations"]["logo"]["enabled"])

    def test_no_a01_bridge_indices_or_limits_leak_into_other_patterns(self):
        request = alternate_request()
        request["shots"][2] = shot(2, end=1, occupied=False)
        request["shots"][2]["emptyBridgeReason"] = "This is not a permitted bridge role"
        with self.assertRaisesRegex(ValueError, "Unoccupied"):
            timeline_plan.build_plan(request, alternate_spec())
        request = alternate_request()
        request["shots"][0] = shot(0, end=2, occupied=False)
        request["shots"][0]["emptyBridgeReason"] = "Entrance exceeds this pattern's limit"
        with self.assertRaisesRegex(ValueError, "Shorten"):
            timeline_plan.build_plan(request, alternate_spec())

    def test_speech_preserves_selected_patterns_caption_appearance(self):
        request = {"pattern": "A99", "mode": "verbatim_speech", "shots": [shot(1)],
                   "speechSegments": [{"sourceId": "treatment", "startSeconds": 0,
                                       "endSeconds": 4, "text": "施術を紹介します。"}]}
        cue = timeline_plan.build_plan(request, alternate_spec())["cues"][0]
        self.assertEqual(cue["style"], "outlined")
        self.assertEqual(cue["templateCueKey"], "body")
        self.assertEqual(cue["postscriptName"], "Example-Heavy")
        self.assertEqual(cue["animation"], {"type": "slide", "durationFrames": 12})
        self.assertEqual(cue["end"], 96)

    def test_catalog_loading_rejects_paths_unknown_ids_and_mismatched_specs(self):
        with self.assertRaisesRegex(ValueError, "catalog ID"):
            timeline_plan.build_plan({"pattern": "../a01"})
        with tempfile.TemporaryDirectory() as directory, patch.object(timeline_plan, "REFERENCE_DIR", Path(directory)):
            Path(directory, "a99.json").write_text(json.dumps(alternate_spec()), encoding="utf-8")
            self.assertEqual(timeline_plan.build_plan(alternate_request())["pattern"], "A99")
            with self.assertRaisesRegex(ValueError, "unavailable"):
                timeline_plan.build_plan({"pattern": "A98"})
        request = alternate_request()
        request["pattern"] = "A01"
        with self.assertRaisesRegex(ValueError, "does not match"):
            timeline_plan.build_plan(request, alternate_spec())

    def test_cli_pattern_conflict_does_not_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            request_path, output_path = Path(directory, "request.json"), Path(directory, "plan.json")
            request_path.write_text(json.dumps(alternate_request()), encoding="utf-8")
            output_path.write_text("keep existing result", encoding="utf-8")
            with patch("sys.stderr"):
                code = timeline_plan.main([str(request_path), "--pattern", "A01", "--output", str(output_path)])
            self.assertEqual(code, 2)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "keep existing result")


class A02PlanTests(unittest.TestCase):
    def setUp(self):
        # These are synthetic review records for validation tests, never media analysis.
        self.spec = timeline_plan.load_spec("A02")
        self.request = {"pattern": "A02", "shots": [], "texts": {
            cue["key"]: {"text": "今回の確認済み情報", "source": "Test clinic fact fixture"}
            for cue in self.spec["cues"]}}
        selection = self.spec["visualSelection"]
        for index, baseline in enumerate(self.spec["cuts"]):
            role = baseline["role"]
            duration = (baseline["end"] - baseline["start"]) / self.spec["canvas"]["fps"]
            recorded = shot(index, end=duration, source="source" + str(index))
            if role in selection["unoccupiedAllowedRoles"]:
                recorded = shot(index, end=duration, source="source" + str(index), occupied=False)
                recorded["emptyBridgeReason"] = "Test fixture of purposeful clinic tour"
            elif role in selection["allowPatientOnlyRoles"] + selection["optionalLicensedImageRoles"]:
                recorded = shot(index, end=duration, source="source" + str(index), occupied=False)
                for sample in recorded["visualReview"]["samples"]:
                    sample.update({"personVisible": True, "evidence": "Test person-only visual record"})
                if role in selection["optionalLicensedImageRoles"]:
                    recorded.update({"sourceMediaType": "image", "imageUsageEvidence": "Test fixture of supplied-asset usage permission"})
            self.request["shots"].append(recorded)

    def test_full_a02_preserves_its_own_timeline_and_does_not_inherit_a01_fonts(self):
        plan = timeline_plan.build_plan(self.request)
        self.assertEqual((plan["pattern"], len(plan["cuts"]), len(plan["cues"])), ("A02", 14, 22))
        self.assertEqual(plan["canvas"], self.spec["canvas"])
        self.assertIsNone(plan["band"])
        self.assertEqual(plan["decorations"], {})
        self.assertIsNone(plan["typography"]["bodyPostscriptName"])
        self.assertEqual(plan["cues"][-2]["postscriptName"], "HiraginoSans-W7")
        self.assertEqual(plan["cues"][-1]["postscriptName"], "HiraginoSans-W8")
        self.assertEqual(plan["cues"][-1]["appliedAnimations"][0]["durationFrames"], 15)
        self.assertEqual([c["role"] for c in plan["cuts"]], [c["role"] for c in self.spec["cuts"]])
        self.assertFalse(plan["verification"]["visualContentAutomaticallyVerified"])

    def test_a02_plan_uses_accepted_layout_and_readable_gold_over_historical_reference(self):
        plan = timeline_plan.build_plan(self.request)
        self.assertEqual(plan["productionProfile"]["id"], "a02-approved-2026-10-06")
        self.assertEqual(plan["productionProfile"]["layout"]["maxLines"], 2)
        self.assertTrue(all(c["metrics"]["centerY"] == 1140 for c in plan["cues"]))
        self.assertTrue(all(c["metrics"]["maxLineAdvance"] == 960 for c in plan["cues"]))
        gold = plan["typography"]["styles"]["gold_mincho"]
        self.assertEqual(gold["fill"], "#ffe34d")
        self.assertIn({"color": "#17130b", "widthPx": 11}, gold["strokeLayers"])
        self.assertEqual(gold["shadow"]["color"], "#000000")
        cue = next(c for c in plan["cues"] if c["style"] == "gold_mincho")
        self.assertEqual(cue["appliedAnimations"][0]["glowEndsAtFrame"], 7)
        self.assertEqual(cue["appliedAnimations"][0]["glowLayer"],
                         "behind-colored-artwork-and-dark-outline")

    def test_person_only_exception_requires_observation_and_stays_role_scoped(self):
        self.request["shots"][0]["visualReview"]["samples"][1]["personVisible"] = False
        with self.assertRaisesRegex(ValueError, "Unoccupied"):
            timeline_plan.build_plan(self.request)
        a01 = reference_request()
        a01["shots"][0] = shot(0, occupied=False)
        for sample in a01["shots"][0]["visualReview"]["samples"]:
            sample["personVisible"] = True
        with self.assertRaisesRegex(ValueError, "Unoccupied"):
            timeline_plan.build_plan(a01)

    def test_image_requires_explicit_media_type_and_permission_evidence(self):
        image = next(s for s in self.request["shots"] if s.get("sourceMediaType") == "image")
        image.pop("sourceMediaType")
        with self.assertRaisesRegex(ValueError, "explicit sourceMediaType"):
            timeline_plan.build_plan(self.request)
        image["sourceMediaType"] = "image"
        image.pop("imageUsageEvidence")
        with self.assertRaisesRegex(ValueError, "imageUsageEvidence"):
            timeline_plan.build_plan(self.request)

    def test_a02_speech_uses_its_own_body_template_and_original_voice(self):
        request = {"pattern": "A02", "mode": "verbatim_speech", "shots": [shot(3)],
                   "speechSegments": [{"sourceId": "treatment", "startSeconds": 0,
                                       "endSeconds": 4, "text": "施術を紹介します。"}]}
        plan = timeline_plan.build_plan(request)
        cue = plan["cues"][0]
        self.assertEqual(cue["templateCueKey"], self.spec["speechCaptionCueKey"])
        self.assertEqual(cue["style"], "body_white")
        self.assertFalse(plan["audio"]["muteSource"])


if __name__ == "__main__":
    unittest.main()
