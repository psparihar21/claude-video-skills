---
name: ps5-obs-setup
description: Check, repair or change the user's PS5 gameplay recording setup in OBS on Windows (UGREEN 25773 capture card, fifine USB mic, Nothing Phone 2 or laptop facecam, 3 audio tracks, Ctrl+Alt+R/S hotkeys). Use when the user says "open OBS" (run scripts/open-obs.ps1, nothing else), OBS, recording, vertical, Aitum, VDO.Ninja camera, capture card, "no game audio", "mic too loud/quiet", "black screen / UGREEN logo", facecam, camera position, zoom the camera, hotkeys not working, or wants OBS set up again. Not for editing a recording (that is /video-edit or /video-pipeline).
---

# ps5-obs-setup

The user records PS5 gameplay with OBS for YouTube (16:9) and cuts Shorts/Reels (9:16) from the same file. This skill keeps that setup working. Set up and verified 2026-10-17 to 2026-10-19.

Windows 11, PowerShell 5.1, OBS 32.2.2, RTX 5070 Laptop. Never use macOS commands.

## The rig

PS5 HDMI -> UGREEN 25773 (HDMI in) -> HDMI out to the XV272K monitor. The user's headphones plug into the monitor, so they hear the game with no delay. The card's USB goes to a USB 3 port on the laptop. The fifine USB mic is on the laptop. Facecam: Nothing Phone (2) via Phone Link ("Windows Virtual Camera"), or the laptop's Integrated Camera as the backup.

## Known-good config

| Item | Value |
|---|---|
| Profile / scene collection | "PS5 Gameplay" (`basic/profiles/PS5_Gameplay`) / "PS5" (`basic/scenes/PS5.json`), the defaults in `user.ini` |
| Video | 1920x1080 canvas and output, 60 fps, NV12, Rec.709 partial, lanczos |
| Card source | dshow "PS5 Capture Card (UGREEN)", 1920x1080, interval 166666, YUY2 (video_format 301), buffering off, **its own audio off (mixers 0, muted)** |
| Game audio | WASAPI input "PS5 Game Audio (UGREEN)" on `Digital Audio Interface (UGREEN 25773)` = `{0.0.1.00000000}.{f7f1bc56-e206-4266-939f-a49dbe105dfc}`, tracks 1+2 (mixers 3). Filters: Gain -4 dB -> "Duck under mic" compressor (sidechain = Mic (fifine), ratio 6, threshold -32, attack 10, release 400) -> Limiter -2 dB |
| Mic | global Mic/Aux "Mic (fifine)" = `{0.0.1.00000000}.{5a259633-ffa3-48fb-95f2-5513f22928cb}`, tracks 1+3 (mixers 5), fader 0 dB. Filters: Noise Suppression (RNNoise) -> Gain +8 dB -> Compressor 4:1 at -20 dB -> Limiter -1 dB |
| Desktop audio | off (no laptop sounds in recordings) |
| Recording | Advanced output, NVENC HEVC CQP 18 p5 hq, Hybrid MP4, tracks 1-3 (RecTracks=7): 1 Mix, 2 PS5 Game, 3 Mic, AAC 320 |
| Files | `%USERPROFILE%\Videos\PS5 Recordings\PS5 YYYY-MM-DD hh-mm-ss.mp4`, about 10-14 GB per hour |
| Hotkeys | Ctrl+Alt+R start, Ctrl+Alt+S stop (the Legion F-keys need Fn, so Ctrl+F9 failed) |
| Facecam (phone) | crop L437 R438 T0 B0 (the phone sends a 405x720 portrait picture centred in 1280x720), scale to inner bounds. Last set: 289x514 at 1615,35 (top-right). The user drags it; read the current values from PS5.json, never assume |
| Facecam (laptop) | Integrated Camera 1280x720 30 fps NV12, hidden |
| Both facecams | `deactivate_when_not_showing: true`, so the hidden camera turns off |

**Shorts rule:** a visible facecam must stay completely outside x 656-1264 (the 608 px centre band a 9:16 crop of 1080p keeps). `check.ps1` fails if it overlaps.

A snapshot of this config is in `assets/known-good/`. `scripts/restore.ps1` puts it back.

## "Open OBS" = this, nothing more

When the user says "open OBS": run `open-obs.ps1`. It waits 8 s, launches OBS, checks the card started and the vertical canvas loaded, and does NOT start recording. Then tell them the two pre-flight items: phone sending to VDO.Ninja, fifine mic plugged in. Ctrl+Alt+R starts the 16:9 and the 9:16 file together, Ctrl+Alt+S stops both. Never launch OBS twice in a row quickly: if the card was just released, DShow fails with `0x800705AA` and every recording is black (fix: close OBS, wait 10 s, open again).

## Vertical canvas (saved by the user 2026-10-22, "now it is perfect")

Aitum Vertical 1.6.6 (official GitHub release, Windows zip) sits in `C:\ProgramData\obs-studio\plugins\vertical-canvas\` (`bin\64bit\vertical-canvas.dll` + `data\`). The `%APPDATA%\obs-studio\plugins` folder is NOT scanned. Settings: `%APPDATA%\obs-studio\plugin_config\vertical-canvas\config.json` (saved in `assets/known-good/vertical/`). Recording only, no stream outputs, replay buffer off.

| Item | Value |
|---|---|
| Output | 1080x1920, NVENC HEVC CQP 20 p5 hq, hybrid MP4, tracks 7 (same 3 as main), AAC 320, `%USERPROFILE%\Videos\PS5 Recordings\Vertical\PS5 Vertical <date>.mp4` |
| Hotkeys | Vertical start/stop are also Ctrl+Alt+R / Ctrl+Alt+S, so one press controls both outputs |
| Vertical scene | "Vertical Scene" (in `PS5.json`). Top half: capture card cropped L528 R528 T156 B156 at 1.25x = 1080x960 at (0,0). Bottom half: camera at (67.5,960), 1.75x, crop L270 R270 T98 B314 |
| Camera | Browser source "Camera (VDO.Ninja)" `https://vdo.ninja/?view=<private id, stored only in the scene file>&cleanoutput&videobitrate=8000` (the id is a secret: anyone who has it can watch the camera; never paste it into chat, docs or the repo), 1080x960, audio muted and not rerouted. The stream is portrait ~540x844 (low resolution: it looks soft when enlarged; for sharper video raise the quality/resolution on the sender link) centred at x270-810, y58-902 inside the source |
| 16:9 camera | same source, whole portrait frame, crop L270 R270 T58 B58, scale 0.43, bottom-left (0,~717), outside the Shorts band x656-1264 |

Items are locked so a stray click does not drag them; the camera drifted once when unlocked. If the vertical camera half shows a black bar, check the camera item's y is 960.

## Scripts

Run with `powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\ps5-obs-setup\scripts\<name>.ps1" ...`

| Script | Does |
|---|---|
| `check.ps1 [-Signal]` | Read-only health check: profile, sources, devices, Windows mute state, last log. `-Signal` also grabs 3 s straight from the card (close OBS first). Exit 1 on any FAIL. |
| `restore.ps1` | Backs up the current config to `obs-studio\backup-<time>`, restores the known-good one, sets the defaults, unmutes the UGREEN input. OBS must be closed. |
| `restore.ps1 -Snapshot` | Saves the current config as the new known-good. Run it only after the user confirms a change looks and sounds right. |
| `open-obs.ps1` | "Open OBS": launch, verify card and vertical canvas, no recording started. |
| `make-playable.ps1 "<file>"` | Lossless copy with only track 1 (mix) as the default audio, for watching in any player. |

## How to work

1. **Always run `check.ps1` first** and fix what it reports before touching anything else.
2. **Never edit OBS files while OBS is running.** OBS rewrites `PS5.json` and `basic.ini` on exit and undoes the change. Never close OBS while it records: check the last log for "Recording Start" without a later "Recording Stop". Close it with `(Get-Process obs64).CloseMainWindow()`, then `WaitForExit`.
3. **Edit `PS5.json` with Python, not PowerShell `ConvertTo-Json`**, which mangles nesting. Use `$env:APPDATA\uv\tools\video-timeline-copilot\Scripts\python.exe -I`, with the script in a short path such as `%LOCALAPPDATA%\Temp\obs-ps5\`. The session scratchpad path is over 260 characters and Python cannot open it.
4. When you move or resize a scene item, write both `pos`/`bounds` and `pos_rel`/`bounds_rel` (rel = (x-960)/540, (y-540)/540, w/540, h/540).
5. **Verify with a real recording:** start OBS with `--startrecording`, stop with Ctrl+Alt+S sent through `keybd_event` (OBS hotkeys are global), then measure each track with ffmpeg `volumedetect` / `ebur128` and look at a frame. For anything that needs the user (talking, clapping), ask with AskUserQuestion first, then start the recording right after they click.
6. After the user approves a change, run `restore.ps1 -Snapshot` and update the Known-good table above.

## Problems already solved

| Symptom | Cause | Fix |
|---|---|---|
| Card shows a UGREEN logo, no picture | HDCP on the PS5 | PS5: Settings > System > HDMI > Enable HDCP off. Also HDR off, and Video Output 1080p if still blank (the card captures up to 1080p60, 1440p30). |
| Game track silent | Windows muted the UGREEN audio input, and the card's dshow audio follows that mute | Unmute it: `restore.ps1` does this as its last step, or reuse its COM snippet on its own. Game sound comes from the WASAPI source. |
| "Only mic, no game" when playing a file | All 3 tracks are flagged default and the player picks track 3 | The file is fine. Use VLC / pick track 1, or run `make-playable.ps1`. |
| Ctrl+F9 does nothing | Legion F-keys are media keys without Fn | Ctrl+Alt+R / Ctrl+Alt+S |
| Phone facecam shows a lock or "i" icon | Phone locked, paused, or busy | Keep it unlocked, on a stand and on a charger. |
| Phone facecam has big black bars | It sends portrait video inside 1280x720 | Crop L437 R438. For a wider view, move the phone back or use its 0.6x lens. OBS cannot zoom out past the full 405x720 picture. |
| Laptop camera light on while using the phone | Hidden dshow source still active | `deactivate_when_not_showing: true` |
| Game too loud / voice buried | Game louder than voice while talking (measured -14 dB on 2026-10-18) | Current filters aim for voice 3-5 dB above game while talking, with ducking. Measure tracks 2 and 3 of the latest recording before changing anything. |

## Not measured yet

Mic-vs-game and facecam-vs-game delay. RNNoise removed the "headphone on mic" test signal, and the phone was pointed at the ceiling during the clap test. If the user notices lip or voice sync drift, ask for 3 sharp claps in front of the phone at the start of a recording, measure the clap in track 3 against the hands meeting on video, and set the source's `sync` offset (in nanoseconds) in PS5.json.

## PS5 console settings the user must set themselves

HDCP off; HDR off; Sound > Audio Output > Output Device = HDMI Device; Video Output resolution 1080p if the card shows no picture.
