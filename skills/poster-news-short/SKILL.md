---
name: poster-news-short
description: Make a faceless vertical news Short (YouTube Shorts + Instagram Reel) from official game posters and the user's own voice, end to end - research, script, scratch voice, Voice Studio recording, take splicing, word-timed posters, edited music bed, cover and captions. Use when the user wants a PS Plus / game-news Short built from posters or key art, says "faceless video", "use the posters", "make the Short like the last one", or sends a competitor reel as a reference. Built from the Nov 2026 PS Plus "12 games leaving" Short; reuse it for each monthly update.
---

# Poster news Short (Pushpstation)

The finished example is `%USERPROFILE%\Videos\pipeline\ps-nov26` (final: `02-shorts\pushpstation-ps-plus-leaving-nov26-FINAL.mp4`). Read `references/choices.md` first: it is the list of what the user decided and corrected, in order. It overrides anything below.

## Workflow (do the steps in this order)

1. **Reference reels (optional).** A competitor reel link is research only (never reuse footage or voice). Use the `agent-reach` skill (`yt-dlp`, no personal Instagram login), look at a 1-per-2-s contact sheet, note structure, then do your own research and write a fresh script.
2. **Research the facts.** Names, dates, counts and the source. Keep caveats ("select regions", list can change) on cards and in the caption, not in the voice.
3. **Posters.** Portrait art, 12 titles max in one grid. Steam `library_600x900_2x.jpg` (`https://cdn.akamai.steamstatic.com/steam/apps/<id>/`) for most; newer apps use the hashed path from `IStoreBrowseService/GetItems/v1` (`library_capsule_2x`); console-only games from the PS Store `image.api.playstation.com` master image. Look at a contact sheet. Square art is placed on a blurred backdrop, never stretched.
4. **Script.** Pushpstation style card (`~/.claude/channel/style-card.md`), Hinglish in English letters, always "aap". Write with `faceless-vo-script` (edit.json + 03-script.json, validator must pass). `scripts/mkscript2.py` shows the shape (8 cues: hook, big names, sports line, list, the "fun" game, rest of list, wishlist ask, outro). Add 1-2 `[your take]` lines.
5. **Scratch voice.** `own-voice-render` (Devanagari for every cue, numbers as words, `lint`, `render`). Offer a Hinglish and an English version if the user asks for English. It is only a draft: the user usually records his own. Say you cannot hear it.
6. **Voice Studio.** `scripts/mkset.py` builds a set (`~/voice-studio/sets/<name>`: proxy video, `my-script.txt`, `cues.json`, `video.json`) and `switch.ps1 -set <name>` loads it; `start.bat` opens the app. The user edits the script while recording, so always work from the transcripts in `recordings\_transcripts`, not from your script.
7. **Voice edit.** `scripts/assemble_nov26.py`: choose takes (user names them or compare), run **voice-enhance** on each take first (`--declip` if the take hits 0 dBFS), level the takes to each other, splice inside a pause, squeeze pauses (> 0.28 s to 0.16 s), trim the ends, 25 ms cross-fades. Fillers: Whisper hides them, so list voiced runs with their words (see `choices.md`) and say plainly what was and was not found.
8. **Picture.** `scripts/build_final.py <voice.wav> <timeline.json> <out.mp4>`: `timeline.json` (from step 7) holds a start time per scene taken from the **words the user actually said** (poster at name start minus 0.12 s). Scenes: hook grid, posters with name cards, a pair shot, "17 NOV" date card + comment ask, outro tape + subscribe pill. It writes `<out>.silent.mp4` plus a mux with its own simple mix. **Use the silent file for the final mix.**
9. **Music + mix.** `scripts/mix_music.py <silent.mp4> <voice.wav> <timeline.json> <out.mp4>` with env `MUSIC` and `MSTART`. Voice at about -15 LUFS alone, music bed automated (intro swell, ducked while talking, extra small dip on each game name, lift in gaps and under the outro), final -14 LUFS, true peak under -2 dB. Pick music with the SnipSound connector (only music source), clean and sparse, never heavy synth.
9b. **Brand (from 2026-10-29).** Run `video-edit/brand/brand_wrap.ps1 -Mode short -NoOutro -Note "<topic, e.g. PS Plus November>" -Tag "GAMING NEWS"` on the mixed final. Its voiced outro scene (tape + subscribe pill) stays the ending. Check that the NOW PLAYING band (y 280-640) hides no poster name in the hook grid.
10. **Cover.** `scripts/cover.py <out.jpg>` makes a 1080x1920 cover from the official posters (red tape hook + cream tape count, safe zones respected); verify with `video-packaging ... check --platform shorts`.
11. **Captions.** `video-packaging` copy rules: 3 ranked titles under 60 characters, a Shorts caption with `#Shorts` + one more, an Instagram caption with the hook in the first 125 characters and 5-8 specific hashtags. Save as `packaging.md`. Do not state reasons, dates or claims you could not verify.
12. **Clean up.** Keep only the final video, the silent picture lock, posters, `voice\final`, `build`, music with its licence line. Delete test versions only when the user says so.

## Using the scripts
They are the working Nov 2026 files. Each has the project folder as one line at the top (`J`, `OUT`, `TMP`, `P`, `R`, `ART`); set it to the new folder, then adjust:
- `build_final.py`: the `G` table (poster files, card titles, "select regions" notes), `ORDER`, the pair shot (`pair_scene(["rdr2","gta5"])` and its card text), the hook card ("12 games", "LEAVING 17 NOV"), the date and ask cards.
- `assemble_nov26.py`: `PARTS` (which take and which seconds), the `E` event list (words to search for in each take's `transcript.roman.json`), `LEAD`.
- `mix_music.py`: dB constants at the top (`BASE, TALK, NAME, OUTRO, INTRO`).
Run Python through `uv run --with numpy --with pillow`; bare `python` is a Store stub on this PC.

## Pitfalls hit on the first run
- PowerShell variables are case-insensitive: `$p` overwrote `$P`. Use distinct names (`$root`, `$name`).
- uv's Python minor-version link fails here: pass the explicit `python.exe` under `%LOCALAPPDATA%\uv\python` when creating venvs.
- A mic-gain mistake produced a clipped take (peak 0 dBFS, thousands of clipped samples) 15 dB hotter than the others. Check every take with `astats` before choosing it.
- Whisper word times drift on stretched words; they are good enough for posters (switch 0.12 s early) but not for cutting. Cut on the energy envelope.
- An adaptive pause threshold must be relative to the speech level (p90 - 24 dB), not only the noise floor, after denoising.
- The final mix must not be judged by `ebur128` alone: measure the music stem under speech (about -25 LUFS was right) and the voice stem (about -15).

## Editions / price explainer Shorts (GTA 6 Standard vs Ultimate, Oct 2026)
Second format built with this skill. Example: `%USERPROFILE%\Videos\pipeline\gta6-editions` (`final\gta6-editions-india-short-v2.mp4`). Script: `scripts/build_editions_short.py` (data-driven `TL` list: start second per cue from `voice.srt`, sub-shots inside a cue) + `scripts/mix_music_generic.py` (set `MUSIC`, `MSTART`; needs a small `tl.json` with `duration` and `events`).
- **Official art, not posters.** Open the publisher's media page in the built-in browser (`rockstargames.com/VI/media`), read the "Download All" zip links with `javascript_tool`, `curl` the zips into a new dir (Ultimate Edition and Vintage Vice City Pack zips had exact item names in the file names - use them for cards). Never use competitor footage.
- **India prices.** Open `store.playstation.com/en-in/search/<title>` in the browser and read the price text. Web search alone gave ₹5,999 / ₹7,499; the store page confirmed it. Say "PS Store India" on the card, check whether an upgrade SKU is "Unavailable" before promising one.
- **Framing (learned Oct 2026, user: "3/4 of the screen is empty").** Never put a small poster on a big blurred backdrop in the first 5 s. Portrait art (aspect > 1.2) goes full-bleed 1080x1920 with a slow push-in; landscape art becomes a 1080x1240 near-square crop (focal x per shot) centred at y 340, over a blurred backdrop; cards sit at y 1150 (above the bottom ~35 % that apps cover; sides about 6 %, top about 15 %). Hook = full-bleed key art + two tapes, no tiny hero.
- Render a 11-frame preview strip (`prev.py` importing the build module) before the full encode.
- Fonts: Segoe UI / Segoe UI Black render the rupee sign (U+20B9); spell rupee amounts as words for the voice ("five thousand nine hundred ninety nine rupees").
- Drop claims you cannot confirm on the publisher or store page (GTA+ bonus month, CEO quotes, upgrade promises, pre-order cutoff dates).
- Bash heredocs with apostrophes inside break the tool: write Python files with the Write tool.
