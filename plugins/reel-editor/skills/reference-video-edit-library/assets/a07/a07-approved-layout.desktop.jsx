import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

const clamp = (n, a, b) => Math.min(b, Math.max(a, n));
const rgba = (hex, opacity) => {
  const v = String(hex).replace("#", "");
  const h = v.length === 3 ? v.split("").map(x => x + x).join("") : v;
  return "rgba(" + parseInt(h.slice(0, 2), 16) + "," + parseInt(h.slice(2, 4), 16) + "," + parseInt(h.slice(4, 6), 16) + "," + clamp(Number(opacity), 0, 1) + ")";
};

function RevealText({ text, time, animated }) {
  const characters = Array.from(String(text));
  const stagger = 0.52 / Math.max(characters.length - 1, 1);
  return <>{characters.map((character, index) => {
    const opacity = animated ? clamp((time - 0.04 - index * stagger) / 0.04, 0, 1) : 1;
    return <span key={index} style={{ display: "inline-block", opacity }}>{character === " " ? "\u00a0" : character}</span>;
  })}</>;
}

export default function A07ReferenceLayout({ item }) {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const time = frame / fps;
  const p = item.props;
  const sizeScale = width / 1080;
  const mode = p.mode;
  const bodyText = p.text2 && time >= Number(p.switchAtSeconds) ? p.text2 : p.text;
  const background = p.transparentBackground ? "transparent" : p.backgroundColor;
  const shadow = Number(p.shadowX) + "px " + Number(p.shadowY) + "px " + Number(p.shadowBlur) + "px " + rgba(p.shadowColor, p.shadowOpacity);
  const typeStyle = {
    width: "max-content", maxWidth: Number(p.maxTextWidth),
    boxSizing: "border-box", textAlign: "center",
    backgroundColor: rgba(p.bandColor, p.bandOpacity),
    color: p.textColor, fontFamily: p.fontFamily, fontWeight: Number(p.fontWeight),
    textShadow: shadow, whiteSpace: "pre-wrap", overflowWrap: "break-word",
  };
  const baseBlock = {
    ...typeStyle, position: "absolute", left: 540, transform: "translateX(-50%)",
  };
  const bodyStyle = {
    fontFamily: p.bodyFontFamily ?? p.fontFamily,
    fontWeight: Number(p.bodyFontWeight ?? p.fontWeight),
    padding: "14px 22px 16px", fontSize: Number(p.bodySize),
    lineHeight: Number(p.bodyLineHeight) + "px", letterSpacing: Number(p.bodySpacing),
  };
  const labelStyle = {
    position: "absolute", left: 72, maxWidth: 900,
    padding: "8px 12px", boxSizing: "border-box",
    fontFamily: p.labelFontFamily, fontWeight: 400,
    color: p.textColor, whiteSpace: "pre-wrap", overflowWrap: "break-word",
    backgroundColor: rgba("#000000", 0.58),
  };
  // A one-line first band lands the second at secondBandY. Longer first copy
  // grows naturally and pushes the second down, preserving the gap.
  const splitGap = Math.max(24, Number(p.secondBandY) - Number(p.bodyY) - Number(p.bodyLineHeight) - 30);
  return <AbsoluteFill style={{ backgroundColor: background, overflow: "hidden" }}>
    <div style={{ position: "absolute", left: 0, top: 0, width: 1080, height: 1920, transformOrigin: "0 0", transform: "scale(" + sizeScale + ")" }}>
      {p.sampleLabel ? <div style={{ ...labelStyle, top: 176, fontSize: 30, lineHeight: "38px", backgroundColor: rgba("#000000", 0.48) }}>{p.sampleLabel}</div> : null}
      {mode === "intro" ? <>
        <div style={{ ...baseBlock, top: 449, minWidth: 307, padding: "7px 24px", fontSize: Number(p.introPlaceSize), lineHeight: "126px" }}>{p.titlePlace}</div>
        <div style={{ ...baseBlock, top: 728, padding: "7px 24px", fontSize: Number(p.introTitleSize), lineHeight: "106px" }}>
          <RevealText text={p.title} time={time} animated={p.animateIntro} />
        </div>
        <div style={{ ...baseBlock, top: 898, minWidth: 356, padding: "7px 24px", fontSize: Number(p.introVlogSize), lineHeight: "111px" }}>
          <RevealText text={p.titleVlog} time={time} animated={p.animateIntro} />
        </div>
      </> : <>
        {p.clock ? <div style={{ ...baseBlock, top: Number(p.clockY), minWidth: 230, minHeight: 122, padding: "6px " + Number(p.clockPaddingX) + "px", fontSize: Number(p.clockSize), lineHeight: Number(p.clockLineHeight) + "px", letterSpacing: Number(p.clockSpacing), fontWeight: Number(p.clockFontWeight ?? p.fontWeight) }}>{p.clock}</div> : null}
        {mode === "split" ? <div style={{
          position: "absolute", left: 540, top: Number(p.bodyY), transform: "translateX(-50%)",
          display: "flex", flexDirection: "column", alignItems: "center", gap: splitGap,
          width: "max-content", maxWidth: Number(p.maxTextWidth),
        }}>
          {bodyText ? <div style={{ ...typeStyle, ...bodyStyle }}>{bodyText}</div> : null}
          {p.secondBandText ? <div style={{
            ...typeStyle, ...bodyStyle,
            fontSize: Number(p.secondBandSize), lineHeight: Number(p.secondBandLineHeight) + "px",
          }}>{p.secondBandText}</div> : null}
        </div> : bodyText ? <div style={{
          ...baseBlock, ...bodyStyle,
          top: mode === "ending" ? 903 : Number(p.bodyCenterY),
          transform: mode === "ending" ? "translateX(-50%)" : "translate(-50%, -50%)",
          padding: mode === "ending" ? "15px 26px" : "14px 22px 16px",
          width: mode === "ending" ? 932 : "max-content",
          maxWidth: mode === "ending" ? 932 : Number(p.maxTextWidth),
          minHeight: mode === "ending" ? 330 : undefined,
          fontSize: mode === "ending" ? Number(p.endingSize) : Number(p.bodySize),
          lineHeight: (mode === "ending" ? Number(p.endingLineHeight) : Number(p.bodyLineHeight)) + "px",
          backgroundColor: mode === "ending" ? rgba(p.endingBandColor, p.endingBandOpacity) : rgba(p.bandColor, p.bandOpacity),
        }}>{bodyText}</div> : null}
      </>}
      {p.sceneLabel ? <div style={{ ...labelStyle, top: Number(p.sceneLabelY), fontSize: Number(p.sceneLabelSize), lineHeight: Number(p.sceneLabelLineHeight) + "px" }}>{p.sceneLabel}</div> : null}
    </div>
  </AbsoluteFill>;
}
