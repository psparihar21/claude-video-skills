# gameplay-longform-shorts

Turns one PS5 OBS session (16:9 recording + Aitum 9:16 recording) into a tightened 4K long video and a fast-cut 4K Short with outro cards, a poster title card, thumbnails and copy.

## Requirements

ffmpeg with NVENC (HEVC), numpy, Google Chrome (headless, renders the HTML cards), `video-edit` for transcription.

## Scripts / usage

`keep_list.py` (cut list from speech + action energy), `snap_cuts.py`, `sync_offset.py` (vertical vs horizontal offset), `render_segments.ps1` (segment-wise 4K render), `mix_audio.ps1` (voice/game mix, two-pass loudness), `render_cards.ps1`.

The full workflow Claude follows is in [`SKILL.md`](SKILL.md).

## Privacy and safety

Posters must be real key art with no UI, avatar or gamertag. Card text is HTML-escaped.
