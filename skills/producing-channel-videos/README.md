# producing-channel-videos

Measures why a reference video holds attention, researches the topic fresh, and produces an original video package for your channel: script in your style, rights-cleared media plan, titles, thumbnail brief, description and chapters.

## Requirements

Python 3.10+, ffmpeg/ffprobe; optional faster-whisper for transcripts.

## Scripts / usage

`analyze_reference.py`, `hookscore.py`, `similarity_guard.py` (blocks scripts too close to the reference transcript), `title.py`, `check_package.py`. Scripts partly adapted from youtube-agent-skill (license included).

The full workflow Claude follows is in [`SKILL.md`](SKILL.md).

## Privacy and safety

Never reuses the reference's footage, audio, wording or voice. Asks approval before every costly step. Keep API keys out of files (see `references/connectors.md`).
