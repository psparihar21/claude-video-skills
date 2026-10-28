---
name: video-packaging
description: Analyzes a real video and makes only the packaging asked for. That is one production-ready thumbnail or cover built from a real frame of that video plus short type (YouTube 1280x720, Shorts or Reel 1080x1920, Instagram feed 1080x1350, JPG under 2 MB), or a title, caption or YouTube description. Use it when the user asks for a thumbnail, cover, title, caption or description, or to package a video. The thumbnail always comes from an extracted frame, never a generated scene, person or background. It finds clean frames (skipping burned-in titles), crops around the subject, checks phone-size legibility and contrast, and designs in Canva Pro when connected, otherwise with a local ffmpeg + Pillow renderer.
compatibility: Local renderer needs ffmpeg/ffprobe on PATH and Python 3.10+ with Pillow and numpy (uv runs it with no install). Optional OCR uses Windows built-in OCR or tesseract. Canva path needs the Canva connector (resize needs Canva Pro). Works in Claude Code and in claude.ai with code execution.
license: MIT
---

# Video packaging

Make what was asked for, from what is actually in the video. Nothing else.

Run the script as `uv run "${CLAUDE_SKILL_DIR}/scripts/package.py" <cmd> …` (or `python scripts/package.py`
after `pip install -r requirements.txt`). Reference files:
- `references/platforms.md`: sizes, layouts, legibility rules, checks.
- `references/copy.md`: hook, title, description and caption rules. Read it before writing copy.
- `references/canva.md`: the verified Canva tool order. Read it before any Canva call.
- `scripts/title.py` lints a title with its thumbnail hook; `scripts/chapters.py` drafts and validates chapters from an SRT, VTT or Whisper JSON. Both are plain Python (from youtube-agent-skill, MIT): `python "${CLAUDE_SKILL_DIR}/scripts/title.py" --title "..." --thumb "..."`.

## 1. Scope the request

| User says | Deliverable |
|---|---|
| YouTube thumbnail / thumbnail for a long video | `youtube` cover 1280×720 |
| Shorts thumbnail / cover | `shorts` cover 1080×1920 |
| Instagram Reel cover | `reel` cover 1080×1920 |
| Instagram feed / post | `feed` cover 1080×1350 |
| caption | caption for the named platform only |
| description | YouTube description |
| title | 3 titles, ranked |
| thumbnail + caption/description | both, for the named platform only |

- Write the scope in one line first ("Making: YouTube thumbnail + YouTube description") and check the answer
  against it. Never add a platform, a format, or titles nobody asked for.
- "Package this" with no platform: ask once, "YouTube, Shorts, or Instagram?". No video: ask for the file.
  Do not search the disk.
- A/B variants only when asked (YouTube Test & Compare takes up to 3). Change **one** element between them
  (the frame, the hook, or the side), never several.

## 2. Analyze (always, before any copy)
```
uv run "${CLAUDE_SKILL_DIR}/scripts/package.py" analyze "<video>" --out "<work>/pkg"
```
It does one low-res decode pass (keyframes only for heavy 4K or long input), scores sharpness, contrast, colour
and exposure, OCRs the best frames and their neighbours for **burned-in titles, logos and stickers**, then picks
8 distinct candidates, clean ones first. It measures audio (dB, LUFS, silence) without transcribing, and never
touches the video. It takes about 10 s for a 20 s 1080p or a 1 min 4K clip.

Outputs: `candidates.jpg` (C1…C8 with time, score and flags), `contact_sheet.jpg` (the timeline), `frames/`
(full-resolution candidates) and `analysis.json`.

**Then look.** Open `candidates.jpg` and `contact_sheet.jpg`. OCR misses stylised lettering, so your eyes are the
final gate. Reject any frame with:
- burned-in text, a logo or sticker from the edit (flags `overlay-text` / `overlay-near`), or a game or brand logo
  you would be re-publishing,
- a transition or blend, motion blur, closed eyes, or a half-visible subject.

Prefer one clear focal point, a calm side for type, and the "after" or payoff look (the finished setup, the
result). If the best look only appears in a short stretch, zoom in with `analyze … --window 15-20`; a window
samples up to 12 fps. Use the exact clean timestamp in the brief (`"video"` + `"time"`), even between
candidates.

Write `<work>/pkg/context.md` with four short sections: what is visible, how it changes, what the audio
measurement supports, and what you will not claim. The user's notes are claims. When they disagree with the
frames, the frames win, and you say so in one sentence.

## 3. Copy
Follow `references/copy.md`. The hook is 2–4 words, never more than 3 lines / 7 words / 18 characters per line, with
no emoji. It complements the title and never repeats it. Write the eyebrow (≤ 4 words) only if it adds a fact,
such as the format or duration. Over the limit means rewrite, never shrink.

## 4. Thumbnail

### Path A: Canva connected
List the Canva tools actually present first, then follow `references/canva.md`. In short:
1. Render a `background_only` brief locally (crop, grade and soft scrim baked in).
2. Upload it and create the design.
3. Replace the page background with the upload and restyle the hook.
4. Preview, and **commit only after the user approves**.
5. Export JPG at the exact size, then run `check`.

### Path B: local renderer (Canva not connected)
Say "Canva is not connected (Settings → Connectors → Canva)", then render. Never use an image generator.
```json
{
  "platform": "youtube",
  "video": "<video path>", "time": 17.17,
  "hook": "Empty desk to night mode",
  "eyebrow": "20 sec build",
  "highlight": "night",
  "out": "youtube_cover.jpg"
}
```
Optional fields:
- `frame`: an extracted image, used instead of `video` + `time`.
- `side`: `auto` (default), or `left` / `right` / `top` / `bottom` (YouTube); `top` / `bottom` (vertical).
- `focus`: `[x, y]`, which overrides the subject-aware crop.
- `font`: `heavy` (default), `condensed` (more letters per line) or `clean`.
- `grade`: `auto` / `none`.
- `accent`: a hex colour, or `auto` (sampled from the frame).
- `uppercase`: defaults to true.
- `trim_bars`: defaults to true.
- `background_only`: for Canva.

Paths in a brief are relative to the brief's folder.
```
uv run "${CLAUDE_SKILL_DIR}/scripts/package.py" render "<work>/brief.json"
```
What the renderer does:
- Fits the hook to every layout.
- Searches crop × layout together, so the subject stays in frame and out from under the type.
- Trims edit bars, grades lightly, and darkens a scrim until white type reaches 4.5:1.
- Draws the hook (stroke and shadow), the eyebrow tag, and the highlight word in a colour that actually reads.
- Exports progressive 4:4:4 JPEG under 2 MB, then checks itself.

Exit codes:
- **0:** passed. It wrote `<out>`, `<out>.report.json` and `<out>.preview.jpg`.
- **2:** refused. The copy is over the limit, has emoji, names several platforms, or cannot fit at a size that
  reads on a phone. Devanagari needing complex shaping is also refused when Pillow lacks raqm; use Hinglish or
  Canva. Rewrite the hook; never loosen the rules.
- **3:** an export check failed. Report it. Do not hand the file over.

**Always open `<out>.preview.jpg` before handing over.** It shows the zones and phone-size tiles on light and dark
UI. Fix it, or pick another frame, if:
- the hook doesn't read at the small size,
- the type covers the subject (the report warns when more than 25% of the subject is under the type),
- the frame looks soft (upscale above 2.2×).

### No shell and no Canva
Deliver the copy, the chosen timestamp and a layout spec. State plainly that no image was made.

## 5. Hand-off
Give only what was asked:
- the scope line,
- the cover path, size, bytes, source timestamp, "upscaled ×N" if any, and the Canva link on Path A,
- the copy in a paste-ready code block,
- one line on any note the frames contradicted, and one on anything you refused to claim.

Do not re-encode, trim, or attach anything to the video.

## Done checklist
- [ ] The deliverables match the scope table exactly.
- [ ] You opened `candidates.jpg` and the chosen frame before writing copy. The frame has no burned-in text or logo.
- [ ] `context.md` exists and matches the frames.
- [ ] `render` (or `check`) exited 0, and you looked at the preview.
- [ ] The cover is JPG at the exact size, under 2 MB, from the real frame. No image generator was used.
- [ ] The copy invents no spec, price, song or speech. Music is mentioned only if the audio allows it and the user
      said so.
