#!/usr/bin/env python3
"""Render the teleprompter, captions, and record notes from 03-script.json.

The JSON is the only script. Do not hand-edit the files this writes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from catalog import ANTI, archetype, edge_rate, edge_voice, model_for  # noqa: E402

WORD_RE = re.compile(r"\S+")
LINE_CHARS = 42


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def clock(seconds: float) -> str:
    ms = max(0, int(round(seconds * 1000)))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"


def srt_clock(seconds: float) -> str:
    return clock(seconds).replace(".", ",")


def words_of(text: str) -> list[str]:
    return WORD_RE.findall(text)


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part for part in parts if part]


def two_lines(words: list[str]) -> str:
    """Split a word list into one line, or two lines near the middle."""
    if not words:
        return ""
    text = " ".join(words)
    if len(text) <= LINE_CHARS:
        return text
    best = 1
    best_score = None
    for index in range(1, len(words)):
        left = " ".join(words[:index])
        right = " ".join(words[index:])
        # Prefer a break close to half, and reject a one-word right side.
        score = abs(len(left) - len(right)) + (80 if len(words) - index < 2 else 0)
        if best_score is None or score < best_score:
            best_score = score
            best = index
    return " ".join(words[:best]) + "\n" + " ".join(words[best:])


def cards_for_sentence(sentence: str) -> list[str]:
    words = words_of(sentence)
    if not words:
        return []
    # One card when the sentence fits on two phone lines. Otherwise split
    # the words in half and give each half its own card.
    if len(" ".join(words)) <= LINE_CHARS * 2:
        return [two_lines(words)]
    mid = max(2, len(words) // 2)
    return [two_lines(words[:mid]), two_lines(words[mid:])]


def caption_blocks(cue: dict) -> list[tuple[float, float, str]]:
    cards = []
    for sentence in sentences(cue["spoken"]):
        cards.extend(cards_for_sentence(sentence))
    if not cards:
        return []
    weights = [max(1, len(words_of(card))) for card in cards]
    total = sum(weights)
    start = float(cue["in_sec"])
    end = float(cue["out_sec"])
    span = end - start
    cursor = start
    blocks = []
    for card, weight in zip(cards, weights):
        card_end = end if card is cards[-1] else cursor + span * (weight / total)
        blocks.append((cursor, max(card_end, cursor + 0.01), card))
        cursor = card_end
    return blocks


def render_teleprompter(script: dict) -> str:
    cues = script["cues"]
    lines = [
        f"# {script['title']}",
        "",
        "Generated from 03-script.json. Change the JSON and render again.",
        "",
        f"Register: {script['register']}",
        f"Format: {script['format']}",
        f"Platform: {script['platform']}",
        f"Status: {script['status']}",
        f"Persona: {script['persona']}",
        "",
        "Read only the spoken line. The bracket is for you, not for the microphone.",
        "",
    ]
    for cue in cues:
        words = words_of(cue["spoken"])
        span = float(cue["out_sec"]) - float(cue["in_sec"])
        wps = len(words) / span if span else 0
        emphasis = ", ".join(cue.get("emphasis") or []) or "—"
        lines.extend([
            f"## {cue['id'].upper()} · {clock(cue['in_sec'])} → {clock(cue['out_sec'])} · {cue['role']} · {wps:.2f} wps",
            f"Shot: {cue['shot_id']}",
            "",
            cue["performance"],
            "",
            f"Spoken: {cue['spoken']}",
            f"Emphasis: {emphasis}",
        ])
        if cue.get("mix_note"):
            lines.append(f"Mix: {cue['mix_note']}")
        if cue.get("fact_source"):
            lines.append(f"Fact: {cue['fact_source']}")
        lines.append("")
    if script.get("intentional_silence"):
        lines.append("## Silence")
        lines.append("")
        for gap in script["intentional_silence"]:
            lines.append(
                f"- {clock(gap['in_sec'])} → {clock(gap['out_sec'])}: {gap['reason']}"
            )
        lines.append("")
    if script.get("recut_requests"):
        lines.append("## Recut requests")
        lines.append("")
        for request in script["recut_requests"]:
            lines.append(f"- {request['shot_id']}: {request['need']} ({request['reason']})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_srt(script: dict) -> str:
    blocks = []
    for cue in script["cues"]:
        blocks.extend(caption_blocks(cue))
    chunks = []
    for index, (start, end, text) in enumerate(blocks, start=1):
        chunks.append(f"{index}\n{srt_clock(start)} --> {srt_clock(end)}\n{text}\n")
    return "\n".join(chunks).rstrip() + "\n"


def render_notes(script: dict) -> str:
    lines = [
        f"# Record notes — {script['title']}",
        "",
        script["persona"],
        "",
        script["mic_note"],
        "",
        "Record the spoken line only. Leave every gap where the teleprompter has no line. "
        "Do not fill silence with a breath that turns into a new word.",
        "",
        "Generated from 03-script.json. Change the JSON and render again.",
        "",
        "## Pronunciation",
        "",
    ]
    pronounce = list(script.get("pronounce") or [])
    for cue in script["cues"]:
        for entry in cue.get("pronounce") or []:
            if entry not in pronounce:
                pronounce.append(entry)
    if not pronounce:
        lines.append("No traps marked.")
    else:
        for entry in pronounce:
            lines.append(f"- {entry['word']}: {entry['say']}")
    lines.extend(["", "## Cues", ""])
    for cue in script["cues"]:
        span = float(cue["out_sec"]) - float(cue["in_sec"])
        lines.append(
            f"- {cue['id']} ({span:.1f}s, {cue['role']}): {cue['performance']}"
        )
    lines.append("")
    return "\n".join(lines)


def pause_track(script: dict) -> str:
    cues = script["cues"]
    chunks = []
    for index, cue in enumerate(cues):
        chunks.append(cue["spoken"])
        if index + 1 >= len(cues):
            continue
        gap = float(cues[index + 1]["in_sec"]) - float(cue["out_sec"])
        if gap >= 0.25:
            chunks.append(f"[pause {gap:.1f}s]")
    return "\n\n".join(chunks) + "\n"


def render_brief(script: dict) -> str:
    voice = archetype(script)
    settings = voice["elevenlabs"]
    edge = edge_voice(script)
    rate = edge_rate(script)
    lines = [
        f"# TTS brief — {script['title']}",
        "",
        "Generated from 03-script.json. Change the JSON and render again.",
        "",
        "## Content analysis",
        "",
        f"- Format: {script['format']}",
        f"- Register: {script['register']}",
        f"- Platform: {script['platform']}",
        f"- Duration: {float(script['video_duration_sec']):.1f}s",
        f"- Archetype: {voice['label']}",
        f"- Why this voice: {voice['direction']}",
        "",
        "## Emotion map",
        "",
        "| Cue | Time | Role | Emphasis | Delivery |",
        "| --- | --- | --- | --- | --- |",
    ]
    for cue in script["cues"]:
        emphasis = ", ".join(cue.get("emphasis") or []) or "—"
        start = clock(float(cue["in_sec"]))
        lines.append(
            f"| {cue['id']} | {start} | {cue['role']} | {emphasis} | {cue['performance']} |"
        )
    if script.get("intentional_silence"):
        lines.extend(["", "Holds where the voice stays out:", ""])
        for gap in script["intentional_silence"]:
            lines.append(f"- {clock(float(gap['in_sec']))} → {clock(float(gap['out_sec']))}: {gap['reason']}")
    setting_text = ", ".join(f"{key} {value}" for key, value in settings.items())
    lines.extend([
        "",
        "## ElevenLabs",
        "",
        f"Model: `{model_for(script)}`.",
        f"Settings: {setting_text}.",
        "",
        "Paste this as the voice direction:",
        "",
        voice["direction"],
        "",
        f"Persona on this video: {script['persona']}",
        "",
        "## Edge TTS",
        "",
        "No API key. This is the voice `scripts/speak.py` records.",
        "",
        f"- Voice: `{edge}`",
        f"- Rate: `{rate}`",
        "- Hindi neural voices (`hi-IN-MadhurNeural`, `hi-IN-SwaraNeural`) want Devanagari. This script is Roman, so the Indian English voice reads both registers.",
        "",
        "## Do not",
        "",
    ])
    for rule in ANTI:
        lines.append(f"- {rule}")
    lines.extend([
        "",
        "## Paste track",
        "",
        "Spoken lines only, with the gaps the edit already has. A TTS box that ignores bracket pauses will run the lines together. Use the timed voice file instead.",
        "",
        pause_track(script).rstrip(),
        "",
    ])
    return "\n".join(lines)


def render(script: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "02-script.md").write_text(render_teleprompter(script), encoding="utf-8")
    (out_dir / "04-captions.srt").write_text(render_srt(script), encoding="utf-8")
    (out_dir / "05-record-notes.md").write_text(render_notes(script), encoding="utf-8")
    (out_dir / "06-tts-brief.md").write_text(render_brief(script), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a voiceover package from 03-script.json")
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    render(load(args.script), args.out)


if __name__ == "__main__":
    main()
