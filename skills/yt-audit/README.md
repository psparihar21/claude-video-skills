# yt-audit

Audits a YouTube channel end to end: packaging, consistency, the first 15 seconds, dead air and retention, and what to fix first. Scripts adapted from youtube-agent-skill (license in `LICENSE-youtube-agent-skill.txt`).

## Requirements

Python 3.10+ (standard library), ffmpeg for `deadair.py`.

## Scripts / usage

`hookscore.py` (scores a hook against the 21 formulas in `hooks.json`), `title.py`, `deadair.py`, `retention.py` (YouTube Studio retention CSV export).

The full workflow Claude follows is in [`SKILL.md`](SKILL.md).

## Privacy and safety

Works on files you export yourself; it never logs in to YouTube.
