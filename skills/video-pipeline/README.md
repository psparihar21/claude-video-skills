# video-pipeline

One video file in, everything ready to upload out. Chains `video-edit` (16:9 edit), the `clipify` moment-finding method (9:16 Shorts/Reels), optional voiceover (`faceless-vo-script` + `own-voice-render`) and `video-packaging` (thumbnails, titles, description, captions).

## Requirements

The skills it chains, ffmpeg/ffprobe, video-timeline-copilot (`uv tool install video-timeline-copilot`).

## Scripts / usage

`scripts/inspect_source.py <video>` writes a source report (streams, tracks, duration) the pipeline plans from.

The full workflow Claude follows is in [`SKILL.md`](SKILL.md).

## Privacy and safety

Only for the user's own footage or footage they may reuse; a downloaded YouTube video must be their own upload.
