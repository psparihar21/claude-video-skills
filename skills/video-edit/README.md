# video-edit

A Claude Code skill that works as a complete, free, Windows-only video editing desk for tech and gameplay videos
in Hindi, Hinglish or English.

## What it does

1. Asks the output format first (Short 9:16, full YouTube 16:9, or both).
2. Inventories the source, transcribes with word timestamps (GPU Whisper large-v3 for Hindi/Hinglish, Parakeet for English).
3. Researches product / game facts in Chrome and saves sources (no invented facts).
4. Plans the cut (silence, fillers, retakes) as an EDL and writes `edit-decision.md`.
5. **Stops and waits for your "yes"** before the final render.
6. Zooms / crops / reframes with FFmpeg, mixes royalty-free music (SnipSound) with ducking, adds captions and motion titles.
7. Exports with NVENC, measures loudness and specs, and rejects a bad export.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | The full workflow Claude follows |
| `RULES.md` | Your style + every correction you've given. Overrides `SKILL.md`. **Edit this to make it yours.** |
| `hinglish-dictionary.json` | Word overrides for the romanizer |
| `scripts/whisper_gpu.py` | faster-whisper large-v3 on CUDA → `transcript.json` |
| `scripts/parakeet_to_vtc.py` | Parakeet transcript → video-timeline-copilot format |
| `scripts/romanize.py` | Devanagari → Roman Hinglish per word, timestamps kept (`draft` then `apply`) |
| `scripts/captions.py` | Remaps words through the cut, writes `captions.srt`, `captions.ass`, `words.out.json` |

## Requirements

Windows 11, NVIDIA GPU (CPU works, slower), FFmpeg with CUDA/NVENC, Python 3.10+, and:
`faster-whisper`, `numpy`, [video-timeline-copilot](https://pypi.org/project/video-timeline-copilot/) (`vtc`),
HyperFrames (local render only), Google Chrome, and the SnipSound MCP (`https://mcp.snipsound.com/mcp`).
Nothing paid; the skill refuses cloud renders and paid services.

`SKILL.md` references the author's machine layout (a `uv` tool environment at
`%APPDATA%\uv\tools\video-timeline-copilot`). If yours differs, change the `$py` line under "Setup facts and commands".

## Usage

```text
> edit this video  C:\videos\review.mp4
> /video-edit make a Short from the second half
```

Correct it in plain words ("transition is very bad, fix it"); the skill asks if it should become a rule and appends it to `RULES.md`.