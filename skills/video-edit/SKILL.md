---
name: video-edit
description: Edit the user's tech and gameplay videos (Hindi, Hinglish or English) on Windows with free tools only — Claude Code, Parakeet / GPU Whisper, Chrome, FFmpeg + video-timeline-copilot (DaVinci Resolve Free when really needed), HyperFrames, SnipSound — using the RTX 5070. Use for any cut, caption, score, clip, Short, or render, and whenever the user corrects an edit.
---

# video-edit

**Read RULES.md first, every run.** RULES.md overrides this file. Its "My style" block is how this user wants videos to look. Follow it unless they say otherwise for one job.

Machine: Windows 11, PowerShell 5.1, NVIDIA RTX 5070 Laptop GPU, Intel Core Ultra 9 275HX (24 cores), 32 GB RAM. **Windows only**: never use macOS commands or Mac-only tools.

Use case:
- Tech: tutorials, reviews, screen recordings. YouTube 16:9, plus one 9:16 Short when the video is longer than 60 seconds.
- Gameplay: game capture with or without facecam. Keep the HUD readable. Open on action.

Non-goals: Epidemic Sound, paid music libraries, Suno, stock-music subscriptions, Tella or any paid editor/service, re-hosting audio, and rendering before the user approves the cut.

## Edit according to the user

1. Read the "My style" block and every added rule in RULES.md before planning. Apply them by default.
2. If the user's message for this job says something different ("make this one fast", "no captions"), the job instruction wins for this job only. Ask whether it should become a rule.
3. Use the user's own words for on-screen titles when they give them. Otherwise propose titles in edit-decision.md for approval.
4. After every delivery, ask: "Anything to change? Should it become a rule?" Every correction goes through Change control at the bottom.

## Pro motion graphics and music recipe (verified 2026-10-15, Windows)

Follow the "Quality bar", "Graphic look", "Graphic set", "Camera feel", "Music" and "Ending" lines in RULES.md. Method that worked:
- **Cards:** write each card as a small HTML file, render it to a transparent PNG with `chrome.exe --headless=new --default-background-color=00000000 --force-device-scale-factor=1 --window-size=W,H --screenshot=out.png file:///...`. Design at the video's pixel size (3840 wide for 4K). Check a contact sheet before using them.
- **Animation:** one `-loop 1 -framerate 30 -t D -i card.png` input per card, then `format=rgba,setpts=PTS-STARTPTS+T0/TB` and `overlay=x='96-(W+96)*(pow(1-min(max((t-T0)/0.35,0),1),3)+pow(min(max((t-(T1-0.3))/0.3,0),1),2))':y=Y:enable='between(t,T0,T1)':format=auto`. Apply overlays per segment, before concat, using segment-local time. Card inputs start after the video and music inputs.
- **Zoom:** `scale=w='trunc(W*(Z0+(Z1-Z0)*t/DUR)/2)*2':h=...:eval=frame,crop=W:H:x='(iw-W)*FX':y='(ih-H)*FY'`. Freeze a frame with `tpad=stop_mode=clone:stop_duration=N`.
- **ffmpeg 9 on this machine:** use `-/filter_complex file`, not `-filter_complex_script`. `drawtext` needs an explicit `fontfile` (fontconfig is missing). Source phone clips are yuvj420p: scale with `in_range=pc:out_range=tv`.
- **Audio:** build stems in separate commands (music: `atrim, loudnorm=I=-27:TP=-4:LRA=7, afade in/out`; natural: `atrim, volume, adelay, apad=whole_dur=TOTAL`; then `sidechaincompress` + `amix normalize=0` + `alimiter`). Put everything in one big graph only if the duration checks out; a combined graph once cut audio to 46 s. Mux with `-c:v copy`.
- **PowerShell traps:** variable names are case-insensitive (`$S` and `$s`, `$H` and `$h` collide). A one-item `@(@(...))` flattens. Do not delete inside `05-graphics`. Run long renders from a `.ps1` file.
- **Deliver:** final with audio, silent picture-lock, music and natural stems, `voiceover-script-*.md`, license line, loudness numbers. HyperFrames 0.8.160 is now installed globally (npm, free, local; the user approved it on 2026-10-15). Use it for animated graphics (add `%APPDATA%\npm` to PATH, set `HYPERFRAMES_SKIP_SKILLS=1`, then `hyperframes init NAME --example blank --resolution 4k --non-interactive`, `hyperframes lint`, `hyperframes render --gpu --browser-gpu`). Docker is not installed and not needed. Smoke render of a 10 s blank project took 18 s. The Chrome + ffmpeg card method above stays as the fallback.

## Hook and retention (every video, studied 2026-10-29)

Read `references/hook-and-retention.md` before planning a cut. In short: open on the best clip (starting just before its peak) so it works muted and proves the title in 5 s; open a question early and pay it off late; edit the first 30 s hardest and fastest; change what is on screen every few seconds without cutting for its own sake; use tight jump cuts; every graphic enters with motion or a sound; keep one look throughout. In edit-decision.md, list the cold-open clips (source times plus why each one hooks) and where the hook ends (that is `-IntroAt`).

## Pushpstation intro and outro (every video, added 2026-10-29)

`brand/` holds the channel's gaming pack (v2, 2026-10-29). It was built after studying Techno Gamerz, Ujjwal, Total Gaming, Live Insaan and GamerFleet:
- **Colours:** deep navy #0B0820, electric violet #6C2BFF, hot yellow #FFD60A, white; the subscribe button is YouTube red #FF0033.
- **Shapes:** sharp 22-degree slash bars, slanted chips, and a "P" emblem (a violet slanted block with a yellow cut corner).
- **Type:** Anton for the big condensed text, Rajdhani Bold for labels.
- **Sound:** synthesised whoosh, impact, tick, click, pop and bell.
- **Motion:** smooth eases only; no wobble or shake.

| Piece | Format | What it does |
|---|---|---|
| `intro_long` | 16:9, 2.9 s overlay | Slash bars sweep across, the emblem spins in, the PUSHPSTATION letters rise, then the "NOW PLAYING" and game-name chips and a shine pass; it clears and the slashes sweep off. Placed where the cold-open hook ends. |
| `transition` | 16:9, 1.0 s | The slash bars cover the frame at 0.40-0.52 s with an emblem flash. Centred on a cut, it is used for section changes (`-Cuts`), not every cut. |
| `subscribe` | 16:9, 3.4 s, bottom centre | The red SUBSCRIBE pill rises, a cursor clicks it, it turns grey SUBSCRIBED, the bell pops and rings. Placed on the sign-off line (`-SubAt`, default 6 s before the end). |
| `outro_long` | 16:9, 15 s | A slash wipe starts 0.42 s before the last frame and leads into a full-frame end screen: logo, next-video note, two corner-bracket slots for YouTube's end-screen videos (720x405 at 150,250 and 1050,250), and a rotating ring for the subscribe circle (centre 960,905). |
| `intro_short` | 9:16, 2.6 s overlay at 0 s | A slanted yellow/violet/navy band at y 280-640 with the emblem, a "NOW PLAYING" chip and the game name, over the hook action. |
| `outro_short` | 9:16, last 3.6 s | A slash wipe into a full-frame card: emblem, PUSHPSTATION, FULL VIDEO, an ON THE CHANNEL chip, and the subscribe click with the bell. |

Apply it as the last step, after picture lock and the mix and before packaging:
```powershell
& "$HOME\.claude\skills\video-edit\brand\brand_wrap.ps1" -Video final.mp4 -Mode long -IntroAt <hook end s> -Note "<Game name>" [-Tag "NOW PLAYING"] [-Cuts "95.2,301.8"] [-SubAt <sign-off s>] [-Next "NEXT: <game>"] [-Right "BEST VIDEO"] [-Music bed.mp3] -Out final-branded.mp4
& "$HOME\.claude\skills\video-edit\brand\brand_wrap.ps1" -Video short.mp4 -Mode short -Note "<Game name>" [-Tag "PS PLUS"] [-NoOutro] -Out short-branded.mp4
```
- The script renders the graphics with HyperFrames at the video's own resolution (alpha ProRes), composites them, adds the SFX, encodes with NVENC cq 16 (HEVC stays HEVC), applies a -2 dB limiter and prints duration and loudness. A long video grows by 14.58 s. Tested at 1080p60 and 4K HEVC 60 (a 25 s 4K clip took 155 s).
- `-Cuts`: section changes only (a new game, a new chapter), usually 2-6 per long video. The cut must sit exactly at the given time, because the frame is covered for only 0.12 s around it.
- Before running it, drop any older title, end or subscribe cards from the edit so nothing stacks. Then look at frames at the hook end +1 s, at each cut, during the subscribe click, and in the end screen.
- The end screen plays over the muffled audio of the last 15 s unless `-Music` (a SnipSound bed) is given. In YouTube Studio the user places the two videos on the corner brackets and the subscribe element on the ring.
- Change the look in `brand/hf/*.html` (shared helpers in `brand.css` and `brand.js`). After moving any animation time, update the times in `brand/make_sfx.sh` and re-run it.

### Channel art (added 2026-10-29)

`brand/channel-art/art.html` holds the same pack as still images; `render_art.ps1 -OutDir <folder> [-Highlights "GAMEPLAY,NEWS,TECH,SHORTS,SETUP"]` screenshots them with headless Chrome.

| File | Size | Notes |
|---|---|---|
| `youtube-profile-800.jpg` | 800x800 | Shown as a circle; the P badge stays inside it |
| `instagram-profile-1080.jpg` | 1080x1080 | Instagram shows it as a 320 px circle |
| `youtube-banner-2560x1440.jpg` | 2560x1440, under 6 MB | Logo and chips inside the 1546x423 safe area (507,508); `banner-safe-area-check.png` draws that box in red |
| `youtube-watermark-150.png` | 150x150, transparent | Studio > Customization > Branding > Video watermark |
| `instagram-highlight-NN-<name>.png` | 1080x1920 | Instagram crops the centre circle; the label sits inside a 750 px disc |

Check the profile and highlights as circle crops at phone size before handing them over. Channel copy (description, keywords, bio) goes in chat, never in a file (RULES 2026-10-23).

## Hiding private info (verified 2026-10-16)

- Track the target with a template match: pull gray 960x540 frames at 10 fps through ffmpeg rawvideo into numpy, FFT normalised cross-correlation against a template cut from one clear frame. Keep matches with score above 0.75, median-filter, interpolate, and hold the nearest sample with a bigger box in gaps. Write a 960x540 gray mask video (FFV1), one frame per output frame.
- Apply it with `[blur][mask]alphamerge` then `overlay`. Do NOT use `maskedmerge`: it only blended about 60% and left the name faintly readable.
- Verify at 100%: crop the region at full size every 0.75 s. Thumbnails hide leaks. Do not call a blur done from a contact sheet.
- Keep unblurred renders out of the delivery folder. Move them to `OLD-name-visible-do-not-share`.
- Windows `Settings > System > About`: record only the four spec tiles (crop 1262x320 starting 490,90 inside the window). Never include the profile name, the device name row, Device ID, Product ID or serial.

## PS5 OBS recordings (set up 2026-10-17 to 2026-10-19)

The user records PS5 gameplay in OBS through a UGREEN 25773 card. Recording problems and OBS changes belong to `/ps5-obs-setup`, not this skill.
- **How to recognise one:** `%USERPROFILE%\Videos\PS5 Recordings\PS5 YYYY-MM-DD hh-mm-ss.mp4`, 1920x1080 60 fps HEVC, **3 AAC audio tracks**: `0:a:0` mix, `0:a:1` PS5 game only, `0:a:2` mic only (fifine, RNNoise, so it is digital silence between words). All 3 are flagged default; players often play the mic track, which looks like "no game audio" but is not.
- **Audio:** build the final mix from `0:a:1` and `0:a:2`, never from the baked mix. Voice 3-5 dB above the game while talking: sidechain-duck the game under the voice (like the music duck), then add the SnipSound bed under both. Measure first: on 2026-10-18 the raw voice sat 14 dB under the game. Silent stretches on the game track are loading, menu or tutorial screens; check a frame before calling it a fault.
- **Sync:** mic-vs-game and facecam delay are unmeasured. Before cutting on speech, check one clap or sharp word against the picture, and shift the mic with `adelay`/`atrim` if they disagree.
- **Facecam:** a phone (Nothing Phone 2) picture cropped to a portrait box in the top-right (last 289x514 at 1615,35), kept outside the 9:16 centre band x 656-1264. **Measure the rectangle from frames on every job** (the user moves it): find the box edges with a column/row difference on a few frames. The laptop camera is the fallback, 16:9.
- **Shorts layouts:** A = full-height centre crop `crop=608:1080:656:0` scaled to 1080x1920 with the facecam cut out and overlaid near the top (default for matches); B = facecam stacked above a wider game crop (reactions). Pan the centre crop to follow the ball or action only when the action leaves the band, using the eased crop-x expression; never cover the scoreboard.
- **HUD:** FC 26 puts the clock and score at the top-right next to the facecam. Keep them readable in 16:9; in Shorts, crop or reposition them only if they carry the moment (a late goal).
- **Deliver** with a single audio track (the new mix). Never ship a file with the 3 OBS tracks.

- **Long video + Short from a horizontal and a vertical recording of one session:** use the gameplay-longform-shorts skill (cut list from speech and action energy, sync offset, segment-wise 4K render, cards, mix, packaging, cleanup).

## Free of cost — always

Never buy, subscribe, start a paid trial, sign up for a paid API, or use a cloud render. If a step would need anything paid, stop and tell the user.

| Tool | Cost |
|---|---|
| Claude Code | The user's existing Claude plan. |
| Parakeet (sherpa-onnx, local) | Free, offline. |
| faster-whisper large-v3 (local GPU) | Free, offline (MIT). |
| Google Chrome | Free. |
| FFmpeg, video-timeline-copilot (`vtc`) | Free (open source). |
| DaVinci Resolve 21 **Free** | Free. Never suggest Studio-only features (external scripting, Voice Isolation, Magic Mask, AI tools marked Studio). |
| HyperFrames | Free for **local** render only. Never use `cloud`, `lambda`, `cloudrun`, `publish`, `auth`, HeyGen TTS/avatars, or media-use `resolve --type bgm/sfx/voice/image`. |
| SnipSound | Free, no account. Royalty-free for YouTube/Reels. Copy each track's license line into LICENSE.md. |
| OBS Studio (recording) | Free, installed. |

## Tools, in this order

All 7 are mandatory. If one cannot be used on a job, write the reason in the delivery checklist. Do not silently substitute.
1. **Editor — Claude Code.** You coordinate. You do not skip ahead of the transcript.
2. **Transcriber — word timestamps.** English → Parakeet. Hindi/Hinglish → GPU Whisper large-v3 (the checklist says "Parakeet unavailable: Hindi not supported").
3. **Researcher — Google Chrome.** Official docs, patch notes, release pages, and posts. Save the URL, the capture, and the date.
4. **Screen editor — FFmpeg + video-timeline-copilot (free).** Cuts, zooms, crops, reframes, EDL, FCPXML. Open DaVinci Resolve Free only when the "Resolve gate" below says so.
5. **Animator — HyperFrames** (local, GPU) for the hook title, lower thirds, and motion graphics. Lint, preview, then render.
6. **Sound designer — SnipSound MCP only** (https://mcp.snipsound.com/mcp).
7. **Finisher — FFmpeg.** Clean voice, assemble, mix, measure loudness, and reject a bad export.

## GPU — where it is required or makes the work easier

| Job | Device | How |
|---|---|---|
| Hindi/Hinglish transcription | **GPU** | `whisper_gpu.py` → faster-whisper large-v3 float16 on CUDA (~10× faster than CPU). |
| English transcription | CPU | Parakeet on the 24-core CPU is already fast. |
| Decoding source video | **GPU** | `-hwaccel cuda` on every input. Essential for 4K/HEVC/AV1 game capture. |
| Proxies and previews | **GPU** | `-c:v h264_nvenc -preset p4 -cq 23 -b:v 0` |
| Final master | **GPU** | `-c:v h264_nvenc -preset p7 -tune hq -rc vbr -cq 19 -b:v 0 -profile:v high -pix_fmt yuv420p` (verified). If NVENC errors or a spec fails, re-export with `libx264 -preset slow -crf 18` and note it. |
| HyperFrames render | **GPU** | `npx hyperframes render --gpu --browser-gpu` |
| Crop, scale, overlay, subtitles, audio | CPU | Filters stay on the CPU and the GPU encodes. Do not chain CUDA filters at 1080p. |

If the GPU path fails, fall back to the CPU, finish the job, and record the fallback in the checklist.

## Setup facts and commands

- Refresh PATH at the start of each shell:
  `$env:Path = "$env:USERPROFILE\.local\bin;" + [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User") + ";$env:APPDATA\npm"`
- PowerShell 5.1 has no `&&`; use `; if ($?) {...}`. Quote paths. Open a file with `Start-Process "<file>"`. Never use `open`, `brew`, `videotoolbox`, `/tmp`, or `python3`.
- **Python for the skill scripts:** `$py = "$env:APPDATA\uv\tools\video-timeline-copilot\Scripts\python.exe"`. Run scripts as `& $py -I "$HOME\.claude\skills\video-edit\scripts\<script>.py" ...`. That environment has faster-whisper, CUDA cuBLAS/cuDNN, numpy, and vtc.
- **Scripts in `scripts/`:**
  - `whisper_gpu.py INPUT OUT_DIR --language hi --prompt "<names>"` writes `transcript.json` (same shape as Parakeet) and `transcript.vtc.json`. Always pass the product, game and person names from research in `--prompt`, or Whisper misspells them.
  - `parakeet_to_vtc.py TRANSCRIPT_JSON SOURCE OUT_JSON` converts a Parakeet transcript to vtc format.
  - `romanize.py draft|apply TRANSCRIPT_JSON OUT_DIR` converts Devanagari to Roman Hinglish word by word, keeping timestamps. `draft` writes `transcript.roman.json` plus `romanize-review.json` (each unique Hindi word once). Claude then reviews and edits that file: casual Hinglish spelling as a YouTuber types it (yeh, nahi, hai, kya); English loanwords back to English (वीडियो→video, सेटिंग्स→settings, क्लिक→click, सब्सक्राइब→subscribe); product and game names from research spelled officially. `apply` writes the final file and saves the corrections in `hinglish-dictionary.json`, so later videos need fewer fixes.
  - `captions.py WORDS_JSON EDL_JSON OUT_DIR [--vertical] [--top] [--margin-v N]` remaps words through the cut and writes `words.out.json`, `captions.srt`, and `captions.ass` (clean minimal, Nirmala UI, which covers Devanagari and Latin).
- **Parakeet:** `npx hyperframes transcribe "<source>" --engine parakeet --dir video-edit/01-transcript --json`
- **vtc** (video-timeline-copilot): `inventory`, `analyze-video`, `pack-transcripts`, `draft-silence-cut`, `refine-audio-cuts`, `validate-edl`, `export-srt`, `export-fcpxml`, `render-preview`, `qa-preview`, `evaluate-edl`. Use `--edit-dir video-edit/03-edl/vtc`. Put the transcript at `video-edit/03-edl/vtc/transcripts/<source-stem>.json` **before** any vtc step, so vtc never runs its own Whisper. Use **absolute** source paths in the EDL.
- **Chrome research:** use the Claude in Chrome tools (`mcp__claude-in-chrome__*`, load them in one ToolSearch call). If the extension is not connected, use headless Chrome: `& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --screenshot="<out.png>" --window-size=1600,2000 <url>` / `--dump-dom <url>`.
- **FFmpeg 9.0** (gyan full build) has loudnorm, ebur128, sidechaincompress, afftdn, deesser, libass, drawtext, cuda, and nvenc.
- **DaVinci Resolve Free 21.1:** `C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe`. Free has no external scripting, so hand-off is by FCPXML: the user does File → Import → Timeline → select the `.fcpxml` and turns off "automatically import source clips" if the clips are already in the Media Pool.
- **Reference skills** (/cut-video, /clipify) are written for macOS. Use their method and translate commands: `videotoolbox` → `cuda`/`h264_nvenc`; `open` → `Start-Process`; `/tmp` → `video-edit/`. Their MFA/conda/whisper steps are replaced by Parakeet or GPU Whisper.

## Resolve gate — open DaVinci Resolve Free only when really needed

Use Resolve (via FCPXML hand-off) only for:
- **Color:** log/HDR footage, mismatched cameras, or a look the user asks for.
- **Multi-source sync:** a separate mic or second camera, or several takes that need syncing by waveform.
- **Hand fine-tuning:** the user wants to drag clips or keyframes themselves, or a fix is easier by eye than by numbers.
- **Complex compositing** beyond FFmpeg/HyperFrames (Fusion tracking, masks that are not Studio-only).

Otherwise FFmpeg does the edit. When Resolve is used: export the FCPXML plus the SRT, tell the user exactly what to do in Resolve, and wait. Then take their Resolve render back into FFmpeg to measure, and fix loudness or specs if needed. Say "Resolve used for: <reason>" in checklist line 4.

## Project layout, created beside the source file

video-edit/
  00-source/
  01-transcript/
  02-research/
  03-edl/          (edit-decision.md, edl.json, vtc/)
  04-audio/
  05-graphics/
  06-renders/
  LICENSE.md

## Pipeline. Stop at the approval gate.

0. **Ask the format first.** Before planning any cut, ask: YouTube Short (9:16), full YouTube video (16:9), or both. Render only what the user picks.

1. **Inventory.** Run ffprobe for duration, fps, size, codec, audio streams/channels, and sample rate. Write the path into 00-source/SOURCE.txt. If the source is HEVC, AV1, 4K or over 500 MB, make a 1080p NVENC proxy for analysis and keep the original for the final render. OBS files with several audio tracks: identify the mic track and the game/desktop track, and keep them separate for mixing.
2. **Language check, then transcribe.** Run `whisper_gpu.py` with `--language auto` on the first 60 s (`-t 60` cut via FFmpeg). Detected `en` with no Hindi words → Parakeet. Detected `hi`, or Hinglish → `whisper_gpu.py --language hi --prompt "<names>"`. Save to 01-transcript/, then copy the vtc-format transcript into `03-edl/vtc/transcripts/`. **Hindi/Hinglish: romanize right away** (`romanize.py draft` → review every word in `romanize-review.json` → `romanize.py apply`). From then on, `01-transcript/transcript.roman.json` is the transcript used for reading, filler detection, edit-decision.md quotes, and captions. Timestamps are identical to the original. Gameplay without voice → skip words, cut on action (clipify transients plus `vtc analyze-video` scene changes), and say so in the checklist.
3. **Research in Chrome.** Tech: the product's official page plus one primary source for every factual claim. Gameplay: patch notes or the mission name, plus control labels if on screen. Save captures, URLs and dates in 02-research/. Invent no specs, prices, or patch numbers. Feed the names you find to `--prompt` (re-run transcription if names were wrong).
4. **Plan the cut.** Run `vtc analyze-video` and `vtc pack-transcripts`. Read `takes_packed.md` and the sampled frames. Build `03-edl/edl.json` using the cutting patterns below, then `vtc refine-audio-cuts --replace` and `vtc validate-edl`.
5. **Write 03-edl/edit-decision.md before any final render:**
   - mode: tech or gameplay; language and transcription engine
   - keep and drop ranges with times and the words at each seam; every retake group (which take is kept)
   - zoom and crop notes; facecam and HUD rectangles for gameplay
   - title text (the user's words if given), lower thirds, caption style (from My style)
   - YouTube chapters (from topic changes in the transcript)
   - SnipSound query, chosen track, license label, download URL
   - whether Resolve is needed, and why
   - target file names
   Render a fast NVENC rough preview (`vtc render-preview`) so the user can watch it. Show the file and the preview, and **wait for "yes"** before the final render.
6. **Screen edit** in FFmpeg using the patterns below. Gameplay: drop menu time and failed attempts unless the failure is the point. gameplay-screen for action, gameplay-facecam for reactions. Facecam never covers the HUD.
7. **Sound.** Search SnipSound by mood and max length. Download only from the official track link into 04-audio/, and append title, URL and license to LICENSE.md. Clean the voice, then duck music under it. Add a short SnipSound effect on a click or a kill only when it matches the cut.
8. **Graphics.** HyperFrames for the hook title and section lower thirds. Captions come from `captions.py`, run on `transcript.roman.json` for Hindi/Hinglish (Roman letters per My style) or on `transcript.json` for English. Check the SRT has no Devanagari left before burning. The style follows My style ("clean minimal" = `captions.ass` burned with libass). Use HyperFrames captions only if the user picks an animated style. Captions sit in the lower third, off the facecam and HUD (`--top` or `--margin-v` to move them). Always ship `captions.srt`.
9. **Finish** in FFmpeg with CUDA decode and NVENC encode. Match the source frame rate; never retime 60 fps gameplay to 30. Measure, compare against the spec, and re-export on any failure.
10. **Short** (when long form > 60 s): one self-contained idea, reframed to 9:16, its own captions (`--vertical`), its own loudness check.
11. **Brand.** Run `brand/brand_wrap.ps1` on every final, long and Short (see "Pushpstation intro and outro"). The checklist names the `-IntroAt` used.

## Delivery specs, measured, not estimated

- Long form: 1920x1080, 16:9, H.264, yuv420p, AAC 48 kHz stereo.
- Short: 1080x1920, 9:16, 60 seconds or under unless the user asks for longer.
- Integrated loudness -14 LUFS ±1 LU, true peak ≤ -1.5 dBTP. Measure with ffmpeg ebur128 and paste the numbers.
- Voice intelligible over music. Music stays under the voice.
- Caption timing follows word timestamps. No caption over a facecam or a gameplay HUD element the viewer needs.
- First picture of a gameplay video is action, within the first 3 seconds. No logo or greeting before the hook; the brand intro comes after it.
- Every final carries the brand intro and outro (long: 15 s end screen appended; Short: overlays only).
- Tech video states the tool name on screen in the first 5 seconds.

Reject and re-export if any measured spec fails.

End every job with:
- render path(s), duration, frame size, fps, encoder (NVENC or libx264 fallback)
- loudness numbers (I, TP, LRA) per file
- SnipSound title and license line
- YouTube chapters text, ready to paste
- a 7-line checklist, one line per tool, marked used or skipped, with a reason if skipped
- "Anything to change? Should it become a rule?"

## Cutting patterns (cut-video, video-timeline-copilot, tella-remove-mistakes method)

- Gap table, using word gaps (Balanced is the user's default): gaps under 0.25 s keep; 0.25–1 s → 0.3 s; 1–3 s → 0.8 s; over 3 s → 0.5 s. Use `aggressive` (0.1/0.2/0.2 s) or `relaxed` (only gaps over 1.5 s → 0.8 s) only when asked.
- Always cut standalone fillers. English: `um, uh, er, erm, ah, hmm`. Hindi/Hinglish: `matlab` (as filler), `yaani`, `toh` (as an opener), `haan toh`, `achha toh`, `basically`, `like`, `you know`, `aa`, `umm`. Cut only when they are filler, never when they carry meaning.
- Retakes: fuzzy-match sentence openers and 4-grams across a 60 s window (works for Devanagari and Roman). Keep the last complete take, and list every retake group in edit-decision.md. Slate words ("okay", "phir se", "ek baar aur", "again") mark a retake.
- Once the finished result is on screen, never cut back to work-in-progress footage (a cold-open teaser of the result is the only exception). Showcase stills/close-ups go after the reveal, not before it.
- Check the first shot frame by frame at full frame rate (not 4–5 fps samples): no person walking through a hero or cold-open shot.
- Never put product or brand labels on screen based on what a frame seems to show. Use only names the user confirms.
- Never hard-cut between shots with very different lighting (day vs night/RGB); use a motivated dissolve or a match-cut on the same object.
- Never cut laughs, reactions, the beat after a punchline, or a pause the user marked intentional. Check amplitude against the measured noise floor, never a fixed dB.
- Any word lasting about 1 s or longer is hiding a pause or a collapsed retake. Re-transcribe that ±3 s window in isolation before trusting it.
- Pads: onset −0.03 s, offset +0.05 s; then `vtc refine-audio-cuts`. Never split a word. Clips ≥ 0.8 s. When unsure, leave it in.
- Render cuts with `trim`/`atrim` + `setpts`/`asetpts` + `concat` via `-filter_complex_script`. Never use `select`/`aselect`.
- Verify: re-transcribe the cut render and scan for duplicate words and bigrams across seams and for stray fragments. Re-cut until clean. `vtc evaluate-edl --require-preview --strict-cut-warnings` must pass.

## Screen and zoom patterns (replaces Tella, all FFmpeg)

- Every shot shows what the viewer should look at. Show the screen during a click, typing, a menu, a result, code, or "yeh dekho / this / here". Show the face for the hook, an opinion, a reaction, or the sign-off.
- **Find zoom moments** from the transcript cues ("yahan click karo", "this button", "settings mein") plus `vtc analyze-video` activity, then confirm by looking at frames (`ffmpeg -ss T -frames:v 1`). A few motivated zooms per minute at most.
- **Smooth zoom-in/hold/out** (Tella-style, verified on this machine) on a segment, with zoom factor Z, target point (CX,CY) in source pixels, ramp R s, zoom-out starting at T2:
  `zoompan=z='1+(Z-1)*(E)':x='max(0,min(iw-iw/zoom,CX-iw/zoom/2))':y='max(0,min(ih-ih/zoom,CY-ih/zoom/2))':d=1:s=1920x1080:fps=<source fps>`
  where `E` = `if(lt(it,R),0.5-0.5*cos(PI*it/R),if(lt(it,T2),1,if(lt(it,T2+R),0.5+0.5*cos(PI*(it-T2)/R),0)))` (`it` = segment time). Use R = 0.4–0.6 s and Z = 1.4–2.0. Apply per segment after `setpts=PTS-STARTPTS`. Do not use `crop` with time-varying w/h (crop size is fixed at init and the zoom lands in the wrong place).
- Static zoom = `crop=W:H:X:Y,scale=...` with W:H matching the target ratio within 2%. Pans use a 0.667 s eased crop-x expression.
- **Blur sensitive info** (emails, tokens, personal tabs) with `boxblur` inside a crop+overlay region. List each blur in edit-decision.md.
- 9:16 reframe: a crop window of source_height × 9/16. Use a blurred backdrop when the panel is narrower. Text that already appears in the source (code, titles, lists) must stay fully readable; black bars beat clipped words.
- **Gameplay + facecam:** measure the facecam and HUD rectangles once. `gameplay-screen` = the largest region excluding the facecam. `gameplay-facecam` = crop into the face for reactions. For Shorts, stack the face on top and the game below (vtc `visual_layers`). Facecam goes on the side away from the HUD; captions at the opposite edge.
- **Gameplay hook:** the first frame within 3 s is action. Pull the best action beat (transient peak or kill sound) to the front as a cold open if the recording starts slowly.

## Shorts (video-timeline-copilot shorts guidelines, clipify)

- One self-contained idea: hook → minimal context → payoff → deliberate end. Never end on a clipped word or an empty tail.
- Choose by hook strength, standalone clarity, payoff, and a usable vertical crop. Do not pad. Cap at 60 s unless the user asks for longer.
- Captions: `captions.py --vertical` (26 chars/line, margin clear of the Shorts UI).

## Sound and finish

- **Voice clean-up (free FFmpeg chain)**, measured before and after: `highpass=f=80,afftdn=nr=12:nf=-30:tn=1,deesser=i=0.3,acompressor=threshold=-20dB:ratio=3:attack=10:release=150:makeup=2`. Back off `afftdn` if the voice sounds watery.
- **Ducking:** `sidechaincompress` with the music bed into the voice sidechain, threshold ≈0.03, ratio 8, attack 20, release 300. The bed sits −18 to −22 dB under the voice. Keep game audio under the voice too.
- **Loudness:** two-pass `loudnorm=I=-14:TP=-1.5:LRA=11` (pass 2 uses `measured_*` + `linear=true`), then measure the final file with `ebur128=peak=true`. Fail if I is outside −15…−13 or TP > −1.5.
- **Final probe:** run ffprobe for size, fps, codec, pix_fmt, sample rate and channels. Compare with the spec and re-export on failure.

## Change control

When the user corrects an edit or says "remember this":
- Add one dated rule to RULES.md, in their words. Style changes also update the "My style" block.
- Update SKILL.md so the next run follows it.
- Reply with the rule text and both file paths.
- Delete a rule only when the user says to remove that rule.
