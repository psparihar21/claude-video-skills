#!/usr/bin/env python3
"""Lay an Indian neural voice on the locked cue times.

Uses Edge TTS (no API key). Each spoken line is synthesized, sped up only if
it would spill past its cue, then placed on a silent bed the length of the edit.
Paid engines stay in the TTS brief. This file is the voice you can drop on the video.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from catalog import edge_rate, edge_voice  # noqa: E402


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def require(tool: str) -> str:
    found = shutil.which(tool)
    if not found:
        raise SystemExit(f"{tool} is not on PATH.")
    return found


def duration(path: Path) -> float:
    result = subprocess.run(
        [
            require("ffprobe"), "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def fit(src: Path, dest: Path, window: float) -> tuple[float, bool]:
    """Fit the read inside the cue. Tempo stays under 1.18. A leftover tail is trimmed."""
    spoken = duration(src)
    room = max(0.3, window - 0.04)
    tempo = 1.0
    current = src
    if spoken > room:
        tempo = min(1.18, spoken / room)
        sped = dest.with_name(dest.stem + "-sped.mp3")
        subprocess.run(
            [
                require("ffmpeg"), "-y", "-i", str(src),
                "-filter:a", f"atempo={tempo:.4f}",
                "-vn", str(sped),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        current = sped
    trimmed = duration(current) > room + 0.15
    subprocess.run(
        [
            require("ffmpeg"), "-y", "-i", str(current),
            "-t", f"{room:.3f}",
            "-c", "copy",
            str(dest),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    if current is not src:
        current.unlink(missing_ok=True)
    return tempo, trimmed


async def synthesize(text: str, voice: str, rate: str, dest: Path) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(str(dest))


def lay(script: dict, clips: list[tuple[dict, Path]], dest: Path) -> None:
    total = float(script["video_duration_sec"])
    command = [
        require("ffmpeg"), "-y",
        "-f", "lavfi",
        "-t", f"{total:.3f}",
        "-i", "anullsrc=channel_layout=mono:sample_rate=48000",
    ]
    for _, path in clips:
        command.extend(["-i", str(path)])
    filters = []
    labels = []
    for index, (cue, _) in enumerate(clips, start=1):
        delay = int(round(float(cue["in_sec"]) * 1000))
        label = f"a{index}"
        filters.append(f"[{index}]adelay={delay}:all=1[{label}]")
        labels.append(f"[{label}]")
    inputs = len(labels) + 1
    filters.append(
        f"[0]{''.join(labels)}amix=inputs={inputs}:duration=first:"
        f"dropout_transition=0:normalize=0[out]"
    )
    command.extend([
        "-filter_complex", ";".join(filters),
        "-map", "[out]",
        "-c:a", "aac", "-b:a", "128k",
        "-t", f"{total:.3f}",
        str(dest),
    ])
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        tail = (result.stderr or "").strip().splitlines()[-8:]
        raise SystemExit("ffmpeg mix failed\n" + "\n".join(tail))


async def build(script: dict, out_dir: Path, voice: str) -> dict:
    rate = edge_rate(script)
    work = out_dir / "cues"
    work.mkdir(parents=True, exist_ok=True)
    report_cues = []
    clips: list[tuple[dict, Path]] = []
    for cue in script["cues"]:
        spoken = cue["spoken"]
        if "[FACT:" in spoken:
            raise SystemExit(f"{cue['id']} still has a [FACT:] hole. Keep the package in draft. No voice file.")
        raw = work / f"{cue['id']}-raw.mp3"
        fitted = work / f"{cue['id']}.mp3"
        await synthesize(spoken, voice, rate, raw)
        window = float(cue["out_sec"]) - float(cue["in_sec"])
        tempo, trimmed = fit(raw, fitted, window)
        raw.unlink(missing_ok=True)
        clips.append((cue, fitted))
        report_cues.append({
            "id": cue["id"],
            "in_sec": cue["in_sec"],
            "window_sec": round(window, 3),
            "spoken_sec": round(duration(fitted), 3),
            "tempo": round(tempo, 3),
            "trimmed": trimmed,
        })
    dest = out_dir / "07-voice.m4a"
    lay(script, clips, dest)
    report = {
        "voice": voice,
        "rate": rate,
        "file": dest.name,
        "duration_sec": round(duration(dest), 3),
        "cues": report_cues,
    }
    (out_dir / "07-voice-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthesize a timed Indian voice track from 03-script.json")
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--voice", type=str, default="", help="Edge voice id. Default follows the persona.")
    args = parser.parse_args()
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        raise SystemExit("edge-tts is not installed. Run: python -m pip install edge-tts")
    script = load(args.script)
    voice = edge_voice(script, args.voice or None)
    report = asyncio.run(build(script, args.out, voice))
    expected = float(load(args.script)["video_duration_sec"])
    if abs(report["duration_sec"] - expected) > 0.25:
        print(f"voice duration {report['duration_sec']}s does not match the edit {expected}s")
        return 1
    print(f"{report['file']}  {report['voice']}  {report['rate']}  {report['duration_sec']}s")
    for cue in report["cues"]:
        if cue["trimmed"]:
            print(f"warn {cue['id']} was trimmed to its {cue['window_sec']:.2f}s window")
    return 0


if __name__ == "__main__":
    sys.exit(main())
