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
| `references/hook-and-retention.md` | Hook, pacing and retention method, studied from 5 top editing tutorials and 5 big Indian gaming channels |
| `brand/brand_wrap.ps1` | Adds the channel's intro, slash transitions, subscribe click and end screen to a finished long video or Short |
| `brand/hf/*.html` | The HyperFrames graphics: `intro_long`, `transition`, `subscribe`, `outro_long` (16:9) and `intro_short`, `outro_short` (9:16), with shared `brand.css` / `brand.js` |
| `brand/hf/fonts/` | Anton and Rajdhani Bold (SIL Open Font License, licence files included) |
| `brand/make_sfx.sh` | Synthesises the whoosh, impact, click, pop and bell sounds into `brand/sfx/*.wav` (no sound library needed) |

## Channel intro and outro (brand pack)

Every final goes through `brand/brand_wrap.ps1`:

```powershell
.\brand\brand_wrap.ps1 -Video final.mp4 -Mode long -IntroAt 6.5 -Note "Game name" -Cuts "95.2,301.8" -Out final-branded.mp4
.\brand\brand_wrap.ps1 -Video short.mp4 -Mode short -Note "Game name" -Out short-branded.mp4
```

- **Long video:** a 2.9 s sting where the cold-open hook ends (`-IntroAt`), a 1 s slash transition at each section change (`-Cuts`), a subscribe-click animation on the sign-off (`-SubAt`), and a 15 s end screen whose slots line up with YouTube's end-screen elements.
- **Short:** a "NOW PLAYING" band over the hook at 0 s and a 3.6 s end card. `-NoOutro` skips the end card.

The script renders the graphics locally with HyperFrames (alpha ProRes) at the video's own resolution, encodes with NVENC and prints loudness. To make the pack yours, change the colours in `brand/hf/brand.css` and the channel name in the `.html` files. If you move an animation time, update `brand/make_sfx.sh` and re-run it.

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