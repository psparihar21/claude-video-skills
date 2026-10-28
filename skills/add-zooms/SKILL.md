---
name: add-zooms
description: Add punch-zooms, listicle ratchet zooms and slow Ken Burns pushes to a flat talking-head or voiceover clip (mostly 9:16 Shorts), driven by word timestamps. Use when the user says "add zooms", "punch in", "make it less flat", "add camera movement" to an existing cut. Windows, ffmpeg only, free. Idea adapted from Tella's add-zooms (louisedesadeleer/add-zooms); script written fresh.
---

# add-zooms

Read `~/.claude/skills/video-edit/RULES.md` first (My style wins). Never overwrite the source.

1. Get word timestamps (video-edit `scripts/whisper_gpu.py` or Parakeet).
2. Write `map.json` next to the clip. Times in seconds:
   - `punch`: hard cut in on one emphasised word, hold 0.4-0.8 s, hard cut out. `z` 1.18-1.30.
   - `ratchet`: for lists; each item cuts to a higher level (`steps`, `each` seconds), then back.
   - `kenburns`: slow smooth push over one insight line, `z` up to 1.14. The only smooth move.
   - `focus_y`: vertical anchor, 0.4 = slightly above centre (faces). 0.5 for b-roll or landscape.
3. Render: `<faceless-vo-script venv python> scripts/zoom.py in.mp4 map.json out.mp4` (NVENC; `--cpu` for libx264). Audio is copied untouched.
4. Verify: grab frames at rest and at a peak, compare crops at 100%. Re-tune the map, re-render.

Rules: peak at or below 1.30 (script asserts) so 1080p stays sharp; no zoom on filler; max one punch per ~3 s; at most one move per sentence. Not for clips with burned captions placed near edges: render zooms first, burn captions after.
