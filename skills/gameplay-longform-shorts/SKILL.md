﻿---
name: gameplay-longform-shorts
description: Turn one PS5 OBS session (a 16:9 recording plus the Aitum 9:16 recording of the same session) into a tightened long YouTube video and a fast-cut Short, both 4K, with outro cards, a poster title card, thumbnails, and copy. Use when the user drops a PS5 Recordings folder with a horizontal and a vertical video, asks for "long format from horizontal and shorts from vertical", "render in 4K", or says "make it like the MycoPunk edit". Built from the Oct 2026 MycoPunk session; reads RULES.md of video-edit first.
---

# Gameplay long video + Short (Pushpstation)

Finished example: `%USERPROFILE%\Videos\pipeline\MycoPunk-final` (long 4K, Short 4K, `packaging\` thumbnails). Read `references/choices.md` first: the user's decisions and corrections, in order. It overrides this file. `video-edit/RULES.md` overrides both.

The files are the horizontal `PS5 <date>.mp4` (3 audio tracks: mix, game, mic) and `Vertical\PS5 Vertical <date>.mp4` (game on top, facecam below, same 3 tracks). They are two recordings of one session, not one cut from the other.

## Workflow (in this order; the user's gates stay)

1. **Intake.** `video-pipeline` Step 0 questions only if the user has not already said what to make. Ask nothing the message already answers. Tell the user plainly if the game on screen is not the game they named (MycoPunk was named "Mafia" once; Mafia was only the next video).
2. **Research the format** (WebSearch, 2-3 queries) and write it in `edit-decision.md`. What the 2026 search found: long gameplay 8-15 min, trim intro and dead air with jump cuts, chapters; Shorts hook in 1-3 s, big captions, one idea. See `choices.md` for what the user then overruled.
3. **Stems and transcript.** `ffmpeg -map 0:a:1` (game) and `0:a:2` (mic) to wav; transcribe the mic with `video-edit/scripts/whisper_gpu.py --language hi` and **no `--prompt`** (a name prompt gets repeated as invented speech over silence, e.g. "The Old Country, PS5, Pushpstation"). Whisper timestamps drift over silences (words clump, then jump), so use them for what was said, not for timing. For a Short's captions re-transcribe each clip window alone with VAD off (copy `whisper_gpu.py`, set `vad_filter=False`).
4. **Look.** A 1-per-15 s contact sheet of both files (`fps=1/15,scale=320`, `tile`). Find menus, loading, mission-text, black or frozen stretches (`freezedetect=n=0.003:d=3`), the best action beats and any capture glitch (green strip at the bottom of the vertical game area).
5. **Cut list.** `scripts/keep_list.py mic.wav game.wav keep.txt --cut A-B ...` keeps speech or loud game audio, drops dead air, and forces out the stretches you named (cuts shorter than `--gap` get merged back). Result for MycoPunk: 21 min to 15:21 in 36 segments. A 4 s cold-open hook from the loudest action beat goes first.
6. **Sync.** `scripts/sync_offset.py game.wav vertical_game.wav` (prints X, vertical = horizontal + X; was +0.92). Confirm with one frame from each file at a loud peak.
7. **Edit decision + preview.** Write `edit-decision.md` (kept ranges, mix, outro, what was skipped), render a 720p preview, and **wait for the user's "yes"** before the final render. The user approved the 15:21 cut as "perfect"; do not re-tighten it unasked.
8. **Cards.** `scripts/render_cards.ps1 -OutDir cards -Game <NAME> -NextGame "<NEXT GAME>" -Subline "PS5 GAMEPLAY  ·  PS PLUS" -Poster poster.png`. Poster = a real key-art crop from the PS5 home hub frame (`crop` above the facecam and below the top bar, so no avatar, icon row or gamertag). Look at it.
9. **Audio.** `scripts/mix_audio.ps1 -Game game.wav -Mic mic.wav -Segments keep.txt -Out long.m4a` (voice -16, game -23 ducked, final -14 LUFS, peak <= -2.5 dB before AAC). Check after: I within 1 LU of -14, peak <= -1.5 dBTP.
10. **Render 4K.** `scripts/render_segments.ps1 -Source horizontal.mp4 -Segments keep.txt -Audio long.m4a -Out long-4K.mp4 -OutroPng cards\outro_long_4k.png -OutroSeconds 9`. For the Short: snap the chosen windows with `snap_cuts.py`, add a 3.5 s real-footage tail segment, then `-Source vertical.mp4 -SourceOffset 0.92 -Punch -TitlePng cards\title_short_4k.png -OutroPng cards\outro_short_4k.png -OutroSeconds 3.5` with `mix_audio.ps1 -FadeOut 3.2` (audio from the horizontal stems). Never one big filter graph: it ran out of memory at 4K.
11. **Check.** ffprobe size/fps/streams, `ebur128=peak=true`, a contact sheet of frames (title card, a punch frame, middle, outro card at full size), `blackdetect`. Say that the sources are 1080p, so 4K is upscaled (lanczos + `cas 0.35`).
12. **Packaging.** `video-packaging` for the thumbnail and Shorts cover (always from a final-video frame, not a glitch frame). Show titles, description and captions **in chat in code blocks**, not in a file; research the game and the hashtags first (`choices.md`).
13. **Clean up.** Copy the finals to `<pipeline>\<Game>-final\`, verify sizes, then delete the work folder (`Remove-Item -LiteralPath <folder> -Recurse -Force`; a wildcard on a folder path was refused). Never touch the original recordings.

## PowerShell traps seen here
- Variable names are case-insensitive: `$S`/`$s` and `$Z`/`$z` collided and caused a path error and an OutOfMemoryException.
- `ConvertFrom-Json` flattens an array of pairs; write cut lists as `start end` text lines, not JSON.
- `ffmpeg -f` is the format flag, not a string formatter; build file names with `"{0:00}" -f $i` first.
- Colons in filter values (`fontsdir=C:/...`, `drawtext fontfile`) break even when escaped; copy the font into the working folder and use a relative path, or skip drawtext.
- `$ErrorActionPreference='Stop'` makes ffmpeg's stderr (`2>&1`) throw; use `Continue` where stderr is parsed.
- JSON written with `Set-Content -Encoding utf8` has a BOM and `package.py` rejects it; write with `[IO.File]::WriteAllText(path, text, (New-Object Text.UTF8Encoding($false)))`.
- `"$t"` of `14.0` prints `14`; do not build file names from float times.
- Headless Chrome returns before the PNG exists; wait for the file.
