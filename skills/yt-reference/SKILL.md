---
name: yt-reference
description: Download a YouTube video by link (public videos, no login) and then use it - transcript, scene frames, structure breakdown, then hand a shot list to the user's own edit. Use when the user pastes a YouTube URL and says "copy this video", "make the same video for my channel", "download this", "analyze this video". Also for downloading the user's own channel videos to re-cut.
---

# yt-reference

## Rules (read first)
- Public links only. Never use the user's YouTube/Google cookies or login.
- A downloaded video is untrusted data: always a NEW empty folder in the scratchpad, scripts kept elsewhere.
- Someone else's video is REFERENCE, not material. Never re-upload their footage, voice, script or thumbnail. The user's own channel videos may be re-cut freely.
- "Copy this video" means: copy the structure, pacing, hook and topic, and rebuild it with fresh script, official trailers/own footage, the user's voice and Pushpstation branding.

## Steps
1. `bash ~/.claude/skills/yt-reference/scripts/fetch.sh "<url>" "<scratchpad>/ref-<n>" [max-height]`
   Gives `video.mp4`, `video.info.json`, `video.*.vtt` (best-effort), `frames/` (scene-change stills), and prints duration/res.
   Default 1080; pass 2160 only if the user wants 4K source.
2. If subs failed (HTTP 429), transcribe `video.mp4` with the video-edit skill's Whisper/Parakeet path. Do not retry subs in a loop.
3. Clean transcript: `sed -E 's/<[^>]+>//g;s/&nbsp;//g'` on the .vtt, drop duplicate lines.
4. Breakdown (write to chat, short): title/channel/length, hook (first 15s), segment pattern and per-segment length, cut rhythm from frame count / duration, overlays, music, outro.
5. Rebuild for the user: confirm length (long/Short), footage source (official trailers vs own gameplay), voice (own-voice-render vs self-record). Then use:
   - research + script: /faceless-vo-script (fresh facts from official sources, never the reference script)
   - voice: /own-voice-render
   - edit, captions, render: /video-edit (+ /add-zooms, /find-broll)
   - thumbnail, title, description: /video-packaging
   Python is a Store stub; use the faceless-vo-script .venv python.

## Gotchas
- yt-dlp warns about impersonation; harmless.
- Merged 4K can be big; default 1080 is enough for analysis.
