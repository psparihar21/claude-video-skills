---
name: video-pipeline
description: One-stop pipeline. The user hands over one video file (a PS5 OBS recording, a raw recording, or a video downloaded from their own YouTube channel) and gets back everything ready to upload, made by chaining their other skills in order. /video-edit makes the YouTube 16:9 edit, Shorts/Reels in 9:16 use the /clipify moment-finding method, an optional voiceover comes from /faceless-vo-script plus /own-voice-render, and /video-packaging makes the thumbnails, titles, description and captions. Use when the user gives a video path and says "make everything", "full package", "YouTube and Shorts", "do the whole thing", "video-pipeline", or just pastes a video file with no other instruction.
---

# video-pipeline

You run the user's existing skills in order on one video. Each skill keeps its own rules: **`video-edit` RULES.md overrides everything here on style, and every approval gate in a child skill stays.** This skill only decides the order, asks the questions once, and passes files between the steps.

Windows 11, PowerShell 5.1, RTX 5070 Laptop, free tools only. Never buy, subscribe, start a trial, or use a cloud render.

## How to call a child skill

Invoke it with the Skill tool (`video-edit`, `clipify`, `faceless-vo-script`, `own-voice-render`, `video-packaging`, `ps5-obs-setup`), pass the file paths and the decisions already made in `args`, then follow the instructions it loads. Do not re-ask a question this skill already answered. When the child skill finishes, come back here for the next step.

## Step 0: Intake (one round of questions)

1. **Get the file.** If the user gave no path, ask for it. Never search the disk.
2. **Inspect it:**
   ```powershell
   & "$env:APPDATA\uv\tools\video-timeline-copilot\Scripts\python.exe" -I "$HOME\.claude\skills\video-pipeline\scripts\inspect_source.py" "<video>"
   ```
   It writes `job.json` and reports the kind:
   - `obs-ps5`: 3 audio tracks (mix / game / mic) from the user's OBS setup. Full edit.
   - `raw`: one track, long, unedited. Full edit.
   - `edited`: short, vertical, or already finished (for example a download of a published video). Default to Shorts and packaging only; don't re-edit the long form unless the user asks.

   If the file sits under the app's scratch-workspace folder, copy it to a short path first (`%USERPROFILE%\Videos\pipeline\`), because uv/Python cannot open those long paths.
3. **Rights check.** The output is for the user's own channel (Pushpstation). If the video was downloaded from YouTube, it must be the user's own upload, or footage they have permission to reuse. If it is someone else's video, stop and say so: re-uploading it would break that creator's copyright and YouTube's rules. Don't continue with a "reaction" or "transformative" workaround.
4. **Ask everything in one AskUserQuestion call** (up to 4 questions), with the recommended option first:
   - **Make what?** "YouTube video + Shorts (Recommended)" / "Only Shorts" / "Only YouTube video". This satisfies video-edit's rule to ask the format before cutting.
   - **How many Shorts?** "3 (Recommended)" / "1" / "5".
   - **Voice?** "Keep my recorded voice (Recommended)" when the mic track has speech; otherwise "Voiceover in my own voice" / "Script only, I'll record it" / "No voice, music only".
   - **Packaging?** "Thumbnails + titles + description + captions (Recommended)" / "Only thumbnails" / "None".

   If the video's language or the game name is unclear, add it as a fifth question in a second call only if it is really needed. Otherwise the transcript and frames answer it.
5. Create the job folder from `job.json` (`<video name> - pipeline\`) with `01-youtube\`, `02-shorts\`, `03-voice\`, `04-packaging\`, `LICENSE.md`, `checklist.md`. video-edit's own working folders (`video-edit\00-source` ... `06-renders`) go inside it.

> **Gameplay pair shortcut:** a PS5 recording plus its `Vertical\` twin (same session) goes through `gameplay-longform-shorts`, which already contains Steps 1, 3 and 4 for that case.

## Step 1: YouTube edit (`/video-edit`)

Skip if the user chose "Only Shorts" or the kind is `edited`.

Invoke `video-edit` with: the source path, "format already chosen: <answer>", the voice choice, and, for `obs-ps5`, "OBS PS5 recording: track 1 mix, track 2 game, track 3 mic; build the mix from tracks 2 and 3". Let it run its full pipeline: transcription, research, the cut, the edit-decision.md, the rough preview, then **wait for the user's "yes"** before the final render. That gate is not optional.

Outputs to collect into `01-youtube\`: the final 16:9 master, the 1080p copy if made, `captions.srt`, the chapters text, the music license line, and loudness numbers.

## Step 2: Voiceover (only if the user chose it)

Run this after the picture is locked and before the final render, so the final mix carries the voice.
1. Invoke `faceless-vo-script` with the locked edit (its EDL or picture-lock render) and the register: Hinglish in English letters, per RULES.md. It writes `vo\<slug>\03-script.json` and the teleprompter.
2. "Script only": hand the user `02-script.md` and stop this step.
3. "My own voice": invoke `own-voice-render` with `03-script.json`. It needs the GPU and a human listen; send the audio and wait for the user's OK.
4. Give the voice track back to `video-edit` for the final mix (voice over game and music, ducked).

Copy the script and the voice files into `03-voice\`.

## Step 3: Shorts / Reels (9:16)

1. **Pick moments with the `clipify` method.** Use action mode for gameplay (transient peaks from goals, kills, crashes; scene changes from `vtc analyze-video`), dialogue mode for commentary (the transcript from step 1), or hybrid. Translate its macOS commands as video-edit says: `videotoolbox` → `cuda`/`h264_nvenc`, `/tmp` → the job folder, `python3` → the uv Python. Score each candidate on hook in the first 2 s, standalone clarity, payoff, and a usable vertical crop. Apply clipify's Shorts survival test (complete first thought, a turn, ends on a line, 20–55 s), give each a new first line scored with `clipify/scripts/hookscore.py`, 2 s of on-screen text in different words, and a loop point.
2. **Show the candidate list** (start, end, why, proposed title), one more than the number asked for, and let the user pick. One AskUserQuestion with multiSelect.
3. **Cut and reframe with `video-edit`'s Shorts rules:** under 60 s, one idea, hook → payoff → deliberate end, captions from `captions.py --vertical`, its own loudness check (-14 LUFS, TP ≤ -1.5).
   - `obs-ps5` layouts: **A** = full-height centre crop with the facecam overlaid near the top (default for matches); **B** = facecam stacked above the game (reactions). Measure the facecam rectangle from frames; never assume.
   - Other sources: centre or action-following crop; a blurred backdrop when the subject is wider than the crop; never clip on-screen text.
4. Name them `02-shorts\short-01-<slug>.mp4` and so on. Each Short ends by pointing to the full video on the Pushpstation YouTube channel, following RULES.md (2026-10-18).

## Step 4: Packaging (`/video-packaging`)

Skip if the user chose "None". Invoke `video-packaging` once per deliverable it supports, always from the finished renders:
- YouTube: one 1280x720 thumbnail from a real frame, 3 ranked titles, and a description that includes video-edit's chapters.
- Each Short: a 1080x1920 cover only if asked, plus a caption for YouTube Shorts and one for Instagram Reels (one caption can serve both if the user prefers).

Follow its rules: frames only, no generated people, and commit in Canva only after the user approves. Save into `04-packaging\`.

## Step 5: Deliver

1. Check every output with ffprobe: size, fps, one audio track, loudness. Re-export anything that fails a spec.
2. Write `checklist.md`: each step, the skill used or skipped (with the reason), every file path, and the loudness numbers.
3. Send the main files with SendUserFile: the YouTube master, the Shorts, and the thumbnail.
4. End the reply the way `video-edit` does: file paths, loudness, the SnipSound license line, chapters ready to paste, then "Anything to change? Should it become a rule?". Corrections go through video-edit's change control.

## When the recording itself is broken

No game audio, black picture, facecam missing, voice buried: that is a recording problem. Invoke `ps5-obs-setup` to check and fix OBS for next time. Then rescue this file in the edit where possible (for example, use track 2 or 3 directly), and tell the user what could not be rescued.

## Approval gates (the user only clicks)

1. The intake questions.
2. video-edit's edit-decision.md and rough preview, before the final render.
3. The Shorts picks.
4. Voice: listen and approve, only when own-voice-render ran.
5. The thumbnail, before a Canva commit.

Never skip a gate to save time. Between gates, keep working without asking.
