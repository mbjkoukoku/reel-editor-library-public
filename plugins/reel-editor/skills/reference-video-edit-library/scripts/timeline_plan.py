#!/usr/bin/env python3
"""Build a portable library-pattern edit plan from reviewed source ranges and text.

This does not inspect video, transcribe speech, or mutate ChatCut. Its output is
validated placement data for Codex to apply with the current ChatCut tools.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import re
import sys

REFERENCE_DIR = Path(__file__).resolve().parent.parent / "references"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, label):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value), label + " must be a finite number")
    return value


def frame(seconds, fps):
    return int(math.floor(number(seconds, "seconds") * fps + 0.5))


def pattern_id(value):
    require(isinstance(value, str) and re.fullmatch(r"A[0-9]{2,}", value.upper()),
            "pattern must be a catalog ID such as A01 or A02")
    return value.upper()


def load_spec(pattern):
    path = REFERENCE_DIR / (pattern_id(pattern).lower() + ".json")
    require(path.is_file(), "Unknown or unavailable pattern: " + pattern)
    return json.loads(path.read_text(encoding="utf-8"))


def caption_line_limit(document, default=None):
    """Read the production limit without loading historical reference evidence."""
    profile = document.get("productionProfile", {})
    limit = profile.get("layout", {}).get("maxLines")
    if limit is None:
        return 2 if document.get("pattern", document.get("id")) == "A02" else default
    require(isinstance(limit, int) and not isinstance(limit, bool) and limit > 0,
            "productionProfile.layout.maxLines must be a positive integer")
    return limit


def validate_spec(spec, pattern):
    require(pattern_id(spec["id"]) == pattern, "Request pattern does not match the supplied reference")
    fps = number(spec["canvas"]["fps"], "reference fps")
    require(fps > 0, "Reference fps must be positive")
    require(spec["cuts"], "Reference needs cuts")
    previous = 0
    for cut in spec["cuts"]:
        start, end = number(cut["start"], "cut start"), number(cut["end"], "cut end")
        require(start == previous and start < end and cut.get("role"),
                "Reference cuts must be contiguous, ordered and have roles")
        previous = end
    require(previous == spec["canvas"]["durationFrames"], "Reference cuts must cover the canvas duration")
    keys = set()
    for cue in spec["cues"]:
        require(isinstance(cue.get("key"), str) and cue["key"] not in keys,
                "Reference cue keys must be unique")
        keys.add(cue["key"])
        start, end = number(cue["start"], "cue start"), number(cue["end"], "cue end")
        require(0 <= start < end <= previous and cue.get("style"), "Invalid reference cue timing/style")
    if spec.get("speechCaptionCueKey") is not None:
        require(spec["speechCaptionCueKey"] in keys, "Unknown speechCaptionCueKey")


def speech_template(spec, cut_index):
    candidates = [cue for cue in spec["cues"] if cue.get("metrics")
                  and cue.get("style") not in ("intro_handwritten", "badges_only")]
    preferred = spec.get("speechCaptionCueKey")
    if preferred is not None:
        candidates = [cue for cue in candidates if cue["key"] == preferred]
    require(candidates, "Pattern needs a measured speech caption template")
    cut = spec["cuts"][cut_index]
    # Prefer the caption occupying this role, then the closest main caption.
    return min(candidates, key=lambda cue: (
        not (cue["start"] < cut["end"] and cut["start"] < cue["end"]),
        abs(cue["start"] - cut["start"])))


def fit_animations(cue, fps, warnings):
    """Keep source animation speed, shortening only when the new cue cannot fit it.

    Raw CapCut parameters stay untouched as evidence; appliedAnimations contains
    cue-local output frames for the renderer, never timeline-global frames.
    """
    originals = cue.get("animations")
    capcut_units = originals is None
    if originals is None:
        originals = cue.get("originalCapCut", {}).get("animations")
    if originals is None and isinstance(cue.get("animation"), dict) and "durationFrames" in cue["animation"]:
        originals, capcut_units = [cue["animation"]], False
    if originals is None:
        return
    length = cue["end"] - cue["start"]
    applied = []
    for original in originals:
        animation = copy.deepcopy(original)
        if capcut_units:
            start = frame(number(animation.pop("start", 0), "animation start") / 1_000_000, fps)
            duration = frame(number(animation.pop("duration", 0), "animation duration") / 1_000_000, fps)
        else:
            start = number(animation.get("startFrame", 0), "animation startFrame")
            duration = number(animation["durationFrames"], "animation durationFrames")
            require(start == int(start) and duration == int(duration), "Animation frames must be integers")
            start, duration = int(start), int(duration)
        require(start >= 0 and duration >= 0, "Animation timing must not be negative")
        if duration == 0:
            continue
        kind = animation.get("type", "in")
        if kind == "out":
            actual_duration = min(duration, length)
            actual_start = length - actual_duration
        else:
            if start >= length:
                warnings.append(cue["key"] + ": animation starts after the adapted cue; omitted pending motion review")
                continue
            actual_start = start
            actual_duration = min(duration, length - start)
        clamped = actual_duration != duration
        animation.update({"type": kind, "startFrame": actual_start,
                          "durationFrames": actual_duration, "endFrame": actual_start + actual_duration,
                          "referenceStartFrame": start, "referenceDurationFrames": duration,
                          "clamped": clamped})
        if clamped and "keyframeTargets" in animation:
            targets = {}
            for target in animation["keyframeTargets"]:
                position = number(target["frame"], "animation keyframe frame")
                require(0 <= position <= duration, "Animation keyframe is outside its duration")
                mapped = frame(position / duration * actual_duration, 1)
                targets[mapped] = {**target, "frame": mapped}
            animation["keyframeTargets"] = [targets[position] for position in sorted(targets)]
        if clamped and "visibleOffsetFrames" in animation:
            animation["visibleOffsetFrames"] = frame(animation["visibleOffsetFrames"] / duration * actual_duration, 1)
        applied.append(animation)
        if clamped:
            warnings.append(cue["key"] + ": animation shortened to fit the adapted cue; verify motion/readability")
    cue["appliedAnimations"] = applied


def build_plan(request, spec=None):
    pattern = pattern_id(request.get("pattern", spec.get("id", "A01") if spec is not None else "A01"))
    spec = load_spec(pattern) if spec is None else spec
    require(spec.get("executionRoute") != "patient_vlog_with_sourced_cast" and pattern != "A07",
            "A07 requires a reviewed Vlog shot plan and sourced cast; follow references/a07.md")
    require(spec.get("executionRoute") != "speech_summary_design" and pattern != "A06",
            "A06 requires speech-grounded summary cards, not a fixed caption plan; follow references/a06.md")
    require(spec.get("executionRoute") != "speech_cleanup_then_overlays" and pattern != "A04",
            "A04 requires speech cleanup and post-edit overlays; follow references/a04.md")
    require(spec.get("executionRoute") != "before_after_comparison" and pattern != "A05",
            "A05 requires paired comparison footage and tracked face mosaic; follow references/a05.md")
    validate_spec(spec, pattern)
    require(spec.get("executionRoute") != "native_independent_overlays",
            "This pattern requires independent caption layers and vertical layout; "
            "follow references/a03.md with current ChatCut tools, not this horizontal planner")
    fps = spec["canvas"]["fps"]
    mode = request.get("mode", "reference")
    require(mode in ("reference", "verbatim_speech"), "Unknown mode")
    max_lines = caption_line_limit(spec, default=3)
    typography = copy.deepcopy(spec["typography"])
    if request.get("typographyFallback"):
        require(request["typographyFallback"] == "noto"
                and request.get("fontFallbackApprovedByUser") is True,
                "Font substitution requires explicit user approval")
        typography.update({"bodyFont": "Noto Serif CJK JP Black",
                           "bodyPostscriptName": "NotoSerifCJKjp-Black",
                           "defaultFidelity": "user-approved-approximation",
                           "fontIdentity": "user-approved substitute, not the reference body font"})
    shots = request.get("shots", [])
    require(shots, "Supply reviewed shots; never fill duration with unrelated footage")
    warnings, cuts, total, previous = [], [], 0, -1
    occupied_run, has_practitioner, has_treatment = 0, False, False
    selection = spec.get("visualSelection", {})
    bridge_roles = selection.get("unoccupiedAllowedRoles", [])
    patient_roles = selection.get("allowPatientOnlyRoles", [])
    image_roles = selection.get("optionalLicensedImageRoles", [])
    limits = request.get("visualLimits", {})
    empty_max = number(limits.get("maxUnoccupiedShotSeconds", selection.get("maxUnoccupiedShotSeconds", 2)), "empty-shot limit")
    empty_run_max = number(limits.get("maxUnoccupiedRunSeconds", selection.get("maxUnoccupiedRunSeconds", 4)), "empty-run limit")
    require(empty_max > 0 and empty_run_max > 0, "Visual limits must be positive")
    for shot in shots:
        index = shot.get("referenceCut")
        require(isinstance(index, int) and not isinstance(index, bool)
                and previous < index < len(spec["cuts"]),
                "referenceCut values must be unique and in reference order")
        previous = index
        source = shot.get("sourceId")
        require(isinstance(source, str) and source.strip(), "Each shot needs current sourceId")
        role = spec["cuts"][index]["role"]
        media_type = shot.get("sourceMediaType", "video")
        require(media_type in ("video", "image"), "sourceMediaType must be video or image")
        require(not shot.get("imageUsageEvidence") or media_type == "image",
                "An image usage record requires explicit sourceMediaType: image")
        if media_type == "image":
            require(role in image_roles and isinstance(shot.get("imageUsageEvidence"), str)
                    and shot["imageUsageEvidence"].strip(),
                    "Images require a permitted image role and imageUsageEvidence for the supplied asset")
        si = number(shot.get("sourceInSeconds"), "sourceInSeconds")
        so = number(shot.get("sourceOutSeconds"), "sourceOutSeconds")
        length = number(shot.get("sourceDurationSeconds"), "sourceDurationSeconds")
        require(0 <= si < so <= length, "Selected range exceeds source duration: " + source)
        duration = frame(so - si, fps)
        require(duration >= 1, "Selected range is shorter than one output frame")
        review = shot.get("visualReview", {})
        require(review.get("continuousChecked") is True and review.get("motionNote"),
                "Watch the selected range and record visualReview.motionNote: " + source)
        samples = review.get("samples", [])
        require(len(samples) >= 3, "Record start/middle/end visual samples: " + source)
        times = [number(s.get("sourceSeconds"), "sample sourceSeconds") for s in samples]
        require(all(si <= t < so for t in times), "Visual sample outside selected range")
        require(min(times) <= si + (so-si)*0.2 and max(times) >= so - (so-si)*0.2
                and any(si + (so-si)*0.3 <= t <= si + (so-si)*0.7 for t in times),
                "Visual samples must cover start/middle/end")
        for sample in samples:
            require(isinstance(sample.get("practitionerVisible"), bool)
                    and isinstance(sample.get("treatmentVisible"), bool)
                    and sample.get("evidence"), "Every visual sample needs observed labels and evidence")
            for label in ("personVisible", "patientVisible"):
                require(label not in sample or isinstance(sample[label], bool), label + " must be observed true/false")
        practitioner = any(s["practitionerVisible"] for s in samples)
        treatment = any(s["treatmentVisible"] for s in samples)
        person_allowed = role in patient_roles or role in image_roles
        all_occupied = all(s["practitionerVisible"] or s["treatmentVisible"]
                           or (person_allowed and (s.get("patientVisible", False) or s.get("personVisible", False)))
                           for s in samples)
        if not all_occupied:
            require(role in bridge_roles and shot.get("emptyBridgeReason"),
                    "Unoccupied footage requires a deliberate bridge allowed by this pattern, never filler")
            require(so-si <= empty_max + 1/fps, "Shorten unoccupied exterior/interior shot")
            occupied_run += duration
            require(occupied_run <= frame(empty_run_max, fps), "Consecutive unoccupied footage is too long")
        else:
            occupied_run = 0
        has_practitioner |= practitioner and media_type == "video"
        has_treatment |= treatment and media_type == "video"
        cut = copy.deepcopy(shot)
        cut.update({"role": role, "sourceMediaType": media_type, "start": total,
                    "end": total+duration, "durationFrames": duration,
                    "playbackRate": 1, "muteSource": mode == "reference"})
        cuts.append(cut)
        total += duration
    require(has_practitioner or selection.get("practitionerRequired") is False,
            "A clinic reel must include the practitioner")
    require(has_treatment or selection.get("actualTreatmentRequired") is False,
            "A clinic reel must include actual treatment")
    by_index = {s["referenceCut"]: s for s in cuts}

    def retime(original):
        offset = 0
        for index, baseline in enumerate(spec["cuts"]):
            duration = by_index[index]["durationFrames"] if index in by_index else 0
            if original <= baseline["end"]:
                fraction = min(1, max(0, (original-baseline["start"]) /
                                       (baseline["end"]-baseline["start"])))
                return offset + int(math.floor(fraction*duration+0.5))
            offset += duration
        return total

    cues = []
    if mode == "reference":
        texts = request.get("texts", {})
        known = {c["key"] for c in spec["cues"]}
        require(set(texts) <= known, "Unknown cue key in texts")
        for baseline in spec["cues"]:
            key = baseline["key"]
            entry = texts.get(key)
            if baseline["style"] == "badges_only" or entry is None:
                continue
            require(isinstance(entry, dict) and isinstance(entry.get("text"), str)
                    and entry["text"].strip() and entry.get("source"),
                    "Each text needs text and fact source: " + key)
            start, end = retime(baseline["start"]), retime(baseline["end"])
            if end <= start:
                warnings.append(key + ": omitted with its removed scene")
                continue
            cue = copy.deepcopy(baseline)
            cue.update({"start": start, "end": end, "text": entry["text"],
                        "source": entry["source"]})
            cues.append(cue)
            cps = len(entry["text"].replace("\n", "")) / ((end-start)/fps)
            if cps > request.get("readingCharactersPerSecond", 8):
                warnings.append(key + ": fast reading pace; shorten verified copy or select a longer source range")
        require(cues, "Provide current-store text with sources")
    else:
        last_source_end = {}
        for cut in cuts:
            require(cut["sourceInSeconds"] >= last_source_end.get(cut["sourceId"], 0),
                    "Verbatim mode must not repeat or reorder speech from one source")
            last_source_end[cut["sourceId"]] = cut["sourceOutSeconds"]
        segments = request.get("speechSegments", [])
        require(segments, "Verbatim mode requires time-aligned original speech")
        for segment in segments:
            require(isinstance(segment.get("text"), str) and segment["text"].strip(),
                    "Speech segment text is required")
            a, b = number(segment.get("startSeconds"), "speech start"), number(segment.get("endSeconds"), "speech end")
            require(0 <= a < b, "Invalid speech timing")
            words = segment.get("words")
            if words:
                require("".join(w["text"] for w in words) == segment["text"],
                        "Word text must reproduce the transcript exactly, including punctuation/spaces")
                prev_end = a
                for word in words:
                    wa, wb = number(word["startSeconds"], "word start"), number(word["endSeconds"], "word end")
                    require(prev_end <= wa < wb <= b and isinstance(word["text"], str), "Invalid word timing/order")
                    prev_end = wb
            else:
                words = [{"text": segment["text"], "startSeconds": a, "endSeconds": b}]
            for cut in cuts:
                if cut["sourceId"] != segment.get("sourceId"):
                    continue
                si, so = cut["sourceInSeconds"], cut["sourceOutSeconds"]
                selected = []
                for word in words:
                    wa, wb = word["startSeconds"], word["endSeconds"]
                    if wb <= si or wa >= so:
                        continue
                    require(si <= wa and wb <= so,
                            "Cut intersects a spoken token; move the cut or supply accurate word timings")
                    selected.append(word)
                if not selected:
                    continue
                template = speech_template(spec, cut["referenceCut"])
                start = cut["start"] + frame(selected[0]["startSeconds"]-si, fps)
                end = min(cut["end"], cut["start"] + frame(selected[-1]["endSeconds"]-si, fps))
                require(end > start, "Speech caption is shorter than one output frame")
                cue = copy.deepcopy(template)
                cue.update({"key": "speech" + str(len(cues)), "start": start, "end": end,
                             "text": "".join(w["text"] for w in selected),
                             "templateCueKey": template["key"],
                             "source": {"sourceId": cut["sourceId"],
                                        "startSeconds": selected[0]["startSeconds"],
                                        "endSeconds": selected[-1]["endSeconds"]},
                             "verbatim": True})
                cues.append(cue)
        require(cues, "No speech segments intersect selected source ranges")
        warnings.append("Check transcription against original audio; text is not paraphrased by this planner")
    for cue in cues:
        fit_animations(cue, fps, warnings)
        # This is only a text-length alarm; real glyph widths are checked later.
        lines = cue["text"].split("\n")
        cue["needsLayoutReview"] = max(map(len, lines)) > 12 or len(lines) > max_lines
        if cue["needsLayoutReview"]:
            warnings.append(cue["key"] + ": long text/line; split at natural word boundaries and verify glyph width")
        if len(lines) > max_lines and ("productionProfile" in spec or pattern == "A02"):
            warnings.append(cue["key"] + ": " + str(len(lines)) + " lines exceed maxLines=" +
                            str(max_lines) + "; regroup at natural speech boundaries without dropping words or changing audio")
        if mode == "verbatim_speech":
            cps = len(cue["text"].replace("\n", "")) / ((cue["end"]-cue["start"])/fps)
            if cps > request.get("readingCharactersPerSecond", 8):
                warnings.append(cue["key"] + ": dense speech; preserve words/audio and review caption grouping")
    cues.sort(key=lambda c: c["start"])
    if mode == "verbatim_speech":
        for earlier, later in zip(cues, cues[1:]):
            require(earlier["end"] <= later["start"], "Caption intervals overlap; split transcript at real utterance boundaries")
    decorations = {}
    reference_decorations = {name: spec[name] for name in ("emphasis", "badges", "evidenceImage", "note") if name in spec}
    reference_decorations.update(spec.get("decorations", {}))
    for name, original in reference_decorations.items():
        value = copy.deepcopy(original)
        value["start"], value["end"] = retime(value["start"]), retime(value["end"])
        if value["end"] > value["start"]:
            value["enabled"] = False
            animation_cue = {**value, "key": name}
            fit_animations(animation_cue, fps, warnings)
            if "appliedAnimations" in animation_cue:
                value["appliedAnimations"] = animation_cue["appliedAnimations"]
            decorations[name] = value
    plan = {"schemaVersion": 1, "pattern": pattern, "patternVersion": spec["version"],
            "mode": mode, "canvas": {**spec["canvas"], "durationFrames": total},
            "cuts": cuts, "cues": cues, "typography": typography,
            "band": copy.deepcopy(spec.get("band")), "decorations": decorations,
            "audio": {"aiVoice": False, "bgm": False, "muteSource": mode == "reference"},
            "warnings": warnings,
            "verification": {"timingAndDeclaredEvidenceChecked": True,
                             "visualContentAutomaticallyVerified": False,
                             "chatcutApplied": False, "composedFramesVerified": False,
                             "exportVerified": False}}
    if "productionProfile" in spec:
        plan["productionProfile"] = copy.deepcopy(spec["productionProfile"])
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--pattern", help="Catalog ID; must agree with request.pattern when both are supplied")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        require(args.request.resolve() != args.output.resolve(), "Keep the request separate from output")
        request = json.loads(args.request.read_text(encoding="utf-8-sig"))
        if args.pattern:
            selected = pattern_id(args.pattern)
            require("pattern" not in request or pattern_id(request["pattern"]) == selected,
                    "--pattern conflicts with request.pattern")
            request["pattern"] = selected
        plan = build_plan(request)
        args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("timeline_plan.py: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
